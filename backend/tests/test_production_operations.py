"""AeroCPI Phase 8 Production Operations & Telemetry Tests."""
import pytest
import datetime as dt
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.observation import Observation
from app.models.index_run import IndexRun
from app.models.collection_orchestration import CollectionRun, CollectionAttempt
from app.models.longitudinal_panel import LongitudinalPanelManifest
from app.services.source_health_service import SourceHealthService
from app.services.operational_metrics_service import OperationalMetricsService
from scripts.run_daily_collection import acquire_process_lock, release_process_lock, LOCK_FILE


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()


def test_01_process_locking_prevents_overlap():
    """Verify that PID file lock prevents duplicate overlapping collector execution."""
    release_process_lock()
    try:
        assert acquire_process_lock() is True
        # Second attempt must be rejected
        assert acquire_process_lock() is False
    finally:
        release_process_lock()
        assert not LOCK_FILE.exists()


def test_02_source_health_taxonomy_separation(db_session):
    """Verify exact taxonomy distinction: IMPLEMENTED, CONFIGURED, OPERATIONAL, CURRENTLY_HEALTHY."""
    health = SourceHealthService.get_source_health_summary(db_session)
    assert health["sources_count"] >= 4
    
    sources_by_id = {s["source_id"]: s for s in health["sources"]}
    
    # Google Flights is operational
    gf = sources_by_id["SRC_GOOGLE_FLIGHTS"]
    assert gf["is_implemented"] is True
    assert gf["is_configured"] is True
    assert gf["is_operational"] is True
    
    # IndiGo NDC is implemented but not configured (missing partner credentials)
    indigo = sources_by_id["SRC_INDIGO_NDC"]
    assert indigo["is_implemented"] is True
    assert indigo["is_configured"] is False
    assert indigo["is_operational"] is False
    assert indigo["taxonomy_state"] in ["IMPLEMENTED", "UNAVAILABLE"]


def test_03_growth_metrics_and_longitudinal_readiness(db_session):
    """Verify operational growth telemetry and zero longitudinal 7-day pairs reporting."""
    now = dt.datetime.now(dt.timezone.utc)
    obs = Observation(
        observation_id="TEST_OBS_OP_1",
        total_fare=5400.0,
        data_status="OBSERVED",
        validation_status="ACCEPT",
        index_eligibility="ELIGIBLE",
        capture_method="LIVE",
        travel_date=now.date() + dt.timedelta(days=7),
        search_date=now.date(),
        search_timestamp=now,
        observed_at=now,
        booking_horizon_days=7,
        advance_purchase_days=7,
        route_id="DEL-BOM",
        carrier_id="6E",
        source_id="SRC_GOOGLE_FLIGHTS",
        currency="INR"
    )
    db_session.add(obs)
    db_session.commit()

    metrics = OperationalMetricsService.get_growth_metrics(db_session)
    assert metrics["total_observations"] == 1
    assert metrics["accepted_observations"] == 1
    assert metrics["panel"]["valid_7d_pairs"] == 0
    assert metrics["panel"]["readiness_status"] == "INSUFFICIENT_DATA"


def test_04_deterministic_operational_alerts(db_session):
    """Verify deterministic alerts without fabricated health signals."""
    alerts = OperationalMetricsService.evaluate_operational_alerts(db_session)
    alert_ids = [a["alert_id"] for a in alerts]
    
    # 0 7-day pairs must trigger info alert
    assert "ALERT_LONGITUDINAL_INSUFFICIENT_HISTORY" in alert_ids


def test_05_index_run_traceability_persisted_state_only(db_session):
    """Verify index run traceability is strictly backed by persisted DB records."""
    ir = IndexRun(
        run_id="RUN_PERSISTED_001",
        run_timestamp=dt.datetime.now(dt.timezone.utc),
        reference_period="2026-01-01",
        comparison_period="2026-01-01",
        canonical_run_fingerprint="fp_traceable_001",
        index_value=102.5
    )
    db_session.add(ir)
    db_session.commit()

    queried = db_session.query(IndexRun).filter(IndexRun.run_id == "RUN_PERSISTED_001").first()
    assert queried is not None
    assert queried.index_value == 102.5
    assert queried.canonical_run_fingerprint == "fp_traceable_001"
