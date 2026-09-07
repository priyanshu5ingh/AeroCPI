import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from app.db.base import Base

class QualityResult(Base):
    __tablename__ = "quality_results"

    quality_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    observation_id = Column(String(36), ForeignKey("observations.observation_id"), nullable=False, unique=True, index=True)
    eligible = Column(Boolean, nullable=False, default=True)
    duplicate_flag = Column(Boolean, nullable=False, default=False)
    missing_data_flag = Column(Boolean, nullable=False, default=False)
    outlier_status = Column(String(30), nullable=False, default="VALID", index=True) # VALID, OUTLIER_FLAGGED, EXCLUDED, RETAINED_WITH_WARNING
    exclusion_reason = Column(String(255), nullable=True)
    quality_rule_version = Column(String(30), nullable=False, default="V1_BASIC_CHECKS")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
