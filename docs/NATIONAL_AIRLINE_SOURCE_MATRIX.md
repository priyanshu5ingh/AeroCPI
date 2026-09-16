# National Airline Source Matrix & NDC Developer Capabilities

## 1. Executive Summary

AeroGuide extends AeroCPI's macro measurement foundation to consumer-facing airfare intelligence. To ensure absolute data provenance and truth in advertising, AeroGuide enforces a strict **4-Tier Source State Distinction**:

$$\text{DOCUMENTED} \ne \text{ACCESSIBLE} \ne \text{ACTUALLY\_COLLECTED} \ne \text{CURRENTLY\_OBSERVED}$$

Search engine aggregator data is **never** labeled as "Airline Direct" unless verified direct collection has occurred.

---

## 2. National Scheduled Domestic Airline Registry

| Carrier | IATA / ICAO | Official NDC / Developer Portal | Access Mechanism | Documented Endpoints | Current System State |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **IndiGo** | `6E` / `IGO` | [IndiGo Developer Portal](https://developer.goindigo.in/ndcAPI) | `AUTHORIZED_PARTNER` | `AirShopping`, `OfferPrice`, `SeatAvailability`, `OrderCreate` | `CURRENTLY_OBSERVED_VIA_SEARCH` |
| **Air India** | `AI` / `AIC` | [Air India NDC Portal](https://www.airindia.com/in/en/corporate/ndc.html) | `AUTHORIZED_PARTNER` | `NDC Shopping`, `NDC Order Management`, `Direct Connect API` | `CURRENTLY_OBSERVED_VIA_SEARCH` |
| **Akasa Air** | `QP` / `AKJ` | Public Web Distribution | `PUBLIC_WEB_PAGE` | Standard Web Tariffs, Schedule | `CURRENTLY_OBSERVED_VIA_SEARCH` |
| **SpiceJet** | `SG` / `SEJ` | Public Web Distribution | `PUBLIC_WEB_PAGE` | Standard Web Tariffs, Schedule | `CURRENTLY_OBSERVED_VIA_SEARCH` |
| **AIX Connect** | `IX` / `AXB` | Tata Aviation NDC Ecosystem | `AUTHORIZED_PARTNER` | Integrated Air India NDC Catalog | `CURRENTLY_OBSERVED_VIA_SEARCH` |
| **Star Air** | `S5` / `SDG` | Regional Distribution | `PUBLIC_WEB_PAGE` | Regional Web Schedule | `CURRENTLY_OBSERVED_VIA_SEARCH` |

---

## 3. The 4-Tier Source State Framework

1. **DOCUMENTED (`is_documented`)**:
   - The carrier maintains public developer documentation, OpenAPI/WSDL schemas, or official NDC landing pages detailing API endpoints (`AirShopping`, `OfferPrice`, etc.).
2. **ACCESSIBLE (`is_accessible`)**:
   - The system holds active partner credentials, API keys, and IP whitelisting permissions to execute programmatic HTTP queries against the endpoint.
   - *Status*: False for IndiGo/Air India NDC until enterprise IATA / seller onboarding is approved.
3. **ACTUALLY_COLLECTED (`is_actually_collected`)**:
   - Direct raw API payloads from the carrier's direct endpoint have been captured, parsed, validated, and stored in the database.
4. **CURRENTLY_OBSERVED (`is_currently_observed`)**:
   - Live quotes for this carrier are observed via multi-source search aggregators (e.g. `SRC_GOOGLE_FLIGHTS`).

---

## 4. Source Capability & Telemetry Matrix

```json
[
  {
    "source_id": "SRC_GOOGLE_FLIGHTS",
    "source_name": "Google Flights (Search Aggregator)",
    "source_type": "SEARCH_ENGINE",
    "access_status": "ACTIVE_SEARCH",
    "is_public_unrestricted": true,
    "fare_breakdown_supported": false,
    "health_status": "HEALTHY",
    "availability_rate": 1.0,
    "median_response_time_ms": 520.0
  },
  {
    "source_id": "SRC_INDIGO_NDC",
    "source_name": "IndiGo NDC Direct API",
    "source_type": "AIRLINE_DIRECT_NDC",
    "access_status": "DOCUMENTED_UNACCESSIBLE",
    "is_public_unrestricted": false,
    "fare_breakdown_supported": true,
    "health_status": "ACCESS_RESTRICTED_PARTNER",
    "availability_rate": 0.0,
    "median_response_time_ms": null
  },
  {
    "source_id": "SRC_AIR_INDIA_NDC",
    "source_name": "Air India NDC Direct API",
    "source_type": "AIRLINE_DIRECT_NDC",
    "access_status": "DOCUMENTED_UNACCESSIBLE",
    "is_public_unrestricted": false,
    "fare_breakdown_supported": true,
    "health_status": "ACCESS_RESTRICTED_PARTNER",
    "availability_rate": 0.0,
    "median_response_time_ms": null
  }
]
```
