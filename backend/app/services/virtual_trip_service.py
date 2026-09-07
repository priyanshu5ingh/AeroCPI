from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.virtual_trip import VirtualTripSpecification
from app.models.booking_horizon import BookingHorizon
from app.schemas.virtual_trip import VirtualTripCreate

class VirtualTripService:
    @staticmethod
    def create_virtual_trip(db: Session, trip_data: VirtualTripCreate) -> VirtualTripSpecification:
        # Ensure BookingHorizon exists
        horizon = db.query(BookingHorizon).filter(BookingHorizon.horizon_days == trip_data.booking_horizon).first()
        if not horizon:
            horizon = BookingHorizon(
                horizon_days=trip_data.booking_horizon,
                horizon_code=f"T+{trip_data.booking_horizon}",
                description=f"{trip_data.booking_horizon} Days Lead Time"
            )
            db.add(horizon)
            db.flush()

        v_trip = VirtualTripSpecification(
            origin=trip_data.origin,
            destination=trip_data.destination,
            travel_date=trip_data.travel_date,
            passengers=trip_data.passengers,
            cabin=trip_data.cabin,
            trip_type=trip_data.trip_type,
            booking_horizon=trip_data.booking_horizon,
            baggage_requirement=trip_data.baggage_requirement,
            eligible_stop_type=trip_data.eligible_stop_type,
            fare_inclusion_rules=trip_data.fare_inclusion_rules
        )

        db.add(v_trip)
        db.commit()
        db.refresh(v_trip)
        return v_trip

    @staticmethod
    def get_virtual_trip_by_id(db: Session, spec_id: str) -> Optional[VirtualTripSpecification]:
        return db.query(VirtualTripSpecification).filter(VirtualTripSpecification.spec_id == spec_id).first()

    @staticmethod
    def get_virtual_trips(db: Session, limit: int = 50, offset: int = 0) -> List[VirtualTripSpecification]:
        return db.query(VirtualTripSpecification).order_by(VirtualTripSpecification.created_at.desc()).offset(offset).limit(limit).all()
