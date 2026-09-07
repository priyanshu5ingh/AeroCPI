# AeroCPI: Master Technical Specification

**Project Name:** AeroCPI  
**Tagline:** Measure. Explain. Verify.  
**SIH Problem Statement:** SIH26056 — Development of a Real-time Airfare Price Index for India through Automated Web Scraping of Airline and Online Travel Aggregator Portals for Augmentation of the Consumer Price Index (CPI).  
**System Nature:** Experimental prototype airfare price measurement platform intended to augment Consumer Price Index (CPI) airfare measurement.  
**Core Architectural Motto:** `DATA → STATISTICS → EVIDENCE → AI`  

---

## 1. Executive Summary & Vision

The Consumer Price Index (CPI) in India, compiled by the Ministry of Statistics and Programme Implementation (MoSPI), requires high-frequency, representative price indicators. Transport sub-components—specifically airfares—exhibit extreme volatility driven by dynamic pricing, lead times, fuel surcharges, and route demand.

While competing projects focus on basic scrapers and dashboards, **AeroCPI fundamentally differentiates itself through MEASUREMENT ASSURANCE**.

AeroCPI provides an **experimental/prototype airfare measurement intended to augment CPI airfare measurement**. It does NOT claim to be the official CPI system or to reproduce the complete official CPI compilation methodology. 

In price statistics, an index movement is uninformative unless analysts can verify whether the shift is driven by genuine market price changes or by changes in data collection quality (e.g. source outage, route composition shift, missing lead times, or supplier mix changes). AeroCPI is explicitly architected to:
1. Measure the **AeroCPI Airfare Price Index** across standardized virtual trip specs.
2. Explain index movement through an analytical decomposition (**Market Signal vs Measurement Artifacts** using a **Constant-Sample Counterfactual Index**).
3. Verify every index run with full determinism, canonical serialization, and cryptographic fingerprinting.

AI features in AeroCPI are strictly constrained to **Evidence-Grounded Explanation**. AI never invents numbers or serves as a source of truth; it translates empirical statistical evidence, counterfactual analysis, and quality audit logs into verifiable analytical narratives.

---

## 2. Key Methodological Rules & Standards

1. **AeroCPI Airfare Price Index vs Official CPI:** AeroCPI is an experimental prototype airfare index for CPI augmentation. It never claims to be the official MoSPI CPI.
2. **DGCA Proxy Weights:** Weights derived from DGCA passenger traffic volume reports are explicitly designated as **"DGCA-derived route-basket / traffic-share proxy weights"**. They represent passenger traffic share, NOT official CPI household expenditure weights.
3. **Core Booking Horizons:** Standardized lead times are strictly **T+1, T+7, T+15, T+30, T+45** days prior to departure. Expenditure weights across horizons are strictly experimental and configurable in the Methodology Lab; no hardcoded horizon weights are represented as official MoSPI facts.
4. **CPI Aggregation Distinction:** Elementary indices at the item level utilize the Jevons geometric mean formula, while higher-level index aggregation utilizes Young or Modified Laspeyres-style formulas.
5. **Preservative Outlier Management:** MAD $> 3.5$ serves as the initial statistical flag threshold. Outliers are **NEVER automatically deleted**. Observations transition through explicit statuses (`VALID`, `OUTLIER_FLAGGED`, `EXCLUDED`, `RETAINED_WITH_WARNING`). Original raw observations remain immutable in the store, and every exclusion requires a logged reason.
6. **Trust Engine Architecture:** Built upon 4 pillars:
   - **Measurement Confidence** (multi-factor data health score)
   - **Constant-Sample Counterfactual Index** (comparing observed sample index vs common sample index to isolate composition effects)
   - **Measurement Break Detection** (structural coverage/carrier shifts)
   - **Movement Attribution** (route, horizon, and carrier contribution analysis)
7. **Deterministic Reproducibility:** SHA-256 serves as a run fingerprint (not statistical proof). Reproducibility requires a complete manifest (dataset, methodology, route basket, weights, normalization, QC, software versions, canonical input serialization) and applies a strict numerical floating-point comparison tolerance ($\epsilon = 10^{-4}$).

---

## 3. Core System Architecture Pipeline

```
[ Data Sources (Ethical/Permitted) ]
               │
               ▼
[ 1. Ingestion Engine (Public APIs & Synthetic Generators) ]
               │
               ▼
[ 2. Raw Observation Store (Append-Only PostgreSQL) ]
               │
               ▼
[ 3. Virtual Trip Standardizer (T+1, T+7, T+15, T+30, T+45) ]
               │
               ▼
[ 4. Fare Normalizer ]
               │
               ▼
[ 5. Quality & Outlier Engine (MAD > 3.5 Status Management) ]
               │
               ▼
[ 6. Index Computation Engine (Jevons & Young/Laspeyres) ]
               │
               ▼
[ 7. Trust & Measurement Assurance Engine ]
   ├── A. Measurement Confidence
   ├── B. Constant-Sample Counterfactual Index
   ├── C. Measurement Break Detection
   └── D. Movement Attribution
               │
               ▼
[ 8. Deterministic Provenance & Reproducibility Engine ]
               │
               ▼
[ 9. Methodology Lab & Sensitivity Sandbox ]
               │
               ▼
[ 10. Evidence-Grounded AI Engine ]
               │
               ▼
[ 11. FastAPI REST Gateway ]
               │
               ▼
[ 12. Prioritized Statistical Dashboard UI ]
```

---

## 4. UI Screen Implementation Priority

During primary hackathon implementation, development is strictly focused on **6 Priority Core Screens**:

1. **Overview:** National AeroCPI Airfare Price Index timeseries, confidence score, daily movement.
2. **Why Did It Move?:** Constant-Sample Counterfactual Index decomposition (Market Signal vs Data Movement) & route attribution.
3. **Index Integrity:** 8-dimension data health scores, break detection alerts, outlier pressure.
4. **Methodology Lab:** What-if sensitivity testing (Jevons vs Young/Laspeyres, MAD thresholds, proxy weights).
5. **Reproduce:** Fingerprint manifest inspector, canonical serialization rerun, floating-point tolerance match check.
6. **Evidence-Grounded AI:** Conversational analytical query tool referencing explicit database fact IDs.

*Secondary views (Route Explorer, Observation Explorer, Stress Testing) will be integrated following the core 6.*

---

## 5. Summary of System Documentation

The updated technical documentation is structured as follows:

1. `docs/MASTER_TECHNICAL_SPEC.md` - Master specification, methodological rules, and priority views.
2. `docs/ARCHITECTURE.md` - Pipeline execution flow, component interaction, and trust engine structure.
3. `docs/DATA_MODEL.md` - Pydantic & PostgreSQL schemas including 4-state outlier statuses and proxy weight tags.
4. `docs/INDEX_METHODOLOGY.md` - Jevons elementary index, Young/Laspeyres aggregation, T+1..T+45 horizons, MAD thresholding.
5. `docs/TRUST_ENGINE.md` - Measurement Confidence, Counterfactual Index algorithm, Break Detection, Movement Attribution.
6. `docs/API_CONTRACT.md` - RESTful OpenAPI specifications, request/response models.
7. `docs/FRONTEND_SPEC.md` - Design system and detailed specifications for prioritized 6 UI screens.
8. `docs/DEMO_SCRIPT.md` - Updated 10-step core demo flow matching SIH priorities.
9. `docs/BUILD_PLAN.md` - 10-day implementation plan focused on core capabilities.
10. `docs/ASSUMPTIONS_AND_RISKS.md` - Disclaimers, DGCA proxy distinction, assumptions, and risk matrix.

---

## 6. Technology Stack & Dependencies

### Backend Stack
- Python 3.11+, FastAPI 0.110+, Pandas 2.2+, NumPy 1.26+, SQLAlchemy 2.0+, AsyncPG, Pydantic v2, Pytest 8.0+, Docker Compose.

### Frontend Stack
- React 18, TypeScript 5, Vite 5, TailwindCSS 3.4, Lucide Icons, Recharts 2.12, Axios.
