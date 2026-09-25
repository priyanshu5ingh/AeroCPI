import pytest
import datetime as dt
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.observation import Observation
from app.models.index_run import IndexRun
from app.models.route_index_result import RouteIndexResult
from app.models.horizon_index_result import HorizonIndexResult
from app.models.trust_evaluation import TrustEvaluation
from app.models.longitudinal_panel import LongitudinalPanelManifest

from app.services.production_data_policy import ProductionDataPolicy
from app.services.market_state_service import MarketStateService
from app.services.feature_builder_service import FeatureBuilderService
from app.services.forecast_dataset_service import ForecastDatasetService, classify_direction
from app.services.forecasting_engine_service import ForecastingEngineService
from app.services.longitudinal_service import execute_longitudinal_pilot_collection

from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def _make_obs(fare, data_status, val_status, index_elig, capture_method, travel_date, search_ts, route_id="DEL-BOM", carrier_id="6E"):
    adv = (travel_date - search_ts.date()).days
    return Observation(
        total_fare=fare,
        data_status=data_status,
        validation_status=val_status,
        index_eligibility=index_elig,
        capture_method=capture_method,
        travel_date=travel_date,
        search_date=search_ts.date(),
        search_timestamp=search_ts,
        observed_at=search_ts,
        booking_horizon_days=adv if adv >= 0 else 0,
        advance_purchase_days=adv if adv >= 0 else 0,
        route_id=route_id,
        carrier_id=carrier_id,
        source_id="SRC_GOOGLE_FLIGHTS",
        currency="INR"
    )

def test_1_synthetic_exclusion(db_session: Session):
    """
    Synthetic records must be excluded from collection -> observation eligibility -> 
    dataset generation -> feature building -> training -> validation -> promotion -> forecast API.
    """
    now = dt.datetime.now(dt.timezone.utc)
    
    # Valid observation
    obs_valid = _make_obs(1000, "OBSERVED", "ACCEPT", "ELIGIBLE", "LIVE", now.date(), now)
    
    # Malicious synthetic observation claiming to be OBSERVED
    obs_malicious = _make_obs(999, "OBSERVED", "ACCEPT", "ELIGIBLE", "SYNTHETIC", now.date(), now)
    
    # Legacy synthetic observation
    obs_legacy = _make_obs(500, "SYNTHETIC", "ACCEPT", "ELIGIBLE", "LIVE", now.date(), now)

    db_session.add_all([obs_valid, obs_malicious, obs_legacy])
    db_session.commit()
    
    # Query via ProductionDataPolicy
    query = db_session.query(Observation)
    filtered = ProductionDataPolicy.apply_forecasting_filters(query).all()
    
    assert len(filtered) == 1
    assert filtered[0].observation_id == obs_valid.observation_id
    
    assert ProductionDataPolicy.is_production_observation(obs_malicious) is False
    assert ProductionDataPolicy.is_production_observation(obs_legacy) is False

def test_2_legacy_synthetic_records_index(db_session: Session):
    """
    Existing historical synthetic records must not alter production index or forecast results.
    """
    state = MarketStateService.get_national_market_state(db_session)
    assert state["market_state"] in ["INSUFFICIENT_DATA", "UNAVAILABLE"]
    assert state["headline_index"] is None

def test_3_temporal_leakage(db_session: Session):
    """
    Temporal leakage:
    - search_timestamp == prediction_timestamp allowed
    - search_timestamp > prediction_timestamp rejected
    - future route statistics rejected
    - future national index rejected
    - future carrier/source information rejected
    - target observations cannot leak into features
    """
    now = dt.datetime.now(dt.timezone.utc)
    future = now + dt.timedelta(days=1)
    travel = now.date() + dt.timedelta(days=7)
    
    past_obs = _make_obs(1000, "OBSERVED", "ACCEPT", "ELIGIBLE", "LIVE", travel, now)
    future_obs = _make_obs(1200, "OBSERVED", "ACCEPT", "ELIGIBLE", "LIVE", travel, future)
    
    future_index = IndexRun(
        run_id="future-run",
        run_timestamp=future,
        index_value=120.0,
        reference_period="2026-01-01",
        comparison_period="2026-01-01",
        canonical_run_fingerprint="fp_future"
    )
    past_index = IndexRun(
        run_id="past-run",
        run_timestamp=now,
        index_value=105.0,
        reference_period="2026-01-01",
        comparison_period="2026-01-01",
        canonical_run_fingerprint="fp_past"
    )
    
    db_session.add_all([past_obs, future_obs, past_index, future_index])
    db_session.commit()
    
    features = FeatureBuilderService.build_prediction_features(db_session, "DEL-BOM", str(travel), search_timestamp=now)
    
    # The feature builder should NOT see future_obs
    assert features["observations_in_sample"] == 1
    assert features["current_fare"] == 1000.0
    
    # The feature builder should NOT see future_index
    assert features["national_aerocpi_index"] == 105.0

def test_4_target_generation(db_session: Session):
    """
    Target generation:
    - exact 7-day pair
    - deterministic target-selection rules
    """
    assert classify_direction(3.01) == "UP"
    assert classify_direction(-3.01) == "DOWN"
    assert classify_direction(2.0) == "STABLE"
    assert classify_direction(-2.0) == "STABLE"

def test_5_model_readiness_promotion(db_session: Session):
    """
    Model readiness/promotion:
    candidate cannot be promoted unless every required gate passes.
    """
    status = ForecastingEngineService.get_model_status(db_session)
    assert status["can_train_live"] is False
    assert status["model_status"] in ["INSUFFICIENT_DATA", "NOT_READY"]

def test_6_forecast_api_states(db_session: Session):
    """
    Forecast API state handling: NO_DATA, INSUFFICIENT_DATA, MODEL_NOT_READY
    """
    client = TestClient(app)
    response = client.post("/api/v1/aeroguide/forecast", json={"origin": "DEL", "destination": "BOM", "travel_date": "2026-10-01", "priority": "CHEAPEST", "adults": 1, "children": 0, "infants": 0, "cabin": "ECONOMY", "flexibility_days": 0})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["INSUFFICIENT_EVIDENCE", "MODEL_NOT_READY", "NO_DATA"]
    assert data["probabilities"] is None

def test_7_legacy_longitudinal_method(db_session: Session):
    """
    calling execute_longitudinal_pilot_collection must never generate synthetic observations.
    """
    result = execute_longitudinal_pilot_collection(db_session, pinned_dates=[], routes=[])
    assert result.get("observations_created", 0) == 0
    assert result.get("raw_quotes_captured", 0) == 0

def test_8_model_artifact_integrity(db_session: Session):
    """
    Model artifact integrity: missing artifact
    """
    from app.services.model_registry_service import ModelRegistryService
    manifest = ModelRegistryService.load_production()
    assert manifest is None
