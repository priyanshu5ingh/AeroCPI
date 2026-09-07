from pydantic import BaseModel

class QualitySummaryResponse(BaseModel):
    total_observations: int
    eligible_observations: int
    excluded_observations: int
    valid_observations: int
    outlier_flagged_observations: int
    retained_with_warning_observations: int
    duplicate_observations: int
    missing_incomplete_observations: int
    coverage_ratio: float
    expected_route_horizon_pairs: int = 40
    calculated_route_horizon_pairs: int = 0
    unavailable_route_horizon_pairs: int = 0
