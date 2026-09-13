from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class ObservationExplorerItem(BaseModel):
    observation_id: str
    route_id: str
    source: str
    collection_timestamp: Optional[datetime] = None
    search_timestamp: Optional[datetime] = None
    travel_date: Optional[str] = None
    advance_purchase_days: int
    carrier: str
    cabin: str
    total_fare: float
    base_fare: Optional[float] = None
    taxes: Optional[float] = None
    fees: Optional[float] = None
    stops: int = 0
    duration_minutes: Optional[int] = None
    currency: str = "INR"
    validation_status: str = "ACCEPT"
    index_eligibility: str = "ELIGIBLE"
    quality_status: str = "COMPLETE"
    anomaly_flags: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class ObservationExplorerResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    observations: List[ObservationExplorerItem]

    model_config = ConfigDict(from_attributes=True)
