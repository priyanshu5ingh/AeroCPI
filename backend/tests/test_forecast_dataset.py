import pytest
import datetime as dt
import hashlib
import json
import statistics
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.observation import Observation
from app.services.forecast_dataset_service import ForecastDatasetService
from app.services.production_data_policy import ProductionDataPolicy
from scripts.build_dataset import build_dataset_and_manifest

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def _create_obs(db: Session, fare: float, data_status: str, val_status: str, capture_method: str, 
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

def test_1_and_2_synthetic_rejected_exclusion(db_session: Session):
    """
    1. synthetic observations cannot enter the final dataset
    2. rejected observations cannot enter
    """
    now = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
    t_date = dt.date(2026, 1, 20)
    
    # Valid
    _create_obs(db_session, 1000, "OBSERVED", "ACCEPT", "LIVE", t_date, now, now.date())
    
    # Synthetic
    _create_obs(db_session, 1100, "SYNTHETIC", "ACCEPT", "SYNTHETIC", t_date, now, now.date())
    
    # Rejected
    _create_obs(db_session, 1200, "OBSERVED", "REJECT", "LIVE", t_date, now, now.date())

    obs = ForecastDatasetService.load_observations(db_session)
    assert len(obs) == 1
    assert obs[0].total_fare == 1000

def test_3_and_4_future_leakage_and_target_separation(db_session: Session):
    """
    3. future observations cannot enter features
    4. target observations are separated from feature observations
    """
    now = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
    future_7d = dt.datetime(2026, 1, 8, 12, 0, 0, tzinfo=dt.timezone.utc)
    future_10d = dt.datetime(2026, 1, 11, 12, 0, 0, tzinfo=dt.timezone.utc)
    t_date = dt.date(2026, 1, 20)
    
    _create_obs(db_session, 1000, "OBSERVED", "ACCEPT", "LIVE", t_date, now, now.date())
    _create_obs(db_session, 1500, "OBSERVED", "ACCEPT", "LIVE", t_date, future_7d, future_7d.date())
    _create_obs(db_session, 2000, "OBSERVED", "ACCEPT", "LIVE", t_date, future_10d, future_10d.date())
    
    examples = ForecastDatasetService.build_examples(db_session, horizon_days=7)
    
    # Should only create one target pair: 1st -> 8th (which is 7 days)
    assert len(examples) == 1
    ex = examples[0]
    
    assert ex["current_fare"] == 1000.0
    assert ex["future_fare"] == 1500.0
    
    # Ensure features don't see 1500 or 2000
    features = ex["features"]
    assert features["current_fare"] == 1000.0
    assert features["route_max"] == 1000.0 # Must not see the future 1500 or 2000
    
def test_5_duplicate_trajectories_deterministic(db_session: Session):
    """
    5. duplicate trajectories are deterministic
    """
    now1 = dt.datetime(2026, 1, 1, 10, 0, 0, tzinfo=dt.timezone.utc)
    now2 = dt.datetime(2026, 1, 1, 14, 0, 0, tzinfo=dt.timezone.utc)
    
    t_date = dt.date(2026, 1, 20)
    
    _create_obs(db_session, 1000, "OBSERVED", "ACCEPT", "LIVE", t_date, now1, now1.date(), carrier_id="6E")
    _create_obs(db_session, 1200, "OBSERVED", "ACCEPT", "LIVE", t_date, now2, now2.date(), carrier_id="UK")
    
    # It takes the median of fares on that search date: (1000+1200)/2 = 1100
    # And timestamp is max(now1, now2) = now2
    
    future_7d = dt.datetime(2026, 1, 8, 12, 0, 0, tzinfo=dt.timezone.utc)
    _create_obs(db_session, 1500, "OBSERVED", "ACCEPT", "LIVE", t_date, future_7d, future_7d.date())
    
    examples = ForecastDatasetService.build_examples(db_session, horizon_days=7)
    assert len(examples) == 1
    ex = examples[0]
    assert ex["current_fare"] == 1100.0
    assert ex["prediction_timestamp"] == now2.isoformat().replace("+00:00", "Z") if ex.get("prediction_timestamp", "").endswith("Z") else now2.isoformat()

def test_6_target_labels_deterministic(db_session: Session):
    """
    6. target labels are deterministic
    """
    from app.services.forecast_dataset_service import classify_direction, TARGET_THRESHOLD_PCT
    assert classify_direction(TARGET_THRESHOLD_PCT + 0.1) == "UP"
    assert classify_direction(TARGET_THRESHOLD_PCT - 0.1) == "STABLE"
    assert classify_direction(-TARGET_THRESHOLD_PCT + 0.1) == "STABLE"
    assert classify_direction(-TARGET_THRESHOLD_PCT - 0.1) == "DOWN"

def test_7_missing_evidence_excluded(db_session: Session):
    """
    7. missing evidence results in exclusion/NO_DATA
    """
    now = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
    t_date = dt.date(2026, 1, 20)
    
    # No fare
    obs = _create_obs(db_session, 0, "OBSERVED", "ACCEPT", "LIVE", t_date, now, now.date())
    obs.total_fare = 0.0
    db_session.commit()
    
    examples = ForecastDatasetService.build_examples(db_session, horizon_days=7)
    assert len(examples) == 0

def test_8_9_10_dataset_manifest_integrity(monkeypatch):
    """
    8. dataset manifest counts equal actual rows
    9. dataset fingerprint changes when eligible source data changes
    10. same source database + same configuration produces the same dataset
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    monkeypatch.setattr('scripts.build_dataset.SessionLocal', lambda: db)
    
    now = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
    future_7d = dt.datetime(2026, 1, 8, 12, 0, 0, tzinfo=dt.timezone.utc)
    t_date = dt.date(2026, 1, 20)
    
    _create_obs(db, 1000, "OBSERVED", "ACCEPT", "LIVE", t_date, now, now.date())
    _create_obs(db, 1500, "OBSERVED", "ACCEPT", "LIVE", t_date, future_7d, future_7d.date())
    
    manifest1 = build_dataset_and_manifest()
    
    # Check 8 (counts equal actual rows)
    assert manifest1["dataset_row_count"] == 1
    assert manifest1["7_day_pair_count"] == 1
    
    # Check 10 (same output on second run)
    manifest2 = build_dataset_and_manifest()
    assert manifest1["fingerprint_sha256"] == manifest2["fingerprint_sha256"]
    
    # Check 9 (fingerprint changes on new data)
    _create_obs(db, 1200, "OBSERVED", "ACCEPT", "LIVE", dt.date(2026, 2, 20), now, now.date(), route_id="BLR-DEL")
    _create_obs(db, 1800, "OBSERVED", "ACCEPT", "LIVE", dt.date(2026, 2, 20), future_7d, future_7d.date(), route_id="BLR-DEL")
    
    manifest3 = build_dataset_and_manifest()
    assert manifest3["dataset_row_count"] == 2
    assert manifest1["fingerprint_sha256"] != manifest3["fingerprint_sha256"]
    
    db.close()
