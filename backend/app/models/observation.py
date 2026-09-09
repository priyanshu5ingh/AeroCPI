import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, DateTime, Numeric, ForeignKey, JSON, Index, Integer
from app.db.base import Base

class Observation(Base):
    __tablename__ = "observations"

    observation_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(30), ForeignKey("sources.source_id"), nullable=False, index=True)
    source_name = Column(String(100), nullable=True)
    source_url = Column(String(500), nullable=True)

    collected_at = Column(DateTime(timezone=True), nullable=True, index=True)
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True) # Backwards compatible
    search_timestamp = Column(DateTime(timezone=True), nullable=True, index=True) # Authoritative collection event timestamp
    search_date = Column(Date, nullable=True, index=True)
    travel_date = Column(Date, nullable=False, index=True)
    advance_purchase_days = Column(Integer, nullable=True, index=True)
    booking_horizon_days = Column(Integer, ForeignKey("booking_horizons.horizon_days"), nullable=False, index=True) # Backwards compatible

    origin_raw = Column(String(100), nullable=True)
    destination_raw = Column(String(100), nullable=True)
    origin_airport = Column(String(10), nullable=True, index=True)
    destination_airport = Column(String(10), nullable=True, index=True)
    route_id = Column(String(15), ForeignKey("routes.route_id"), nullable=False, index=True)
    carrier_id = Column(String(10), ForeignKey("carriers.carrier_id"), nullable=False, index=True)
    airline = Column(String(50), nullable=True, index=True)
    flight_number = Column(String(30), nullable=True)

    cabin = Column(String(20), nullable=False, default="ECONOMY")
    fare_class = Column(String(20), nullable=True, default="STANDARD")
    trip_type = Column(String(20), nullable=False, default="ONE_WAY")
    stops = Column(Integer, nullable=True) # NULL if missing, 0 only if observed non-stop
    stops_status = Column(String(20), nullable=True, default="MISSING")
    duration_minutes = Column(Integer, nullable=True)

    raw_total_fare = Column(String(100), nullable=True)
    raw_base_fare = Column(String(100), nullable=True)
    raw_taxes = Column(String(100), nullable=True)
    raw_fees = Column(String(100), nullable=True)

    base_fare = Column(Numeric(10, 2), nullable=True)
    taxes = Column(Numeric(10, 2), nullable=True)
    mandatory_fees = Column(Numeric(10, 2), nullable=True)
    fees = Column(Numeric(10, 2), nullable=True) # Synonym/Alias for mandatory_fees
    total_fare = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    baggage_information = Column(JSON, nullable=True)
    stop_type = Column(String(20), nullable=False, default="NON_STOP")

    raw_payload_hash = Column(String(64), nullable=True) # Backwards compatible
    raw_payload_sha256 = Column(String(64), nullable=True, index=True) # Hash of uncompressed source payload
    stored_file_sha256 = Column(String(64), nullable=True, index=True) # Hash of persisted/compressed artifact
    observation_key = Column(String(255), nullable=True, index=True) # Flight/Search Context identity
    quote_fingerprint = Column(String(64), nullable=True, index=True) # Payload identity

    breakdown_status = Column(String(30), nullable=True, default="TOTAL_ONLY")
    arithmetic_status = Column(String(30), nullable=True, default="ARITHMETIC_UNCHECKABLE")
    horizon_code = Column(String(20), nullable=True, default="OFF_HORIZON", index=True)
    route_mapping_status = Column(String(30), nullable=True, default="CANONICAL_MAPPED")
    basket_status = Column(String(40), nullable=True, default="ROUTE_OUTSIDE_REFERENCE_BASKET")
    validation_status = Column(String(20), nullable=False, default="ACCEPT", index=True)
    validation_reasons = Column(JSON, nullable=True)
    data_status = Column(String(20), nullable=False, default="OBSERVED", index=True)
    raw_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

__table_args__ = (
    Index("idx_obs_route_travel_date", "route_id", "travel_date"),
    Index("idx_obs_observation_key", "observation_key"),
    Index("idx_obs_quote_fingerprint", "quote_fingerprint"),
)
Observation.__table_args__ = __table_args__
