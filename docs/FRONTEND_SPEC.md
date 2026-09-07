# AeroCPI: Frontend Architecture & UI Specification

**Document Version:** 1.1.0 (Methodological Review Revision)  
**Stack:** React 18 / TypeScript 5 / Vite 5 / TailwindCSS / Recharts / Lucide Icons  
**Implementation Strategy:** Prioritized 6 Core Screens  

---

## 1. UI Navigation & Screen Priority

To maximize SIH 2026 presentation impact and technical clarity, frontend development is prioritized into **6 Core Primary Screens**, followed by secondary diagnostic screens.

### Priority 1: 6 Core Screens (Immediate Build)
1. **Overview:** National AeroCPI Airfare Price Index, confidence score, daily movement, status badge.
2. **Why Did It Move?:** Constant-Sample Counterfactual Index comparison (Observed vs Constant-Sample), analytical signal vs data shift breakdown.
3. **Index Integrity:** 8-dimension Measurement Confidence radar, break detection alerts, outlier pressure.
4. **Methodology Lab:** Interactive sensitivity sandbox (Jevons vs Young/Laspeyres, MAD thresholds, proxy weights).
5. **Reproduce:** 8-part fingerprint manifest inspector, canonical serialization rerun, floating-point tolerance indicator ($\epsilon = 10^{-4}$).
6. **Evidence-Grounded AI:** Grounded analytical query interface referencing explicit database IDs.

### Priority 2: Secondary Screens (Deferred for Phase 2)
- Route Explorer
- Observation Explorer
- Stress Testing Sandbox

---

## 2. Visual Design System & Headers

- **Header Title:** **AeroCPI** — *Measure. Explain. Verify.*
- **System Nature Badge:** `Experimental Prototype for CPI Augmentation` (Slate badge).
- **Mandatory Data Mode Indicator:** `Data Label: OBSERVED` (Emerald) | `SYNTHETIC` (Amber) | `DEMO` (Purple).
- **Palette:** Slate-900 background (`#0F172A`), Slate-800 cards, Indigo-500 primary, Emerald-500 market signal, Amber-500 warning, Rose-500 outlier/break.

---

## 3. Detailed Specification of Priority Core Screens

### Screen 1: Overview
- **Header Badge:** `AeroCPI Airfare Price Index` (Experimental prototype airfare measurement intended to augment CPI airfare measurement).
- **Metric Cards:**
  - Index Value (e.g. `104.25` base 100).
  - 1-Day Change (e.g. `+0.85%`).
  - Measurement Confidence Score (e.g. `91.5 / 100` High Integrity).
- **Main Chart:** Timeseries plot of AeroCPI Airfare Price Index vs 7-day Moving Average with confidence bands.

### Screen 2: Why Did It Move? (Counterfactual & Attribution)
- **Counterfactual Comparison Panel:**
  - Observed-Sample Index Change: `+1.45%`
  - Constant-Sample Counterfactual Index Change: `+1.30%`
  - Composition Shift Effect: `+0.15%`
- **Analytical Breakdown Chart:** Dual-line comparison showing Observed Index vs Constant-Sample Index (stable common sample between periods).
- **Composition Shifts:** Estimated impact associated with coverage, route composition, source composition, and lead-time horizon composition changes.
- **Disclaimer Banner:** `Analytical decomposition estimate; not a definitive causal attribution.`

### Screen 3: Index Integrity
- **Overall Confidence Meter:** Large radial score gauge ($91.5 / 100$).
- **8-Dimension Radar & Sub-Score Breakdown:** Observation Coverage, Route Coverage, Source Agreement, Trip Spec Compliance, Outlier Pressure, Missingness, Basket Stability, Horizon Stability.
- **Outlier Health Panel:** Percentage of quotes tagged `VALID`, `OUTLIER_FLAGGED`, `EXCLUDED`, `RETAINED_WITH_WARNING`.
- **Measurement Break Feed:** Alerts for carrier dropouts, source outages, or horizon blackouts.

### Screen 4: Methodology Lab
- **Interactive Controls:**
  - Formula Switch: `Young / Modified Laspeyres (Proxy Weighted)` vs `Jevons (Geometric Mean)`.
  - MAD Outlier Threshold Slider: $2.0 - 5.0$ (Default $3.5$).
  - Lead-Time Horizon Weight Sliders: Experimental allocation across T+1, T+7, T+15, T+30, T+45.
- **Sensitivity Comparison Chart:** Baseline AeroCPI Index vs Simulated Experimental Index.
- **Warning Banner:** `EXPERIMENTAL SIMULATION - NOT OFFICIAL MOSPI CPI`.

### Screen 5: Reproduce
- **Run Inspector:** Select historical `IndexRun`.
- **8-Part Manifest Inspector Card:** Displays Dataset Version, Methodology Version, Route Basket Version, Proxy Weight Version, Normalization Version, QC Version, Software Version, and Canonical Serialization Hash.
- **Interactive Action:** "Reproduce Index Run" button.
- **Verification Result Card:** Displays SHA-256 Run Fingerprint match check and floating-point tolerance check ($|I_{\text{reproduced}} - I_{\text{recorded}}| \le 10^{-4}$). Verdict: `VERIFIED EXACT MATCH`.

### Screen 6: Evidence-Grounded AI
- **Conversational Interface:** Query box for airfare movement inquiry.
- **Response View:** Markdown answer explaining movement via counterfactual decomposition.
- **Evidence Reference Badges:** Clickable inline citations pointing to explicit database IDs (`RunId`, `RouteId`, `QualityEventId`).
- **Safety Banner:** `Strict Evidence-Grounded AI Mode. Zero Hallucinations.`
