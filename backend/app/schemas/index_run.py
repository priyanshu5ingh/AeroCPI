from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.schemas.quality_summary import QualitySummaryResponse

from app.schemas.common import IndexFrequency, UnavailableReason

class IndexRunCreate(BaseModel):
    reference_period: str # e.g. "2026-08-01"
    comparison_period: str # e.g. "2026-09-01"
    frequency: IndexFrequency = IndexFrequency.MONTHLY
    dataset_version_id: Optional[str] = None
    route_basket_version: str = "BASKET_2026_Q1"
    proxy_weight_version: str = "DGCA_PROXY_2026_V1"

class IndexRunResponse(BaseModel):
    run_id: str
    run_timestamp: datetime
    reference_period: str
    comparison_period: str
    frequency: str
    dataset_version_id: Optional[str] = None
    route_basket_version: str
    proxy_weight_version: str
    methodology_version: str
    normalization_version: str
    quality_rule_version: str
    index_method: str
    
    expected_route_horizon_pairs: int
    calculated_route_horizon_pairs: int
    unavailable_route_horizon_pairs: int
    
    valid_count: int
    outlier_flagged_count: int
    retained_with_warning_count: int
    excluded_count: int
    
    number_of_observations: int
    number_of_eligible_observations: int
    number_of_excluded_observations: int
    number_of_outlier_flagged: int
    number_of_retained_warning: int
    number_of_duplicates: int
    coverage_ratio: float
    
    index_value: float
    software_version: str
    canonical_run_fingerprint: str
    calculation_manifest: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)
