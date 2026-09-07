# AeroCPI: Data Model & Schema Specification

**Document Version:** 2.0.0 (Milestone 2 Schema Update)  
**Target Database:** PostgreSQL 16+ / SQLAlchemy 2.0 / Pydantic v2  

---

## Milestone 2 Entity Additions

1. **`DatasetVersion`**:
   - `dataset_version_id` (VARCHAR(50), PRIMARY KEY)
   - `created_at` (TIMESTAMPTZ, DEFAULT NOW())
   - `description` (VARCHAR(255))
   - `source_status` (VARCHAR(30), DEFAULT 'OBSERVED')
   - `record_count` (INT, DEFAULT 0)
   - `fingerprint` (VARCHAR(64), SHA-256)

2. **`ProxyRouteWeight`**:
   - `weight_version_id` (VARCHAR(50), PRIMARY KEY)
   - `route_id` (VARCHAR(15), FOREIGN KEY -> `Route.route_id`, PRIMARY KEY)
   - `weight_share` (DECIMAL(8, 6), NOT NULL)
   - `weight_type` (VARCHAR(50), DEFAULT 'DGCA_TRAFFIC_SHARE_PROXY')
   - `is_demo` (BOOLEAN, DEFAULT True)
   - `source_metadata` (JSONB)
   - `created_at` (TIMESTAMPTZ, DEFAULT NOW())

3. **`IndexRun`**:
   - `run_id` (UUID string, PRIMARY KEY)
   - `run_timestamp` (TIMESTAMPTZ, DEFAULT NOW())
   - `reference_period` (VARCHAR(20), NOT NULL)
   - `comparison_period` (VARCHAR(20), NOT NULL)
   - `dataset_version_id` (VARCHAR(50), FOREIGN KEY -> `DatasetVersion.dataset_version_id`)
   - `route_basket_version` (VARCHAR(50))
   - `proxy_weight_version` (VARCHAR(50))
   - `methodology_version` (VARCHAR(50))
   - `normalization_version` (VARCHAR(30))
   - `quality_rule_version` (VARCHAR(30))
   - `index_method` (VARCHAR(50))
   - `number_of_observations` (INT)
   - `number_of_eligible_observations` (INT)
   - `number_of_excluded_observations` (INT)
   - `number_of_outlier_flagged` (INT)
   - `number_of_retained_warning` (INT)
   - `number_of_duplicates` (INT)
   - `coverage_ratio` (FLOAT)
   - `index_value` (FLOAT)
   - `software_version` (VARCHAR(30))
   - `canonical_run_fingerprint` (VARCHAR(64), SHA-256)

4. **`RouteIndexResult`**:
   - `result_id` (UUID string, PRIMARY KEY)
   - `run_id` (VARCHAR(36), FOREIGN KEY -> `IndexRun.run_id`, INDEX)
   - `route_id` (VARCHAR(15), FOREIGN KEY -> `Route.route_id`, INDEX)
   - `origin_code` (VARCHAR(10))
   - `destination_code` (VARCHAR(10))
   - `travel_date` (DATE, NULLABLE)
   - `booking_horizon` (INT)
   - `cabin` (VARCHAR(20))
   - `stop_type` (VARCHAR(20))
   - `reference_price` (FLOAT)
   - `current_price` (FLOAT)
   - `price_relative` (FLOAT)
   - `route_index_value` (FLOAT)
   - `weight_share` (FLOAT)
   - `sample_count` (INT)
   - `eligible_count` (INT)
   - `excluded_count` (INT)
   - `flagged_count` (INT)
