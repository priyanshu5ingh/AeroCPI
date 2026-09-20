"""AeroGuide Multi-Source Registry.
Central registry and lifecycle manager for all airfare observation adapters.
Enforces the 8-state model: DOCUMENTED, CONFIGURED, ACCESSIBLE, COLLECTED, OBSERVED, CREDENTIALS_REQUIRED, PARTNER_ACCESS_REQUIRED, DISABLED, FAILED.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.schemas.observation import RawQuoteInput
from app.services.source_adapters.base import (
    BaseSourceAdapter,
    SourceStatus,
    SourceTelemetry
)
class MultiSourceRegistry:
    """Singleton registry coordinating all AeroCPI observation sources."""

    _instance: Optional[MultiSourceRegistry] = None

    def __init__(self):
        self._adapters: Dict[str, BaseSourceAdapter] = {}
        self._register_default_adapters()

    @classmethod
    def get_instance(cls) -> MultiSourceRegistry:
        if cls._instance is None:
            cls._instance = MultiSourceRegistry()
        return cls._instance

    def _register_default_adapters(self):
        from app.services.source_adapters.google_flights_adapter import GoogleFlightsSourceAdapter
        from app.services.source_adapters.duffel_source_adapter import DuffelSourceAdapter
        from app.services.source_adapters.ndc_adapters import IndiGoNDCAdapter, AirIndiaNDCAdapter
        from app.services.scrapy.adapters.scrapy_source_adapter import ScrapySourceAdapter
        from app.services.scrapy.spiders.trip_com_spider import TripComFlightSpider
        from app.services.scrapy.spiders.easemytrip_spider import EaseMyTripFlightSpider

        self.register(GoogleFlightsSourceAdapter())
        self.register(ScrapySourceAdapter(TripComFlightSpider()))
        self.register(ScrapySourceAdapter(EaseMyTripFlightSpider()))
        self.register(DuffelSourceAdapter())
        self.register(IndiGoNDCAdapter())
        self.register(AirIndiaNDCAdapter())

    def register(self, adapter: BaseSourceAdapter):
        self._adapters[adapter.source_id] = adapter

    def get_adapter(self, source_id: str) -> Optional[BaseSourceAdapter]:
        return self._adapters.get(source_id)

    def list_adapters(self) -> List[BaseSourceAdapter]:
        return list(self._adapters.values())

    def get_all_telemetry(self) -> List[SourceTelemetry]:
        return [adapter.get_telemetry() for adapter in self._adapters.values()]

    def get_health_summary(self) -> List[Dict[str, Any]]:
        return [adapter.health_check() for adapter in self._adapters.values()]

    def query_source(
        self,
        source_id: str,
        origin: str,
        destination: str,
        travel_date: str,
        cabin: str = "ECONOMY",
        adults: int = 1,
        **kwargs: Any
    ) -> List[RawQuoteInput]:
        """Queries a specific adapter with strict failure isolation."""
        adapter = self.get_adapter(source_id)
        if not adapter:
            raise ValueError(f"Unknown source adapter: {source_id}")
        return adapter.fetch_quotes(
            origin=origin,
            destination=destination,
            travel_date=travel_date,
            cabin=cabin,
            adults=adults,
            **kwargs
        )

    def query_all_active_sources(
        self,
        origin: str,
        destination: str,
        travel_date: str,
        cabin: str = "ECONOMY",
        adults: int = 1,
        **kwargs: Any
    ) -> Dict[str, List[RawQuoteInput]]:
        """Queries all configured/active sources in parallel or sequence, isolating any individual failure."""
        results: Dict[str, List[RawQuoteInput]] = {}
        for source_id, adapter in self._adapters.items():
            status = adapter.get_status()
            if status in [SourceStatus.CONFIGURED, SourceStatus.ACCESSIBLE, SourceStatus.COLLECTED, SourceStatus.OBSERVED]:
                try:
                    quotes = adapter.fetch_quotes(
                        origin=origin,
                        destination=destination,
                        travel_date=travel_date,
                        cabin=cabin,
                        adults=adults,
                        **kwargs
                    )
                    results[source_id] = quotes
                except Exception as e:
                    # Isolated: one source failure does not kill collection sweep
                    results[source_id] = []
        return results
