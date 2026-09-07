# AeroCPI: External Reference Data Integration Specification

**Document Version:** 1.0.0 (Milestone 3 Readiness)  
**Classification:** Reference Data Domain Architecture & Module Boundary  

---

## 1. Overview & Purpose

To fulfill the **Measurement Assurance** mission of AeroCPI, observed web-scraped airfare quotes must be systematically validated against official external reference data sources (such as DGCA monthly traffic statistics, MoSPI CPI subgroup publications, and official tariff monitoring reports).

This specification defines the clean domain boundary (`app.validation_data`) and schema abstractions where external reference data enters the system.

---

## 2. Domain Abstraction (`ExternalReferenceData`)

All external validation data enters through a unified domain abstraction represented by `ExternalReferenceDataRecord` (Pydantic) and `ExternalReferenceData` (SQLAlchemy).

### Schema Fields
| Field Name | Type | Description |
|---|---|---|
| `reference_id` | String (UUID) | Primary key for the reference record |
| `source` | String | Data provider identifier (e.g. `DGCA_MONTHLY_TRAFFIC`, `MOSPI_CPI_AIRFARE`) |
| `reference_period` | String | Reference month/date string (e.g. `2026-08`) |
| `route_id` | String | Directional airport pair key (e.g. `DEL-BOM`) |
| `origin` | String (3-IATA) | Origin airport code |
| `destination` | String (3-IATA) | Destination airport code |
| `average_fare` | Float (INR) | Official published average route fare (if published) |
| `passenger_traffic` | Integer | Official published monthly passenger count |
| `publication_date` | Date | Date published by the official authority |
| `data_status` | Enum (`DataStatus`) | Status classification (`OFFICIAL`, `FROZEN`, `DEMO`) |
| `provenance_reference_url` | String | Citation link to official report or PDF publication |
| `metadata_info` | JSON | Additional source-specific metadata |

---

## 3. Module Boundary & Interfaces (`app.validation_data`)

```
backend/app/validation_data/
├── __init__.py           # Module package exports
├── schemas.py            # ExternalReferenceDataRecord domain DTOs
├── interfaces.py         # IReferenceDataProvider abstract contract
└── repository.py         # ValidationDataRepository implementation
```

### Interface Contract (`IReferenceDataProvider`)
```python
class IReferenceDataProvider(ABC):
    @abstractmethod
    def fetch_reference_records(self, reference_period: str, source: Optional[str] = None) -> List[ExternalReferenceDataRecord]:
        """Fetch all official reference records for a specified period and source."""
        pass

    @abstractmethod
    def get_route_reference_fare(self, route_id: str, reference_period: str) -> Optional[float]:
        """Retrieve official published average fare for a route and period."""
        pass

    @abstractmethod
    def get_route_passenger_traffic(self, route_id: str, reference_period: str) -> Optional[int]:
        """Retrieve official published passenger traffic for a route and period."""
        pass
```

---

## 4. Ingestion Entry Points (Milestone 3 Setup)

External reference data will enter the system in **Milestone 3** through designated collector adapters implementing `IReferenceDataProvider`:

1. **DGCA Monthly Traffic Reports Collector**:
   - Ingests city-pair passenger volume figures to update `DGCA-derived route-basket / traffic-share proxy weights`.
   - Populates `passenger_traffic` and `publication_date`.

2. **DGCA Airfare Monitoring Cell Collector**:
   - Ingests published fare band monitoring reports on top domestic routes.
   - Populates `average_fare` and `provenance_reference_url`.

3. **MoSPI Official CPI Subgroup Collector**:
   - Ingests monthly official Transport & Communication / Airfare subgroup CPI indices.
   - Used in Trust Engine Pillar 2 for macro-level divergence comparisons.

---

## 5. Non-Fabrication Guarantee

> [!IMPORTANT]
> In accordance with AeroCPI governance standards, **no fabricated DGCA or MoSPI data** is created during Milestone 2.
> The `IReferenceDataProvider` interface serves as an explicit placeholder boundary ready to receive authenticated external data during Milestone 3 collector ingestion.
