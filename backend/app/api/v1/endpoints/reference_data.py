from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.validation_data.repository import ValidationDataRepository
from app.validation_data.schemas import ExternalReferenceDataRecord
from app.validation_data.mospi_provenance import MoSPIProvenanceRecord
from app.services.mospi_benchmark_service import MospiBenchmarkService

router = APIRouter()

@router.get("/reference/mospi/airfare", response_model=List[ExternalReferenceDataRecord])
def get_official_mospi_airfare_series(
    series_type: str = "CURRENT",
    db: Session = Depends(get_db)
):
    """
    Retrieves official MoSPI CPI-2024 Airfare reference series (Item 07.3.3.1.2.01).
    Strictly filters series_type='CURRENT' by default to prevent LINKED/BACK series contamination.
    """
    repo = ValidationDataRepository(db)
    records = repo.get_mospi_airfare_series(series_type=series_type)
    return records

@router.get("/reference/mospi/compare/{run_id}")
def compare_index_run_with_mospi_benchmark(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Compares an AeroCPI market-observed index run against official MoSPI CPI-2024 Airfare benchmark.
    Includes explicit safeguards clarifying this is a BENCHMARK COMPARISON between market-observed and official monthly CPI.
    """
    try:
        res = MospiBenchmarkService.compare_run_with_mospi_benchmark(db, run_id)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to perform benchmark comparison: {str(e)}")

@router.get("/reference/mospi/provenance", response_model=MoSPIProvenanceRecord)
def get_mospi_reference_provenance(
    db: Session = Depends(get_db)
):
    """
    Retrieves official provenance metadata for the MoSPI CPI-2024 Airfare series.
    Exposes OFFICIAL_SOURCE_DATA tag and PARTIAL provenance status (uncaptured original eSankhyiki download URL).
    """
    repo = ValidationDataRepository(db)
    records = repo.get_mospi_airfare_series()
    
    canonical_hash = records[0].canonical_dataset_sha256 if records and records[0].canonical_dataset_sha256 else "UNHASHED"
    cpi_weight = records[0].cpi_weight_value if records and records[0].cpi_weight_value else 0.02950972

    return MoSPIProvenanceRecord(
        cpi_weight_value=cpi_weight,
        canonical_dataset_sha256=canonical_hash,
        retrieved_at=records[0].download_timestamp or records[0].publication_date if records else None
    )
