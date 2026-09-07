import pytest
from datetime import date, datetime, timezone
from pydantic import ValidationError
from app.schemas.observation import ObservationCreate
from app.schemas.route import RouteCreate
from app.schemas.virtual_trip import VirtualTripCreate
from app.schemas.common import DataStatus

def test_negative_fare_rejection():
    with pytest.raises(ValidationError) as excinfo:
        ObservationCreate(
            source_id="INDIGO_DIRECT",
            route_id="DEL-BOM",
            carrier_id="6E",
            travel_date=date(2026, 9, 15),
            observed_at=datetime.now(timezone.utc),
            booking_horizon_days=7,
            base_fare=-1000.0,
            taxes=500.0,
            mandatory_fees=200.0,
            total_fare=-300.0,
            currency="INR"
        )
    assert "base_fare" in str(excinfo.value) or "negative" in str(excinfo.value)

def test_invalid_booking_horizon_rejection():
    with pytest.raises(ValidationError) as excinfo:
        ObservationCreate(
            source_id="INDIGO_DIRECT",
            route_id="DEL-BOM",
            carrier_id="6E",
            travel_date=date(2026, 9, 15),
            observed_at=datetime.now(timezone.utc),
            booking_horizon_days=60, # T+60 is invalid, core SIH lead times are 1, 7, 15, 30, 45
            base_fare=4000.0,
            taxes=500.0,
            mandatory_fees=200.0,
            total_fare=4700.0,
            currency="INR"
        )
    assert "booking_horizon_days" in str(excinfo.value)

def test_same_origin_destination_rejection():
    with pytest.raises(ValidationError) as excinfo:
        RouteCreate(
            route_id="DEL-DEL",
            origin_code="DEL",
            destination_code="DEL"
        )
    assert "Origin and destination airport codes cannot be the same" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo_vt:
        VirtualTripCreate(
            origin="BOM",
            destination="BOM",
            travel_date=date(2026, 9, 20),
            booking_horizon=15
        )
    assert "Origin and destination cannot be the same" in str(excinfo_vt.value)

def test_inconsistent_currency_rejection():
    with pytest.raises(ValidationError) as excinfo:
        ObservationCreate(
            source_id="INDIGO_DIRECT",
            route_id="DEL-BOM",
            carrier_id="6E",
            travel_date=date(2026, 9, 15),
            observed_at=datetime.now(timezone.utc),
            booking_horizon_days=7,
            base_fare=4000.0,
            taxes=500.0,
            mandatory_fees=200.0,
            total_fare=4700.0,
            currency="USD" # Reject non-INR / silent conversions
        )
    # Currency must be INR for domestic AeroCPI in milestone 1
    # Test normalization service currency check
    from app.models.observation import Observation
    from app.services.normalization_service import NormalizationService
    obs_usd = Observation(
        observation_id="test-usd",
        source_id="INDIGO_DIRECT",
        route_id="DEL-BOM",
        carrier_id="6E",
        travel_date=date(2026, 9, 15),
        observed_at=datetime.now(timezone.utc),
        booking_horizon_days=7,
        base_fare=100.0,
        taxes=10.0,
        mandatory_fees=5.0,
        total_fare=115.0,
        currency="USD"
    )
    with pytest.raises(ValueError) as val_exc:
        NormalizationService.normalize_observation(obs_usd)
    assert "Unsupported currency 'USD'" in str(val_exc.value)

def test_data_status_validation():
    # Valid status
    obs_valid = ObservationCreate(
        source_id="SYNTHETIC_SIMULATOR",
        route_id="BLR-DEL",
        carrier_id="AI",
        travel_date=date(2026, 9, 15),
        observed_at=datetime.now(timezone.utc),
        booking_horizon_days=30,
        base_fare=5000.0,
        taxes=600.0,
        mandatory_fees=400.0,
        total_fare=6000.0,
        currency="INR",
        data_status=DataStatus.SYNTHETIC
    )
    assert obs_valid.data_status == DataStatus.SYNTHETIC

    # Invalid status
    with pytest.raises(ValidationError):
        ObservationCreate(
            source_id="SYNTHETIC_SIMULATOR",
            route_id="BLR-DEL",
            carrier_id="AI",
            travel_date=date(2026, 9, 15),
            observed_at=datetime.now(timezone.utc),
            booking_horizon_days=30,
            base_fare=5000.0,
            taxes=600.0,
            mandatory_fees=400.0,
            total_fare=6000.0,
            currency="INR",
            data_status="INVALID_STATUS"
        )
