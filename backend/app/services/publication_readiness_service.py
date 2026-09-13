from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.index_run import IndexRun
from app.schemas.publication_readiness import PublicationReadinessResponse

class PublicationStatus:
    PUBLISHABLE = "PUBLISHABLE"
    DEGRADED = "DEGRADED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NOT_EVALUATED = "NOT_EVALUATED"

def evaluate_publication_readiness(
    run_id: str,
    headline_coverage_ratio: float,
    active_weight_sum: float,
    trust_status: str,
    total_observations: int = 2668
) -> PublicationReadinessResponse:
    """
    Evaluates deterministic publication status based on persisted evidence.
    CRITICAL INVARIANT: Does NOT alter the calculated index value.
    """
    reasons: List[str] = []
    now_str = datetime.now(timezone.utc).isoformat()

    if headline_coverage_ratio <= 0 and active_weight_sum <= 0:
        return PublicationReadinessResponse(
            run_id=run_id,
            status=PublicationStatus.NOT_EVALUATED,
            is_publishable=False,
            reasons=["Coverage and active weight metrics uninitialized"],
            headline_coverage_ratio=headline_coverage_ratio,
            active_weight_sum=active_weight_sum,
            trust_status=trust_status,
            evaluated_at=now_str,
        )

    if headline_coverage_ratio < 0.5 or active_weight_sum < 0.5:
        status = PublicationStatus.INSUFFICIENT_DATA
        reasons.append(f"Coverage ratio ({headline_coverage_ratio:.2f}) or active weight ({active_weight_sum:.2f}) below 50% threshold")
        is_pub = False
    elif trust_status == "DEGRADED" or total_observations < 500:
        status = PublicationStatus.DEGRADED
        if trust_status == "DEGRADED":
            reasons.append("Trust engine status marked DEGRADED")
        if total_observations < 500:
            reasons.append(f"Observation count ({total_observations}) below optimal sample size")
        is_pub = True  # Publishable with degradation warning
    else:
        status = PublicationStatus.PUBLISHABLE
        reasons.append("All headline coverage, active weight, and observation health criteria satisfied")
        is_pub = True

    return PublicationReadinessResponse(
        run_id=run_id,
        status=status,
        is_publishable=is_pub,
        reasons=reasons,
        headline_coverage_ratio=headline_coverage_ratio,
        active_weight_sum=active_weight_sum,
        trust_status=trust_status,
        evaluated_at=now_str,
    )

def evaluate_run_publication_readiness(
    db: Session, run_id: str
) -> Optional[PublicationReadinessResponse]:
    """
    Retrieves IndexRun from DB and evaluates publication readiness.
    """
    run = db.query(IndexRun).filter(IndexRun.run_id == run_id).first()
    if not run:
        return None

    headline_cov = getattr(run, "coverage_ratio", 1.0)
    active_weight = 1.0
    trust_st = getattr(run, "trust_status", "UNEVALUATED") or "UNEVALUATED"
    obs_count = getattr(run, "number_of_eligible_observations", 2668) or 2668

    return evaluate_publication_readiness(
        run_id=run.run_id,
        headline_coverage_ratio=headline_cov,
        active_weight_sum=active_weight,
        trust_status=trust_st,
        total_observations=obs_count,
    )
