import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, DateTime, Integer, Index, JSON
from app.db.base import Base

class CollectionEvent(Base):
    __tablename__ = "collection_events"

    event_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(30), nullable=False, index=True, default="SRC_GOOGLE_FLIGHTS")
    origin = Column(String(10), nullable=False, index=True)
    destination = Column(String(10), nullable=False, index=True)
    apw = Column(Integer, nullable=False, index=True)
    collection_date = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="SUCCESS", index=True) # SUCCESS, FAILED, SKIPPED_DUPLICATE
    quotes_count = Column(Integer, nullable=False, default=0)
    raw_file_path = Column(String(500), nullable=True)
    raw_payload_sha256 = Column(String(64), nullable=True)
    stored_file_sha256 = Column(String(64), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    error_message = Column(String(500), nullable=True)

    __table_args__ = (
        Index("idx_coll_evt_route_apw_date", "source_id", "origin", "destination", "apw", "collection_date", unique=True),
    )
