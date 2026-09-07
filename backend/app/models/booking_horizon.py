from sqlalchemy import Column, Integer, String
from app.db.base import Base

class BookingHorizon(Base):
    __tablename__ = "booking_horizons"

    horizon_days = Column(Integer, primary_key=True, index=True)
    horizon_code = Column(String(10), nullable=False)
    description = Column(String(100), nullable=True)
