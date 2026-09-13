"""
AeroCPI Duffel API v2 Source Adapter Service
- Maps Duffel API v2 responses into 4A RawQuoteInput contracts & Canonical Observation Pipeline
- Preserves exact breakdown component nullability (base_fare, taxes, fees=None)
- Strict prohibition on inferring fees from total - base - tax
- Explicit TEST_DATA isolation guard: live_mode=false quotes marked INELIGIBLE for LIVE_MARKET_DATA
- Complete raw response & SHA-256 provenance preservation
"""
from __future__ import annotations
import json
import re
import hashlib
import datetime as dt
from zoneinfo import ZoneInfo
from typing import Dict, List, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.schemas.observation import RawQuoteInput
from app.services.duffel_client_service import DuffelClientService
from app.services.observation_service import ObservationService
from app.models.observation import Observation


def parse_iso_duration_minutes(s: Optional[str]) -> Optional[int]:
    """Parses ISO 8601 duration strings like PT2H15M into integer minutes."""
    if not s or not isinstance(s, str):
        return None
    h = re.search(r"(\d+)\s*H", s)
    m = re.search(r"(\d+)\s*M", s)
    if not h and not m:
        return None
    hours = int(h.group(1)) if h else 0
    mins = int(m.group(1)) if m else 0
    return hours * 60 + mins


class DuffelAdapterService:
    @classmethod
    def transform_duffel_response_to_raw_quotes(
        cls,
        raw_payload: Any,
        search_timestamp: Optional[dt.datetime] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], str]:
        """
        Transforms Duffel API v2 JSON response bytes or dict into a list of RawQuoteInput dicts
        plus provenance metadata.
        Returns: (quote_dicts_list, audit_report_dict, raw_payload_sha256)
        """
        if isinstance(raw_payload, (bytes, bytearray)):
            raw_bytes = bytes(raw_payload)
            resp_dict = json.loads(raw_bytes.decode("utf-8"))
        elif isinstance(raw_payload, str):
            raw_bytes = raw_payload.encode("utf-8")
            resp_dict = json.loads(raw_payload)
        elif isinstance(raw_payload, dict):
            raw_bytes = json.dumps(raw_payload).encode("utf-8")
            resp_dict = raw_payload
        else:
            raise ValueError("Unsupported raw_payload type for Duffel adapter transformation")

        raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        audit_report = DuffelClientService.audit_offer_request_response(resp_dict)

        if search_timestamp is None:
            search_ts = dt.datetime.now(dt.timezone.utc)
        else:
            search_ts = search_timestamp

        kolkata_tz = ZoneInfo("Asia/Kolkata")
        search_date = search_ts.astimezone(kolkata_tz).date()

        offer_req_id = audit_report.get("offer_request_id") or "UNKNOWN_OFFER_REQ"
        live_mode = audit_report.get("live_mode")
        data_classification = audit_report.get("data_classification")

        quote_records: List[Dict[str, Any]] = []

        for offer in audit_report.get("offers", []):
            offer_id = offer.get("offer_id")
            owner_code = offer.get("owner_code") or "UNKNOWN"

            base_amt_str = offer.get("base_amount")
            base_curr = offer.get("base_currency")
            tax_amt_str = offer.get("tax_amount")
            tax_curr = offer.get("tax_currency")
            total_amt_str = offer.get("total_amount")
            total_curr = offer.get("total_currency") or "INR"

            base_amt = float(base_amt_str) if base_amt_str is not None else None
            tax_amt = float(tax_amt_str) if tax_amt_str is not None else None
            total_amt = float(total_amt_str) if total_amt_str is not None else 0.0

            # Strict Nullability: Fees are NEVER inferred from total - base - tax
            fee_amt = None

            for sl in offer.get("slices", []):
                slice_id = sl.get("slice_id")
                duration_mins = parse_iso_duration_minutes(sl.get("duration"))

                for seg in sl.get("segments", []):
                    seg_id = seg.get("segment_id")
                    flt_no = seg.get("flight_number")
                    origin_iata = seg.get("origin_iata") or "DEL"
                    dest_iata = seg.get("destination_iata") or "BOM"

                    owner_carrier_code = owner_code
                    mkt_carrier_code = seg.get("marketing_carrier_code") or owner_code
                    op_carrier_code = seg.get("operating_carrier_code") or owner_code
                    carrier_code = op_carrier_code or mkt_carrier_code or owner_carrier_code

                    dep_str = seg.get("departing_at")
                    if dep_str:
                        try:
                            travel_dt = dt.datetime.fromisoformat(dep_str).date()
                        except Exception:
                            travel_dt = search_date + dt.timedelta(days=15)
                    else:
                        travel_dt = search_date + dt.timedelta(days=15)

                    # Correction 1: Do not construct source_url unless verified retrievable URL
                    source_url = None

                    # Fingerprint construction
                    fp_string = f"DUFFEL|{origin_iata}|{dest_iata}|{travel_dt}|{carrier_code}|{flt_no}|{total_amt}|{offer_id}|{raw_sha256[:12]}"
                    quote_fp = hashlib.sha256(fp_string.encode("utf-8")).hexdigest()

                    raw_input_dict = {
                        "source_id": "SRC_DUFFEL",
                        "source_name": "Duffel API v2 Adapter",
                        "source_url": source_url,
                        "source_request_id": offer_req_id,
                        "source_offer_id": offer_id,
                        "collected_at": search_ts,
                        "search_timestamp": search_ts,
                        "search_date": search_date,
                        "travel_date": travel_dt,
                        "origin_raw": origin_iata,
                        "destination_raw": dest_iata,
                        "airline": carrier_code,
                        "owner_carrier": owner_carrier_code,
                        "marketing_carrier": mkt_carrier_code,
                        "operating_carrier": op_carrier_code,
                        "flight_number": flt_no,
                        "cabin": "ECONOMY",
                        "fare_class": "STANDARD",
                        "trip_type": "ONE_WAY",
                        "stops": seg.get("stops_count", 0),
                        "duration_minutes": duration_mins,
                        "raw_total_fare": f"{total_amt_str} {total_curr}" if total_amt_str else None,
                        "raw_base_fare": f"{base_amt_str} {base_curr}" if base_amt_str else None,
                        "raw_taxes": f"{tax_amt_str} {tax_curr}" if tax_amt_str else None,
                        "raw_fees": None,
                        "base_fare": base_amt,
                        "taxes": tax_amt,
                        "fees": fee_amt,
                        "total_fare": total_amt,
                        "currency": total_curr,
                        # Extra Provenance Metadata
                        "raw_payload_sha256": raw_sha256,
                        "quote_fingerprint": quote_fp,
                        "offer_request_id": offer_req_id,
                        "offer_id": offer_id,
                        "slice_id": slice_id,
                        "segment_id": seg_id,
                        "live_mode": live_mode,
                        "data_classification": data_classification,
                        "is_test_data": (live_mode is False)
                    }
                    quote_records.append(raw_input_dict)

        return quote_records, audit_report, raw_sha256

    @classmethod
    def ingest_duffel_fixture_to_database(
        cls,
        db: Session,
        raw_payload: Any,
        search_timestamp: Optional[dt.datetime] = None
    ) -> List[Observation]:
        """
        Ingests Duffel API response payload through 4A Canonical Normalization and Validation Engine.
        Enforces test data isolation: live_mode=false results are tagged INELIGIBLE for LIVE_MARKET_DATA.
        """
        quote_dicts, audit_report, raw_sha256 = cls.transform_duffel_response_to_raw_quotes(
            raw_payload=raw_payload,
            search_timestamp=search_timestamp
        )

        ingested_observations: List[Observation] = []

        for q_dict in quote_dicts:
            raw_input_schema = RawQuoteInput(
                source_id=q_dict["source_id"],
                source_name=q_dict["source_name"],
                source_url=q_dict["source_url"],
                collected_at=q_dict["collected_at"],
                search_timestamp=q_dict["search_timestamp"],
                search_date=q_dict["search_date"],
                travel_date=q_dict["travel_date"],
                origin_raw=q_dict["origin_raw"],
                destination_raw=q_dict["destination_raw"],
                airline=q_dict["airline"],
                flight_number=q_dict["flight_number"],
                cabin=q_dict["cabin"],
                fare_class=q_dict["fare_class"],
                trip_type=q_dict["trip_type"],
                stops=q_dict["stops"],
                duration_minutes=q_dict["duration_minutes"],
                raw_total_fare=q_dict["raw_total_fare"],
                raw_base_fare=q_dict["raw_base_fare"],
                raw_taxes=q_dict["raw_taxes"],
                raw_fees=q_dict["raw_fees"],
                base_fare=q_dict["base_fare"],
                taxes=q_dict["taxes"],
                fees=q_dict["fees"],
                total_fare=q_dict["total_fare"],
                currency=q_dict["currency"]
            )

            obs = ObservationService.ingest_raw_quote(db=db, raw_input=raw_input_schema)
            obs.raw_payload_sha256 = raw_sha256
            obs.quote_fingerprint = q_dict["quote_fingerprint"]

            # Explicit Test Mode Isolation Guard
            if q_dict.get("live_mode") is False or q_dict.get("is_test_data") is True:
                obs.index_eligibility = "INELIGIBLE"
                reasons = [r for r in (obs.index_eligibility_reasons or []) if r != "INDEX_ELIGIBLE"]
                if "INELIGIBLE_TEST_MODE_DATA" not in reasons:
                    reasons.append("INELIGIBLE_TEST_MODE_DATA")
                obs.index_eligibility_reasons = reasons

            db.commit()
            db.refresh(obs)
            ingested_observations.append(obs)

        return ingested_observations
