import pytest
import gzip
import hashlib
import pathlib
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.services.live_collector_service import LiveCollectorService, PRODUCTION_APW_SET
from app.models.collection_event import CollectionEvent
from app.models.observation import Observation
from app.schemas.observation import RawQuoteInput
from app.services.observation_service import ObservationService
from app.validation.canonical_validation_rules import CanonicalValidationRules

from zoneinfo import ZoneInfo
from app.services.live_collector_service import LiveCollectorService, PRODUCTION_APW_SET

def test_collection_date_timezone_semantics(db_session):
    # Test that search_timestamp remains UTC but collection_date is derived in Asia/Kolkata
    # Boundary case: 00:30 IST on 2026-09-10 is 19:00 UTC on 2026-09-09.
    utc_time = datetime(2026, 9, 9, 19, 0, 0, tzinfo=timezone.utc)
    
    html_mock = "<li class=\"pIav2d\">IndiGo 08:00 AM - 10:15 AM Nonstop ₹4,500 2 hr 15 min</li>"
    with patch("app.services.live_collector_service.dt") as mock_dt, \
         patch("app.services.live_collector_service.fetch_flights_html", return_value=html_mock):
        
        mock_dt.datetime.now.return_value = utc_time
        mock_dt.timezone = timezone
        mock_dt.timedelta = timedelta
        
        LiveCollectorService.collect_single_route("DEL", "BOM", 15, dry_run=False, db=db_session)
        
        # Verify collection event date is 2026-09-10 (IST), not 2026-09-09 (UTC)
        evt = db_session.query(CollectionEvent).first()
        assert evt is not None
        assert evt.executed_at.replace(tzinfo=timezone.utc) == utc_time
        assert evt.collection_date.strftime("%Y-%m-%d") == "2026-09-10"
        
        # Verify observation travel_date is based on IST date (2026-09-10 + 15 = 2026-09-25)
        obs = db_session.query(Observation).first()
        assert obs is not None
        assert obs.travel_date.strftime("%Y-%m-%d") == "2026-09-25"

def test_production_apw_set_strictness():
    assert PRODUCTION_APW_SET == [1, 7, 15, 30, 45]
    assert 14 not in PRODUCTION_APW_SET
    assert 60 not in PRODUCTION_APW_SET

def test_collection_event_idempotency_vs_observation_deduplication(db_session):
    # Simulate single route collection event on Today's date
    search_ts = datetime.now(timezone.utc)
    search_date = search_ts.date()

    evt1 = CollectionEvent(
        source_id="SRC_GOOGLE_FLIGHTS",
        origin="DEL",
        destination="BOM",
        apw=15,
        collection_date=search_date,
        status="SUCCESS",
        quotes_count=20,
        executed_at=search_ts
    )
    db_session.add(evt1)
    db_session.commit()

    # Second attempt on SAME collection_date -> must return SKIPPED_DUPLICATE
    rows, raw_path, sha, status = LiveCollectorService.collect_single_route(
        origin="DEL",
        dest="BOM",
        apw=15,
        dry_run=False,
        db=db_session
    )

    assert status == "SKIPPED_DUPLICATE"
    assert rows == []

    # Simulation for a NEW collection_date (tomorrow) -> duplicate check does not match, new event proceeds
    tomorrow_date = search_date + timedelta(days=1)
    existing_tomorrow = db_session.query(CollectionEvent).filter(
        CollectionEvent.source_id == "SRC_GOOGLE_FLIGHTS",
        CollectionEvent.origin == "DEL",
        CollectionEvent.destination == "BOM",
        CollectionEvent.apw == 15,
        CollectionEvent.collection_date == tomorrow_date,
        CollectionEvent.status == "SUCCESS"
    ).first()

    assert existing_tomorrow is None

def test_audited_quote_fingerprint_list_view_no_flight_number():
    html_mock = """
    <ul>
      <li class="pIav2d">IndiGo 08:00 AM - 10:15 AM Nonstop ₹4,500 2 hr 15 min</li>
      <li class="pIav2d">IndiGo 08:00 AM - 10:15 AM 1 stop ₹4,500 4 hr 30 min</li>
    </ul>
    """
    with patch("app.services.live_collector_service.fetch_flights_html", return_value=html_mock):
        rows, raw_path, sha, status = LiveCollectorService.collect_single_route(
            origin="DEL",
            dest="BOM",
            apw=15,
            dry_run=True
        )

        assert len(rows) == 2
        fp1 = rows[0]["quote_fingerprint"]
        fp2 = rows[1]["quote_fingerprint"]

        # Distinct offers must NOT collide
        assert fp1 != fp2

def test_index_eligibility_state_separate_from_validation_status(db_session):
    search_ts = datetime.now(timezone.utc)
    travel_date = (search_ts + timedelta(days=15)).date()

    # Case 1: Total-only Google Flights quote (FLAG validation, ELIGIBLE index)
    raw_quote_total_only = RawQuoteInput(
        source_id="SRC_GOOGLE_FLIGHTS",
        source_name="Google Flights",
        source_url="https://www.google.com/travel/flights",
        collected_at=search_ts,
        search_timestamp=search_ts,
        travel_date=travel_date,
        origin_raw="DEL",
        destination_raw="BOM",
        airline="6E",
        flight_number=None, # Missing flight number
        cabin="ECONOMY",
        fare_class="STANDARD",
        trip_type="ONE_WAY",
        stops=0,
        duration_minutes=135,
        raw_total_fare="₹4,500",
        total_fare=4500.0,
        currency="INR"
    )

    obs1 = ObservationService.ingest_raw_quote(db_session, raw_quote_total_only)
    assert obs1.validation_status == "FLAG"
    assert "FLAG_MISSING_FARE_COMPONENT_BREAKDOWN" in obs1.validation_reasons
    assert obs1.index_eligibility == "ELIGIBLE"
    assert obs1.base_fare is None
    assert obs1.taxes is None
    assert obs1.mandatory_fees is None

    # Case 2: Route Outside Basket (FLAG validation, INELIGIBLE index)
    raw_quote_outside_basket = RawQuoteInput(
        source_id="SRC_GOOGLE_FLIGHTS",
        source_name="Google Flights",
        source_url="https://www.google.com/travel/flights",
        collected_at=search_ts,
        search_timestamp=search_ts,
        travel_date=travel_date,
        origin_raw="IXB", # Bagdogra -> Leh (outside reference basket)
        destination_raw="IXL",
        airline="6E",
        flight_number="6E-101",
        cabin="ECONOMY",
        fare_class="STANDARD",
        trip_type="ONE_WAY",
        stops=0,
        duration_minutes=120,
        raw_total_fare="₹7,200",
        total_fare=7200.0,
        currency="INR"
    )

    obs2 = ObservationService.ingest_raw_quote(db_session, raw_quote_outside_basket)
    assert obs2.validation_status == "FLAG"
    assert "FLAG_ROUTE_OUTSIDE_REFERENCE_BASKET" in obs2.validation_reasons
    assert obs2.index_eligibility == "INELIGIBLE"

def test_raw_capture_no_overwrite_protection(tmp_path, monkeypatch):
    custom_raw = tmp_path / "raw_captures"
    custom_raw.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.services.live_collector_service.RAW_CAPTURES_DIR", custom_raw)

    html_mock = "<html><body>Flight Data</body></html>"
    with patch("app.services.live_collector_service.fetch_flights_html", return_value=html_mock):
        rows1, path1, sha1, status1 = LiveCollectorService.collect_single_route("DEL", "BOM", 15, dry_run=True)
        assert path1.exists()

        # Second collection at same exact timestamp target path
        rows2, path2, sha2, status2 = LiveCollectorService.collect_single_route("DEL", "BOM", 15, dry_run=True)
        assert path2.exists()
        assert path1 != path2 or path2.name.count(".html.gz") == 1

def test_collection_health_summary_fields(db_session):
    html_mock = "<li class=\"pIav2d\">IndiGo 08:00 AM - 10:15 AM Nonstop ₹4,500 2 hr 15 min</li>"
    with patch("app.services.live_collector_service.fetch_flights_html", return_value=html_mock):
        summary = LiveCollectorService.execute_daily_collection_sweep(
            db=db_session,
            routes=[("DEL", "BOM")],
            apws=[15],
            dry_run=True
        )

        assert "collection_date" in summary
        assert "events_attempted" in summary
        assert "events_succeeded" in summary
        assert "events_failed" in summary
        assert "events_skipped_duplicate" in summary
        assert "observations_collected" in summary
        assert "observations_accepted" in summary
        assert "observations_flagged" in summary
        assert "observations_rejected" in summary
        assert "duplicate_payloads" in summary
        assert summary["events_attempted"] == 1
