from abc import ABC, abstractmethod
from typing import List, Optional
from app.validation_data.schemas import ExternalReferenceDataRecord

class IReferenceDataProvider(ABC):
    """
    Abstract interface contract for loading and validating external reference data.
    Provides placeholder methods for Milestone 3 ingestion without fabricating DGCA data.
    """

    @abstractmethod
    def fetch_reference_records(
        self,
        reference_period: str,
        source: Optional[str] = None
    ) -> List[ExternalReferenceDataRecord]:
        """Fetch all official reference records for a specified period and optional source."""
        pass

    @abstractmethod
    def get_route_reference_fare(
        self,
        route_id: str,
        reference_period: str
    ) -> Optional[float]:
        """Retrieve official published average fare for a route and period."""
        pass

    @abstractmethod
    def get_route_passenger_traffic(
        self,
        route_id: str,
        reference_period: str
    ) -> Optional[int]:
        """Retrieve official published passenger traffic for a route and period."""
        pass
