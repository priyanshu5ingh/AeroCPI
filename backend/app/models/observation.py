import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, DateTime, Numeric, ForeignKey, JSON, Index, Integer
from app.db.base import Base

class Observation(Base):
    __tablename__ = "observations"

    observation_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(30), ForeignKey("sources.source_id"), nullable=False, index=True)
    route_id = Column(String(15), ForeignKey("routes.route_id"), nullable=False, index=True)
    carrier_id = Column(String(10), ForeignKey("carriers.carrier_id"), nullable=False, index=True)
    travel_date = Column(Date, nullable=False, index=True)
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    booking_horizon_days = Column(Integer, ForeignKey("booking_horizons.horizon_days"), nullable=False, index=True)
    cabin = Column(String(20), nullable=False, default="ECONOMY")
    fare_class = Column(String(20), nullable=True, default="STANDARD")
    trip_type = Column(String(20), nullable=False, default="ONE_WAY")
    base_fare = Column(Numeric(10, 2), nullable=False)
    taxes = Column(Numeric(10, 2), nullable=False)
    mandatory_fees = Column(Numeric(10, 2), nullable=False)
    total_fare = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    baggage_information = Column(JSON, nullable=True)
    stop_type = Column(String(20), nullable=False, default="NON_STOP")
    data_status = Column(String(20), nullable=False, default="OBSERVED", index=True)
    raw_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

__table_args__ = (
    Index("idx_obs_route_travel_date", "route_id", "travel_date"),
)
Observation.__table_args__ = __table_args__
