import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from app.db.base import Base

class IndexRun(Base):
    __tablename__ = "index_runs"

    run_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    reference_period = Column(String(20), nullable=False)
    comparison_period = Column(String(20), nullable=False)
    dataset_version_id = Column(String(50), ForeignKey("dataset_versions.dataset_version_id"), nullable=True, index=True)
    route_basket_version = Column(String(50), nullable=False, default="BASKET_2026_Q1")
    proxy_weight_version = Column(String(50), nullable=False, default="DGCA_PROXY_2026_V1")
    methodology_version = Column(String(50), nullable=False, default="JEVONS_YOUNG_LASPEYRES_V1")
    normalization_version = Column(String(30), nullable=False, default="V1_SIMPLE_SUM")
    quality_rule_version = Column(String(30), nullable=False, default="V1_MAD_DUPLICATE_CHECKS")
    index_method = Column(String(50), nullable=False, default="JEVONS_YOUNG_LASPEYRES")
    
    frequency = Column(String(20), nullable=False, default="MONTHLY")
    expected_route_horizon_pairs = Column(Integer, nullable=False, default=40)
    calculated_route_horizon_pairs = Column(Integer, nullable=False, default=0)
    unavailable_route_horizon_pairs = Column(Integer, nullable=False, default=0)
    
    valid_count = Column(Integer, nullable=False, default=0)
    outlier_flagged_count = Column(Integer, nullable=False, default=0)
    retained_with_warning_count = Column(Integer, nullable=False, default=0)
    excluded_count = Column(Integer, nullable=False, default=0)
    
    number_of_observations = Column(Integer, nullable=False, default=0)
    number_of_eligible_observations = Column(Integer, nullable=False, default=0)
    number_of_excluded_observations = Column(Integer, nullable=False, default=0)
    number_of_outlier_flagged = Column(Integer, nullable=False, default=0)
    number_of_retained_warning = Column(Integer, nullable=False, default=0)
    number_of_duplicates = Column(Integer, nullable=False, default=0)
    coverage_ratio = Column(Float, nullable=False, default=0.0)
    
    index_value = Column(Float, nullable=False, default=100.0)
    software_version = Column(String(30), nullable=False, default="0.2.0-milestone2")
    canonical_run_fingerprint = Column(String(64), nullable=False)
    calculation_manifest = Column(JSON, nullable=True)
    trust_evaluation_id = Column(String(36), nullable=True, index=True)

