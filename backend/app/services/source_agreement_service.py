"""
AeroCPI Source Agreement & Data Health Service (Milestone 4C.2)
- Compares eligible observations across multiple sources (e.g. Google Flights, Duffel) without merging fares
- Computes source-wise descriptive statistics and cross-source agreement metrics
- Evaluates deterministic data health classifications: HEALTHY, DEGRADED, INSUFFICIENT
- Every health classification contains explicit machine-readable reason codes
- Zero composite Trust Score calculation (raw multi-dimensional health metrics)
- Zero changes to mathematical index formulas
- Test-mode data is strictly excluded from production cross-source agreement calculations
"""
from __future__ import annotations
import math
import datetime as dt
from typing import Dict, List, Any, Optional
from collections import Counter
from sqlalchemy.orm import Session

from app.models.observation import Observation
from app.services.observation_quality_service import calculate_price_distribution, classify_observation_data



def is_observation_comparable(
    obs: Any,
    route_id: str,
    travel_date: dt.date,
    horizon: int,
    cabin: str = "ECONOMY",
    collection_date: Optional[dt.date] = None,
) -> bool:
    """
    Checks if an observation is strictly comparable to the target evaluation slice:
    (route_id, travel_date, horizon, cabin, collection_date).
    """
    # 1. Route check
    if getattr(obs, "route_id", None) != route_id:
        return False

    # 2. Travel date check
    obs_td = getattr(obs, "travel_date", None)
    if isinstance(obs_td, str):
        try:
            obs_td = dt.date.fromisoformat(obs_td)
        except Exception:
            return False
    elif isinstance(obs_td, dt.datetime):
        obs_td = obs_td.date()
    if obs_td != travel_date:
        return False

    # 3. Horizon check
    obs_horizon = getattr(obs, "booking_horizon_days", None)
    if obs_horizon is None:
        obs_horizon = getattr(obs, "advance_purchase_days", None)
    if obs_horizon is not None:
        try:
            obs_horizon = int(obs_horizon)
        except (ValueError, TypeError):
            return False
    if obs_horizon != horizon:
        return False

    # 4. Cabin check
    obs_cabin = str(getattr(obs, "cabin", "ECONOMY") or "ECONOMY").strip().upper()
    if obs_cabin != cabin.strip().upper():
        return False

    # 5. Collection date check (if specified)
    if collection_date is not None:
        obs_cd = getattr(obs, "search_date", None)
        if obs_cd is None:
            obs_cd = getattr(obs, "collection_date", None)
        if isinstance(obs_cd, str):
            try:
                obs_cd = dt.date.fromisoformat(obs_cd)
            except Exception:
                return False
        elif isinstance(obs_cd, dt.datetime):
            obs_cd = obs_cd.date()
        if obs_cd != collection_date:
            return False

    return True


class SourceAgreementService:
    EXPECTED_DEFAULT_SOURCES = ["SRC_GOOGLE_FLIGHTS", "SRC_DUFFEL"]
    DEFAULT_MIN_OBSERVATIONS_PER_SOURCE = 5

    @classmethod
    def evaluate_source_agreement(
        cls,
        observations: List[Observation],
        route_id: str,
        travel_date: dt.date,
        horizon: int,
        cabin: str = "ECONOMY",
        collection_date: Optional[dt.date] = None,
        expected_sources: Optional[List[str]] = None,
        min_observations_per_source: int = DEFAULT_MIN_OBSERVATIONS_PER_SOURCE
    ) -> Dict[str, Any]:
        """
        Pure deterministic function: takes a list of canonical observations and evaluates
        source agreement and data health status with explicit machine-readable reason codes.
        Enforces sample sufficiency per source (default N >= 5) before HEALTHY can be returned.
        Only strictly comparable observations matching (route_id, travel_date, horizon, cabin, collection_date)
        are admitted into source-wise pricing and cross-source comparisons.
        """
        cabin_clean = cabin.strip().upper()
        target_expected_sources = expected_sources or cls.EXPECTED_DEFAULT_SOURCES

        # 0. Isolate strictly comparable observations from non-comparable observations
        comparable_obs: List[Observation] = []
        non_comparable_obs: List[Observation] = []

        for obs in observations:
            if is_observation_comparable(obs, route_id, travel_date, horizon, cabin_clean, collection_date):
                comparable_obs.append(obs)
            else:
                non_comparable_obs.append(obs)

        # 1. Catalog comparable observations by source and classification
        source_all_obs: Dict[str, List[Observation]] = {}
        source_eligible_obs: Dict[str, List[Observation]] = {}
        source_test_obs: Dict[str, List[Observation]] = {}

        for obs in comparable_obs:
            src_id = obs.source_id or "UNKNOWN_SOURCE"
            source_all_obs.setdefault(src_id, []).append(obs)

            # Classify data
            d_class = classify_observation_data(obs)
            inelig_status = str(getattr(obs, "index_eligibility", "INELIGIBLE") or "INELIGIBLE").upper()
            val_status = str(getattr(obs, "validation_status", "ACCEPT") or "ACCEPT").upper()

            # Eligible production observations MUST be ELIGIBLE, LIVE_MARKET_DATA, and non-rejected
            if inelig_status == "ELIGIBLE" and d_class == "LIVE_MARKET_DATA" and val_status != "REJECT":
                source_eligible_obs.setdefault(src_id, []).append(obs)
            elif d_class == "TEST_DATA":
                source_test_obs.setdefault(src_id, []).append(obs)

        # 2. Compute source-wise statistics for each source
        all_sources = sorted(list(set(list(source_all_obs.keys()) + target_expected_sources)))
        source_metrics: Dict[str, Any] = {}

        for src in all_sources:
            all_list = source_all_obs.get(src, [])
            el_list = source_eligible_obs.get(src, [])
            el_prices = [float(o.total_fare) for o in el_list if getattr(o, "total_fare", None) is not None and float(o.total_fare) > 0]
            price_dist = calculate_price_distribution(el_prices)

            source_metrics[src] = {
                "total_observations_count": len(all_list),
                "eligible_observations_count": len(el_list),
                "has_eligible_data": len(el_list) > 0,
                "is_sample_sufficient": len(el_list) >= min_observations_per_source,
                "median_fare": price_dist["median"],
                "mean_fare": price_dist["mean"],
                "min_fare": price_dist["min"],
                "max_fare": price_dist["max"],
                "dispersion": price_dist["dispersion"]
            }

        # 3. Cross-Source Agreement Analysis (across eligible production sources)
        active_eligible_sources = [s for s, m in source_metrics.items() if m["has_eligible_data"]]
        k_active = len(active_eligible_sources)

        total_expected = len(target_expected_sources)
        source_coverage_ratio = round(k_active / total_expected, 4) if total_expected > 0 else 0.0

        if k_active == 0:
            agreement_state = "INSUFFICIENT_COMPARABLE_DATA"
            health_status = "INSUFFICIENT"
            if len(comparable_obs) == 0:
                if len(observations) == 0:
                    health_reasons = ["INSUFFICIENT_NO_OBSERVATIONS"]
                else:
                    health_reasons = ["INSUFFICIENT_NO_COMPARABLE_OBSERVATIONS"]
            else:
                health_reasons = ["INSUFFICIENT_NO_ELIGIBLE_DATA"]
            abs_median_diff = None
            pct_median_diff = None
            obs_imbalance_ratio = 0.0
            obs_imbalance_index = 0.0
            sample_sufficient = False

        elif k_active == 1:
            agreement_state = "SINGLE_SOURCE"
            health_status = "DEGRADED"
            health_reasons = ["DEGRADED_SINGLE_SOURCE_ONLY"]
            abs_median_diff = None
            pct_median_diff = None
            obs_imbalance_ratio = 1.0
            obs_imbalance_index = 1.0
            sample_sufficient = source_metrics[active_eligible_sources[0]]["eligible_observations_count"] >= min_observations_per_source

        else:
            agreement_state = "AGREEMENT_AVAILABLE"
            active_medians = [source_metrics[s]["median_fare"] for s in active_eligible_sources if source_metrics[s]["median_fare"] is not None]
            active_counts = [source_metrics[s]["eligible_observations_count"] for s in active_eligible_sources]

            min_med = min(active_medians)
            max_med = max(active_medians)
            abs_median_diff = round(max_med - min_med, 2)
            avg_med = sum(active_medians) / len(active_medians)
            pct_median_diff = round((abs_median_diff / avg_med) * 100.0, 2) if avg_med > 0 else 0.0

            min_cnt = min(active_counts)
            max_cnt = max(active_counts)
            obs_imbalance_ratio = round(max_cnt / min_cnt, 2) if min_cnt > 0 else float(max_cnt)
            obs_imbalance_index = round((max_cnt - min_cnt) / max_cnt, 4) if max_cnt > 0 else 0.0

            sample_sufficient = all(c >= min_observations_per_source for c in active_counts)

            # Health classification evaluation
            health_reasons = []
            if not sample_sufficient:
                health_reasons.append("DEGRADED_INSUFFICIENT_SAMPLE_SIZE")
            if pct_median_diff > 10.0:
                health_reasons.append("DEGRADED_LARGE_MEDIAN_DISCREPANCY")
            if obs_imbalance_ratio > 4.0:
                health_reasons.append("DEGRADED_SAMPLE_SIZE_IMBALANCE")

            if len(health_reasons) > 0:
                health_status = "DEGRADED"
            else:
                health_status = "HEALTHY"
                health_reasons = ["HEALTHY_MULTI_SOURCE_AGREEMENT"]

        report = {
            "metadata": {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "route_id": route_id,
                "travel_date": travel_date.isoformat(),
                "horizon_days": horizon,
                "horizon_code": f"T+{horizon}",
                "cabin": cabin_clean,
                "collection_date": collection_date.isoformat() if collection_date else None,
                "expected_sources": target_expected_sources,
                "min_observations_per_source": min_observations_per_source,
                "total_input_observations_count": len(observations),
                "comparable_observations_count": len(comparable_obs),
                "non_comparable_observations_excluded_count": len(non_comparable_obs),
                "note": "Source Agreement & Data Health Layer (Milestone 4C.2). No composite Trust Score calculated."
            },
            "comparability_audit": {
                "total_input_observations": len(observations),
                "comparable_observations_count": len(comparable_obs),
                "non_comparable_observations_excluded_count": len(non_comparable_obs),
                "target_specification": {
                    "route_id": route_id,
                    "travel_date": travel_date.isoformat(),
                    "horizon_days": horizon,
                    "cabin": cabin_clean,
                    "collection_date": collection_date.isoformat() if collection_date else None
                },
                "is_fully_comparable": len(non_comparable_obs) == 0
            },
            "health_evaluation": {
                "health_status": health_status,
                "agreement_state": agreement_state,
                "health_reasons": health_reasons,
                "is_healthy": health_status == "HEALTHY",
                "is_degraded": health_status == "DEGRADED",
                "is_insufficient": health_status == "INSUFFICIENT"
            },
            "cross_source_agreement": {
                "active_eligible_sources_count": k_active,
                "active_eligible_sources": active_eligible_sources,
                "source_coverage_ratio": source_coverage_ratio,
                "absolute_median_difference": abs_median_diff,
                "percentage_median_difference": pct_median_diff,
                "observation_count_imbalance_ratio": obs_imbalance_ratio,
                "observation_count_imbalance_index": obs_imbalance_index,
                "sample_sufficiency": {
                    "min_required_per_source": min_observations_per_source,
                    "is_sample_sufficient": sample_sufficient
                }
            },
            "source_wise_metrics": source_metrics,
            "test_mode_isolation": {
                "test_data_sources_count": len(source_test_obs),
                "test_data_observations_count": sum(len(obs_l) for obs_l in source_test_obs.values()),
                "test_data_excluded_from_production_agreement": True
            }
        }

        return report

    @classmethod
    def calculate_route_health_report(
        cls,
        db: Session,
        route_id: str,
        travel_date: dt.date,
        horizon: int,
        cabin: str = "ECONOMY",
        collection_date: Optional[dt.date] = None,
        expected_sources: Optional[List[str]] = None,
        min_observations_per_source: int = DEFAULT_MIN_OBSERVATIONS_PER_SOURCE
    ) -> Dict[str, Any]:
        """
        Queries the database for observations matching the target criteria and evaluates
        source agreement and data health.
        """
        cabin_clean = cabin.strip().upper()
        query = db.query(Observation).filter(
            Observation.route_id == route_id,
            Observation.travel_date == travel_date,
            Observation.booking_horizon_days == horizon,
            Observation.cabin == cabin_clean
        )

        if collection_date is not None:
            query = query.filter(Observation.search_date == collection_date)

        observations = query.all()

        return cls.evaluate_source_agreement(
            observations=observations,
            route_id=route_id,
            travel_date=travel_date,
            horizon=horizon,
            cabin=cabin_clean,
            collection_date=collection_date,
            expected_sources=expected_sources,
            min_observations_per_source=min_observations_per_source
        )
