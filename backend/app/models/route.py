from sqlalchemy import Column, String, Boolean
from app.db.base import Base

class Route(Base):
    __tablename__ = "routes"

    route_id = Column(String(15), primary_key=True, index=True)
    origin_code = Column(String(10), nullable=False, index=True)
    destination_code = Column(String(10), nullable=False, index=True)
    directionality = Column(String(20), nullable=False, default="OUTBOUND")
    active = Column(Boolean, default=True, nullable=False)
