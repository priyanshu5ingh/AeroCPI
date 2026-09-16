"""AeroGuide Versioned Decision Policy Configuration.
Decouples heuristics from application code and enables empirical benchmarking.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any

class DecisionPolicyConfig(BaseModel):
    policy_version: str = "DECISION_POLICY_V1"
    policy_type: str = "HEURISTIC_PRE_VALIDATION"
    description: str = "Initial heuristic decision policy awaiting empirical walk-forward calibration."
    
    # Percentile Thresholds
    book_percentile: float = Field(default=15.0, description="Fares at or below this percentile trigger BOOK consideration if market is rising.")
    wait_percentile: float = Field(default=80.0, description="Fares at or above this percentile trigger WAIT consideration if lead time is sufficient.")
    
    # Lead Time & Movement Parameters
    wait_min_lead_days: int = Field(default=21, description="Minimum days to departure required to safely recommend WAIT.")
    flex_date_threshold_pct: float = Field(default=15.0, description="Minimum percentage discount on adjacent date to trigger FLEX_DATE.")
    stable_threshold_pct: float = Field(default=3.0, description="Movement within +/- 3% classified as STABLE.")
    
    # Standard Passenger Context
    standard_passenger_context: Dict[str, Any] = Field(
        default_factory=lambda: {
            "adults": 1,
            "children": 0,
            "infants": 0,
            "cabin": "ECONOMY",
            "currency": "INR",
            "trip_type": "ONE_WAY"
        }
    )

# Active Global Default Policy
ACTIVE_DECISION_POLICY = DecisionPolicyConfig()
