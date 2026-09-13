from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

class ValidationBenchmarkSchema(BaseModel):
    benchmark_id: str
    name: str
    description: Optional[str] = None
    source: str
    reference_period: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ValidationMetricSchema(BaseModel):
    metric_id: str
    validation_run_id: str
    coverage: Optional[float] = None
    directional_agreement: Optional[float] = None
    correlation: Optional[float] = None
    absolute_deviation: Optional[float] = None
    relative_deviation: Optional[float] = None
    route_level_deviation: Optional[Dict[str, float]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ValidationRunSchema(BaseModel):
    validation_run_id: str
    run_id: str
    benchmark_id: Optional[str] = None
    status: str = Field(..., description="ACTIVE | DISABLED_NO_BENCHMARK_DATA")
    validation_timestamp: datetime
    metrics: Optional[ValidationMetricSchema] = None

    model_config = ConfigDict(from_attributes=True)
