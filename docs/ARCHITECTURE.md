# AeroCPI: System Architecture Document

**Document Version:** 1.1.0 (Methodological Review Revision)  
**Status:** Approved Architecture Draft  

---

## 1. System Pipeline Overview

AeroCPI processes raw airfare price quotes into a verifiable, high-integrity experimental airfare price index through a unidirectional 12-stage pipeline. Each stage is strictly isolated with clear input and output data contracts, guaranteeing data lineage from raw collection to AI explanation.

```
       +-------------------------------------------------------------+
       | 1. DATA SOURCES & ETHICAL INGESTION ENGINE                  |
       +-------------------------------------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       | 2. RAW OBSERVATION STORE (Append-Only PostgreSQL)           |
       +-------------------------------------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       | 3. VIRTUAL TRIP STANDARDIZER (T+1, T+7, T+15, T+30, T+45)   |
       +-------------------------------------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       | 4. FARE NORMALIZATION ENGINE                                |
       +-------------------------------------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       | 5. QUALITY & OUTLIER ENGINE (MAD > 3.5 Status Management)   |
       +-------------------------------------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       | 6. INDEX COMPUTATION ENGINE (Jevons & Young/Laspeyres)      |
       +-------------------------------------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       | 7. TRUST & MEASUREMENT ASSURANCE ENGINE                     |
       |    ├── A. Measurement Confidence                            |
       |    ├── B. Constant-Sample Counterfactual Index              |
       |    ├── C. Measurement Break Detection                       |
       |    └── D. Movement Attribution                              |
       +-------------------------------------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       | 8. DETERMINISTIC PROVENANCE & REPRODUCIBILITY ENGINE        |
       +-------------------------------------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       | 9. METHODOLOGY LAB & SENSITIVITY SANDBOX                    |
       +-------------------------------------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       | 10. EVIDENCE-GROUNDED AI ENGINE                             |
       +-------------------------------------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       | 11. FASTAPI REST GATEWAY                                    |
       +-------------------------------------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       | 12. STATISTICAL DASHBOARD (6 Core Prioritized UI Screens)   |
       +-------------------------------------------------------------+
```

---

## 2. Stage Breakdown & Component Specifications

### Stage 1: Data Sources & Ethical Ingestion Engine
- Ingests raw airfare quotes via public APIs, permitted partner feeds, and synthetic fallback generators.
- Labels all data batches: `OBSERVED`, `FROZEN`, `OFFICIAL`, `SYNTHETIC`, `DEMO`.
- Strictly adheres to `robots.txt` and open access rules (no CAPTCHA bypass).

### Stage 2: Raw Observation Store
- Immutable, append-only PostgreSQL store preserving original raw observations intact regardless of subsequent quality filtering or exclusion.

### Stage 3: Virtual Trip Standardizer
- Standardizes quotes onto Virtual Trip Specifications across core SIH booking lead times:
  $$h \in \{\text{T}+1, \text{T}+7, \text{T}+15, \text{T}+30, \text{T}+45\}$$
- Maps fare rules, cabin class (Economy Standard), and 15kg baggage allowance.

### Stage 4: Fare Normalization Engine
- Decomposes price quotes:
  $$\text{Normalized Fare} = \text{Base Fare} + \text{Mandatory Surcharges} - \text{Promotional Discounts} + \text{Baggage Standard Adjustment}$$

### Stage 5: Quality & Outlier Engine
- Applies Modified Z-Score using Median Absolute Deviation (MAD):
  $$M_i = \frac{0.6745 \cdot (x_i - \tilde{x})}{\text{MAD}}$$
- Initial default statistical flag threshold is $M_i > 3.5$.
- **Outliers are NEVER automatically deleted.** Observations transition between explicit workflow statuses:
  - `VALID`: Clean observation, included in index aggregation.
  - `OUTLIER_FLAGGED`: Exceeds MAD 3.5 threshold, flagged for review.
  - `EXCLUDED`: Excluded from final calculation with logged reason (e.g., `MAD_EXCEEDED_3.5_EXTREME_SPIKE`).
  - `RETAINED_WITH_WARNING`: Outlier retained in aggregation with an analytical warning flag.
- Raw observations remain permanently stored in Stage 2.

### Stage 6: Index Computation Engine
- **Elementary Indices (Item Level):** Calculated using the Jevons geometric mean formula across elementary aggregates where individual expenditure weights are unobserved.
- **Higher-Level Aggregation:** Calculated using Young or Modified Laspeyres-style formulas using **DGCA-derived route-basket / traffic-share proxy weights**.
- Does NOT claim to reproduce complete official CPI compilation methodology.

### Stage 7: Trust & Measurement Assurance Engine
Architected into 4 core pillars:
1. **Measurement Confidence:** Evaluates 8 data health metrics ($0-100$ score).
2. **Constant-Sample Counterfactual Index:** Computes index on a stable/common sample across periods ($I_t^{\text{counterfactual}}$) to compare against the observed-sample index ($I_t^{\text{observed}}$), quantifying movement linked to coverage/composition shifts.
3. **Measurement Break Detection:** Flags carrier dropouts, source outages, or horizon blackouts.
4. **Movement Attribution:** Decomposes index movement across routes, booking horizons, and carriers (presented as analytical decomposition, not definitive causality).

### Stage 8: Deterministic Provenance & Reproducibility Engine
- Uses SHA-256 as a **dataset/run fingerprint** (not proof of statistical correctness).
- Binds run execution to an 8-part manifest:
  $$\text{Run Fingerprint} = \text{SHA256}(\text{DatasetVersion} \parallel \text{MethodologyVersion} \parallel \text{RouteBasketVersion} \parallel \text{ProxyWeightVersion} \parallel \text{NormalizationVersion} \parallel \text{QCVersion} \parallel \text{CodeVersion} \parallel \text{CanonicalInputSerialization})$$
- Verification rerun compares newly computed index against original index using a floating-point tolerance of $\epsilon = 10^{-4}$ ($0.0001$).

### Stage 9: Methodology Lab & Sensitivity Sandbox
- Interactive environment for what-if sensitivity analysis (e.g. formula swapping, MAD threshold adjustments, proxy weight alterations). Outputs explicitly tagged `EXPERIMENTAL_SIMULATION`.

### Stage 10: Evidence-Grounded AI Engine
- Generates analytical explanations referencing explicit database IDs (`IndexRunId`, `RouteId`, `QualityEventId`). Operating in zero-hallucination grounded mode.

### Stage 11 & 12: API & Prioritized Frontend UI
- FastAPI REST gateway exposing OpenAPI endpoints.
- React frontend prioritized across 6 core screens: **Overview**, **Why Did It Move?**, **Index Integrity**, **Methodology Lab**, **Reproduce**, **Evidence-Grounded AI**.
