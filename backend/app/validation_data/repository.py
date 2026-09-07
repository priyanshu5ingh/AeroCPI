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
        source: Optional[str] = None
    ) -> List[ExternalReferenceDataRecord]:
        query = self.db.query(ExternalReferenceData).filter(
            ExternalReferenceData.reference_period.startswith(reference_period[:7])
        )
        if source:
            query = query.filter(ExternalReferenceData.source == source)
        
        records = query.all()
        return [ExternalReferenceDataRecord.model_validate(r) for r in records]

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
