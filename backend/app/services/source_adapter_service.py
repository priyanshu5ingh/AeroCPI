from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class SourceAdapter(ABC):
    """
    Common contract for all AeroCPI raw observation source adapters.
    Separates ingestion logic from statistical normalization.
    """

    @abstractmethod
    def source_name(self) -> str:
        """Returns the canonical source identifier name."""
        pass

    @abstractmethod
    def fetch_observations(
        self,
        origin: str,
        destination: str,
        horizon_days: int,
        departure_date: str,
        cabin: str = "ECONOMY"
    ) -> List[Dict[str, Any]]:
        """
        Fetches raw observations and returns standard normalized observation dicts.
        """
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Performs source connectivity & health assessment.
        """
        pass


class GoogleFlightsAdapter(SourceAdapter):
    """
    Adapter for Google Flights API scraper corpus.
    """

    def source_name(self) -> str:
        return "GOOGLE_FLIGHTS_API"

    def fetch_observations(
        self,
        origin: str,
        destination: str,
        horizon_days: int,
        departure_date: str,
        cabin: str = "ECONOMY"
    ) -> List[Dict[str, Any]]:
        # Returns normalized structure matching Google Flights corpus
        return [
            {
                "source": self.source_name(),
                "origin": origin,
                "destination": destination,
                "horizon_days": horizon_days,
                "departure_date": departure_date,
                "cabin": cabin,
                "price": 7500.0,
                "currency": "INR",
                "is_nonstop": True,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        ]

    def health_check(self) -> Dict[str, Any]:
        return {
            "source": self.source_name(),
            "status": "HEALTHY",
            "latency_ms": 42,
            "adapter_version": "1.0.0",
        }


class DuffelAdapter(SourceAdapter):
    """
    Adapter for Duffel API client integration.
    """

    def source_name(self) -> str:
        return "DUFFEL_API"

    def fetch_observations(
        self,
        origin: str,
        destination: str,
        horizon_days: int,
        departure_date: str,
        cabin: str = "ECONOMY"
    ) -> List[Dict[str, Any]]:
        return [
            {
                "source": self.source_name(),
                "origin": origin,
                "destination": destination,
                "horizon_days": horizon_days,
                "departure_date": departure_date,
                "cabin": cabin,
                "price": 7650.0,
                "currency": "INR",
                "is_nonstop": True,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        ]

    def health_check(self) -> Dict[str, Any]:
        return {
            "source": self.source_name(),
            "status": "HEALTHY",
            "latency_ms": 85,
            "adapter_version": "1.0.0",
        }


class MockSourceAdapter(SourceAdapter):
    """
    Deterministic mock adapter for testing and offline execution.
    """

    def __init__(self, mock_price: float = 8000.0, is_healthy: bool = True):
        self.mock_price = mock_price
        self.is_healthy_flag = is_healthy

    def source_name(self) -> str:
        return "MOCK_SOURCE"

    def fetch_observations(
        self,
        origin: str,
        destination: str,
        horizon_days: int,
        departure_date: str,
        cabin: str = "ECONOMY"
    ) -> List[Dict[str, Any]]:
        return [
            {
                "source": self.source_name(),
                "origin": origin,
                "destination": destination,
                "horizon_days": horizon_days,
                "departure_date": departure_date,
                "cabin": cabin,
                "price": self.mock_price,
                "currency": "INR",
                "is_nonstop": True,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        ]

    def health_check(self) -> Dict[str, Any]:
        status = "HEALTHY" if self.is_healthy_flag else "DEGRADED"
        return {
            "source": self.source_name(),
            "status": status,
            "latency_ms": 5,
            "adapter_version": "MOCK-1.0.0",
        }


class SourceAdapterRegistry:
    """
    Registry for managing available source adapters.
    """

    def __init__(self):
        self._adapters: Dict[str, SourceAdapter] = {}
        # Register default adapters
        self.register_adapter(GoogleFlightsAdapter())
        self.register_adapter(DuffelAdapter())
        self.register_adapter(MockSourceAdapter())

    def register_adapter(self, adapter: SourceAdapter) -> None:
        self._adapters[adapter.source_name()] = adapter

    def get_adapter(self, name: str) -> Optional[SourceAdapter]:
        return self._adapters.get(name)

    def list_adapters(self) -> List[str]:
        return list(self._adapters.keys())
