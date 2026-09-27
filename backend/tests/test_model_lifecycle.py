import pytest
import datetime as dt
import os
import json
import pathlib
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.services.model_lifecycle_service import ModelLifecycleService
from app.services.model_registry_service import ModelRegistryService
from app.services.model_training_service import PromotionGateException, ModelTrainingService

@pytest.fixture(autouse=True)
def isolate_model_dir(tmp_path, monkeypatch):
    test_dir = tmp_path / "models"
    test_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AEROCPI_MODEL_DIR", str(test_dir))
    yield test_dir

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_readiness_below_threshold_no_training(db_session):
    res = ModelLifecycleService.execute_lifecycle_trigger(db_session)
    assert res["triggered"] is False
    assert "NOT satisfied" in res["reason"]

def test_readiness_becomes_satisfied_one_training_run(db_session, monkeypatch):
    # Mock readiness to pass
    monkeypatch.setattr("app.services.model_lifecycle_service.calculate_readiness_metrics", 
        lambda db: {"overall_readiness": "READY_FOR_MODEL", "effective_forecasting_examples": 200})
    
    # Mock train_candidate to raise an exception just to see it was called and failed validation
    monkeypatch.setattr("app.services.model_training_service.ModelTrainingService.train_candidate", 
        mock.Mock(side_effect=PromotionGateException("Mock failure")))
    
    res = ModelLifecycleService.execute_lifecycle_trigger(db_session)
    assert res["triggered"] is True
    assert res["training_success"] is False

def test_duplicate_trigger_no_duplicate_run(db_session, monkeypatch):
    monkeypatch.setattr("app.services.model_lifecycle_service.calculate_readiness_metrics", 
        lambda db: {"overall_readiness": "READY_FOR_MODEL", "effective_forecasting_examples": 200})
    
    # Create the lock file
    lock_file = ModelRegistryService.model_dir() / ".training.lock"
    lock_file.touch()
    
    res = ModelLifecycleService.execute_lifecycle_trigger(db_session)
    assert res["triggered"] is False
    assert "lock is currently held" in res["reason"]
    lock_file.unlink()

def test_candidate_validation_failure_no_promotion(db_session, monkeypatch):
    monkeypatch.setattr("app.services.model_lifecycle_service.calculate_readiness_metrics", 
        lambda db: {"overall_readiness": "READY_FOR_MODEL", "effective_forecasting_examples": 200})
    
    cand = {
        "bundle": {}, "manifest_path": str(ModelRegistryService.model_dir() / "test.json"),
        "manifest": {"status": "CANDIDATE", "model_version": "v1", "metrics": {}}
    }
    monkeypatch.setattr("app.services.model_training_service.ModelTrainingService.train_candidate", lambda *args, **kwargs: cand)
    monkeypatch.setattr("app.services.model_training_service.ModelTrainingService.evaluate_promotion_gates", lambda c: (False, ["mock reason"]))
    
    res = ModelLifecycleService.execute_lifecycle_trigger(db_session)
    assert res["triggered"] is True
    assert res["promoted"] is False
    assert "mock reason" in res["reason"]

def test_insufficient_new_data_no_retraining(db_session, monkeypatch):
    monkeypatch.setattr("app.services.model_lifecycle_service.calculate_readiness_metrics", 
        lambda db: {"overall_readiness": "READY_FOR_MODEL", "effective_forecasting_examples": 200})
        
    ModelRegistryService.save_candidate({}, {"training_summary": {"examples": 190}, "status": "PROMOTED"}, "v1")
    cand = ModelRegistryService.model_dir() / "v1_test.json"
    cand.write_text(json.dumps({"training_summary": {"examples": 190}, "status": "PROMOTED"}))
    monkeypatch.setattr("app.services.model_registry_service.ModelRegistryService.load_production", lambda: {"manifest": {"training_summary": {"examples": 190}}})
    
    res = ModelLifecycleService.execute_lifecycle_trigger(db_session)
    assert res["triggered"] is False
    assert "Retraining bypassed" in res["reason"]

def test_failed_candidate_while_existing_model_exists(db_session, monkeypatch):
    # If prod model exists, evaluate_promotion_gates returns false for inferior model
    cand = {"manifest": {"status": "CANDIDATE", "metrics": {"classification": {"accuracy": 0.5, "macro_f1": 0.5}, "regression": {"mae": 100, "rmse": 100}}}}
    monkeypatch.setattr("app.services.model_registry_service.ModelRegistryService.load_production", lambda: {"manifest": {"metrics": {"classification": {"accuracy": 0.9, "macro_f1": 0.9}, "regression": {"mae": 10, "rmse": 10}}}})
    passed, reasons = ModelTrainingService.evaluate_promotion_gates(cand)
    assert passed is False
    assert any("Accuracy materially regressed" in r for r in reasons)

def test_e2e_lifecycle_trigger(db_session, monkeypatch):
    from app.models.observation import Observation
    from app.services.longitudinal_service import _upsert_panel_manifest
    
    # 1. Collection complete -> Readiness insufficient -> no training
    res1 = ModelLifecycleService.execute_lifecycle_trigger(db_session)
    assert res1["triggered"] is False
    assert "NOT satisfied" in res1["reason"]
    
    # 2. Inject ISOLATED TEST DATA that looks like real LIVE data to satisfy gates
    # We will lower thresholds to make the test fast, but keep the full flow intact
    monkeypatch.setattr("app.services.forecasting_engine_service.ForecastingEngineService.MIN_EXAMPLES", 2)
    monkeypatch.setattr("app.services.model_training_service.MIN_TRAINING_EXAMPLES", 2)
    monkeypatch.setattr("app.services.model_training_service.MIN_ROUTES", 1)
    monkeypatch.setattr("app.services.model_training_service.MIN_CLASS_SUPPORT", 0)
    monkeypatch.setattr("app.services.model_training_service.MIN_TEMPORAL_COVERAGE_DAYS", 0)
    monkeypatch.setattr("app.services.model_training_service.MIN_HOLDOUT_FRACTION", 0.3)
    
    now = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
    future_7d = dt.datetime(2026, 1, 8, 12, 0, 0, tzinfo=dt.timezone.utc)
    
    def _create(fare, search_ts, travel_dt, route):
        obs = Observation(
            total_fare=fare, data_status="OBSERVED", validation_status="ACCEPT",
            index_eligibility="ELIGIBLE", capture_method="LIVE",
            travel_date=travel_dt.date(), search_timestamp=search_ts, search_date=search_ts.date(),
            route_id=route, carrier_id="6E", observed_at=search_ts, source_id="SRC_1",
            booking_horizon_days=(travel_dt.date() - search_ts.date()).days, advance_purchase_days=10
        )
        db_session.add(obs)
        db_session.commit()
        return obs

    _create(1000, now, dt.datetime(2026, 1, 20), "R1")
    _upsert_panel_manifest(db_session, "R1", dt.date(2026, 1, 20), now.strftime("%Y-%m-%d"), now)
    _create(1100, future_7d, dt.datetime(2026, 1, 20), "R1")
    _upsert_panel_manifest(db_session, "R1", dt.date(2026, 1, 20), future_7d.strftime("%Y-%m-%d"), now)

    _create(2000, now, dt.datetime(2026, 1, 21), "R2")
    _upsert_panel_manifest(db_session, "R2", dt.date(2026, 1, 21), now.strftime("%Y-%m-%d"), now)
    _create(1900, future_7d, dt.datetime(2026, 1, 21), "R2")
    _upsert_panel_manifest(db_session, "R2", dt.date(2026, 1, 21), future_7d.strftime("%Y-%m-%d"), now)
    
    _create(3000, now, dt.datetime(2026, 1, 22), "R3")
    _upsert_panel_manifest(db_session, "R3", dt.date(2026, 1, 22), now.strftime("%Y-%m-%d"), now)
    _create(2900, future_7d, dt.datetime(2026, 1, 22), "R3")
    _upsert_panel_manifest(db_session, "R3", dt.date(2026, 1, 22), future_7d.strftime("%Y-%m-%d"), now)

    # In production ModelTrainingService uses `train_candidate` with `allow_synthetic_override=False`.
    # Since our data is labeled capture_method="LIVE", it bypasses the synthetic check naturally.
    # However, to pass the promote gates (which requires holdout data), we need enough data.
    # Let's mock evaluate_promotion_gates to pass so we don't have to build a perfectly tuned synthetic dataset
    monkeypatch.setattr("app.services.model_training_service.ModelTrainingService.evaluate_promotion_gates", lambda c: (True, []))

    # 3. Trigger -> Readiness Satisfied -> exactly one training run -> PROMOTED
    res2 = ModelLifecycleService.execute_lifecycle_trigger(db_session)
    assert res2["triggered"] is True, f"Failed to trigger: {res2.get('reason')}"
    assert res2["training_success"] is True
    assert res2["promoted"] is True
    
    # Verify the registry state
    prod = ModelRegistryService.load_production()
    assert prod is not None
    assert prod["manifest"]["status"] == "PROMOTED"
    assert prod["manifest"]["training_examples"] > 0
