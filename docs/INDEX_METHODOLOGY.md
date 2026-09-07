# AeroCPI: Airfare Index Methodology & Mathematical Formulation

**Document Version:** 1.1.0 (Methodological Review Revision)  
**System Classification:** Experimental prototype airfare price measurement intended to augment CPI airfare measurement.  

---

## 1. Overview & Methodological Scope

The **AeroCPI Airfare Price Index** provides high-frequency measurement of domestic airfare movements across India. AeroCPI does **NOT** claim to be the official Consumer Price Index (CPI) compiled by MoSPI, nor does it claim to reproduce the complete official CPI compilation methodology.

---

## 2. Virtual Trip Standardization & Booking Horizons

To ensure price quotes compare like-for-like products, all raw quotes are normalized to a **Virtual Trip Specification**:
- **Cabin Class:** Economy Standard.
- **Baggage Standard:** 1 piece check-in baggage (15kg).
- **Refundability:** Non-refundable standard fare.
- **Core SIH Booking Horizons:**
  $$h \in \{\text{T}+1, \text{T}+7, \text{T}+15, \text{T}+30, \text{T}+45\}$$
  (Days prior to flight departure).

> [!IMPORTANT]
> **No official MoSPI booking-horizon expenditure weights exist.**
> AeroCPI does NOT hardcode or assert invented weights (e.g. 10/25/35/20/10) as official MoSPI weights.
> Any lead-time horizon aggregation used during testing is **strictly experimental and user-configurable** within the Methodology Lab.

---

## 3. Elementary & Higher-Level Index Formulations

### 3.1 Elementary Index (Jevons Formula)
At the elementary aggregate level (item quotes on a given route $r$ and lead-time horizon $h$ where individual quantity weights are unobserved), AeroCPI uses the unweighted **Jevons Geometric Mean Index**:

$$P_{r,h,t}^J = \prod_{k=1}^{N_{r,h,t}} \left( p_{k,r,h,t} \right)^{\frac{1}{N_{r,h,t}}}$$

Relative price ratio for route $r$ and horizon $h$:

$$R_{r,h,t} = \frac{P_{r,h,t}^J}{P_{r,h,0}^J}$$

### 3.2 Higher-Level Aggregation (Young / Modified Laspeyres Index)
For higher-level index compilation across routes into the national **AeroCPI Airfare Price Index**, AeroCPI applies a **Young or Modified Laspeyres-style Index** using **DGCA-derived route-basket / traffic-share proxy weights**:

$$I_t^{\text{AeroCPI}} = \left( \sum_{r=1}^{R} w_r^{\text{proxy}} \cdot \frac{P_{r,t}}{P_{r,0}} \right) \times 100$$

Where:
- $w_r^{\text{proxy}}$ represents route $r$'s share of national passenger traffic derived from public DGCA traffic volume reports.
- **Clarification:** $w_r^{\text{proxy}}$ represents *passenger traffic share*, NOT official CPI household expenditure weights.

---

## 4. Preservative Outlier & Quality Management

Dynamic pricing algorithms in aviation occasionally produce extreme prices (e.g. single remaining seat sold at $5\times$ normal price).

### 4.1 Statistical Flagging Threshold
Outlier flagging utilizes the **Modified Z-Score via Median Absolute Deviation (MAD)**:

$$\text{MAD}_{r,h,t} = \text{median}\left( |p_{i,r,h,t} - \text{median}(p_{i,r,h,t})| \right)$$

$$M_{i,r,h,t} = \frac{0.6745 \cdot (p_{i,r,h,t} - \text{median}(p_{i,r,h,t}))}{\text{MAD}_{r,h,t}}$$

Initial default statistical flag threshold: **$|M_{i,r,h,t}| > 3.5$**.

### 4.2 Workflow Statuses & Preservation Rule
Outliers are **NEVER automatically deleted**. The raw observation remains stored in the database. Observations transition through explicit statuses:

1. `VALID`: Clean observation included in index compilation.
2. `OUTLIER_FLAGGED`: Exceeds MAD 3.5 threshold; flagged for statistical review.
3. `EXCLUDED`: Excluded from final calculation. Requires an explicit logged reason (e.g., `MAD_EXCEEDED_3.5_EXTREME_SPIKE`).
4. `RETAINED_WITH_WARNING`: Retained in calculation with an analytical warning flag.

---

## 5. Summary of Methodological Boundaries

| Aspect | AeroCPI Implementation | Official MoSPI CPI Boundary |
| :--- | :--- | :--- |
| **Index Name** | AeroCPI Airfare Price Index | Official Consumer Price Index (CPI) |
| **Scope** | Prototype airfare price measurement for CPI augmentation | National macro-economic inflation benchmark |
| **Route Weights** | DGCA-derived route-basket / traffic-share proxy weights | Secret / Official household expenditure weights |
| **Lead Times** | Configurable experimental horizons (T+1, T+7, T+15, T+30, T+45) | Official survey methodology |
| **Elementary Index** | Jevons Geometric Mean | Official elementary aggregate rule |
| **Outliers** | Preservative 4-state workflow (MAD > 3.5 default) | Official statistical audit protocol |
