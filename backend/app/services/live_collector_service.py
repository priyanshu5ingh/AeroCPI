"""
AeroCPI Live Observation Collector Service (Prototype Source Adapter)
- Sources: Google Flights prototype adapter via fast_flights / selectolax
- Production APW Set: T+1, T+7, T+15, T+30, T+45 (SIH Required Set)
- Project-Root Relative & Configurable Directory Paths
- Full Ingestion through 4A Canonical Observation & Validation Engine
- Collection Event Idempotency & Observation Deduplication Separation
- Audit Fingerprinting & No-Overwrite Raw Capture Preservation
"""
from __future__ import annotations
import os
import re
import json
import gzip
import time
import uuid
import hashlib
import pathlib
import datetime as dt
from zoneinfo import ZoneInfo
from typing import List, Dict, Tuple, Optional, Any
from sqlalchemy.orm import Session

from selectolax.lexbor import LexborHTMLParser
from fast_flights import FlightQuery, Passengers, create_query, fetch_flights_html

from app.schemas.observation import RawQuoteInput
from app.services.observation_service import ObservationService
from app.models.observation import Observation
from app.models.collection_event import CollectionEvent

# Path Configuration (Environment Variable Override with Project-Root Fallback)
BACKEND_DIR = pathlib.Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent

DATA_DIR = pathlib.Path(os.getenv("AEROCPI_DATA_DIR", PROJECT_ROOT / "data"))
RAW_CAPTURES_DIR = pathlib.Path(os.getenv("AEROCPI_RAW_DIR", DATA_DIR / "raw" / "captures"))
OUT_DIR = pathlib.Path(os.getenv("AEROCPI_OUT_DIR", DATA_DIR / "out"))
LOG_DIR = pathlib.Path(os.getenv("AEROCPI_LOG_DIR", BACKEND_DIR / "logs"))

# Production APW Set (SIH Standard)
PRODUCTION_APW_SET = [1, 7, 15, 30, 45]

# Top 10 DGCA Reference Basket Routes
DEFAULT_BASKET_ROUTES = [
    ("DEL", "BOM"),
    ("BLR", "DEL"),
    ("BOM", "BLR"),
    ("DEL", "HYD"),
    ("DEL", "CCU"),
    ("DEL", "MAA"),
    ("BOM", "GOI"),
    ("BLR", "HYD"),
    ("DEL", "PAT"),
    ("BLR", "CCU")
]

CARRIER_MAP = {
    "IndiGo": "6E",
    "Air India": "AI",
    "Air India Express": "IX",
    "SpiceJet": "SG",
    "Akasa Air": "QP",
    "Alliance Air": "9I",
    "Vistara": "UK",
    "Star Air": "S5"
}

PROTOTYPE_DISCLAIMER = (
    "Ethical public search prototype adapter - no claim of official affiliation or legal authorization. "
    "Used strictly for academic research, methodology evaluation, and index demonstration."
)

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def parse_duration_minutes(s: str) -> Optional[int]:
    h = re.search(r"(\d+)\s*hr", s)
    m = re.search(r"(\d+)\s*min", s)
    if not h and not m:
        return None
    return (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0)

def parse_stops_count(s: str) -> Optional[int]:
    if "Nonstop" in s or "nonstop" in s or "Non-stop" in s:
        return 0
    m = re.search(r"(\d+)\s*stop", s)
    return int(m.group(1)) if m else None


class LiveCollectorService:
    """
    Live Collector Adapter Service:
    Executes live collection sweeps against public prototype surfaces,
    saves uncompressed and compressed raw artifacts with separated provenance SHA-256 digests,
    enforces collection-event level idempotency, and ingests quotes into the canonical observation pipeline.
    """

    @classmethod
    def collect_single_route(
        cls,
        origin: str,
        dest: str,
        apw: int,
        cabin: str = "ECONOMY",
        dry_run: bool = False,
        db: Optional[Session] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[pathlib.Path], Optional[str], str]:
        """
        Executes collection for one (origin, destination, apw) combination.
        Returns: (parsed_rows, raw_file_path, uncompressed_sha256, event_status)
        where event_status is "EXECUTED" or "SKIPPED_DUPLICATE".
        """
        origin = origin.upper().strip()
        dest = dest.upper().strip()
        cabin = cabin.upper().strip()

        # Enforce Production APW Rules
        if apw not in PRODUCTION_APW_SET and not dry_run:
            raise ValueError(f"APW {apw} is not in production APW set {PRODUCTION_APW_SET}")

        kolkata_tz = ZoneInfo("Asia/Kolkata")
        search_ts = dt.datetime.now(dt.timezone.utc)
        search_date = search_ts.astimezone(kolkata_tz).date()
        travel_date = search_date + dt.timedelta(days=apw)

        # 1. Collection-Event Level Idempotency Check
        if db is not None and not dry_run:
            existing_event = db.query(CollectionEvent).filter(
                CollectionEvent.source_id == "SRC_GOOGLE_FLIGHTS",
                CollectionEvent.origin == origin,
                CollectionEvent.destination == dest,
                CollectionEvent.apw == apw,
                CollectionEvent.collection_date == search_date,
                CollectionEvent.status == "SUCCESS"
            ).first()

            if existing_event:
                raw_path = pathlib.Path(existing_event.raw_file_path) if existing_event.raw_file_path else None
                return [], raw_path, existing_event.raw_payload_sha256, "SKIPPED_DUPLICATE"

        # 2. Fetch HTML from prototype source surface
        q = create_query(
            flights=[FlightQuery(date=travel_date.strftime("%Y-%m-%d"), from_airport=origin, to_airport=dest)],
            trip="one-way",
            seat=cabin.lower(),
            passengers=Passengers(adults=1),
            currency="INR"
        )
        html = fetch_flights_html(q)
        raw_bytes = html.encode("utf-8", "replace")
        raw_payload_sha256 = sha256_bytes(raw_bytes)

        # 3. Persist compressed raw HTML payload with NO-OVERWRITE guarantee
        RAW_CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
        stamp = search_ts.strftime("%Y%m%dT%H%M%SZ")
        raw_filename = f"{origin}-{dest}_apw{apw:02d}_{stamp}_{raw_payload_sha256[:12]}.html.gz"
        raw_file_path = RAW_CAPTURES_DIR / raw_filename

        if raw_file_path.exists():
            unique_suffix = uuid.uuid4().hex[:6]
            raw_filename = f"{origin}-{dest}_apw{apw:02d}_{stamp}_{raw_payload_sha256[:12]}_{unique_suffix}.html.gz"
            raw_file_path = RAW_CAPTURES_DIR / raw_filename

        compressed_bytes = gzip.compress(raw_bytes)
        stored_file_sha256 = sha256_bytes(compressed_bytes)

        with open(raw_file_path, "wb") as f:
            f.write(compressed_bytes)

        # 4. Parse HTML quotes using Selectolax Lexbor parser
        parsed_rows: List[Dict[str, Any]] = []
        seen_fingerprints = set()

        for idx, li in enumerate(LexborHTMLParser(html).css("li.pIav2d")):
            t = li.text(strip=False)
            pm = re.search(r"₹([\d,]+)", t)
            if not pm:
                continue
            total_fare = float(pm.group(1).replace(",", ""))

            matched_airline = next((a for a in CARRIER_MAP if a in t), None)
            carrier_code = CARRIER_MAP.get(matched_airline, "UNKNOWN") if matched_airline else "UNKNOWN"
            airline_name = matched_airline or "UNKNOWN"

            time_matches = re.findall(r"(\d{1,2}:\d{2}\s?[AP]M)", t)
            dep_time = time_matches[0] if time_matches else None
            arr_time = time_matches[1] if len(time_matches) > 1 else None

            stops = parse_stops_count(t)
            duration = parse_duration_minutes(t)

            # Audited Fingerprint Logic: Include stops, duration, offer position index (idx), and raw payload digest
            # to guarantee distinct offers in list view without flight numbers are never silently collapsed.
            # NOTE: idx is presentation order, not business identity. This means the fingerprint represents
            # capture-specific observation identity rather than stable flight identity.
            fp_string = f"{origin}|{dest}|{travel_date}|{airline_name}|{dep_time}|{arr_time}|{stops}|{duration}|{total_fare}|idx:{idx}|{raw_payload_sha256[:12]}"
            quote_fp = sha256_str(fp_string)

            if quote_fp in seen_fingerprints:
                continue
            seen_fingerprints.add(quote_fp)

            source_url = f"https://www.google.com/travel/flights?q=Flights+to+{dest}+from+{origin}+on+{travel_date}"

            raw_input_dict = {
                "source_id": "SRC_GOOGLE_FLIGHTS",
                "source_name": "Google Flights (Prototype Adapter)",
                "source_url": source_url,
                "collected_at": search_ts,
                "search_timestamp": search_ts,
                "travel_date": travel_date,
                "origin_raw": origin,
                "destination_raw": dest,
                "airline": carrier_code,
                "flight_number": None,
                "cabin": cabin,
                "fare_class": "STANDARD",
                "trip_type": "ONE_WAY",
                "stops": stops,
                "duration_minutes": duration,
                "raw_total_fare": f"₹{int(total_fare):,}",
                "total_fare": total_fare,
                "currency": "INR",
                "raw_payload_sha256": raw_payload_sha256,
                "stored_file_sha256": stored_file_sha256,
                "quote_fingerprint": quote_fp,
                "disclaimer": PROTOTYPE_DISCLAIMER
            }

            parsed_rows.append(raw_input_dict)

            # 5. Pipeline Ingestion into Database (if Session supplied & not dry-run)
            if db is not None and not dry_run:
                quote_schema = RawQuoteInput(
                    source_id="SRC_GOOGLE_FLIGHTS",
                    source_name="Google Flights (Prototype Adapter)",
                    source_url=source_url,
                    collected_at=search_ts,
                    search_timestamp=search_ts,
                    travel_date=travel_date,
                    origin_raw=origin,
                    destination_raw=dest,
                    airline=carrier_code,
                    flight_number=None,
                    cabin=cabin,
                    fare_class="STANDARD",
                    trip_type="ONE_WAY",
                    stops=stops,
                    duration_minutes=duration,
                    raw_total_fare=f"₹{int(total_fare):,}",
                    total_fare=total_fare,
                    currency="INR"
                )

                # Observation-Level Deduplication: Check if exact same quote fingerprint on search_date exists
                obs_key_str = f"SRC_GOOGLE_FLIGHTS|{search_date}|{travel_date}|{origin}|{dest}|{carrier_code}|NONE|{cabin}|STANDARD".upper()
                existing = db.query(Observation).filter(
                    Observation.observation_key == obs_key_str,
                    Observation.quote_fingerprint == quote_fp,
                    Observation.search_date == search_date
                ).first()

                if not existing:
                    obs = ObservationService.ingest_raw_quote(db=db, raw_input=quote_schema)
                    obs.raw_payload_sha256 = raw_payload_sha256
                    obs.stored_file_sha256 = stored_file_sha256
                    obs.quote_fingerprint = quote_fp
                    db.commit()

        # 6. Record Collection Event in Database
        if db is not None and not dry_run:
            evt = CollectionEvent(
                source_id="SRC_GOOGLE_FLIGHTS",
                origin=origin,
                destination=dest,
                apw=apw,
                collection_date=search_date,
                status="SUCCESS",
                quotes_count=len(parsed_rows),
                raw_file_path=str(raw_file_path),
                raw_payload_sha256=raw_payload_sha256,
                stored_file_sha256=stored_file_sha256,
                executed_at=search_ts
            )
            db.add(evt)
            db.commit()

        return parsed_rows, raw_file_path, raw_payload_sha256, "EXECUTED"

    @classmethod
    def execute_daily_collection_sweep(
        cls,
        db: Optional[Session] = None,
        routes: Optional[List[Tuple[str, str]]] = None,
        apws: Optional[List[int]] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Executes a complete daily collection sweep over specified or default basket routes & production APWs.
        Returns a Collection-Health Summary dictionary and writes health summary JSON artifact.
        """
        if routes is None:
            routes = DEFAULT_BASKET_ROUTES
        if apws is None:
            apws = PRODUCTION_APW_SET

        kolkata_tz = ZoneInfo("Asia/Kolkata")
        start_time = dt.datetime.now(dt.timezone.utc)
        collection_date_str = start_time.astimezone(kolkata_tz).strftime("%Y-%m-%d")
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        log_path = LOG_DIR / "collection_scheduler.log"

        events_attempted = len(routes) * len(apws)
        events_succeeded = 0
        events_failed = 0
        events_skipped_duplicate = 0

        total_quotes = 0
        obs_accepted = 0
        obs_flagged = 0
        obs_rejected = 0
        duplicate_payloads = 0

        all_rows: List[Dict[str, Any]] = []
        errors: List[str] = []

        def log_msg(msg: str):
            st = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            formatted = f"[{st}] {msg}"
            print(formatted, flush=True)
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write(formatted + "\n")

        log_msg(f"=== Starting Daily Collection Sweep (Date: {collection_date_str}, Dry Run: {dry_run}) ===")
        log_msg(f"Targeting {len(routes)} routes x {len(apws)} production APWs ({events_attempted} total sampling events)")

        for origin, dest in routes:
            for apw in apws:
                try:
                    rows, raw_path, digest, status = cls.collect_single_route(
                        origin=origin,
                        dest=dest,
                        apw=apw,
                        cabin="ECONOMY",
                        dry_run=dry_run,
                        db=db
                    )

                    if status == "SKIPPED_DUPLICATE":
                        events_skipped_duplicate += 1
                        raw_name = raw_path.name if raw_path else "NONE"
                        log_msg(f"SKIPPED_DUPLICATE {origin}-{dest} APW{apw:02d}: Collection event already recorded for {collection_date_str}")
                    else:
                        events_succeeded += 1
                        total_quotes += len(rows)
                        all_rows.extend(rows)
                        raw_name = raw_path.name if raw_path else "NONE"
                        log_msg(f"OK {origin}-{dest} APW{apw:02d}: {len(rows)} quotes -> {raw_name}")

                except Exception as e:
                    events_failed += 1
                    err_str = f"FAIL {origin}-{dest} APW{apw:02d}: {type(e).__name__}: {str(e)}"
                    errors.append(err_str)
                    log_msg(err_str)

                time.sleep(1.2) # Polite delay between requests

        # Query Database Ingestion Quality Summary if DB was provided
        if db is not None and not dry_run:
            from sqlalchemy import func
            db_date = start_time.date()
            obs_accepted = db.query(Observation).filter(Observation.search_date == db_date, Observation.validation_status == "ACCEPT").count()
            obs_flagged = db.query(Observation).filter(Observation.search_date == db_date, Observation.validation_status == "FLAG").count()
            obs_rejected = db.query(Observation).filter(Observation.search_date == db_date, Observation.validation_status == "REJECT").count()

        # Save collection observations JSONL
        stamp = start_time.strftime("%Y%m%dT%H%M%SZ")
        summary_file = OUT_DIR / f"aerocpi_observations_{stamp}.jsonl"
        with open(summary_file, "w", encoding="utf-8") as sf:
            for r in all_rows:
                sf.write(json.dumps(r, default=str) + "\n")

        # Collection Health Summary Dictionary
        health_summary = {
            "collection_date": collection_date_str,
            "events_attempted": events_attempted,
            "events_succeeded": events_succeeded,
            "events_failed": events_failed,
            "events_skipped_duplicate": events_skipped_duplicate,
            "observations_collected": total_quotes,
            "observations_accepted": obs_accepted,
            "observations_flagged": obs_flagged,
            "observations_rejected": obs_rejected,
            "duplicate_payloads": duplicate_payloads,
            "summary_file": str(summary_file),
            "log_file": str(log_path),
            "errors": errors
        }

        # Save Collection Health Summary JSON
        health_file = OUT_DIR / f"aerocpi_health_summary_{stamp}.json"
        with open(health_file, "w", encoding="utf-8") as hf:
            json.dump(health_summary, hf, indent=2)

        log_msg(f"=== Daily Collection Sweep Finished ===")
        log_msg(f"Succeeded: {events_succeeded}, Skipped Duplicates: {events_skipped_duplicate}, Failed: {events_failed}")
        log_msg(f"Quotes Collected: {total_quotes} (Accepted: {obs_accepted}, Flagged: {obs_flagged}, Rejected: {obs_rejected})")
        log_msg(f"Health Summary Saved: {health_file}")

        return health_summary
