"""AeroGuide Multi-Source Adapters Package."""
from app.services.source_adapters.base import (
    BaseSourceAdapter,
    SourceStatus,
    SourceType,
    SourceCapabilityDeclaration,
    SourceTelemetry
)
from app.services.source_adapters.google_flights_adapter import GoogleFlightsSourceAdapter
from app.services.source_adapters.duffel_source_adapter import DuffelSourceAdapter
from app.services.source_adapters.ndc_adapters import IndiGoNDCAdapter, AirIndiaNDCAdapter
from app.services.source_adapters.registry import MultiSourceRegistry

__all__ = [
    "BaseSourceAdapter",
    "SourceStatus",
    "SourceType",
    "SourceCapabilityDeclaration",
    "SourceTelemetry",
    "GoogleFlightsSourceAdapter",
    "DuffelSourceAdapter",
    "IndiGoNDCAdapter",
    "AirIndiaNDCAdapter",
    "MultiSourceRegistry"
]
