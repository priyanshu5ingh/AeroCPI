# AeroCPI: SIH 2026 Presentation & Live Demo Script

**Project Name:** AeroCPI  
**Tagline:** Measure. Explain. Verify.  
**System Nature:** Experimental prototype airfare price measurement intended to augment CPI airfare measurement.  
**Target Duration:** 8 - 10 Minutes  

---

## Core Demo Sequence Matrix

| Step # | Screen / Action | Presenter Talking Point / Goal | Target Feature Demonstrated |
| :---: | :--- | :--- | :--- |
| **1** | Overview Screen | Introduce national **AeroCPI Airfare Price Index** (104.25) and daily movement (+0.85%). | AeroCPI Airfare Price Index |
| **2** | Audience Question | Ask SIH central question: *"Is this airfare movement real or a data collection artifact?"* | Core Problem Framing |
| **3** | Index Integrity Screen | Show **Measurement Confidence Score (91.5/100)** across 8 data health sub-dimensions. | Measurement Assurance |
| **4** | Why Did It Move? Screen | Present **Constant-Sample Counterfactual Index** comparison (Observed vs Constant-Sample). | Counterfactual Index Engine |
| **5** | Why Did It Move? Screen | Demonstrate breakdown: **Market Signal (+1.30%)** vs **Composition Shift (+0.15%)**. | Market vs Data Movement |
| **6** | Why Did It Move? Screen | Highlight route contributions (DEL-BOM, BLR-DEL) driving constant-sample shift. | Movement Attribution |
| **7** | Index Integrity Screen | Explain preservative outlier management (MAD > 3.5 default, 4 workflow statuses, 0 deletions). | Preservative Outlier System |
| **8** | Methodology Lab Screen | Test Jevons vs Young/Laspeyres formulas & T+1..T+45 lead times; observe sensitivity delta (-0.37). | Methodology Sensitivity Lab |
| **9** | Reproduce Screen | Inspect 8-part manifest, run canonical rerun, verify SHA-256 fingerprint & floating point match ($\epsilon \le 10^{-4}$). | Deterministic Reproducibility |
| **10** | Evidence AI Screen | Ask AI why index moved; highlight response citing explicit database entity IDs. | Evidence-Grounded AI |

---

## Step-by-Step Presentation Narrative

### Step 1 - 2: AeroCPI Index Movement & Core Question
- **Action:** Open Dashboard to `Overview`.
- **Narrative:** *"Honorable Judges, welcome to AeroCPI: Measure, Explain, Verify. We present an experimental prototype airfare price measurement intended to augment Consumer Price Index airfare measurement. Here is our live AeroCPI Airfare Price Index standing at 104.25, showing a +0.85% movement today. But whenever an airfare index moves, statisticians must ask: Is this movement real market inflation, or is it caused by missing quotes, source outages, or booking lead-time changes?"*

### Step 3 - 5: Trust Engine, Counterfactual Index & Signal Breakdown
- **Action:** Navigate to `Index Integrity` (Score: 91.5/100) -> Switch to `Why Did It Move?`.
- **Narrative:** *"AeroCPI answers this through our 4-pillar Trust Engine. First, our Measurement Confidence Score proves data health is high at 91.5/100. Second, we run a Constant-Sample Counterfactual Index. By comparing the index on the full observed sample against a stable common sample across periods, we isolate the movement: +1.30% is true Market Signal, while +0.15% is composition shift. We can confidently assert: The index movement is real."*

### Step 6 - 7: Route Attribution & Preservative Outliers
- **Action:** Point to route contribution bars -> Open Outlier Health Panel on `Index Integrity`.
- **Narrative:** *"Route DEL-BOM, weighted by its DGCA-derived passenger traffic share proxy, accounts for 55% of the movement. Crucially, our Quality Engine never deletes outlier price quotes. Using MAD > 3.5 statistical flagging, observations transition through explicit statuses—VALID, OUTLIER_FLAGGED, EXCLUDED, RETAINED_WITH_WARNING—with all raw data preserved intact."*

### Step 8: Methodology Lab Sensitivity Analysis
- **Action:** Open `Methodology Lab` -> Change formula to Jevons -> View sensitivity delta.
- **Narrative:** *"In our Methodology Lab, statisticians can test alternative formulas—Jevons geometric mean vs Young/Laspeyres—and experiment with T+1 through T+45 lead time windows. Notice the experimental banner clearly indicating that what-if simulations are distinct from baseline reference calculations."*

### Step 9: Deterministic Reproducibility & 8-Part Manifest
- **Action:** Open `Reproduce` -> Click `Reproduce Index Run`.
- **Narrative:** *"For strict statistical auditing, SHA-256 serves as a run fingerprint. A run is reproducible if and only if its 8-part manifest—dataset, methodology, route basket, proxy weights, normalization, QC, software version, and canonical serialization—can be rerun. Watch as the system recalculates the index and verifies an exact match within a floating-point tolerance of epsilon = 10^-4."*

### Step 10: Evidence-Grounded AI Explanation
- **Action:** Open `Evidence AI` -> Ask *"Why did the national airfare index rise today?"*.
- **Narrative:** *"Finally, our Evidence-Grounded AI translates statistical evidence into narrative explanations. Notice that the AI does NOT invent numbers. It references explicit database IDs from our counterfactual decomposition and quality logs. Data leads to statistics, statistics create evidence, and AI explains the evidence."*
