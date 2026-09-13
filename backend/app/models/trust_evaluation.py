import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, DateTime, Numeric, JSON, Integer, Index
from app.db.base import Base


class TrustEvaluation(Base):
    __tablename__ = "trust_evaluations"

    trust_evaluation_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    index_run_id = Column(String(36), nullable=True, index=True)
    route_id = Column(String(15), nullable=True, index=True)
    travel_date = Column(Date, nullable=True, index=True)
    horizon_code = Column(String(20), nullable=True, index=True)
    cabin = Column(String(20), nullable=True, index=True)
    collection_date = Column(Date, nullable=True, index=True)

    trust_engine_version = Column(String(20), nullable=False, default="v1")
    trust_score = Column(Numeric(5, 2), nullable=False)
    trust_status = Column(String(30), nullable=False, index=True)  # HIGH_TRUST, MODERATE_TRUST, DEGRADED_TRUST, LOW_TRUST

    # 7 Dimension Scores (Max 100.0)
    coverage_score = Column(Numeric(5, 2), nullable=False)              # Max 20.0
    agreement_score = Column(Numeric(5, 2), nullable=False)             # Max 20.0
    sample_sufficiency_score = Column(Numeric(5, 2), nullable=False)    # Max 15.0
    validity_score = Column(Numeric(5, 2), nullable=False)              # Max 15.0
    outlier_health_score = Column(Numeric(5, 2), nullable=False)        # Max 10.0
    source_availability_score = Column(Numeric(5, 2), nullable=False)   # Max 10.0
    basket_horizon_stability_score = Column(Numeric(5, 2), nullable=False) # Max 10.0

    # Observation summary
    total_observations = Column(Integer, nullable=False, default=0)
    eligible_observations = Column(Integer, nullable=False, default=0)
    flagged_observations = Column(Integer, nullable=False, default=0)
    rejected_observations = Column(Integer, nullable=False, default=0)
    source_count = Column(Integer, nullable=False, default=0)
    health_status_from_4c2 = Column(String(30), nullable=False, default="INSUFFICIENT")

    # Structured details
    reason_codes = Column(JSON, nullable=False)
    dimension_breakdown = Column(JSON, nullable=True)
    evidence_summary = Column(JSON, nullable=True)
    calculation_fingerprint = Column(String(64), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

__table_args__ = (
    Index("idx_trust_eval_route_date_horizon", "route_id", "travel_date", "horizon_code"),
    Index("idx_trust_eval_fingerprint", "calculation_fingerprint"),
)
TrustEvaluation.__table_args__ = __table_args__
