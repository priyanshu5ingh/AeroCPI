import pytest
import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.observation import Observation
from app.models.index_run import IndexRun
from app.services.forecast_dataset_service import ForecastDatasetService
from app.services.model_registry_service import ModelRegistryService

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
        booking_horizon_days=booking_horizon_days, advance_purchase_days=booking_horizon_days,
        currency="INR"
    )
    db.add(obs)
    db.commit()
    return obs

def test_restored_leakage_audit(db_session):
    """
    Prove that changing observations strictly AFTER prediction_timestamp cannot alter:
    - route aggregates
    - national AeroCPI index feature
    - target-independent features
    Using actual public interface (build_examples).
    """
    past = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
    prediction = dt.datetime(2026, 1, 5, 12, 0, 0, tzinfo=dt.timezone.utc)
    future = dt.datetime(2026, 1, 12, 12, 0, 0, tzinfo=dt.timezone.utc)
    travel_date = dt.date(2026, 1, 25)

    # 1. Setup PAST index run (Index = 100.0)
    ir1 = IndexRun(
        run_timestamp=past,
        reference_period="2026-01-01",
        comparison_period="2026-01-01",
        canonical_run_fingerprint="past_run",
        index_value=100.0
    )
    db_session.add(ir1)
    
    # 2. Setup FUTURE index run (Index = 150.0)
    ir2 = IndexRun(
        run_timestamp=future,
        reference_period="2026-01-01",
        comparison_period="2026-01-01",
        canonical_run_fingerprint="future_run",
        index_value=150.0
    )
    db_session.add(ir2)

    # 3. Create Current Observation (at prediction_timestamp)
    obs_current = _create_obs(
        db_session, 5000.0, "OBSERVED", "ACCEPT", "LIVE", 
        travel_date, prediction, prediction.date()
    )
    
    # 4. Create Future Observation (The Target)
    obs_future = _create_obs(
        db_session, 6000.0, "OBSERVED", "ACCEPT", "LIVE", 
        travel_date, future, future.date()
    )

    # 5. Extract via ForecastDatasetService
    examples = ForecastDatasetService.build_examples(db_session, horizon_days=7)
    assert len(examples) == 1
    
    ex = examples[0]
    
    # Target should be exactly delta between 5000 and 6000
    assert ex["target_delta_pct"] == 20.0
    
    # The national index feature must strictly be 100.0 (past run), NOT 150.0 (future run)
    assert ex["features"]["national_aerocpi_index"] == 100.0
    
    # The rolling statistics / aggregates should NOT peek at the 6000 fare
    # e.g., the route fare median at `prediction` should just be 5000 (since it's the only one <= prediction)
    assert ex["features"]["fare_to_median_ratio"] == 1.0
