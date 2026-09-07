from datetime import date, datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, field_validator, ConfigDict
from app.schemas.common import VALID_HORIZONS

class VirtualTripBase(BaseModel):
    origin: str
    destination: str
    travel_date: date
    passengers: int = 1
    cabin: str = "ECONOMY"
    trip_type: str = "ONE_WAY"
    booking_horizon: int
    baggage_requirement: str = "15KG_CHECKIN_7KG_CARRYON"
    eligible_stop_type: str = "NON_STOP"
    fare_inclusion_rules: Optional[Dict[str, Any]] = None

    @field_validator("booking_horizon")
    @classmethod
    def validate_horizon(cls, v: int) -> int:
        if v not in VALID_HORIZONS:
            raise ValueError(f"Invalid booking_horizon '{v}'. Must be one of {sorted(list(VALID_HORIZONS))}")
        return v

    @field_validator("destination")
    @classmethod
    def validate_origin_dest(cls, v: str, info) -> str:
        origin = info.data.get("origin")
        if origin and origin.upper() == v.upper():
            raise ValueError("Origin and destination cannot be the same")
        return v.upper()

    @field_validator("origin")
    @classmethod
    def uppercase_origin(cls, v: str) -> str:
        return v.upper()

    @field_validator("passengers")
    @classmethod
    def validate_passengers(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Passengers count must be greater than 0")
        return v

class VirtualTripCreate(VirtualTripBase):
    pass

class VirtualTripResponse(VirtualTripBase):
    spec_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
