from datetime import datetime
from typing import Optional, Any, List
from pydantic import BaseModel, ConfigDict

class NormalizationResultResponse(BaseModel):
    normalization_id: str
    observation_id: str
    base_fare: float
    taxes: float
    mandatory_fees: float
    included_fare_components: Optional[List[Any]] = None
    normalized_total: float
    exclusions: Optional[List[Any]] = None
    normalization_version: str = "V1_SIMPLE_SUM"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
