# AeroCPI Source Adapter Registry

| Adapter | Status | search_ts | base/tax | Notes |
|---|---|---|---|---|
| google_flights (aggregator surface) | WORKING, DEMONSTRATED | observed | NULL (TOTAL_ONLY) | 552 obs / 14 captures collected 2026-09-09 |
| duffel | RECOMMENDED for components | observed | base_amount + tax_amount + total_amount | needs API token; test mode available |
| indigo_ndc | TARGET | observed | NDC OfferPrice returns fare components | requires registration, IP whitelist, certification |
| travelpayouts | FALLBACK | observed | total only | free tier, 200 req/hr/IP, request-based approval |
| amadeus_selfservice | DEPRIORITISED | observed | full breakdown | test env is cached/static; excludes IndiGo |
| easemytrip_kaggle | REJECTED | NONE | NULL | days_left is derived; single crawl |
| kaggle_goibibo | DISQUALIFIED | fabricated | NULL | +500-day clone of EaseMyTrip file |
