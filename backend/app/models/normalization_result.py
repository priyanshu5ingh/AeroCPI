import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, ForeignKey, JSON, DateTime
from app.db.base import Base

class NormalizationResult(Base):
    __tablename__ = "normalization_results"

    normalization_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    observation_id = Column(String(36), ForeignKey("observations.observation_id"), nullable=False, unique=True, index=True)
    base_fare = Column(Numeric(10, 2), nullable=False)
    taxes = Column(Numeric(10, 2), nullable=False)
    mandatory_fees = Column(Numeric(10, 2), nullable=False)
    included_fare_components = Column(JSON, nullable=True)
    normalized_total = Column(Numeric(10, 2), nullable=False)
    exclusions = Column(JSON, nullable=True)
    normalization_version = Column(String(30), nullable=False, default="V1_SIMPLE_SUM")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
