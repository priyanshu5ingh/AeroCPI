from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class RouteHorizonResultItem(BaseModel):
    horizon_code: str
    base_representative_fare: float
    current_representative_fare: float
    price_relative: float
    point_contribution: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class RouteIntelligenceResponse(BaseModel):
    route_id: str
    origin: str
    destination: str
    dgca_weight: float
    active_weight: float
    collection_dates: List[str]
    route_index_value: float
    base_representative_fare: float
    current_representative_fare: float
    point_contribution: Optional[float] = None
    direction: str
    horizon_results: List[RouteHorizonResultItem]
    coverage_ratio: float
    quality_summary: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
