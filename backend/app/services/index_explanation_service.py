from __future__ import annotations
import math
from decimal import Decimal, ROUND_HALF_UP
import datetime as dt
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.index_run import IndexRun
from app.models.horizon_index_result import HorizonIndexResult
from app.models.route_index_result import RouteIndexResult
from app.models.trust_evaluation import TrustEvaluation
from app.schemas.index_explanation import (
    IndexExplanationResponse,
    ExplanationScope,
    HorizonExplanation,
    RouteContributionExplanation,
    MissingRouteInfo,
    TrustExplanation
)
from app.services.dgca_basket_service import DGCABasketService


class IndexExplanationService:
    """
    Milestone 5A Explanation Service:
    Provides transparent, mathematically traceable explanations of a completed AeroCPI index run.
    Derives metrics strictly from persisted IndexRun, HorizonIndexResult, RouteIndexResult, TrustEvaluation,
    and calculation_manifest records without modifying the underlying index engine, querying raw observations,
    or mutating database state.
    """

    ZERO_SHIFT_EPSILON = 1e-9
    TOLERANCE_EPSILON = 1e-6

    @classmethod
    def explain_index_run(cls, db: Session, run_id: str) -> IndexExplanationResponse:
        """
        Derives full explanation object for a specified index_run_id.
        Raises ValueError if run_id is not found or if point contribution identity fails tolerance check.
        """
        # 1. Fetch IndexRun (read-only)
        run = db.query(IndexRun).filter(IndexRun.run_id == run_id).first()
        if not run:
            raise ValueError(f"INDEX_RUN_NOT_FOUND: Index run '{run_id}' not found.")

        # 2. Fetch associated horizon and route results (strictly persisted 4D facts)
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

        # 3. Fetch associated trust evaluation
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

        # 4. Extract scope details
        reference_date = run.reference_period
        calculation_date = run.comparison_period
        cabin = manifest.get("cabin", "ECONOMY")
        basket_version = run.route_basket_version

        # Determine full basket routes from manifest or DGCA Basket Service
        basket_routes = manifest.get("routes_used")
        if not basket_routes:
            try:
                basket_weights, basket_routes = DGCABasketService.get_basket_weights(db, basket_version)
            except Exception:
                basket_routes = sorted(list(set(r.route_id for r in routes)))

        scope = ExplanationScope(
            run_id=run.run_id,
            reference_date=reference_date,
            calculation_date=calculation_date,
            cabin=cabin,
            basket_version=basket_version
        )

        # 5. Process per-horizon explanations
        horizon_explanations: List[HorizonExplanation] = []
        headline_horizon_code = "T+15"
        headline_index_value = float(run.index_value)

        for h in horizons:
            h_code = h.horizon_code
            h_days = h.horizon_days
            if h.is_headline and h.index_value is not None:
                headline_horizon_code = h_code
                headline_index_value = float(h.index_value)

            # Filter active routes strictly from persisted RouteIndexResult records for this horizon
            h_routes = [r for r in routes if r.booking_horizon == h_days]
            active_w_sum = sum(r.weight_share for r in h_routes)
            if active_w_sum <= 0:
                active_w_sum = 1.0

            I_val = h.index_value
            sum_w_log_j = sum(
                (r.weight_share / active_w_sum) * math.log(r.route_index_value / 100.0)
                for r in h_routes if r.route_index_value > 0
            )

            is_zero_shift = False
            if I_val is None or I_val <= 0 or abs(sum_w_log_j) <= cls.ZERO_SHIFT_EPSILON or abs(I_val - 100.0) <= cls.ZERO_SHIFT_EPSILON:
                is_zero_shift = True

            horizon_reason_codes: List[str] = []
            if is_zero_shift:
                horizon_reason_codes.append("ZERO_NATIONAL_LOG_SHIFT")

            # Route contributions
            route_contributions: List[RouteContributionExplanation] = []
            unrounded_point_contribs: List[float] = []

            for r in h_routes:
                w_active = r.weight_share / active_w_sum
                j_val = r.route_index_value
                ln_j_ratio = math.log(j_val / 100.0) if j_val > 0 else 0.0
                log_contrib = round(w_active * ln_j_ratio, 6)

                if is_zero_shift:
                    pt_contrib_dec = None
                    direction = "NEUTRAL"
                else:
                    delta_I = I_val - 100.0
                    c_r = w_active * (ln_j_ratio / sum_w_log_j) * delta_I
                    unrounded_point_contribs.append(c_r)

                    pt_contrib_dec = Decimal(str(round(c_r, 4))).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

                    if c_r > 1e-6:
                        direction = "POSITIVE"
                    elif c_r < -1e-6:
                        direction = "NEGATIVE"
                    else:
                        direction = "NEUTRAL"

                route_contributions.append(
                    RouteContributionExplanation(
                        route_id=r.route_id,
                        horizon_code=h_code,
                        collection_date=calculation_date,
                        origin_code=r.origin_code,
                        destination_code=r.destination_code,
                        base_representative_fare=float(r.reference_price),
                        current_representative_fare=float(r.current_price),
                        price_relative=float(r.price_relative),
                        route_index_value=float(r.route_index_value),
                        dgca_basket_weight=float(r.weight_share),
                        active_weight=round(w_active, 6),
                        log_contribution=log_contrib,
                        point_contribution=pt_contrib_dec,
                        direction=direction
                    )
                )

            # Invariant check: Additive point attribution identity within tolerance
            if not is_zero_shift and I_val is not None and unrounded_point_contribs:
                total_c = sum(unrounded_point_contribs)
                expected_delta = I_val - 100.0
                if abs(total_c - expected_delta) > cls.TOLERANCE_EPSILON:
                    raise ValueError(
                        f"CONTRIBUTION_IDENTITY_VIOLATION: Point contribution sum ({total_c}) "
                        f"deviates from national index shift ({expected_delta}) beyond tolerance {cls.TOLERANCE_EPSILON}."
                    )

            # Missing routes classification based strictly on persisted 4D facts
            active_route_ids = set(r.route_id for r in h_routes)
            missing_routes_info: List[MissingRouteInfo] = []

            nat_manifest = manifest.get("national_horizon_indices", {}).get(h_code, {})

            for b_route in basket_routes:
                if b_route not in active_route_ids:
                    # Precedence: NO_BASE_OBSERVATION > LATE_APPEARING_EXCLUDED > MISSING_CURRENT_OBSERVATION
                    if b_route in nat_manifest.get("late_appearing_excluded_routes", []):
                        reason = "LATE_APPEARING_EXCLUDED"
                        desc = f"Route '{b_route}' observed on calculation date but excluded as late-appearing."
                    elif b_route in nat_manifest.get("missing_routes", []):
                        reason = "MISSING_CURRENT_OBSERVATION"
                        desc = f"Route '{b_route}' present in base period ({reference_date}) but missing on calculation date ({calculation_date})."
                    else:
                        reason = "NO_BASE_OBSERVATION"
                        desc = f"Route '{b_route}' lacked eligible base observations on baseline reference date ({reference_date})."

                    missing_routes_info.append(
                        MissingRouteInfo(
                            route_id=b_route,
                            horizon_code=h_code,
                            reason_code=reason,
                            description=desc
                        )
                    )

            horizon_explanations.append(
                HorizonExplanation(
                    horizon_code=h_code,
                    horizon_days=h_days,
                    collection_date=calculation_date,
                    index_name=h.index_name,
                    index_value=float(h.index_value) if h.index_value is not None else None,
                    matched_sample_index_value=float(h.matched_sample_index_value) if h.matched_sample_index_value is not None else None,
                    is_headline=h.is_headline,
                    active_routes_count=h.active_routes_count,
                    base_routes_count=h.base_routes_count,
                    total_basket_routes_count=h.total_basket_routes_count,
                    base_coverage_ratio=float(h.base_coverage_ratio),
                    current_coverage_ratio=float(h.current_coverage_ratio),
                    matched_coverage_ratio=float(h.matched_coverage_ratio),
                    active_weight_sum=float(h.active_weight_sum),
                    reason_codes=horizon_reason_codes,
                    route_contributions=route_contributions,
                    missing_routes=missing_routes_info
                )
            )

        # 6. Build TrustExplanation
        if trust_eval:
            trust_summary = TrustExplanation(
                trust_evaluation_id=trust_eval.trust_evaluation_id,
                trust_score=float(trust_eval.trust_score),
                trust_status=trust_eval.trust_status,
                reason_codes=trust_eval.reason_codes or [],
                is_diagnostic_only=True
            )
        else:
            trust_summary = TrustExplanation(
                trust_evaluation_id=None,
                trust_score=None,
                trust_status="UNEVALUATED",
                reason_codes=[],
                is_diagnostic_only=True
            )

        return IndexExplanationResponse(
            explanation_scope=scope,
            index_run_id=run.run_id,
            headline_horizon_code=headline_horizon_code,
            headline_index_value=headline_index_value,
            reference_date=reference_date,
            calculation_date=calculation_date,
            methodology_version=run.methodology_version,
            route_basket_version=run.route_basket_version,
            proxy_weight_version=run.proxy_weight_version,
            software_version=run.software_version,
            canonical_run_fingerprint=run.canonical_run_fingerprint,
            horizons=horizon_explanations,
            trust_summary=trust_summary,
            calculation_manifest=manifest
        )
