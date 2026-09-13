import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from app.db.base import Base

class HorizonIndexResult(Base):
    __tablename__ = "horizon_index_results"

    result_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("index_runs.run_id"), nullable=False, index=True)
    horizon_code = Column(String(10), nullable=False, index=True)
    horizon_days = Column(Integer, nullable=False)
    index_name = Column(String(50), nullable=False)
    index_value = Column(Float, nullable=False)
    matched_sample_index_value = Column(Float, nullable=True)
    
    # Coverage Triad
    base_coverage_ratio = Column(Float, nullable=False, default=0.0)
    current_coverage_ratio = Column(Float, nullable=False, default=0.0)
    matched_coverage_ratio = Column(Float, nullable=False, default=0.0)
    active_weight_sum = Column(Float, nullable=False, default=1.0)
    
    # Active vs Base route counts
    active_routes_count = Column(Integer, nullable=False, default=0)
    base_routes_count = Column(Integer, nullable=False, default=0)
    total_basket_routes_count = Column(Integer, nullable=False, default=10)
    
    is_headline = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
