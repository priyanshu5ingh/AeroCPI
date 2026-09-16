"""AeroGuide National Route Universe Model.
Scales across 4 tiers without modifying AeroCPI's 10-corridor statistical basket.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Index
from datetime import datetime, timezone
from app.db.base import Base

class RouteUniverse(Base):
    __tablename__ = "route_universe"

    route_id = Column(String(20), primary_key=True, index=True) # e.g. "DEL-BOM"
    canonical_origin_airport = Column(String(10), nullable=False, index=True) # "DEL"
    canonical_destination_airport = Column(String(10), nullable=False, index=True) # "BOM"
    city_pair = Column(String(50), nullable=False, index=True) # "Delhi-Mumbai"
    directionality = Column(String(20), nullable=False, default="OUTBOUND") # OUTBOUND, INBOUND, BIDIRECTIONAL
    
    # 4-Tier Classification (Tiers 2-4 are AeroGuide Market Coverage, NOT CPI Weights)
    tier = Column(String(30), nullable=False, default="TIER_2_NATIONAL_HIGH_TRAFFIC", index=True)
    # TIER_1_DGCA_CORE, TIER_2_NATIONAL_HIGH_TRAFFIC, TIER_3_REGIONAL_CONNECTIVITY, TIER_4_DYNAMIC_DISCOVERY
    
    is_cpi_basket_member = Column(Boolean, nullable=False, default=False, index=True)
    active_status = Column(String(20), nullable=False, default="ACTIVE") # ACTIVE, SEASONAL, INACTIVE
    
    dgca_annual_passenger_share = Column(String(20), nullable=True) # e.g. "17.8%" for Tier 1
    source_of_route = Column(String(100), nullable=False, default="DGCA_OFFICIAL_TRAFFIC_SCHEDULE")
    
    first_seen = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

__table_args__ = (
    Index("idx_route_universe_pair_tier", "canonical_origin_airport", "canonical_destination_airport", "tier"),
)
RouteUniverse.__table_args__ = __table_args__
