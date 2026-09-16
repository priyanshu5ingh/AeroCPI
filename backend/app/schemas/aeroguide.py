"""AeroGuide Pydantic Schemas.
Strict contracts for consumer airfare intelligence, airline matrices, and decision traces.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class AeroGuideAnalyzeRequest(BaseModel):
    origin: str = Field(..., description="IATA origin airport code, e.g. 'BLR'")
    destination: str = Field(..., description="IATA destination airport code, e.g. 'DEL'")
    travel_date: str = Field(..., description="ISO travel date 'YYYY-MM-DD'")
    flexibility_days: int = Field(default=2, ge=0, le=3, description="Day window around requested date")
    priority: str = Field(default="CHEAPEST", description="User ranking priority: CHEAPEST, FASTEST, DIRECT_AIRLINE, FLEXIBILITY")
    adults: int = Field(default=1, ge=1, le=9)
    children: int = Field(default=0, ge=0)
    infants: int = Field(default=0, ge=0)
    cabin: str = Field(default="ECONOMY")

class AirlineAlternative(BaseModel):
    carrier_code: str
    airline_name: str
    observed_fare: float
    currency: str = "INR"
    stops: int = 0
    duration_minutes: Optional[int] = None
    source_id: str
    source_evidence: str # e.g. "SEARCH_OBSERVATION", "AIRLINE_DIRECT"
    source_state: str # "CURRENTLY_OBSERVED_VIA_SEARCH", "DOCUMENTED_NDC_RESTRICTED"
    is_direct_airline: bool = False
    current_position: str # "LOW", "TYPICAL", "HIGH"
    departure_time: Optional[str] = None
    observation_id: Optional[str] = None

class FlexibleDateOption(BaseModel):
    travel_date: str
    days_diff: int
    observed_fare: float
    difference_from_requested: float
    percent_difference: float
    carrier_code: str
    stops: int
    source_evidence: str
    is_lower_fare: bool
    label: str # e.g. "Oct 16 — ₹6,180 observed"

class DecisionTraceNode(BaseModel):
    stage_number: int
    stage_name: str
    status: str
    evidence_summary: str
    structured_payload: Dict[str, Any] = Field(default_factory=dict)

class AeroGuideAnalyzeResponse(BaseModel):
    request_id: str
    origin: str
    destination: str
    route_id: str
    travel_date: str
    days_to_departure: int
    
    # Primary Market Observation
    current_observed_fare: float
    currency: str = "INR"
    price_position: str # LOW, TYPICAL, HIGH, INSUFFICIENT_DATA
    route_historical_median: float
    route_historical_min: float
    route_historical_max: float
    observations_in_sample: int
    
    # Model Outlook
    model_outlook_status: str # "COLLECTING_LONGITUDINAL_EVIDENCE", "READY_FOR_MODEL"
    model_probabilities: Optional[Dict[str, float]] = None # e.g. {"up": 0.45, "stable": 0.34, "down": 0.21}
    model_outlook_message: str
    
    # Deterministic Decision Verdict
    booking_guidance: str # BOOK, WAIT, WATCH, FLEX_DATE, INSUFFICIENT_DATA
    guidance_reason: str
    decision_policy_version: str = "DECISION_POLICY_V1"
    
    # Market Options & Alternatives
    airline_alternatives: List[AirlineAlternative] = Field(default_factory=list)
    flexible_dates: List[FlexibleDateOption] = Field(default_factory=list)
    sources_available: List[str] = Field(default_factory=list)
    
    # Verifiable Lineage & Explanation
    decision_trace: List[DecisionTraceNode] = Field(default_factory=list)
    grounded_explanation: str
    longitudinal_readiness: Dict[str, Any] = Field(default_factory=dict)

class ForecastingReadinessResponse(BaseModel):
    dataset_classification: str # INSUFFICIENT_LONGITUDINAL_HISTORY, READY_FOR_MODEL
    model_training_status: str # DISABLED, ENABLED
    total_observations: int
    unique_routes: int
    unique_travel_dates: int
    unique_search_dates: int
    longitudinal_pairs_count: int
    repeated_trajectories: int = 0
    trajectories_with_gte_3_searches: int = 0
    effective_forecasting_examples: int = 0
    seven_day_target_pairs: int = 0
    fourteen_day_target_pairs: int = 0
    longest_history_days: int = 0
    source_coverage: List[str] = Field(default_factory=list)
    airline_coverage: List[str] = Field(default_factory=list)
    overall_readiness: str = "INSUFFICIENT_LONGITUDINAL_HISTORY"
    readiness_notes: str
    required_collection_schedule: Dict[str, Any]

class CarrierQuotePoint(BaseModel):
    carrier_code: str
    airline_name: str
    fare: float
    stops: int = 0
    duration_minutes: int = 135

class TrajectorySearchPoint(BaseModel):
    search_date: str
    search_timestamp: Optional[str] = None
    days_to_departure: int
    median_fare: float
    min_fare: float
    max_fare: float
    carrier_quotes: List[CarrierQuotePoint] = Field(default_factory=list)

class MatchedCarrierTarget(BaseModel):
    carrier_code: str
    airline_name: str
    prediction_fare: float
    future_fare: float
    delta_fare: float
    delta_pct: float
    direction: str

class TrajectoryTargetEvaluation(BaseModel):
    prediction_search_date: str
    future_search_date: str
    days_gap: int
    is_valid_7d_target: bool
    is_valid_14d_target: bool = False
    
    # 1. Market-Level Target
    prediction_median_fare: float
    future_median_fare: float
    delta_fare: float
    delta_pct: float
    direction: str
    market_target: Dict[str, Any] = Field(default_factory=dict)
    
    # 2. Matched-Carrier Target
    carrier_composition_status: str # IDENTICAL, PARTIAL_OVERLAP, DISJOINT
    matched_carriers_count: int = 0
    matched_carrier_mean_delta_fare: Optional[float] = None
    matched_carrier_mean_delta_pct: Optional[float] = None
    matched_carrier_targets: List[MatchedCarrierTarget] = Field(default_factory=list)

class TrajectoryDetailResponse(BaseModel):
    route_id: str
    origin: str
    destination: str
    travel_date: str
    search_dates_count: int
    observations_count: int
    search_points: List[TrajectorySearchPoint] = Field(default_factory=list)
    target_evaluations: List[TrajectoryTargetEvaluation] = Field(default_factory=list)
    has_7_day_pair: bool
    status: str

