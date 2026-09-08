from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base

class RouteBasket(Base):
    """
    Representative Route Basket container derived from DGCA passenger traffic volume.
    Explicitly labeled as "AeroCPI DGCA Traffic-Derived Route Basket" (NOT an official CPI basket).
    """
    __tablename__ = "route_baskets"

    basket_id = Column(String, primary_key=True, index=True) # e.g. "BASKET-DGCA-2025-TOP10"
    basket_name = Column(String, nullable=False)             # "AeroCPI DGCA Traffic-Derived Route Basket (Top 10)"
    reference_period_type = Column(String, default="CALENDAR_YEAR", nullable=False) # "CALENDAR_YEAR" / "ROLLING_12_MONTH" / "CUSTOM"
    reference_period_start = Column(String, nullable=False)  # "2025-01"
    reference_period_end = Column(String, nullable=False)    # "2025-12"
    selection_method = Column(String, default="TOP_N_TRAFFIC", nullable=False) # "TOP_N_TRAFFIC" / "TOP_N_TRAFFIC_BY_REGION"
    basket_size = Column(Integer, default=10, nullable=False)
    total_period_passengers = Column(Integer, nullable=False) # Total passengers across basket members
    source_dataset_id = Column(String, nullable=False)
    methodology_version = Column(String, default="AEROCPI_BASKET_V1_2026", nullable=False)
    relationship_to_mospi = Column(
        Text, 
        default="DGCA traffic is an experimental route-selection proxy informed by official MoSPI use of DGCA popular-route information.",
        nullable=False
    )
    status = Column(String, default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    members = relationship("RouteBasketMember", back_populates="basket", cascade="all, delete-orphan")


class RouteBasketMember(Base):
    """
    Member route of an AeroCPI representative RouteBasket.
    Calculates DGCA_TRAFFIC_PROXY_WEIGHT (passenger traffic share).
    Strictly separated from MoSPI CPI expenditure weights.
    """
    __tablename__ = "route_basket_members"

    member_id = Column(String, primary_key=True, index=True)
    basket_id = Column(String, ForeignKey("route_baskets.basket_id"), nullable=False, index=True)
    rank = Column(Integer, nullable=False) # 1, 2, 3, ...
    
    route_id = Column(String, nullable=False, index=True)            # e.g. "DEL-BOM"
    canonical_route_key = Column(String, nullable=False, index=True) # e.g. "DELHI::MUMBAI"
    city_1 = Column(String, nullable=False) # e.g. "DELHI"
    city_2 = Column(String, nullable=False) # e.g. "MUMBAI"
    origin_airport = Column(String, nullable=False)      # e.g. "DEL"
    destination_airport = Column(String, nullable=False) # e.g. "BOM"

    period_passengers = Column(Integer, nullable=False) # Total annual/period passenger volume
    traffic_share = Column(Float, nullable=False)       # DGCA_TRAFFIC_PROXY_WEIGHT (0.0 to 1.0)
    traffic_share_unit = Column(String, default="share_of_basket_traffic", nullable=False)
    
    selection_reason = Column(String, default="Highest observed DGCA passenger traffic volume in reference period", nullable=False)
    source_status = Column(String, default="PROVENANCE_PARTIAL", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    basket = relationship("RouteBasket", back_populates="members")
