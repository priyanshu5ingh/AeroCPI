"""AeroGuide Duffel Source Adapter.
Authenticates against Duffel API v2 when DUFFEL_API_TOKEN is provided.
When credentials are absent, exposes CONFIGURATION_REQUIRED / CREDENTIALS_REQUIRED and refuses to fabricate data.
"""
from __future__ import annotations
import os
import time
import datetime as dt
from typing import List, Dict, Any, Optional

from app.schemas.observation import RawQuoteInput
from app.services.source_adapters.base import (
    BaseSourceAdapter,
    SourceStatus,
    SourceType,
    SourceCapabilityDeclaration
)
from app.services.duffel_client_service import DuffelClientService
from app.services.duffel_adapter_service import DuffelAdapterService


class DuffelSourceAdapter(BaseSourceAdapter):
    """Adapter for Duffel API v2 GDS / airline aggregator access."""

    def __init__(self):
        super().__init__(
            source_id="SRC_DUFFEL",
            display_name="Duffel API v2",
            source_type=SourceType.GDS_DIRECT,
            provider="Duffel Technology Ltd",
            access_mode="AUTHENTICATED_REST_API",
            adapter_version="2.0.0",
            documentation_url="https://duffel.com/docs/api"
        )

    def get_status(self) -> SourceStatus:
        token = os.getenv("DUFFEL_API_TOKEN")
        if not token or token.strip() == "":
            return SourceStatus.CREDENTIALS_REQUIRED
        return SourceStatus.CONFIGURED

    def get_capabilities(self) -> SourceCapabilityDeclaration:
        return SourceCapabilityDeclaration(
            supports_total_fare=True,
            supports_base_fare=True,
            supports_taxes=True,
            supports_fees=True,
            supports_carrier=True,
            supports_flight_number=True,
            supports_segments=True,
            supports_stops=True,
            supports_duration=True,
            supports_baggage=True,
            supports_timestamp=True,
            supports_seat_availability=True,
            supports_ancillary=True
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
        token = os.getenv("DUFFEL_API_TOKEN")
        if not token or token.strip() == "":
            # Gated: Never fabricate quotes
            return []

        t0 = time.perf_counter()
        try:
            client = DuffelClientService(api_token=token)
            duffel_cabin = "economy" if cabin.upper() == "ECONOMY" else "business"
            
            resp = client.create_offer_request(
                origin_code=origin.upper(),
                destination_code=destination.upper(),
                departure_date=travel_date,
                cabin_class=duffel_cabin,
                passengers=[{"type": "adult"} for _ in range(adults)]
            )
            
            quote_dicts, audit_report, raw_sha256 = DuffelAdapterService.transform_duffel_response_to_raw_quotes(
                raw_payload=resp
            )
            
            latency = (time.perf_counter() - t0) * 1000.0
            self.latencies_ms.append(latency)
            self.success_count += 1
            self.last_success_at = dt.datetime.now(dt.timezone.utc)
            
            quotes: List[RawQuoteInput] = []
            for q in quote_dicts:
                quotes.append(
                    RawQuoteInput(
                        source_id=self.source_id,
                        source_name=self.display_name,
                        source_url=None,
                        collected_at=q["collected_at"],
                        search_timestamp=q["search_timestamp"],
                        travel_date=q["travel_date"],
                        origin_raw=q["origin_raw"],
                        destination_raw=q["destination_raw"],
                        airline=q["airline"],
                        flight_number=q["flight_number"],
                        cabin=q["cabin"],
                        fare_class=q["fare_class"],
                        trip_type=q["trip_type"],
                        stops=q["stops"],
                        duration_minutes=q["duration_minutes"],
                        raw_total_fare=q["raw_total_fare"],
                        raw_base_fare=q["raw_base_fare"],
                        raw_taxes=q["raw_taxes"],
                        raw_fees=q["raw_fees"],
                        base_fare=q["base_fare"],
                        taxes=q["taxes"],
                        fees=q["fees"],
                        total_fare=q["total_fare"],
                        currency=q["currency"]
                    )
                )
            return quotes
        except Exception as e:
            latency = (time.perf_counter() - t0) * 1000.0
            self.latencies_ms.append(latency)
            self.failure_count += 1
            self.last_failure_at = dt.datetime.now(dt.timezone.utc)
            raise e
