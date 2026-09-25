"""Leakage-safe AeroGuide feature engineering."""
from __future__ import annotations

import datetime as dt
import statistics
from collections import defaultdict
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.observation import Observation
from app.models.route_basket import RouteBasketMember
from app.models.index_run import IndexRun
from app.services.production_data_policy import ProductionDataPolicy


class FeatureBuilderService:
    """Builds prediction-time features from real observations only."""

    FEATURE_VERSION = "AEROGUIDE_FEATURES_V2"

    @classmethod
    def build_feature_vector_at_timestamp(
        cls,
        db: Session,
        route_id: str,
        travel_date_str: str,
        prediction_timestamp: dt.datetime,
        carrier_code: Optional[str] = None,
        cabin: str = "ECONOMY",
    ) -> Dict[str, Any]:
        route_id_clean = route_id.upper().strip()
        try:
            travel_date = dt.date.fromisoformat(travel_date_str)
        except ValueError as exc:
            raise ValueError(f"Invalid travel_date: {travel_date_str}") from exc

        prediction_timestamp = (
            prediction_timestamp
            if prediction_timestamp.tzinfo is not None
            else prediction_timestamp.replace(tzinfo=dt.timezone.utc)
        )

        query = db.query(Observation).filter(
            Observation.route_id == route_id_clean,
            Observation.cabin == cabin.upper(),
            Observation.search_timestamp.isnot(None),
            Observation.search_timestamp <= prediction_timestamp,
        )
        query = ProductionDataPolicy.apply_forecasting_filters(query)
        historical_obs = query.order_by(Observation.search_timestamp.asc()).all()

        daily_fares: Dict[dt.date, list[float]] = defaultdict(list)
        daily_timestamps: Dict[dt.date, list[dt.datetime]] = defaultdict(list)
        current_quotes = []

        for obs in historical_obs:
            if obs.total_fare is None or float(obs.total_fare) <= 0:
                continue
            obs_date = obs.search_date or obs.search_timestamp.date()
            fare = float(obs.total_fare)
            if obs.travel_date == travel_date:
                daily_fares[obs_date].append(fare)
                daily_timestamps[obs_date].append(obs.search_timestamp)
                if obs_date == prediction_timestamp.date():
                    current_quotes.append(obs)

        daily_points = [
            {
                "date": search_date,
                "median": float(statistics.median(daily_fares[search_date])),
                "timestamp": max(daily_timestamps[search_date]),
            }
            for search_date in sorted(daily_fares)
        ]

        current_fare = (
            float(statistics.median([float(o.total_fare) for o in current_quotes]))
            if current_quotes
            else (
                daily_points[-1]["median"]
                if daily_points and daily_points[-1]["date"] == prediction_timestamp.date()
                else None
            )
        )

        route_fares = [float(o.total_fare) for o in historical_obs if o.total_fare and float(o.total_fare) > 0]
        route_median = float(statistics.median(route_fares)) if route_fares else None

        route_p15 = route_p80 = route_std = route_dispersion = None
        if route_fares:
            ordered = sorted(route_fares)
            n = len(ordered)
            route_p15 = float(ordered[int(0.15 * (n - 1))])
            route_p80 = float(ordered[int(0.80 * (n - 1))])
            route_std = float(statistics.stdev(route_fares)) if len(route_fares) > 1 else 0.0
            route_dispersion = (
                (route_p80 - route_p15) / route_median
                if route_median and route_median > 0
                else None
            )

        fare_percentile = None
        fare_to_median_ratio = None
        if current_fare is not None and route_fares:
            fare_percentile = round(
                sum(1 for fare in route_fares if fare < current_fare) / len(route_fares) * 100.0,
                1,
            )
        if current_fare is not None and route_median and route_median > 0:
            fare_to_median_ratio = round(current_fare / route_median, 4)

        medians = [point["median"] for point in daily_points]
        recent_1d = recent_3d = recent_7d = None
        if len(medians) >= 2 and medians[-2]:
            recent_1d = (medians[-1] - medians[-2]) / medians[-2] * 100.0
        if len(medians) >= 4 and medians[-4]:
            recent_3d = (medians[-1] - medians[-4]) / medians[-4] * 100.0
        if len(medians) >= 8 and medians[-8]:
            recent_7d = (medians[-1] - medians[-8]) / medians[-8] * 100.0

        rolling_window = medians[-7:]
        rolling_std_7 = statistics.pstdev(rolling_window) if len(rolling_window) >= 2 else 0.0

        source_medians: Dict[str, list[float]] = defaultdict(list)
        for obs in current_quotes:
            if obs.source_id and obs.total_fare and float(obs.total_fare) > 0:
                source_medians[obs.source_id].append(float(obs.total_fare))
        source_values = [statistics.median(values) for values in source_medians.values() if values]
        if len(source_values) >= 2:
            median_source = statistics.median(source_values)
            source_spread = (max(source_values) - min(source_values)) / median_source * 100.0 if median_source else 0.0
        else:
            source_spread = 0.0

        basket_member = db.query(RouteBasketMember).filter(RouteBasketMember.route_id == route_id_clean).first()
        dgca_weight = (
            float(basket_member.dgca_basket_weight)
            if basket_member and basket_member.dgca_basket_weight is not None
            else None
        )

        latest_index_run = db.query(IndexRun).filter(
            IndexRun.run_timestamp <= prediction_timestamp
        ).order_by(IndexRun.run_timestamp.desc()).first()
        national_index = (
            float(latest_index_run.index_value)
            if latest_index_run and latest_index_run.index_value is not None
            else None
        )

        carriers_present = sorted({o.carrier_id for o in current_quotes if o.carrier_id})
        sources_present = sorted({o.source_id for o in current_quotes if o.source_id})

        return {
            "feature_version": cls.FEATURE_VERSION,
            "route_id": route_id_clean,
            "origin": route_id_clean.split("-")[0],
            "destination": route_id_clean.split("-")[1] if "-" in route_id_clean else "",
            "travel_date": travel_date_str,
            "prediction_timestamp": prediction_timestamp.isoformat(),
            "cabin": cabin.upper(),
            "carrier_code": carrier_code.upper() if carrier_code else "ALL",
            "days_to_departure": max(0, (travel_date - prediction_timestamp.date()).days),
            "travel_day_of_week": travel_date.weekday(),
            "search_day_of_week": prediction_timestamp.date().weekday(),
            "travel_month": travel_date.month,
            "is_weekend_departure": travel_date.weekday() in (5, 6),
            "current_fare": current_fare,
            "route_historical_median": route_median,
            "route_p15": route_p15,
            "route_p50": route_median,
            "route_p80": route_p80,
            "route_min": min(route_fares) if route_fares else None,
            "route_max": max(route_fares) if route_fares else None,
            "route_std": round(route_std, 2) if route_std is not None else None,
            "route_dispersion": round(route_dispersion, 4) if route_dispersion is not None else None,
            "fare_percentile": fare_percentile,
            "fare_to_median_ratio": fare_to_median_ratio,
            "trajectory_search_count": len(daily_points),
            "carriers_observed_count": len(carriers_present),
            "sources_observed_count": len(sources_present),
            "dgca_route_weight": dgca_weight,
            "national_aerocpi_index": national_index,
            "observations_in_sample": len(historical_obs),
            "recent_1d_change_pct": round(recent_1d, 4) if recent_1d is not None else None,
            "recent_3d_change_pct": round(recent_3d, 4) if recent_3d is not None else None,
            "recent_7d_change_pct": round(recent_7d, 4) if recent_7d is not None else None,
            "rolling_std_7": round(rolling_std_7, 4),
            "source_median_spread_pct": round(source_spread, 4),
            "anti_leakage_guarantee": "ENFORCED_SEARCH_TIMESTAMP_LEQ_T_AND_PRODUCTION_DATA_ONLY",
        }

    @classmethod
    def build_prediction_features(
        cls,
        db: Session,
        route_id: str,
        travel_date_str: str,
        search_timestamp: Optional[dt.datetime] = None,
        carrier_code: Optional[str] = None,
        cabin: str = "ECONOMY",
    ) -> Dict[str, Any]:
        return cls.build_feature_vector_at_timestamp(
            db=db,
            route_id=route_id,
            travel_date_str=travel_date_str,
            prediction_timestamp=search_timestamp or dt.datetime.now(dt.timezone.utc),
            carrier_code=carrier_code,
            cabin=cabin
        )
