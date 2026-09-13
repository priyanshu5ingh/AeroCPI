from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

class DataQualitySummaryResponse(BaseModel):
    run_id: str
    total_observations: int
    eligible_observations: int
    eligibility_ratio: float
    completeness: Dict[str, int]
    timestamp_validity: Dict[str, int]
    fare_integrity: Dict[str, int]
    route_mapping: Dict[str, int]
    duplicate_risk: Dict[str, int]
    anomaly_flags_breakdown: Dict[str, int]
    source_health_breakdown: Dict[str, int]
    quality_rule_version: str

    model_config = ConfigDict(from_attributes=True)

class DataQualityRouteItem(BaseModel):
    route_id: str
    total_quotes: int
    eligible_quotes: int
    eligibility_ratio: float
    anomaly_flags: List[str]

    model_config = ConfigDict(from_attributes=True)

class DataQualityRoutesResponse(BaseModel):
    run_id: str
    routes: List[DataQualityRouteItem]

    model_config = ConfigDict(from_attributes=True)

class DataQualitySourceItem(BaseModel):
    source_name: str
    status: str
    observations_contributed: int
    latency_ms: int

    model_config = ConfigDict(from_attributes=True)

class DataQualitySourcesResponse(BaseModel):
    run_id: str
    sources: List[DataQualitySourceItem]

    model_config = ConfigDict(from_attributes=True)
