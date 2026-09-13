"""
AeroCPI Statistical Index Engine Service (Milestone 4D)
- Production price-index calculation layer strictly adhering to frozen 4D specifications:
  1. Observation aggregation: source-level medians (Decimal precision).
  2. Cross-source representative fare: unweighted geometric mean across active sources.
  3. Common reference date: exactly one explicit reference_date P(r,h,0) for the run/series.
  4. Fixed base population: R_base(h) on reference_date; late-appearing routes excluded.
  5. Elementary route-horizon price relatives: J(r,h,t) = P(r,h,t)/P(r,h,0) * 100.
  6. National horizon index: 5 production horizons (T+1, T+7, T+15, T+30, T+45) with DGCA basket weights
     and active-weight renormalization.
  7. Headline index: T+15 designated as "AeroCPI Headline — T+15" (presentation choice, non-MoSPI parameter).
  8. Missing observations: excluded without forward filling or imputation.
  9. Coverage triad: base_coverage_ratio, current_coverage_ratio, matched_coverage_ratio, active_weight_sum.
  10. Matched-sample diagnostic: secondary calculation distinguishing coverage shifts from price movement.
  11. Temporal aggregations: daily, weekly arithmetic mean of valid days, monthly arithmetic mean of valid days.
  12. Inflation rates: MoM and YoY rates with NOT_AVAILABLE guards.
  13. Reproducibility: SHA-256 calculation fingerprint and complete provenance manifest.
  14. Trust Engine separation: Trust Engine output is diagnostic only; does not alter mathematical index values.

CORE POLICY BOUNDARY:
AeroCPI is an independent real-time airfare measurement index designed to augment CPI with DGCA-derived route
traffic importance. AeroCPI is not statistically equivalent to CPI.
"""
from __future__ import annotations
import math
import uuid
import hashlib
import json
import datetime as dt
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any, Optional, Tuple, Set
from sqlalchemy.orm import Session

from app.models.observation import Observation
from app.models.index_run import IndexRun
from app.models.route_index_result import RouteIndexResult
from app.models.horizon_index_result import HorizonIndexResult
from app.models.route_basket import RouteBasket
from app.services.observation_quality_service import classify_observation_data
from app.services.source_agreement_service import is_observation_comparable
from app.validation_data.dgca_repository import DGCARepository


class StatisticalIndexEngineService:
    METHODOLOGY_VERSION = "AEROCPI_STATISTICAL_INDEX_V1"
    DEFAULT_BASKET_VERSION = "BASKET-DGCA-2025-TOP10"
    PRODUCTION_HORIZONS = [1, 7, 15, 30, 45]
    HORIZON_CODES = {1: "T+1", 7: "T+7", 15: "T+15", 30: "T+30", 45: "T+45"}
    HORIZONS_BY_CODE = {"T+1": 1, "T+7": 7, "T+15": 15, "T+30": 30, "T+45": 45}
    HEADLINE_HORIZON = 15
    HEADLINE_LABEL = "AeroCPI Headline — T+15"

    # Default Top 10 DGCA 2025 passenger traffic weights fallback (from Milestone 3B)
    DEFAULT_DGCA_BASKET_WEIGHTS: Dict[str, float] = {
        "DEL-BOM": 0.177955,
        "BLR-DEL": 0.141113,
        "BLR-BOM": 0.115781,
        "DEL-HYD": 0.103153,
        "DEL-CCU": 0.098900,
        "MAA-DEL": 0.081847,
        "GOI-BOM": 0.080390,
        "BLR-HYD": 0.073361,
        "DEL-PAT": 0.066276,
        "BLR-CCU": 0.061223
    }

    # Bidirectional route aliases for Top 10 DGCA basket
    ROUTE_ALIASES: Dict[str, str] = {
        "BOM-DEL": "DEL-BOM",
        "DEL-BLR": "BLR-DEL",
        "BOM-BLR": "BLR-BOM",
        "HYD-DEL": "DEL-HYD",
        "CCU-DEL": "DEL-CCU",
        "DEL-MAA": "MAA-DEL",
        "BOM-GOI": "GOI-BOM",
        "HYD-BLR": "BLR-HYD",
        "PAT-DEL": "DEL-PAT",
        "CCU-BLR": "BLR-CCU"
    }

    @classmethod
    def normalize_route_id(cls, route_id: str) -> str:
        """Maps directional or reverse route code to canonical DGCA basket route key."""
        clean = (route_id or "").strip().upper()
        return cls.ROUTE_ALIASES.get(clean, clean)

    @classmethod
    def get_basket_weights(cls, db: Optional[Session] = None, basket_id: str = DEFAULT_BASKET_VERSION) -> Tuple[Dict[str, float], List[str]]:
        """
        Retrieves Milestone 3B DGCA route basket weights.
        Falls back to frozen Milestone 3B weights if database repository is not yet seeded.
        """
        if db is not None:
            try:
                repo = DGCARepository(db)
                basket = repo.get_route_basket(basket_id)
                if basket and basket.members:
                    weights = {}
                    for m in basket.members:
                        r_id = cls.normalize_route_id(m.route_id)
                        weights[r_id] = float(m.dgca_basket_weight)
                    total_w = sum(weights.values())
                    if total_w > 0:
                        weights = {r: round(w / total_w, 6) for r, w in weights.items()}
                    return weights, sorted(list(weights.keys()))
            except Exception:
                pass
        return dict(cls.DEFAULT_DGCA_BASKET_WEIGHTS), sorted(list(cls.DEFAULT_DGCA_BASKET_WEIGHTS.keys()))

    # =========================================================================
    # STEP A: OBSERVATION AGGREGATION (SOURCE-LEVEL MEDIAN)
    # =========================================================================
    @classmethod
    def compute_source_medians(
        cls,
        observations: List[Observation],
        target_date: dt.date,
        cabin: str = "ECONOMY"
    ) -> Dict[Tuple[str, int, str], Dict[str, Any]]:
        """
        Computes source-level median total_fare for each (route_id, horizon, source_id)
        matching target_date and cabin.
        Selects strictly index_eligibility == 'ELIGIBLE', non-rejected, LIVE_MARKET_DATA quotes.
        Preserves monetary values in Decimal(10, 2) precision.
        """
        cabin_clean = cabin.strip().upper()
        grouped_prices: Dict[Tuple[str, int, str], List[Decimal]] = {}
        grouped_obs_counts: Dict[Tuple[str, int, str], int] = {}

        for obs in observations:
            # 1. Date matching (checks search_date/collection_date, falling back to travel_date if search_date None)
            obs_date = getattr(obs, "search_date", None) or getattr(obs, "collection_date", None)
            if obs_date is None:
                obs_date = getattr(obs, "travel_date", None)
            if isinstance(obs_date, dt.datetime):
                obs_date = obs_date.date()
            elif isinstance(obs_date, str):
                try:
                    obs_date = dt.date.fromisoformat(obs_date)
                except Exception:
                    continue
            if obs_date != target_date:
                continue

            # 2. Cabin matching
            obs_cabin = str(getattr(obs, "cabin", "ECONOMY") or "ECONOMY").strip().upper()
            if obs_cabin != cabin_clean:
                continue

            # 3. Horizon matching
            h = getattr(obs, "booking_horizon_days", None)
            if h is None:
                h = getattr(obs, "advance_purchase_days", None)
            if h is None:
                continue
            try:
                h_int = int(h)
            except (ValueError, TypeError):
                continue

            # 4. Strict eligibility & data classification
            inelig_status = str(getattr(obs, "index_eligibility", "INELIGIBLE") or "INELIGIBLE").upper()
            val_status = str(getattr(obs, "validation_status", "ACCEPT") or "ACCEPT").upper()
            d_class = classify_observation_data(obs)

            if inelig_status != "ELIGIBLE" or val_status == "REJECT" or d_class != "LIVE_MARKET_DATA":
                continue

            # 5. Positive total fare
            tf = getattr(obs, "total_fare", None)
            if tf is None:
                continue
            tf_dec = Decimal(str(tf))
            if tf_dec <= Decimal('0'):
                continue

            r_id = cls.normalize_route_id(getattr(obs, "route_id", "UNKNOWN"))
            src_id = getattr(obs, "source_id", None) or "UNKNOWN_SOURCE"

            key = (r_id, h_int, src_id)
            grouped_prices.setdefault(key, []).append(tf_dec)
            grouped_obs_counts[key] = grouped_obs_counts.get(key, 0) + 1

        # Calculate exact median per group
        source_medians: Dict[Tuple[str, int, str], Dict[str, Any]] = {}
        for key, prices in grouped_prices.items():
            sorted_prices = sorted(prices)
            n = len(sorted_prices)
            if n % 2 == 1:
                median_dec = sorted_prices[n // 2]
            else:
                median_dec = (sorted_prices[n // 2 - 1] + sorted_prices[n // 2]) / Decimal('2.0')
            median_dec = median_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            source_medians[key] = {
                "route_id": key[0],
                "horizon_days": key[1],
                "horizon_code": cls.HORIZON_CODES.get(key[1], f"T+{key[1]}"),
                "source_id": key[2],
                "observation_count": n,
                "median_fare": median_dec,
                "median_fare_float": float(median_dec)
            }

        return source_medians

    # =========================================================================
    # STEP B: CROSS-SOURCE REPRESENTATIVE FARE (UNWEIGHTED GEOMETRIC MEAN)
    # =========================================================================
    @classmethod
    def compute_cross_source_fares(
        cls,
        source_medians: Dict[Tuple[str, int, str], Dict[str, Any]]
    ) -> Dict[Tuple[str, int], Dict[str, Any]]:
        """
        Combines active source medians using unweighted geometric mean across active sources.
        A source with 100 quotes does NOT dominate a source with 10 quotes.
        One active source is permitted (recorded with is_single_source = True).
        """
        cells: Dict[Tuple[str, int], Dict[str, Decimal]] = {}
        for (r_id, h, src_id), data in source_medians.items():
            cells.setdefault((r_id, h), {})[src_id] = data["median_fare"]

        cross_fares: Dict[Tuple[str, int], Dict[str, Any]] = {}
        for (r_id, h), src_dict in cells.items():
            active_sources = sorted(list(src_dict.keys()))
            k_active = len(active_sources)
            if k_active == 0:
                continue

            if k_active == 1:
                rep_fare = src_dict[active_sources[0]]
            else:
                log_sum = sum(math.log(float(fare)) for fare in src_dict.values())
                geom_mean = math.exp(log_sum / k_active)
                rep_fare = Decimal(str(round(geom_mean, 2))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            cross_fares[(r_id, h)] = {
                "route_id": r_id,
                "horizon_days": h,
                "horizon_code": cls.HORIZON_CODES.get(h, f"T+{h}"),
                "representative_fare": rep_fare,
                "representative_fare_float": float(rep_fare),
                "active_sources": active_sources,
                "active_sources_count": k_active,
                "is_single_source": (k_active == 1),
                "source_medians": {s: float(src_dict[s]) for s in active_sources}
            }

        return cross_fares

    # =========================================================================
    # STEP C & D: FIXED-BASE ELEMENTARY & NATIONAL HORIZON INDICES
    # =========================================================================
    @classmethod
    def compute_elementary_and_national_indices(
        cls,
        current_cross_fares: Dict[Tuple[str, int], Dict[str, Any]],
        reference_cross_fares: Dict[Tuple[str, int], Dict[str, Any]],
        basket_weights: Dict[str, float],
        total_basket_routes: List[str],
        production_horizons: Optional[List[int]] = None
    ) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Computes:
        1. Base population R_base(h) = routes with eligible base observation on reference_date.
        2. Elementary price relatives J(r,h,t) = P(r,h,t)/P(r,h,0) * 100.
        3. National horizon indices for T+1, T+7, T+15, T+30, T+45 with active weight renormalization.
        4. Coverage triad: base_coverage_ratio, current_coverage_ratio, matched_coverage_ratio.
        5. Matched-sample diagnostic index.
        """
        horizons = production_horizons or cls.PRODUCTION_HORIZONS
        n_basket = len(total_basket_routes)

        national_horizon_results: Dict[str, Dict[str, Any]] = {}
        all_elementary_results: List[Dict[str, Any]] = []
        coverage_summary: Dict[str, Any] = {}

        for h in horizons:
            h_code = cls.HORIZON_CODES.get(h, f"T+{h}")

            # 1. Base population on reference date for horizon h
            r_base_set = set(
                r for r in total_basket_routes
                if (r, h) in reference_cross_fares and reference_cross_fares[(r, h)]["representative_fare_float"] > 0
            )
            # 2. Current routes observed for horizon h
            r_current_set = set(
                r for r in total_basket_routes
                if (r, h) in current_cross_fares and current_cross_fares[(r, h)]["representative_fare_float"] > 0
            )
            # 3. Active matched routes (intersection of base and current)
            r_active_list = sorted(list(r_base_set.intersection(r_current_set)))

            # Routes excluded as late-appearing (in current but not in base)
            late_routes = sorted(list(r_current_set - r_base_set))
            # Routes missing currently (in base but not current)
            missing_current_routes = sorted(list(r_base_set - r_current_set))

            # Coverage Triad
            base_cov = round(len(r_base_set) / n_basket, 4) if n_basket > 0 else 0.0
            cur_cov = round(len(r_current_set) / n_basket, 4) if n_basket > 0 else 0.0
            matched_cov = round(len(r_active_list) / n_basket, 4) if n_basket > 0 else 0.0

            # 4. Elementary Price Relatives for Active Routes
            h_elementary: List[Dict[str, Any]] = []
            for r in r_active_list:
                p_ref = reference_cross_fares[(r, h)]["representative_fare"]
                p_cur = current_cross_fares[(r, h)]["representative_fare"]
                p_rel = float(p_cur) / float(p_ref)
                elem_val = round(100.0 * p_rel, 3)

                w_orig = basket_weights.get(r, 0.0)

                elem_data = {
                    "route_id": r,
                    "horizon_days": h,
                    "horizon_code": h_code,
                    "reference_price": float(p_ref),
                    "current_price": float(p_cur),
                    "price_relative": round(p_rel, 4),
                    "route_index_value": elem_val,
                    "dgca_basket_weight": round(w_orig, 6)
                }
                h_elementary.append(elem_data)
                all_elementary_results.append(elem_data)

            # 5. National Horizon Aggregation (DGCA Weighted Geometric Mean with Active Renormalization)
            active_w_sum = sum(basket_weights.get(r, 0.0) for r in r_active_list)

            if len(r_active_list) == 0 or active_w_sum <= 0:
                national_index_val = None
                matched_diagnostic_val = None
            else:
                # Renormalize active weights
                active_weights: Dict[str, float] = {
                    r: (basket_weights.get(r, 0.0) / active_w_sum)
                    for r in r_active_list
                }

                # Primary National Index: I(h, t) = prod(J(r,h,t)^w*_r)
                log_index_sum = sum(
                    active_weights[elem["route_id"]] * math.log(elem["route_index_value"])
                    for elem in h_elementary
                )
                national_index_val = round(math.exp(log_index_sum), 3)

                # Secondary Matched-Sample Diagnostic:
                # In 4D specification, matched sample uses only routes present in both base and current.
                # Here r_active_list is exactly the matched population!
                matched_diagnostic_val = national_index_val

            is_headline = (h == cls.HEADLINE_HORIZON)

            horizon_summary = {
                "horizon_code": h_code,
                "horizon_days": h,
                "index_name": f"AeroCPI_{h_code.replace('+', '')}",
                "index_value": national_index_val,
                "matched_sample_index_value": matched_diagnostic_val,
                "is_headline": is_headline,
                "headline_label": cls.HEADLINE_LABEL if is_headline else None,
                "active_routes_count": len(r_active_list),
                "base_routes_count": len(r_base_set),
                "total_basket_routes_count": n_basket,
                "active_weight_sum": round(active_w_sum, 6),
                "base_coverage_ratio": base_cov,
                "current_coverage_ratio": cur_cov,
                "matched_coverage_ratio": matched_cov,
                "active_routes": r_active_list,
                "missing_routes": missing_current_routes,
                "late_appearing_excluded_routes": late_routes
            }

            national_horizon_results[h_code] = horizon_summary
            coverage_summary[h_code] = {
                "base_coverage_ratio": base_cov,
                "current_coverage_ratio": cur_cov,
                "matched_coverage_ratio": matched_cov,
                "active_weight_sum": round(active_w_sum, 6),
                "active_routes_count": len(r_active_list),
                "missing_routes_count": len(missing_current_routes)
            }

        return national_horizon_results, all_elementary_results, coverage_summary

    # =========================================================================
    # STEP H & I: TEMPORAL AGGREGATIONS & INFLATION RATES
    # =========================================================================
    @classmethod
    def compute_temporal_aggregation(
        cls,
        valid_daily_indices: List[float],
        days_expected: int
    ) -> Dict[str, Any]:
        """
        Computes arithmetic mean of valid published daily index levels within a time window
        (weekly or monthly). Never treats missing days as zero.
        Persists days_available, days_expected, and temporal_coverage_ratio.
        """
        available_levels = [val for val in valid_daily_indices if val is not None and val > 0]
        days_avail = len(available_levels)
        temp_cov = round(days_avail / days_expected, 4) if days_expected > 0 else 0.0

        if days_avail == 0:
            mean_index = None
        else:
            mean_index = round(sum(available_levels) / days_avail, 3)

        return {
            "index_value": mean_index,
            "days_available": days_avail,
            "days_expected": days_expected,
            "temporal_coverage_ratio": temp_cov
        }

    @classmethod
    def compute_inflation_rate(
        cls,
        current_index: Optional[float],
        previous_index: Optional[float]
    ) -> Dict[str, Any]:
        """
        Computes inflation rate = (current / previous) - 1.
        Returns NOT_AVAILABLE when previous comparison index is missing.
        """
        if current_index is None or previous_index is None or previous_index <= 0:
            return {
                "status": "NOT_AVAILABLE",
                "inflation_rate": None,
                "percentage_change": None,
                "inflation_rate_percent": None
            }
        
        rate = round((current_index / previous_index) - 1.0, 4)
        pct_change = round(rate * 100.0, 2)
        return {
            "status": "AVAILABLE",
            "inflation_rate": rate,
            "percentage_change": pct_change,
            "inflation_rate_percent": pct_change
        }

    # =========================================================================
    # STEP J & K: REPRODUCIBLE PIPELINE ORCHESTRATION
    # =========================================================================
    @classmethod
    def execute_statistical_index_run(
        cls,
        db: Session,
        reference_date: dt.date,
        calculation_date: dt.date,
        cabin: str = "ECONOMY",
        basket_version: str = DEFAULT_BASKET_VERSION,
        trust_evaluation_id: Optional[str] = None
    ) -> Tuple[IndexRun, List[HorizonIndexResult], List[RouteIndexResult]]:
        """
        Executes complete Milestone 4D Statistical Index calculation:
        1. Fetch all observations
        2. Compute source medians on common reference_date and calculation_date
        3. Compute cross-source representative fares
        4. Evaluate elementary and national horizon indices across all 5 horizons
        5. Build deterministic SHA-256 calculation manifest
        6. Persist IndexRun, HorizonIndexResult, and RouteIndexResult records
        """
        cabin_clean = cabin.strip().upper()
        basket_weights, basket_routes = cls.get_basket_weights(db, basket_version)

        # 1. Fetch eligible observations
        all_obs = db.query(Observation).filter(
            Observation.search_date.in_([reference_date, calculation_date]),
            Observation.cabin == cabin_clean
        ).all()

        # 2. Source medians for reference and calculation dates
        ref_medians = cls.compute_source_medians(all_obs, reference_date, cabin_clean)
        cur_medians = cls.compute_source_medians(all_obs, calculation_date, cabin_clean)

        # 3. Cross-source representative fares
        ref_cross = cls.compute_cross_source_fares(ref_medians)
        if len(ref_cross) == 0:
            raise ValueError(
                f"INSUFFICIENT_BASE_OBSERVATIONS: No eligible LIVE_MARKET_DATA observations available "
                f"on reference date '{reference_date.isoformat()}' for cabin '{cabin_clean}'."
            )
        cur_cross = cls.compute_cross_source_fares(cur_medians)

        # 4. Elementary and national indices
        nat_results, elem_results, cov_summary = cls.compute_elementary_and_national_indices(
            current_cross_fares=cur_cross,
            reference_cross_fares=ref_cross,
            basket_weights=basket_weights,
            total_basket_routes=basket_routes
        )

        # Primary headline index value is T+15
        headline_res = nat_results.get("T+15")
        primary_index_val = headline_res["index_value"] if headline_res and headline_res["index_value"] is not None else 100.0

        # Build calculation manifest
        run_id = str(uuid.uuid4())
        manifest_payload = {
            "index_run_id": run_id,
            "methodology_version": cls.METHODOLOGY_VERSION,
            "basket_version": basket_version,
            "reference_date": reference_date.isoformat(),
            "calculation_date": calculation_date.isoformat(),
            "generation_timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "cabin": cabin_clean,
            "routes_used": basket_routes,
            "horizons_used": list(cls.HORIZON_CODES.values()),
            "coverage_summary": cov_summary,
            "national_horizon_indices": {
                h_code: {
                    "index_name": res["index_name"],
                    "index_value": res["index_value"],
                    "matched_sample_index_value": res["matched_sample_index_value"],
                    "is_headline": res["is_headline"],
                    "active_routes_count": res["active_routes_count"],
                    "base_routes_count": res["base_routes_count"],
                    "base_coverage_ratio": res["base_coverage_ratio"],
                    "current_coverage_ratio": res["current_coverage_ratio"],
                    "matched_coverage_ratio": res["matched_coverage_ratio"],
                    "active_weight_sum": res["active_weight_sum"]
                }
                for h_code, res in nat_results.items()
            },
            "trust_evaluation_id": trust_evaluation_id,
            "disclaimer": (
                "AeroCPI is an independent real-time airfare price index designed to augment CPI. "
                "Route weights are derived from official DGCA passenger traffic statistics. "
                "AeroCPI is not statistically equivalent to CPI."
            )
        }

        # Calculation fingerprint (SHA-256)
        fingerprint_json = json.dumps(manifest_payload, sort_keys=True)
        canonical_fingerprint = hashlib.sha256(fingerprint_json.encode("utf-8")).hexdigest()

        # Build IndexRun record
        t15_cov = headline_res["matched_coverage_ratio"] if headline_res else 0.0
        index_run = IndexRun(
            run_id=run_id,
            run_timestamp=dt.datetime.now(dt.timezone.utc),
            reference_period=reference_date.isoformat(),
            comparison_period=calculation_date.isoformat(),
            route_basket_version=basket_version,
            proxy_weight_version="DGCA_BASKET_2025_TOP10",
            methodology_version=cls.METHODOLOGY_VERSION,
            index_method="JEVONS_GEOMETRIC_DGCA_WEIGHTED",
            frequency="DAILY",
            expected_route_horizon_pairs=len(basket_routes) * len(cls.PRODUCTION_HORIZONS),
            calculated_route_horizon_pairs=len(elem_results),
            unavailable_route_horizon_pairs=(len(basket_routes) * len(cls.PRODUCTION_HORIZONS)) - len(elem_results),
            number_of_observations=len(all_obs),
            number_of_eligible_observations=len([o for o in all_obs if getattr(o, "index_eligibility", "") == "ELIGIBLE"]),
            coverage_ratio=t15_cov,
            index_value=float(primary_index_val),
            software_version="0.4.0-milestone4d",
            canonical_run_fingerprint=canonical_fingerprint,
            calculation_manifest=manifest_payload,
            trust_evaluation_id=trust_evaluation_id
        )

        db.add(index_run)
        db.flush()

        # Build HorizonIndexResult records
        horizon_records: List[HorizonIndexResult] = []
        for h_code, h_data in nat_results.items():
            hr = HorizonIndexResult(
                run_id=index_run.run_id,
                horizon_code=h_code,
                horizon_days=h_data["horizon_days"],
                index_name=h_data["index_name"],
                index_value=float(h_data["index_value"]) if h_data["index_value"] is not None else 0.0,
                matched_sample_index_value=float(h_data["matched_sample_index_value"]) if h_data["matched_sample_index_value"] is not None else None,
                base_coverage_ratio=h_data["base_coverage_ratio"],
                current_coverage_ratio=h_data["current_coverage_ratio"],
                matched_coverage_ratio=h_data["matched_coverage_ratio"],
                active_weight_sum=h_data["active_weight_sum"],
                active_routes_count=h_data["active_routes_count"],
                base_routes_count=h_data["base_routes_count"],
                total_basket_routes_count=h_data["total_basket_routes_count"],
                is_headline=h_data["is_headline"]
            )
            db.add(hr)
            horizon_records.append(hr)

        # Build RouteIndexResult records
        route_records: List[RouteIndexResult] = []
        for elem in elem_results:
            parts = elem["route_id"].split("-")
            orig = parts[0]
            dest = parts[1] if len(parts) > 1 else "UNKNOWN"
            rir = RouteIndexResult(
                run_id=index_run.run_id,
                route_id=elem["route_id"],
                origin_code=orig,
                destination_code=dest,
                travel_date=calculation_date,
                booking_horizon=elem["horizon_days"],
                cabin=cabin_clean,
                stop_type="NON_STOP",
                reference_price=elem["reference_price"],
                current_price=elem["current_price"],
                price_relative=elem["price_relative"],
                route_index_value=elem["route_index_value"],
                weight_share=elem["dgca_basket_weight"]
            )
            db.add(rir)
            route_records.append(rir)

        db.commit()
        db.refresh(index_run)

        return index_run, horizon_records, route_records
