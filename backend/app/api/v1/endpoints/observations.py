from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.observation import ObservationCreate, ObservationResponse, ObservationFilter
from app.schemas.common import DataStatus
from app.schemas.normalization import NormalizationResultResponse
from app.schemas.quality import QualityResultResponse
from app.services.observation_service import ObservationService
from app.models.normalization_result import NormalizationResult
from app.models.quality_result import QualityResult

router = APIRouter()

def build_observation_response(obs) -> ObservationResponse:
    norm_dto = None
    qual_dto = None
    if hasattr(obs, 'observation_id'):
        # SQLAlchemy object
        db = Session.object_session(obs)
        if db:
            norm = db.query(NormalizationResult).filter(NormalizationResult.observation_id == obs.observation_id).first()
            if norm:
                norm_dto = NormalizationResultResponse.model_validate(norm)
            qual = db.query(QualityResult).filter(QualityResult.observation_id == obs.observation_id).first()
            if qual:
                qual_dto = QualityResultResponse.model_validate(qual)

    resp = ObservationResponse.model_validate(obs)
    resp.normalization_result = norm_dto
    resp.quality_result = qual_dto
    return resp

@router.post("/observations", response_model=ObservationResponse, status_code=status.HTTP_201_CREATED)
def create_observation(
    obs_in: ObservationCreate,
    db: Session = Depends(get_db)
):
    try:
        obs = ObservationService.create_observation(db=db, obs_data=obs_in)
        return build_observation_response(obs)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create observation: {str(e)}")

@router.get("/observations/{observation_id}", response_model=ObservationResponse)
def get_observation_by_id(
    observation_id: str,
    db: Session = Depends(get_db)
):
    obs = ObservationService.get_observation_by_id(db=db, observation_id=observation_id)
    if not obs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Observation '{observation_id}' not found")
    return build_observation_response(obs)

@router.get("/observations", response_model=List[ObservationResponse])
def get_observations(
    route_id: Optional[str] = Query(None, description="Filter by route_id (e.g. DEL-BOM)"),
    carrier_id: Optional[str] = Query(None, description="Filter by carrier_id (e.g. 6E)"),
    booking_horizon_days: Optional[int] = Query(None, description="Filter by lead time horizon (1, 7, 15, 30, 45)"),
    data_status: Optional[DataStatus] = Query(None, description="Filter by data_status (OBSERVED, FROZEN, OFFICIAL, SYNTHETIC, DEMO)"),
    travel_date: Optional[date] = Query(None, description="Filter by travel_date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    filter_params = ObservationFilter(
        route_id=route_id,
        carrier_id=carrier_id,
        booking_horizon_days=booking_horizon_days,
        data_status=data_status,
        travel_date=travel_date,
        limit=limit,
        offset=offset
    )
    observations = ObservationService.get_observations(db=db, filters=filter_params)
    return [build_observation_response(o) for o in observations]
