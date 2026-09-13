from __future__ import annotations
import datetime as dt
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class AuditScope(BaseModel):
    run_id: str
    reference_date: str
    calculation_date: str
    cabin: str = "ECONOMY"
    basket_version: str = "BASKET-DGCA-2025-TOP10"
    audit_timestamp: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class RunIdentity(BaseModel):
    run_id: str
    run_timestamp: dt.datetime
    reference_period: str
    comparison_period: str
    index_method: str
    frequency: str
    headline_index_value: float
    headline_horizon_code: str

    model_config = ConfigDict(from_attributes=True)


class VersionAudit(BaseModel):
    methodology_version: str
    route_basket_version: str
    proxy_weight_version: str
    software_version: str
    quality_rule_version: str
    normalization_version: str

    model_config = ConfigDict(from_attributes=True)


class PopulationAudit(BaseModel):
    total_observations_queried: Optional[int] = None
    total_eligible_observations: Optional[int] = None
    total_excluded_observations: Optional[int] = None
    rejection_breakdown: Optional[Dict[str, int]] = None
    reference_date_count: Optional[int] = None
    calculation_date_count: Optional[int] = None
    provenance_status: str = Field(
        ..., description="PERSISTED, DERIVED_FROM_PERSISTED_RUN_ARTIFACT, or NOT_AVAILABLE"
    )

    model_config = ConfigDict(from_attributes=True)


class HorizonRouteAudit(BaseModel):
    horizon_code: str
    horizon_days: int
    active_routes_count: int
    base_routes_count: int
    missing_routes_count: int
    total_basket_routes_count: int

    model_config = ConfigDict(from_attributes=True)


class RouteAudit(BaseModel):
    total_basket_routes: int
    expected_route_horizon_pairs: int
    calculated_route_horizon_pairs: int
    unavailable_route_horizon_pairs: int
    horizon_route_counts: List[HorizonRouteAudit] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class HorizonCoverageAudit(BaseModel):
    horizon_code: str
    base_coverage_ratio: float
    current_coverage_ratio: float
    matched_coverage_ratio: float
    active_weight_sum: float

    model_config = ConfigDict(from_attributes=True)


class CoverageAudit(BaseModel):
    headline_coverage_ratio: float
    horizon_coverage: List[HorizonCoverageAudit] = Field(default_factory=list)
    temporal_coverage_status: str = "NOT_APPLICABLE_FOR_SINGLE_RUN"

    model_config = ConfigDict(from_attributes=True)


class TrustAudit(BaseModel):
    trust_evaluation_id: Optional[str] = None
    trust_score: Optional[float] = None
    trust_status: str = "UNEVALUATED"
    reason_codes: List[str] = Field(default_factory=list)
    is_diagnostic_only: bool = True
    trust_evaluation_status: str = Field(
        ..., description="VERIFIED_FROM_PERSISTED_EVALUATION or UNEVALUATED"
    )

    model_config = ConfigDict(from_attributes=True)


class ReproducibilityAudit(BaseModel):
    canonical_run_fingerprint: str
    manifest_sha256: Optional[str] = None
    manifest_present: bool = True
    raw_input_artifacts_available: bool = False
    is_reproducible: bool = False
    reproducibility_status: str = Field(
        ..., description="FULLY_REPRODUCIBLE, ARTIFACT_REPRODUCIBLE, or NOT_REPRODUCIBLE"
    )

    model_config = ConfigDict(from_attributes=True)


class IndexAuditResponse(BaseModel):
    audit_scope: AuditScope
    run_identity: RunIdentity
    versions: VersionAudit
    population_audit: PopulationAudit
    route_audit: RouteAudit
    coverage_audit: CoverageAudit
    trust_audit: TrustAudit
    reproducibility_audit: ReproducibilityAudit
    calculation_manifest: Optional[Dict[str, Any]] = None
    limitations: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "AeroCPI is an independent real-time airfare price index designed to augment CPI. "
        "Route weights are derived from official DGCA passenger traffic statistics. "
        "AeroCPI is not statistically equivalent to CPI."
    )

    model_config = ConfigDict(from_attributes=True)
