from datetime import date as dt_date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.index_run import IndexRun
from app.models.route_index_result import RouteIndexResult
from app.models.horizon_index_result import HorizonIndexResult
from app.models.observation import Observation
from app.schemas.index_run import IndexRunCreate, IndexRunResponse
from app.schemas.route_index_result import RouteIndexResultResponse
from app.schemas.observation import ObservationResponse
from app.schemas.quality_summary import QualitySummaryResponse
from app.schemas.statistical_index import (
    StatisticalIndexRunRequest,
    StatisticalIndexRunResponse,
    HorizonIndexResponse,
    TemporalAggregationResponse,
    InflationRateResponse
)
from app.services.index_engine_service import IndexEngineService
from app.services.statistical_index_service import StatisticalIndexEngineService
from app.services.index_explanation_service import IndexExplanationService
from app.services.index_audit_service import IndexAuditService
from app.services.index_dashboard_service import IndexDashboardService
from app.schemas.index_explanation import IndexExplanationResponse
from app.schemas.index_audit import IndexAuditResponse
from app.schemas.index_dashboard import IndexDashboardResponse
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

@router.get("/index-runs/{run_id}/trust")
def get_index_run_trust(
    run_id: str,
    db: Session = Depends(get_db)
):
    from app.models.trust_evaluation import TrustEvaluation
    run = db.query(IndexRun).filter(IndexRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Index run '{run_id}' not found")
    
    trust_evals = db.query(TrustEvaluation).filter(TrustEvaluation.index_run_id == run_id).all()
    return {
        "index_run_id": run_id,
        "trust_evaluations_count": len(trust_evals),
        "evaluations": [
            {
                "trust_evaluation_id": t.trust_evaluation_id,
                "route_id": t.route_id,
                "horizon_code": t.horizon_code,
                "trust_score": float(t.trust_score),
                "trust_status": t.trust_status,
                "reason_codes": t.reason_codes,
                "dimension_scores": t.dimension_breakdown,
                "calculation_fingerprint": t.calculation_fingerprint
            }
            for t in trust_evals
        ]
    }


# =============================================================================
# MILESTONE 4D: STATISTICAL INDEX ENGINE V1 ENDPOINTS
# =============================================================================

@router.post("/index-runs/calculate-v1", response_model=StatisticalIndexRunResponse, status_code=status.HTTP_201_CREATED)
def calculate_statistical_index_run(
    payload: StatisticalIndexRunRequest,
    db: Session = Depends(get_db)
):
    try:
        index_run, horizon_records, _ = StatisticalIndexEngineService.execute_statistical_index_run(
            db=db,
            reference_date=payload.reference_date,
            calculation_date=payload.calculation_date,
            cabin=payload.cabin,
            basket_version=payload.basket_version,
            trust_evaluation_id=payload.trust_evaluation_id
        )
        return StatisticalIndexRunResponse(
            run_id=index_run.run_id,
            run_timestamp=index_run.run_timestamp,
            reference_date=index_run.reference_period,
            calculation_date=index_run.comparison_period,
            methodology_version=index_run.methodology_version,
            route_basket_version=index_run.route_basket_version,
            proxy_weight_version=index_run.proxy_weight_version,
            canonical_run_fingerprint=index_run.canonical_run_fingerprint,
            headline_index_value=index_run.index_value,
            coverage_ratio=index_run.coverage_ratio,
            trust_evaluation_id=index_run.trust_evaluation_id,
            horizons=[HorizonIndexResponse.model_validate(h) for h in horizon_records],
            calculation_manifest=index_run.calculation_manifest
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Statistical index calculation failed: {str(e)}")


@router.get("/index-runs/{run_id}/horizons", response_model=List[HorizonIndexResponse])
def get_index_run_horizons(
    run_id: str,
    db: Session = Depends(get_db)
):
    run = db.query(IndexRun).filter(IndexRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Index run '{run_id}' not found")
    horizons = db.query(HorizonIndexResult).filter(HorizonIndexResult.run_id == run_id).all()
    return horizons


@router.get("/index-runs/{run_id}/manifest")
def get_index_run_manifest(
    run_id: str,
    db: Session = Depends(get_db)
):
    run = db.query(IndexRun).filter(IndexRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Index run '{run_id}' not found")
    return {
        "run_id": run.run_id,
        "canonical_run_fingerprint": run.canonical_run_fingerprint,
        "calculation_manifest": run.calculation_manifest
    }


@router.get("/indices/temporal-aggregate", response_model=TemporalAggregationResponse)
def get_temporal_aggregation(
    frequency: str = Query("WEEKLY", description="WEEKLY or MONTHLY"),
    start_date: dt_date = Query(..., description="Start date YYYY-MM-DD"),
    end_date: dt_date = Query(..., description="End date YYYY-MM-DD"),
    horizon_code: str = Query("T+15", description="Horizon code e.g. T+15"),
    db: Session = Depends(get_db)
):
    if end_date < start_date:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="end_date must be >= start_date")

    horizon_clean = horizon_code.replace(" ", "+")

    runs = db.query(IndexRun).filter(
        IndexRun.comparison_period >= start_date.isoformat(),
        IndexRun.comparison_period <= end_date.isoformat(),
        IndexRun.methodology_version == StatisticalIndexEngineService.METHODOLOGY_VERSION
    ).order_by(IndexRun.comparison_period.asc()).all()

    daily_values = []
    for r in runs:
        h_rec = db.query(HorizonIndexResult).filter(
            HorizonIndexResult.run_id == r.run_id,
            HorizonIndexResult.horizon_code == horizon_clean
        ).first()
        if h_rec and h_rec.index_value is not None:
            daily_values.append(h_rec.index_value)

    days_expected = (end_date - start_date).days + 1
    agg = StatisticalIndexEngineService.compute_temporal_aggregation(
        valid_daily_indices=daily_values,
        days_expected=days_expected
    )

    stat = "AVAILABLE" if agg["index_value"] is not None else "NOT_AVAILABLE"
    return TemporalAggregationResponse(
        frequency=frequency.upper(),
        horizon_code=horizon_clean,
        start_date=start_date,
        end_date=end_date,
        index_value=agg["index_value"],
        days_expected=agg["days_expected"],
        days_available=agg["days_available"],
        temporal_coverage_ratio=agg["temporal_coverage_ratio"],
        status=stat
    )


@router.get("/indices/inflation-rate", response_model=InflationRateResponse)
def get_inflation_rate(
    rate_type: str = Query("MOM", description="MOM or YOY"),
    current_date: dt_date = Query(..., description="Current date YYYY-MM-DD"),
    comparison_date: dt_date = Query(..., description="Comparison date YYYY-MM-DD"),
    horizon_code: str = Query("T+15", description="Horizon code e.g. T+15"),
    db: Session = Depends(get_db)
):
    horizon_clean = horizon_code.replace(" ", "+")

    cur_run = db.query(IndexRun).filter(
        IndexRun.comparison_period == current_date.isoformat(),
        IndexRun.methodology_version == StatisticalIndexEngineService.METHODOLOGY_VERSION
    ).order_by(IndexRun.run_timestamp.desc()).first()

    cur_val = None
    if cur_run:
        h_cur = db.query(HorizonIndexResult).filter(
            HorizonIndexResult.run_id == cur_run.run_id,
            HorizonIndexResult.horizon_code == horizon_clean
        ).first()
        if h_cur:
            cur_val = h_cur.index_value

    prev_run = db.query(IndexRun).filter(
        IndexRun.comparison_period == comparison_date.isoformat(),
        IndexRun.methodology_version == StatisticalIndexEngineService.METHODOLOGY_VERSION
    ).order_by(IndexRun.run_timestamp.desc()).first()

    prev_val = None
    if prev_run:
        h_prev = db.query(HorizonIndexResult).filter(
            HorizonIndexResult.run_id == prev_run.run_id,
            HorizonIndexResult.horizon_code == horizon_clean
        ).first()
        if h_prev:
            prev_val = h_prev.index_value

    inf_result = StatisticalIndexEngineService.compute_inflation_rate(
        current_index=cur_val,
        previous_index=prev_val
    )

    return InflationRateResponse(
        rate_type=rate_type.upper(),
        horizon_code=horizon_clean,
        current_date=current_date,
        comparison_date=comparison_date,
        current_index=cur_val,
        previous_index=prev_val,
        inflation_rate_percent=inf_result["inflation_rate_percent"],
        status=inf_result["status"]
    )


@router.get("/indices/series")
def get_indices_series(
    horizon_code: str = Query("T+15", description="Horizon code e.g. T+15"),
    start_date: Optional[dt_date] = Query(None, description="Start date filter"),
    end_date: Optional[dt_date] = Query(None, description="End date filter"),
    db: Session = Depends(get_db)
):
    horizon_clean = horizon_code.replace(" ", "+")

    query = db.query(IndexRun, HorizonIndexResult).join(
        HorizonIndexResult, IndexRun.run_id == HorizonIndexResult.run_id
    ).filter(
        HorizonIndexResult.horizon_code == horizon_clean,
        IndexRun.methodology_version == StatisticalIndexEngineService.METHODOLOGY_VERSION
    )

    if start_date:
        query = query.filter(IndexRun.comparison_period >= start_date.isoformat())
    if end_date:
        query = query.filter(IndexRun.comparison_period <= end_date.isoformat())

    results = query.order_by(IndexRun.comparison_period.asc()).all()

    return [
        {
            "run_id": run.run_id,
            "date": run.comparison_period,
            "horizon_code": h.horizon_code,
            "index_name": h.index_name,
            "index_value": h.index_value,
            "matched_sample_index_value": h.matched_sample_index_value,
            "coverage_ratio": h.matched_coverage_ratio,
            "is_headline": h.is_headline
        }
        for run, h in results
    ]


@router.get("/index-runs/{run_id}/explanation", response_model=IndexExplanationResponse)
def get_index_run_explanation(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Milestone 5A: Returns complete mathematically traceable explanation for a completed index run.
    """
    try:
        explanation = IndexExplanationService.explain_index_run(db=db, run_id=run_id)
        return explanation
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to generate index run explanation: {str(e)}")


@router.get("/index-runs/{run_id}/audit", response_model=IndexAuditResponse)
def get_index_run_audit(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Milestone 5B: Returns complete machine-readable measurement audit & reproducibility record for a completed index run.
    """
    try:
        audit = IndexAuditService.audit_index_run(db=db, run_id=run_id)
        return audit
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to generate index run audit: {str(e)}")


@router.get("/index-runs/{run_id}/dashboard", response_model=IndexDashboardResponse)
def get_index_run_dashboard(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Milestone 5C: Returns executive presentation dashboard payload for a completed index run.
    """
    try:
        dashboard = IndexDashboardService.get_dashboard(db=db, run_id=run_id)
        return dashboard
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to generate index run dashboard: {str(e)}")




