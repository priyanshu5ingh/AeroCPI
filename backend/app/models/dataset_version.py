from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime
from app.db.base import Base

class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    dataset_version_id = Column(String(50), primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    description = Column(String(255), nullable=False)
    source_status = Column(String(30), nullable=False, default="OBSERVED")
    record_count = Column(Integer, nullable=False, default=0)
    fingerprint = Column(String(64), nullable=False)
