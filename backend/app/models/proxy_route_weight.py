from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, JSON
from app.db.base import Base

class ProxyRouteWeight(Base):
    __tablename__ = "proxy_route_weights"

    weight_version_id = Column(String(50), primary_key=True, nullable=False)
    route_id = Column(String(15), ForeignKey("routes.route_id"), primary_key=True, nullable=False, index=True)
    weight_share = Column(Numeric(8, 6), nullable=False)
    weight_type = Column(String(50), nullable=False, default="DGCA_TRAFFIC_SHARE_PROXY")
    is_demo = Column(Boolean, nullable=False, default=True)
    source_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
