"""AeroCPI Production Operations API Endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.source_health_service import SourceHealthService
from app.services.operational_metrics_service import OperationalMetricsService
from app.services.collection_orchestrator_service import CollectionOrchestratorService
from app.models.collection_orchestration import CollectionRun

router = APIRouter()


@router.get("/source-health")
def get_source_health(db: Session = Depends(get_db)):
    """Returns granular health, taxonomy states, and 24h failure rates across all source adapters."""
    return SourceHealthService.get_source_health_summary(db)


@router.get("/metrics")
def get_operational_metrics(db: Session = Depends(get_db)):
    """Returns live observation growth, route/source breakdowns, and longitudinal panel trajectory counts."""
    return OperationalMetricsService.get_growth_metrics(db)


@router.get("/alerts")
def get_operational_alerts(db: Session = Depends(get_db)):
    """Returns active deterministic operational alerts for collection stagnation, parser issues, and ML blockers."""
    return OperationalMetricsService.evaluate_operational_alerts(db)


@router.get("/runs")
def get_collection_runs(limit: int = 30, db: Session = Depends(get_db)):
    """Returns historical collection sweeps with query counts, latencies, and error summaries."""
    runs = db.query(CollectionRun).order_by(CollectionRun.started_at.desc()).limit(limit).all()
    return [
        {
            "run_id": r.run_id,
            "run_type": r.run_type,
            "status": r.status,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "routes_attempted": r.routes_attempted,
            "sources_attempted": r.sources_attempted,
            "queries_total": r.queries_total,
            "queries_success": r.queries_success,
            "queries_failed": r.queries_failed,
            "observations_saved": r.observations_saved,
            "errors_by_source": r.errors_by_source or {},
        }
        for r in runs
    ]


@router.post("/trigger-sweep")
def trigger_collection_sweep(
    run_type: str = "LONGITUDINAL_PANEL",
    sources: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """Executes a production collection sweep with isolation and audit persistence."""
    return CollectionOrchestratorService.execute_collection_sweep(
        db=db,
        run_type=run_type,
        source_ids=sources
    )
