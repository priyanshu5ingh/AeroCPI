# AeroCPI: REST API Contract Specification

**Document Version:** 1.1.0 (Methodological Review Revision)  
**Protocol:** HTTP REST / JSON  
**Base Path:** `/api/v1`  

---

## 1. Overview & Standard Headers

The AeroCPI API exposes endpoints for querying the **AeroCPI Airfare Price Index**, 4-pillar trust engine metrics, counterfactual analysis, methodology lab simulations, reproducibility checks, and evidence-grounded AI explanations.

### Standard Headers
- `Content-Type: application/json`
- `X-AeroCPI-Data-Mode: OBSERVED | DEMO | SYNTHETIC`

---

## 2. Priority API Endpoints Specification

### 2.1 National Index Timeseries
`GET /api/v1/indices/national`

#### Response Body (`200 OK`)
```json
{
  "status": "success",
  "data_label": "OBSERVED",
  "index_name": "AeroCPI Airfare Price Index",
  "total_records": 30,
  "series": [
    {
      "effective_date": "2026-03-01",
      "run_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "index_value": 104.250,
      "prev_day_change_pct": 0.85,
      "confidence_score": 91.50,
      "is_frozen": true,
      "run_fingerprint": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0"
    }
  ]
}
```

---

### 2.2 Index Execution & Quality Summary Endpoints (Milestone 2)

#### 2.2.1 Create / Execute Index Run
`POST /api/v1/index-runs`

**Request Body:**
```json
{
  "reference_period": "2026-08-01",
  "comparison_period": "2026-09-01",
  "dataset_version_id": "DS-20260907-001",
  "proxy_weight_version": "DGCA_PROXY_2026_V1",
  "route_basket_version": "BASKET_2026_Q1"
}
```

**Response Body (`201 Created`):**
```json
{
  "run_id": "f377137e-72fc-4bbf-8527-918922b7f5a4",
  "run_timestamp": "2026-09-07T13:35:43Z",
  "reference_period": "2026-08-01",
  "comparison_period": "2026-09-01",
  "dataset_version": "DS-20260907-001",
  "proxy_weight_version": "DGCA_PROXY_2026_V1",
  "route_basket_version": "BASKET_2026_Q1",
  "methodology_version": "YOUNG_LASPEYRES_V1",
  "quality_rule_version": "MAD_3.5_V1",
  "index_method": "JEVONS_ELEMENTARY_YOUNG_NATIONAL",
  "index_name": "AeroCPI Airfare Price Index",
  "classification": "Experimental prototype airfare price measurement intended to augment CPI airfare measurement.",
  "number_of_observations": 401,
  "number_of_eligible_observations": 394,
  "number_of_excluded_observations": 7,
  "index_value": 107.717,
  "canonical_run_fingerprint": "1647aacffab35892cea8581bc80d5d5b72413963223b3b206edb97a8f63e9dc1",
  "software_version": "0.2.0-milestone-2"
}
```

#### 2.2.2 List Index Runs
`GET /api/v1/index-runs`

#### 2.2.3 Get Index Run Details
`GET /api/v1/index-runs/{run_id}`

#### 2.2.4 Get Route-Level Index Breakdown
`GET /api/v1/index-runs/{run_id}/routes`

#### 2.2.5 Get Underlying Observations for Index Run
`GET /api/v1/index-runs/{run_id}/observations`

#### 2.2.6 Get Quality Summary for Index Run
`GET /api/v1/index-runs/{run_id}/quality-summary`

**Response Body (`200 OK`):**
```json
{
  "total_observations": 401,
  "eligible_observations": 394,
  "excluded_observations": 7,
  "outlier_flagged_observations": 4,
  "retained_with_warning_observations": 0,
  "duplicate_observations": 3,
  "missing_incomplete_observations": 0,
  "coverage_ratio": 0.9825
}
```

---

### 2.3 Constant-Sample Counterfactual & Movement Breakdown
`GET /api/v1/runs/{run_id}/movement-breakdown`

Retrieves the 4-pillar Trust Engine movement analysis, comparing observed sample index vs constant-sample counterfactual index.

#### Response Body (`200 OK`)
```json
{
  "run_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "observed_sample_index": 104.250,
  "constant_sample_index": 104.100,
  "total_index_change_pct": 1.45,
  "constant_sample_change_pct": 1.30,
  "composition_shift_pct": 0.15,
  "analytical_verdict": "CONSTANT_SAMPLE_STABLE",
  "composition_effect_breakdown": {
    "coverage_effect_pct": 0.05,
    "route_composition_effect_pct": 0.04,
    "source_composition_effect_pct": 0.03,
    "horizon_composition_effect_pct": 0.03
  },
  "disclaimer": "Analytical decomposition estimate; not a definitive causal attribution."
}
```

---

### 2.3 Index Integrity & 8-Dimension Confidence
`GET /api/v1/runs/{run_id}/integrity`

#### Response Body (`200 OK`)
```json
{
  "run_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "overall_confidence_score": 91.50,
  "sub_scores": {
    "observation_coverage": 95.00,
    "route_coverage": 100.00,
    "source_agreement": 88.50,
    "trip_spec_compliance": 98.00,
    "outlier_pressure": 92.00,
    "missingness": 94.00,
    "basket_stability": 97.00,
    "horizon_stability": 85.00
  },
  "detected_breaks": []
}
```

---

### 2.4 Methodology Lab Simulation
`POST /api/v1/lab/simulate`

Executes a what-if sensitivity analysis across formulas, MAD thresholds, or proxy weights.

#### Request Body
```json
{
  "dataset_version_id": "DS-2026-03-01-V1",
  "formula_type": "JEVONS",
  "outlier_mad_threshold": 3.5,
  "experimental_horizon_weights": {
    "T+1": 0.10,
    "T+7": 0.25,
    "T+15": 0.35,
    "T+30": 0.20,
    "T+45": 0.10
  }
}
```

#### Response Body (`200 OK`)
```json
{
  "simulation_status": "EXPERIMENTAL_SIMULATION",
  "baseline_index_value": 104.250,
  "simulated_index_value": 103.880,
  "delta_index": -0.370,
  "formula_used": "JEVONS"
}
```

---

### 2.5 Deterministic Index Run Reproducibility
`POST /api/v1/reproduce/{run_id}`

Re-evaluates execution manifest and computes floating-point comparison with $\epsilon = 10^{-4}$ tolerance.

#### Response Body (`200 OK`)
```json
{
  "target_run_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "manifest": {
    "dataset_version": "DS-2026-03-01-V1",
    "methodology_version": "YOUNG_LASPEYRES_V1",
    "route_basket_version": "BASKET_2026_Q1",
    "proxy_weight_version": "DGCA_PROXY_2026_V1",
    "normalization_version": "NORM_V1",
    "qc_version": "MAD_3.5_V1",
    "software_version": "git-commit-a1b2c3d",
    "canonical_serialization_hash": "c1d2e3f4..."
  },
  "recorded_fingerprint": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
  "reproduced_fingerprint": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
  "recorded_index_value": 104.2500,
  "reproduced_index_value": 104.2500,
  "floating_point_delta": 0.0000,
  "tolerance_epsilon": 0.0001,
  "is_reproducible_match": true,
  "verdict": "VERIFIED_EXACT_MATCH"
}
```

---

### 2.6 Evidence-Grounded AI Explanation
`POST /api/v1/ai/explain`

#### Response Body (`200 OK`)
```json
{
  "run_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "explanation_markdown": "The +0.85% movement in the AeroCPI Airfare Price Index (Run ID `9b1deb4d`) was analyzed using the Constant-Sample Counterfactual Index.\n\n- Observed Sample Index change: +1.45%\n- Constant Sample Counterfactual Index change: +1.30%\n- Estimated composition shift effect: +0.15%\n\nThis confirms that 89% of the measured shift represents genuine market fare increases on DEL-BOM and BLR-DEL, rather than coverage or source changes.",
  "evidence_chain": [
    {
      "evidence_type": "COUNTERFACTUAL_DECOMPOSITION",
      "constant_sample_change_pct": 1.30,
      "composition_shift_pct": 0.15
    }
  ],
  "grounded_verification_status": "FULLY_GROUNDED"
}
```
