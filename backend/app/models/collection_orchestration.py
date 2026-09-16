"""AeroGuide Collection Orchestration Models.
Persists collection runs, per-query source attempts, and operational health manifests.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Date, DateTime, Integer, Float, JSON, Index, ForeignKey
from app.db.base import Base


class CollectionRun(Base):
    __tablename__ = "collection_runs"

    run_id = Column(String(50), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    run_type = Column(String(30), nullable=False, default="LONGITUDINAL_PANEL") # LONGITUDINAL_PANEL, NATIONAL_SWEEP, ON_DEMAND
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime(timezone=True), nullable=True)
    
    routes_attempted = Column(Integer, nullable=False, default=0)
    sources_attempted = Column(Integer, nullable=False, default=0)
    queries_total = Column(Integer, nullable=False, default=0)
    queries_success = Column(Integer, nullable=False, default=0)
    queries_failed = Column(Integer, nullable=False, default=0)
    observations_saved = Column(Integer, nullable=False, default=0)
    
    errors_by_source = Column(JSON, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default="RUNNING") # RUNNING, COMPLETED, PARTIAL_SUCCESS, FAILED
    cadence = Column(String(30), nullable=False, default="DAILY_SCHEDULED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_coll_run_started", "started_at"),
        Index("idx_coll_run_status", "status"),
    )


class CollectionAttempt(Base):
    __tablename__ = "collection_attempts"

    attempt_id = Column(String(50), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(50), ForeignKey("collection_runs.run_id"), nullable=False, index=True)
    source_id = Column(String(40), nullable=False, index=True)
    
    origin = Column(String(10), nullable=False, index=True)
    destination = Column(String(10), nullable=False, index=True)
    route_id = Column(String(20), nullable=False, index=True)
    travel_date = Column(Date, nullable=False, index=True)
    apw = Column(Integer, nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime(timezone=True), nullable=True)
    latency_ms = Column(Float, nullable=True)
    
    status = Column(String(30), nullable=False, default="SUCCESS") # SUCCESS, FAILED, TIMEOUT, CONFIGURATION_REQUIRED, SKIPPED_DUPLICATE
    error_class = Column(String(50), nullable=True)
    error_detail = Column(String(500), nullable=True)
    observations_count = Column(Integer, nullable=False, default=0)
    raw_payload_sha256 = Column(String(64), nullable=True)

    __table_args__ = (
        Index("idx_coll_att_run_source", "run_id", "source_id"),
        Index("idx_coll_att_route_date", "route_id", "travel_date"),
    )
