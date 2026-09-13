from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.publication_readiness import PublicationReadinessResponse
from app.services.publication_readiness_service import evaluate_run_publication_readiness

router = APIRouter(prefix="/index-runs", tags=["Publication Readiness"])

@router.get("/{run_id}/publication-readiness", response_model=PublicationReadinessResponse)
def get_publication_readiness(run_id: str, db: Session = Depends(get_db)):
    """
    Evaluates deterministic publication status for an index run.
    Does NOT alter the calculated index.
    """
    res = evaluate_run_publication_readiness(db, run_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Index run '{run_id}' not found",
        )
    return res
