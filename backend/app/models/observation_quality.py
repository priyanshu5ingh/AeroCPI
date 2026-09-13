import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from app.db.base import Base

class ObservationQuality(Base):
    __tablename__ = "observation_qualities"

    quality_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    observation_id = Column(String(36), nullable=False, index=True)
    completeness_status = Column(String(30), nullable=False, default="COMPLETE")
    timestamp_status = Column(String(30), nullable=False, default="VALID")
    fare_integrity_status = Column(String(30), nullable=False, default="VALID")
    route_mapping_status = Column(String(30), nullable=False, default="MAPPED")
    duplicate_risk = Column(String(30), nullable=False, default="LOW")
    anomaly_flags = Column(JSON, nullable=False, default=list)
    source_health_status = Column(String(30), nullable=False, default="HEALTHY")
    quality_rule_version = Column(String(50), nullable=False, default="QR-2026.1")
    quality_fingerprint = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
