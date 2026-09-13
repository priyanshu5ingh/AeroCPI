from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.measurement_trace import MeasurementTraceResponse
from app.services.measurement_trace_service import get_measurement_trace

router = APIRouter(prefix="/index-runs", tags=["Measurement Trace Engine"])

@router.get("/{run_id}/trace", response_model=MeasurementTraceResponse)
def get_index_run_measurement_trace(run_id: str, db: Session = Depends(get_db)):
    """
    Returns the complete 9-stage structured measurement trace provenance graph (9 nodes / 8 edges) for an index run:
    IndexRun -> Configuration -> Horizons -> Routes -> Representative Fares -> Observations -> Quality -> Explanation -> SHA-256 Fingerprint.
    """
    res = get_measurement_trace(db, run_id=run_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Measurement trace for index run '{run_id}' not found",
        )
    return res
