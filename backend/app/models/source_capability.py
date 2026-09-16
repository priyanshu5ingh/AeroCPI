"""AeroGuide Source Capability Matrix Model.
Maintains operational telemetry, access tiers, and supported offer dimensions per source adapter.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, JSON
from datetime import datetime, timezone
from app.db.base import Base

class SourceCapability(Base):
    __tablename__ = "source_capabilities"

    source_id = Column(String(40), primary_key=True, index=True) # e.g. "SRC_INDIGO_NDC", "SRC_GOOGLE_FLIGHTS"
    source_name = Column(String(100), nullable=False)
    source_type = Column(String(30), nullable=False) # NDC_DIRECT, GDS_DIRECT, OTA_AGGREGATOR, SEARCH_ENGINE
    
    # Access & Security Constraints
    access_status = Column(String(40), nullable=False, default="NOT_CONFIGURED") # PUBLIC_UNRESTRICTED, AUTHORIZED_PARTNER, ACCESS_RESTRICTED, ACTIVE_SEARCH
    is_public_unrestricted = Column(Boolean, nullable=False, default=False)
    requires_partner_credentials = Column(Boolean, nullable=False, default=True)
    credentials_available = Column(Boolean, nullable=False, default=False)
    rate_limit_per_minute = Column(Integer, nullable=False, default=30)
    
    # Observable Dimensions
    fare_search_supported = Column(Boolean, nullable=False, default=True)
    domestic_supported = Column(Boolean, nullable=False, default=True)
    seat_availability_supported = Column(Boolean, nullable=False, default=False)
    ancillary_fare_supported = Column(Boolean, nullable=False, default=False)
    fare_breakdown_supported = Column(Boolean, nullable=False, default=False) # True if base + tax separated

    # Operational Telemetry
    health_status = Column(String(20), nullable=False, default="HEALTHY") # HEALTHY, DEGRADED, UNAVAILABLE, NOT_CONFIGURED
    availability_rate = Column(Float, nullable=False, default=1.0)
    successful_requests = Column(Integer, nullable=False, default=0)
    failed_requests = Column(Integer, nullable=False, default=0)
    median_response_time_ms = Column(Float, nullable=False, default=450.0)
    last_success = Column(DateTime(timezone=True), nullable=True)
    last_failure = Column(DateTime(timezone=True), nullable=True)
    provenance_doc_url = Column(String(255), nullable=True)
