from __future__ import annotations
import datetime as dt
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class DashboardScope(BaseModel):
    run_id: str
    reference_date: str
    calculation_date: str
    cabin: str = "ECONOMY"
    dashboard_timestamp: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardHeadline(BaseModel):
    horizon_code: str
    index_name: str
    index_value: float
    reference_date: str
    calculation_date: str
    change_from_base: float = Field(..., description="Presentation metric: index_value - 100.0")
    direction: str = Field(..., description="UP, DOWN, or UNCHANGED")
    is_headline: bool = True

    model_config = ConfigDict(from_attributes=True)


class RouteDriverItem(BaseModel):
    route_id: str
    origin: str
    destination: str
    base_representative_fare: float
    current_representative_fare: float
    route_index_value: float
    point_contribution: Optional[float] = Field(None, description="Persisted 5A point contribution to index shift")
    direction: str = Field(..., description="POSITIVE, NEGATIVE, or NEUTRAL")
    active_weight: float

    model_config = ConfigDict(from_attributes=True)


class DriverSummary(BaseModel):
    top_positive_drivers: List[RouteDriverItem] = Field(default_factory=list)
    top_negative_drivers: List[RouteDriverItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class HorizonCoverageItem(BaseModel):
    horizon_code: str
    index_value: Optional[float]
    base_coverage_ratio: float
    current_coverage_ratio: float
    matched_coverage_ratio: float
    active_routes_count: int
    total_basket_routes_count: int
    active_weight_sum: float

    model_config = ConfigDict(from_attributes=True)


class CoverageSummary(BaseModel):
    headline_horizon_code: str
    headline_coverage_ratio: float
    horizon_coverage: List[HorizonCoverageItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DashboardTrustSummary(BaseModel):
    trust_score: Optional[float] = None
    trust_status: str = "UNEVALUATED"
    reason_codes: List[str] = Field(default_factory=list)
    is_diagnostic_only: bool = True
    trust_evaluation_status: str = "UNEVALUATED"

    model_config = ConfigDict(from_attributes=True)


class MethodologySummary(BaseModel):
    methodology_version: str
    basket_version: str
    proxy_weight_version: str
    software_version: str
    reference_date: str
    calculation_date: str
    cabin: str
    headline_horizon: str
    disclaimer: str = (
        "AeroCPI is an independent real-time airfare price index designed to augment CPI "
        "and is not statistically equivalent to CPI."
    )

    model_config = ConfigDict(from_attributes=True)


class DashboardAuditSummary(BaseModel):
    canonical_run_fingerprint: str
    manifest_sha256: Optional[str] = None
    manifest_present: bool = True
    raw_input_artifacts_available: bool = False
    reproducibility_status: str = "ARTIFACT_REPRODUCIBLE"
    limitations: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class IndexDashboardResponse(BaseModel):
    dashboard_scope: DashboardScope
    headline: DashboardHeadline
    drivers: DriverSummary
    coverage: CoverageSummary
    trust: DashboardTrustSummary
    methodology: MethodologySummary
    audit: DashboardAuditSummary
    disclaimer: str = (
        "AeroCPI is an independent real-time airfare price index designed to augment CPI "
        "and is not statistically equivalent to CPI."
    )

    model_config = ConfigDict(from_attributes=True)
