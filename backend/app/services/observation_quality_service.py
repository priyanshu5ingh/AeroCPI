"""
AeroCPI Observation Quality Service (Milestone 4C.1)
- Calculates deterministic, reproducible data quality metrics for a specified:
  route_id + travel_date + horizon + cabin + collection_date
- Zero composite Trust Score calculation (raw multi-dimensional quality reporting)
- Zero changes to existing statistical index mathematics
- Clear separation between Validation Status (ACCEPT/FLAG/REJECT) and Index Eligibility (ELIGIBLE/INELIGIBLE)
- Two distinct price populations: population_price_metrics (all observed) vs index_eligible_price_metrics (production input)
- Data classification distribution (LIVE_MARKET_DATA, TEST_DATA, HISTORICAL_PROTOTYPE_DATA)
- Strict mathematical invariants and empty/single observation handling
"""
from __future__ import annotations
import math
import datetime as dt
from typing import Dict, List, Any, Optional
from collections import Counter
from sqlalchemy.orm import Session

from app.models.observation import Observation


def compute_percentile(sorted_vals: List[float], p: float) -> float:
    """
    Computes percentile p in [0, 1] using standard linear interpolation.
    """
    n = len(sorted_vals)
    if n == 0:
        return 0.0
    if n == 1:
        return sorted_vals[0]
    idx = p * (n - 1)
    low = int(idx)
    high = min(low + 1, n - 1)
    weight = idx - low
    return round(sorted_vals[low] * (1.0 - weight) + sorted_vals[high] * weight, 2)


def calculate_price_distribution(prices: List[float]) -> Dict[str, Any]:
    """
    Calculates deterministic price summary and dispersion statistics.
    """
    sorted_prices = sorted(prices)
    n_prices = len(sorted_prices)
    if n_prices == 0:
        return {
            "price_observations_count": 0,
            "min": None,
            "p25": None,
            "median": None,
            "p75": None,
            "max": None,
            "mean": None,
            "dispersion": {
                "std_dev": 0.0,
                "iqr": 0.0,
                "range": 0.0,
                "coeff_of_variation": 0.0
            }
        }

    p_min = round(sorted_prices[0], 2)
    p25 = compute_percentile(sorted_prices, 0.25)
    p_med = compute_percentile(sorted_prices, 0.50)
    p75 = compute_percentile(sorted_prices, 0.75)
    p_max = round(sorted_prices[-1], 2)
    p_mean = round(sum(sorted_prices) / n_prices, 2)
    p_iqr = round(p75 - p25, 2)
    p_range = round(p_max - p_min, 2)

    if n_prices > 1:
        variance = sum((x - p_mean) ** 2 for x in sorted_prices) / (n_prices - 1)
        p_std = round(math.sqrt(variance), 2)
        p_cv = round(p_std / p_mean, 4) if p_mean > 0 else 0.0
    else:
        p_std = 0.0
        p_cv = 0.0

    return {
        "price_observations_count": n_prices,
        "min": p_min,
        "p25": p25,
        "median": p_med,
        "p75": p75,
        "max": p_max,
        "mean": p_mean,
        "dispersion": {
            "std_dev": p_std,
            "iqr": p_iqr,
            "range": p_range,
            "coeff_of_variation": p_cv
        }
    }


def classify_observation_data(obs: Any) -> str:
    """
    Classifies an observation into LIVE_MARKET_DATA, TEST_DATA, or HISTORICAL_PROTOTYPE_DATA.
    """
    bag_info = getattr(obs, "baggage_information", None) or {}
    live_mode = bag_info.get("live_mode") if isinstance(bag_info, dict) else None
    if getattr(obs, "live_mode", None) is False or live_mode is False or getattr(obs, "is_test_data", None) is True:
        return "TEST_DATA"

    inelig_reasons = getattr(obs, "index_eligibility_reasons", None) or []
    if "INELIGIBLE_TEST_MODE_DATA" in inelig_reasons:
        return "TEST_DATA"

    data_stat = str(getattr(obs, "data_status", "") or "").upper()
    if "HISTORICAL" in data_stat or "PROTOTYPE" in str(getattr(obs, "source_id", "") or "").upper():
        return "HISTORICAL_PROTOTYPE_DATA"
    if "TEST" in data_stat:
        return "TEST_DATA"

    return "LIVE_MARKET_DATA"


class ObservationQualityService:
    @classmethod
    def compute_quality_metrics(
        cls,
        observations: List[Observation],
        route_id: str,
        travel_date: dt.date,
        horizon: int,
        cabin: str = "ECONOMY",
        collection_date: Optional[dt.date] = None
    ) -> Dict[str, Any]:
        """
        Pure deterministic function: takes a list of canonical observations and returns
        a comprehensive, semantically precise quality metrics dictionary.
        """
        total_obs = len(observations)
        cabin_clean = cabin.strip().upper()

        # 1. Population & Validation Status Breakdown
        accepted_count = 0
        flagged_count = 0
        rejected_count = 0
        eligible_count = 0
        ineligible_count = 0

        val_reasons_counter = Counter()
        inelig_reasons_counter = Counter()
        data_status_counter = Counter()
        classification_counter = Counter()

        # Sources & Carriers
        sources_counter = Counter()
        sources_eligible_counter = Counter()
        carrier_counter = Counter()
        cabin_counter = Counter()

        # Metadata completeness checks
        missing_flight_no = 0
        missing_duration = 0
        missing_stops = 0
        missing_url = 0
        missing_carrier = 0

        # Duplicate tracking
        fingerprints = []

        # Arithmetic & Breakdown
        arithmetic_counter = Counter()
        breakdown_counter = Counter()
        has_base_fare_count = 0
        has_taxes_count = 0
        has_fees_count = 0

        # Price populations
        population_prices: List[float] = []
        index_eligible_prices: List[float] = []

        for obs in observations:
            val_status = str(getattr(obs, "validation_status", "ACCEPT") or "ACCEPT").upper()
            val_reasons = getattr(obs, "validation_reasons", None) or []
            inelig_status = str(getattr(obs, "index_eligibility", "INELIGIBLE") or "INELIGIBLE").upper()
            inelig_reasons = getattr(obs, "index_eligibility_reasons", None) or []

            # Exact three-state status alignment:
            # - REJECT: hard validation errors
            # - FLAG: non-blocking validation warnings (e.g. partial breakdown, missing flight no)
            # - ACCEPT: zero warnings/errors
            if val_status == "REJECT" or any(str(r).startswith("REJECT_") for r in val_reasons):
                effective_status = "REJECT"
                rejected_count += 1
            elif val_status == "FLAG" or any(str(r).startswith("FLAG_") for r in val_reasons):
                effective_status = "FLAG"
                flagged_count += 1
            else:
                effective_status = "ACCEPT"
                accepted_count += 1

            if inelig_status == "ELIGIBLE":
                eligible_count += 1
                sources_eligible_counter[obs.source_id] += 1
            else:
                ineligible_count += 1

            data_status_counter[getattr(obs, "data_status", "OBSERVED") or "OBSERVED"] += 1

            # Data classification
            d_class = classify_observation_data(obs)
            classification_counter[d_class] += 1

            # Reasons
            for r in val_reasons:
                val_reasons_counter[r] += 1
            for r in inelig_reasons:
                inelig_reasons_counter[r] += 1

            # Sources & Carriers
            sources_counter[obs.source_id] += 1
            carrier = (getattr(obs, "airline", None) or getattr(obs, "carrier_id", None) or "UNKNOWN").upper()
            carrier_counter[carrier] += 1
            if carrier in ("UNKNOWN", "NONE", "NULL", ""):
                missing_carrier += 1

            obs_cabin = (getattr(obs, "cabin", "ECONOMY") or "ECONOMY").upper()
            cabin_counter[obs_cabin] += 1

            # Metadata completeness
            flt_no = getattr(obs, "flight_number", None)
            if not flt_no or not str(flt_no).strip():
                missing_flight_no += 1
            if getattr(obs, "duration_minutes", None) is None:
                missing_duration += 1
            if getattr(obs, "stops", None) is None:
                missing_stops += 1
            src_url = getattr(obs, "source_url", None)
            if not src_url or not str(src_url).strip():
                missing_url += 1

            # Fingerprint
            fp = getattr(obs, "quote_fingerprint", None) or f"{obs.source_id}|{carrier}|{flt_no}|{getattr(obs, 'total_fare', 0)}"
            fingerprints.append(fp)

            # Arithmetic & Breakdown
            arithmetic_counter[getattr(obs, "arithmetic_status", "ARITHMETIC_UNCHECKABLE") or "ARITHMETIC_UNCHECKABLE"] += 1
            breakdown_counter[getattr(obs, "breakdown_status", "TOTAL_ONLY") or "TOTAL_ONLY"] += 1

            if getattr(obs, "base_fare", None) is not None:
                has_base_fare_count += 1
            if getattr(obs, "taxes", None) is not None:
                has_taxes_count += 1
            if getattr(obs, "fees", None) is not None or getattr(obs, "mandatory_fees", None) is not None:
                has_fees_count += 1

            # Prices
            tf = float(obs.total_fare) if getattr(obs, "total_fare", None) is not None else 0.0
            if effective_status != "REJECT" and tf > 0:
                population_prices.append(tf)
                if inelig_status == "ELIGIBLE":
                    index_eligible_prices.append(tf)

        # Duplicate Calculations
        unique_fps_count = len(set(fingerprints))
        dup_count = max(0, total_obs - unique_fps_count)
        dup_rate = round(dup_count / total_obs, 4) if total_obs > 0 else 0.0

        # Completeness & Rates (Mathematically Consistent)
        acceptance_rate = round(accepted_count / total_obs, 4) if total_obs > 0 else 0.0
        flag_rate = round(flagged_count / total_obs, 4) if total_obs > 0 else 0.0
        rejection_rate = round(rejected_count / total_obs, 4) if total_obs > 0 else 0.0
        index_eligibility_rate = round(eligible_count / total_obs, 4) if total_obs > 0 else 0.0

        # Two-Population Price Distributions
        pop_price_metrics = calculate_price_distribution(population_prices)
        idx_price_metrics = calculate_price_distribution(index_eligible_prices)

        # Backward compatibility alias
        price_metrics = pop_price_metrics

        # Cabin Consistency: True if empty or all match queried cabin
        cabin_consistent = (len(cabin_counter) == 0) or (len(cabin_counter) == 1 and cabin_clean in cabin_counter)

        # Build comprehensive output structure
        report = {
            "metadata": {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "route_id": route_id,
                "travel_date": travel_date.isoformat(),
                "horizon_days": horizon,
                "horizon_code": f"T+{horizon}",
                "cabin": cabin_clean,
                "collection_date": collection_date.isoformat() if collection_date else None,
                "note": "Observation Quality Metrics Layer (Milestone 4C.1). No aggregate Trust Score calculated."
            },
            "population_summary": {
                "total_observations": total_obs,
                "accepted_observations": accepted_count,
                "flagged_observations": flagged_count,
                "rejected_observations": rejected_count,
                "index_eligible_observations": eligible_count,
                "index_ineligible_observations": ineligible_count,
                "data_classification_distribution": dict(classification_counter),
                "data_status_distribution": dict(data_status_counter),
                "validation_reasons_distribution": dict(val_reasons_counter),
                "index_eligibility_reasons_distribution": dict(inelig_reasons_counter)
            },
            "source_metrics": {
                "source_count": len(sources_counter),
                "sources_represented": sorted(list(sources_counter.keys())),
                "source_wise_observation_counts": dict(sources_counter),
                "source_wise_eligible_counts": dict(sources_eligible_counter)
            },
            "carrier_metrics": {
                "carrier_count": len(carrier_counter),
                "carrier_coverage": dict(carrier_counter)
            },
            "cabin_metrics": {
                "cabin_consistency": cabin_consistent,
                "cabin_distribution": dict(cabin_counter)
            },
            "metadata_completeness": {
                "missing_flight_number_count": missing_flight_no,
                "missing_duration_count": missing_duration,
                "missing_stops_count": missing_stops,
                "missing_source_url_count": missing_url,
                "missing_carrier_count": missing_carrier
            },
            "duplicate_metrics": {
                "unique_observations_count": unique_fps_count,
                "duplicate_observations_count": dup_count,
                "duplicate_rate": dup_rate
            },
            "population_price_metrics": pop_price_metrics,
            "index_eligible_price_metrics": idx_price_metrics,
            "price_metrics": price_metrics,  # Alias for population price metrics
            "arithmetic_metrics": {
                "arithmetic_status_distribution": dict(arithmetic_counter)
            },
            "fare_breakdown_metrics": {
                "breakdown_status_distribution": dict(breakdown_counter),
                "has_base_fare_count": has_base_fare_count,
                "has_taxes_count": has_taxes_count,
                "has_fees_count": has_fees_count
            },
            "collection_completeness": {
                "has_data": total_obs > 0,
                "has_eligible_data": eligible_count > 0,
                "acceptance_rate": acceptance_rate,
                "flag_rate": flag_rate,
                "rejection_rate": rejection_rate,
                "index_eligibility_rate": index_eligibility_rate,
                "eligibility_rate": index_eligibility_rate  # Backward compatible alias
            }
        }

        return report

    @classmethod
    def calculate_route_quality_report(
        cls,
        db: Session,
        route_id: str,
        travel_date: dt.date,
        horizon: int,
        cabin: str = "ECONOMY",
        collection_date: Optional[dt.date] = None
    ) -> Dict[str, Any]:
        """
        Queries the database for observations matching the given criteria and returns
        the serialized quality report.
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

        return cls.compute_quality_metrics(
            observations=observations,
            route_id=route_id,
            travel_date=travel_date,
            horizon=horizon,
            cabin=cabin_clean,
            collection_date=collection_date
        )
