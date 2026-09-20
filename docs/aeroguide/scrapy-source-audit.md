# AeroGuide Multi-Source Web Ingestion Audit
## Pre-Implementation Feasibility and Access Analysis

This document evaluates prospective web-based airfare sources for domestic Indian air routes to support empirical multi-source collection in AeroGuide without violating security, CAPTCHA, or anti-bot boundaries.

---

### Candidate Source Evaluation Matrix

| Source Candidate | Provider Type | Endpoint / Target | Publicly Queryable? | Anti-Bot / CAPTCHA | Extraction Feasibility | Audit Status | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EaseMyTrip Flight Search** | Public OTA | `https://www.easemytrip.com/flight-listing/{ORG}-{DST}/{DATE}` | Partial (HTML shell / JS hydrated) | Cloudflare Turnstile / Bot Management on high rate | Medium-High | **FEASIBLE (Scrapy Spider)** | Public SSR / hydration payload accessible with canonical headers; returns structured carrier, flight no, fare, departure/arrival timestamps. |
| **Trip.com Domestic Search** | Global OTA / Metasearch | `https://in.trip.com/flights/{origin}-to-{destination}/...` | Yes | Akamai Bot Manager (rate limited) | Medium-High | **FEASIBLE (Scrapy Spider)** | Unauthenticated public flight listings accessible for Indian domestic city pairs with complete fare breakdown & carrier attribution. |
| **Wego India** | Flight Metasearch | `https://www.wego.co.in/flights/searches/...` | Session Required | Strict PerimeterX / Human Challenge | Low | **UNSUITABLE** | Requires client JS session bootstrap and dynamic token exchange. Fails zero-bypass policy. |
| **Cleartrip** | Domestic OTA | `https://www.cleartrip.com/flights/results?...` | Restricted | Cloudflare managed challenge | Low | **UNSUITABLE** | Explicitly blocks automated user-agents without browser session handshake. |
| **Ixigo** | Domestic OTA / Metasearch | `https://www.ixigo.com/search/result/flight/...` | Restricted | PerimeterX / Datadome | Low | **UNSUITABLE** | Dynamic challenge prevents headless HTTP/Scrapy fetch. |
| **Kayak India** | Global Metasearch | `https://www.kayak.co.in/flights/...` | Heavy JS | Cloudflare Bot Challenge | Low | **UNSUITABLE** | Blocks direct spider requests. |
| **Akasa Air Direct Booking** | Direct Airline | `https://www.akasaair.com/` | Single Page App | Cloudflare + Custom API Signature | Low-Medium | **PARTNER_ACCESS_REQUIRED** | Direct NDC/API required for robust programmatic access. |
| **IndiGo Direct Booking** | Direct Airline | `https://www.goindigo.in/` | Dynamic SPA | Akamai Bot Manager + Token Session | Low | **PARTNER_ACCESS_REQUIRED** | Reserved for IndiGo NDC Partner adapter. |
| **Air India Direct Booking** | Direct Airline | `https://www.airindia.com/` | Dynamic SPA | Imperva Incapsula | Low | **PARTNER_ACCESS_REQUIRED** | Reserved for Air India NDC Partner adapter. |

---

### Selected Web Sources for Scrapy Implementation

1. **`SRC_WEB_EASEMYTRIP` (EaseMyTrip Web Spider)**
   - **Source ID**: `SRC_WEB_EASEMYTRIP`
   - **Provider**: EaseMyTrip (Easy Trip Planners Ltd)
   - **Access Mode**: `PUBLIC_WEB_SCRAPE`
   - **Target Pattern**: `https://www.easemytrip.com/flight-listing/{origin}-{destination}/{travel_date}`
   - **Capture Method**: `html_fetch:scrapy`
   - **Extracted Fields**: Carrier (`airline`), flight number, total fare (`INR`), departure time, arrival time, stops, duration, search timestamp, SHA-256 raw HTML digest.

2. **`SRC_WEB_TRIP` (Trip.com India Web Spider)**
   - **Source ID**: `SRC_WEB_TRIP`
   - **Provider**: Trip.com India
   - **Access Mode**: `PUBLIC_WEB_SCRAPE`
   - **Target Pattern**: `https://in.trip.com/flights/{origin_city}-to-{dest_city}/tickets-{origin}-{destination}?dcity={origin}&acity={destination}&ddate={travel_date}`
   - **Capture Method**: `html_fetch:scrapy`
   - **Extracted Fields**: Carrier, total fare, stops, flight duration, search timestamp, SHA-256 raw HTML digest.

---

### Data Ingestion & Provenance Architecture

```
                                  +-----------------------------+
                                  |   AeroGuide MultiSource     |
                                  |         Registry            |
                                  +--------------+--------------+
                                                 |
         +---------------------------------------+---------------------------------------+
         |                                       |                                       |
+--------v---------+                   +---------v----------+                   +--------v---------+
| Google Flights   |                   | Scrapy Spider      |                   | Duffel API v2    |
| (SRC_GOOGLE_     |                   | - SRC_WEB_EASEMYTRIP|                  | (SRC_DUFFEL)     |
|  FLIGHTS)        |                   | - SRC_WEB_TRIP     |                   |                  |
+--------+---------+                   +---------+----------+                   +--------+---------+
         |                                       |                                       |
         | Raw HTML/JSON                         | Raw HTML Captures                     | Signed JSON
         | SHA-256 Provenance                    | SHA-256 Provenance                    | SHA-256 Provenance
         |                                       |                                       |
         +---------------------------------------+---------------------------------------+
                                                 |
                                  +--------------v--------------+
                                  | CanonicalObservationPipeline|
                                  |  - Normalization            |
                                  |  - Route Mapping            |
                                  |  - Arithmetic Verification  |
                                  |  - SHA-256 Provenance Gzip  |
                                  |  - Database Ingestion       |
                                  +--------------+--------------+
                                                 |
                                  +--------------v--------------+
                                  | Source Agreement & Audit    |
                                  |  - Comparability Engine     |
                                  |  - Source Agreement Badges  |
                                  |  - Decision Engine Feed     |
                                  +-----------------------------+
```
