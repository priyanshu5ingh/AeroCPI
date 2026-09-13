from __future__ import annotations
import json
import hashlib
import datetime as dt
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.index_run import IndexRun
from app.models.horizon_index_result import HorizonIndexResult
from app.models.route_index_result import RouteIndexResult
from app.models.trust_evaluation import TrustEvaluation
from app.schemas.index_audit import (
    IndexAuditResponse,
    AuditScope,
    RunIdentity,
    VersionAudit,
    PopulationAudit,
    RouteAudit,
    HorizonRouteAudit,
    CoverageAudit,
    HorizonCoverageAudit,
    TrustAudit,
    ReproducibilityAudit
)
from app.services.dgca_basket_service import DGCABasketService


class IndexAuditService:
    """
    Milestone 5B Audit Service:
    Provides a machine-readable historical audit and reproducibility record for a completed AeroCPI index run.
    Derives all audit metrics strictly from stored IndexRun, HorizonIndexResult, RouteIndexResult, TrustEvaluation,
    and calculation_manifest artifacts without modifying 4D/5A, re-querying raw observations, or mutating state.
    """

    @classmethod
    def audit_index_run(cls, db: Session, run_id: str) -> IndexAuditResponse:
        """
        Generates full audit response for a specified run_id.
        Raises ValueError if run_id is not found.
        """
        # 1. Fetch IndexRun (read-only)
        run = db.query(IndexRun).filter(IndexRun.run_id == run_id).first()
        if not run:
            raise ValueError(f"INDEX_RUN_NOT_FOUND: Index run '{run_id}' not found.")

        # 2. Fetch associated horizon and route results
        horizons = (
            db.query(HorizonIndexResult)
            .filter(HorizonIndexResult.run_id == run_id)
            .order_by(HorizonIndexResult.horizon_days.asc())
            .all()
        )

        routes = (
            db.query(RouteIndexResult)
            .filter(RouteIndexResult.run_id == run_id)
            .all()
        )

        # 3. Fetch trust evaluation
        trust_eval = None
        if run.trust_evaluation_id:
            trust_eval = (
                db.query(TrustEvaluation)
                .filter(TrustEvaluation.trust_evaluation_id == run.trust_evaluation_id)
                .first()
            )
        if not trust_eval:
            trust_eval = (
                db.query(TrustEvaluation)
                .filter(TrustEvaluation.index_run_id == run_id)
                .first()
            )

        manifest = run.calculation_manifest or {}

        # 4. Manifest SHA-256 hash
        if manifest:
            manifest_json = json.dumps(manifest, sort_keys=True)
            manifest_sha256 = hashlib.sha256(manifest_json.encode("utf-8")).hexdigest()
            manifest_present = True
        else:
            manifest_sha256 = None
            manifest_present = False

        # 5. Scope
        reference_date = run.reference_period
        calculation_date = run.comparison_period
        cabin = manifest.get("cabin", "ECONOMY")
        basket_version = run.route_basket_version

        basket_routes = manifest.get("routes_used")
        if not basket_routes:
            try:
                basket_weights, basket_routes = DGCABasketService.get_basket_weights(db, basket_version)
            except Exception:
                basket_routes = sorted(list(set(r.route_id for r in routes)))

        n_basket = len(basket_routes)

        audit_scope = AuditScope(
            run_id=run.run_id,
            reference_date=reference_date,
            calculation_date=calculation_date,
            cabin=cabin,
            basket_version=basket_version,
            audit_timestamp=dt.datetime.now(dt.timezone.utc)
        )

        # 6. Run Identity & Headline Reconciliation
        headline_h = next((h for h in horizons if h.is_headline), None)
        if not headline_h and horizons:
            headline_h = next((h for h in horizons if h.horizon_code == "T+15"), horizons[0])

        headline_index_value = float(run.index_value)
        headline_horizon_code = headline_h.horizon_code if headline_h else "T+15"

        run_identity = RunIdentity(
            run_id=run.run_id,
            run_timestamp=run.run_timestamp,
            reference_period=run.reference_period,
            comparison_period=run.comparison_period,
            index_method=run.index_method,
            frequency=run.frequency,
            headline_index_value=headline_index_value,
            headline_horizon_code=headline_horizon_code
        )

        # 7. Versions
        versions = VersionAudit(
            methodology_version=run.methodology_version,
            route_basket_version=run.route_basket_version,
            proxy_weight_version=run.proxy_weight_version,
            software_version=run.software_version,
            quality_rule_version=run.quality_rule_version,
            normalization_version=run.normalization_version
        )

        # 8. Population Audit (strictly persisted facts, null for non-persisted metrics)
        obs_manifest = manifest.get("observations", {}) if manifest else {}
        ref_date_count = obs_manifest.get("reference_date_count")
        calc_date_count = obs_manifest.get("calculation_date_count")

        limitations: List[str] = []

        if ref_date_count is None or calc_date_count is None:
            limitations.append(
                "POPULATION_METRIC_NOT_PERSISTED: Exact collection date observation counts (reference vs calculation date) "
                "were not recorded in the persisted run manifest."
            )

        limitations.append(
            "RAW_CAPTURE_PAYLOADS_NOT_IN_DB: Raw HTML capture files reside on filesystem storage outside SQL database tables."
        )
        limitations.append(
            "CARRIER_MARKET_SHARE_NOT_PERSISTED: Carrier-specific market share breakdown is not stored in elementary route index results."
        )

        rejection_breakdown = {
            "excluded_count": run.excluded_count,
            "outlier_flagged_count": run.outlier_flagged_count,
            "retained_with_warning_count": run.retained_with_warning_count,
            "duplicate_observations": run.number_of_duplicates
        }

        provenance_stat = "DERIVED_FROM_PERSISTED_RUN_ARTIFACT" if manifest_present else "PERSISTED"

        population_audit = PopulationAudit(
            total_observations_queried=run.number_of_observations,
            total_eligible_observations=run.number_of_eligible_observations,
            total_excluded_observations=run.number_of_excluded_observations,
            rejection_breakdown=rejection_breakdown,
            reference_date_count=ref_date_count,
            calculation_date_count=calc_date_count,
            provenance_status=provenance_stat
        )

        # 9. Route Audit (derived from persisted 4D facts)
        expected_pairs = run.expected_route_horizon_pairs or (n_basket * len(horizons))
        calculated_pairs = len(routes) if routes else run.calculated_route_horizon_pairs
        unavailable_pairs = max(0, expected_pairs - calculated_pairs)

        horizon_route_counts: List[HorizonRouteAudit] = []
        for h in horizons:
            h_routes = [r for r in routes if r.booking_horizon == h.horizon_days]
            active_c = len(h_routes)
            base_c = h.base_routes_count
            missing_c = max(0, n_basket - active_c)

            horizon_route_counts.append(
                HorizonRouteAudit(
                    horizon_code=h.horizon_code,
                    horizon_days=h.horizon_days,
                    active_routes_count=active_c,
                    base_routes_count=base_c,
                    missing_routes_count=missing_c,
                    total_basket_routes_count=n_basket
                )
            )

        route_audit = RouteAudit(
            total_basket_routes=n_basket,
            expected_route_horizon_pairs=expected_pairs,
            calculated_route_horizon_pairs=calculated_pairs,
            unavailable_route_horizon_pairs=unavailable_pairs,
            horizon_route_counts=horizon_route_counts
        )

        # 10. Coverage Audit
        horizon_coverage: List[HorizonCoverageAudit] = []
        for h in horizons:
            horizon_coverage.append(
                HorizonCoverageAudit(
                    horizon_code=h.horizon_code,
                    base_coverage_ratio=float(h.base_coverage_ratio),
                    current_coverage_ratio=float(h.current_coverage_ratio),
                    matched_coverage_ratio=float(h.matched_coverage_ratio),
                    active_weight_sum=float(h.active_weight_sum)
                )
            )

        coverage_audit = CoverageAudit(
            headline_coverage_ratio=float(run.coverage_ratio),
            horizon_coverage=horizon_coverage,
            temporal_coverage_status="NOT_APPLICABLE_FOR_SINGLE_RUN"
        )

        # 11. Trust Audit
        if trust_eval:
            trust_audit = TrustAudit(
                trust_evaluation_id=trust_eval.trust_evaluation_id,
                trust_score=float(trust_eval.trust_score),
                trust_status=trust_eval.trust_status,
                reason_codes=trust_eval.reason_codes or [],
                is_diagnostic_only=True,
                trust_evaluation_status="VERIFIED_FROM_PERSISTED_EVALUATION"
            )
        else:
            trust_audit = TrustAudit(
                trust_evaluation_id=None,
                trust_score=None,
                trust_status="UNEVALUATED",
                reason_codes=[],
                is_diagnostic_only=True,
                trust_evaluation_status="UNEVALUATED"
            )

        # 12. Reproducibility Audit
        reproducibility_status = "ARTIFACT_REPRODUCIBLE" if manifest_present else "NOT_REPRODUCIBLE"

        reproducibility_audit = ReproducibilityAudit(
            canonical_run_fingerprint=run.canonical_run_fingerprint,
            manifest_sha256=manifest_sha256,
            manifest_present=manifest_present,
            raw_input_artifacts_available=False,
            is_reproducible=False,
            reproducibility_status=reproducibility_status
        )

        return IndexAuditResponse(
            audit_scope=audit_scope,
            run_identity=run_identity,
            versions=versions,
            population_audit=population_audit,
            route_audit=route_audit,
            coverage_audit=coverage_audit,
            trust_audit=trust_audit,
            reproducibility_audit=reproducibility_audit,
            calculation_manifest=manifest,
            limitations=limitations
        )
