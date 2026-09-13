from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.route_intelligence import RouteIntelligenceResponse
from app.services.route_intelligence_service import get_route_intelligence

router = APIRouter(prefix="/routes", tags=["Route Intelligence"])

@router.get("/{route_id}/intelligence", response_model=RouteIntelligenceResponse)
def get_route_intelligence_by_id(
    route_id: str,
    run_id: Optional[str] = Query(None, description="Optional index run_id filter"),
    db: Session = Depends(get_db)
):
    """
    Returns route corridor intelligence from persisted results.
    Does NOT calculate new index values.
    """
    res = get_route_intelligence(db, route_id=route_id, run_id=run_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route intelligence for '{route_id}' not found",
        )
    return res
