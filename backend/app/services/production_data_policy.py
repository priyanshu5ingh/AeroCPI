"""Production data policy for AeroCPI."""
from __future__ import annotations

from typing import Any

from app.models.observation import Observation


class ProductionDataPolicy:
    """Single source of truth for the empirical forecasting boundary."""

    OBSERVED_STATUS = "OBSERVED"
    ACCEPTED_VALIDATION = "ACCEPT"
    ELIGIBLE_INDEX = "ELIGIBLE"

    @classmethod
    def is_production_observation(cls, observation: Observation) -> bool:
        if getattr(observation, "data_status", None) == "SYNTHETIC":
            return False
        if getattr(observation, "capture_method", None) == "SYNTHETIC":
            return False
            
        return (
            getattr(observation, "data_status", None) == cls.OBSERVED_STATUS
            and getattr(observation, "validation_status", None) == cls.ACCEPTED_VALIDATION
            and getattr(observation, "index_eligibility", None) == cls.ELIGIBLE_INDEX
        )

    @classmethod
    def apply_forecasting_filters(cls, query: Any) -> Any:
        return query.filter(
            Observation.data_status == cls.OBSERVED_STATUS,
            Observation.validation_status == cls.ACCEPTED_VALIDATION,
            Observation.index_eligibility == cls.ELIGIBLE_INDEX,
            Observation.capture_method != "SYNTHETIC"
        )
