"""AeroGuide Scrapy Base Spider Interface.
Defines canonical contracts for all web-ingestion spiders.
"""
from __future__ import annotations
from abc import abstractmethod
from typing import List, Dict, Any, Optional
import scrapy
from scrapy.http import HtmlResponse, Request


class BaseAeroGuideSpider(scrapy.Spider):
    """Abstract base class for all AeroGuide Scrapy spiders."""

    source_id: str = "SRC_WEB_BASE"
    display_name: str = "Base Web Spider"
    provider: str = "Generic Web"
    access_mode: str = "PUBLIC_WEB_SCRAPE"
    adapter_version: str = "1.0.0"
    documentation_url: Optional[str] = None

    @abstractmethod
    def build_search_request(
        self,
        origin: str,
        destination: str,
        travel_date: str,
        cabin: str = "ECONOMY",
        adults: int = 1
    ) -> Request:
        """Constructs a Scrapy Request object targeting the search endpoint."""
        pass

    @abstractmethod
    def parse_quotes(
        self,
        response: HtmlResponse,
        origin: str,
        destination: str,
        travel_date: str,
        cabin: str = "ECONOMY"
    ) -> List[Dict[str, Any]]:
        """Parses the Scrapy HtmlResponse and extracts raw quote dictionaries."""
        pass
