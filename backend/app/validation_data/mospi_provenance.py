from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict

class MoSPIProvenanceRecord(BaseModel):
    """
    Provenance metadata record for MoSPI CPI-2024 Airfare Reference Series.
    Maintains strict separation between OFFICIAL_SOURCE_DATA (authenticity)
    and PARTIAL provenance status (uncaptured original eSankhyiki download URL).
    """
    source_organization: str = "MoSPI / NSO"
    source_document: str = "Expert Group Report on Comprehensive Updation of Consumer Price Index, January 2026"
    source_file: str = "eSankhyiki CPI-2024 Current Airfare Export & Annexure 5.3d"
    source_url: Optional[str] = None
    
    series_type: str = "CURRENT"
    base_year: int = 2024
    geography: str = "All India"
    sector: str = "Combined"
    item_code: str = "07.3.3.1.2.01"
    item_label: str = "Airfare"
    
    cpi_weight_value: float = 0.02950972 # Reconciled exact Annexure 5.3d weight (Rural: 0.01166625, Urban: 0.01784347, Combined: 0.02950972)
    cpi_weight_unit: str = "percent_of_CPI"
    cpi_weight_scope: str = "All India Combined"
    cpi_weight_source: str = "MoSPI Expert Group Report — Annexure 5.3d"
    
    coverage_start: str = "2025-01"
    coverage_end: str = "2026-07"
    observation_count: int = 19
    
    data_status: str = "OFFICIAL_SOURCE_DATA"
    provenance_status: str = "PARTIAL" # PARTIAL until live eSankhyiki API request chain is captured
    
    canonical_dataset_sha256: str
    source_file_sha256: Optional[str] = None
    retrieved_at: datetime
    verification_notes: str = (
        "Official CPI-2024 CURRENT Airfare observations (2025-01 to 2026-07) retrieved from "
        "the official eSankhyiki CPI dataset/export. Methodology and classification supported by "
        "MoSPI Expert Group Report (Jan 2026). Source authenticity verified; URL chain provenance is PARTIAL."
    )

    model_config = ConfigDict(from_attributes=True)
