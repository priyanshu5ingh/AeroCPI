from datetime import date, datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, field_validator, model_validator, ConfigDict
from app.schemas.common import DataStatus, VALID_HORIZONS
from app.schemas.normalization import NormalizationResultResponse
from app.schemas.quality import QualityResultResponse

class RawQuoteInput(BaseModel):
    source_id: str
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    collected_at: Optional[datetime] = None
    search_timestamp: Optional[datetime] = None
    search_date: Optional[date] = None
    travel_date: date
    origin_raw: str
    destination_raw: str
    airline: str
    flight_number: Optional[str] = None
    cabin: str = "ECONOMY"
    fare_class: Optional[str] = "STANDARD"
    trip_type: str = "ONE_WAY"
    stops: Optional[int] = None
    duration_minutes: Optional[int] = None
    raw_total_fare: Optional[str] = None
    raw_base_fare: Optional[str] = None
    raw_taxes: Optional[str] = None
    raw_fees: Optional[str] = None
    base_fare: Optional[float] = None
    taxes: Optional[float] = None
    fees: Optional[float] = None
    total_fare: float
    currency: str = "INR"

    @model_validator(mode="after")
    def validate_search_time(self) -> "RawQuoteInput":
        if self.search_timestamp is None and self.search_date is None:
            raise ValueError("Either search_timestamp or search_date must be provided")
        if self.search_timestamp is not None and self.search_date is None:
            self.search_date = self.search_timestamp.date()
        elif self.search_date is not None and self.search_timestamp is None:
            from datetime import time
            self.search_timestamp = datetime.combine(self.search_date, time.min, tzinfo=timezone.utc)
        return self

class CanonicalObservationResponse(BaseModel):
    observation_id: str
    source_id: str
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    collected_at: datetime
    search_timestamp: Optional[datetime] = None
    search_date: date
    travel_date: date
    advance_purchase_days: Optional[int] = None
    horizon_code: str
    origin_raw: str
    destination_raw: str
    origin_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    route_id: str
    route_mapping_status: str
    basket_status: str
    airline: str
    flight_number: Optional[str] = None
    cabin: str
    fare_class: Optional[str] = None
    trip_type: str
    stops: Optional[int] = None
    stops_status: str
    duration_minutes: Optional[int] = None
    raw_total_fare: Optional[str] = None
    raw_base_fare: Optional[str] = None
    raw_taxes: Optional[str] = None
    raw_fees: Optional[str] = None
    base_fare: Optional[float] = None
    taxes: Optional[float] = None
    fees: Optional[float] = None
    total_fare: float
    currency: str
    breakdown_status: str
    arithmetic_status: str
    raw_payload_hash: Optional[str] = None
    observation_key: Optional[str] = None
    quote_fingerprint: Optional[str] = None
    validation_status: str
    validation_reasons: Optional[list] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ObservationBase(BaseModel):
    source_id: str
    route_id: str
    carrier_id: str
    travel_date: date
    observed_at: datetime
    booking_horizon_days: int
    cabin: str = "ECONOMY"
    fare_class: Optional[str] = "STANDARD"
    trip_type: str = "ONE_WAY"
    base_fare: float
    taxes: float
    mandatory_fees: float
    total_fare: float
    currency: str = "INR"
    baggage_information: Optional[Dict[str, Any]] = None
    stop_type: str = "NON_STOP"
    data_status: DataStatus = DataStatus.OBSERVED
    raw_reference: Optional[str] = None

    @field_validator("booking_horizon_days")
    @classmethod
    def validate_horizon(cls, v: int) -> int:
        if v not in VALID_HORIZONS:
            raise ValueError(f"Invalid booking_horizon_days '{v}'. Core SIH horizons must be one of {sorted(list(VALID_HORIZONS))}")
        return v

    @field_validator("observed_at")
    @classmethod
    def validate_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @field_validator("base_fare")
    @classmethod
    def validate_base_fare(cls, v: float) -> float:
        if v < 0:
            raise ValueError("base_fare cannot be negative")
        return v

    @field_validator("taxes")
    @classmethod
    def validate_taxes(cls, v: float) -> float:
        if v < 0:
            raise ValueError("taxes cannot be negative")
        return v

    @field_validator("mandatory_fees")
    @classmethod
    def validate_mandatory_fees(cls, v: float) -> float:
        if v < 0:
            raise ValueError("mandatory_fees cannot be negative")
        return v

    @field_validator("total_fare")
    @classmethod
    def validate_total_fare(cls, v: float) -> float:
        if v < 0:
            raise ValueError("total_fare cannot be negative")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if not v_clean or len(v_clean) != 3:
            raise ValueError("currency must be an explicit 3-character code (e.g. 'INR')")
        if v_clean != "INR":
            raise ValueError(f"Unsupported currency '{v_clean}'. AeroCPI strictly requires INR and prohibits silent currency conversions.")
        return v_clean

    @model_validator(mode="after")
    def validate_sums_and_currency(self):
        # Deterministic normalization check: sum of components must match total_fare
        expected_total = round(self.base_fare + self.taxes + self.mandatory_fees, 2)
        if abs(round(self.total_fare, 2) - expected_total) > 0.01:
            raise ValueError(f"total_fare ({self.total_fare}) does not match sum of base_fare ({self.base_fare}) + taxes ({self.taxes}) + mandatory_fees ({self.mandatory_fees}) = {expected_total}")
        return self

class ObservationCreate(ObservationBase):
    pass

class ObservationResponse(ObservationBase):
    observation_id: str
    created_at: datetime
    normalization_result: Optional[NormalizationResultResponse] = None
    quality_result: Optional[QualityResultResponse] = None

    model_config = ConfigDict(from_attributes=True)

class ObservationFilter(BaseModel):
    route_id: Optional[str] = None
    carrier_id: Optional[str] = None
    booking_horizon_days: Optional[int] = None
    validation_status: Optional[str] = None
    basket_status: Optional[str] = None
    data_status: Optional[DataStatus] = None
    travel_date: Optional[date] = None
    limit: int = 50
    offset: int = 0
