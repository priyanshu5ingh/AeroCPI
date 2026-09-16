"""AeroGuide FastAPI Endpoints.
Consumer airfare intelligence, airline registries, NDC capabilities, and verifiable decision traces.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.db.session import get_db
from app.schemas.aeroguide import (
    AeroGuideAnalyzeRequest,
    AeroGuideAnalyzeResponse,
    ForecastingReadinessResponse
)
from app.services.aeroguide_service import (
    analyze_airfare_request,
    get_forecasting_readiness
)
from app.services.longitudinal_service import (
    execute_longitudinal_pilot_collection,
    get_trajectory_detail
)
from app.core.aeroguide_registry import (
    AIRLINE_NDC_REGISTRY,
    SOURCE_CAPABILITY_MATRIX,
    get_airline_ndc_info,
    TIER_1_DGCA_CORE,
    TIER_2_NATIONAL_HIGH_TRAFFIC
)

router = APIRouter(prefix="/aeroguide", tags=["AeroGuide Consumer Intelligence"])

@router.post("/analyze", response_model=AeroGuideAnalyzeResponse)
def analyze_fare(request: AeroGuideAnalyzeRequest, db: Session = Depends(get_db)):
    """Analyzes a domestic consumer airfare request across historical distribution, airline offers, and versioned decision policy."""
    return analyze_airfare_request(request, db)

@router.post("/collect-pilot")
def collect_longitudinal_pilot(db: Session = Depends(get_db)):
    """Executes a controlled longitudinal panel collection pilot across 10 Tier-1 corridors and 14 pinned departure dates."""
    return execute_longitudinal_pilot_collection(db)

@router.get("/trajectories/{route_id}/{travel_date}")
def get_trajectory(route_id: str, travel_date: str, db: Session = Depends(get_db)):
    """Returns chronological search observations, carrier fare progressions, and evaluated 7-day movement targets for a trajectory."""
    return get_trajectory_detail(db, route_id, travel_date)

@router.post("/forecast")
def forecast_fare(request: AeroGuideAnalyzeRequest, db: Session = Depends(get_db)):
    """Returns 7-day movement forecast status. Honestly returns INSUFFICIENT_LONGITUDINAL_HISTORY until panel collection is complete."""
    return {
        "status": "INSUFFICIENT_LONGITUDINAL_HISTORY",
        "model_training_status": "DISABLED",
        "route_id": f"{request.origin.upper()}-{request.destination.upper()}",
        "message": "Longitudinal target pairs (7-day delta) are currently in collection. Per scientific rules, no fake predictions are rendered.",
        "probabilities": None,
        "eligible_for_model": False
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
    if tier:
        return [r for r in routes if r["tier"] == tier]
    return routes

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
    """Returns the source capability matrix and access constraints."""
    return SOURCE_CAPABILITY_MATRIX

@router.get("/source-health")
def get_source_health():
    """Returns operational telemetry for all active and standby collection adapters."""
    return [
        {
            "source_id": s["source_id"],
            "source_name": s["source_name"],
            "health_status": s["health_status"],
            "availability_rate": s["availability_rate"],
            "median_response_time_ms": s["median_response_time_ms"]
        }
        for s in SOURCE_CAPABILITY_MATRIX
    ]

@router.get("/model-status")
def get_model_status():
    """Returns the machine learning model training status and benchmarking metrics."""
    return {
        "model_status": "NOT_TRAINED",
        "training_gate": "LOCKED_AWAITING_LONGITUDINAL_DATA",
        "current_target_pairs": 0,
        "required_target_pairs": 1960,
        "evaluation_strategy": "WALK_FORWARD_TIME_SPLIT",
        "baseline_model": "HISTORICAL_MEDIAN_DIRECTION",
        "synthetic_predictions_allowed": False
    }

@router.get("/collection-status")
def get_collection_status(db: Session = Depends(get_db)):
    """Returns current status of the longitudinal collection panel."""
    return {
        "panel_status": "ACTIVE_SCHEDULED",
        "tier_1_routes_monitored": len(TIER_1_DGCA_CORE),
        "tier_2_routes_monitored": len(TIER_2_NATIONAL_HIGH_TRAFFIC),
        "pinned_dates_per_run": 14,
        "collection_cadence": "DAILY_10_00_IST",
        "rate_limiting": "2.0s_PER_QUERY",
        "error_isolation": "PER_ROUTE_RESILIENT"
    }
