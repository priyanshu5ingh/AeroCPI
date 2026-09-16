"""AeroGuide Authoritative NDC & Airline Source Capability Matrix.
Encodes verified developer portal specifications and access restrictions.
Strict Rule: DOCUMENTED != ACCESSIBLE != ACTUALLY_COLLECTED != CURRENTLY_OBSERVED.
"""
import hashlib
from typing import Dict, Any, List, Optional

TIER_1_DGCA_CORE = [
    ("DEL", "BOM"), ("BOM", "DEL"),
    ("DEL", "BLR"), ("BLR", "DEL"),
    ("DEL", "MAA"), ("MAA", "DEL"),
    ("BOM", "BLR"), ("BLR", "BOM"),
    ("DEL", "CCU"), ("CCU", "DEL")
]

TIER_2_NATIONAL_HIGH_TRAFFIC = [
    ("DEL", "HYD"), ("HYD", "DEL"),
    ("BOM", "GOI"), ("GOI", "BOM"),
    ("BLR", "HYD"), ("HYD", "BLR"),
    ("BOM", "MAA"), ("MAA", "BOM"),
    ("DEL", "PNQ"), ("PNQ", "DEL"),
    ("BLR", "MAA"), ("MAA", "BLR"),
    ("DEL", "COK"), ("COK", "DEL"),
    ("BOM", "HYD"), ("HYD", "BOM"),
    ("DEL", "AMD"), ("AMD", "DEL"),
    ("BLR", "CCU"), ("CCU", "BLR")
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

AIRLINE_NDC_REGISTRY: List[Dict[str, Any]] = [
    {
        "airline_id": "AIRLINE_INDIGO",
        "iata_code": "6E",
        "name": "IndiGo",
        "official_api_available": True,
        "ndc_available": True,
        "ndc_portal_url": "https://developer.goindigo.in/ndcAPI",
        "api_access_type": "AUTHORIZED_PARTNER",
        "requires_authentication": True,
        "partner_restriction": True,
        "documented_endpoints": ["AirShopping", "OfferPrice", "SeatAvailability", "OrderCreate"],
        "observable_content": ["Domestic Flight Offers", "Direct Fares", "Seat Maps (Partner restricted)"],
        "is_documented": True,
        "is_accessible": False, # Requires authenticated partner onboarding & IP whitelisting
        "is_actually_collected": False,
        "is_currently_observed": True, # Actively observed via Google Flights search aggregator
        "verification_source": "https://developer.goindigo.in/airshopping",
        "verification_status": "VERIFIED"
    },
    {
        "airline_id": "AIRLINE_AIR_INDIA",
        "iata_code": "AI",
        "name": "Air India",
        "official_api_available": True,
        "ndc_available": True,
        "ndc_portal_url": "https://www.airindia.com/in/en/corporate/ndc.html",
        "api_access_type": "AUTHORIZED_PARTNER",
        "requires_authentication": True,
        "partner_restriction": True,
        "documented_endpoints": ["NDC Shopping", "NDC Order Management", "Direct Connect API"],
        "observable_content": ["Domestic Flight Schedules", "Standard & Ancillary Fares"],
        "is_documented": True,
        "is_accessible": False, # Requires IATA / accredited seller accreditation
        "is_actually_collected": False,
        "is_currently_observed": True,
        "verification_source": "https://www.airindia.com/in/en/corporate/ndc.html",
        "verification_status": "VERIFIED"
    },
    {
        "airline_id": "AIRLINE_AKASA_AIR",
        "iata_code": "QP",
        "name": "Akasa Air",
        "official_api_available": False,
        "ndc_available": False,
        "ndc_portal_url": None,
        "api_access_type": "PUBLIC_WEB_PAGE",
        "requires_authentication": False,
        "partner_restriction": False,
        "documented_endpoints": [],
        "observable_content": ["Standard Web Tariffs", "Schedule"],
        "is_documented": False,
        "is_accessible": True,
        "is_actually_collected": False,
        "is_currently_observed": True,
        "verification_source": "Public Distribution Monitoring",
        "verification_status": "VERIFIED"
    },
    {
        "airline_id": "AIRLINE_SPICEJET",
        "iata_code": "SG",
        "name": "SpiceJet",
        "official_api_available": False,
        "ndc_available": False,
        "ndc_portal_url": None,
        "api_access_type": "PUBLIC_WEB_PAGE",
        "requires_authentication": False,
        "partner_restriction": False,
        "documented_endpoints": [],
        "observable_content": ["Standard Web Tariffs", "Schedule"],
        "is_documented": False,
        "is_accessible": True,
        "is_actually_collected": False,
        "is_currently_observed": True,
        "verification_source": "Public Distribution Monitoring",
        "verification_status": "VERIFIED"
    }
]

SOURCE_CAPABILITY_MATRIX: List[Dict[str, Any]] = [
    {
        "source_id": "SRC_GOOGLE_FLIGHTS",
        "source_name": "Google Flights (Search Aggregator)",
        "source_type": "SEARCH_ENGINE",
        "access_status": "ACTIVE_SEARCH",
        "is_public_unrestricted": True,
        "fare_breakdown_supported": False, # Total-Only policy
        "health_status": "HEALTHY",
        "availability_rate": 1.0,
        "median_response_time_ms": 520.0
    },
    {
        "source_id": "SRC_INDIGO_NDC",
        "source_name": "IndiGo NDC Direct API",
        "source_type": "AIRLINE_DIRECT_NDC",
        "access_status": "DOCUMENTED_UNACCESSIBLE",
        "is_public_unrestricted": False,
        "fare_breakdown_supported": True,
        "health_status": "ACCESS_RESTRICTED_PARTNER",
        "availability_rate": 0.0,
        "median_response_time_ms": None
    },
    {
        "source_id": "SRC_AIR_INDIA_NDC",
        "source_name": "Air India NDC Direct API",
        "source_type": "AIRLINE_DIRECT_NDC",
        "access_status": "DOCUMENTED_UNACCESSIBLE",
        "is_public_unrestricted": False,
        "fare_breakdown_supported": True,
        "health_status": "ACCESS_RESTRICTED_PARTNER",
        "availability_rate": 0.0,
        "median_response_time_ms": None
    }
]

def get_airline_ndc_info(carrier_code: str) -> Optional[Dict[str, Any]]:
    for a in AIRLINE_NDC_REGISTRY:
        if a["iata_code"] == carrier_code.upper():
            return a
    return None
