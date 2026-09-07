from app.models.observation import Observation
from app.models.normalization_result import NormalizationResult

class NormalizationService:
    @staticmethod
    def normalize_observation(observation: Observation) -> NormalizationResult:
        if observation.currency.upper() != "INR":
            raise ValueError(f"Unsupported currency '{observation.currency}'. AeroCPI strictly requires INR and prohibits silent currency conversions.")
        
        base_fare = float(observation.base_fare)
        taxes = float(observation.taxes)
        mandatory_fees = float(observation.mandatory_fees)

        # Deterministic formula: normalized_total = base_fare + taxes + mandatory_fees
        normalized_total = round(base_fare + taxes + mandatory_fees, 2)

        return NormalizationResult(
            observation_id=observation.observation_id,
            base_fare=base_fare,
            taxes=taxes,
            mandatory_fees=mandatory_fees,
            included_fare_components=[
                {"name": "BASE_FARE", "amount": base_fare, "currency": observation.currency},
                {"name": "TAXES", "amount": taxes, "currency": observation.currency},
                {"name": "MANDATORY_FEES", "amount": mandatory_fees, "currency": observation.currency},
            ],
            normalized_total=normalized_total,
            exclusions=[],
            normalization_version="V1_SIMPLE_SUM"
        )
