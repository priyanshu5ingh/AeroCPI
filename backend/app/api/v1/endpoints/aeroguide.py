"""AeroGuide FastAPI Endpoints.
Consumer airfare intelligence, multi-source data fabric, national route universe,
11-node decision traces, and grounded explanations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional

from app.db.session import get_db
from app.schemas.aeroguide import (
    AeroGuideAnalyzeRequest,
    AeroGuideAnalyzeResponse,
    ForecastingReadinessResponse,
    RouteSourceAgreementResponse
)
from app.services.aeroguide_service import (
    analyze_airfare_request,
    get_forecasting_readiness,
    get_route_source_agreement,
    get_all_source_agreements
)
from app.services.longitudinal_service import (
    execute_longitudinal_pilot_collection,
    get_trajectory_detail
)
from app.services.collection_orchestrator_service import CollectionOrchestratorService
from app.services.forecasting_engine_service import ForecastingEngineService
from app.services.market_state_service import MarketStateService
from app.services.source_adapters.registry import MultiSourceRegistry
from app.services.source_adapters.base import SourceStatus
from app.models.collection_orchestration import CollectionRun, CollectionAttempt
from app.models.observation import Observation
from app.core.aeroguide_registry import (
    AIRLINE_NDC_REGISTRY,
    SOURCE_CAPABILITY_MATRIX,
    get_airline_ndc_info,
    TIER_1_DGCA_CORE,
    TIER_2_NATIONAL_HIGH_TRAFFIC,
    TIER_3_REGIONAL_CONNECTIVITY,
    TIER_4_DYNAMIC_DISCOVERY
)

router = APIRouter(prefix="/aeroguide", tags=["AeroGuide Consumer Intelligence"])

@router.get("/source-agreement/{route_id}/{travel_date}", response_model=RouteSourceAgreementResponse)
def get_source_agreement(
    route_id: str,
    travel_date: str,
    cabin: str = "ECONOMY",
    db: Session = Depends(get_db)
):
    """Returns multi-source intelligence, descriptive distributions, and pairwise concordance metrics for a route/date."""
    return get_route_source_agreement(db, route_id, travel_date, cabin=cabin)

@router.get("/source-agreement", response_model=List[RouteSourceAgreementResponse])
def get_all_source_agreements_summary(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Returns cross-source agreement evaluations for all trajectories with multi-source coverage."""
    return get_all_source_agreements(db, limit=limit)

@router.post("/analyze", response_model=AeroGuideAnalyzeResponse)
def analyze_fare(request: AeroGuideAnalyzeRequest, db: Session = Depends(get_db)):
    """Analyzes a domestic consumer airfare request across historical distribution, airline offers, and versioned decision policy."""
    return analyze_airfare_request(request, db)

@router.post("/collect-pilot")
def collect_longitudinal_pilot(db: Session = Depends(get_db)):
    """Executes a controlled longitudinal panel collection pilot across 10 Tier-1 corridors and 14 pinned departure dates."""
    return execute_longitudinal_pilot_collection(db)

@router.post("/collect-sweep")
def execute_collection_sweep(
    run_type: str = "LONGITUDINAL_PANEL",
    sources: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """Executes an orchestrated multi-source collection sweep with failure isolation and run logging."""
    return CollectionOrchestratorService.execute_collection_sweep(
        db=db,
        run_type=run_type,
        source_ids=sources
    )

@router.get("/collection-runs")
def get_collection_runs(limit: int = 20, db: Session = Depends(get_db)):
    """Returns historical collection runs and query audit statistics."""
    runs = db.query(CollectionRun).order_by(CollectionRun.started_at.desc()).limit(limit).all()
    return [
        {
            "run_id": r.run_id,
            "run_type": r.run_type,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "routes_attempted": r.routes_attempted,
            "sources_attempted": r.sources_attempted,
            "queries_total": r.queries_total,
            "queries_success": r.queries_success,
            "queries_failed": r.queries_failed,
            "observations_saved": r.observations_saved,
            "status": r.status
        }
        for r in runs
    ]

@router.get("/collection-attempts/{run_id}")
def get_collection_attempts(run_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """Returns detailed per-query attempts for a specific collection run."""
    attempts = db.query(CollectionAttempt).filter(CollectionAttempt.run_id == run_id).limit(limit).all()
    return [
        {
            "attempt_id": a.attempt_id,
            "source_id": a.source_id,
            "route_id": a.route_id,
            "travel_date": a.travel_date.isoformat(),
            "status": a.status,
            "latency_ms": a.latency_ms,
            "observations_count": a.observations_count,
            "error_detail": a.error_detail
        }
        for a in attempts
    ]

@router.get("/trajectories/{route_id}/{travel_date}")
def get_trajectory(route_id: str, travel_date: str, db: Session = Depends(get_db)):
    """Returns chronological search observations, carrier fare progressions, and evaluated 7-day movement targets for a trajectory."""
    return get_trajectory_detail(db, route_id, travel_date)

@router.post("/forecast")
def forecast_fare(request: AeroGuideAnalyzeRequest, db: Session = Depends(get_db)):
    """Returns 7-day movement forecast status. Honestly returns INSUFFICIENT_LONGITUDINAL_HISTORY until panel collection is complete."""
    status_info = ForecastingEngineService.get_model_status(db)
    readiness = get_forecasting_readiness(db)
    return {
        "status": readiness.dataset_classification,
        "model_status": status_info["model_status"],
        "model_training_status": "ENABLED" if status_info["can_train_live"] else "DISABLED",
        "route_id": f"{request.origin.upper()}-{request.destination.upper()}",
        "message": status_info["reason"],
        "probabilities": None,
        "eligible_for_model": status_info["can_train_live"]
    }

@router.get("/readiness", response_model=ForecastingReadinessResponse)
def get_readiness(db: Session = Depends(get_db)):
    """Evaluates empirical dataset and machine learning model readiness."""
    return get_forecasting_readiness(db)

@router.get("/routes")
def get_route_universe(tier: Optional[str] = None):
    """Returns the national route universe categorized across 4 tiers."""
    routes = []
    for o, d in TIER_1_DGCA_CORE:
        routes.append({
            "route_id": f"{o}-{d}",
            "origin": o,
            "destination": d,
            "city_pair": f"{o} - {d}",
            "tier": "TIER_1_DGCA_CORE",
            "is_cpi_basket_member": True,
            "description": "Top 10 DGCA Sovereign Basket Corridor"
        })
    for o, d in TIER_2_NATIONAL_HIGH_TRAFFIC:
        routes.append({
            "route_id": f"{o}-{d}",
            "origin": o,
            "destination": d,
            "city_pair": f"{o} - {d}",
            "tier": "TIER_2_NATIONAL_HIGH_TRAFFIC",
            "is_cpi_basket_member": False,
            "description": "High-Density National Market Route"
        })
    for o, d in TIER_3_REGIONAL_CONNECTIVITY:
        routes.append({
            "route_id": f"{o}-{d}",
            "origin": o,
            "destination": d,
            "city_pair": f"{o} - {d}",
            "tier": "TIER_3_REGIONAL_CONNECTIVITY",
            "is_cpi_basket_member": False,
            "description": "Regional & UDAN Connectivity Corridor"
        })
    for o, d in TIER_4_DYNAMIC_DISCOVERY:
        routes.append({
            "route_id": f"{o}-{d}",
            "origin": o,
            "destination": d,
            "city_pair": f"{o} - {d}",
            "tier": "TIER_4_DYNAMIC_DISCOVERY",
            "is_cpi_basket_member": False,
            "description": "Dynamic Market Discovery Route"
        })
    if tier:
        return [r for r in routes if r["tier"] == tier]
    return routes

@router.get("/routes/{route_id}/airlines")
def get_route_airlines(route_id: str, db: Session = Depends(get_db)):
    """Returns carriers observed on a specific corridor."""
    obs = db.query(Observation.carrier_id, Observation.airline).filter(
        Observation.route_id == route_id.upper()
    ).distinct().all()
    return [{"carrier_code": o[0], "airline_name": o[1] or o[0]} for o in obs if o[0]]

@router.get("/route-coverage")
def get_route_coverage(db: Session = Depends(get_db)):
    """Returns comprehensive multi-source coverage and empirical statistics across all 33 routes in 4 tiers."""
    all_routes = get_route_universe()
    registry = MultiSourceRegistry.get_instance()
    configured_sources = [s.source_id for s in registry.list_adapters()]
    accessible_sources = [
        s.source_id for s in registry.list_adapters()
        if s.get_status() in [SourceStatus.ACCESSIBLE, SourceStatus.COLLECTED, SourceStatus.OBSERVED]
    ]

    obs_summary = db.query(
        Observation.route_id,
        Observation.source_id,
        Observation.carrier_id,
        func.count(Observation.observation_id),
        func.max(Observation.collected_at)
    ).group_by(Observation.route_id, Observation.source_id, Observation.carrier_id).all()

    route_map: Dict[str, Dict[str, Any]] = {}
    for r in all_routes:
        rid = r["route_id"]
        route_map[rid] = {
            "route_id": rid,
            "origin": r["origin"],
            "destination": r["destination"],
            "tier": r["tier"],
            "description": r["description"],
            "is_cpi_basket_member": r["is_cpi_basket_member"],
            "airlines_observed": set(),
            "sources_configured": configured_sources,
            "sources_accessible": accessible_sources,
            "sources_collected": set(),
            "observations_count": 0,
            "last_collection": None,
            "coverage_status": "SCHEDULED_PENDING"
        }

    for rid, sid, cid, cnt, max_ts in obs_summary:
        if rid in route_map:
            if cid:
                route_map[rid]["airlines_observed"].add(cid)
            if sid:
                route_map[rid]["sources_collected"].add(sid)
            route_map[rid]["observations_count"] += cnt
            if max_ts:
                cur_max = route_map[rid]["last_collection"]
                if not cur_max or max_ts > cur_max:
                    route_map[rid]["last_collection"] = max_ts

    result = []
    for rid, data in route_map.items():
        data["airlines_observed"] = sorted(list(data["airlines_observed"]))
        data["sources_collected"] = sorted(list(data["sources_collected"]))
        if data["observations_count"] > 0:
            data["coverage_status"] = "ACTIVE_OBSERVED"
        elif data["tier"] == "TIER_1_DGCA_CORE":
            data["coverage_status"] = "PRIORITY_CORE_TRACKING"
        else:
            data["coverage_status"] = "SCHEDULED_PENDING"
        data["last_collection"] = data["last_collection"].isoformat() if data["last_collection"] else None
        result.append(data)

    return result

@router.get("/airlines")
def get_airlines():
    """Returns all registered scheduled domestic carriers and their official NDC/API capabilities."""
    return AIRLINE_NDC_REGISTRY

@router.get("/airlines/{carrier_code}")
def get_airline_detail(carrier_code: str):
    """Returns detailed NDC and API capability for a specific airline."""
    info = get_airline_ndc_info(carrier_code.upper())
    return info

@router.get("/sources")
def get_sources():
    """Returns all registered sources with live operational status and capabilities."""
    registry = MultiSourceRegistry.get_instance()
    return [t.model_dump() for t in registry.get_all_telemetry()]

@router.get("/source-health")
def get_source_health():
    """Returns operational telemetry for all active and standby collection adapters."""
    registry = MultiSourceRegistry.get_instance()
    return registry.get_health_summary()

@router.get("/model-status")
def get_model_status(db: Session = Depends(get_db)):
    """Returns the machine learning model training status and empirical gating rules."""
    return ForecastingEngineService.get_model_status(db)

@router.get("/model-evaluation")
def get_model_evaluation():
    """Returns walk-forward benchmark metrics on test fixtures (Research Preview)."""
    return ForecastingEngineService.evaluate_walk_forward()

@router.get("/market-state")
def get_market_state(run_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns national airfare market state from completed AeroCPI measurement runs."""
    return MarketStateService.get_national_market_state(db, run_id=run_id)

@router.get("/what-changed")
def get_what_changed(run_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns 'What Changed?' attribution bridge linking national movement to corridor drivers."""
    return MarketStateService.get_what_changed_summary(db, run_id=run_id)

@router.get("/collection-status")
def get_collection_status(db: Session = Depends(get_db)):
    """Returns current status of the longitudinal collection panel."""
    return {
        "panel_status": "ACTIVE_SCHEDULED",
        "tier_1_routes_monitored": len(TIER_1_DGCA_CORE),
        "tier_2_routes_monitored": len(TIER_2_NATIONAL_HIGH_TRAFFIC),
        "tier_3_routes_monitored": len(TIER_3_REGIONAL_CONNECTIVITY),
        "tier_4_routes_monitored": len(TIER_4_DYNAMIC_DISCOVERY),
        "pinned_dates_per_run": 14,
        "collection_cadence": "DAILY_10_00_IST",
        "rate_limiting": "2.0s_PER_QUERY",
        "error_isolation": "PER_ROUTE_RESILIENT"
    }
