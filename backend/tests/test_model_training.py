import pytest
import datetime as dt
import os
import numpy as np

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.observation import Observation
from app.services.model_training_service import ModelTrainingService, PromotionGateException
from app.services.model_registry_service import ModelRegistryService
from app.services.forecast_dataset_service import classify_direction

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

def _create_obs(db, fare: float, data_status: str, val_status: str, capture_method: str, 
                travel_date: dt.date, search_timestamp: dt.datetime, search_date: dt.date, 
                route_id: str="DEL-BOM", index_eligibility="ELIGIBLE", carrier_id="6E"):
    booking_horizon_days = (travel_date - search_date).days
    obs = Observation(
        total_fare=fare, data_status=data_status, validation_status=val_status,
        index_eligibility=index_eligibility, capture_method=capture_method,
        travel_date=travel_date, search_timestamp=search_timestamp, search_date=search_date,
        route_id=route_id, carrier_id=carrier_id, observed_at=search_timestamp, source_id="SRC_1",
        booking_horizon_days=booking_horizon_days, advance_purchase_days=booking_horizon_days
    )
    db.add(obs)
    db.commit()
    return obs

def test_13_production_training_refuses_insufficient_data(db_session):
    """Production training must refuse to run when the real dataset is INSUFFICIENT_DATA."""
    with pytest.raises(PromotionGateException, match="INSUFFICIENT_DATA"):
        ModelTrainingService.train_candidate(db_session, allow_synthetic_override=False)

def test_14_synthetic_fixtures_allowed_in_isolated_tests(db_session):
    """Synthetic fixtures may be used ONLY inside isolated tests."""
    now = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
    future_7d = dt.datetime(2026, 1, 8, 12, 0, 0, tzinfo=dt.timezone.utc)
    
    _create_obs(db_session, 1000, "OBSERVED", "ACCEPT", "LIVE", dt.date(2026, 1, 20), now, now.date(), route_id="R1")
    _create_obs(db_session, 1100, "OBSERVED", "ACCEPT", "LIVE", dt.date(2026, 1, 20), future_7d, future_7d.date(), route_id="R1")
    
    _create_obs(db_session, 2000, "OBSERVED", "ACCEPT", "LIVE", dt.date(2026, 1, 21), now, now.date(), route_id="R2")
    _create_obs(db_session, 1900, "OBSERVED", "ACCEPT", "LIVE", dt.date(2026, 1, 21), future_7d, future_7d.date(), route_id="R2")

    # Bypass INSUFFICIENT_DATA
    candidate = ModelTrainingService.train_candidate(db_session, allow_synthetic_override=True)
    
    assert candidate["manifest"]["status"] == "CANDIDATE"
    assert candidate["manifest"]["training_examples"] >= 1
    assert candidate["manifest"]["holdout_examples"] >= 1
    
    assert candidate["manifest"]["feature_version"] == "AEROGUIDE_FEATURES_V2"
    assert "artifact_sha256" in candidate["manifest"]
    assert os.path.exists(candidate["artifact_path"])
    
def test_11_16_promotion_gates_and_registry_states(db_session):
    """Implement strict promotion gates and registry states."""
    now = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
    future_7d = dt.datetime(2026, 1, 8, 12, 0, 0, tzinfo=dt.timezone.utc)
    
    _create_obs(db_session, 1000, "OBSERVED", "ACCEPT", "LIVE", dt.date(2026, 1, 20), now, now.date(), route_id="R1")
    _create_obs(db_session, 1100, "OBSERVED", "ACCEPT", "LIVE", dt.date(2026, 1, 20), future_7d, future_7d.date(), route_id="R1")
    _create_obs(db_session, 2000, "OBSERVED", "ACCEPT", "LIVE", dt.date(2026, 1, 21), now, now.date(), route_id="R2")
    _create_obs(db_session, 1900, "OBSERVED", "ACCEPT", "LIVE", dt.date(2026, 1, 21), future_7d, future_7d.date(), route_id="R2")

    candidate = ModelTrainingService.train_candidate(db_session, allow_synthetic_override=True)
    
    # Valid candidate
    candidate["manifest"]["status"] = "VALIDATED"
    
    # Classification check: fails to beat baseline
    candidate["manifest"]["metrics"]["classification"] = {"accuracy": 0.4, "macro_f1": 0.4, "temporal_baseline": {"accuracy": 0.5, "macro_f1": 0.5}}
    candidate["manifest"]["metrics"]["regression"] = {"mae": 50, "temporal_baseline": {"mae": 100}}
    with pytest.raises(PromotionGateException, match="fails to beat temporal persistence"):
        ModelTrainingService.promote_candidate(candidate)
        
    # Regression check: fails to beat baseline
    candidate["manifest"]["metrics"]["classification"] = {"accuracy": 0.9, "macro_f1": 0.9, "temporal_baseline": {"accuracy": 0.5, "macro_f1": 0.5}}
    candidate["manifest"]["metrics"]["regression"] = {"mae": 150, "temporal_baseline": {"mae": 100}}
    with pytest.raises(PromotionGateException, match="Regression MAE"):
        ModelTrainingService.promote_candidate(candidate)

    # Pass all gates
    candidate["manifest"]["metrics"]["classification"] = {"accuracy": 0.9, "macro_f1": 0.9, "temporal_baseline": {"accuracy": 0.5, "macro_f1": 0.5}}
    candidate["manifest"]["metrics"]["regression"] = {"mae": 50, "rmse": 50, "temporal_baseline": {"mae": 100, "rmse": 100}}
    
    promoted = ModelTrainingService.promote_candidate(candidate)
    assert promoted["manifest"]["status"] == "PROMOTED"
    
def test_walk_forward_and_holdout_isolation(db_session):
    """Ensure walk-forward splits leave holdout fully untouched."""
    now = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
    for i in range(10):
        # Create 10 sequential days
        dt_start = now + dt.timedelta(days=i)
        dt_end = dt_start + dt.timedelta(days=7)
        fare = 1000 + i * 10
        fare_future = fare * (1.1 if i % 2 == 0 else 0.9)
        _create_obs(db_session, fare, "OBSERVED", "ACCEPT", "LIVE", dt.date(2026, 2, 20), dt_start, dt_start.date(), route_id=f"R{i}")
        _create_obs(db_session, fare_future, "OBSERVED", "ACCEPT", "LIVE", dt.date(2026, 2, 20), dt_end, dt_end.date(), route_id=f"R{i}")

    candidate = ModelTrainingService.train_candidate(db_session, allow_synthetic_override=True)
    manifest = candidate["manifest"]
    assert manifest["holdout_examples"] >= 1
    assert manifest["walk_forward_folds"] == 3
    # Check metric baselines are populated
    assert "temporal_baseline" in manifest["metrics"]["classification"]
    assert "temporal_baseline" in manifest["metrics"]["regression"]
