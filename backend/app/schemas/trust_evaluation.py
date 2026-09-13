"""
Pydantic Schemas for Milestone 4C.3: Trust Engine
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import datetime as dt


class TrustEvaluationCreateRequest(BaseModel):
    route_id: str = Field(...)
    travel_date: dt.date = Field(...)
    horizon_days: int = Field(...)
    cabin: str = Field("ECONOMY")
    collection_date: Optional[dt.date] = Field(None)
    expected_observations: Optional[int] = Field(None)
    expected_sources: Optional[List[str]] = Field(None)
    min_observations_per_source: Optional[int] = Field(5)
    index_run_id: Optional[str] = Field(None)


class DimensionBreakdownSchema(BaseModel):
    observation_coverage: float
    source_agreement: float
    sample_sufficiency: float
    observation_validity: float
    outlier_health: float
    source_availability: float
    basket_horizon_stability: float


class EvidenceSummarySchema(BaseModel):
    coverage_ratio: float
    expected_required_observations: int
    percentage_median_difference: Optional[float]
    active_eligible_sources_count: int
    expected_sources_count: int
    minimum_source_observation_count: int
    total_observations: int
    eligible_observations: int
    accepted_observations: int
    flagged_observations: int
    rejected_observations: int
    validity_ratio: float
    outlier_count: int
    outlier_rate: float
    source_coverage_ratio: float
    stability_checks: Dict[str, bool]
    live_market_data_count: int
    test_data_count: int


class TrustEvaluationResponse(BaseModel):
    trust_evaluation_id: Optional[str] = None
    trust_engine_version: str
    trust_score: float
    trust_status: str
    health_status_from_4c2: str
    dimension_scores: DimensionBreakdownSchema
    evidence: EvidenceSummarySchema
    reason_codes: List[str]
    calculation_fingerprint: str
    trust_scope: Optional[Dict[str, Any]] = None
    policy_parameters: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any]

