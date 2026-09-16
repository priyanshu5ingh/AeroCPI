"""AeroGuide Airline x Route Coverage Matrix Model.
Enables consumers to see which carriers and sources are observed vs restricted on any domestic corridor.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Index
from datetime import datetime, timezone
from app.db.base import Base

class AirlineRouteCoverage(Base):
    __tablename__ = "airline_route_coverage"

    coverage_id = Column(String(50), primary_key=True, index=True) # e.g. "6E_DEL-BOM_SRC_GOOGLE_FLIGHTS"
    airline_id = Column(String(20), nullable=False, index=True) # "6E"
    route_id = Column(String(20), nullable=False, index=True) # "DEL-BOM"
    source_id = Column(String(40), nullable=False, index=True) # "SRC_GOOGLE_FLIGHTS"
    
    # Coverage States: OBSERVED, NOT_OBSERVED, SOURCE_UNAVAILABLE, ACCESS_RESTRICTED, NOT_SCHEDULED
    coverage_status = Column(String(30), nullable=False, default="OBSERVED", index=True)
    
    fare_observable = Column(Boolean, nullable=False, default=True)
    schedule_observable = Column(Boolean, nullable=False, default=True)
    availability_observable = Column(Boolean, nullable=False, default=False)
    access_method = Column(String(50), nullable=False, default="SEARCH_AGGREGATION")
    
    first_verified = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_verified = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    provenance = Column(String(255), nullable=False, default="VERIFIED_OBSERVATION_RUN")

__table_args__ = (
    Index("idx_coverage_route_airline", "route_id", "airline_id"),
)
AirlineRouteCoverage.__table_args__ = __table_args__
