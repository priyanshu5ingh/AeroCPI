from __future__ import annotations
import datetime as dt
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.schemas.index_dashboard import (
    IndexDashboardResponse,
    DashboardScope,
    DashboardHeadline,
    RouteDriverItem,
    DriverSummary,
    HorizonCoverageItem,
    CoverageSummary,
    DashboardTrustSummary,
    MethodologySummary,
    DashboardAuditSummary
)
from app.services.index_explanation_service import IndexExplanationService
from app.services.index_audit_service import IndexAuditService


class IndexDashboardService:
    """
    Milestone 5C Decision & Presentation Service:
    Provides a compact, read-only dashboard payload synthesizing frozen 4D statistical results,
    5A attribution explanations, and 5B audit artifacts for front-end presentation.
    Does NOT calculate new indices, recalculate weights, or mutate database state.
    """

    DIRECTION_THRESHOLD = 0.001

    @classmethod
    def get_dashboard(cls, db: Session, run_id: str) -> IndexDashboardResponse:
        """
        Derives dashboard response for a given index run_id by delegating to
        IndexExplanationService (5A) and IndexAuditService (5B).
        Raises ValueError if run_id is not found.
        """
        # 1. Fetch 5A explanation and 5B audit (these raise ValueError if run_id is not found)
        explanation = IndexExplanationService.explain_index_run(db, run_id)
        audit = IndexAuditService.audit_index_run(db, run_id)

        # 2. Extract scope info
        scope_info = explanation.explanation_scope
        dashboard_scope = DashboardScope(
            run_id=scope_info.run_id,
            reference_date=scope_info.reference_date,
            calculation_date=scope_info.calculation_date,
            cabin=scope_info.cabin,
            dashboard_timestamp=dt.datetime.now(dt.timezone.utc)
        )

        # 3. Dynamic Headline Extraction
        headline_code = explanation.headline_horizon_code
        headline_val = explanation.headline_index_value

        # Find headline horizon object from 5A
        headline_horizon = next(
            (h for h in explanation.horizons if h.horizon_code == headline_code),
            explanation.horizons[0] if explanation.horizons else None
        )

        index_name = headline_horizon.index_name if headline_horizon else "AeroCPI T+15 National Index"
        change_from_base = round(headline_val - 100.0, 3)

        if change_from_base > cls.DIRECTION_THRESHOLD:
            direction = "UP"
        elif change_from_base < -cls.DIRECTION_THRESHOLD:
            direction = "DOWN"
        else:
            direction = "UNCHANGED"

        headline = DashboardHeadline(
            horizon_code=headline_code,
            index_name=index_name,
            index_value=headline_val,
            reference_date=scope_info.reference_date,
            calculation_date=scope_info.calculation_date,
            change_from_base=change_from_base,
            direction=direction,
            is_headline=True
        )

        # 4. Top Positive and Negative Drivers (from headline horizon's 5A route_contributions)
        headline_route_contribs = headline_horizon.route_contributions if headline_horizon else []

        # Convert Decimal point_contribution to float for sorting & serialization
        items_with_float_contrib = []
        for rc in headline_route_contribs:
            val = float(rc.point_contribution) if rc.point_contribution is not None else None
            items_with_float_contrib.append((rc, val))

        # Positive drivers (point_contribution > 0), sorted descending
        positive_items = [
            (rc, val) for rc, val in items_with_float_contrib
            if val is not None and val > 0.0
        ]
        positive_items.sort(key=lambda x: x[1], reverse=True)
        top_positive_raw = positive_items[:3]

        top_positive_drivers: List[RouteDriverItem] = [
            RouteDriverItem(
                route_id=rc.route_id,
                origin=rc.origin_code,
                destination=rc.destination_code,
                base_representative_fare=rc.base_representative_fare,
                current_representative_fare=rc.current_representative_fare,
                route_index_value=rc.route_index_value,
                point_contribution=val,
                direction=rc.direction,
                active_weight=rc.active_weight
            )
            for rc, val in top_positive_raw
        ]

        # Negative drivers (point_contribution < 0), sorted ascending (most negative first)
        negative_items = [
            (rc, val) for rc, val in items_with_float_contrib
            if val is not None and val < 0.0
        ]
        negative_items.sort(key=lambda x: x[1])
        top_negative_raw = negative_items[:3]

        top_negative_drivers: List[RouteDriverItem] = [
            RouteDriverItem(
                route_id=rc.route_id,
                origin=rc.origin_code,
                destination=rc.destination_code,
                base_representative_fare=rc.base_representative_fare,
                current_representative_fare=rc.current_representative_fare,
                route_index_value=rc.route_index_value,
                point_contribution=val,
                direction=rc.direction,
                active_weight=rc.active_weight
            )
            for rc, val in top_negative_raw
        ]

        drivers = DriverSummary(
            top_positive_drivers=top_positive_drivers,
            top_negative_drivers=top_negative_drivers
        )

        # 5. Coverage Summary
        horizon_coverage_items: List[HorizonCoverageItem] = [
            HorizonCoverageItem(
                horizon_code=h.horizon_code,
                index_value=h.index_value,
                base_coverage_ratio=h.base_coverage_ratio,
                current_coverage_ratio=h.current_coverage_ratio,
                matched_coverage_ratio=h.matched_coverage_ratio,
                active_routes_count=h.active_routes_count,
                total_basket_routes_count=h.total_basket_routes_count,
                active_weight_sum=h.active_weight_sum
            )
            for h in explanation.horizons
        ]

        headline_matched_coverage = headline_horizon.matched_coverage_ratio if headline_horizon else 0.0

        coverage = CoverageSummary(
            headline_horizon_code=headline_code,
            headline_coverage_ratio=headline_matched_coverage,
            horizon_coverage=horizon_coverage_items
        )

        # 6. Trust Summary
        trust_info = explanation.trust_summary
        trust = DashboardTrustSummary(
            trust_score=trust_info.trust_score,
            trust_status=trust_info.trust_status,
            reason_codes=trust_info.reason_codes,
            is_diagnostic_only=True,
            trust_evaluation_status=audit.trust_audit.trust_evaluation_status
        )

        # 7. Methodology Summary
        methodology = MethodologySummary(
            methodology_version=explanation.methodology_version,
            basket_version=explanation.route_basket_version,
            proxy_weight_version=explanation.proxy_weight_version,
            software_version=explanation.software_version,
            reference_date=explanation.reference_date,
            calculation_date=explanation.calculation_date,
            cabin=scope_info.cabin,
            headline_horizon=headline_code
        )

        # 8. Audit Summary
        repro = audit.reproducibility_audit
        dashboard_audit = DashboardAuditSummary(
            canonical_run_fingerprint=explanation.canonical_run_fingerprint,
            manifest_sha256=repro.manifest_sha256,
            manifest_present=repro.manifest_present,
            raw_input_artifacts_available=repro.raw_input_artifacts_available,
            reproducibility_status=repro.reproducibility_status,
            limitations=audit.limitations
        )

        return IndexDashboardResponse(
            dashboard_scope=dashboard_scope,
            headline=headline,
            drivers=drivers,
            coverage=coverage,
            trust=trust,
            methodology=methodology,
            audit=dashboard_audit
        )
