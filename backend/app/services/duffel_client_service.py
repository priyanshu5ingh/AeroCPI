"""
AeroCPI Duffel API v2 Client & Response Audit Service
- Isolated, read-only offer_request connectivity
- Strict environment-variable based credentials (DUFFEL_API_TOKEN)
- Never hardcodes, logs, or persists API tokens or Authorization headers
- Preserves complete raw response bytes with SHA-256 digests
- Credential-free request metadata separation
- Recursive hierarchical offer/slice/segment inspection
- Explicit TEST_DATA vs LIVE_MARKET_DATA classification (live_mode=false is TEST_DATA)
- Zero value inference (missing components remain None)
"""
from __future__ import annotations
import os
import json
import hashlib
import datetime as dt
from typing import Dict, List, Any, Tuple, Optional
import httpx
from dotenv import load_dotenv

DUFFEL_API_URL = "https://api.duffel.com/air/offer_requests?return_offers=true"
DUFFEL_VERSION_HEADER = "v2"


class DuffelClientService:
    @staticmethod
    def get_api_token() -> str:
        """Retrieves DUFFEL_API_TOKEN from environment. Raises ValueError if missing."""
        load_dotenv()
        token = os.getenv("DUFFEL_API_TOKEN")
        if not token or not token.strip():
            raise ValueError("DUFFEL_API_TOKEN environment variable is not set.")
        return token.strip()

    @classmethod
    def create_offer_request(
        cls,
        origin: str,
        dest: str,
        departure_date: str,
        cabin_class: str = "economy",
        passengers_count: int = 1,
        timeout: float = 30.0,
        api_token: Optional[str] = None
    ) -> Tuple[Dict[str, Any], bytes, Dict[str, Any], Dict[str, Any]]:
        """
        Executes a controlled read-only POST /air/offer_requests?return_offers=true API call.
        Returns: (metadata_dict, raw_response_bytes, response_json_dict, audit_report_dict)
        """
        token = api_token or cls.get_api_token()

        origin_clean = origin.upper().strip()
        dest_clean = dest.upper().strip()
        cabin_clean = cabin_class.lower().strip()

        headers = {
            "Authorization": f"Bearer {token}",
            "Duffel-Version": DUFFEL_VERSION_HEADER,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "gzip"
        }

        payload = {
            "data": {
                "slices": [
                    {
                        "origin": origin_clean,
                        "destination": dest_clean,
                        "departure_date": departure_date
                    }
                ],
                "passengers": [
                    {"type": "adult"} for _ in range(passengers_count)
                ],
                "cabin_class": cabin_clean
            }
        }

        req_ts_utc = dt.datetime.now(dt.timezone.utc)

        with httpx.Client(timeout=timeout) as client:
            resp = client.post(DUFFEL_API_URL, headers=headers, json=payload)

        resp_ts_utc = dt.datetime.now(dt.timezone.utc)
        raw_bytes = resp.content
        raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()

        try:
            resp_json = resp.json()
        except Exception:
            resp_json = {}

        audit_report = cls.audit_offer_request_response(resp_json)

        # Build credential-free request metadata
        metadata = {
            "request_timestamp_utc": req_ts_utc.isoformat(),
            "response_timestamp_utc": resp_ts_utc.isoformat(),
            "endpoint": "POST /air/offer_requests?return_offers=true",
            "http_status": resp.status_code,
            "offer_request_id": audit_report.get("offer_request_id"),
            "live_mode": audit_report.get("live_mode"),
            "data_classification": audit_report.get("data_classification"),
            "route": f"{origin_clean}-{dest_clean}",
            "travel_date": departure_date,
            "cabin": cabin_clean,
            "passenger_count": passengers_count,
            "raw_response_sha256": raw_sha256
        }

        return metadata, raw_bytes, resp_json, audit_report

    @classmethod
    def audit_offer_request_response(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively audits a Duffel API v2 offer_request response dictionary.
        Does not infer missing values. Classifies live_mode=false as TEST_DATA.
        """
        if not isinstance(data, dict):
            data = {}

        offer_req = data.get("data")
        if not isinstance(offer_req, dict):
            offer_req = {}

        offer_req_id = offer_req.get("id")
        live_mode = offer_req.get("live_mode")

        # Classification rule: live_mode=false is strictly TEST_DATA
        if live_mode is False:
            classification = "TEST_DATA"
        elif live_mode is True:
            classification = "LIVE_MARKET_DATA"
        else:
            classification = "UNKNOWN"

        raw_offers = offer_req.get("offers")
        if not isinstance(raw_offers, list):
            raw_offers = []

        audited_offers: List[Dict[str, Any]] = []

        for offer in raw_offers:
            if not isinstance(offer, dict):
                continue

            owner = offer.get("owner") or {}
            owner_name = owner.get("name") if isinstance(owner, dict) else None
            owner_code = owner.get("iata_code") if isinstance(owner, dict) else None

            # Slices & Segments recursive inspection
            raw_slices = offer.get("slices")
            if not isinstance(raw_slices, list):
                raw_slices = []

            audited_slices: List[Dict[str, Any]] = []
            for sl in raw_slices:
                if not isinstance(sl, dict):
                    continue

                sl_origin = sl.get("origin") or {}
                sl_dest = sl.get("destination") or {}

                raw_segments = sl.get("segments")
                if not isinstance(raw_segments, list):
                    raw_segments = []

                audited_segments: List[Dict[str, Any]] = []
                for seg in raw_segments:
                    if not isinstance(seg, dict):
                        continue

                    mkt_carrier = seg.get("marketing_carrier") or {}
                    op_carrier = seg.get("operating_carrier") or {}
                    seg_origin = seg.get("origin") or {}
                    seg_dest = seg.get("destination") or {}

                    flt_no = (
                        seg.get("marketing_carrier_flight_number")
                        or seg.get("operating_carrier_flight_number")
                    )

                    stops_list = seg.get("stops")
                    stops_count = len(stops_list) if isinstance(stops_list, list) else 0

                    audited_seg = {
                        "segment_id": seg.get("id"),
                        "marketing_carrier_name": mkt_carrier.get("name") if isinstance(mkt_carrier, dict) else None,
                        "marketing_carrier_code": mkt_carrier.get("iata_code") if isinstance(mkt_carrier, dict) else None,
                        "operating_carrier_name": op_carrier.get("name") if isinstance(op_carrier, dict) else None,
                        "operating_carrier_code": op_carrier.get("iata_code") if isinstance(op_carrier, dict) else None,
                        "flight_number": flt_no,
                        "origin_iata": seg_origin.get("iata_code") if isinstance(seg_origin, dict) else None,
                        "origin_name": seg_origin.get("name") if isinstance(seg_origin, dict) else None,
                        "origin_city": seg_origin.get("city_name") if isinstance(seg_origin, dict) else None,
                        "destination_iata": seg_dest.get("iata_code") if isinstance(seg_dest, dict) else None,
                        "destination_name": seg_dest.get("name") if isinstance(seg_dest, dict) else None,
                        "destination_city": seg_dest.get("city_name") if isinstance(seg_dest, dict) else None,
                        "departing_at": seg.get("departing_at"),
                        "arriving_at": seg.get("arriving_at"),
                        "stops_count": stops_count
                    }
                    audited_segments.append(audited_seg)

                audited_sl = {
                    "slice_id": sl.get("id"),
                    "duration": sl.get("duration"),
                    "origin_iata": sl_origin.get("iata_code") if isinstance(sl_origin, dict) else None,
                    "destination_iata": sl_dest.get("iata_code") if isinstance(sl_dest, dict) else None,
                    "segments_count": len(audited_segments),
                    "segments": audited_segments
                }
                audited_slices.append(audited_sl)

            audited_offer = {
                "offer_id": offer.get("id"),
                "owner_name": owner_name,
                "owner_code": owner_code,
                "live_mode": offer.get("live_mode"),
                "expires_at": offer.get("expires_at"),
                "base_amount": offer.get("base_amount"),
                "base_currency": offer.get("base_currency"),
                "tax_amount": offer.get("tax_amount"),
                "tax_currency": offer.get("tax_currency"),
                "total_amount": offer.get("total_amount"),
                "total_currency": offer.get("total_currency"),
                "slices_count": len(audited_slices),
                "slices": audited_slices
            }
            audited_offers.append(audited_offer)

        # Component availability assessment
        has_base = any(o.get("base_amount") is not None for o in audited_offers)
        has_tax = any(o.get("tax_amount") is not None for o in audited_offers)
        has_total = any(o.get("total_amount") is not None for o in audited_offers)
        has_flt_no = any(
            seg.get("flight_number") is not None
            for o in audited_offers
            for sl in o.get("slices", [])
            for seg in sl.get("segments", [])
        )
        has_exp = any(o.get("expires_at") is not None for o in audited_offers)

        component_availability = {
            "has_offer_request_id": offer_req_id is not None,
            "has_live_mode": live_mode is not None,
            "has_offers": len(audited_offers) > 0,
            "has_base_amount": has_base,
            "has_tax_amount": has_tax,
            "has_total_amount": has_total,
            "has_flight_number": has_flt_no,
            "has_offer_expiry": has_exp
        }

        return {
            "offer_request_id": offer_req_id,
            "live_mode": live_mode,
            "data_classification": classification,
            "offers_count": len(audited_offers),
            "component_availability": component_availability,
            "offers": audited_offers
        }
