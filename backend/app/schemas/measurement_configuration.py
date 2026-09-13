from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class MeasurementConfigurationCreate(BaseModel):
    configuration_version: str = Field(..., description="Configuration version identifier")
    basket_version: str = Field("DGCA-10-2026.1", description="Route basket version")
    horizon_set: List[str] = Field(default_factory=lambda: ["T+1", "T+7", "T+15", "T+30", "T+45"])
    validation_rule_version: str = Field("VAL-2026.1")
    outlier_rule_version: str = Field("IQR-1.5-v1")
    source_policy_version: str = Field("MULTI-SOURCE-V1")
    aggregation_version: str = Field("JEVONS-GEOMETRIC-V1")
    publication_threshold_version: str = Field("PUB-THRESH-V1")
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None

class MeasurementConfigurationSchema(MeasurementConfigurationCreate):
    configuration_id: str
    effective_from: datetime
    configuration_fingerprint: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
