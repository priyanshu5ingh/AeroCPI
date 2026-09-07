from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, field_validator, ConfigDict

class ProxyRouteWeightBase(BaseModel):
    weight_version_id: str
    route_id: str
    weight_share: float
    weight_type: str = "DGCA_TRAFFIC_SHARE_PROXY"
    is_demo: bool = True
    source_metadata: Optional[Dict[str, Any]] = None

    @field_validator("weight_share")
    @classmethod
    def validate_weight_share(cls, v: float) -> float:
        if v < 0 or v > 1.0:
            raise ValueError(f"weight_share must be between 0.0 and 1.0 (got {v})")
        return v

class ProxyRouteWeightCreate(ProxyRouteWeightBase):
    pass

class ProxyRouteWeightResponse(ProxyRouteWeightBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
