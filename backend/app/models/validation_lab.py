import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from app.db.base import Base

class ValidationBenchmark(Base):
    __tablename__ = "validation_benchmarks"

    benchmark_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(255), nullable=True)
    source = Column(String(100), nullable=False)
    reference_period = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class ValidationRun(Base):
    __tablename__ = "validation_runs"

    validation_run_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("index_runs.run_id"), nullable=False, index=True)
    benchmark_id = Column(String(36), ForeignKey("validation_benchmarks.benchmark_id"), nullable=True, index=True)
    status = Column(String(30), nullable=False, default="DISABLED_NO_BENCHMARK_DATA")
    validation_timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class ValidationMetric(Base):
    __tablename__ = "validation_metrics"

    metric_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    validation_run_id = Column(String(36), ForeignKey("validation_runs.validation_run_id"), nullable=False, index=True)
    coverage = Column(Float, nullable=True)
    directional_agreement = Column(Float, nullable=True)
    correlation = Column(Float, nullable=True)
    absolute_deviation = Column(Float, nullable=True)
    relative_deviation = Column(Float, nullable=True)
    route_level_deviation = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
