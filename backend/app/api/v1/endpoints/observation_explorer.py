from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.observation_explorer import ObservationExplorerResponse
from app.services.observation_explorer_service import get_observation_explorer_records

router = APIRouter(prefix="/observations", tags=["Observation Explorer"])

@router.get("/explorer", response_model=ObservationExplorerResponse)
def explore_observations(
    run_id: Optional[str] = Query(None, description="Filter by index run_id"),
    collection_date: Optional[str] = Query(None, description="Filter by collection_date (YYYY-MM-DD)"),
    route_id: Optional[str] = Query(None, description="Filter by route_id (e.g. DEL-HYD)"),
    origin: Optional[str] = Query(None, description="Filter by origin airport code"),
    destination: Optional[str] = Query(None, description="Filter by destination airport code"),
    horizon: Optional[int] = Query(None, description="Filter by horizon days (1, 7, 15, 30, 45)"),
    source: Optional[str] = Query(None, description="Filter by source adapter name"),
    carrier: Optional[str] = Query(None, description="Filter by airline carrier code"),
    cabin: Optional[str] = Query(None, description="Filter by cabin class"),
    validation_status: Optional[str] = Query(None, description="Filter by validation_status"),
    index_eligibility: Optional[str] = Query(None, description="Filter by index_eligibility"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page (max 500)"),
    db: Session = Depends(get_db)
):
    """
    Returns normalized observation records with attached decomposed quality diagnostics.
    Enforces deterministic ordering and pagination bounds.
    Does NOT recalculate quality.
    """
    return get_observation_explorer_records(
        db=db,
        run_id=run_id,
        collection_date=collection_date,
        route_id=route_id,
        origin=origin,
        destination=destination,
        horizon=horizon,
        source=source,
        carrier=carrier,
        cabin=cabin,
        validation_status=validation_status,
        index_eligibility=index_eligibility,
        page=page,
        page_size=page_size,
    )
