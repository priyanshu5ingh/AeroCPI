from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.common import OutlierStatus

class QualityResultResponse(BaseModel):
    quality_id: str
    observation_id: str
    eligible: bool = True
    duplicate_flag: bool = False
    missing_data_flag: bool = False
    outlier_status: OutlierStatus = OutlierStatus.VALID
    exclusion_reason: Optional[str] = None
    quality_rule_version: str = "V1_BASIC_CHECKS"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
