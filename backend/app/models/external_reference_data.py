import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, JSON
from app.db.base import Base

class ExternalReferenceData(Base):
    __tablename__ = "external_reference_data"

    reference_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String(100), nullable=False, index=True) # e.g., "DGCA_MONTHLY_REPORT"
    reference_period = Column(String(20), nullable=False, index=True) # e.g., "2026-08"
    route_id = Column(String(15), nullable=False, index=True) # e.g., "DEL-BOM"
    origin = Column(String(3), nullable=False)
    destination = Column(String(3), nullable=False)
    
    average_fare = Column(Float, nullable=True) # Benchmark average fare (INR)
    passenger_traffic = Column(Integer, nullable=True) # Passenger traffic volume
    publication_date = Column(Date, nullable=False) # Date published by official source
    data_status = Column(String(30), nullable=False, default="OFFICIAL") # Data status tag
    provenance_reference_url = Column(String(500), nullable=True) # Provenance source link / citation
    metadata_info = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
