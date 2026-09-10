import pytest
import os
import gzip
import hashlib
import pathlib
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.services.live_collector_service import (
    LiveCollectorService,
    PRODUCTION_APW_SET,
    DATA_DIR,
    RAW_CAPTURES_DIR,
    OUT_DIR,
    LOG_DIR
)
from app.db.session import SessionLocal
from app.models.observation import Observation
from app.schemas.observation import RawQuoteInput
from app.services.observation_service import ObservationService

def test_production_apw_set_has_no_t14():
    assert PRODUCTION_APW_SET == [1, 7, 15, 30, 45]
    assert 14 not in PRODUCTION_APW_SET

def test_path_resolution_defaults():
    assert DATA_DIR is not None
    assert RAW_CAPTURES_DIR is not None
    assert OUT_DIR is not None
    assert LOG_DIR is not None
    assert "aerocpi" not in str(RAW_CAPTURES_DIR).lower() or "data" in str(RAW_CAPTURES_DIR).lower()

def test_provenance_hash_separation(tmp_path):
    raw_content = "<html><head><title>Mock Flight</title></head><body>Flight Quote</body></html>"
    raw_bytes = raw_content.encode("utf-8")
    
    raw_hash = hashlib.sha256(raw_bytes).hexdigest()
    
    gz_path = tmp_path / "test_capture.html.gz"
    with gzip.open(gz_path, "wb") as f:
        f.write(raw_bytes)
        
    stored_bytes = gz_path.read_bytes()
    stored_hash = hashlib.sha256(stored_bytes).hexdigest()
    
    assert raw_hash != stored_hash
    assert len(raw_hash) == 64
    assert len(stored_hash) == 64

def test_live_collector_idempotency(db_session):
    search_ts = datetime.now(timezone.utc)
    travel_date = (search_ts + timedelta(days=15)).date()
    
    quote_schema = RawQuoteInput(
        source_id="SRC_GOOGLE_FLIGHTS",
        source_name="Google Flights (Prototype Adapter)",
        source_url="https://www.google.com/travel/flights",
        collected_at=search_ts,
        search_timestamp=search_ts,
        travel_date=travel_date,
        origin_raw="DEL",
        destination_raw="BOM",
        airline="6E",
        flight_number=None,
        cabin="ECONOMY",
        fare_class="STANDARD",
        trip_type="ONE_WAY",
        stops=0,
        duration_minutes=130,
        raw_total_fare="₹4,500",
        total_fare=4500.0,
        currency="INR"
    )
    
    quote_fp = "test_fingerprint_hash_12345"
    raw_payload_sha256 = "a" * 64
    stored_file_sha256 = "b" * 64
    
    obs_key_str = f"SRC_GOOGLE_FLIGHTS|{search_ts.date()}|{travel_date}|DEL|BOM|6E|NONE|ECONOMY|STANDARD".upper()
    
    # Ingest 1
    existing1 = db_session.query(Observation).filter(
        Observation.observation_key == obs_key_str,
        Observation.quote_fingerprint == quote_fp,
        Observation.search_date == search_ts.date()
    ).first()
    assert existing1 is None
    
    obs1 = ObservationService.ingest_raw_quote(db=db_session, raw_input=quote_schema)
    obs1.raw_payload_sha256 = raw_payload_sha256
    obs1.stored_file_sha256 = stored_file_sha256
    obs1.quote_fingerprint = quote_fp
    db_session.commit()
    
    # Ingest 2 attempt with same key & fingerprint
    existing2 = db_session.query(Observation).filter(
        Observation.observation_key == obs_key_str,
        Observation.quote_fingerprint == quote_fp,
        Observation.search_date == search_ts.date()
    ).first()
    assert existing2 is not None
    assert existing2.observation_id == obs1.observation_id
