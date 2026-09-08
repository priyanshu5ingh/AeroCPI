from datetime import date, datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class ExternalReferenceDataRecord(BaseModel):
    """
    Validation-data domain abstraction for external benchmark & reference data.
    Represents published statistics from authorities (e.g., MoSPI CPI-2024, DGCA).
    """
    reference_id: Optional[str] = None
    reference_dataset_id: Optional[str] = "DS-MOSPI-CPI2024-AIRFARE"
    publisher: str = "MoSPI / NSO"
    dataset_name: str = "CPI-2024 Airfare Official Reference Series"
    
    source: str = "MOSPI_CPI_CURRENT"
    reference_period: str # e.g., "2026-07"
    month: Optional[str] = None # e.g., "2026-07"
    
    base_year: int = 2024
    series_type: str = "CURRENT" # "CURRENT" vs "BACK"
    geography: str = "All India"
    sector: str = "Combined"
    
    division_code: Optional[str] = "07"
    group_code: Optional[str] = "07.3"
    class_code: Optional[str] = "07.3.3"
    subclass_code: Optional[str] = "07.3.3.1"
    item_code: str = "07.3.3.1.2.01"
    item_label: str = "Airfare"
    
    index_value: Optional[float] = None
    inflation_value: Optional[float] = None
    inflation_type: str = "YOY"
    revision_status: str = "FINAL"
    
    # Official CPI Weight Metadata (Annexure 5.3d)
    cpi_weight_value: Optional[float] = None
    cpi_weight_unit: str = "percent_of_CPI"
    cpi_weight_scope: str = "All India Combined"
    cpi_weight_source: str = "MoSPI Expert Group Report — Annexure 5.3d"
    cpi_weight_source_document: str = "Expert Group Report on Comprehensive Updation of Consumer Price Index, January 2026"
    
    # Optional route-level fields for DGCA / route benchmarks
    route_id: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    average_fare: Optional[float] = None
    passenger_traffic: Optional[int] = None
    publication_date: Optional[date] = None
    
    # Authenticity & Provenance Tracking
    data_status: str = "OFFICIAL_SOURCE_DATA"
    provenance_status: str = "PARTIAL"
    
    source_url: Optional[str] = None
    source_document: Optional[str] = "MoSPI eSankhyiki CPI Dataset Export & Expert Group Report (Jan 2026)"
    source_sheet: Optional[str] = "Annexure 5.3d"
    download_timestamp: Optional[datetime] = None
    source_file_sha256: Optional[str] = None
    canonical_dataset_sha256: Optional[str] = None
    provenance_reference_url: Optional[str] = None
    notes: Optional[str] = None
    metadata_info: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
