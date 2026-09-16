"""AeroGuide Multi-Source Adapter Base Architecture.
Defines canonical contracts, lifecycle states, and telemetry tracking for all airfare data sources.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional
import datetime as dt
from pydantic import BaseModel, Field

from app.schemas.observation import RawQuoteInput


class SourceStatus(str, Enum):
    DOCUMENTED = "DOCUMENTED"
    CONFIGURED = "CONFIGURED"
    ACCESSIBLE = "ACCESSIBLE"
    COLLECTED = "COLLECTED"
    OBSERVED = "OBSERVED"
    CREDENTIALS_REQUIRED = "CREDENTIALS_REQUIRED"
    PARTNER_ACCESS_REQUIRED = "PARTNER_ACCESS_REQUIRED"
    DISABLED = "DISABLED"
    FAILED = "FAILED"


class SourceType(str, Enum):
    SEARCH_AGGREGATOR = "SEARCH_AGGREGATOR"
    GDS_DIRECT = "GDS_DIRECT"
    NDC_DIRECT = "NDC_DIRECT"
    OTA_AFFILIATE = "OTA_AFFILIATE"
    METASEARCH = "METASEARCH"
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"


class SourceCapabilityDeclaration(BaseModel):
    supports_total_fare: bool = True
    supports_base_fare: bool = False
    supports_taxes: bool = False
    supports_fees: bool = False
    supports_carrier: bool = True
    supports_flight_number: bool = False
    supports_segments: bool = False
    supports_stops: bool = True
    supports_duration: bool = True
    supports_baggage: bool = False
    supports_timestamp: bool = True
    supports_seat_availability: bool = False
    supports_ancillary: bool = False


class SourceTelemetry(BaseModel):
    source_id: str
    display_name: str
    source_type: SourceType
    provider: str
    access_mode: str
    status: SourceStatus
    credential_required: bool = False
    configured: bool = False
    accessible: bool = False
    collected: bool = False
    observed: bool = False
    coverage_scope: str = "DOMESTIC_INDIA"
    capabilities: SourceCapabilityDeclaration = Field(default_factory=SourceCapabilityDeclaration)
    adapter_version: str = "1.0.0"
    documentation_url: Optional[str] = None
    last_success_at: Optional[str] = None
    last_failure_at: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0
    error_rate: float = 0.0
    median_latency_ms: float = 0.0


class BaseSourceAdapter(ABC):
    """Abstract contract for all AeroCPI and AeroGuide observation source adapters."""

    def __init__(
        self,
        source_id: str,
        display_name: str,
        source_type: SourceType,
        provider: str,
        access_mode: str,
        adapter_version: str = "1.0.0",
        documentation_url: Optional[str] = None
    ):
        self.source_id = source_id
        self.display_name = display_name
        self.source_type = source_type
        self.provider = provider
        self.access_mode = access_mode
        self.adapter_version = adapter_version
        self.documentation_url = documentation_url
        
        self.success_count = 0
        self.failure_count = 0
        self.last_success_at: Optional[dt.datetime] = None
        self.last_failure_at: Optional[dt.datetime] = None
        self.latencies_ms: List[float] = []

    @abstractmethod
    def get_status(self) -> SourceStatus:
        """Determines the live operational status based on environment, credentials, and connectivity."""
        pass

    @abstractmethod
    def get_capabilities(self) -> SourceCapabilityDeclaration:
        """Declares what offering components this source can observe."""
        pass

    @abstractmethod
    def fetch_quotes(
        self,
        origin: str,
        destination: str,
        travel_date: str,
        cabin: str = "ECONOMY",
        adults: int = 1,
        **kwargs: Any
    ) -> List[RawQuoteInput]:
        """Fetches raw flight offers and transforms them into standardized RawQuoteInput objects.
        Raises RuntimeError or returns empty list with appropriate status on failure.
        """
        pass

    def health_check(self) -> Dict[str, Any]:
        """Returns diagnostic health summary."""
        status = self.get_status()
        tot = self.success_count + self.failure_count
        err_rate = (self.failure_count / tot) if tot > 0 else 0.0
        med_lat = sum(self.latencies_ms[-20:]) / len(self.latencies_ms[-20:]) if self.latencies_ms else 0.0
        
        return {
            "source_id": self.source_id,
            "display_name": self.display_name,
            "status": status.value,
            "configured": status not in [SourceStatus.CREDENTIALS_REQUIRED, SourceStatus.PARTNER_ACCESS_REQUIRED, SourceStatus.DISABLED],
            "accessible": status in [SourceStatus.ACCESSIBLE, SourceStatus.COLLECTED, SourceStatus.OBSERVED],
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "error_rate": round(err_rate, 4),
            "median_latency_ms": round(med_lat, 1),
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None
        }

    def get_telemetry(self) -> SourceTelemetry:
        """Returns structured telemetry object for API publication."""
        status = self.get_status()
        tot = self.success_count + self.failure_count
        err_rate = (self.failure_count / tot) if tot > 0 else 0.0
        med_lat = sum(self.latencies_ms[-20:]) / len(self.latencies_ms[-20:]) if self.latencies_ms else 0.0
        
        return SourceTelemetry(
            source_id=self.source_id,
            display_name=self.display_name,
            source_type=self.source_type,
            provider=self.provider,
            access_mode=self.access_mode,
            status=status,
            credential_required=self.source_id in ["SRC_DUFFEL", "SRC_INDIGO_NDC", "SRC_AIR_INDIA_NDC"] or status in [SourceStatus.CREDENTIALS_REQUIRED, SourceStatus.PARTNER_ACCESS_REQUIRED],
            configured=status not in [SourceStatus.CREDENTIALS_REQUIRED, SourceStatus.PARTNER_ACCESS_REQUIRED, SourceStatus.DISABLED],
            accessible=status in [SourceStatus.ACCESSIBLE, SourceStatus.COLLECTED, SourceStatus.OBSERVED],
            collected=self.success_count > 0 or status == SourceStatus.COLLECTED,
            observed=status == SourceStatus.OBSERVED or self.success_count > 0,
            coverage_scope="DOMESTIC_INDIA",
            capabilities=self.get_capabilities(),
            adapter_version=self.adapter_version,
            documentation_url=self.documentation_url,
            last_success_at=self.last_success_at.isoformat() if self.last_success_at else None,
            last_failure_at=self.last_failure_at.isoformat() if self.last_failure_at else None,
            success_count=self.success_count,
            failure_count=self.failure_count,
            error_rate=round(err_rate, 4),
            median_latency_ms=round(med_lat, 1)
        )
