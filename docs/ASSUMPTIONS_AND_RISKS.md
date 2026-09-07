# AeroCPI: Assumptions, Methodological Boundaries & Risk Matrix

**Document Version:** 1.1.0 (Methodological Review Revision)  

---

## 1. Disclaimers & Methodological Boundaries

> [!CAUTION]
> The following disclaimers define the legal and statistical scope of AeroCPI. These boundaries MUST be explicitly understood and presented to judges:

1. **Experimental Prototype Status:** AeroCPI is an **experimental/prototype airfare price measurement platform intended to augment CPI airfare measurement**. It is NOT the official Consumer Price Index (CPI) system compiled by MoSPI, nor does it claim to reproduce the complete official CPI compilation methodology.
2. **DGCA-Derived Proxy Weights vs Official CPI Weights:** Weights derived from DGCA passenger traffic reports are designated as **"DGCA-derived route-basket / traffic-share proxy weights"**. They represent passenger traffic volume shares across routes, NOT official MoSPI CPI household expenditure weights.
3. **No Official Booking Horizon Expenditure Weights:** No official MoSPI expenditure weights exist across advance booking lead times. The core SIH horizons are **T+1, T+7, T+15, T+30, T+45** days prior to departure. Any expenditure weighting applied across lead-time horizons during testing is **strictly experimental and configurable** within the Methodology Lab; no hardcoded horizon weights are represented as official MoSPI facts.
4. **Preservation of Raw Data:** Outlier flagging using MAD $> 3.5$ transitions observations into explicit workflow states (`VALID`, `OUTLIER_FLAGGED`, `EXCLUDED`, `RETAINED_WITH_WARNING`). Outliers are **NEVER automatically deleted**, and original raw observations remain permanently preserved in the store.
5. **SHA-256 Fingerprint Scope:** SHA-256 is used as a **dataset/run fingerprint** for execution tracking and manifest integrity, NOT as a proof of statistical correctness. Reproducibility verification applies a numerical floating-point comparison tolerance of $\epsilon = 10^{-4}$ ($0.0001$).
6. **Analytical Decomposition Disclaimer:** The Constant-Sample Counterfactual Index decomposes index movement into constant-sample price shifts vs composition shifts (coverage, route, source, horizon). This decomposition is presented as an **analytical signal decomposition**, NOT as a definitive causal attribution.

---

## 2. Remaining Unresolved Questions

1. **Dynamic Basket Re-indexing Frequency:** How frequently should DGCA passenger traffic share proxy weights be updated (e.g. quarterly vs annually) to balance basket stability against market relevance?
2. **Festival & Peak Demand Normalization:** How should advance booking lead-time curves (T+1 to T+45) be adjusted during major festive periods (e.g. Diwali, Durga Puja) when advance fares collapse into peak flat pricing?
3. **Multi-Leg / Connecting Route Representation:** Should non-stop domestic quotes be weighted separately from 1-stop connecting flights when calculating elementary Jevons price relatives for regional routes?

---

## 3. Risk Analysis & Mitigation Matrix

| Risk Factor | Impact | Likelihood | Mitigation Strategy in AeroCPI |
| :--- | :--- | :--- | :--- |
| **Confusing AeroCPI with Official CPI** | High | High | Display mandatory system nature header badge: `Experimental Prototype for CPI Augmentation`. |
| **Data Source Outage / Scraping Failure** | High | High | Trust Engine flags `MEASUREMENT_BREAK`, degrades confidence score, and triggers Counterfactual Index analysis. Prototype falls back to `SYNTHETIC` simulator mode. |
| **Dynamic Price Spikes (Single Seat Left)** | Medium | High | Preservative Quality Engine flags quotes with MAD $> 3.5$ as `OUTLIER_FLAGGED` / `EXCLUDED` with mandatory logged reasons, keeping raw data stored. |
| **AI Hallucination in Demo** | High | Low | Evidence AI Engine is strictly constrained by structured database evidence facts (`RunId`, `CounterfactualId`, `QualityEventId`). |
| **Floating-Point Comparison Failures Across Operating Systems** | Medium | Low | Reproducibility Engine uses canonical input serialization and applies an explicit numerical comparison tolerance ($\epsilon = 10^{-4}$). |
