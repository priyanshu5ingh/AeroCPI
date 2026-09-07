from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.index_run import IndexRun
from app.models.route_index_result import RouteIndexResult
from app.models.observation import Observation
from app.schemas.index_run import IndexRunCreate, IndexRunResponse
from app.schemas.route_index_result import RouteIndexResultResponse
from app.schemas.observation import ObservationResponse
from app.schemas.quality_summary import QualitySummaryResponse
from app.services.index_engine_service import IndexEngineService
from app.api.v1.endpoints.observations import build_observation_response

router = APIRouter()

@router.post("/index-runs", response_model=IndexRunResponse, status_code=status.HTTP_201_CREATED)
def create_index_run(
    run_in: IndexRunCreate,
    db: Session = Depends(get_db)
):
    try:
        index_run, _ = IndexEngineService.execute_index_run(
            db=db,
            reference_period=run_in.reference_period,
            comparison_period=run_in.comparison_period,
            frequency=run_in.frequency.value,
            dataset_version_id=run_in.dataset_version_id,
            proxy_weight_version=run_in.proxy_weight_version,
            route_basket_version=run_in.route_basket_version
        )
        return index_run
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to execute index run: {str(e)}")

@router.get("/index-runs", response_model=List[IndexRunResponse])
def list_index_runs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    runs = db.query(IndexRun).order_by(IndexRun.run_timestamp.desc()).offset(offset).limit(limit).all()
    return runs

@router.get("/index-runs/{run_id}", response_model=IndexRunResponse)
def get_index_run(
    run_id: str,
    db: Session = Depends(get_db)
):
    run = db.query(IndexRun).filter(IndexRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Index run '{run_id}' not found")
    return run

@router.get("/index-runs/{run_id}/routes", response_model=List[RouteIndexResultResponse])
def get_index_run_routes(
    run_id: str,
    db: Session = Depends(get_db)
):
    run = db.query(IndexRun).filter(IndexRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Index run '{run_id}' not found")
    
    routes = db.query(RouteIndexResult).filter(RouteIndexResult.run_id == run_id).all()
    return routes

@router.get("/index-runs/{run_id}/observations", response_model=List[ObservationResponse])
def get_index_run_observations(
    run_id: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    run = db.query(IndexRun).filter(IndexRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Index run '{run_id}' not found")
    
    observations = db.query(Observation).order_by(Observation.observed_at.desc()).offset(offset).limit(limit).all()
    return [build_observation_response(o) for o in observations]

@router.get("/index-runs/{run_id}/quality-summary", response_model=QualitySummaryResponse)
def get_index_run_quality_summary(
    run_id: str,
    db: Session = Depends(get_db)
):
    run = db.query(IndexRun).filter(IndexRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Index run '{run_id}' not found")
    
    return QualitySummaryResponse(
        total_observations=run.number_of_observations,
        eligible_observations=run.number_of_eligible_observations,
        excluded_observations=run.number_of_excluded_observations,
        valid_observations=run.valid_count,
        outlier_flagged_observations=run.number_of_outlier_flagged,
        retained_with_warning_observations=run.number_of_retained_warning,
        duplicate_observations=run.number_of_duplicates,
        missing_incomplete_observations=0,
        coverage_ratio=run.coverage_ratio,
        expected_route_horizon_pairs=run.expected_route_horizon_pairs,
        calculated_route_horizon_pairs=run.calculated_route_horizon_pairs,
        unavailable_route_horizon_pairs=run.unavailable_route_horizon_pairs
    )
