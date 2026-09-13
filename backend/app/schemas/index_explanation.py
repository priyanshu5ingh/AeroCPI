from __future__ import annotations
import datetime as dt
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ExplanationScope(BaseModel):
    run_id: str
    reference_date: str
    calculation_date: str
    cabin: str = "ECONOMY"
    basket_version: str = "BASKET-DGCA-2025-TOP10"

    model_config = ConfigDict(from_attributes=True)


class RouteContributionExplanation(BaseModel):
    route_id: str
    horizon_code: str
    collection_date: str
    origin_code: str
    destination_code: str
    base_representative_fare: float
    current_representative_fare: float
    price_relative: float
    route_index_value: float
    dgca_basket_weight: float
    active_weight: float
    log_contribution: float
    point_contribution: Optional[Decimal] = None
    direction: str = Field(..., description="POSITIVE, NEGATIVE, or NEUTRAL")

    @field_serializer("point_contribution", when_used="json")
    def serialize_point_contribution(self, v: Optional[Decimal]) -> Optional[float]:
        return float(v) if v is not None else None

    model_config = ConfigDict(from_attributes=True)


class MissingRouteInfo(BaseModel):
    route_id: str
    horizon_code: str
    reason_code: str = Field(..., description="MISSING_CURRENT_OBSERVATION, LATE_APPEARING_EXCLUDED, or NO_BASE_OBSERVATION")
    description: str

    model_config = ConfigDict(from_attributes=True)


class HorizonExplanation(BaseModel):
    horizon_code: str
    horizon_days: int
    collection_date: str
    index_name: str
    index_value: Optional[float]
    matched_sample_index_value: Optional[float] = None
    is_headline: bool = False
    active_routes_count: int
    base_routes_count: int
    total_basket_routes_count: int
    base_coverage_ratio: float
    current_coverage_ratio: float
    matched_coverage_ratio: float
    active_weight_sum: float
    reason_codes: List[str] = Field(default_factory=list)
    route_contributions: List[RouteContributionExplanation] = Field(default_factory=list)
    missing_routes: List[MissingRouteInfo] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TrustExplanation(BaseModel):
    trust_evaluation_id: Optional[str] = None
    trust_score: Optional[float] = None
    trust_status: str = "UNEVALUATED"
    reason_codes: List[str] = Field(default_factory=list)
    is_diagnostic_only: bool = True

    model_config = ConfigDict(from_attributes=True)


class IndexExplanationResponse(BaseModel):
    explanation_scope: ExplanationScope
    index_run_id: str
    headline_horizon_code: str
    headline_index_value: float
    reference_date: str
    calculation_date: str
    methodology_version: str
    route_basket_version: str
    proxy_weight_version: str
    software_version: str
    canonical_run_fingerprint: str
    horizons: List[HorizonExplanation] = Field(default_factory=list)
    trust_summary: TrustExplanation
    calculation_manifest: Optional[Dict[str, Any]] = None
    disclaimer: str = (
        "AeroCPI is an independent real-time airfare price index designed to augment CPI. "
        "Route weights are derived from official DGCA passenger traffic statistics. "
        "AeroCPI is not statistically equivalent to CPI."
    )

    model_config = ConfigDict(from_attributes=True)
