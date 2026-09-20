"""AeroGuide Scrapy Source Adapter Architecture.
Bridges Scrapy spiders into the BaseSourceAdapter and MultiSourceRegistry ecosystem.
Executes public web scrapes, preserves SHA-256 provenance in gzip captures, and maps to canonical RawQuoteInput.
"""
from __future__ import annotations
import os
import gzip
import time
import uuid
import hashlib
import pathlib
import datetime as dt
from typing import List, Dict, Any, Optional
import httpx
from scrapy.http import HtmlResponse, Request

from app.schemas.observation import RawQuoteInput
from app.services.source_adapters.base import (
    BaseSourceAdapter,
    SourceStatus,
    SourceType,
    SourceCapabilityDeclaration
)
from app.services.scrapy.spiders.base_spider import BaseAeroGuideSpider

# Path Configuration
BACKEND_DIR = pathlib.Path(__file__).resolve().parents[4]
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = pathlib.Path(os.getenv("AEROCPI_DATA_DIR", PROJECT_ROOT / "data"))
RAW_CAPTURES_DIR = pathlib.Path(os.getenv("AEROCPI_RAW_DIR", DATA_DIR / "raw" / "captures"))


class ScrapySourceAdapter(BaseSourceAdapter):
    """Adapter wrapping an AeroGuide Scrapy spider for standardized multi-source collection."""

    def __init__(self, spider: BaseAeroGuideSpider):
        super().__init__(
            source_id=spider.source_id,
            display_name=spider.display_name,
            source_type=SourceType.OTA_AFFILIATE if "WEB" in spider.source_id else SourceType.SEARCH_AGGREGATOR,
            provider=spider.provider,
            access_mode=spider.access_mode,
            adapter_version=spider.adapter_version,
            documentation_url=spider.documentation_url
        )
        self.spider = spider

    def get_status(self) -> SourceStatus:
        if self.success_count > 0:
            return SourceStatus.OBSERVED
        return SourceStatus.ACCESSIBLE

    def get_capabilities(self) -> SourceCapabilityDeclaration:
        return SourceCapabilityDeclaration(
            supports_total_fare=True,
            supports_base_fare=False,
            supports_taxes=False,
            supports_fees=False,
            supports_carrier=True,
            supports_flight_number=True,
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
        """Executes the Scrapy spider request, captures raw payload with SHA-256 provenance,
        and returns normalized canonical RawQuoteInput list.
        """
        t0 = time.perf_counter()
        origin_clean = origin.upper().strip()
        dest_clean = destination.upper().strip()

        try:
            # 1. Build Scrapy Request
            scrapy_req: Request = self.spider.build_search_request(
                origin=origin_clean,
                destination=dest_clean,
                travel_date=travel_date,
                cabin=cabin,
                adults=adults
            )

            # Check if fixture response is passed in kwargs (for unit testing)
            fixture_html = kwargs.get("fixture_html")
            if fixture_html is not None:
                body_bytes = fixture_html.encode("utf-8") if isinstance(fixture_html, str) else fixture_html
                status_code = 200
            elif hasattr(self.spider, "fetch_live_html"):
                html_str = self.spider.fetch_live_html(origin=origin_clean, destination=dest_clean, travel_date=travel_date, cabin=cabin, adults=adults)
                body_bytes = html_str.encode("utf-8", "replace")
                status_code = 200
            else:
                # 2. Execute HTTP fetch
                headers_dict = {k.decode("utf-8") if isinstance(k, bytes) else k: 
                                v.decode("utf-8") if isinstance(v, bytes) else str(v)
                                for k, v in scrapy_req.headers.items()}
                with httpx.Client(headers=headers_dict, follow_redirects=True, timeout=15.0) as client:
                    resp = client.get(scrapy_req.url)
                    body_bytes = resp.content
                    status_code = resp.status_code

            raw_sha256 = hashlib.sha256(body_bytes).hexdigest()

            # 3. Persist GZIP raw capture to disk (No-overwrite guarantee)
            RAW_CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
            stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            raw_filename = f"{origin_clean}-{dest_clean}_{self.source_id}_{stamp}_{raw_sha256[:12]}.html.gz"
            raw_path = RAW_CAPTURES_DIR / raw_filename

            if raw_path.exists():
                unique_suffix = uuid.uuid4().hex[:6]
                raw_filename = f"{origin_clean}-{dest_clean}_{self.source_id}_{stamp}_{raw_sha256[:12]}_{unique_suffix}.html.gz"
                raw_path = RAW_CAPTURES_DIR / raw_filename

            compressed = gzip.compress(body_bytes)
            with open(raw_path, "wb") as f:
                f.write(compressed)

            # 4. Construct Scrapy HtmlResponse
            scrapy_resp = HtmlResponse(
                url=scrapy_req.url,
                status=status_code,
                headers=scrapy_req.headers,
                body=body_bytes,
                encoding="utf-8",
                request=scrapy_req
            )

            # 5. Extract quotes using Spider parse logic
            quote_dicts = self.spider.parse_quotes(
                response=scrapy_resp,
                origin=origin_clean,
                destination=dest_clean,
                travel_date=travel_date,
                cabin=cabin
            )

            latency = (time.perf_counter() - t0) * 1000.0
            self.latencies_ms.append(latency)
            self.success_count += 1
            self.last_success_at = dt.datetime.now(dt.timezone.utc)

            # 6. Map to canonical RawQuoteInput
            raw_quotes: List[RawQuoteInput] = []
            now_iso = dt.datetime.now(dt.timezone.utc).isoformat()

            for q in quote_dicts:
                raw_quotes.append(
                    RawQuoteInput(
                        source_id=self.source_id,
                        source_name=self.display_name,
                        source_url=q.get("source_url") or scrapy_req.url,
                        collected_at=q.get("collected_at") or now_iso,
                        search_timestamp=q.get("search_timestamp") or now_iso,
                        travel_date=q.get("travel_date") or travel_date,
                        origin_raw=q.get("origin_raw") or origin_clean,
                        destination_raw=q.get("destination_raw") or dest_clean,
                        airline=q.get("airline") or "UNKNOWN",
                        carrier_id=q.get("carrier_id") or "UNKNOWN",
                        flight_number=q.get("flight_number"),
                        cabin=q.get("cabin") or cabin.upper(),
                        fare_class=q.get("fare_class", "STANDARD"),
                        trip_type=q.get("trip_type", "ONE_WAY"),
                        stops=q.get("stops", 0),
                        duration_minutes=q.get("duration_minutes", 135),
                        raw_total_fare=str(q.get("total_fare") or q.get("raw_total_fare")),
                        total_fare=q.get("total_fare"),
                        currency=q.get("currency", "INR")
                    )
                )

            return raw_quotes

        except Exception as e:
            latency = (time.perf_counter() - t0) * 1000.0
            self.latencies_ms.append(latency)
            self.failure_count += 1
            self.last_failure_at = dt.datetime.now(dt.timezone.utc)
            raise e
