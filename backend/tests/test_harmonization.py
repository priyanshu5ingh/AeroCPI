import pathlib
import json
import pytest
from datetime import datetime, date, timezone

from app.schemas.observation import RawQuoteInput
from app.services.observation_service import ObservationService
from app.services.duffel_adapter_service import DuffelAdapterService
from app.services.harmonization_service import HarmonizationService
from app.models.observation import Observation

DUFFEL_FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "duffel_offer_request_response.json"


def test_multi_source_coexistence_and_harmonization(db_session):
    now_utc = datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc)
    travel_dt = date(2026, 9, 25)

    # 1. Ingest Google Flights Quote (Total-only)
    google_quote = RawQuoteInput(
        source_id="SRC_GOOGLE_FLIGHTS",
        source_name="Google Flights",
        source_url="https://www.google.com/travel/flights",
        collected_at=now_utc,
        search_timestamp=now_utc,
        travel_date=travel_dt,
        origin_raw="DEL",
        destination_raw="BOM",
        airline="6E",
        flight_number="6E-2131",
        cabin="ECONOMY",
        fare_class="STANDARD",
        trip_type="ONE_WAY",
        stops=0,
        duration_minutes=135,
        raw_total_fare="₹4,500",
        total_fare=4500.0,
        currency="INR"
    )
    obs_google = ObservationService.ingest_raw_quote(db_session, google_quote)
    obs_google.quote_fingerprint = "fp_google_12345"
    db_session.commit()

    # 2. Ingest Duffel Quote (Component Breakdown)
    with open(DUFFEL_FIXTURE_PATH, "rb") as f:
        duffel_raw_bytes = f.read()

    obs_duffel_list = DuffelAdapterService.ingest_duffel_fixture_to_database(
        db=db_session,
        raw_payload=duffel_raw_bytes,
        search_timestamp=now_utc
    )
    obs_duffel = obs_duffel_list[0]

    # 3. Assert Co-existence in Database
    all_obs = db_session.query(Observation).filter(
        Observation.route_id == "DEL-BOM",
        Observation.travel_date == travel_dt
    ).all()

    assert len(all_obs) == 3  # 1 Google Flights + 2 Duffel offers from fixture
    source_ids = {o.source_id for o in all_obs}
    assert "SRC_GOOGLE_FLIGHTS" in source_ids
    assert "SRC_DUFFEL" in source_ids


def test_no_fare_combination(db_session):
    now_utc = datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc)
    travel_dt = date(2026, 9, 25)

    # Google Flights (4500 INR)
    google_quote = RawQuoteInput(
        source_id="SRC_GOOGLE_FLIGHTS",
        source_name="Google Flights",
        collected_at=now_utc,
        search_timestamp=now_utc,
        travel_date=travel_dt,
        origin_raw="DEL",
        destination_raw="BOM",
        airline="6E",
        total_fare=4500.0,
        currency="INR"
    )
    obs_g = ObservationService.ingest_raw_quote(db_session, google_quote)

    # Duffel (5312 INR)
    with open(DUFFEL_FIXTURE_PATH, "rb") as f:
        duffel_bytes = f.read()

    obs_d_list = DuffelAdapterService.ingest_duffel_fixture_to_database(db_session, duffel_bytes, search_timestamp=now_utc)
    obs_d = obs_d_list[0]

    # Distinct records with distinct total fares preserved
    assert obs_g.observation_id != obs_d.observation_id
    assert obs_g.total_fare == 4500.0
    assert obs_d.total_fare == 5312.0


def test_google_flights_total_only_preservation(db_session):
    now_utc = datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc)
    travel_dt = date(2026, 9, 25)

    google_quote = RawQuoteInput(
        source_id="SRC_GOOGLE_FLIGHTS",
        source_name="Google Flights",
        collected_at=now_utc,
        search_timestamp=now_utc,
        travel_date=travel_dt,
        origin_raw="DEL",
        destination_raw="BOM",
        airline="6E",
        total_fare=4500.0,
        currency="INR"
    )
    obs = ObservationService.ingest_raw_quote(db_session, google_quote)

    assert obs.breakdown_status == "TOTAL_ONLY"
    assert obs.base_fare is None
    assert obs.taxes is None
    assert obs.fees is None
    assert obs.mandatory_fees is None


def test_duffel_component_breakdown_preservation(db_session):
    with open(DUFFEL_FIXTURE_PATH, "rb") as f:
        duffel_bytes = f.read()

    obs_list = DuffelAdapterService.ingest_duffel_fixture_to_database(db_session, duffel_bytes)
    obs0 = obs_list[0]

    assert obs0.source_id == "SRC_DUFFEL"
    assert obs0.base_fare == 4500.00
    assert obs0.taxes == 812.00
    assert obs0.fees is None  # Fees preserved NULL; no fee inference!
    assert obs0.total_fare == 5312.00
    assert obs0.breakdown_status == "PARTIAL_BREAKDOWN"


def test_carrier_roles_and_source_ids_preservation(db_session):
    with open(DUFFEL_FIXTURE_PATH, "rb") as f:
        duffel_bytes = f.read()

    obs_list = DuffelAdapterService.ingest_duffel_fixture_to_database(db_session, duffel_bytes)
    obs0 = obs_list[0]

    # Verify carrier roles & IDs are accessible
    assert obs0.airline == "6E"
    assert obs0.source_url is None  # Correction 1: No constructed URL unless retrievable
    assert obs0.raw_payload_sha256 is not None


def test_source_comparison_report_output(db_session):
    now_utc = datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc)
    travel_dt = date(2026, 9, 25)

    # Ingest Google quote
    google_quote = RawQuoteInput(
        source_id="SRC_GOOGLE_FLIGHTS",
        source_name="Google Flights",
        collected_at=now_utc,
        search_timestamp=now_utc,
        travel_date=travel_dt,
        origin_raw="DEL",
        destination_raw="BOM",
        airline="6E",
        flight_number="6E-2131",
        total_fare=4500.0,
        currency="INR"
    )
    ObservationService.ingest_raw_quote(db_session, google_quote)

    # Ingest Duffel quotes
    with open(DUFFEL_FIXTURE_PATH, "rb") as f:
        duffel_bytes = f.read()
    DuffelAdapterService.ingest_duffel_fixture_to_database(db_session, duffel_bytes, search_timestamp=now_utc)

    # Run Harmonization Comparison Report
    report = HarmonizationService.compare_route_observations(
        db=db_session,
        route_id="DEL-BOM",
        travel_date=travel_dt,
        horizon_days=15
    )

    assert report["route_id"] == "DEL-BOM"
    assert report["travel_date"] == "2026-09-25"
    assert report["total_observations_count"] == 3
    assert report["sources_count"] == 2
    assert set(report["sources_represented"]) == {"SRC_GOOGLE_FLIGHTS", "SRC_DUFFEL"}
    assert "Controlled harmonization fixture" in report["disclaimer"]

    # Regression Assertions for Evidence-Pack Consistency
    assert report["total_observations_count"] == len(report["observations"])
    assert report["sources_count"] == len(set(o["source_id"] for o in report["observations"]))

    # Verify detailed comparison items
    for item in report["observations"]:
        assert "source_id" in item
        assert "total_fare" in item
        assert "component_availability" in item
        assert "carrier" in item
        assert "validation_status" in item
        assert "index_eligibility" in item


def test_cabin_isolation_in_harmonization(db_session):
    now_utc = datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc)
    travel_dt = date(2026, 9, 25)

    # Ingest Economy quote
    econ_quote = RawQuoteInput(
        source_id="SRC_GOOGLE_FLIGHTS",
        source_name="Google Flights",
        collected_at=now_utc,
        search_timestamp=now_utc,
        travel_date=travel_dt,
        origin_raw="DEL",
        destination_raw="BOM",
        airline="6E",
        cabin="ECONOMY",
        total_fare=4500.0,
        currency="INR"
    )
    ObservationService.ingest_raw_quote(db_session, econ_quote)

    # Ingest Business quote
    biz_quote = RawQuoteInput(
        source_id="SRC_GOOGLE_FLIGHTS",
        source_name="Google Flights",
        collected_at=now_utc,
        search_timestamp=now_utc,
        travel_date=travel_dt,
        origin_raw="DEL",
        destination_raw="BOM",
        airline="AI",
        cabin="BUSINESS",
        total_fare=18500.0,
        currency="INR"
    )
    ObservationService.ingest_raw_quote(db_session, biz_quote)

    # Query Economy cabin only
    econ_report = HarmonizationService.compare_route_observations(
        db=db_session,
        route_id="DEL-BOM",
        travel_date=travel_dt,
        horizon_days=15,
        cabin_class="ECONOMY"
    )
    assert econ_report["total_observations_count"] == 1
    assert econ_report["observations"][0]["cabin"] == "ECONOMY"
    assert econ_report["observations"][0]["total_fare"] == 4500.0

    # Query Business cabin only
    biz_report = HarmonizationService.compare_route_observations(
        db=db_session,
        route_id="DEL-BOM",
        travel_date=travel_dt,
        horizon_days=15,
        cabin_class="BUSINESS"
    )
    assert biz_report["total_observations_count"] == 1
    assert biz_report["observations"][0]["cabin"] == "BUSINESS"
    assert biz_report["observations"][0]["total_fare"] == 18500.0

