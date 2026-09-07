import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, JSON
from app.db.base import Base

class VirtualTripSpecification(Base):
    __tablename__ = "virtual_trip_specifications"

    spec_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    origin = Column(String(10), nullable=False, index=True)
    destination = Column(String(10), nullable=False, index=True)
    travel_date = Column(Date, nullable=False, index=True)
    passengers = Column(Integer, nullable=False, default=1)
    cabin = Column(String(20), nullable=False, default="ECONOMY")
    trip_type = Column(String(20), nullable=False, default="ONE_WAY")
    booking_horizon = Column(Integer, ForeignKey("booking_horizons.horizon_days"), nullable=False, index=True)
    baggage_requirement = Column(String(100), nullable=False, default="15KG_CHECKIN_7KG_CARRYON")
    eligible_stop_type = Column(String(20), nullable=False, default="NON_STOP")
    fare_inclusion_rules = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
