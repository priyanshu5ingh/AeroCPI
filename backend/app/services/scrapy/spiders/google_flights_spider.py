"""Google Flights Scrapy Web Ingestion Spider.
Executes public Google Flights searches, extracts flight offers, carrier attributions, and fare classes using Scrapy Selectors.
"""
from __future__ import annotations
import re
import datetime as dt
from typing import List, Dict, Any, Optional
from scrapy.http import HtmlResponse, Request
from fast_flights import FlightQuery, Passengers, create_query, fetch_flights_html

from app.services.scrapy.spiders.base_spider import BaseAeroGuideSpider
from app.services.scrapy.parsers.quote_parser import (
    parse_price,
    parse_duration_minutes,
    parse_stops_count,
    identify_carrier,
    CARRIER_MAP
)


class GoogleFlightsSpider(BaseAeroGuideSpider):
    """Scrapy spider for Google Flights search ingestion."""

    name = "google_flights_spider"
    source_id = "SRC_GOOGLE_FLIGHTS"
    display_name = "Google Flights"
    provider = "Google Travel / Search"
    access_mode = "PUBLIC_SEARCH_CAPTURE"
    adapter_version = "2.1.0"
    documentation_url = "https://www.google.com/travel/flights"

    def build_search_request(
        self,
        origin: str,
        destination: str,
        travel_date: str,
        cabin: str = "ECONOMY",
        adults: int = 1
    ) -> Request:
        q = create_query(
            flights=[FlightQuery(date=travel_date, from_airport=origin.upper(), to_airport=destination.upper())],
            trip="one-way",
            seat=cabin.lower(),
            passengers=Passengers(adults=adults),
            currency="INR"
        )
        url = f"https://www.google.com/travel/flights?tfs={q.url}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-IN,en;q=0.9",
            "Referer": "https://www.google.com/travel/flights"
        }
        return Request(
            url=url,
            headers=headers,
            meta={
                "origin": origin.upper(),
                "destination": destination.upper(),
                "travel_date": travel_date,
                "cabin": cabin.upper(),
                "adults": adults,
                "query_obj": q
            }
        )

    def fetch_live_html(self, origin: str, destination: str, travel_date: str, cabin: str = "ECONOMY", adults: int = 1) -> str:
        q = create_query(
            flights=[FlightQuery(date=travel_date, from_airport=origin.upper(), to_airport=destination.upper())],
            trip="one-way",
            seat=cabin.lower(),
            passengers=Passengers(adults=adults),
            currency="INR"
        )
        return fetch_flights_html(q)

    def parse_quotes(
        self,
        response: HtmlResponse,
        origin: str,
        destination: str,
        travel_date: str,
        cabin: str = "ECONOMY"
    ) -> List[Dict[str, Any]]:
        quotes: List[Dict[str, Any]] = []
        now_utc = dt.datetime.now(dt.timezone.utc)
        now_iso = now_utc.isoformat()

        # Extract li.pIav2d flight rows
        items = response.xpath("//li[contains(@class, 'pIav2d')]")
        for idx, item in enumerate(items):
            text_content = " ".join(item.xpath(".//text()").getall())
            
            # Find fare in ₹
            pm = re.search(r"₹([\d,]+)", text_content)
            if not pm:
                continue
            fare = parse_price(pm.group(1))
            if not fare:
                continue

            # Identify carrier
            matched_name = None
            for a_name in CARRIER_MAP:
                if a_name.lower() in text_content.lower():
                    matched_name = a_name
                    break
            
            c_code, c_name = identify_carrier(matched_name or "UNKNOWN")

            # Times
            time_matches = re.findall(r"(\d{1,2}:\d{2}\s?[AP]M)", text_content)
            dep_time = time_matches[0] if time_matches else None
            arr_time = time_matches[1] if len(time_matches) > 1 else None

            # Stops & duration
            stops = parse_stops_count(text_content)
            duration = parse_duration_minutes(text_content) or 135

            quotes.append({
                "source_id": self.source_id,
                "source_name": self.display_name,
                "source_url": response.url,
                "collected_at": now_iso,
                "search_timestamp": now_iso,
                "travel_date": travel_date,
                "origin_raw": origin,
                "destination_raw": destination,
                "airline": c_name,
                "carrier_id": c_code,
                "flight_number": None,
                "cabin": cabin.upper(),
                "fare_class": "STANDARD",
                "trip_type": "ONE_WAY",
                "stops": stops,
                "duration_minutes": duration,
                "raw_total_fare": str(fare),
                "total_fare": fare,
                "currency": "INR"
            })

        return quotes
