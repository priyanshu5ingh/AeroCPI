"""
AeroCPI Multi-Source Observation Harmonization Service
- Queries co-existing raw observations across multiple sources (e.g. Google Flights, Duffel API)
- Maps and compares observations side-by-side through the 4A Canonical Observation Contract
- Preserves source-specific breakdown status (TOTAL_ONLY vs PARTIAL_BREAKDOWN/COMPLETE_BREAKDOWN)
- Preserves separated carrier roles (owner_carrier, marketing_carrier, operating_carrier)
- Strictly prevents combining/merging distinct source fares into a single observation
- Strictly does NOT compute Trust Scores or alter statistical index formulas
"""
from __future__ import annotations
import datetime as dt
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.models.observation import Observation


class HarmonizationService:
    @classmethod
    def compare_route_observations(
        cls,
        db: Session,
        route_id: str,
        travel_date: dt.date,
        horizon_days: Optional[int] = None,
        cabin_class: str = "ECONOMY"
    ) -> Dict[str, Any]:
        """
        Queries co-existing observations for a specific route, travel_date, horizon, and cabin class.
        Returns a multi-source harmonization comparison report.
        """
        cabin_clean = cabin_class.strip().upper()
        query = db.query(Observation).filter(
            Observation.route_id == route_id,
            Observation.travel_date == travel_date,
            Observation.cabin == cabin_clean
        )

        if horizon_days is not None:
            query = query.filter(Observation.booking_horizon_days == horizon_days)

        observations = query.order_by(Observation.created_at.desc()).all()

        harmonized_records: List[Dict[str, Any]] = []
        sources_seen = set()

        for obs in observations:
            sources_seen.add(obs.source_id)

            # Extract carrier roles safely from baggage_information or attributes
            bag_info = obs.baggage_information or {}
            owner_carrier = bag_info.get("owner_carrier") or obs.airline
            mkt_carrier = bag_info.get("marketing_carrier") or obs.airline
            op_carrier = bag_info.get("operating_carrier") or obs.airline
            req_id = bag_info.get("source_request_id")
            off_id = bag_info.get("source_offer_id")

            base_f = float(obs.base_fare) if obs.base_fare is not None else None
            taxes_f = float(obs.taxes) if obs.taxes is not None else None
            fees_f = float(obs.fees) if obs.fees is not None else (float(obs.mandatory_fees) if obs.mandatory_fees is not None else None)
            total_f = float(obs.total_fare) if obs.total_fare is not None else 0.0

            rec = {
                "observation_id": obs.observation_id,
                "source_id": obs.source_id,
                "source_name": obs.source_name or obs.source_id,
                "source_request_id": req_id,
                "source_offer_id": off_id,
                "observation_timestamp": (obs.search_timestamp or obs.collected_at or obs.created_at).isoformat(),
                "search_date": obs.search_date.isoformat() if obs.search_date else None,
                "travel_date": obs.travel_date.isoformat(),
                "booking_horizon_days": obs.booking_horizon_days,
                "horizon_code": obs.horizon_code,
                "route_id": obs.route_id,
                "total_fare": total_f,
                "currency": obs.currency,
                "component_availability": {
                    "breakdown_status": obs.breakdown_status,
                    "base_fare": base_f,
                    "taxes": taxes_f,
                    "fees": fees_f,
                    "has_base_fare": base_f is not None,
                    "has_taxes": taxes_f is not None,
                    "has_fees": fees_f is not None
                },
                "carrier": {
                    "airline": obs.airline,
                    "owner_carrier": owner_carrier,
                    "marketing_carrier": mkt_carrier,
                    "operating_carrier": op_carrier
                },
                "flight_number": obs.flight_number,
                "cabin": obs.cabin,
                "stops": obs.stops,
                "stops_status": obs.stops_status,
                "duration_minutes": obs.duration_minutes,
                "validation_status": obs.validation_status,
                "validation_reasons": obs.validation_reasons or [],
                "index_eligibility": obs.index_eligibility,
                "index_eligibility_reasons": obs.index_eligibility_reasons or [],
                "raw_payload_sha256": obs.raw_payload_sha256,
                "quote_fingerprint": obs.quote_fingerprint
            }
            harmonized_records.append(rec)

        return {
            "disclaimer": "Controlled harmonization fixture — not a claim of cross-source offer identity.",
            "route_id": route_id,
            "travel_date": travel_date.isoformat(),
            "horizon_days": horizon_days,
            "cabin_class": cabin_clean,
            "total_observations_count": len(harmonized_records),
            "sources_count": len(sources_seen),
            "sources_represented": sorted(list(sources_seen)),
            "observations": harmonized_records
        }
