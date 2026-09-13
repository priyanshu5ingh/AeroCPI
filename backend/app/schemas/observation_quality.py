from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class ObservationQualityCreate(BaseModel):
    observation_id: str
    completeness_status: str = Field("COMPLETE")
    timestamp_status: str = Field("VALID")
    fare_integrity_status: str = Field("VALID")
    route_mapping_status: str = Field("MAPPED")
    duplicate_risk: str = Field("LOW")
    anomaly_flags: List[str] = Field(default_factory=list)
    source_health_status: str = Field("HEALTHY")
    quality_rule_version: str = Field("QR-2026.1")

class ObservationQualityProfileSchema(ObservationQualityCreate):
    quality_id: str
    quality_fingerprint: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
