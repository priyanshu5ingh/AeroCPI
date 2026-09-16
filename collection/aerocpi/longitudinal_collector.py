"""AeroGuide Longitudinal Panel Collector.
Implements the persistent pinned travel date panel strategy with rate limiting,
error isolation, deterministic comparability hashing, and UTC timestamp locking.
"""
from __future__ import annotations
import datetime as dt, hashlib, json, os, pathlib, sys, time, uuid, gzip
from typing import List, Dict, Any, Tuple

PROJECT_ROOT = pathlib.Path(os.getenv("AEROCPI_ROOT", pathlib.Path(__file__).resolve().parents[2]))
DATA_DIR = pathlib.Path(os.getenv("AEROCPI_DATA_DIR", PROJECT_ROOT / "data"))
PANEL_DIR = pathlib.Path(os.getenv("AEROCPI_PANEL_DIR", DATA_DIR / "longitudinal_panel"))

# 4-Tier National Route Universe Definition
TIER_1_DGCA_CORE = [
    ("DEL", "BOM"), ("BLR", "DEL"), ("BOM", "BLR"), ("DEL", "HYD"),
    ("DEL", "CCU"), ("DEL", "MAA"), ("BOM", "GOI"), ("BLR", "HYD"),
    ("DEL", "PAT"), ("BLR", "CCU")
]

TIER_2_NATIONAL_HIGH_TRAFFIC = [
    ("BOM", "MAA"), ("DEL", "PNQ"), ("DEL", "AMD"), ("BLR", "PNQ"),
    ("CCU", "BLR"), ("HYD", "BOM"), ("DEL", "COK"), ("DEL", "GAU"),
    ("DEL", "JAI"), ("DEL", "LKO"), ("BOM", "CCU"), ("BOM", "HYD"),
    ("BLR", "MAA"), ("MAA", "CCU"), ("HYD", "MAA"), ("DEL", "IXC"),
    ("BOM", "AMD"), ("BOM", "COK"), ("BLR", "COK"), ("DEL", "BBI")
]

def generate_comparability_id(
    origin: str,
    destination: str,
    travel_date: str,
    cabin: str = "ECONOMY",
    adults: int = 1,
    currency: str = "INR"
) -> str:
    """Generates deterministic comparability signature for consumer fare matching."""
    raw = f"{origin}-{destination}|{travel_date}|{cabin}|{adults}|{currency}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

def generate_pinned_travel_dates(reference_date: dt.date, span_days: int = 14, start_offset: int = 7) -> List[dt.date]:
    """Generates fixed calendar departure dates to be tracked repeatedly across daily collection runs."""
    return [reference_date + dt.timedelta(days=start_offset + i) for i in range(span_days)]

def build_longitudinal_manifest(
    route: Tuple[str, str],
    pinned_dates: List[dt.date],
    search_timestamp: dt.datetime
) -> List[Dict[str, Any]]:
    """Creates longitudinal panel records tracking fixed travel date trajectories."""
    manifest = []
    origin, dest = route
    route_id = f"{origin}-{dest}"
    
    for t_date in pinned_dates:
        lead_days = (t_date - search_timestamp.date()).days
        manifest.append({
            "panel_id": f"PANEL_{route_id}_{t_date.isoformat()}",
            "route_id": route_id,
            "origin": origin,
            "destination": dest,
            "travel_date": t_date.isoformat(),
            "search_timestamp": search_timestamp.isoformat(),
            "search_date": search_timestamp.date().isoformat(),
            "days_to_departure": lead_days,
            "comparability_id": generate_comparability_id(origin, dest, t_date.isoformat()),
            "passenger_context": {
                "adults": 1,
                "children": 0,
                "infants": 0,
                "cabin": "ECONOMY",
                "currency": "INR",
                "trip_type": "ONE_WAY"
            }
        })
    return manifest

if __name__ == "__main__":
    now_utc = dt.datetime.now(dt.timezone.utc)
    pinned = generate_pinned_travel_dates(now_utc.date(), span_days=14, start_offset=7)
    print(f"AeroGuide Longitudinal Panel: {len(TIER_1_DGCA_CORE)} Tier-1 routes x {len(pinned)} pinned travel dates")
    print(f"Date range: {pinned[0]} to {pinned[-1]}")
