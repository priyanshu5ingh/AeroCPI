from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.index_dashboard import RouteDriverItem

class HorizonIntelligenceResponse(BaseModel):
    horizon_code: str
    horizon_days: int
    index_value: float
    base_coverage_ratio: float
    current_coverage_ratio: float
    matched_coverage_ratio: float
    active_routes_count: int
    total_basket_routes_count: int
    active_weight_sum: float
    is_headline: bool
    top_positive_routes: List[RouteDriverItem] = Field(default_factory=list)
    top_negative_routes: List[RouteDriverItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
