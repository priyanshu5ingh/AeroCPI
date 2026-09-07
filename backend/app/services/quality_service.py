from sqlalchemy.orm import Session
from app.models.observation import Observation
from app.models.quality_result import QualityResult

class QualityService:
    @staticmethod
    def evaluate_quality(db: Session, observation: Observation) -> QualityResult:
        # Check for duplicates: identical route, carrier, travel_date, horizon, source, total_fare ingested previously
        existing_dup = db.query(Observation).filter(
            Observation.route_id == observation.route_id,
            Observation.carrier_id == observation.carrier_id,
            Observation.travel_date == observation.travel_date,
            Observation.booking_horizon_days == observation.booking_horizon_days,
            Observation.source_id == observation.source_id,
            Observation.total_fare == observation.total_fare,
            Observation.observation_id != observation.observation_id
        ).first()

        is_duplicate = existing_dup is not None

        return QualityResult(
            observation_id=observation.observation_id,
            eligible=not is_duplicate,
            duplicate_flag=is_duplicate,
            missing_data_flag=False,
            outlier_status="VALID",
            exclusion_reason="DUPLICATE_OBSERVATION" if is_duplicate else None,
            quality_rule_version="V1_BASIC_CHECKS"
        )
