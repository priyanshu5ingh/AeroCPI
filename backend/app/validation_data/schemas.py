from datetime import date, datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.schemas.common import DataStatus

class ExternalReferenceDataRecord(BaseModel):
    """
    Validation-data domain abstraction for external benchmark & reference data.
    Represents published statistics from authorities (e.g. DGCA, MoSPI).
    """
    reference_id: Optional[str] = None
    source: str # e.g., "DGCA_MONTHLY_REPORT", "MOSPI_CPI_AIRFARE_INDEX"
    reference_period: str # e.g., "2026-08" or "2026-08-01"
    route_id: str # e.g., "DEL-BOM"
    origin: str # e.g., "DEL"
    destination: str # e.g., "BOM"
    
    average_fare: Optional[float] = None # Published average fare (INR)
    passenger_traffic: Optional[int] = None # Passenger traffic volume
    publication_date: date # Publication date of the official report
    data_status: DataStatus = DataStatus.OFFICIAL
    provenance_reference_url: Optional[str] = None # Citation URL / PDF reference
    metadata_info: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
