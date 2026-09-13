"""
API Endpoints for Milestone 4C.3: Trust Engine
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import datetime as dt

from app.db.session import get_db
from app.models.trust_evaluation import TrustEvaluation
from app.schemas.trust_evaluation import (
    TrustEvaluationCreateRequest,
    TrustEvaluationResponse,
    DimensionBreakdownSchema,
    EvidenceSummarySchema
)
from app.services.trust_engine_service import TrustEngineService

router = APIRouter()


@router.post("/trust-evaluations", response_model=TrustEvaluationResponse)
def create_trust_evaluation(
    payload: TrustEvaluationCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluates and records a deterministic Measurement Trust Score for a route context.
    """
    record = TrustEngineService.evaluate_and_store_route_trust(
        db=db,
        route_id=payload.route_id,
        travel_date=payload.travel_date,
        horizon=payload.horizon_days,
        cabin=payload.cabin,
        collection_date=payload.collection_date,
        expected_observations=payload.expected_observations,
        expected_sources=payload.expected_sources,
        min_observations_per_source=payload.min_observations_per_source or 5,
        index_run_id=payload.index_run_id
    )

    ev = record.evidence_summary or {}
    return TrustEvaluationResponse(
        trust_evaluation_id=record.trust_evaluation_id,
        trust_engine_version=record.trust_engine_version,
        trust_score=float(record.trust_score),
        trust_status=record.trust_status,
        health_status_from_4c2=record.health_status_from_4c2,
        dimension_scores=record.dimension_breakdown,
        evidence=record.evidence_summary,
        reason_codes=record.reason_codes,
        calculation_fingerprint=record.calculation_fingerprint,
        trust_scope=ev.get("trust_scope"),
        policy_parameters=ev.get("policy_parameters"),
        metadata={
            "route_id": record.route_id,
            "travel_date": record.travel_date.isoformat() if record.travel_date else None,
            "horizon_code": record.horizon_code,
            "cabin": record.cabin,
            "collection_date": record.collection_date.isoformat() if record.collection_date else None,
            "index_run_id": record.index_run_id,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "disclaimer": TrustEngineService.DISCLAIMER,
            "trust_scope": ev.get("trust_scope"),
            "policy_parameters": ev.get("policy_parameters")
        }
    )


@router.get("/trust-evaluations", response_model=List[TrustEvaluationResponse])
def list_trust_evaluations(
    route_id: Optional[str] = Query(None),
    trust_status: Optional[str] = Query(None),
    index_run_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Lists recorded trust evaluations.
    """
    query = db.query(TrustEvaluation)
    if route_id:
        query = query.filter(TrustEvaluation.route_id == route_id)
    if trust_status:
        query = query.filter(TrustEvaluation.trust_status == trust_status)
    if index_run_id:
        query = query.filter(TrustEvaluation.index_run_id == index_run_id)

    records = query.order_by(TrustEvaluation.created_at.desc()).limit(limit).all()

    return [
        TrustEvaluationResponse(
            trust_evaluation_id=r.trust_evaluation_id,
            trust_engine_version=r.trust_engine_version,
            trust_score=float(r.trust_score),
            trust_status=r.trust_status,
            health_status_from_4c2=r.health_status_from_4c2,
            dimension_scores=r.dimension_breakdown,
            evidence=r.evidence_summary,
            reason_codes=r.reason_codes,
            calculation_fingerprint=r.calculation_fingerprint,
            trust_scope=(r.evidence_summary or {}).get("trust_scope"),
            policy_parameters=(r.evidence_summary or {}).get("policy_parameters"),
            metadata={
                "route_id": r.route_id,
                "travel_date": r.travel_date.isoformat() if r.travel_date else None,
                "horizon_code": r.horizon_code,
                "cabin": r.cabin,
                "collection_date": r.collection_date.isoformat() if r.collection_date else None,
                "index_run_id": r.index_run_id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "disclaimer": TrustEngineService.DISCLAIMER,
                "trust_scope": (r.evidence_summary or {}).get("trust_scope"),
                "policy_parameters": (r.evidence_summary or {}).get("policy_parameters")
            }
        )
        for r in records
    ]


@router.get("/trust-evaluations/{evaluation_id}", response_model=TrustEvaluationResponse)
def get_trust_evaluation(
    evaluation_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves a single trust evaluation by ID.
    """
    record = db.query(TrustEvaluation).filter(TrustEvaluation.trust_evaluation_id == evaluation_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Trust evaluation not found")

    ev = record.evidence_summary or {}
    return TrustEvaluationResponse(
        trust_evaluation_id=record.trust_evaluation_id,
        trust_engine_version=record.trust_engine_version,
        trust_score=float(record.trust_score),
        trust_status=record.trust_status,
        health_status_from_4c2=record.health_status_from_4c2,
        dimension_scores=record.dimension_breakdown,
        evidence=record.evidence_summary,
        reason_codes=record.reason_codes,
        calculation_fingerprint=record.calculation_fingerprint,
        trust_scope=ev.get("trust_scope"),
        policy_parameters=ev.get("policy_parameters"),
        metadata={
            "route_id": record.route_id,
            "travel_date": record.travel_date.isoformat() if record.travel_date else None,
            "horizon_code": record.horizon_code,
            "cabin": record.cabin,
            "collection_date": record.collection_date.isoformat() if record.collection_date else None,
            "index_run_id": record.index_run_id,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "disclaimer": TrustEngineService.DISCLAIMER,
            "trust_scope": ev.get("trust_scope"),
            "policy_parameters": ev.get("policy_parameters")
        }
    )


@router.get("/trust-evaluations/{evaluation_id}/breakdown")
def get_trust_evaluation_breakdown(
    evaluation_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves the granular 7-dimension score and evidence breakdown for a trust evaluation.
    """
    record = db.query(TrustEvaluation).filter(TrustEvaluation.trust_evaluation_id == evaluation_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Trust evaluation not found")

    return {
        "trust_evaluation_id": record.trust_evaluation_id,
        "trust_engine_version": record.trust_engine_version,
        "trust_score": float(record.trust_score),
        "trust_status": record.trust_status,
        "dimension_scores": record.dimension_breakdown,
        "evidence": record.evidence_summary,
        "reason_codes": record.reason_codes,
        "disclaimer": TrustEngineService.DISCLAIMER
    }
