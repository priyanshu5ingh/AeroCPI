from sqlalchemy import Column, String, Boolean
from app.db.base import Base

class Carrier(Base):
    __tablename__ = "carriers"

    carrier_id = Column(String(10), primary_key=True, index=True)
    iata_code = Column(String(10), nullable=True)
    display_name = Column(String(100), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
