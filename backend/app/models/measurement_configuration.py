import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from app.db.base import Base

class MeasurementConfiguration(Base):
    __tablename__ = "measurement_configurations"

    configuration_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    configuration_version = Column(String(50), nullable=False, unique=True, index=True)
    basket_version = Column(String(50), nullable=False, default="DGCA-10-2026.1")
    horizon_set = Column(JSON, nullable=False)
    validation_rule_version = Column(String(50), nullable=False, default="VAL-2026.1")
    outlier_rule_version = Column(String(50), nullable=False, default="IQR-1.5-v1")
    source_policy_version = Column(String(50), nullable=False, default="MULTI-SOURCE-V1")
    aggregation_version = Column(String(50), nullable=False, default="JEVONS-GEOMETRIC-V1")
    publication_threshold_version = Column(String(50), nullable=False, default="PUB-THRESH-V1")
    effective_from = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    effective_to = Column(DateTime(timezone=True), nullable=True)
    configuration_fingerprint = Column(String(64), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
