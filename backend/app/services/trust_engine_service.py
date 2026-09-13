"""
AeroCPI Trust Engine Service (Milestone 4C.3 - Final Methodology Audit)
- Produces a transparent, deterministic Measurement Trust Score (0 to 100) under version 'v1'
- Summarizes 7 evidence-based dimensions: Coverage, Source Agreement, Sample Sufficiency,
  Observation Validity, Outlier Health, Source Availability, and Basket/Horizon Stability
- Applies deterministic override rules and exact 84.99 numerical caps
- Diagnostic/measurement-assurance indicator; zero modifications to statistical CPI index formulas
- Test-mode data is strictly isolated and barred from production trust scoring

METHODOLOGY AUDIT PRINCIPLES:
1. Measurement-Assurance vs Statistical Confidence:
   The Measurement Trust Score is a deterministic diagnostic indicator of data quality and collection health.
   It is NOT a statistical probability of correctness or formal Bayesian confidence interval, and does not alter
   index formulas or weights.
2. Versioned Engineering Policy Parameters:
   Thresholds (min sample N=5, 10% discrepancy, 4x imbalance) and scoring weights are explicit engineering policy
   choices calibrated for diagnostic utility, not official MoSPI statistical parameters.
3. Orthogonal & Intentionally Overlapping Diagnostic Penalties:
   Dimensions intentionally permit overlapping penalties for shared systemic failures. For example, if an expected source
   drops out entirely, it simultaneously reduces Coverage, Source Availability, and Source Agreement (since multi-source
   comparison becomes unavailable). Each dimension evaluates a distinct diagnostic facet of the evidence base.
"""
from __future__ import annotations
import math
import hashlib
import json
import datetime as dt
from decimal import Decimal
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.models.observation import Observation
from app.models.trust_evaluation import TrustEvaluation
from app.services.observation_quality_service import ObservationQualityService, classify_observation_data
from app.services.source_agreement_service import SourceAgreementService, is_observation_comparable


class TrustEngineService:
    TRUST_ENGINE_VERSION = "v1"
    DEFAULT_EXPECTED_SOURCES = ["SRC_GOOGLE_FLIGHTS", "SRC_DUFFEL"]
    DEFAULT_MIN_OBSERVATIONS_PER_SOURCE = 5
    DISCLAIMER = (
        "The Trust Score is an AeroCPI prototype measurement-assurance indicator. "
        "Its weights and thresholds are transparent engineering policy choices and are not "
        "official MoSPI statistical parameters. The score should be validated and calibrated "
        "against historical or expert-reviewed quality outcomes before being treated as a "
        "formal statistical confidence measure."
    )


    @classmethod
    def evaluate_measurement_trust(
        cls,
        observations: List[Observation],
        route_id: str,
        travel_date: dt.date,
        horizon: int,
        cabin: str = "ECONOMY",
        collection_date: Optional[dt.date] = None,
        expected_observations: Optional[int] = None,
        expected_sources: Optional[List[str]] = None,
        min_observations_per_source: int = DEFAULT_MIN_OBSERVATIONS_PER_SOURCE,
        index_run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pure deterministic function that calculates the Measurement Trust Score (0 to 100)
        and evaluates all 7 dimensions and override rules.
        """
        cabin_clean = cabin.strip().upper()
        target_expected_sources = expected_sources if expected_sources is not None else cls.DEFAULT_EXPECTED_SOURCES
        horizon_code = f"T+{horizon}"

        # 1. Reuse 4C.1 Quality Metrics and 4C.2 Source Agreement
        quality_metrics = ObservationQualityService.compute_quality_metrics(
            observations=observations,
            route_id=route_id,
            travel_date=travel_date,
            horizon=horizon,
            cabin=cabin_clean,
            collection_date=collection_date
        )

        source_agreement = SourceAgreementService.evaluate_source_agreement(
            observations=observations,
            route_id=route_id,
            travel_date=travel_date,
            horizon=horizon,
            cabin=cabin_clean,
            collection_date=collection_date,
            expected_sources=target_expected_sources,
            min_observations_per_source=min_observations_per_source
        )

        # 2. Extract population & classification counts
        pop_summary = quality_metrics["population_summary"]
        total_obs = pop_summary["total_observations"]
        accepted_obs = pop_summary["accepted_observations"]
        flagged_obs = pop_summary["flagged_observations"]
        rejected_obs = pop_summary["rejected_observations"]
        eligible_obs = pop_summary["index_eligible_observations"]
        data_classes = pop_summary.get("data_classification_distribution", {})
        live_obs_count = data_classes.get("LIVE_MARKET_DATA", 0)
        test_obs_count = data_classes.get("TEST_DATA", 0)

        # Active eligible sources from 4C.2
        cross_source = source_agreement["cross_source_agreement"]
        k_active = cross_source["active_eligible_sources_count"]
        active_sources = cross_source["active_eligible_sources"]
        health_4c2 = source_agreement["health_evaluation"]["health_status"]

        # -------------------------------------------------------------
        # DIMENSION 1 — Observation Coverage (Max 20.0 pts)
        # -------------------------------------------------------------
        # expected_observations derived from specification (e.g. min_per_source * expected_sources_count or explicit spec)
        derived_expected_obs = expected_observations
        if derived_expected_obs is None:
            derived_expected_obs = len(target_expected_sources) * min_observations_per_source

        if derived_expected_obs <= 0:
            coverage_ratio = 0.0
            coverage_score = 0.0
            coverage_status = "COVERAGE_UNAVAILABLE"
        else:
            coverage_ratio = min(1.0, round(eligible_obs / derived_expected_obs, 4))
            coverage_score = round(20.0 * coverage_ratio, 2)
            coverage_status = "FULL_COVERAGE" if coverage_ratio >= 1.0 else ("PARTIAL_COVERAGE" if coverage_ratio > 0 else "ZERO_COVERAGE")

        # -------------------------------------------------------------
        # DIMENSION 2 — Source Agreement (Max 20.0 pts)
        # -------------------------------------------------------------
        pct_med_diff = cross_source.get("percentage_median_difference")
        if k_active == 0:
            agreement_score = 0.0
            agreement_status = "NO_ELIGIBLE_SOURCE_DATA"
        elif k_active == 1:
            agreement_score = 0.0
            agreement_status = "SINGLE_SOURCE"
        else:
            if pct_med_diff is None:
                agreement_score = 0.0
                agreement_status = "AGREEMENT_UNAVAILABLE"
            elif pct_med_diff <= 2.0:
                agreement_score = 20.0
                agreement_status = "EXCELLENT_AGREEMENT"
            elif pct_med_diff <= 5.0:
                agreement_score = 17.0
                agreement_status = "GOOD_AGREEMENT"
            elif pct_med_diff <= 10.0:
                agreement_score = 12.0
                agreement_status = "MODERATE_AGREEMENT"
            elif pct_med_diff <= 20.0:
                agreement_score = 6.0
                agreement_status = "WEAK_AGREEMENT"
            else:
                agreement_score = 0.0
                agreement_status = "DISCREPANT_SOURCES"

        # -------------------------------------------------------------
        # DIMENSION 3 — Sample Sufficiency (Max 15.0 pts)
        # -------------------------------------------------------------
        source_metrics = source_agreement["source_wise_metrics"]
        if k_active == 0:
            min_source_ratio = 0.0
            sample_sufficiency_score = 0.0
            weakest_source_count = 0
        else:
            source_eligible_counts = [source_metrics[s]["eligible_observations_count"] for s in active_sources]
            weakest_source_count = min(source_eligible_counts)
            min_source_ratio = min(1.0, weakest_source_count / min_observations_per_source)
            sample_sufficiency_score = round(15.0 * min_source_ratio, 2)

        # -------------------------------------------------------------
        # DIMENSION 4 — Observation Validity (Max 15.0 pts)
        # -------------------------------------------------------------
        if total_obs > 0:
            validity_ratio = min(1.0, round(eligible_obs / total_obs, 4))
        else:
            validity_ratio = 0.0
        validity_score = round(15.0 * validity_ratio, 2)

        # -------------------------------------------------------------
        # DIMENSION 5 — Outlier Health (Max 10.0 pts)
        # -------------------------------------------------------------
        outlier_count = 0
        for obs in observations:
            inelig_status = str(getattr(obs, "index_eligibility", "INELIGIBLE") or "INELIGIBLE").upper()
            val_reasons = getattr(obs, "validation_reasons", None) or []
            if inelig_status == "ELIGIBLE" and any("OUTLIER" in str(r).upper() for r in val_reasons):
                outlier_count += 1

        if eligible_obs > 0:
            outlier_rate = round(outlier_count / eligible_obs, 4)
            outlier_pct = outlier_rate * 100.0
            if outlier_pct <= 2.0:
                outlier_health_score = 10.0
            elif outlier_pct <= 5.0:
                outlier_health_score = 8.0
            elif outlier_pct <= 10.0:
                outlier_health_score = 5.0
            elif outlier_pct <= 20.0:
                outlier_health_score = 2.0
            else:
                outlier_health_score = 0.0
        else:
            outlier_rate = 0.0
            outlier_health_score = 0.0

        # -------------------------------------------------------------
        # DIMENSION 6 — Source Availability (Max 10.0 pts)
        # -------------------------------------------------------------
        k_expected = len(target_expected_sources)
        if k_expected <= 0:
            source_cov_ratio = 0.0
            source_availability_score = 0.0
            source_avail_status = "SOURCE_AVAILABILITY_UNAVAILABLE"
        else:
            source_cov_ratio = min(1.0, round(k_active / k_expected, 4))
            source_availability_score = round(10.0 * source_cov_ratio, 2)
            source_avail_status = "ALL_SOURCES_AVAILABLE" if source_cov_ratio >= 1.0 else ("PARTIAL_SOURCES_AVAILABLE" if source_cov_ratio > 0 else "NO_SOURCES_AVAILABLE")

        # -------------------------------------------------------------
        # DIMENSION 7 — Basket / Horizon Stability (Max 10.0 pts, 5 binary checks)
        # -------------------------------------------------------------
        # Check 1: Route mapping is valid
        chk_route_valid = bool(route_id and len(route_id.split("-")) == 2 and all(getattr(o, "route_id", None) == route_id for o in observations) if observations else bool(route_id))
        # Check 2: Route belongs to DGCA reference basket
        # Check if basket_status on observations is ROUTE_IN_REFERENCE_BASKET or standard basket route
        chk_basket_valid = True
        if observations:
            chk_basket_valid = any(getattr(o, "basket_status", "") == "ROUTE_IN_REFERENCE_BASKET" for o in observations) or route_id in [
                "DEL-BOM", "BLR-DEL", "BOM-BLR", "DEL-HYD", "DEL-CCU", "DEL-MAA", "BOM-GOI", "BLR-HYD", "DEL-PAT", "BLR-CCU"
            ]
        # Check 3: Requested horizon exists and matches
        chk_horizon_valid = bool(horizon > 0 and (all(getattr(o, "booking_horizon_days", None) == horizon for o in observations) if observations else True))
        # Check 4: Cabin is present and matches target cabin
        chk_cabin_valid = bool(cabin_clean and (all(str(getattr(o, "cabin", "")).upper() == cabin_clean for o in observations) if observations else True))
        # Check 5: Homogeneous group (no incompatible horizon/cabin mixing)
        chk_no_mixing = True
        if observations:
            obs_horizons = set(getattr(o, "booking_horizon_days", None) for o in observations)
            obs_cabins = set(str(getattr(o, "cabin", "")).upper() for o in observations)
            chk_no_mixing = (len(obs_horizons) <= 1) and (len(obs_cabins) <= 1)

        stability_checks = {
            "route_mapping_valid": chk_route_valid,
            "route_in_reference_basket": chk_basket_valid,
            "horizon_specification_matches": chk_horizon_valid,
            "cabin_specification_matches": chk_cabin_valid,
            "no_incompatible_mixing": chk_no_mixing
        }
        passed_stability_checks = sum(1 for v in stability_checks.values() if v)
        basket_horizon_stability_score = round(passed_stability_checks * 2.0, 2)

        # -------------------------------------------------------------
        # TOTAL SCORE & STATUS EVALUATION
        # -------------------------------------------------------------
        raw_trust_score = round(
            coverage_score +
            agreement_score +
            sample_sufficiency_score +
            validity_score +
            outlier_health_score +
            source_availability_score +
            basket_horizon_stability_score,
            2
        )
        raw_trust_score = max(0.0, min(100.0, raw_trust_score))

        # Initial Status
        if raw_trust_score >= 85.0:
            initial_status = "HIGH_TRUST"
        elif raw_trust_score >= 70.0:
            initial_status = "MODERATE_TRUST"
        elif raw_trust_score >= 50.0:
            initial_status = "DEGRADED_TRUST"
        else:
            initial_status = "LOW_TRUST"

        # -------------------------------------------------------------
        # REASON CODES ACCUMULATION
        # -------------------------------------------------------------
        reason_codes: List[str] = []

        if coverage_status == "COVERAGE_UNAVAILABLE":
            reason_codes.append("COVERAGE_UNAVAILABLE")
        elif coverage_ratio < 0.75:
            reason_codes.append("LOW_COVERAGE")

        if agreement_status == "SINGLE_SOURCE":
            reason_codes.append("SINGLE_SOURCE")
        elif agreement_status == "NO_ELIGIBLE_SOURCE_DATA":
            reason_codes.append("NO_ELIGIBLE_SOURCE_DATA")
        elif agreement_status == "DISCREPANT_SOURCES" or (pct_med_diff is not None and pct_med_diff > 10.0):
            reason_codes.append("LARGE_SOURCE_DISCREPANCY")

        if cross_source.get("observation_count_imbalance_ratio", 1.0) > 4.0:
            reason_codes.append("SOURCE_SAMPLE_IMBALANCE")

        if k_active > 0 and weakest_source_count < min_observations_per_source:
            reason_codes.append("INSUFFICIENT_SAMPLE_SIZE")

        if validity_ratio < 0.80:
            reason_codes.append("LOW_VALIDITY_RATE")

        if outlier_rate > 0.05:
            reason_codes.append("HIGH_OUTLIER_RATE")

        if source_avail_status == "SOURCE_AVAILABILITY_UNAVAILABLE":
            reason_codes.append("SOURCE_AVAILABILITY_UNAVAILABLE")
        elif source_cov_ratio < 1.0:
            reason_codes.append("SOURCE_UNAVAILABLE")

        if not chk_basket_valid:
            reason_codes.append("BASKET_MISMATCH")
        if not chk_horizon_valid:
            reason_codes.append("HORIZON_MISMATCH")
        if not chk_cabin_valid:
            reason_codes.append("CABIN_MISMATCH")

        # -------------------------------------------------------------
        # OVERRIDE RULES & EXACT CEILINGS
        # -------------------------------------------------------------
        final_trust_score = raw_trust_score
        final_status = initial_status

        # Rule B: Test-mode isolation vs mixed data
        if live_obs_count == 0 and test_obs_count > 0:
            final_trust_score = 0.0
            final_status = "LOW_TRUST"
            if "TEST_DATA_ONLY" not in reason_codes:
                reason_codes.append("TEST_DATA_ONLY")

        # Rule A: Zero eligible observations
        elif eligible_obs == 0:
            final_trust_score = 0.0
            final_status = "LOW_TRUST"
            if "NO_ELIGIBLE_OBSERVATIONS" not in reason_codes:
                reason_codes.append("NO_ELIGIBLE_OBSERVATIONS")

        # If mixed live and test data exists
        if live_obs_count > 0 and test_obs_count > 0:
            reason_codes.append("MIXED_LIVE_AND_TEST_DATA")

        # Rule C: 4C.2 Insufficient Health Cap
        if health_4c2 == "INSUFFICIENT" and eligible_obs > 0:
            if final_trust_score > 84.99:
                final_trust_score = 84.99
            if final_status == "HIGH_TRUST":
                final_status = "MODERATE_TRUST"
            if "LIMITED_BY_INSUFFICIENT_HEALTH" not in reason_codes:
                reason_codes.append("LIMITED_BY_INSUFFICIENT_HEALTH")

        # Rule D: Single source cap
        if k_active == 1 and k_expected > 1 and eligible_obs > 0:
            if final_trust_score > 84.99:
                final_trust_score = 84.99
            if final_status == "HIGH_TRUST":
                final_status = "MODERATE_TRUST"
            if "LIMITED_BY_SINGLE_SOURCE" not in reason_codes:
                reason_codes.append("LIMITED_BY_SINGLE_SOURCE")

        # Rule E: Severe sample deficiency cap (< 2 eligible obs on any active source)
        if k_active > 0 and weakest_source_count < 2 and eligible_obs > 0:
            if final_trust_score > 84.99:
                final_trust_score = 84.99
            if final_status == "HIGH_TRUST":
                final_status = "MODERATE_TRUST"
            if "INSUFFICIENT_SAMPLE_SIZE" not in reason_codes:
                reason_codes.append("INSUFFICIENT_SAMPLE_SIZE")

        # Re-verify status band against final capped score if not overridden to LOW_TRUST
        if final_status != "LOW_TRUST" and eligible_obs > 0 and not (live_obs_count == 0 and test_obs_count > 0):
            if final_trust_score >= 85.0:
                final_status = "HIGH_TRUST"
            elif final_trust_score >= 70.0:
                final_status = "MODERATE_TRUST"
            elif final_trust_score >= 50.0:
                final_status = "DEGRADED_TRUST"
            else:
                final_status = "LOW_TRUST"

        # If healthy evidence base
        if final_status == "HIGH_TRUST" and len(reason_codes) == 0:
            reason_codes = ["HEALTHY_EVIDENCE_BASE"]
        elif not reason_codes:
            reason_codes = ["HEALTHY_EVIDENCE_BASE"]

        # -------------------------------------------------------------
        # FINGERPRINT CALCULATION (SHA-256)
        # -------------------------------------------------------------
        dimension_breakdown = {
            "observation_coverage": coverage_score,
            "source_agreement": agreement_score,
            "sample_sufficiency": sample_sufficiency_score,
            "observation_validity": validity_score,
            "outlier_health": outlier_health_score,
            "source_availability": source_availability_score,
            "basket_horizon_stability": basket_horizon_stability_score
        }

        trust_scope = {
            "route_id": route_id,
            "travel_date": travel_date.isoformat(),
            "horizon_days": horizon,
            "horizon_code": horizon_code,
            "cabin": cabin_clean,
            "collection_date": collection_date.isoformat() if collection_date else None,
            "index_run_id": index_run_id,
            "target_basket": "DGCA_REFERENCE_BASKET" if chk_basket_valid else "EXTENDED_ROUTE_NETWORK",
            "population_definition": "Live market quotes matching exact route, travel date, booking horizon, cabin, and collection date"
        }

        policy_parameters = {
            "policy_version": "v1.0",
            "policy_authority": "AeroCPI Engineering Measurement Assurance Policy (Non-MoSPI)",
            "is_official_statistical_parameter": False,
            "min_observations_per_source": min_observations_per_source,
            "expected_sources": target_expected_sources,
            "expected_required_observations": derived_expected_obs,
            "agreement_thresholds_pct": {
                "excellent": 2.0,
                "good": 5.0,
                "moderate": 10.0,
                "weak": 20.0
            },
            "sample_imbalance_threshold_ratio": 4.0,
            "outlier_tolerance_pct": 5.0,
            "validity_tolerance_ratio": 0.80,
            "coverage_tolerance_ratio": 0.75,
            "overlapping_penalties_principle": "Intentionally permitted to reflect multi-faceted diagnostic degradation from shared root causes."
        }

        evidence_summary = {
            "coverage_ratio": coverage_ratio,
            "expected_required_observations": derived_expected_obs,
            "percentage_median_difference": pct_med_diff,
            "active_eligible_sources_count": k_active,
            "expected_sources_count": k_expected,
            "minimum_source_observation_count": weakest_source_count,
            "total_observations": total_obs,
            "eligible_observations": eligible_obs,
            "accepted_observations": accepted_obs,
            "flagged_observations": flagged_obs,
            "rejected_observations": rejected_obs,
            "validity_ratio": validity_ratio,
            "outlier_count": outlier_count,
            "outlier_rate": outlier_rate,
            "source_coverage_ratio": source_cov_ratio,
            "stability_checks": stability_checks,
            "live_market_data_count": live_obs_count,
            "test_data_count": test_obs_count,
            "trust_scope": trust_scope,
            "policy_parameters": policy_parameters
        }

        fingerprint_payload = {
            "trust_engine_version": cls.TRUST_ENGINE_VERSION,
            "route_id": route_id,
            "travel_date": travel_date.isoformat(),
            "horizon_days": horizon,
            "cabin": cabin_clean,
            "collection_date": collection_date.isoformat() if collection_date else None,
            "dimension_breakdown": dimension_breakdown,
            "trust_score": final_trust_score,
            "trust_status": final_status,
            "reason_codes": sorted(reason_codes),
            "evidence_summary": evidence_summary
        }
        fingerprint_json = json.dumps(fingerprint_payload, sort_keys=True)
        calculation_fingerprint = hashlib.sha256(fingerprint_json.encode("utf-8")).hexdigest()

        return {
            "trust_engine_version": cls.TRUST_ENGINE_VERSION,
            "trust_score": final_trust_score,
            "trust_status": final_status,
            "trust_scope": trust_scope,
            "policy_parameters": policy_parameters,
            "health_status_from_4c2": health_4c2,
            "dimension_scores": dimension_breakdown,
            "evidence": evidence_summary,
            "reason_codes": reason_codes,
            "calculation_fingerprint": calculation_fingerprint,
            "metadata": {
                "route_id": route_id,
                "travel_date": travel_date.isoformat(),
                "horizon_days": horizon,
                "horizon_code": horizon_code,
                "cabin": cabin_clean,
                "collection_date": collection_date.isoformat() if collection_date else None,
                "index_run_id": index_run_id,
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "disclaimer": cls.DISCLAIMER,
                "trust_scope": trust_scope,
                "policy_parameters": policy_parameters
            }
        }

    @classmethod
    def evaluate_and_store_route_trust(
        cls,
        db: Session,
        route_id: str,
        travel_date: dt.date,
        horizon: int,
        cabin: str = "ECONOMY",
        collection_date: Optional[dt.date] = None,
        expected_observations: Optional[int] = None,
        expected_sources: Optional[List[str]] = None,
        min_observations_per_source: int = DEFAULT_MIN_OBSERVATIONS_PER_SOURCE,
        index_run_id: Optional[str] = None
    ) -> TrustEvaluation:
        """
        Evaluates trust for route context from database observations and persists
        the TrustEvaluation record.
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

        report = cls.evaluate_measurement_trust(
            observations=observations,
            route_id=route_id,
            travel_date=travel_date,
            horizon=horizon,
            cabin=cabin_clean,
            collection_date=collection_date,
            expected_observations=expected_observations,
            expected_sources=expected_sources,
            min_observations_per_source=min_observations_per_source,
            index_run_id=index_run_id
        )

        dim = report["dimension_scores"]
        ev = report["evidence"]

        record = TrustEvaluation(
            index_run_id=index_run_id,
            route_id=route_id,
            travel_date=travel_date,
            horizon_code=f"T+{horizon}",
            cabin=cabin_clean,
            collection_date=collection_date,
            trust_engine_version=report["trust_engine_version"],
            trust_score=Decimal(str(report["trust_score"])),
            trust_status=report["trust_status"],
            coverage_score=Decimal(str(dim["observation_coverage"])),
            agreement_score=Decimal(str(dim["source_agreement"])),
            sample_sufficiency_score=Decimal(str(dim["sample_sufficiency"])),
            validity_score=Decimal(str(dim["observation_validity"])),
            outlier_health_score=Decimal(str(dim["outlier_health"])),
            source_availability_score=Decimal(str(dim["source_availability"])),
            basket_horizon_stability_score=Decimal(str(dim["basket_horizon_stability"])),
            total_observations=ev["total_observations"],
            eligible_observations=ev["eligible_observations"],
            flagged_observations=ev["flagged_observations"],
            rejected_observations=ev["rejected_observations"],
            source_count=ev["active_eligible_sources_count"],
            health_status_from_4c2=report["health_status_from_4c2"],
            reason_codes=report["reason_codes"],
            dimension_breakdown=dim,
            evidence_summary=ev,
            calculation_fingerprint=report["calculation_fingerprint"]
        )

        db.add(record)
        db.commit()
        db.refresh(record)
        return record
