"""AeroCPI Centralized Collection Configuration.
Defines active routes, target horizons, sources, timeouts, retries, and cadence without hardcoded scattered lists.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

# 1. Active Production Routes (Top 10 DGCA Core Sovereignty Basket)
ACTIVE_PRODUCTION_ROUTES: List[Tuple[str, str]] = [
    ("DEL", "BOM"),
    ("BOM", "DEL"),
    ("DEL", "BLR"),
    ("BLR", "DEL"),
    ("DEL", "MAA"),
    ("MAA", "DEL"),
    ("BOM", "BLR"),
    ("BLR", "BOM"),
    ("DEL", "CCU"),
    ("CCU", "DEL"),
]

# 2. Production Advance Purchase Windows (Days before departure)
PRODUCTION_APW_SET: List[int] = [1, 7, 15, 30, 45]

# 3. Pinned Travel Dates for Empirical Longitudinal Trajectory Panel (14 Fixed Dates)
PINNED_LONGITUDINAL_DATES: List[str] = [
    "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04",
    "2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08",
    "2026-10-09", "2026-10-10", "2026-10-11", "2026-10-12",
    "2026-10-13", "2026-10-14"
]

# 4. Source Definitions & Capabilities
SOURCE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "SRC_GOOGLE_FLIGHTS": {
        "source_id": "SRC_GOOGLE_FLIGHTS",
        "name": "Google Flights Public Interface",
        "adapter_class": "GoogleFlightsAdapter",
        "adapter_version": "1.0.0",
        "category": "SEARCH_AGGREGATOR",
        "requires_auth": False,
        "is_implemented": True,
        "is_configured": True,
        "is_operational": True,
        "rate_limit_delay_seconds": 1.2,
        "timeout_seconds": 25,
        "max_retries": 3,
        "retry_backoff_factor": 1.5,
    },
    "SRC_DUFFEL": {
        "source_id": "SRC_DUFFEL",
        "name": "Duffel NDC Direct API",
        "adapter_class": "DuffelAdapter",
        "adapter_version": "1.0.0",
        "category": "GDS_NDC_AGGREGATOR",
        "requires_auth": True,
        "is_implemented": True,
        "is_configured": bool(os.getenv("DUFFEL_API_TOKEN")),
        "is_operational": bool(os.getenv("DUFFEL_API_TOKEN")),
        "rate_limit_delay_seconds": 0.5,
        "timeout_seconds": 15,
        "max_retries": 2,
        "retry_backoff_factor": 2.0,
    },
    "SRC_WEB_EASEMYTRIP": {
        "source_id": "SRC_WEB_EASEMYTRIP",
        "name": "EaseMyTrip Web Portal",
        "adapter_class": "EaseMyTripAdapter",
        "adapter_version": "1.0.0",
        "category": "OTA_AGGREGATOR",
        "requires_auth": False,
        "is_implemented": True,
        "is_configured": True,
        "is_operational": False, # Parser under review
        "rate_limit_delay_seconds": 2.0,
        "timeout_seconds": 20,
        "max_retries": 2,
        "retry_backoff_factor": 2.0,
    },
    "SRC_INDIGO_NDC": {
        "source_id": "SRC_INDIGO_NDC",
        "name": "IndiGo NDC Direct Connect",
        "adapter_class": "IndigoNDCAdapter",
        "adapter_version": "1.0.0",
        "category": "AIRLINE_DIRECT_NDC",
        "requires_auth": True,
        "is_implemented": True,
        "is_configured": False, # Missing production credentials
        "is_operational": False,
        "rate_limit_delay_seconds": 0.2,
        "timeout_seconds": 10,
        "max_retries": 3,
        "retry_backoff_factor": 1.5,
    },
    "SRC_AIRINDIA_NDC": {
        "source_id": "SRC_AIRINDIA_NDC",
        "name": "Air India NDC Direct Connect",
        "adapter_class": "AirIndiaNDCAdapter",
        "adapter_version": "1.0.0",
        "category": "AIRLINE_DIRECT_NDC",
        "requires_auth": True,
        "is_implemented": True,
        "is_configured": False, # Missing production credentials
        "is_operational": False,
        "rate_limit_delay_seconds": 0.2,
        "timeout_seconds": 10,
        "max_retries": 3,
        "retry_backoff_factor": 1.5,
    }
}
