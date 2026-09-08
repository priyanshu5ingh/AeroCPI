import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, JSON
from app.db.base import Base

class ExternalReferenceData(Base):
    __tablename__ = "external_reference_data"

    reference_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference_dataset_id = Column(String(50), nullable=True, index=True)
    publisher = Column(String(100), nullable=False, default="MoSPI / NSO")
    dataset_name = Column(String(150), nullable=False, default="CPI-2024 Airfare Official Reference Series")
    
    source = Column(String(100), nullable=False, index=True) # e.g., "MOSPI_CPI_CURRENT"
    reference_period = Column(String(20), nullable=False, index=True) # e.g., "2026-07"
    month = Column(String(10), nullable=True) # e.g., "2026-07"
    
    base_year = Column(Integer, nullable=False, default=2024)
    series_type = Column(String(20), nullable=False, default="CURRENT", index=True) # "CURRENT" vs "BACK"
    geography = Column(String(50), nullable=False, default="All India")
    sector = Column(String(50), nullable=False, default="Combined")
    
    division_code = Column(String(10), nullable=True, default="07")
    group_code = Column(String(10), nullable=True, default="07.3")
    class_code = Column(String(15), nullable=True, default="07.3.3")
    subclass_code = Column(String(20), nullable=True, default="07.3.3.1")
    item_code = Column(String(20), nullable=False, default="07.3.3.1.2.01", index=True)
    item_label = Column(String(100), nullable=False, default="Airfare")
    
    index_value = Column(Float, nullable=True)
    inflation_value = Column(Float, nullable=True)
    inflation_type = Column(String(10), nullable=False, default="YOY") # Always YOY for MoSPI series
    revision_status = Column(String(20), nullable=False, default="FINAL")
    
    # Official CPI Weight Metadata (Annexure 5.3d)
    cpi_weight_value = Column(Float, nullable=True) # Official expenditure weight precision
    cpi_weight_unit = Column(String(30), nullable=False, default="percent_of_CPI")
    cpi_weight_scope = Column(String(50), nullable=False, default="All India Combined")
    cpi_weight_source = Column(String(150), nullable=False, default="MoSPI Expert Group Report — Annexure 5.3d")
    cpi_weight_source_document = Column(String(200), nullable=False, default="Expert Group Report on Comprehensive Updation of Consumer Price Index, January 2026")
    
    # Optional route-level fields for DGCA / route benchmarks
    route_id = Column(String(15), nullable=True, index=True)
    origin = Column(String(3), nullable=True)
    destination = Column(String(3), nullable=True)
    average_fare = Column(Float, nullable=True)
    passenger_traffic = Column(Integer, nullable=True)
    publication_date = Column(Date, nullable=False, default=date(2026, 1, 31))
    
    # Authenticity & Provenance Tracking
    data_status = Column(String(40), nullable=False, default="OFFICIAL_SOURCE_DATA")
    provenance_status = Column(String(30), nullable=False, default="PARTIAL")
    
    source_url = Column(String(500), nullable=True)
    source_document = Column(String(200), nullable=True, default="MoSPI eSankhyiki CPI Dataset Export & Expert Group Report (Jan 2026)")
    source_sheet = Column(String(50), nullable=True, default="Annexure 5.3d")
    download_timestamp = Column(DateTime(timezone=True), nullable=True)
    source_file_sha256 = Column(String(64), nullable=True) # Hash of original file if present
    canonical_dataset_sha256 = Column(String(64), nullable=True) # Hash of normalized imported dataset
    provenance_reference_url = Column(String(500), nullable=True)
    notes = Column(String(500), nullable=True)
    metadata_info = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
