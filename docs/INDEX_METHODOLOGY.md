# AeroCPI: Airfare Index Methodology & Mathematical Formulation

**Document Version:** 2.0.0 (Milestone 2 Quality & Index Engine Revision)  
**System Classification:** Experimental prototype airfare price measurement intended to augment CPI airfare measurement.  

---

## 1. Overview & Statistical Foundations

The **AeroCPI Airfare Price Index** provides high-frequency measurement of domestic airfare movements across India. AeroCPI does **NOT** claim to be the official Consumer Price Index (CPI) compiled by MoSPI, nor does it claim to reproduce the complete official CPI compilation methodology.

---

## 2. Quality Engine & Preservative Outlier Logic

### 2.1 MAD Outlier Detection Formula
Outlier detection utilizes the **Modified Z-Score via Median Absolute Deviation (MAD)** for observation $x_i$:

$$\text{MAD} = \text{median}\left( |x_i - \text{median}(x)| \right)$$

$$M_i = 0.6745 \cdot \frac{x_i - \text{median}(x)}{\text{MAD}}$$

- **Statistical Flag Threshold:** $|M_i| > 3.5$.
- **Grouping Rule:** MAD outlier detection is calculated strictly within comparable comparison groups:
  $$\text{Group} = (\text{route\_id}, \text{travel\_date}, \text{booking\_horizon\_days}, \text{cabin}, \text{stop\_type})$$
- **MAD = 0 Handling:** When all prices in a comparison group are identical ($\text{MAD} = 0$), $M_i = 0.0$. If a single price deviates from a flat median group, $M_i = 999.0$, flagging the outlier without division-by-zero crashes. Single observation groups ($N=1$) receive $M_i = 0.0$.

### 2.2 Preservative Outlier Workflow
Outliers are **NEVER automatically deleted**. The raw observation remains permanently stored in the database. Observations transition through explicit statuses:
- `VALID`: Normal observation ($|M_i| \le 3.5$) included in index compilation.
- `OUTLIER_FLAGGED`: Flagged statistical outlier ($|M_i| > 3.5$). Retained with warning flag unless extreme.
- `EXCLUDED`: Excluded from final index calculation with a mandatory logged reason (e.g. `EXTREME_MAD_OUTLIER_SCORE_12.5`).
- `RETAINED_WITH_WARNING`: Retained in index calculation with analytical warning flag.

### 2.3 Deterministic Duplicate Detection Rule
Two observations are marked as duplicates if they share identical values across:
`source_id, route_id, carrier_id, travel_date, booking_horizon_days, cabin, trip_type, fare_class, stop_type, total_fare`.

Subsequent duplicate occurrences are marked `duplicate_flag = True`, assigned status `EXCLUDED`, and logged with `exclusion_reason = "DUPLICATE_OBSERVATION"`. Original raw observations remain preserved in the store.

---

## 3. Elementary & Higher-Level Index Formulations

### 3.1 Elementary Index (Jevons Geometric Mean)
For elementary comparison groups (price quotes on a specific route, lead-time horizon, cabin, and stop type), AeroCPI uses the unweighted **Jevons Geometric Mean Index**:

Logarithmic price relative formulation:

$$\ln(J_g) = \frac{1}{N_g} \sum_{i=1}^{N_g} \ln \left( \frac{p_{t,i}}{p_{0,i}} \right)$$

$$J_g = \exp(\ln(J_g))$$

$$\text{Elementary Index } I_{g,t} = 100 \times J_g$$

- **Numerical Stability Rules:** Validates that all prices $> 0$, verifies no invalid logarithms, and sorts price relatives deterministically prior to summation.

### 3.2 Route-Level Index
Preserves directional route identity (`DEL-BOM` $\ne$ `BOM-DEL`) and produces route-level price index values reproducible from underlying eligible observations.

### 3.3 Higher-Level Aggregation (Young / Modified Laspeyres Index)
National index compilation aggregates route-level price relatives using **DGCA-derived route-basket / traffic-share proxy weights** ($w_r^{\text{proxy}}$):

$$I_t^{\text{AeroCPI}} = \left( \sum_{r=1}^{R} w_r^{\text{proxy}} \cdot \frac{P_{r,t}}{P_{r,0}} \right) \times 100$$

- **Proxy Weight Validation:** System validates that $\sum_{r} w_r^{\text{proxy}} = 1.0 \pm 0.001$. Calculation fails loudly if weights do not sum to 1.0 within tolerance.

---

## 4. Dataset Versioning & Index Run Fingerprinting

Every index calculation generates an immutable **IndexRun** record bound to a **DatasetVersion**.
- **Run Fingerprint (SHA-256):** Computed across canonical JSON string containing reference period, comparison period, dataset version ID, route basket version, proxy weight version, methodology version, software version (`0.2.0-milestone2`), and sorted route index results.
- **Scope:** Fingerprint is an integrity identifier verifying execution tracking and data payload consistency, NOT proof of statistical correctness.
