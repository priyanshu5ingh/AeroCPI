import os
import sys
import json
import hashlib
from datetime import date, datetime, timezone

# Add backend directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import SessionLocal, engine
from app.models.external_reference_data import ExternalReferenceData
from app.db.base import Base

OFFICIAL_MOSPI_AIRFARE_OBSERVATIONS = [
    {"month": "2025-01", "index": 115.05, "yoy": None},
    {"month": "2025-02", "index": 131.66, "yoy": None},
    {"month": "2025-03", "index": 108.19, "yoy": None},
    {"month": "2025-04", "index": 110.94, "yoy": None},
    {"month": "2025-05", "index": 110.92, "yoy": None},
    {"month": "2025-06", "index": 114.48, "yoy": None},
    {"month": "2025-07", "index": 102.05, "yoy": None},
    {"month": "2025-08", "index": 112.11, "yoy": None},
    {"month": "2025-09", "index": 105.22, "yoy": None},
    {"month": "2025-10", "index": 108.19, "yoy": None},
    {"month": "2025-11", "index": 121.45, "yoy": None},
    {"month": "2025-12", "index": 124.23, "yoy": None},
    {"month": "2026-01", "index": 122.71, "yoy": 6.66},
    {"month": "2026-02", "index": 122.43, "yoy": -7.01},
    {"month": "2026-03", "index": 123.55, "yoy": 14.20},
    {"month": "2026-04", "index": 123.27, "yoy": 11.11},
    {"month": "2026-05", "index": 127.62, "yoy": 15.06},
    {"month": "2026-06", "index": 126.09, "yoy": 10.14},
    {"month": "2026-07", "index": 125.46, "yoy": 22.94},
]

# Official CPI-2024 Expenditure Weight from Annexure 5.3d (Rural: 0.01166625 + Urban: 0.01784347 = Combined: 0.02950972)
OFFICIAL_CPI2024_AIRFARE_WEIGHT = 0.02950972 # Exact stored precision from Annexure 5.3d workbook

def seed_mospi_reference_data(db=None):
    close_db = False
    if db is None:
        print("Initializing database tables for MoSPI CPI-2024 reference data seeding...")
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        close_db = True

    try:
        # Compute canonical dataset hash
        canonical_str = json.dumps(OFFICIAL_MOSPI_AIRFARE_OBSERVATIONS, sort_keys=True)
        canonical_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

        print(f"Seeding {len(OFFICIAL_MOSPI_AIRFARE_OBSERVATIONS)} official CPI-2024 Airfare observations...")
        print(f"Canonical Dataset SHA-256: {canonical_hash}")

        # Remove existing records for this item to ensure clean deterministic reload
        db.query(ExternalReferenceData).filter(
            ExternalReferenceData.item_code == "07.3.3.1.2.01",
            ExternalReferenceData.series_type == "CURRENT"
        ).delete()
        db.commit()

        pub_date = date(2026, 1, 31)

        for obs in OFFICIAL_MOSPI_AIRFARE_OBSERVATIONS:
            m_str = obs["month"]
            idx_val = obs["index"]
            yoy_val = obs["yoy"]

            ref_record = ExternalReferenceData(
                reference_dataset_id="DS-MOSPI-CPI2024-AIRFARE",
                publisher="MoSPI / NSO",
                dataset_name="CPI-2024 Airfare Official Reference Series",
                source="MOSPI_CPI_CURRENT",
                reference_period=m_str,
                month=m_str,
                base_year=2024,
                series_type="CURRENT",
                geography="All India",
                sector="Combined",
                division_code="07",
                group_code="07.3",
                class_code="07.3.3",
                subclass_code="07.3.3.1",
                item_code="07.3.3.1.2.01",
                item_label="Airfare",
                index_value=idx_val,
                inflation_value=yoy_val,
                inflation_type="YOY",
                revision_status="FINAL",
                cpi_weight_value=OFFICIAL_CPI2024_AIRFARE_WEIGHT,
                cpi_weight_unit="percent_of_CPI",
                cpi_weight_scope="All India Combined",
                cpi_weight_source="MoSPI Expert Group Report — Annexure 5.3d",
                cpi_weight_source_document="Expert Group Report on Comprehensive Updation of Consumer Price Index, January 2026",
                publication_date=pub_date,
                data_status="OFFICIAL_SOURCE_DATA",
                provenance_status="PARTIAL",
                source_document="MoSPI eSankhyiki CPI Dataset Export & Expert Group Report (Jan 2026)",
                source_sheet="Annexure 5.3d",
                canonical_dataset_sha256=canonical_hash,
                notes="Official CPI-2024 CURRENT Airfare observations (2025-01 to 2026-07) retrieved from eSankhyiki export. Weight reconciled against Annexure 5.3d (Rural: 0.01166625, Urban: 0.01784347, Combined: 0.02950972)."
            )
            db.add(ref_record)

        db.commit()
        print(f"Successfully seeded {len(OFFICIAL_MOSPI_AIRFARE_OBSERVATIONS)} official MoSPI CPI-2024 Airfare records into database!")

    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    seed_mospi_reference_data()
