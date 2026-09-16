# Milestone Freeze: AeroGuide Longitudinal Panel Foundation
**Tag**: `milestone-aeroguide-longitudinal-panel-foundation`  
**Date**: 2026-09-16  
**Status**: Certified & Frozen  

---

## 1. System Invariants & Certification

- **Backend Test Suite**: 275 / 275 passed (100% green).
- **Frontend TypeScript**: 0 errors (`npx tsc --noEmit`).
- **Frontend Production Build**: Clean build (`npm run build`).
- **Controlled Panel**: 10 Tier-1 Core Corridors × 14 Pinned Departure Dates (2026-10-01 to 2026-10-14) = 140 persistent trajectories.
- **Valid 7-Day Target Pairs**: 0 (Strict chronological invariant: t2 - t1 >= 7 days).
- **Effective Forecasting Examples**: 0 (Zero synthetic forecasts / zero fake probabilities).
- **Model Training Status**: DISABLED (Gated until >= 7 empirical target pairs).
- **Canonical Readiness Source of Truth**: Harmonized across Database -> API (/readiness) -> Decision Trace (Stage 7).

---

## 2. Dual-Target Formulation

The trajectory evaluation engine computes two complementary targets:
1. **Market-Level Target**: Delta P_market = Median(t+7) - Median(t)
2. **Matched-Carrier Target**: Delta P_carrier = P_c(t+7) - P_c(t) for identical carrier c.
