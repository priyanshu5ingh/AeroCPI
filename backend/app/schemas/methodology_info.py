from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict

class MethodologyInfoResponse(BaseModel):
    configuration_version: str
    configuration_fingerprint: str
    basket_version: str
    horizon_set: List[str]
    validation_rule_version: str
    outlier_rule_version: str
    source_policy_version: str
    aggregation_version: str
    publication_threshold_version: str
    effective_from: datetime
    effective_to: Optional[datetime] = None
    human_descriptions: Dict[str, str]

    model_config = ConfigDict(from_attributes=True)
