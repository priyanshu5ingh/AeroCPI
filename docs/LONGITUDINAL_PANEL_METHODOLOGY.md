# Longitudinal Panel Methodology & Data Acquisition Protocol

## 1. The Longitudinal Panel Principle

To train a legitimate, non-hallucinatory machine learning model for airfare price forecasting, the system requires genuine **temporal price evolution pairs** on fixed departure dates.

A single search date with multiple travel dates represents an *advance-purchase curve snapshot*, **not** a longitudinal price series.

$$\text{Snapshot: } P(t, d_1), P(t, d_2), \dots, P(t, d_k)$$
$$\text{Longitudinal Series: } P(t_1, d^*), P(t_2, d^*), \dots, P(t_m, d^*)$$

---

## 2. Pinned Departure Date Strategy

The longitudinal collector establishes a pinned manifest of calendar travel dates:

1. **Pinned Dates Generator**:
   - For any reference run date $t$, pins 14 calendar dates $d^* \in [t + 7, t + 20]$.
2. **Consecutive Daily Runs**:
   - At 10:00 AM IST daily, queries each $(r, d^*)$ pair across all monitored routes.
3. **Deterministic Comparability Signature**:
   $$\text{Signature} = \text{SHA256}(\text{Origin} \parallel \text{Destination} \parallel \text{TravelDate} \parallel \text{Cabin} \parallel \text{Adults} \parallel \text{Currency})[:16]$$
   Guarantees that quotes across consecutive days match identical flight specifications.

---

## 3. Forward Movement Target Construction

For a given route $r$ and pinned travel date $d^*$, after 7 consecutive collection runs:

$$\Delta P_{t+7} = P(t+7, d^*) - P(t, d^*)$$

$$\text{Target Class} = \begin{cases} 
\text{UP} & \text{if } \frac{\Delta P_{t+7}}{P(t, d^*)} > +0.03 \\
\text{DOWN} & \text{if } \frac{\Delta P_{t+7}}{P(t, d^*)} < -0.03 \\
\text{STABLE} & \text{otherwise}
\end{cases}$$

---

## 4. Operational Telemetry & Resilience

- **Cadence**: Daily at 10:00:00 UTC (15:30 IST)
- **Rate Limiting**: 2.0s sleep per request to prevent IP blocking
- **Error Isolation**: Failure on route $r_i$ does not abort route $r_{i+1}$
- **Immutability**: All panel runs are written to gzip JSON-Lines with SHA-256 manifest signatures
