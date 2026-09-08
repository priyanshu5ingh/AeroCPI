from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime, timezone
from app.db.base import Base

class CityAirportMapping(Base):
    """
    Explicit identity mapping between raw DGCA city names, canonical cities,
    and AeroCPI airport/metro codes.
    Prevents ambiguous string matching and handles multi-airport metros explicitly.
    """
    __tablename__ = "city_airport_mappings"

    raw_city_name = Column(String, primary_key=True, index=True) # e.g. "NEW DELHI", "BOMBAY"
    canonical_city_name = Column(String, nullable=False, index=True) # e.g. "DELHI", "MUMBAI"
    primary_airport_code = Column(String, nullable=False, index=True) # e.g. "DEL", "BOM"
    metro_area_code = Column(String, nullable=False, index=True) # e.g. "DEL", "BOM"
    is_multi_airport = Column(Boolean, default=False, nullable=False)
    state_or_ut = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
