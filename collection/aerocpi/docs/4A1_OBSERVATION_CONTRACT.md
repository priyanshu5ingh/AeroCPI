# AeroCPI 4A.1 — Observation Contract (FROZEN)

## Rule 1 — search_timestamp is an observed collection fact
`search_timestamp` MUST be supplied by the adapter as the real wall-clock instant
the fare was seen. Timezone-aware ISO-8601, preserved byte-for-byte as received.

FORBIDDEN: `search_timestamp = travel_date - days_left`
Adapters attempting this MUST raise `DERIVED_HORIZON_NO_OBSERVED_SEARCH_TIMESTAMP`.

## Rule 2 — advance_purchase_days is derived, and only from Rule 1
    advance_purchase_days = DATE(travel_date) - DATE(search_timestamp)
Never read from a source's `days_left` / `Days_left` / `daysToDeparture` column.

Audit evidence: the EaseMyTrip "Flight Price Prediction" file claims 50 collection
days. Reconstructing `travel_date - days_left` yields ONE date for 100% of business
rows and two dates for ~99% of economy rows. `days_left` there is arithmetic, not
observation. Fixture: `fixtures/days_left_trap.json`.

## Rule 3 — unknown stays unknown
Total-only sources set `base_fare`, `taxes_total`, `fees_charges`, `gst_amount`,
`fuel_surcharge` to NULL and `fare_breakdown_status = TOTAL_ONLY`.
A published carrier tariff (e.g. GST 5%/18%, YQ bands) is METHODOLOGY CONTEXT ONLY.
It MUST NOT be used to back-solve components of a third-party observed total.

## Rule 4 — provenance
Every collection event persists the raw payload plus SHA-256. `provenance_manifest.json`
records file, route, horizon, capture instant, hash and byte length.

## Data layer labels
| Layer | Label | Use |
|---|---|---|
| Airfare ML 452k (EaseMyTrip 2023-01-15) | HISTORICAL_PROTOTYPE_DATA | APW-curve calibration only |
| AeroCPI live panel | LIVE_MARKET_DATA | The index |
| Route aggregates / MoSPI | VALIDATION_REFERENCE | Plausibility + official anchor |

## Architecture language (approved)
"AeroCPI prioritizes documented/licensed data-access mechanisms and avoids direct
automation of restricted OTA booking funnels." No legal-safety guarantees.
