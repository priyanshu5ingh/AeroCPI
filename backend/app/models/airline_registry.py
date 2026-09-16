"""AeroGuide Airline Registry Model.
Maintains national scheduled carriers, official NDC developer interfaces, and access constraints.
Distinguishes: DOCUMENTED -> ACCESSIBLE -> ACTUALLY_COLLECTED -> CURRENTLY_OBSERVED.
"""
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Integer
from datetime import datetime, timezone
from app.db.base import Base

class AirlineRegistry(Base):
    __tablename__ = "airline_registry"

    airline_id = Column(String(20), primary_key=True, index=True) # e.g. "AIRLINE_INDIGO"
    iata_code = Column(String(5), nullable=False, unique=True, index=True) # "6E"
    icao_code = Column(String(5), nullable=True) # "IGO"
    name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE") # ACTIVE, STANDBY, INACTIVE
    domestic_scheduled = Column(Boolean, nullable=False, default=True)
    direct_booking_url = Column(String(255), nullable=True)

    # NDC & API Capability Status
    official_api_available = Column(Boolean, nullable=False, default=False)
    ndc_available = Column(Boolean, nullable=False, default=False)
    ndc_portal_url = Column(String(255), nullable=True)
    api_access_type = Column(String(50), nullable=False, default="NOT_AVAILABLE") # PUBLIC_API, AUTHORIZED_PARTNER, GDS, WEB_SEARCH, NOT_AVAILABLE
    requires_authentication = Column(Boolean, nullable=False, default=True)
    partner_restriction = Column(Boolean, nullable=False, default=True)

    # Observable Offer Dimensions (when integrated)
    fare_data_available = Column(Boolean, nullable=False, default=True)
    seat_availability_available = Column(Boolean, nullable=False, default=False)
    ancillary_data_available = Column(Boolean, nullable=False, default=False)

    # 4-Tier Source State Flags
    is_documented = Column(Boolean, nullable=False, default=True)
    is_accessible = Column(Boolean, nullable=False, default=False) # False if system lacks partner credentials
    is_actually_collected = Column(Boolean, nullable=False, default=False) # True only if actively collected directly
    is_currently_observed = Column(Boolean, nullable=False, default=True) # True if observed via search aggregator

    # Provenance
    last_verified_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    verification_source = Column(String(255), nullable=False)
    verification_status = Column(String(30), nullable=False, default="VERIFIED") # VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED
