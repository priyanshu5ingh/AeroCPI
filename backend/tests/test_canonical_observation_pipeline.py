import pytest
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from decimal import Decimal

# Add repository root to sys.path
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.schemas.observation import RawQuoteInput
from app.services.canonical_normalization_service import CanonicalNormalizationService, classify_booking_horizon
from app.validation.canonical_validation_rules import CanonicalValidationRules
from app.services.observation_service import ObservationService
from app.models.observation import Observation

def test_valid_observation_accept(db_session):
    """Test 1: Valid quote maps to ACCEPT validation status."""
    raw_input = RawQuoteInput(
        source_id="SRC_MAKE_MY_TRIP",
        source_name="MakeMyTrip",
        source_url="https://www.makemytrip.com",
        search_date=date(2026, 9, 1),
        travel_date=date(2026, 9, 16),
        origin_raw="Delhi",
        destination_raw="Mumbai (Mumbai)",
        airline="6E",
        flight_number="6E-204",
        cabin="ECONOMY",
        fare_class="STANDARD",
        stops=0,
        duration_minutes=130,
        raw_total_fare="₹5,312 incl. taxes",
        base_fare=4500.0,
        taxes=812.0,
        fees=0.0,
        total_fare=5312.0,
        currency="INR"
    )

    obs = ObservationService.ingest_raw_quote(db_session, raw_input)
    assert obs.validation_status == "ACCEPT"
    assert obs.route_id == "DEL-BOM"
    assert obs.origin_airport == "DEL"
    assert obs.destination_airport == "BOM"
    assert obs.advance_purchase_days == 15
    assert obs.horizon_code == "T+15"
    assert obs.basket_status == "BASKET_MEMBER"


def test_negative_fare_reject(db_session):
    """Test 2: Negative total fare maps to REJECT."""
    raw_input = RawQuoteInput(
        source_id="SRC_GOIBIBO",
        search_date=date(2026, 9, 1),
        travel_date=date(2026, 9, 16),
        origin_raw="Delhi",
        destination_raw="Mumbai",
        airline="6E",
        total_fare=-500.0,
        currency="INR"
    )

    obs = ObservationService.ingest_raw_quote(db_session, raw_input)
    assert obs.validation_status == "REJECT"
    assert "REJECT_TOTAL_FARE_NON_POSITIVE" in obs.validation_reasons


def test_zero_fare_reject(db_session):
    """Test 3: Zero total fare maps to REJECT."""
    raw_input = RawQuoteInput(
        source_id="SRC_GOIBIBO",
        search_date=date(2026, 9, 1),
        travel_date=date(2026, 9, 16),
        origin_raw="Delhi",
        destination_raw="Mumbai",
        airline="6E",
        total_fare=0.0,
        currency="INR"
    )

    obs = ObservationService.ingest_raw_quote(db_session, raw_input)
    assert obs.validation_status == "REJECT"
    assert "REJECT_TOTAL_FARE_NON_POSITIVE" in obs.validation_reasons


def test_negative_tax_reject(db_session):
    """Test 4: Negative tax component maps to REJECT."""
    raw_input = RawQuoteInput(
        source_id="SRC_AIRLINE_DIRECT",
        search_date=date(2026, 9, 1),
        travel_date=date(2026, 9, 16),
        origin_raw="Delhi",
        destination_raw="Mumbai",
        airline="6E",
        base_fare=5000.0,
        taxes=-100.0,
        fees=0.0,
        total_fare=4900.0,
        currency="INR"
    )

    obs = ObservationService.ingest_raw_quote(db_session, raw_input)
    assert obs.validation_status == "REJECT"
    assert "REJECT_NEGATIVE_FARE_COMPONENT" in obs.validation_reasons


def test_travel_date_before_search_date_reject(db_session):
    """Test 5: Travel date before search date (advance_purchase < 0) maps to REJECT."""
    raw_input = RawQuoteInput(
        source_id="SRC_YATRA",
        search_date=date(2026, 9, 15),
        travel_date=date(2026, 9, 1),
        origin_raw="Delhi",
        destination_raw="Mumbai",
        airline="UK",
        total_fare=6000.0,
        currency="INR"
    )

    obs = ObservationService.ingest_raw_quote(db_session, raw_input)
    assert obs.validation_status == "REJECT"
    assert "REJECT_TRAVEL_BEFORE_SEARCH" in obs.validation_reasons
    assert obs.advance_purchase_days == -14


def test_same_origin_destination_reject(db_session):
    """Test 6: Same origin and destination airport maps to REJECT."""
    raw_input = RawQuoteInput(
        source_id="SRC_YATRA",
        search_date=date(2026, 9, 1),
        travel_date=date(2026, 9, 16),
        origin_raw="New Delhi",
        destination_raw="Delhi Airport",
        airline="6E",
        total_fare=4500.0,
        currency="INR"
    )

    obs = ObservationService.ingest_raw_quote(db_session, raw_input)
    assert obs.validation_status == "REJECT"
    assert "REJECT_SAME_ORIGIN_DESTINATION" in obs.validation_reasons


def test_invalid_currency_reject_and_auditable_preservation(db_session):
    """Test 7: Currency USD maps to REJECT but is preserved in DB for auditability."""
    raw_input = RawQuoteInput(
        source_id="SRC_EXPEDIA_US",
        search_date=date(2026, 9, 1),
        travel_date=date(2026, 9, 16),
        origin_raw="Delhi",
        destination_raw="Mumbai",
        airline="AI",
        total_fare=75.0,
        currency="USD"
    )

    obs = ObservationService.ingest_raw_quote(db_session, raw_input)
    assert obs.validation_status == "REJECT"
    assert "REJECT_UNSUPPORTED_CURRENCY" in obs.validation_reasons
    assert obs.currency == "USD"
    assert obs.total_fare == 75.0


def test_route_outside_basket_flag(db_session):
    """Test 8: Valid canonical route DEL-PNQ outside Top 10 basket maps to FLAG."""
    raw_input = RawQuoteInput(
        source_id="SRC_MAKE_MY_TRIP",
        search_date=date(2026, 9, 1),
        travel_date=date(2026, 9, 16),
        origin_raw="Delhi",
        destination_raw="Pune",
        airline="6E",
        total_fare=4200.0,
        currency="INR"
    )

    obs = ObservationService.ingest_raw_quote(db_session, raw_input)
    assert obs.validation_status == "FLAG"
    assert "FLAG_ROUTE_OUTSIDE_REFERENCE_BASKET" in obs.validation_reasons
    assert obs.route_id == "DEL-PNQ"
    assert obs.route_mapping_status == "CANONICAL_MAPPED"
    assert obs.basket_status == "ROUTE_OUTSIDE_REFERENCE_BASKET"


def test_missing_tax_breakdown_flag(db_session):
    """Test 9: Missing base fare and tax breakdown maps to FLAG_MISSING_FARE_COMPONENT_BREAKDOWN."""
    raw_input = RawQuoteInput(
        source_id="SRC_MAKE_MY_TRIP",
        search_date=date(2026, 9, 1),
        travel_date=date(2026, 9, 16),
        origin_raw="Delhi",
        destination_raw="Mumbai",
        airline="6E",
        total_fare=5312.0,
        currency="INR"
    )

    obs = ObservationService.ingest_raw_quote(db_session, raw_input)
    assert obs.validation_status == "FLAG"
    assert "FLAG_MISSING_FARE_COMPONENT_BREAKDOWN" in obs.validation_reasons
    assert obs.breakdown_status == "TOTAL_ONLY"


def test_fare_arithmetic_mismatch_flag(db_session):
    """Test 10: Fare component sum mismatch maps to FLAG_ARITHMETIC_MISMATCH."""
    raw_input = RawQuoteInput(
        source_id="SRC_MAKE_MY_TRIP",
        search_date=date(2026, 9, 1),
        travel_date=date(2026, 9, 16),
        origin_raw="Delhi",
        destination_raw="Mumbai",
        airline="6E",
        base_fare=4000.0,
        taxes=500.0,
        fees=100.0,
        total_fare=9999.0, # Mismatch vs expected 4600
        currency="INR"
    )

    obs = ObservationService.ingest_raw_quote(db_session, raw_input)
    assert obs.validation_status == "FLAG"
    assert "FLAG_ARITHMETIC_MISMATCH" in obs.validation_reasons
    assert obs.arithmetic_status == "ARITHMETIC_MISMATCH"


def test_advance_purchase_calculation_correct():
    """Test 11: Advance purchase days calculation and explicit horizon classification."""
    q_dict = {
        "source_id": "SRC_TEST",
        "search_date": "2026-09-01",
        "travel_date": "2026-09-08",
        "origin_raw": "Delhi",
        "destination_raw": "Mumbai",
        "total_fare": 5000.0
    }
    canon = CanonicalNormalizationService.normalize_raw_quote(q_dict)
    assert canon["advance_purchase_days"] == 7
    assert canon["horizon_code"] == "T+7"

    # Non-standard lead time
    q_dict2 = {
        "source_id": "SRC_TEST",
        "search_date": "2026-09-01",
        "travel_date": "2026-09-13",
        "origin_raw": "Delhi",
        "destination_raw": "Mumbai",
        "total_fare": 5000.0
    }
    canon2 = CanonicalNormalizationService.normalize_raw_quote(q_dict2)
    assert canon2["advance_purchase_days"] == 12
    assert canon2["horizon_code"] == "OFF_HORIZON"


def test_raw_values_preserved():
    """Test 12: Raw strings are explicitly preserved without loss of source text."""
    q_dict = {
        "source_id": "SRC_TEST",
        "search_date": "2026-09-01",
        "travel_date": "2026-09-16",
        "origin_raw": "New Delhi (DEL)",
        "destination_raw": "Chhatrapati Shivaji Maharaj Bombay",
        "raw_total_fare": "₹5,312.50 inclusive of GST",
        "total_fare": 5312.50
    }
    canon = CanonicalNormalizationService.normalize_raw_quote(q_dict)
    assert canon["origin_raw"] == "New Delhi (DEL)"
    assert canon["destination_raw"] == "Chhatrapati Shivaji Maharaj Bombay"
    assert canon["raw_total_fare"] == "₹5,312.50 inclusive of GST"
    assert canon["origin_airport"] == "DEL"
    assert canon["destination_airport"] == "BOM"


def test_normalized_route_mapping_correct():
    """Test 13: Mapping of raw city names to canonical IATA codes and routes."""
    q_dict = {
        "source_id": "SRC_TEST",
        "search_date": "2026-09-01",
        "travel_date": "2026-09-16",
        "origin_raw": "Bangalore",
        "destination_raw": "Calcutta",
        "total_fare": 4800.0
    }
    canon = CanonicalNormalizationService.normalize_raw_quote(q_dict)
    assert canon["origin_airport"] == "BLR"
    assert canon["destination_airport"] == "CCU"
    assert canon["route_id"] == "BLR-CCU"
    assert canon["basket_status"] == "BASKET_MEMBER"


def test_observation_payload_hash_deterministic():
    """Test 14: SHA-256 payload hash is deterministic."""
    q_dict = {"source_id": "SRC_TEST", "search_date": "2026-09-01", "travel_date": "2026-09-16", "total_fare": 5000.0}
    c1 = CanonicalNormalizationService.normalize_raw_quote(q_dict)
    c2 = CanonicalNormalizationService.normalize_raw_quote(q_dict)

    assert c1["raw_payload_hash"] == c2["raw_payload_hash"]
    assert len(c1["raw_payload_hash"]) == 64


test_stops_null_when_missing_cases = [
    (None, None, "MISSING"),
    (0, 0, "OBSERVED"),
    (1, 1, "OBSERVED")
]

@pytest.mark.parametrize("input_stops, expected_stops, expected_status", test_stops_null_when_missing_cases)
def test_stops_null_when_missing(input_stops, expected_stops, expected_status):
    """Test 15: stops is NULL when missing, and 0 only when non-stop is explicitly observed."""
    q_dict = {
        "source_id": "SRC_TEST",
        "search_date": "2026-09-01",
        "travel_date": "2026-09-16",
        "stops": input_stops,
        "total_fare": 5000.0
    }
    canon = CanonicalNormalizationService.normalize_raw_quote(q_dict)
    assert canon["stops"] == expected_stops
    assert canon["stops_status"] == expected_status


def test_api_ingest_raw_quote_endpoint(client):
    """Test 16: API Endpoint POST /api/v1/observations/ingest-raw returns 201 CREATED and CanonicalObservationResponse."""
    payload = {
        "source_id": "SRC_API_TEST",
        "source_name": "API Test Source",
        "search_date": "2026-09-01",
        "travel_date": "2026-09-16",
        "origin_raw": "Delhi",
        "destination_raw": "Mumbai",
        "airline": "6E",
        "flight_number": "6E-501",
        "base_fare": 4000.0,
        "taxes": 500.0,
        "fees": 100.0,
        "total_fare": 4600.0,
        "currency": "INR"
    }

    res = client.post("/api/v1/observations/ingest-raw", json=payload)
    assert res.status_code == 201
    data = res.json()

    assert data["observation_id"] is not None
    assert data["validation_status"] == "ACCEPT"
    assert data["route_id"] == "DEL-BOM"
    assert data["advance_purchase_days"] == 15
    assert data["horizon_code"] == "T+15"
    assert data["breakdown_status"] == "COMPLETE_BREAKDOWN"
    assert data["arithmetic_status"] == "ARITHMETIC_MATCH"


def test_search_timestamp_authoritative_and_misleading_days_left_ignored(db_session):
    """Test 17: search_timestamp is authoritative, advance_purchase_days is derived strictly from it, ignoring misleading days_left."""
    raw_input = RawQuoteInput(
        source_id="SRC_TEST_SEARCH_TS",
        source_name="Search TS Test",
        search_timestamp=datetime(2026, 9, 1, 14, 30, 0, tzinfo=timezone.utc),
        travel_date=date(2026, 9, 16),
        origin_raw="Delhi",
        destination_raw="Mumbai",
        airline="6E",
        flight_number="6E-204",
        total_fare=5312.0,
        currency="INR"
    )

    # Ingest quote payload with a misleading 'days_left' field in raw dictionary
    raw_dict = raw_input.model_dump()
    raw_dict["days_left"] = 10 # Misleading raw field from third-party source

    canon = CanonicalNormalizationService.normalize_raw_quote(raw_dict)
    assert canon["search_timestamp"] == datetime(2026, 9, 1, 14, 30, 0, tzinfo=timezone.utc)
    assert canon["search_date"] == date(2026, 9, 1)
    # 2026-09-16 minus 2026-09-01 = 15 days (NOT 10 from days_left!)
    assert canon["advance_purchase_days"] == 15

    obs = ObservationService.ingest_raw_quote(db_session, raw_input)
    assert obs.search_timestamp.replace(tzinfo=timezone.utc) == datetime(2026, 9, 1, 14, 30, 0, tzinfo=timezone.utc)
    assert obs.search_date == date(2026, 9, 1)
    assert obs.advance_purchase_days == 15


def test_missing_fare_components_remain_null_in_db(db_session):
    """Test 18: Missing base_fare, taxes, fees remain NULL in database without manufacturing 0.0 defaults."""
    raw_input = RawQuoteInput(
        source_id="SRC_TOTAL_ONLY_TEST",
        source_name="Total Only Test",
        search_date=date(2026, 9, 1),
        travel_date=date(2026, 9, 16),
        origin_raw="Delhi",
        destination_raw="Mumbai",
        airline="6E",
        flight_number="6E-555",
        total_fare=5000.0,
        currency="INR"
    )

    obs = ObservationService.ingest_raw_quote(db_session, raw_input)
    assert obs.total_fare == Decimal("5000.00")
    assert obs.base_fare is None
    assert obs.taxes is None
    assert obs.fees is None
    assert obs.mandatory_fees is None
    assert obs.breakdown_status == "TOTAL_ONLY"
    assert obs.validation_status == "FLAG"
    assert "FLAG_MISSING_FARE_COMPONENT_BREAKDOWN" in obs.validation_reasons

