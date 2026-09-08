from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base

class DGCAReferenceDataset(Base):
    """
    Metadata container for official DGCA monthly domestic city-pair traffic reference series.
    """
    __tablename__ = "dgca_reference_datasets"

    dataset_id = Column(String, primary_key=True, index=True) # e.g. "DS-DGCA-TRAFFIC-2025"
    publisher = Column(String, default="DGCA", nullable=False) # Always "DGCA"
    dataset_name = Column(String, nullable=False)
    reference_period_start = Column(String, nullable=False) # e.g. "2025-01"
    reference_period_end = Column(String, nullable=False)   # e.g. "2025-12"
    months_expected = Column(Integer, default=12, nullable=False)
    months_available = Column(Integer, default=0, nullable=False)
    months_missing = Column(Text, nullable=True) # JSON list string of missing months
    completeness_status = Column(String, default="INCOMPLETE", nullable=False) # "COMPLETE" / "INCOMPLETE"
    source_status = Column(String, default="PROVENANCE_PARTIAL", nullable=False) # "OFFICIAL_SOURCE_FILE" / "PROVENANCE_PARTIAL" / "SECONDARY_DERIVATION"
    canonical_dataset_sha256 = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    observations = relationship("DGCARouteMonthObservation", back_populates="dataset", cascade="all, delete-orphan")


class DGCARawObservation(Base):
    """
    Verbatim raw source rows from DGCA monthly traffic workbooks/CSVs.
    Preserves exact un-normalized inputs, including raw dash ('-') strings.
    """
    __tablename__ = "dgca_raw_observations"

    raw_id = Column(String, primary_key=True, index=True)
    dataset_id = Column(String, ForeignKey("dgca_reference_datasets.dataset_id"), nullable=False, index=True)
    source_filename = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    source_row_index = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    raw_city1 = Column(String, nullable=False)
    raw_city2 = Column(String, nullable=False)
    raw_pax_to = Column(String, nullable=True)   # Raw string before coercion (e.g. "45120", "-")
    raw_pax_from = Column(String, nullable=True) # Raw string before coercion
    raw_freight_to = Column(String, nullable=True)
    raw_freight_from = Column(String, nullable=True)
    raw_mail_to = Column(String, nullable=True)
    raw_mail_from = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class DGCARouteMonthObservation(Base):
    """
    Normalized, deduplicated route-month passenger traffic observation.
    Merged across reverse-direction rows (A->B and B->A) within the same month
    to guarantee NO double-counting of traffic.
    """
    __tablename__ = "dgca_route_month_observations"

    obs_id = Column(String, primary_key=True, index=True)
    dataset_id = Column(String, ForeignKey("dgca_reference_datasets.dataset_id"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    reference_period = Column(String, nullable=False, index=True) # "YYYY-MM"
    
    canonical_route_key = Column(String, nullable=False, index=True) # e.g. "DELHI::MUMBAI"
    city1_code = Column(String, nullable=False) # Canonical city 1
    city2_code = Column(String, nullable=False) # Canonical city 2
    origin_airport = Column(String, nullable=False)      # e.g. "DEL"
    destination_airport = Column(String, nullable=False) # e.g. "BOM"

    passengers_city1_to_city2 = Column(Integer, nullable=True)
    passengers_city2_to_city1 = Column(Integer, nullable=True)
    combined_passengers = Column(Integer, nullable=True)

    freight_tons = Column(Float, nullable=True)
    mail_tons = Column(Float, nullable=True)

    aggregation_mode = Column(String, default="BIDIRECTIONAL_MERGED", nullable=False) # "SINGLE_ROW_PAIR" / "BIDIRECTIONAL_MERGED"
    deduplication_status = Column(String, default="DEDUPLICATED", nullable=False)
    raw_passenger_value = Column(String, nullable=True) # Original raw input string or notes
    normalization_reason = Column(String, nullable=True) # e.g. "PARSED_OK", "SOURCE_SYMBOL_DASH"
    source_status = Column(String, default="PROVENANCE_PARTIAL", nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    dataset = relationship("DGCAReferenceDataset", back_populates="observations")


class DGCAIngestionRun(Base):
    """
    Audit log record for DGCA monthly ingestion execution runs.
    """
    __tablename__ = "dgca_ingestion_runs"

    ingestion_id = Column(String, primary_key=True, index=True)
    dataset_id = Column(String, nullable=False)
    run_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    source_files_count = Column(Integer, nullable=False)
    raw_records_count = Column(Integer, nullable=False)
    normalized_records_count = Column(Integer, nullable=False)
    unique_routes_count = Column(Integer, nullable=False)
    parser_version = Column(String, default="DGCA_PARSER_V1_2026", nullable=False)
    status = Column(String, default="SUCCESS", nullable=False)
    ingestion_notes = Column(Text, nullable=True)


class DGCAProvenanceRecord(Base):
    """
    Provenance tracking record for DGCA monthly statistics datasets.
    """
    __tablename__ = "dgca_provenance_records"

    provenance_id = Column(String, primary_key=True, index=True)
    dataset_id = Column(String, nullable=False, index=True)
    publisher = Column(String, default="DGCA", nullable=False)
    source_type = Column(String, default="OFFICIAL_DGCA_S3", nullable=False)
    source_url = Column(String, nullable=True)
    secondary_discovery_repo = Column(String, default="Vonter/india-aviation-traffic", nullable=True)
    download_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    source_file_sha256 = Column(String, nullable=False)
    canonical_dataset_sha256 = Column(String, nullable=False)
    parser_version = Column(String, default="DGCA_PARSER_V1_2026", nullable=False)
    schema_version = Column(String, default="DGCA_SCHEMA_V1", nullable=False)
    source_status = Column(String, default="PROVENANCE_PARTIAL", nullable=False)
    verification_notes = Column(Text, nullable=True)
