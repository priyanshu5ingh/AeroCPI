"""Leakage-safe production forecasting dataset builder for AeroGuide."""
from __future__ import annotations

import datetime as dt
import statistics
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.services.feature_builder_service import FeatureBuilderService
from app.models.observation import Observation
from app.services.production_data_policy import ProductionDataPolicy

TARGET_VERSION = "AEROGUIDE_7D_MARKET_MOVEMENT_V1"
FEATURE_VERSION = "AEROGUIDE_FEATURES_V2"
TARGET_THRESHOLD_PCT = 2.0
FORECAST_HORIZON_DAYS = 7

MODEL_NUMERIC_FEATURES = [
    "days_to_departure", "travel_day_of_week", "search_day_of_week",
    "travel_month", "is_weekend_departure", "current_fare",
    "route_historical_median", "route_p15", "route_p80", "route_min",
    "route_max", "route_std", "route_dispersion", "fare_percentile",
    "fare_to_median_ratio", "trajectory_search_count", "carriers_observed_count",
    "sources_observed_count", "dgca_route_weight", "national_aerocpi_index",
    "observations_in_sample", "recent_1d_change_pct", "recent_3d_change_pct",
    "recent_7d_change_pct", "rolling_std_7", "source_median_spread_pct",
]


def classify_direction(delta_pct: float, threshold_pct: float = TARGET_THRESHOLD_PCT) -> str:
    if delta_pct > threshold_pct:
        return "UP"
    if delta_pct < -threshold_pct:
        return "DOWN"
    return "STABLE"


def _safe_float(value: Any) -> float:
    return 0.0 if value is None else float(value)


def _model_feature_dict(features: Dict[str, Any]) -> Dict[str, Any]:
    row = {key: _safe_float(features.get(key)) for key in MODEL_NUMERIC_FEATURES}
    row["route_id"] = str(features.get("route_id") or "UNKNOWN")
    row["dgca_weight_missing"] = 1.0 if features.get("dgca_route_weight") is None else 0.0
    row["national_index_missing"] = 1.0 if features.get("national_aerocpi_index") is None else 0.0
    return row


class ForecastDatasetService:
    """Constructs supervised targets only from repeated real observations."""

    @classmethod
    def load_observations(cls, db: Session, cutoff: Optional[dt.datetime] = None) -> List[Observation]:
        query = db.query(Observation).filter(
            Observation.search_timestamp.isnot(None),
            Observation.travel_date.isnot(None),
        )
        query = ProductionDataPolicy.apply_forecasting_filters(query)
        if cutoff is not None:
            query = query.filter(Observation.search_timestamp <= cutoff)
        return query.order_by(Observation.search_timestamp.asc(), Observation.observation_id.asc()).all()

    @classmethod
    def build_examples(
        cls,
        db: Session,
        horizon_days: int = FORECAST_HORIZON_DAYS,
        cutoff: Optional[dt.datetime] = None,
    ) -> List[Dict[str, Any]]:
        observations = cls.load_observations(db, cutoff=cutoff)
        daily: Dict[Tuple[str, dt.date, dt.date], Dict[str, Any]] = defaultdict(
            lambda: {"fares": [], "timestamps": []}
        )

        for obs in observations:
            if not ProductionDataPolicy.is_production_observation(obs):
                continue
            search_date = getattr(obs, "search_date", None)
            search_ts = getattr(obs, "search_timestamp", None)
            travel_date = getattr(obs, "travel_date", None)
            route_id = getattr(obs, "route_id", None)
            fare = getattr(obs, "total_fare", None)
            if not (search_date and search_ts and travel_date and route_id and fare):
                continue
            if float(fare) <= 0:
                continue
            key = (route_id.upper(), travel_date, search_date)
            daily[key]["fares"].append(float(fare))
            daily[key]["timestamps"].append(search_ts)

        by_trajectory: Dict[Tuple[str, dt.date], Dict[dt.date, Dict[str, Any]]] = defaultdict(dict)
        for (route_id, travel_date, search_date), payload in daily.items():
            by_trajectory[(route_id, travel_date)][search_date] = {
                "median_fare": float(statistics.median(payload["fares"])),
                "search_timestamp": max(payload["timestamps"]),
            }

        examples: List[Dict[str, Any]] = []
        for (route_id, travel_date), points in by_trajectory.items():
            for prediction_date in sorted(points):
                future_date = prediction_date + dt.timedelta(days=horizon_days)
                if future_date not in points or travel_date <= prediction_date:
                    continue

                prediction_point = points[prediction_date]
                future_point = points[future_date]
                current_fare = prediction_point["median_fare"]
                future_fare = future_point["median_fare"]
                if current_fare <= 0 or future_fare <= 0:
                    continue

                delta_pct = (future_fare - current_fare) / current_fare * 100.0
                prediction_ts = prediction_point["search_timestamp"]
                features = FeatureBuilderService.build_feature_vector_at_timestamp(
                    db=db,
                    route_id=route_id,
                    travel_date_str=travel_date.isoformat(),
                    prediction_timestamp=prediction_ts,
                    carrier_code=None,
                    cabin="ECONOMY",
                )
                if features.get("current_fare") is None:
                    continue

                examples.append({
                    "route_id": route_id,
                    "travel_date": travel_date.isoformat(),
                    "prediction_date": prediction_date.isoformat(),
                    "future_date": future_date.isoformat(),
                    "prediction_timestamp": prediction_ts.isoformat(),
                    "current_fare": round(current_fare, 2),
                    "future_fare": round(future_fare, 2),
                    "target_delta_pct": round(delta_pct, 4),
                    "target_direction": classify_direction(delta_pct),
                    "features": _model_feature_dict(features),
                })

        examples.sort(key=lambda x: (x["prediction_date"], x["route_id"], x["travel_date"]))
        return examples

    @classmethod
    def dataset_summary(cls, examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        routes = sorted({e["route_id"] for e in examples})
        dates = sorted({e["prediction_date"] for e in examples})
        labels = [e["target_direction"] for e in examples]
        span = 0
        if len(dates) >= 2:
            span = (dt.date.fromisoformat(dates[-1]) - dt.date.fromisoformat(dates[0])).days
        return {
            "examples": len(examples),
            "routes": len(routes),
            "prediction_dates": len(dates),
            "prediction_date_span_days": span,
            "label_counts": {k: labels.count(k) for k in ("UP", "STABLE", "DOWN")},
            "feature_version": FEATURE_VERSION,
            "target_version": TARGET_VERSION,
            "target_threshold_pct": TARGET_THRESHOLD_PCT,
            "forecast_horizon_days": FORECAST_HORIZON_DAYS,
        }
