from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict

class RouteIndexResultResponse(BaseModel):
    result_id: str
    run_id: str
    route_id: str
    origin_code: str
    destination_code: str
    travel_date: Optional[date] = None
    booking_horizon: int
    cabin: str
    stop_type: str
    reference_price: float
    current_price: float
    price_relative: float
    route_index_value: float
    weight_share: float
    sample_count: int
    eligible_count: int
    excluded_count: int
    flagged_count: int

    model_config = ConfigDict(from_attributes=True)
