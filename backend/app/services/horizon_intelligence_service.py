from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.index_run import IndexRun
from app.models.horizon_index_result import HorizonIndexResult
from app.schemas.horizon_intelligence import HorizonIntelligenceResponse
from app.schemas.index_dashboard import RouteDriverItem
from app.services.index_dashboard_service import IndexDashboardService
from app.services.index_explanation_service import IndexExplanationService

def list_horizon_intelligence(
    db: Session, run_id: Optional[str] = None
) -> List[HorizonIntelligenceResponse]:
    """
    Returns intelligence for all 5 forward booking horizons from persisted database records.
    Populates genuine route contributions for each horizon from persisted calculations.
    """
    if not run_id:
        run = db.query(IndexRun).order_by(IndexRun.run_timestamp.desc()).first()
        if not run:
            return []
        run_id = run.run_id

    dash = IndexDashboardService.get_dashboard(db, run_id)
    if not dash:
        return []

    # Get explanation to extract route-level contributions across all horizons
    try:
        explanation = IndexExplanationService.explain_index_run(db, run_id)
    except Exception:
        explanation = None

    horizons_res = db.query(HorizonIndexResult).filter(HorizonIndexResult.run_id == run_id).all()
    if not horizons_res:
        # Fallback from dash coverage
        result = []
        for cov in dash.coverage.horizon_coverage:
            h_days = int(cov.horizon_code.replace("T+", "")) if "T+" in cov.horizon_code else 15
            is_hl = cov.horizon_code == dash.coverage.headline_horizon_code
            result.append(
                HorizonIntelligenceResponse(
                    horizon_code=cov.horizon_code,
                    horizon_days=h_days,
                    index_value=cov.index_value or 100.0,
                    base_coverage_ratio=cov.base_coverage_ratio,
                    current_coverage_ratio=cov.current_coverage_ratio,
                    matched_coverage_ratio=cov.matched_coverage_ratio,
                    active_routes_count=cov.active_routes_count,
                    total_basket_routes_count=cov.total_basket_routes_count,
                    active_weight_sum=cov.active_weight_sum,
                    is_headline=is_hl,
                    top_positive_routes=dash.drivers.top_positive_drivers if is_hl else [],
                    top_negative_routes=dash.drivers.top_negative_drivers if is_hl else [],
                )
            )
        return result

    result = []
    for hr in horizons_res:
        is_hl = hr.horizon_code == dash.coverage.headline_horizon_code
        top_pos: List[RouteDriverItem] = []
        top_neg: List[RouteDriverItem] = []

        if explanation:
            h_exp = next((h for h in explanation.horizons if h.horizon_code == hr.horizon_code), None)
            if h_exp:
                pos = [
                    rc for rc in h_exp.route_contributions
                    if rc.point_contribution is not None and float(rc.point_contribution) > 0
                ]
                pos.sort(key=lambda x: float(x.point_contribution), reverse=True)
                top_pos = [
                    RouteDriverItem(
                        route_id=rc.route_id,
                        origin=rc.origin_code,
                        destination=rc.destination_code,
                        base_representative_fare=rc.base_representative_fare,
                        current_representative_fare=rc.current_representative_fare,
                        route_index_value=rc.route_index_value,
                        point_contribution=float(rc.point_contribution),
                        direction=rc.direction,
                        active_weight=rc.active_weight,
                    )
                    for rc in pos[:3]
                ]

                neg = [
                    rc for rc in h_exp.route_contributions
                    if rc.point_contribution is not None and float(rc.point_contribution) < 0
                ]
                neg.sort(key=lambda x: float(x.point_contribution))
                top_neg = [
                    RouteDriverItem(
                        route_id=rc.route_id,
                        origin=rc.origin_code,
                        destination=rc.destination_code,
                        base_representative_fare=rc.base_representative_fare,
                        current_representative_fare=rc.current_representative_fare,
                        route_index_value=rc.route_index_value,
                        point_contribution=float(rc.point_contribution),
                        direction=rc.direction,
                        active_weight=rc.active_weight,
                    )
                    for rc in neg[:3]
                ]

        if not top_pos and is_hl:
            top_pos = dash.drivers.top_positive_drivers
        if not top_neg and is_hl:
            top_neg = dash.drivers.top_negative_drivers

        result.append(
            HorizonIntelligenceResponse(
                horizon_code=hr.horizon_code,
                horizon_days=hr.horizon_days,
                index_value=hr.index_value,
                base_coverage_ratio=hr.base_coverage_ratio,
                current_coverage_ratio=hr.current_coverage_ratio,
                matched_coverage_ratio=hr.matched_coverage_ratio,
                active_routes_count=hr.active_routes_count,
                total_basket_routes_count=hr.total_basket_routes_count,
                active_weight_sum=hr.active_weight_sum,
                is_headline=hr.is_headline,
                top_positive_routes=top_pos,
                top_negative_routes=top_neg,
            )
        )
    return result

def get_horizon_intelligence_by_code(
    db: Session, horizon_code: str, run_id: Optional[str] = None
) -> Optional[HorizonIntelligenceResponse]:
    horizons = list_horizon_intelligence(db, run_id)
    return next((h for h in horizons if h.horizon_code == horizon_code), None)
