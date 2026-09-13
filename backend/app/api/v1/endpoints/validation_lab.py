from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.validation_lab import (
    ValidationBenchmarkSchema,
    ValidationRunSchema,
    ValidationMetricSchema,
)
from app.services.validation_lab_service import (
    list_validation_benchmarks,
    get_validation_run_by_index_run,
)

router = APIRouter(prefix="/validation-lab", tags=["Validation Lab"])

@router.get("/benchmarks", response_model=List[ValidationBenchmarkSchema])
def get_validation_benchmarks(db: Session = Depends(get_db)):
    """
    Returns list of registered validation benchmarks.
    """
    return list_validation_benchmarks(db)

@router.get("/runs/{run_id}", response_model=ValidationRunSchema)
def get_validation_run(run_id: str, db: Session = Depends(get_db)):
    """
    Returns validation run metrics for a given index run.
    Gracefully returns DISABLED_NO_BENCHMARK_DATA if benchmark data is absent.
    """
    return get_validation_run_by_index_run(db, run_id)

@router.get("/metrics", response_model=Optional[ValidationMetricSchema])
def get_validation_metrics(run_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Returns validation metrics for a given index run if executed.
    Gracefully returns None if absent or not executed.
    """
    if not run_id:
        return None
    val_run = get_validation_run_by_index_run(db, run_id)
    return val_run.metrics
