import pathlib
import json
import hashlib
import pytest
from datetime import datetime, timezone

from app.services.duffel_adapter_service import DuffelAdapterService, parse_iso_duration_minutes
from app.models.observation import Observation

FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "duffel_offer_request_response.json"


def test_parse_iso_duration_minutes():
    assert parse_iso_duration_minutes("PT2H15M") == 135
    assert parse_iso_duration_minutes("PT1H50M") == 110
    assert parse_iso_duration_minutes("PT45M") == 45
    assert parse_iso_duration_minutes("PT3H") == 180
    assert parse_iso_duration_minutes(None) is None


def test_duffel_raw_quote_mapping_determinism():
    with open(FIXTURE_PATH, "rb") as f:
        raw_bytes = f.read()

    quotes, audit_report, raw_sha256 = DuffelAdapterService.transform_duffel_response_to_raw_quotes(raw_bytes)
    assert len(quotes) == 2
    assert audit_report["offer_request_id"] == "orq_0000AcX1Y2Z3A4B5C6D7E8"
    assert raw_sha256 == hashlib.sha256(raw_bytes).hexdigest()

    q0 = quotes[0]
    assert q0["source_id"] == "SRC_DUFFEL"
    assert q0["airline"] == "6E"
    assert q0["flight_number"] == "6E-2131"
    assert q0["origin_raw"] == "DEL"
    assert q0["destination_raw"] == "BOM"
    assert q0["total_fare"] == 5312.00
    assert q0["base_fare"] == 4500.00
    assert q0["taxes"] == 812.00
    assert q0["fees"] is None
    assert q0["duration_minutes"] == 135
    assert q0["live_mode"] is False
    assert q0["is_test_data"] is True


def test_nullability_and_no_fee_inference():
    with open(FIXTURE_PATH, "rb") as f:
        raw_bytes = f.read()

    quotes, audit_report, _ = DuffelAdapterService.transform_duffel_response_to_raw_quotes(raw_bytes)
    q1 = quotes[1]  # Air India offer with null base fare and taxes in fixture

    assert q1["airline"] == "AI"
    assert q1["total_fare"] == 6100.00
    assert q1["base_fare"] is None
    assert q1["taxes"] is None
    assert q1["fees"] is None  # Strict Prohibited Fee Inference: fees are NEVER computed from total - base - tax


def test_component_rich_observation_4a_pipeline_ingestion(db_session):
    with open(FIXTURE_PATH, "rb") as f:
        raw_bytes = f.read()

    now_utc = datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc)
    observations = DuffelAdapterService.ingest_duffel_fixture_to_database(
        db=db_session,
        raw_payload=raw_bytes,
        search_timestamp=now_utc
    )

    assert len(observations) == 2

    # Check component-rich offer (IndiGo offer)
    obs0 = observations[0]
    assert obs0.source_id == "SRC_DUFFEL"
    assert obs0.origin_raw == "DEL"
    assert obs0.destination_raw == "BOM"
    assert obs0.airline == "6E"
    assert obs0.flight_number == "6E-2131"
    assert obs0.base_fare == 4500.00
    assert obs0.taxes == 812.00
    assert obs0.total_fare == 5312.00
    assert obs0.breakdown_status == "PARTIAL_BREAKDOWN"  # base + tax present, fees is None (no fee inference)
    assert obs0.arithmetic_status in ("ARITHMETIC_MATCH", "ARITHMETIC_UNCHECKABLE")

    # Validation result
    assert obs0.validation_status in ("ACCEPT", "FLAG")

    # Isolation Test Mode Check: live_mode=false is strictly INELIGIBLE
    assert obs0.index_eligibility == "INELIGIBLE"
    assert "INELIGIBLE_TEST_MODE_DATA" in obs0.index_eligibility_reasons


def test_test_mode_isolation_guard(db_session):
    with open(FIXTURE_PATH, "rb") as f:
        raw_bytes = f.read()

    observations = DuffelAdapterService.ingest_duffel_fixture_to_database(
        db=db_session,
        raw_payload=raw_bytes
    )

    for obs in observations:
        # Guarantee that test mode data can NEVER be eligible for LIVE_MARKET_DATA
        assert obs.index_eligibility == "INELIGIBLE"
        assert "INELIGIBLE_TEST_MODE_DATA" in obs.index_eligibility_reasons


def test_provenance_hash_preservation(db_session):
    with open(FIXTURE_PATH, "rb") as f:
        raw_bytes = f.read()

    expected_sha = hashlib.sha256(raw_bytes).hexdigest()
    observations = DuffelAdapterService.ingest_duffel_fixture_to_database(
        db=db_session,
        raw_payload=raw_bytes
    )

    assert observations[0].raw_payload_sha256 == expected_sha
    assert len(observations[0].quote_fingerprint) == 64
