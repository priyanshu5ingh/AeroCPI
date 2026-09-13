from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.data_quality import (
    DataQualitySummaryResponse,
    DataQualityRoutesResponse,
    DataQualitySourcesResponse,
)
from app.services.data_quality_service import (
    get_data_quality_summary,
    get_data_quality_routes,
    get_data_quality_sources,
)

router = APIRouter(prefix="/data-quality", tags=["Data Quality Intelligence"])

@router.get("/summary", response_model=DataQualitySummaryResponse)
def get_data_quality_summary_endpoint(
    run_id: Optional[str] = Query(None, description="Optional index run_id filter"),
    db: Session = Depends(get_db)
):
    """
    Returns decomposed quality summary metrics across all observations.
    Does NOT collapse flags into an arbitrary single score.
    """
    return get_data_quality_summary(db, run_id=run_id)

@router.get("/routes", response_model=DataQualityRoutesResponse)
def get_data_quality_routes_endpoint(
    run_id: Optional[str] = Query(None, description="Optional index run_id filter"),
    db: Session = Depends(get_db)
):
    """
    Returns route-level quality metrics.
    """
    return get_data_quality_routes(db, run_id=run_id)

@router.get("/sources", response_model=DataQualitySourcesResponse)
def get_data_quality_sources_endpoint(
    run_id: Optional[str] = Query(None, description="Optional index run_id filter"),
    db: Session = Depends(get_db)
):
    """
    Returns source-level quality and health metrics.
    """
    return get_data_quality_sources(db, run_id=run_id)
