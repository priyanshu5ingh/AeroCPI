"""Trip.com Web Ingestion Spider.
Extracts live domestic Indian flight listings and prices from Trip.com India public web pages.
"""
from __future__ import annotations
import json
import re
import datetime as dt
from typing import List, Dict, Any, Optional
from scrapy.http import HtmlResponse, Request

from app.services.scrapy.spiders.base_spider import BaseAeroGuideSpider
from app.services.scrapy.parsers.quote_parser import (
    parse_price,
    parse_duration_minutes,
    parse_stops_count,
    identify_carrier,
    CARRIER_MAP
)

CITY_SLUG_MAP: Dict[str, str] = {
    "DEL": "delhi",
    "BOM": "mumbai",
    "BLR": "bengaluru",
    "HYD": "hyderabad",
    "CCU": "kolkata",
    "MAA": "chennai",
    "GOI": "goa",
    "PAT": "patna",
    "PNQ": "pune",
    "AMD": "ahmedabad",
    "COK": "kochi",
    "JAI": "jaipur",
    "LKO": "lucknow",
    "GAU": "guwahati",
    "IXC": "chandigarh"
}


class TripComFlightSpider(BaseAeroGuideSpider):
    """Scrapy spider for Trip.com India flight search ingestion."""

    name = "trip_com_flight_spider"
    source_id = "SRC_WEB_TRIP"
    display_name = "Trip.com Web Ingestion"
    provider = "Trip.com Group"
    access_mode = "PUBLIC_WEB_SCRAPE"
    adapter_version = "1.1.0"
    documentation_url = "https://in.trip.com/flights/"

    def build_search_request(
        self,
        origin: str,
        destination: str,
        travel_date: str,
        cabin: str = "ECONOMY",
        adults: int = 1
    ) -> Request:
        org_code = origin.upper().strip()
        dst_code = destination.upper().strip()
        org_city = CITY_SLUG_MAP.get(org_code, org_code.lower())
        dst_city = CITY_SLUG_MAP.get(dst_code, dst_code.lower())

        url = (
            f"https://in.trip.com/flights/{org_city}-to-{dst_city}/"
            f"tickets-{org_code.lower()}-{dst_code.lower()}?"
            f"dcity={org_code.lower()}&acity={dst_code.lower()}&ddate={travel_date}"
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
            "Referer": "https://in.trip.com/flights/"
        }

        return Request(
            url=url,
            headers=headers,
            meta={
                "origin": org_code,
                "destination": dst_code,
                "travel_date": travel_date,
                "cabin": cabin,
                "adults": adults
            }
        )

    def fetch_live_html(
        self,
        origin: str,
        destination: str,
        travel_date: str,
        cabin: str = "ECONOMY",
        adults: int = 1
    ) -> str:
        req = self.build_search_request(origin, destination, travel_date, cabin, adults)
        try:
            from playwright.sync_api import sync_playwright
            import time
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
                page.goto(req.url, timeout=25000, wait_until="networkidle")
                time.sleep(2.5)
                html = page.content()
                browser.close()
                return html
        except Exception:
            import httpx
            headers_dict = {k.decode("utf-8") if isinstance(k, bytes) else k: 
                            v.decode("utf-8") if isinstance(v, bytes) else str(v)
                            for k, v in req.headers.items()}
            with httpx.Client(headers=headers_dict, follow_redirects=True, timeout=15.0) as client:
                resp = client.get(req.url)
                return resp.text

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

        # Strategy 1: DOM Elements for Flight Listings
        flight_cards = response.xpath(
            "//div[contains(@class, 'flight-card') or contains(@class, 'flight-item') "
            "or contains(@class, 'm-flight-item') or contains(@class, 'ticket-card') "
            "or contains(@class, 'flight-list-item') or contains(@class, 'flight-box')]"
        )

        for card in flight_cards:
            text_content = " ".join(card.xpath(".//text()").getall())
            pm = re.search(r"(?:₹|INR|Rs\.?)\s*([\d,]+)", text_content)
            if not pm:
                continue
            fare = parse_price(pm.group(1))
            if not fare or fare < 500:
                continue

            matched_airline = None
            for a_name in CARRIER_MAP:
                if a_name.lower() in text_content.lower():
                    matched_airline = a_name
                    break
            c_code, c_name = identify_carrier(matched_airline or "UNKNOWN")

            fn_m = re.search(r"((?:6E|AI|QP|SG|IX|9I|UK|S5)[-\s]?\d{3,4})", text_content, re.IGNORECASE)
            flight_no = fn_m.group(1) if fn_m else None

            duration = parse_duration_minutes(text_content) or 135
            stops = parse_stops_count(text_content)

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
                "flight_number": flight_no,
                "cabin": cabin.upper(),
                "fare_class": "STANDARD",
                "trip_type": "ONE_WAY",
                "stops": stops,
                "duration_minutes": duration,
                "raw_total_fare": str(fare),
                "total_fare": fare,
                "currency": "INR"
            })

        # Strategy 2: JSON-LD Schema.org FlightReservation / Product extraction
        json_lds = response.xpath("//script[@type='application/ld+json']/text()").getall()
        for jld in json_lds:
            try:
                data = json.loads(jld)
                items = data if isinstance(data, list) else [data]
                for it in items:
                    if it.get("@type") in ["Flight", "Product", "Offer"]:
                        offers = it.get("offers", {})
                        p = offers.get("price") or it.get("price")
                        if p:
                            p_float = parse_price(p)
                            if p_float and p_float > 500:
                                airline_str = it.get("provider", {}).get("name") or it.get("name") or "UNKNOWN"
                                c_code, c_name = identify_carrier(airline_str)
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
                                    "flight_number": it.get("flightNumber"),
                                    "cabin": cabin.upper(),
                                    "fare_class": "STANDARD",
                                    "trip_type": "ONE_WAY",
                                    "stops": 0,
                                    "duration_minutes": 135,
                                    "raw_total_fare": str(p_float),
                                    "total_fare": p_float,
                                    "currency": offers.get("priceCurrency", "INR")
                                })
            except Exception:
                pass

        return quotes
