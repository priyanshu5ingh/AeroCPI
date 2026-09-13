from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.horizon_intelligence import HorizonIntelligenceResponse
from app.services.horizon_intelligence_service import (
    list_horizon_intelligence,
    get_horizon_intelligence_by_code,
)

router = APIRouter(prefix="/horizons", tags=["Horizon Intelligence"])

@router.get("", response_model=List[HorizonIntelligenceResponse])
def get_all_horizons_intelligence(
    run_id: Optional[str] = Query(None, description="Optional index run_id filter"),
    db: Session = Depends(get_db)
):
    """
    Returns intelligence for all 5 forward booking horizons from persisted results.
    """
    return list_horizon_intelligence(db, run_id=run_id)

@router.get("/{horizon_code}", response_model=HorizonIntelligenceResponse)
def get_horizon_intelligence_by_horizon_code(
    horizon_code: str,
    run_id: Optional[str] = Query(None, description="Optional index run_id filter"),
    db: Session = Depends(get_db)
):
    """
    Returns intelligence for a specific horizon code (e.g. T+15, T+1, T+7, T+30, T+45).
    """
    res = get_horizon_intelligence_by_code(db, horizon_code=horizon_code, run_id=run_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Horizon intelligence for '{horizon_code}' not found",
        )
    return res
