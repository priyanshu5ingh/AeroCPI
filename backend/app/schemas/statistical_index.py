from __future__ import annotations
import datetime as dt
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class StatisticalIndexRunRequest(BaseModel):
    reference_date: dt.date = Field(..., description="Common baseline date t0 for all routes")
    calculation_date: dt.date = Field(..., description="Target calculation date t")
    cabin: str = Field(default="ECONOMY", description="Cabin class (default: ECONOMY)")
    basket_version: str = Field(default="BASKET-DGCA-2025-TOP10", description="Route basket version")
    trust_evaluation_id: Optional[str] = Field(default=None, description="Optional diagnostic trust evaluation ID")


class HorizonIndexResponse(BaseModel):
    id: Optional[int] = None
    run_id: str
    horizon_code: str
    horizon_days: int
    index_name: str
    index_value: Optional[float]
    matched_sample_index_value: Optional[float] = None
    base_coverage_ratio: float
    current_coverage_ratio: float
    matched_coverage_ratio: float
    active_weight_sum: float
    active_routes_count: int
    base_routes_count: int
    total_basket_routes_count: int
    is_headline: bool

    model_config = ConfigDict(from_attributes=True)


class StatisticalIndexRunResponse(BaseModel):
    run_id: str
    run_timestamp: dt.datetime
    reference_date: str
    calculation_date: str
    methodology_version: str
    route_basket_version: str
    proxy_weight_version: str
    canonical_run_fingerprint: str
    headline_index_value: float
    coverage_ratio: float
    trust_evaluation_id: Optional[str] = None
    horizons: List[HorizonIndexResponse] = []
    calculation_manifest: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class TemporalAggregationRequest(BaseModel):
    frequency: str = Field(default="WEEKLY", description="WEEKLY or MONTHLY")
    horizon_code: str = Field(default="T+15", description="Horizon code (e.g. T+1, T+7, T+15, T+30, T+45)")
    start_date: dt.date = Field(..., description="Start of the aggregation window")
    end_date: dt.date = Field(..., description="End of the aggregation window")


class TemporalAggregationResponse(BaseModel):
    frequency: str
    horizon_code: str
    start_date: dt.date
    end_date: dt.date
    index_value: Optional[float]
    days_expected: int
    days_available: int
    temporal_coverage_ratio: float
    status: str

    model_config = ConfigDict(from_attributes=True)


class InflationRateRequest(BaseModel):
    rate_type: str = Field(default="MOM", description="MOM (Month-over-Month) or YOY (Year-over-Year)")
    current_date: dt.date = Field(..., description="Date of the current index level")
    comparison_date: dt.date = Field(..., description="Date of the base/historical index level")
    horizon_code: str = Field(default="T+15", description="Horizon code (e.g. T+15)")


class InflationRateResponse(BaseModel):
    rate_type: str
    horizon_code: str
    current_date: dt.date
    comparison_date: dt.date
    current_index: Optional[float]
    previous_index: Optional[float]
    inflation_rate_percent: Optional[float]
    status: str

    model_config = ConfigDict(from_attributes=True)
