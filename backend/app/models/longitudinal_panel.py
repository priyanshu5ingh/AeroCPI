"""AeroGuide Longitudinal Panel Manifest & Source Price Comparison Models.
Tracks rolling pinned travel date trajectories and deterministic cross-source comparability.
"""
from sqlalchemy import Column, String, Date, DateTime, Integer, Float, Boolean, JSON, Index
from datetime import datetime, timezone
from app.db.base import Base

class LongitudinalPanelManifest(Base):
    __tablename__ = "longitudinal_panel_manifest"

    manifest_id = Column(String(50), primary_key=True, index=True) # e.g. "PANEL_DEL-BOM_2026-10-15"
    route_id = Column(String(20), nullable=False, index=True)
    travel_date = Column(Date, nullable=False, index=True)
    
    first_observed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_observed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    search_count = Column(Integer, nullable=False, default=1)
    search_dates = Column(JSON, nullable=False, default=list) # List of ISO date strings
    observation_count = Column(Integer, nullable=False, default=0)
    history_span_days = Column(Integer, nullable=False, default=0)
    
    # Target Construction Eligibility Flags
    has_3_searches = Column(Boolean, nullable=False, default=False)
    has_7_day_pair = Column(Boolean, nullable=False, default=False)
    has_14_day_pair = Column(Boolean, nullable=False, default=False)
    eligible_for_forecasting = Column(Boolean, nullable=False, default=False, index=True)
    
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

__table_args__ = (
    Index("idx_panel_route_travel_date", "route_id", "travel_date", unique=True),
)
LongitudinalPanelManifest.__table_args__ = __table_args__


class SourcePriceComparison(Base):
    __tablename__ = "source_price_comparisons"

    comparison_id = Column(String(64), primary_key=True, index=True)
    route_id = Column(String(20), nullable=False, index=True)
    travel_date = Column(Date, nullable=False, index=True)
    carrier = Column(String(20), nullable=False, index=True)
    
    source_a = Column(String(40), nullable=False) # e.g. "SRC_INDIGO_DIRECT"
    source_b = Column(String(40), nullable=False) # e.g. "SRC_GOOGLE_FLIGHTS"
    
    fare_a = Column(Float, nullable=False)
    fare_b = Column(Float, nullable=False)
    difference = Column(Float, nullable=False)
    difference_pct = Column(Float, nullable=False)
    
    comparison_timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Comparability Status: COMPARABLE, PARTIALLY_COMPARABLE, NOT_COMPARABLE
    comparability_status = Column(String(30), nullable=False, default="COMPARABLE")
    comparability_reasons = Column(JSON, nullable=False, default=list)
    passenger_configuration = Column(JSON, nullable=False, default=lambda: {"adults": 1, "children": 0, "infants": 0, "cabin": "ECONOMY", "currency": "INR"})
