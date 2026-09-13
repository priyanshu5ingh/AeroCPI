from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class PublicationReadinessResponse(BaseModel):
    run_id: str
    status: str = Field(..., description="PUBLISHABLE | DEGRADED | INSUFFICIENT_DATA | NOT_EVALUATED")
    is_publishable: bool
    reasons: List[str] = Field(default_factory=list)
    headline_coverage_ratio: float
    active_weight_sum: float
    trust_status: str
    evaluated_at: str

    model_config = ConfigDict(from_attributes=True)
