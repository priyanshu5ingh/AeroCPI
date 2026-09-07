import uuid
from sqlalchemy import Column, String, Numeric, ForeignKey
from app.db.base import Base

class FareComponent(Base):
    __tablename__ = "fare_components"

    component_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    observation_id = Column(String(36), ForeignKey("observations.observation_id"), nullable=False, index=True)
    component_name = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
