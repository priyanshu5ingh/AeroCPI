from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

class TraceIndexRunNode(BaseModel):
    run_id: str
    headline_index_value: float
    headline_horizon_code: str
    reference_date: str
    calculation_date: str

class TraceConfigurationNode(BaseModel):
    configuration_version: str
    basket_version: str
    aggregation_version: str
    configuration_fingerprint: str

class TraceHorizonNode(BaseModel):
    horizon_code: str
    index_value: float
    is_headline: bool
    active_routes_count: int

class TraceRouteNode(BaseModel):
    route_id: str
    route_index_value: float
    point_contribution: Optional[float] = None
    dgca_weight: float
    base_representative_fare: float
    current_representative_fare: float

class TraceObservationsNode(BaseModel):
    total_observations_queried: int
    eligible_observations: int
    rejection_rate_pct: float

class TraceQualityNode(BaseModel):
    completeness_pct: float
    fare_integrity_pct: float
    rule_version: str

class TraceExplanationNode(BaseModel):
    top_positive_driver: str
    top_positive_points: float
    top_negative_driver: str
    top_negative_points: float

class MeasurementTraceResponse(BaseModel):
    run_id: str
    provenance_chain: List[str]
    index_run: TraceIndexRunNode
    configuration: TraceConfigurationNode
    horizons: List[TraceHorizonNode]
    routes: List[TraceRouteNode]
    observation_summary: TraceObservationsNode
    quality_summary: TraceQualityNode
    explanation_summary: TraceExplanationNode
    canonical_run_fingerprint: str
    manifest_sha256: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
