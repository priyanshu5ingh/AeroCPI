# AeroCPI: Data Model & Schema Specification

**Document Version:** 1.1.0 (Methodological Review Revision)  
**Target Database:** PostgreSQL 16+ / SQLAlchemy 2.0 / Pydantic v2  

---

## 1. Schema Architecture & Entity Relationship

The AeroCPI data model enforces immutability of raw observations, granular data status tagging, 4-state outlier management, proxy weight classification, and cryptographic run fingerprints.

```
┌─────────────────────┐     ┌─────────────────────┐
│       Source        ├────►│     Observation     │ (Immutable Store)
└─────────────────────┘ 1:N └──────────┬──────────┘
                                       │ 1:1
                                       ▼
┌─────────────────────┐     ┌─────────────────────┐
│    Carrier / Route  ├────►│  VirtualTripSpec    │ (T+1, T+7, T+15, T+30, T+45)
└─────────────────────┘ 1:N └──────────┬──────────┘
                                       │ 1:1
                                       ▼
                            ┌─────────────────────┐
                            │ NormalizationResult │
                            └──────────┬──────────┘
                                       │ 1:1
                                       ▼
                            ┌─────────────────────┐
                            │    QualityResult    │ (VALID | OUTLIER_FLAGGED |
                            └──────────┬──────────┘  EXCLUDED | RETAINED_WITH_WARNING)
                                       │
                                       ▼
┌─────────────────────┐     ┌─────────────────────┐
│ MethodologyVersion  │     │      IndexRun       │
├─────────────────────┤     ├─────────────────────┤
│ DatasetVersion      ├────►│ (National / Route   │
├─────────────────────┤ 1:N │  AeroCPI Index)     │
│ ProxyRouteWeight    │     └──────────┬──────────┘
└─────────────────────┘                │ 1:1
                                       ▼
                            ┌─────────────────────┐
                            │ 4-Pillar Trust      │
                            │ Engine Entities     │
                            │ (Confidence /       │
                            │  Counterfactual /   │
                            │  Breaks /           │
                            │  Attribution)       │
                            └─────────────────────┘
```

---

## 2. Updated Entity Definitions & Schemas

### 2.1 Standardized Booking Horizon
- `horizon_id` (INT, PRIMARY KEY): Days prior to departure (`1`, `7`, `15`, `30`, `45`).
- `horizon_code` (VARCHAR(10), NOT NULL): `T+1`, `T+7`, `T+15`, `T+30`, `T+45`.
- `description` (VARCHAR(100)): Experimental lead time window.

### 2.2 Ingestion & Observation Entities
- **`Observation`**:
  - `observation_id` (UUID, PRIMARY KEY).
  - `source_id` (VARCHAR(30), FOREIGN KEY -> `Source.source_id`).
  - `carrier_id` (VARCHAR(10), FOREIGN KEY -> `Carrier.carrier_id`).
  - `route_id` (VARCHAR(15), FOREIGN KEY -> `Route.route_id`).
  - `departure_date` (DATE, NOT NULL).
  - `booking_date` (DATE, NOT NULL).
  - `horizon_days` (INT, NOT NULL): `1`, `7`, `15`, `30`, or `45`.
  - `quoted_price_inr` (DECIMAL(10, 2), NOT NULL).
  - `data_label` (VARCHAR(20), NOT NULL): `OBSERVED`, `FROZEN`, `OFFICIAL`, `SYNTHETIC`, `DEMO`.
  - `ingested_at` (TIMESTAMPTZ, DEFAULT NOW()).

### 2.3 Preservative Outlier & Quality Entity
- **`QualityResult`**:
  - `quality_id` (UUID, PRIMARY KEY).
  - `observation_id` (UUID, FOREIGN KEY -> `Observation.observation_id`).
  - `quality_status` (VARCHAR(30), NOT NULL): `VALID`, `OUTLIER_FLAGGED`, `EXCLUDED`, `RETAINED_WITH_WARNING`.
  - `modified_z_score` (DECIMAL(6, 3)): MAD score.
  - `exclusion_reason` (TEXT, NULLABLE): Mandatory explanation if `EXCLUDED` (e.g. `MAD_EXCEEDED_3.5_SPIKE`).
  - `reviewed_by` (VARCHAR(50), DEFAULT 'AUTOMATED_QUALITY_ENGINE').

### 2.4 Proxy Weight Classification
- **`ProxyRouteWeight`**:
  - `weight_version_id` (VARCHAR(40), NOT NULL).
  - `route_id` (VARCHAR(15), FOREIGN KEY -> `Route.route_id`).
  - `weight_type` (VARCHAR(50), DEFAULT 'DGCA_TRAFFIC_SHARE_PROXY'): Explicitly tagged as DGCA passenger traffic share proxy, NOT official CPI household expenditure weight.
  - `traffic_share_pct` (DECIMAL(8, 6), NOT NULL): Share of national passenger traffic.
  - PRIMARY KEY (`weight_version_id`, `route_id`).

### 2.5 Index Run & Reproducibility Manifest
- **`IndexRun`**:
  - `run_id` (UUID, PRIMARY KEY).
  - `run_timestamp` (TIMESTAMPTZ, DEFAULT NOW()).
  - `dataset_version_id` (VARCHAR(50), FOREIGN KEY -> `DatasetVersion.dataset_version_id`).
  - `methodology_id` (VARCHAR(30), FOREIGN KEY -> `MethodologyVersion.methodology_id`).
  - `route_basket_version` (VARCHAR(30), NOT NULL).
  - `proxy_weight_version` (VARCHAR(30), NOT NULL).
  - `normalization_version` (VARCHAR(30), NOT NULL).
  - `qc_version` (VARCHAR(30), NOT NULL).
  - `software_version` (VARCHAR(30), NOT NULL).
  - `canonical_serialization_hash` (VARCHAR(64), NOT NULL).
  - `run_fingerprint` (VARCHAR(64), NOT NULL): SHA-256 fingerprint of full 8-part manifest.
  - `national_aerocpi_value` (DECIMAL(8, 3), NOT NULL): AeroCPI Airfare Price Index value.
  - `prev_period_change_pct` (DECIMAL(6, 3), NOT NULL).

### 2.6 Trust Engine Entities

- **`CounterfactualIndexResult`**:
  - `counterfactual_id` (UUID, PRIMARY KEY).
  - `run_id` (UUID, FOREIGN KEY -> `IndexRun.run_id`).
  - `observed_sample_index` (DECIMAL(8, 3), NOT NULL): Index computed on actual observed sample.
  - `constant_sample_index` (DECIMAL(8, 3), NOT NULL): Index computed on common/stable sample between periods.
  - `sample_composition_delta` (DECIMAL(6, 3), NOT NULL): `observed_sample_index - constant_sample_index`.
  - `decomposition_summary` (JSONB, NOT NULL): Estimated breakdown by route, source, carrier, and horizon composition shift.

- **`MeasurementConfidence`**:
  - `confidence_id` (UUID, PRIMARY KEY).
  - `run_id` (UUID, FOREIGN KEY -> `IndexRun.run_id`).
  - `overall_confidence_score` (DECIMAL(5, 2), NOT NULL).
  - `sub_scores` (JSONB, NOT NULL): 8 sub-dimension data health scores.

- **`MeasurementBreak`**:
  - `break_id` (UUID, PRIMARY KEY).
  - `run_id` (UUID, FOREIGN KEY -> `IndexRun.run_id`).
  - `break_type` (VARCHAR(40), NOT NULL): `CARRIER_DROPOUT`, `SOURCE_OUTAGE`, `HORIZON_BLACKOUT`, `COMPOSITION_SHIFT`.
  - `severity` (VARCHAR(20), NOT NULL): `MINOR`, `MODERATE`, `CRITICAL`.
  - `description` (TEXT, NOT NULL).

- **`MovementAttribution`**:
  - `attribution_id` (UUID, PRIMARY KEY).
  - `run_id` (UUID, FOREIGN KEY -> `IndexRun.run_id`).
  - `route_attributions` (JSONB, NOT NULL): Route level delta contributions.
  - `horizon_attributions` (JSONB, NOT NULL): Horizon level delta contributions.
