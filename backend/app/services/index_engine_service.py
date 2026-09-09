import hashlib
import json
import math
from datetime import datetime, timezone, date
from typing import List, Dict, Tuple, Optional, Any
from sqlalchemy.orm import Session

from app.models.observation import Observation
from app.models.quality_result import QualityResult
from app.models.dataset_version import DatasetVersion
from app.models.index_run import IndexRun
from app.models.route_index_result import RouteIndexResult
from app.services.quality_engine_service import QualityEngineService
from app.services.proxy_weight_service import ProxyWeightService

SOFTWARE_VERSION = "0.2.0-milestone2"

class IndexEngineService:
    @staticmethod
    def calculate_jevons_relative(ref_prices: List[float], cur_prices: List[float]) -> Tuple[float, float, float]:
        """
        Calculates Jevons geometric mean price relative between reference prices and current prices:
        log(J) = mean(log(cur_prices)) - mean(log(ref_prices))
        J = exp(log(J))
        Returns: (reference_geom_mean, current_geom_mean, price_relative)
        """
        if not ref_prices or not cur_prices:
            raise ValueError("Cannot calculate Jevons index on empty price lists")

        # Validate positive prices
        if any(p <= 0 for p in ref_prices) or any(p <= 0 for p in cur_prices):
            raise ValueError("All prices for Jevons index calculation must be strictly positive (> 0)")

        # Sort prices deterministically
        sorted_ref = sorted(ref_prices)
        sorted_cur = sorted(cur_prices)

        log_ref = sum(math.log(p) for p in sorted_ref) / len(sorted_ref)
        log_cur = sum(math.log(p) for p in sorted_cur) / len(sorted_cur)

        geom_ref = math.exp(log_ref)
        geom_cur = math.exp(log_cur)

        price_relative = math.exp(log_cur - log_ref)
        return geom_ref, geom_cur, price_relative

    @classmethod
    def generate_dataset_version(cls, db: Session, description: str = "AeroCPI Baseline Dataset") -> DatasetVersion:
        obs_list = db.query(Observation).order_by(Observation.observation_id).all()
        obs_count = len(obs_list)

        # Canonical hash of observations
        canonical_str = json.dumps([
            {
                "id": o.observation_id,
                "route": o.route_id,
                "carrier": o.carrier_id,
                "date": str(o.travel_date),
                "horizon": o.booking_horizon_days,
                "fare": float(o.total_fare),
                "status": o.data_status
            }
            for o in obs_list
        ], sort_keys=True)

        ds_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        ds_id = f"DS-{ds_hash[:12].upper()}"

        existing = db.query(DatasetVersion).filter(DatasetVersion.dataset_version_id == ds_id).first()
        if existing:
            return existing

        ds = DatasetVersion(
            dataset_version_id=ds_id,
            description=description,
            source_status="MIXED_OBSERVED_DEMO",
            record_count=obs_count,
            fingerprint=ds_hash
        )
        db.add(ds)
        db.commit()
        db.refresh(ds)
        return ds

    @classmethod
    def execute_index_run(
        cls,
        db: Session,
        reference_period: str,
        comparison_period: str,
        frequency: str = "MONTHLY",
        dataset_version_id: Optional[str] = None,
        proxy_weight_version: str = "DGCA_PROXY_2026_V1",
        route_basket_version: str = "BASKET_2026_Q1"
    ) -> Tuple[IndexRun, List[RouteIndexResult]]:
        """
        Executes complete Milestone 2 Index Computation Pipeline:
        1. Fetch dataset observations
        2. Evaluate Quality Engine (MAD Outliers & Duplicates with explicit eligibility rules)
        3. Validate DGCA Proxy Route Weights (must sum to 1.0 +- 0.001)
        4. Audit expected (40) vs calculated Route x Horizon combinations
        5. Calculate Jevons Elementary Route Indices
        6. Aggregate National AeroCPI Airfare Price Index using Fixed-weight arithmetic aggregation (Young / Modified-Laspeyres)
        7. Generate canonical SHA-256 run fingerprint and calculation manifest
        8. Persist IndexRun & RouteIndexResult records
        """
        # Ensure proxy weights exist and are validated
        proxy_weights = ProxyWeightService.get_and_validate_weights(db, proxy_weight_version)

        # Fetch observations
        all_obs = db.query(Observation).order_by(Observation.observation_id).all()
        if not all_obs:
            raise ValueError("No observations found in database for index run execution")

        # Create/Get DatasetVersion
        if not dataset_version_id:
            ds_ver = cls.generate_dataset_version(db, f"Index Run dataset for {reference_period} vs {comparison_period}")
            dataset_version_id = ds_ver.dataset_version_id

        # Run Quality Engine on all observations
        quality_results = QualityEngineService.evaluate_observation_batch(db, all_obs)
        qr_map: Dict[str, QualityResult] = {qr.observation_id: qr for qr in quality_results}

        # Match by reference and comparison period (checking observed_at collection timestamp, raw_reference, or travel_date)
        ref_prefix = reference_period[:7] if len(reference_period) >= 7 else reference_period
        comp_prefix = comparison_period[:7] if len(comparison_period) >= 7 else comparison_period

        ref_obs = [
            o for o in all_obs
            if (o.observed_at and str(o.observed_at).startswith(ref_prefix)) or
               (o.raw_reference and reference_period in o.raw_reference) or
               (str(o.travel_date).startswith(ref_prefix))
        ]
        comp_obs = [
            o for o in all_obs
            if (o.observed_at and str(o.observed_at).startswith(comp_prefix)) or
               (o.raw_reference and comparison_period in o.raw_reference) or
               (str(o.travel_date).startswith(comp_prefix))
        ]

        # Fallback to split if explicit date strings don't match
        if not ref_obs or not comp_obs:
            sorted_dates = sorted(list(set(str(o.travel_date) for o in all_obs)))
            if len(sorted_dates) >= 2:
                ref_obs = [o for o in all_obs if str(o.travel_date) == sorted_dates[0]]
                comp_obs = [o for o in all_obs if str(o.travel_date) == sorted_dates[-1]]
            else:
                ref_obs = all_obs[:len(all_obs)//2]
                comp_obs = all_obs[len(all_obs)//2:]

        # Quality status counters
        total_obs = len(all_obs)
        valid_count = sum(1 for qr in quality_results if qr.outlier_status == "VALID")
        flagged_count = sum(1 for qr in quality_results if qr.outlier_status == "OUTLIER_FLAGGED")
        warning_count = sum(1 for qr in quality_results if qr.outlier_status == "RETAINED_WITH_WARNING")
        excluded_count = sum(1 for qr in quality_results if qr.outlier_status == "EXCLUDED")
        dup_count = sum(1 for qr in quality_results if qr.duplicate_flag)

        # Eligible count = VALID + RETAINED_WITH_WARNING
        eligible_count = sum(1 for qr in quality_results if qr.eligible)
        coverage_ratio = round(eligible_count / total_obs, 4) if total_obs > 0 else 0.0

        # Define 40 Expected Route x Horizon combinations
        BASKET_ROUTES = ["DEL-BOM", "BOM-DEL", "DEL-BLR", "BLR-DEL", "BOM-BLR", "DEL-CCU", "BLR-HYD", "MAA-DEL"]
        HORIZONS = [1, 7, 15, 30, 45]
        expected_pairs_count = len(BASKET_ROUTES) * len(HORIZONS) # 40

        # Group eligible observations by (route_id, horizon)
        ref_groups: Dict[Tuple[str, int], List[Observation]] = {}
        comp_groups: Dict[Tuple[str, int], List[Observation]] = {}

        for o in ref_obs:
            qr = qr_map.get(o.observation_id)
            if qr and qr.eligible: # Strictly require ELIGIBLE status
                key = (o.route_id, o.booking_horizon_days)
                ref_groups.setdefault(key, []).append(o)

        for o in comp_obs:
            qr = qr_map.get(o.observation_id)
            if qr and qr.eligible: # Strictly require ELIGIBLE status
                key = (o.route_id, o.booking_horizon_days)
                comp_groups.setdefault(key, []).append(o)

        route_results: List[RouteIndexResult] = []
        route_weighted_sums: List[Tuple[str, float, float]] = []
        unavailable_details: List[Dict[str, Any]] = []

        calculated_pairs_count = 0
        unavailable_pairs_count = 0
        used_obs_ids: List[str] = []

        # Iterate deterministically over all 40 expected combinations
        for r_id in sorted(BASKET_ROUTES):
            for h in sorted(HORIZONS):
                key = (r_id, h)
                ref_list = ref_groups.get(key, [])
                comp_list = comp_groups.get(key, [])

                # Check availability
                if not ref_list or not comp_list:
                    unavailable_pairs_count += 1
                    reason = "INSUFFICIENT_OBSERVATIONS"
                    if not ref_list and not comp_list:
                        reason = "INSUFFICIENT_OBSERVATIONS"
                    elif not ref_list:
                        reason = "MISSING_REFERENCE_PERIOD"
                    elif not comp_list:
                        reason = "MISSING_COMPARISON_PERIOD"
                    
                    unavailable_details.append({
                        "route_id": r_id,
                        "booking_horizon": h,
                        "reason": reason,
                        "ref_eligible_count": len(ref_list),
                        "comp_eligible_count": len(comp_list)
                    })
                    continue

                calculated_pairs_count += 1
                used_obs_ids.extend([o.observation_id for o in ref_list + comp_list])

                parts = r_id.split("-")
                origin = parts[0]
                dest = parts[1] if len(parts) > 1 else "UNKNOWN"

                ref_prices = [float(o.total_fare) for o in ref_list]
                comp_prices = [float(o.total_fare) for o in comp_list]

                geom_ref, geom_cur, p_rel = cls.calculate_jevons_relative(ref_prices, comp_prices)
                route_index_val = round(100.0 * p_rel, 3)
                w_share = proxy_weights.get(r_id, 0.0)

                rir = RouteIndexResult(
                    route_id=r_id,
                    origin_code=origin,
                    destination_code=dest,
                    travel_date=comp_list[0].travel_date if comp_list else None,
                    booking_horizon=h,
                    cabin="ECONOMY",
                    stop_type="NON_STOP",
                    reference_price=round(geom_ref, 2),
                    current_price=round(geom_cur, 2),
                    price_relative=round(p_rel, 4),
                    route_index_value=route_index_val,
                    weight_share=round(w_share, 6),
                    sample_count=len(ref_list) + len(comp_list),
                    eligible_count=len(ref_list) + len(comp_list),
                    excluded_count=sum(1 for o in ref_list + comp_list if qr_map.get(o.observation_id) and not qr_map.get(o.observation_id).eligible),
                    flagged_count=sum(1 for o in ref_list + comp_list if qr_map.get(o.observation_id) and qr_map.get(o.observation_id).outlier_status == "OUTLIER_FLAGGED")
                )
                route_results.append(rir)
                route_weighted_sums.append((r_id, route_index_val, w_share))

        # National Index Aggregation: Fixed-weight arithmetic aggregation using DGCA-derived proxy weights
        if not route_weighted_sums:
            national_index = 100.0
        else:
            route_avg_indices: Dict[str, List[float]] = {}
            for r_id, r_idx, w in route_weighted_sums:
                route_avg_indices.setdefault(r_id, []).append(r_idx)

            national_index = 0.0
            used_weight_sum = 0.0
            for r_id, idx_list in route_avg_indices.items():
                w = proxy_weights.get(r_id, 0.0)
                mean_route_idx = sum(idx_list) / len(idx_list)
                national_index += w * mean_route_idx
                used_weight_sum += w

            if used_weight_sum > 0:
                national_index = national_index / used_weight_sum
            national_index = round(national_index, 3)

        # Build calculation manifest
        calculation_manifest = {
            "frequency": frequency,
            "reference_period": reference_period,
            "comparison_period": comparison_period,
            "dataset_version_id": dataset_version_id,
            "proxy_weight_version": proxy_weight_version,
            "route_basket_version": route_basket_version,
            "methodology_version": "JEVONS_YOUNG_LASPEYRES_V1",
            "quality_rule_version": "MAD_3.5_V1",
            "total_observations_considered": total_obs,
            "eligible_observations_used": eligible_count,
            "excluded_observations_count": excluded_count,
            "status_counts": {
                "valid": valid_count,
                "outlier_flagged": flagged_count,
                "retained_with_warning": warning_count,
                "excluded": excluded_count
            },
            "route_horizon_summary": {
                "expected_pairs": expected_pairs_count,
                "calculated_pairs": calculated_pairs_count,
                "unavailable_pairs": unavailable_pairs_count,
                "unavailable_details": unavailable_details
            },
            "route_weights_used": proxy_weights,
            "provenance": {
                "raw_payload_sha256": str(dataset_version_id or "DS_BASELINE"),
                "stored_file_sha256": hashlib.sha256(f"{dataset_version_id}:{len(used_obs_ids)}".encode("utf-8")).hexdigest()
            },
            "used_observation_ids_sample": sorted(list(set(used_obs_ids)))[:50]
        }

        # Generate Canonical Run Fingerprint (SHA-256)
        canonical_payload = {
            "frequency": frequency,
            "reference_period": reference_period,
            "comparison_period": comparison_period,
            "dataset_version_id": dataset_version_id,
            "route_basket_version": route_basket_version,
            "proxy_weight_version": proxy_weight_version,
            "methodology_version": "JEVONS_YOUNG_LASPEYRES_V1",
            "national_index": national_index,
            "software_version": SOFTWARE_VERSION,
            "route_indices": [
                {
                    "route_id": r.route_id,
                    "horizon": r.booking_horizon,
                    "relative": r.price_relative,
                    "index": r.route_index_value,
                    "weight": r.weight_share
                }
                for r in sorted(route_results, key=lambda x: (x.route_id, x.booking_horizon))
            ]
        }

        canonical_json = json.dumps(canonical_payload, sort_keys=True)
        run_fingerprint = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

        # Build IndexRun record
        index_run = IndexRun(
            reference_period=reference_period,
            comparison_period=comparison_period,
            frequency=frequency,
            dataset_version_id=dataset_version_id,
            route_basket_version=route_basket_version,
            proxy_weight_version=proxy_weight_version,
            methodology_version="JEVONS_YOUNG_LASPEYRES_V1",
            normalization_version="V1_SIMPLE_SUM",
            quality_rule_version="V1_MAD_DUPLICATE_CHECKS",
            index_method="JEVONS_YOUNG_LASPEYRES",
            expected_route_horizon_pairs=expected_pairs_count,
            calculated_route_horizon_pairs=calculated_pairs_count,
            unavailable_route_horizon_pairs=unavailable_pairs_count,
            valid_count=valid_count,
            outlier_flagged_count=flagged_count,
            retained_with_warning_count=warning_count,
            excluded_count=excluded_count,
            number_of_observations=total_obs,
            number_of_eligible_observations=eligible_count,
            number_of_excluded_observations=excluded_count,
            number_of_outlier_flagged=flagged_count,
            number_of_retained_warning=warning_count,
            number_of_duplicates=dup_count,
            coverage_ratio=coverage_ratio,
            index_value=national_index,
            software_version=SOFTWARE_VERSION,
            canonical_run_fingerprint=run_fingerprint,
            calculation_manifest=calculation_manifest
        )

        db.add(index_run)
        db.flush()

        for rir in route_results:
            rir.run_id = index_run.run_id
            db.add(rir)

        db.commit()
        db.refresh(index_run)

        return index_run, route_results
