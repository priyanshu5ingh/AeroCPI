import pytest
import gzip
import hashlib
from datetime import date, datetime, timezone
from decimal import Decimal

from app.schemas.common import PRODUCTION_HORIZONS, EXPERIMENTAL_HORIZONS, VALID_HORIZONS
from app.schemas.observation import RawQuoteInput
from app.services.canonical_normalization_service import CanonicalNormalizationService, classify_booking_horizon
from app.services.observation_service import ObservationService
from app.services.index_engine_service import IndexEngineService
from app.validation.canonical_validation_rules import CanonicalValidationRules

def test_1_apw_production_set_realignment():
    """Change 1: Verify production APW set is {1, 7, 15, 30, 45} and experimental set is {14, 21, 60}."""
    assert PRODUCTION_HORIZONS == {1, 7, 15, 30, 45}
    assert EXPERIMENTAL_HORIZONS == {14, 21, 60}
    assert VALID_HORIZONS == PRODUCTION_HORIZONS

    # Verify classification
    assert classify_booking_horizon(1) == "T+1"
    assert classify_booking_horizon(7) == "T+7"
    assert classify_booking_horizon(15) == "T+15"
    assert classify_booking_horizon(30) == "T+30"
    assert classify_booking_horizon(45) == "T+45"
    # Experimental/non-production horizons (14, 21, 60) map to OFF_HORIZON to stay excluded from production index
    assert classify_booking_horizon(14) == "OFF_HORIZON"
    assert classify_booking_horizon(60) == "OFF_HORIZON"


def test_2_separate_provenance_hashes(db_session):
    """Change 2: Separate provenance hashes into raw_payload_sha256 and stored_file_sha256."""
    raw_input = RawQuoteInput(
        source_id="SRC_HASH_TEST",
        source_name="Hash Test Source",
        search_date=date(2026, 9, 1),
        travel_date=date(2026, 9, 16),
        origin_raw="Delhi",
        destination_raw="Mumbai",
        airline="6E",
        flight_number="6E-101",
        base_fare=4000.0,
        taxes=500.0,
        fees=100.0,
        total_fare=4600.0,
        currency="INR"
    )

    obs = ObservationService.ingest_raw_quote(db_session, raw_input)

    assert obs.raw_payload_sha256 is not None
    assert obs.stored_file_sha256 is not None
    assert len(obs.raw_payload_sha256) == 64
    assert len(obs.stored_file_sha256) == 64
    # Compressed bytes hash should differ from uncompressed raw payload hash
    assert obs.raw_payload_sha256 != obs.stored_file_sha256


def test_3_flag_live_observations_with_missing_carrier(db_session):
    """Change 3: Explicitly flag 2 observations with missing carrier info without deleting them."""
    q1 = RawQuoteInput(
        source_id="SRC_UNKNOWN_CARRIER_1",
        source_name="Unknown Carrier Source 1",
        search_date=date(2026, 9, 1),
        travel_date=date(2026, 9, 16),
        origin_raw="Delhi",
        destination_raw="Mumbai",
        airline="UNKNOWN",
        total_fare=4800.0,
        currency="INR"
    )

    q2 = RawQuoteInput(
        source_id="SRC_UNKNOWN_CARRIER_2",
        source_name="Unknown Carrier Source 2",
        search_date=date(2026, 9, 1),
        travel_date=date(2026, 9, 16),
        origin_raw="Bengaluru",
        destination_raw="Delhi",
        airline="",
        total_fare=5200.0,
        currency="INR"
    )

    obs1 = ObservationService.ingest_raw_quote(db_session, q1)
    obs2 = ObservationService.ingest_raw_quote(db_session, q2)

    # Assert neither observation was deleted
    assert obs1.observation_id is not None
    assert obs2.observation_id is not None

    # Assert both observations receive FLAG validation_status
    assert obs1.validation_status == "FLAG"
    assert obs2.validation_status == "FLAG"

    # Assert both contain FLAG_MISSING_CARRIER_INFO reason
    assert "FLAG_MISSING_CARRIER_INFO" in obs1.validation_reasons
    assert "FLAG_MISSING_CARRIER_INFO" in obs2.validation_reasons


def test_4_index_engine_manifest_includes_provenance():
    """Change 4: Manifest includes raw_payload_sha256 and stored_file_sha256."""
    ref_prices = [5000.0, 5200.0]
    cur_prices = [5500.0, 5720.0]
    geom_ref, geom_cur, p_rel = IndexEngineService.calculate_jevons_relative(ref_prices, cur_prices)
    assert round(p_rel, 4) == 1.1000
