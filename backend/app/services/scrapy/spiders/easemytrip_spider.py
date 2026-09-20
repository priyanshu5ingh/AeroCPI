"""EaseMyTrip Web Ingestion Spider.
Extracts live domestic Indian flight listings and prices from EaseMyTrip public web pages.
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

CITY_NAME_MAP: Dict[str, str] = {
    "DEL": "Delhi",
    "BOM": "Mumbai",
    "BLR": "Bangalore",
    "HYD": "Hyderabad",
    "CCU": "Kolkata",
    "MAA": "Chennai",
    "GOI": "Goa",
    "PAT": "Patna",
    "PNQ": "Pune",
    "AMD": "Ahmedabad",
    "COK": "Cochin",
    "JAI": "Jaipur",
    "LKO": "Lucknow",
    "GAU": "Guwahati",
    "IXC": "Chandigarh"
}


class EaseMyTripFlightSpider(BaseAeroGuideSpider):
    """Scrapy spider for EaseMyTrip flight search ingestion."""

    name = "easemytrip_flight_spider"
    source_id = "SRC_WEB_EASEMYTRIP"
    display_name = "EaseMyTrip Web Ingestion"
    provider = "Easy Trip Planners Ltd"
    access_mode = "PUBLIC_WEB_SCRAPE"
    adapter_version = "1.1.0"
    documentation_url = "https://www.easemytrip.com/flights.html"

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
        org_city = CITY_NAME_MAP.get(org_code, org_code)
        dst_city = CITY_NAME_MAP.get(dst_code, dst_code)

        try:
            d_obj = dt.datetime.strptime(travel_date, "%Y-%m-%d")
            formatted_date = d_obj.strftime("%d/%m/%Y")
        except ValueError:
            formatted_date = travel_date

        url = (
            f"https://flight.easemytrip.com/FlightList/Index?"
            f"srch={org_code}-{org_city}-India|{dst_code}-{dst_city}-India|{formatted_date}"
            f"&px={adults}-0-0&cbn=0&ar=undefined&isSearch=true"
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
            "Referer": "https://www.easemytrip.com/"
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
                page.goto(req.url, timeout=20000, wait_until="domcontentloaded")
                try:
                    page.wait_for_selector(".fltResult", timeout=8000)
                    time.sleep(0.5)
                except Exception:
                    time.sleep(2.0)
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

        # Strategy 1: Structured fltResult flight cards from hydrated page
        cards = response.xpath("//div[contains(@class, 'fltResult')]")
        if cards:
            for card in cards:
                # Airline name
                air_name = card.xpath(".//span[contains(@class, 'txt-r4')]/text()").get()
                if not air_name:
                    text_all = " ".join(card.xpath(".//text()").getall())
                    for a_name in CARRIER_MAP:
                        if a_name.lower() in text_all.lower():
                            air_name = a_name
                            break
                if not air_name:
                    continue
                c_code, c_name = identify_carrier(air_name.strip())

                # Flight number
                fn_nodes = card.xpath(".//span[contains(@class, 'txt-r5')]//text()").getall()
                fn_text = " ".join([t.strip() for t in fn_nodes if t.strip()])
                fn_m = re.search(r"((?:6E|AI|QP|SG|IX|9I|UK|S5)[-\s]?\d{3,4})", fn_text, re.IGNORECASE)
                flight_no = fn_m.group(1).replace(" ", "") if fn_m else None

                # Duration
                dur_str = card.xpath(".//span[contains(@class, 'dura_md')]/text()").get() or ""
                duration = parse_duration_minutes(dur_str) or 135

                # Stops
                stops_str = card.xpath(".//span[contains(@class, 'dura_md2')]/text()").get() or ""
                stops = parse_stops_count(stops_str)

                # Price: Look at prominent fare nodes, then right column
                price_nodes = card.xpath(".//*[contains(@class, 'cross-pr-txt') or contains(@class, 'exPrc') or contains(@class, 'prc')]//text()").getall()
                fare = None
                for pn in price_nodes:
                    p_val = parse_price(pn)
                    if p_val and p_val >= 1000:
                        fare = p_val
                        break
                if not fare:
                    right_col = card.xpath(".//div[contains(@class, 'col-md-2') or contains(@class, 'col-sm-2')]//text()").getall()
                    for rn in right_col:
                        p_val = parse_price(rn)
                        if p_val and p_val >= 1000:
                            fare = p_val
                            break

                if not fare or fare < 500:
                    continue

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

            if quotes:
                return quotes

        # Strategy 2: Generic Fallback DOM Elements (.flt-list, .row_flt, etc.)
        rows = response.xpath(
            "//div[contains(@class, 'flt-list') or contains(@class, 'fltResult') "
            "or contains(@class, 'row_flt') or contains(@class, 'flight-card') "
            "or contains(@class, 'fltList') or contains(@class, 'flt-box')]"
        )

        for row in rows:
            text_content = " ".join(row.xpath(".//text()").getall())
            
            # Find price
            pm = re.search(r"(?:₹|INR|Rs\.?)\s*([\d,]+)", text_content)
            if not pm:
                continue
            fare = parse_price(pm.group(1))
            if not fare or fare < 500:
                continue

            # Identify airline
            matched_airline = None
            for a_name in CARRIER_MAP:
                if a_name.lower() in text_content.lower():
                    matched_airline = a_name
                    break
            c_code, c_name = identify_carrier(matched_airline or "UNKNOWN")

            # Flight number
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

        return quotes
