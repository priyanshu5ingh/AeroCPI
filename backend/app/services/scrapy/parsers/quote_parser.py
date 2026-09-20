"""AeroGuide Scrapy Quote Parsers and Normalizers.
Extracts structured flight attributes from arbitrary DOM nodes, JSON scripts, and text fragments.
"""
from __future__ import annotations
import re
from typing import Optional, Dict, Any

CARRIER_MAP: Dict[str, str] = {
    "AIR INDIA EXPRESS": "IX",
    "AIRINDIA EXPRESS": "IX",
    "AKASA AIR": "QP",
    "AKASAAIR": "QP",
    "ALLIANCE AIR": "9I",
    "ALLIANCEAIR": "9I",
    "AIR INDIA": "AI",
    "AIRINDIA": "AI",
    "SPICEJET": "SG",
    "SPICE JET": "SG",
    "INDIGO": "6E",
    "VISTARA": "UK",
    "STAR AIR": "S5",
    "STARAIR": "S5",
    "6E": "6E",
    "AI": "AI",
    "IX": "IX",
    "SG": "SG",
    "QP": "QP",
    "9I": "9I",
    "UK": "UK",
    "S5": "S5"
}

CARRIER_NAME_MAP: Dict[str, str] = {
    "6E": "IndiGo",
    "AI": "Air India",
    "IX": "Air India Express",
    "SG": "SpiceJet",
    "QP": "Akasa Air",
    "9I": "Alliance Air",
    "UK": "Vistara",
    "S5": "Star Air"
}


def parse_price(val: Any) -> Optional[float]:
    """Extracts numeric price from strings like '₹5,420', 'INR 6890.00', 'Rs. 4500', '5420', '5420.50' etc."""
    if val is None:
        return None
    val_str = str(val).strip()
    if not val_str:
        return None
    # Strip currency words and symbols
    cleaned = re.sub(r"(?i)\b(?:inr|rs|inr\.|rs\.|in|usd|eur|gbp)\b|[₹$,]", "", val_str)
    match = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    if not match:
        return None
    try:
        return float(match.group(1))
    except (ValueError, TypeError):
        return None


def parse_duration_minutes(val: Any) -> Optional[int]:
    """Parses duration strings like '2h 15m', '2 hr 15 min', '135 min', '02:15', etc."""
    if val is None:
        return None
    val_str = str(val).strip().lower()
    if not val_str:
        return None

    # Check for direct integer
    if val_str.isdigit():
        return int(val_str)

    # Check for Xh Ym or X hr Y min
    h_match = re.search(r"(\d+)\s*(?:h|hr|hrs|hour|hours)", val_str)
    m_match = re.search(r"(\d+)\s*(?:m|min|mins|minute|minutes)", val_str)
    if h_match or m_match:
        hours = int(h_match.group(1)) if h_match else 0
        minutes = int(m_match.group(1)) if m_match else 0
        return hours * 60 + minutes

    # Check for HH:MM format
    colon_match = re.search(r"(\d{1,2}):(\d{2})", val_str)
    if colon_match:
        return int(colon_match.group(1)) * 60 + int(colon_match.group(2))

    return None


def parse_stops_count(val: Any) -> int:
    """Parses stop count strings like 'Non-stop', 'Nonstop', 'Direct', '1 stop', '2 stops'."""
    if val is None:
        return 0
    val_str = str(val).strip().lower()
    if not val_str or any(kw in val_str for kw in ["non-stop", "nonstop", "direct", "0 stop"]):
        return 0
    match = re.search(r"(\d+)\s*stop", val_str)
    if match:
        return int(match.group(1))
    return 0


def identify_carrier(text_or_code: str) -> tuple[str, str]:
    """Identifies canonical carrier code and airline display name from text or IATA code.
    Returns: (carrier_code, airline_name)
    """
    if not text_or_code:
        return "UNKNOWN", "Unknown Airline"

    upper = text_or_code.strip().upper()
    
    # Direct code match
    if upper in CARRIER_NAME_MAP:
        return upper, CARRIER_NAME_MAP[upper]

    # Substring search in name
    for name_key, code in CARRIER_MAP.items():
        if name_key in upper:
            return code, CARRIER_NAME_MAP.get(code, name_key.title())

    return "UNKNOWN", text_or_code.strip()
