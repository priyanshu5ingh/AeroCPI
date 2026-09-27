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
    cand = {"manifest": {"status": "CANDIDATE", "metrics": {"classification": {"accuracy": 0.5}, "regression": {"mae": 100}}}}
    monkeypatch.setattr("app.services.model_registry_service.ModelRegistryService.load_production", lambda: {"manifest": {"metrics": {"classification": {"accuracy": 0.9}, "regression": {"mae": 10}}}})
    passed, reasons = ModelTrainingService.evaluate_promotion_gates(cand)
    assert passed is False
    assert any("is worse than current production" in r for r in reasons)
