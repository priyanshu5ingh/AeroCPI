"""AeroGuide Feature Engineering & Anti-Leakage Service.
Constructs strictly chronological feature vectors at prediction timestamp t.
Guarantees zero future observation leakage by enforcing search_timestamp <= t across all historical windows.
"""
from __future__ import annotations
import math
import statistics
import datetime as dt
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.observation import Observation
from app.models.route_basket import RouteBasketMember
from app.models.index_run import IndexRun


class FeatureBuilderService:
    """Builds deterministic, leakage-safe feature vectors for airfare movement models."""

    @classmethod
    def build_feature_vector_at_timestamp(
        cls,
        db: Session,
        route_id: str,
        travel_date_str: str,
        prediction_timestamp: dt.datetime,
        carrier_code: Optional[str] = None,
        cabin: str = "ECONOMY"
    ) -> Dict[str, Any]:
        """Constructs a deterministic feature dictionary using ONLY information observed on or before prediction_timestamp."""
        route_id_clean = route_id.upper().strip()
        parts = route_id_clean.split("-")
        origin = parts[0] if len(parts) >= 1 else route_id_clean
        destination = parts[1] if len(parts) >= 2 else ""

        try:
            t_date = dt.datetime.strptime(travel_date_str, "%Y-%m-%d").date()
        except ValueError:
            t_date = prediction_timestamp.date() + dt.timedelta(days=15)

        prediction_date = prediction_timestamp.date()
        days_to_departure = (t_date - prediction_date).days
        if days_to_departure < 0:
            days_to_departure = 0

        # Strict Anti-Leakage Query: Only observations observed at or before prediction_timestamp
        historical_obs = db.query(Observation).filter(
            Observation.route_id == route_id_clean,
            Observation.cabin == cabin.upper(),
            Observation.search_timestamp <= prediction_timestamp
        ).order_by(Observation.search_timestamp.asc()).all()

        all_fares = [float(o.total_fare) for o in historical_obs if o.total_fare]
        
        # Route baseline statistics
        if all_fares:
            sorted_fares = sorted(all_fares)
            n = len(sorted_fares)
            route_median = float(statistics.median(sorted_fares))
            p15_idx = int(0.15 * (n - 1))
            p80_idx = int(0.80 * (n - 1))
            route_p15 = sorted_fares[p15_idx]
            route_p80 = sorted_fares[p80_idx]
            route_min = float(min(sorted_fares))
            route_max = float(max(sorted_fares))
            route_std = float(statistics.stdev(all_fares)) if len(all_fares) > 1 else 0.0
            route_dispersion = (route_p80 - route_p15) / route_median if route_median > 0 else 0.0
        else:
            route_median = 6200.0
            route_p15 = 5500.0
            route_p80 = 7200.0
            route_min = 4800.0
            route_max = 8900.0
            route_std = 600.0
            route_dispersion = 0.27

        # Current quotes on the prediction date (or closest search on or before prediction_timestamp)
        current_quotes = [
            o for o in historical_obs
            if o.travel_date == t_date and (o.search_date == prediction_date or o.search_timestamp == prediction_timestamp)
        ]
        if not current_quotes and historical_obs:
            # Fall back to quotes for this travel date on the latest available search date <= t
            target_travel_obs = [o for o in historical_obs if o.travel_date == t_date]
            if target_travel_obs:
                latest_ts = max(o.search_timestamp for o in target_travel_obs if o.search_timestamp)
                current_quotes = [o for o in target_travel_obs if o.search_timestamp == latest_ts]

        current_fares = [float(o.total_fare) for o in current_quotes if o.total_fare]
        if carrier_code and current_quotes:
            c_matches = [float(o.total_fare) for o in current_quotes if o.carrier_id == carrier_code.upper() and o.total_fare]
            current_fare = c_matches[0] if c_matches else (float(statistics.median(current_fares)) if current_fares else route_median)
        elif current_fares:
            current_fare = float(statistics.median(current_fares))
        else:
            current_fare = route_median

        # Percentile rank of current fare
        if all_fares:
            below_count = sum(1 for f in all_fares if f < current_fare)
            fare_percentile = round((below_count / len(all_fares)) * 100.0, 1)
        else:
            fare_percentile = 50.0

        # Rolling search velocity on or before t
        trajectory_dates = sorted(list({o.search_date for o in historical_obs if o.travel_date == t_date and o.search_date}))
        search_count_to_date = len(trajectory_dates)

        # DGCA traffic weight signal
        basket_member = db.query(RouteBasketMember).filter(
            RouteBasketMember.route_id == route_id_clean
        ).first()
        dgca_weight = float(basket_member.dgca_basket_weight) if basket_member and basket_member.dgca_basket_weight else 0.05

        # National AeroCPI index movement signal from latest run <= t
        latest_index_run = db.query(IndexRun).filter(
            IndexRun.run_timestamp <= prediction_timestamp
        ).order_by(IndexRun.run_timestamp.desc()).first()
        index_headline = float(latest_index_run.index_value) if latest_index_run and latest_index_run.index_value else 100.0

        carriers_present = list({o.carrier_id for o in current_quotes if o.carrier_id})
        sources_present = list({o.source_id for o in current_quotes if o.source_id})

        return {
            # Metadata & Provenance
            "route_id": route_id_clean,
            "origin": origin,
            "destination": destination,
            "travel_date": travel_date_str,
            "prediction_timestamp": prediction_timestamp.isoformat(),
            "cabin": cabin.upper(),
            "carrier_code": carrier_code.upper() if carrier_code else "ALL",
            
            # Temporal dimensions
            "days_to_departure": days_to_departure,
            "travel_day_of_week": t_date.weekday(), # 0 = Mon, 6 = Sun
            "search_day_of_week": prediction_date.weekday(),
            "travel_month": t_date.month,
            "is_weekend_departure": t_date.weekday() in [5, 6],
            
            # Fare & Price Distribution Features (observed <= t)
            "current_fare": current_fare,
            "route_historical_median": route_median,
            "route_p15": route_p15,
            "route_p50": route_median,
            "route_p80": route_p80,
            "route_min": route_min,
            "route_max": route_max,
            "route_std": round(route_std, 2),
            "route_dispersion": round(route_dispersion, 4),
            "fare_percentile": fare_percentile,
            "fare_to_median_ratio": round(current_fare / route_median, 4) if route_median > 0 else 1.0,
            
            # Trajectory & Market Density Features
            "trajectory_search_count": search_count_to_date,
            "carriers_observed_count": len(carriers_present),
            "sources_observed_count": len(sources_present),
            "dgca_route_weight": dgca_weight,
            "national_aerocpi_index": index_headline,
            
            # Audit & Integrity
            "observations_in_sample": len(historical_obs),
            "anti_leakage_guarantee": "ENFORCED_SEARCH_TIMESTAMP_LEQ_T"
        }
