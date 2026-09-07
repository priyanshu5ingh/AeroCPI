from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.observation import Observation
from app.models.carrier import Carrier
from app.models.route import Route
from app.models.source import Source
from app.models.booking_horizon import BookingHorizon
from app.schemas.observation import ObservationCreate, ObservationFilter
from app.services.normalization_service import NormalizationService
from app.services.quality_service import QualityService

class ObservationService:
    @staticmethod
    def ensure_reference_entities(db: Session, source_id: str, route_id: str, carrier_id: str, horizon_days: int):
        # Ensure Source exists
        source = db.query(Source).filter(Source.source_id == source_id).first()
        if not source:
            source = Source(
                source_id=source_id,
                source_name=source_id.replace("_", " ").title(),
                source_type="AIRLINE_DIRECT" if "DIRECT" in source_id else "OTA_AGGREGATOR",
                collection_policy="ETHICAL_PUBLIC_PERMITTED",
                active=True
            )
            db.add(source)

        # Ensure Carrier exists
        carrier = db.query(Carrier).filter(Carrier.carrier_id == carrier_id).first()
        if not carrier:
            carrier = Carrier(
                carrier_id=carrier_id,
                iata_code=carrier_id[:2].upper(),
                display_name=carrier_id.upper(),
                active=True
            )
            db.add(carrier)

        # Ensure Route exists
        route = db.query(Route).filter(Route.route_id == route_id).first()
        if not route:
            parts = route_id.split("-")
            origin = parts[0] if len(parts) > 0 else "UNKNOWN"
            dest = parts[1] if len(parts) > 1 else "UNKNOWN"
            route = Route(
                route_id=route_id,
                origin_code=origin,
                destination_code=dest,
                directionality="OUTBOUND",
                active=True
            )
            db.add(route)

        # Ensure BookingHorizon exists
        horizon = db.query(BookingHorizon).filter(BookingHorizon.horizon_days == horizon_days).first()
        if not horizon:
            horizon = BookingHorizon(
                horizon_days=horizon_days,
                horizon_code=f"T+{horizon_days}",
                description=f"{horizon_days} Days Lead Time"
            )
            db.add(horizon)

        db.flush()

    @classmethod
    def create_observation(cls, db: Session, obs_data: ObservationCreate) -> Observation:
        cls.ensure_reference_entities(
            db=db,
            source_id=obs_data.source_id,
            route_id=obs_data.route_id,
            carrier_id=obs_data.carrier_id,
            horizon_days=obs_data.booking_horizon_days
        )

        obs = Observation(
            source_id=obs_data.source_id,
            route_id=obs_data.route_id,
            carrier_id=obs_data.carrier_id,
            travel_date=obs_data.travel_date,
            observed_at=obs_data.observed_at,
            booking_horizon_days=obs_data.booking_horizon_days,
            cabin=obs_data.cabin,
            fare_class=obs_data.fare_class,
            trip_type=obs_data.trip_type,
            base_fare=obs_data.base_fare,
            taxes=obs_data.taxes,
            mandatory_fees=obs_data.mandatory_fees,
            total_fare=obs_data.total_fare,
            currency=obs_data.currency,
            baggage_information=obs_data.baggage_information,
            stop_type=obs_data.stop_type,
            data_status=obs_data.data_status.value if hasattr(obs_data.data_status, 'value') else str(obs_data.data_status),
            raw_reference=obs_data.raw_reference
        )

        db.add(obs)
        db.flush()

        # Run Normalization
        norm_result = NormalizationService.normalize_observation(obs)
        db.add(norm_result)

        # Run Quality Evaluation
        quality_result = QualityService.evaluate_quality(db, obs)
        db.add(quality_result)

        db.commit()
        db.refresh(obs)
        return obs

    @staticmethod
    def get_observation_by_id(db: Session, observation_id: str) -> Optional[Observation]:
        return db.query(Observation).filter(Observation.observation_id == observation_id).first()

    @staticmethod
    def get_observations(db: Session, filters: ObservationFilter) -> List[Observation]:
        query = db.query(Observation)
        if filters.route_id:
            query = query.filter(Observation.route_id == filters.route_id)
        if filters.carrier_id:
            query = query.filter(Observation.carrier_id == filters.carrier_id)
        if filters.booking_horizon_days:
            query = query.filter(Observation.booking_horizon_days == filters.booking_horizon_days)
        if filters.data_status:
            status_str = filters.data_status.value if hasattr(filters.data_status, 'value') else str(filters.data_status)
            query = query.filter(Observation.data_status == status_str)
        if filters.travel_date:
            query = query.filter(Observation.travel_date == filters.travel_date)

        return query.order_by(Observation.observed_at.desc()).offset(filters.offset).limit(filters.limit).all()
