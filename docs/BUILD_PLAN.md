# AeroCPI: 10-Day Implementation & Build Plan

**Document Version:** 1.1.0 (Methodological Review Revision)  
**Target Event:** Smart India Hackathon 2026 Sprint  

---

## Milestone Implementation Progress

| Milestone | Scope / Objective | Status | Verification Gate |
|---|---|---|---|
| **Milestone 1** | Foundation & Domain Layer (Models, Schemas, Services, Validation) | ✅ **COMPLETED & VERIFIED** | Tag: `milestone-1-foundation` |
| **Milestone 2** | Quality Engine + Core Index Computation Pipeline (Jevons, Young/Laspeyres, MAD, SHA-256 Fingerprint) | ✅ **COMPLETED & VERIFIED** | 30/30 Tests Passed, Fingerprint Verified |
| **Milestone 3** | Ingestion & Live Scraper Integration | ⏳ Pending | Next Milestone |
| **Milestone 4** | Trust Engine & Counterfactual Analysis | ⏳ Pending | Later Milestone |

---

## Priority Implementation Focus

The 10-day build focuses on delivering the **core measurement assurance platform** and **6 prioritized UI screens**:
1. Overview
2. Why Did It Move? (Constant-Sample Counterfactual Index)
3. Index Integrity (8-Dimension Confidence & Outliers)
4. Methodology Lab (Jevons vs Young/Laspeyres, T+1..T+45)
5. Reproduce (8-Part Manifest & Floating-Point Tolerance Verification)
6. Evidence-Grounded AI (Grounded Evidence Chain Narrative)

---

## Daily Task Breakdown & Verification Milestones

### Day 1: Architecture & Database Schema Setup
- Setup repository, Docker Compose, PostgreSQL schema for all entities.
- Implement booking horizons (T+1, T+7, T+15, T+30, T+45), proxy weight classification, 4-state outlier status ENUMs (`VALID`, `OUTLIER_FLAGGED`, `EXCLUDED`, `RETAINED_WITH_WARNING`), and 8-part reproducibility manifest.
- **Verification Gate:** Database tables initialize cleanly; migration script completes.

### Day 2: Ingestion Engine & Data Generator
- Build public API collectors and synthetic fallback data generator tagged with mandatory data labels (`OBSERVED`, `SYNTHETIC`, `DEMO`).
- Seed 30-day baseline quotes across 15 Indian domestic routes and 5 core booking lead times (T+1, T+7, T+15, T+30, T+45).
- **Verification Gate:** Immutable raw observation store populated with > 10,000 clean quotes.

### Day 3: Virtual Trip Standardizer & Fare Normalizer
- Build Virtual Trip Standardizer mapping Economy Standard and 15kg check-in baggage.
- Implement Fare Normalizer calculating normalized fare INR.
- **Verification Gate:** Unit tests pass for normalization formula.

### Day 4: Preservative Outlier & Quality Engine
- Implement duplicate filter and Modified Z-score (MAD) outlier calculation.
- Build 4-state workflow status manager (flagging MAD $> 3.5$, logging exclusion reasons, preserving raw observations).
- **Verification Gate:** Test suite verifies raw observations are preserved intact and outlier exclusions require logged reasons.

### Day 5: Index Computation Engine (Jevons & Young/Laspeyres)
- Build elementary aggregate calculation using Jevons geometric mean index.
- Build higher-level national AeroCPI Airfare Price Index using Young / Modified Laspeyres formula with DGCA-derived route-basket / traffic-share proxy weights.
- **Verification Gate:** Elementary and national index calculations run deterministically.

### Day 6: Trust Engine & Constant-Sample Counterfactual Index
- Build 4-pillar Trust Engine:
  - Pillar 1: Measurement Confidence Score (8 sub-dimensions).
  - Pillar 2: Constant-Sample Counterfactual Index ($I_t^{\text{observed}}$ vs $I_t^{\text{counterfactual}}$).
  - Pillar 3: Measurement Break Detection.
  - Pillar 4: Movement Attribution.
- **Verification Gate:** Counterfactual engine successfully decomposes index delta into constant-sample shift vs composition artifact.

### Day 7: Deterministic Reproducibility & Methodology Lab
- Build 8-part reproducibility manifest builder and SHA-256 run fingerprint generator.
- Implement `/api/v1/reproduce/{run_id}` endpoint with canonical serialization rerun and floating-point tolerance check ($\epsilon = 10^{-4}$).
- Build Methodology Lab simulation engine (Jevons vs Young/Laspeyres, MAD thresholds, lead-time horizon sensitivity).
- **Verification Gate:** Rerun endpoint returns `VERIFIED_EXACT_MATCH` within floating-point tolerance $\epsilon = 10^{-4}$.

### Day 8: Evidence-Grounded AI Engine & API Gateway
- Build Evidence Context Builder assembling database entity facts (`RunId`, `RouteId`, `CounterfactualId`, `QualityEventId`).
- Build grounded AI narrative engine.
- Finalize all REST API endpoints.
- **Verification Gate:** AI assistant endpoint responds with verified evidence citations and zero hallucinations.

### Day 9: React Dashboard UI (6 Priority Screens)
- Build React + TypeScript frontend scaffold with Vite and TailwindCSS.
- Build 6 priority screens: **Overview**, **Why Did It Move?**, **Index Integrity**, **Methodology Lab**, **Reproduce**, **Evidence-Grounded AI**.
- Connect frontend components to FastAPI endpoints via Axios.
- **Verification Gate:** All 6 priority screens render cleanly with live interactive Recharts and zero console errors.

### Day 10: End-to-End Dry Run & Presentation Setup
- Execute full dry run of the 10-step demo script matching `DEMO_SCRIPT.md`.
- Verify containerized Docker deployment (`docker compose up --build`).
- Freeze code state and prepare demo backup snapshots.
- **Verification Gate:** Flawless 8-minute live presentation execution.
