"""AeroGuide Google Flights Source Adapter.
Production prototype adapter capturing live public flight searches with SHA-256 provenance.
"""
from __future__ import annotations
import os
import time
import datetime as dt
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo

from app.schemas.observation import RawQuoteInput
from app.services.source_adapters.base import (
    BaseSourceAdapter,
    SourceStatus,
    SourceType,
    SourceCapabilityDeclaration
)
from app.services.live_collector_service import LiveCollectorService


class GoogleFlightsSourceAdapter(BaseSourceAdapter):
    """Adapter for Google Flights search observation capture."""

    def __init__(self):
        super().__init__(
            source_id="SRC_GOOGLE_FLIGHTS",
            display_name="Google Flights",
            source_type=SourceType.SEARCH_AGGREGATOR,
            provider="Google Travel / Search",
            access_mode="PUBLIC_SEARCH_CAPTURE",
            adapter_version="2.1.0",
            documentation_url="https://www.google.com/travel/flights"
        )

    def get_status(self) -> SourceStatus:
        # Google flights prototype is actively collected and observed
        return SourceStatus.LIVE_OBSERVED if hasattr(SourceStatus, 'LIVE_OBSERVED') else SourceStatus.OBSERVED

    def get_capabilities(self) -> SourceCapabilityDeclaration:
        return SourceCapabilityDeclaration(
            supports_total_fare=True,
            supports_base_fare=False,
            supports_taxes=False,
            supports_fees=False,
            supports_carrier=True,
            supports_flight_number=False,
            supports_segments=False,
            supports_stops=True,
            supports_duration=True,
            supports_baggage=False,
            supports_timestamp=True,
            supports_seat_availability=False,
            supports_ancillary=False
        )

    def fetch_quotes(
        self,
        origin: str,
        destination: str,
        travel_date: str,
        cabin: str = "ECONOMY",
        adults: int = 1,
        **kwargs: Any
    ) -> List[RawQuoteInput]:
        t0 = time.perf_counter()
        try:
            t_dt = dt.datetime.strptime(travel_date, "%Y-%m-%d").date()
            today_kolkata = dt.datetime.now(dt.timezone.utc).astimezone(ZoneInfo("Asia/Kolkata")).date()
            apw = max(1, (t_dt - today_kolkata).days)
            if apw not in [1, 7, 15, 30, 45]:
                # Closest supported APW or fallback
                apw = 15

            rows, raw_path, sha_digest, status = LiveCollectorService.collect_single_route(
                origin=origin,
                dest=destination,
                apw=apw,
                cabin=cabin,
                dry_run=kwargs.get("dry_run", False),
                db=kwargs.get("db", None)
            )

            latency = (time.perf_counter() - t0) * 1000.0
            self.latencies_ms.append(latency)
            self.success_count += 1
            self.last_success_at = dt.datetime.now(dt.timezone.utc)

            quotes: List[RawQuoteInput] = []
            for r in rows:
                quotes.append(
                    RawQuoteInput(
                        source_id=self.source_id,
                        source_name=self.display_name,
                        source_url=r.get("source_url"),
                        collected_at=r.get("collected_at"),
                        search_timestamp=r.get("search_timestamp"),
                        travel_date=r.get("travel_date"),
                        origin_raw=r.get("origin_raw"),
                        destination_raw=r.get("destination_raw"),
                        airline=r.get("airline"),
                        flight_number=r.get("flight_number"),
                        cabin=r.get("cabin", cabin),
                        fare_class=r.get("fare_class", "STANDARD"),
                        trip_type=r.get("trip_type", "ONE_WAY"),
                        stops=r.get("stops", 0),
                        duration_minutes=r.get("duration_minutes", 135),
                        raw_total_fare=r.get("raw_total_fare"),
                        total_fare=r.get("total_fare"),
                        currency=r.get("currency", "INR")
                    )
                )
            return quotes
        except Exception as e:
            latency = (time.perf_counter() - t0) * 1000.0
            self.latencies_ms.append(latency)
            self.failure_count += 1
            self.last_failure_at = dt.datetime.now(dt.timezone.utc)
            raise e
