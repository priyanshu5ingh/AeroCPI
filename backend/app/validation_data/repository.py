from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.external_reference_data import ExternalReferenceData
from app.validation_data.schemas import ExternalReferenceDataRecord
from app.validation_data.interfaces import IReferenceDataProvider

class ValidationDataRepository(IReferenceDataProvider):
    """
    Database repository implementing the IReferenceDataProvider abstraction.
    Acts as the clean boundary between external validation data sources and the core index engine.
    """

    def __init__(self, db: Session):
        self.db = db

    def fetch_reference_records(
        self,
        reference_period: str,
        source: Optional[str] = None,
        series_type: str = "CURRENT"
    ) -> List[ExternalReferenceDataRecord]:
        """
        Fetch official reference records matching reference period.
        Filters by series_type="CURRENT" by default to prevent BACK series from leaking into primary benchmark queries.
        """
        query = self.db.query(ExternalReferenceData).filter(
            ExternalReferenceData.reference_period.startswith(reference_period[:7]),
            ExternalReferenceData.series_type == series_type
        )
        if source:
            query = query.filter(ExternalReferenceData.source == source)
        
        records = query.all()
        return [ExternalReferenceDataRecord.model_validate(r) for r in records]

    def get_mospi_airfare_series(
        self,
        item_code: str = "07.3.3.1.2.01",
        base_year: int = 2024,
        series_type: str = "CURRENT",
        geography: str = "All India",
        sector: str = "Combined"
    ) -> List[ExternalReferenceDataRecord]:
        """
        Retrieves the official MoSPI CPI-2024 Airfare series.
        Strictly filters series_type="CURRENT" to prevent linked/back series from contaminating the primary series.
        """
        records = self.db.query(ExternalReferenceData).filter(
            ExternalReferenceData.item_code == item_code,
            ExternalReferenceData.base_year == base_year,
            ExternalReferenceData.series_type == series_type,
            ExternalReferenceData.geography == geography,
            ExternalReferenceData.sector == sector
        ).order_by(ExternalReferenceData.reference_period.asc()).all()

        return [ExternalReferenceDataRecord.model_validate(r) for r in records]

    def get_mospi_airfare_for_month(
        self,
        month: str,
        item_code: str = "07.3.3.1.2.01",
        series_type: str = "CURRENT"
    ) -> Optional[ExternalReferenceDataRecord]:
        rec = self.db.query(ExternalReferenceData).filter(
            ExternalReferenceData.item_code == item_code,
            ExternalReferenceData.series_type == series_type,
            ExternalReferenceData.reference_period.startswith(month[:7])
        ).first()

        return ExternalReferenceDataRecord.model_validate(rec) if rec else None

    def get_route_reference_fare(
        self,
        route_id: str,
        reference_period: str
    ) -> Optional[float]:
        rec = self.db.query(ExternalReferenceData).filter(
            ExternalReferenceData.route_id == route_id,
            ExternalReferenceData.reference_period.startswith(reference_period[:7])
        ).first()
        return float(rec.average_fare) if rec and rec.average_fare is not None else None

    def get_route_passenger_traffic(
        self,
        route_id: str,
        reference_period: str
    ) -> Optional[int]:
        rec = self.db.query(ExternalReferenceData).filter(
            ExternalReferenceData.route_id == route_id,
            ExternalReferenceData.reference_period.startswith(reference_period[:7])
        ).first()
        return rec.passenger_traffic if rec else None
