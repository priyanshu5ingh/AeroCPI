import re
import json
import hashlib
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Optional, Tuple, Set

from app.validation_data.dgca_parser import map_city_to_airport, make_canonical_route_key

# Default DGCA Top 10 Reference Basket Canonical Keys (2025 Reference Period)
TOP_10_DGCA_BASKET_ROUTE_KEYS: Set[str] = {
    "DELHI::MUMBAI",
    "BENGALURU::DELHI",
    "BENGALURU::MUMBAI",
    "DELHI::HYDERABAD",
    "DELHI::KOLKATA",
    "CHENNAI::DELHI",
    "GOA::MUMBAI",
    "BENGALURU::HYDERABAD",
    "DELHI::PATNA",
    "BENGALURU::KOLKATA"
}

def parse_decimal(val: Any) -> Optional[Decimal]:
    """
    Parses a string, int, float or Decimal value into a 2-decimal place Decimal.
    Returns None if missing, blank, or invalid.
    """
    if val is None:
        return None
    val_str = str(val).strip()
    if val_str == "" or val_str.lower() in ("none", "null", "n/a", "na", "-"):
        return None
    try:
        # Strip currency symbols, commas, spaces
        clean_str = re.sub(r"[^\d.-]", "", val_str)
        if not clean_str:
            return None
        d = Decimal(clean_str).quantize(Decimal("0.01"))
        return d
    except (InvalidOperation, TypeError, ValueError):
        return None

def parse_date_value(val: Any) -> Optional[date]:
    """
    Parses a date string (YYYY-MM-DD) or date/datetime object into datetime.date.
    """
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    val_str = str(val).strip()
    if not val_str:
        return None
    try:
        # Try YYYY-MM-DD
        return datetime.strptime(val_str[:10], "%Y-%m-%d").date()
    except ValueError:
        return None

def parse_datetime_value(val: Any) -> datetime:
    """
    Parses a ISO datetime string or datetime object into UTC datetime.
    """
    if val is None:
        return datetime.now(timezone.utc)
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val
    val_str = str(val).strip()
    try:
        dt = datetime.fromisoformat(val_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return datetime.now(timezone.utc)

def classify_booking_horizon(advance_purchase_days: Optional[int]) -> str:
    """
    Explicit horizon classification:
    - T+1  -> advance_purchase_days == 1
    - T+7  -> advance_purchase_days == 7
    - T+15 -> advance_purchase_days == 15
    - T+30 -> advance_purchase_days == 30
    - T+45 -> advance_purchase_days == 45
    - OFF_HORIZON -> all other values
    """
    if advance_purchase_days is None:
        return "OFF_HORIZON"
    if advance_purchase_days == 1:
        return "T+1"
    elif advance_purchase_days == 7:
        return "T+7"
    elif advance_purchase_days == 15:
        return "T+15"
    elif advance_purchase_days == 30:
        return "T+30"
    elif advance_purchase_days == 45:
        return "T+45"
    else:
        return "OFF_HORIZON"


class CanonicalNormalizationService:
    """
    Decoupled Canonical Normalization Service:
    Converts a raw airfare quote input payload into a standardized CanonicalObservation dict.
    Strictly preserves raw input strings while extracting clean canonical data.
    """

    @staticmethod
    def normalize_raw_quote(
        raw_quote: Dict[str, Any],
        basket_keys: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        if basket_keys is None:
            basket_keys = TOP_10_DGCA_BASKET_ROUTE_KEYS

        # 1. Raw Metadata Preservation & Authoritative Search Timestamp
        source_id = str(raw_quote.get("source_id") or "UNKNOWN_SOURCE").strip()
        source_name = raw_quote.get("source_name") or source_id.replace("_", " ").title()
        source_url = raw_quote.get("source_url")

        collected_at = parse_datetime_value(raw_quote.get("collected_at") or raw_quote.get("observed_at"))

        # search_timestamp is the primary authoritative collection event field
        raw_search_ts = raw_quote.get("search_timestamp")
        if raw_search_ts is not None:
            search_timestamp = parse_datetime_value(raw_search_ts)
            search_date = search_timestamp.date()
        else:
            raw_sdate = parse_date_value(raw_quote.get("search_date"))
            if raw_sdate is not None:
                search_date = raw_sdate
                from datetime import time
                search_timestamp = datetime.combine(search_date, time.min, tzinfo=timezone.utc)
            else:
                search_timestamp = collected_at
                search_date = search_timestamp.date()

        travel_date = parse_date_value(raw_quote.get("travel_date"))

        # DERIVATION CONTRACT:
        # advance_purchase_days is a derived canonical field calculated strictly as:
        # (travel_date - search_timestamp.date()).days
        # It MUST NEVER be read, trusted, or reconstructed from a raw source's 'days_left' or 'advance_days' field.
        if search_timestamp and travel_date:
            advance_purchase_days = (travel_date - search_timestamp.date()).days
        else:
            advance_purchase_days = None

        horizon_code = classify_booking_horizon(advance_purchase_days)

        # 2. Raw Origin / Destination & Canonical Mapping
        origin_raw = str(raw_quote.get("origin_raw") or raw_quote.get("origin") or "").strip()
        destination_raw = str(raw_quote.get("destination_raw") or raw_quote.get("destination") or "").strip()

        if origin_raw and destination_raw and origin_raw.upper() != destination_raw.upper():
            c1_canon, apt1, metro1 = map_city_to_airport(origin_raw)
            c2_canon, apt2, metro2 = map_city_to_airport(destination_raw)

            origin_airport = apt1
            destination_airport = apt2
            route_id = f"{apt1}-{apt2}"
            route_mapping_status = "CANONICAL_MAPPED"

            canonical_key = make_canonical_route_key(c1_canon, c2_canon)
            if canonical_key in basket_keys:
                basket_status = "BASKET_MEMBER"
            else:
                basket_status = "ROUTE_OUTSIDE_REFERENCE_BASKET"
        else:
            origin_airport = None
            destination_airport = None
            route_id = f"UNKNOWN-UNKNOWN"
            route_mapping_status = "UNMAPPABLE"
            basket_status = "UNMAPPABLE_ROUTE"

        # 3. Carrier & Flight Details
        airline = str(raw_quote.get("airline") or raw_quote.get("carrier_id") or "UNKNOWN").strip().upper()
        flight_number = str(raw_quote.get("flight_number") or "").strip() or None
        cabin = str(raw_quote.get("cabin") or "ECONOMY").strip().upper()
        fare_class = str(raw_quote.get("fare_class") or "STANDARD").strip().upper() or None
        trip_type = str(raw_quote.get("trip_type") or "ONE_WAY").strip().upper()

        raw_stops = raw_quote.get("stops")
        if raw_stops is None:
            stops = None
            stops_status = "MISSING"
        else:
            try:
                stops = int(raw_stops)
                stops_status = "OBSERVED"
            except (ValueError, TypeError):
                stops = None
                stops_status = "MISSING"

        duration_minutes = raw_quote.get("duration_minutes")
        if duration_minutes is not None:
            try:
                duration_minutes = int(duration_minutes)
            except (ValueError, TypeError):
                duration_minutes = None

        # 4. Raw Fare Strings & Decimal Money Normalization
        raw_total_fare = str(raw_quote.get("raw_total_fare") or raw_quote.get("total_fare") or "")
        raw_base_fare = str(raw_quote.get("raw_base_fare") or raw_quote.get("base_fare") or "")
        raw_taxes = str(raw_quote.get("raw_taxes") or raw_quote.get("taxes") or "")
        raw_fees = str(raw_quote.get("raw_fees") or raw_quote.get("fees") or raw_quote.get("mandatory_fees") or "")

        tf_val = raw_quote.get("total_fare") if raw_quote.get("total_fare") is not None else raw_quote.get("raw_total_fare")
        bf_val = raw_quote.get("base_fare") if raw_quote.get("base_fare") is not None else raw_quote.get("raw_base_fare")
        tx_val = raw_quote.get("taxes") if raw_quote.get("taxes") is not None else raw_quote.get("raw_taxes")
        fee_val = raw_quote.get("fees") if raw_quote.get("fees") is not None else (raw_quote.get("mandatory_fees") if raw_quote.get("mandatory_fees") is not None else raw_quote.get("raw_fees"))

        total_fare = parse_decimal(tf_val)
        base_fare = parse_decimal(bf_val)
        taxes = parse_decimal(tx_val)
        fees = parse_decimal(fee_val)

        currency = str(raw_quote.get("currency") or "INR").strip().upper()

        # Component Breakdown Status
        if base_fare is not None and taxes is not None and fees is not None:
            breakdown_status = "COMPLETE_BREAKDOWN"
        elif base_fare is not None or taxes is not None or fees is not None:
            breakdown_status = "PARTIAL_BREAKDOWN"
        else:
            breakdown_status = "TOTAL_ONLY"

        # Arithmetic Evaluation
        if base_fare is not None and taxes is not None and fees is not None and total_fare is not None:
            expected_total = (base_fare + taxes + fees).quantize(Decimal("0.01"))
            if abs(total_fare - expected_total) <= Decimal("0.01"):
                arithmetic_status = "ARITHMETIC_MATCH"
            else:
                arithmetic_status = "ARITHMETIC_MISMATCH"
        else:
            arithmetic_status = "ARITHMETIC_UNCHECKABLE"

        # 5. Fingerprints & Hashes (Separated Provenance Hashes)
        import gzip
        raw_payload_str = json.dumps(raw_quote, sort_keys=True, default=str)
        raw_payload_bytes = raw_payload_str.encode("utf-8")
        raw_payload_sha256 = hashlib.sha256(raw_payload_bytes).hexdigest()
        stored_file_sha256 = hashlib.sha256(gzip.compress(raw_payload_bytes)).hexdigest()

        # Backward compatible alias
        raw_payload_hash = raw_payload_sha256

        # Observation Context Identity (Flight/Search Context)
        obs_key_str = f"{source_id}|{search_date}|{travel_date}|{origin_airport}|{destination_airport}|{airline}|{flight_number}|{cabin}|{fare_class}"
        observation_key = obs_key_str.upper()

        # Payload Identity
        quote_fingerprint = raw_payload_sha256

        return {
            "source_id": source_id,
            "source_name": source_name,
            "source_url": source_url,
            "collected_at": collected_at,
            "search_timestamp": search_timestamp,
            "search_date": search_date,
            "travel_date": travel_date,
            "advance_purchase_days": advance_purchase_days,
            "horizon_code": horizon_code,
            "origin_raw": origin_raw,
            "destination_raw": destination_raw,
            "origin_airport": origin_airport,
            "destination_airport": destination_airport,
            "route_id": route_id,
            "route_mapping_status": route_mapping_status,
            "basket_status": basket_status,
            "airline": airline,
            "flight_number": flight_number,
            "cabin": cabin,
            "fare_class": fare_class,
            "trip_type": trip_type,
            "stops": stops,
            "stops_status": stops_status,
            "duration_minutes": duration_minutes,
            "raw_total_fare": raw_total_fare,
            "raw_base_fare": raw_base_fare,
            "raw_taxes": raw_taxes,
            "raw_fees": raw_fees,
            "base_fare": base_fare,
            "taxes": taxes,
            "fees": fees,
            "total_fare": total_fare,
            "currency": currency,
            "breakdown_status": breakdown_status,
            "arithmetic_status": arithmetic_status,
            "raw_payload_hash": raw_payload_hash,
            "raw_payload_sha256": raw_payload_sha256,
            "stored_file_sha256": stored_file_sha256,
            "observation_key": observation_key,
            "quote_fingerprint": quote_fingerprint,
        }
