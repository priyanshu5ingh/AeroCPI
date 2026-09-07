# AeroCPI: Trust & Measurement Assurance Engine Specification

**Document Version:** 1.1.0 (Methodological Review Revision)  
**Core Architecture:** 4 Pillars of Measurement Assurance  

---

## 1. Trust Engine Architecture Overview

The **AeroCPI Trust & Measurement Assurance Engine** evaluates the statistical health, composition stability, and reproducibility of every calculated `IndexRun`.

The engine is structured around **4 core pillars**:

```
+---------------------------------------------------------------------------------+
|                    AEROCPI TRUST & MEASUREMENT ASSURANCE ENGINE                  |
+---------------------------------------------------------------------------------+
        │                         │                         │                         │
        ▼                         ▼                         ▼                         ▼
+---------------+       +-------------------+     +-------------------+     +------------------+
| 1. MEASUREMENT|       | 2. CONSTANT-SAMPLE|     | 3. MEASUREMENT    |     | 4. MOVEMENT      |
|    CONFIDENCE |       |    COUNTERFACTUAL |     |    BREAK DETECTION|     |    ATTRIBUTION   |
|    SCORE      |       |    INDEX          |     |                   |     |                  |
+---------------+       +-------------------+     +-------------------+     +------------------+
```

---

## 2. Pillar 1: Measurement Confidence Score

Evaluates data collection health across 8 empirical sub-dimensions into a composite score ($C_{\text{run}} \in [0, 100]$):

$$C_{\text{run}} = \sum_{k=1}^{8} \alpha_k \cdot S_k$$

Sub-dimensions evaluated:
1. **Observation Coverage ($S_{\text{obs}}$):** Actual vs target quota.
2. **Route Coverage ($S_{\text{route}}$):** Active basket routes ratio.
3. **Source Agreement ($S_{\text{source}}$):** Cross-source quote agreement.
4. **Trip Spec Compliance ($S_{\text{spec}}$):** Compliance with Virtual Trip specs.
5. **Outlier Pressure ($S_{\text{outlier}}$):** Proportion of quotes flagged ($M_i > 3.5$).
6. **Missingness Score ($S_{\text{missing}}$):** Density of Carrier $\times$ Route $\times$ Horizon matrix.
7. **Basket Stability ($S_{\text{basket}}$):** Proxy route weight contribution stability.
8. **Horizon Stability ($S_{\text{horizon}}$):** Representation across T+1, T+7, T+15, T+30, T+45 lead times.

---

## 3. Pillar 2: Constant-Sample / Counterfactual Index

The Counterfactual Index engine provides a first-class analytical comparison between:
- **Index A (Observed-Sample Index $I_t^{\text{observed}}$):** Index calculated on all valid observations available in period $t$.
- **Index B (Constant-Sample Index $I_t^{\text{counterfactual}}$):** Index calculated using *only* the stable/common sample of routes, carriers, sources, and booking horizons present in *both* period $t-1$ and period $t$.

### Analytical Decomposition Algorithm
$$\Delta I_{\text{total}} = I_t^{\text{observed}} - I_{t-1}^{\text{observed}}$$

$$\Delta I_{\text{counterfactual}} = I_t^{\text{counterfactual}} - I_{t-1}^{\text{observed}}$$

$$\Delta I_{\text{composition\_shift}} = I_t^{\text{observed}} - I_t^{\text{counterfactual}}$$

This estimates how much observed movement may be associated with:
- Coverage changes (e.g. source outage)
- Route composition changes
- Source composition changes
- Booking-horizon composition changes (e.g. shift from T+30 to T+1)

> [!IMPORTANT]
> This decomposition is presented as an **analytical signal decomposition**, NOT as a definitive causal attribution.

---

## 4. Pillar 3: Measurement Break Detection

Structural disruption triggers:
1. **Carrier Dropout:** Major carrier quotes drop $> 50\%$ relative to 7-day moving average.
2. **Source Outage:** Primary data source fails for $> 6$ consecutive hours.
3. **Horizon Blackout:** Any core horizon (T+1, T+7, T+15, T+30, T+45) missing across $\ge 20\%$ of routes.

Detected breaks generate a `MeasurementBreak` record and append an analytical warning banner.

---

## 5. Pillar 4: Movement Attribution

Decomposes the constant-sample index change ($\Delta I_{\text{counterfactual}}$) into itemized contributions by:
- **Route Contribution:** $\text{Contr}_r = w_r^{\text{proxy}} \cdot (R_{r,t} - R_{r,t-1})$
- **Booking Horizon Contribution:** Lead-time sensitivity.
- **Carrier Price Contribution:** Carrier price changes on shared routes.

---

## 6. Deterministic Provenance & Reproducibility Engine

### 6.1 Role of SHA-256 Fingerprint
> [!NOTE]
> SHA-256 serves as a **dataset/run fingerprint** to verify payload integrity and execution tracking. It is **NOT** a proof of statistical correctness.

### 6.2 The 8-Part Reproducibility Manifest
A run is reproducible if and only if the exact execution environment can be reconstructed using:
1. `DatasetVersion` (raw immutable dataset hash)
2. `MethodologyVersion` (formula specification: Jevons / Young-Laspeyres)
3. `RouteBasketVersion` (included route definitions)
4. `ProxyWeightVersion` (DGCA-derived proxy weight matrix)
5. `NormalizationVersion` (Virtual Trip spec mapping rules)
6. `QCVersion` (MAD 3.5 threshold & status rules)
7. `SoftwareVersion` (Git commit SHA of code pipeline)
8. `CanonicalInputSerialization` (Deterministic JSON/CSV row ordering)

$$\text{Run Fingerprint} = \text{SHA256}(\text{Manifest}_1 \parallel \text{Manifest}_2 \parallel \dots \parallel \text{Manifest}_8)$$

### 6.3 Verification & Floating-Point Comparison Tolerance
During rerun verification (`POST /api/v1/reproduce/{run_id}`), floating-point calculations across hardware environments are compared using an explicit numerical tolerance:

$$|I_{\text{reproduced}} - I_{\text{recorded}}| \le \epsilon = 10^{-4} \quad (0.0001)$$

- If $|I_{\text{reproduced}} - I_{\text{recorded}}| \le 10^{-4}$ and Run Fingerprints match $\rightarrow$ `VERIFIED_MATCH`.
- Else $\rightarrow$ `REPRODUCIBILITY_DISCREPANCY` with itemized numerical diff.
