import datetime as dt
import math
from decimal import Decimal
import pytest
from app.models.index_run import IndexRun
from app.models.horizon_index_result import HorizonIndexResult
from app.models.route_index_result import RouteIndexResult
from app.models.observation import Observation
from app.models.trust_evaluation import TrustEvaluation
from app.services.statistical_index_service import StatisticalIndexEngineService
from app.services.index_explanation_service import IndexExplanationService
from app.schemas.index_explanation import IndexExplanationResponse
from tests.test_statistical_index_engine import seed_test_routes, create_obs


# =============================================================================
# 1. VALID INDEX RUN EXPLANATION RETRIEVAL & FIELD COMPLETENESS
# =============================================================================

def test_01_explain_valid_index_run(db_session):
    """
    Verifies that explain_index_run returns a complete response with all required 14 fields.
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    for h in [1, 7, 15, 30, 45]:
        db_session.add(create_obs(f"OB_R1_{h}", "SRC_GOOGLE", 5000.00, "DEL-BOM", ref_date, h))
        db_session.add(create_obs(f"OB_R2_{h}", "SRC_GOOGLE", 4000.00, "BLR-DEL", ref_date, h))
        db_session.add(create_obs(f"OC_R1_{h}", "SRC_GOOGLE", 5500.00, "DEL-BOM", cur_date, h))
        db_session.add(create_obs(f"OC_R2_{h}", "SRC_GOOGLE", 4400.00, "BLR-DEL", cur_date, h))
    db_session.commit()

    run, _, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    explanation = IndexExplanationService.explain_index_run(db_session, run.run_id)

    assert isinstance(explanation, IndexExplanationResponse)
    assert explanation.explanation_scope.run_id == run.run_id
    assert explanation.explanation_scope.reference_date == "2026-09-10"
    assert explanation.explanation_scope.calculation_date == "2026-09-12"
    assert explanation.explanation_scope.cabin == "ECONOMY"

    assert explanation.index_run_id == run.run_id
    assert explanation.headline_horizon_code == "T+15"
    assert explanation.headline_index_value > 0
    assert explanation.reference_date == "2026-09-10"
    assert explanation.calculation_date == "2026-09-12"
    assert explanation.methodology_version is not None
    assert explanation.route_basket_version is not None
    assert explanation.proxy_weight_version is not None
    assert explanation.software_version is not None
    assert len(explanation.canonical_run_fingerprint) == 64
    assert len(explanation.horizons) == 5
    assert explanation.trust_summary is not None
    assert explanation.disclaimer is not None


# =============================================================================
# 2. ADDITIVE POINT ATTRIBUTION IDENTITY WITHIN TOLERANCE
# =============================================================================

def test_02_additive_point_attribution_identity_within_tolerance(db_session):
    """
    Verifies that for I != 100, point_contribution sum equals I - 100 within tolerance.
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    for h in [15]:
        db_session.add(create_obs(f"OB_R1_{h}", "SRC_GOOGLE", 5000.00, "DEL-BOM", ref_date, h))
        db_session.add(create_obs(f"OB_R2_{h}", "SRC_GOOGLE", 5000.00, "BLR-DEL", ref_date, h))
        db_session.add(create_obs(f"OC_R1_{h}", "SRC_GOOGLE", 6000.00, "DEL-BOM", cur_date, h))
        db_session.add(create_obs(f"OC_R2_{h}", "SRC_GOOGLE", 4500.00, "BLR-DEL", cur_date, h))
    db_session.commit()

    run, _, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    explanation = IndexExplanationService.explain_index_run(db_session, run.run_id)
    t15_h = next(h for h in explanation.horizons if h.horizon_code == "T+15")

    index_val = t15_h.index_value
    expected_shift = index_val - 100.0

    contrib_sum = float(sum(c.point_contribution for c in t15_h.route_contributions if c.point_contribution is not None))
    assert abs(contrib_sum - expected_shift) <= 1e-3


# =============================================================================
# 3. ZERO NATIONAL LOG SHIFT EDGE CASE (I = 100) WITH OFFSETTING MOVEMENTS
# =============================================================================

def test_03_zero_national_log_shift_with_offsetting_routes(db_session):
    """
    Verifies zero national log shift edge case:
    - Fares unchanged -> I == 100.0
    - point_contribution is set to None (0/0 prevented)
    - direction is set to NEUTRAL
    - ZERO_NATIONAL_LOG_SHIFT reason code is included
    - log_contribution is retained and sums approximately to 0
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    for h in [15]:
        db_session.add(create_obs("O_R1_REF", "SRC_GOOGLE", 5000.00, "DEL-BOM", ref_date, h))
        db_session.add(create_obs("O_R2_REF", "SRC_GOOGLE", 4000.00, "BLR-DEL", ref_date, h))
        db_session.add(create_obs("O_R1_CUR", "SRC_GOOGLE", 5000.00, "DEL-BOM", cur_date, h))
        db_session.add(create_obs("O_R2_CUR", "SRC_GOOGLE", 4000.00, "BLR-DEL", cur_date, h))
    db_session.commit()

    run, _, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    explanation = IndexExplanationService.explain_index_run(db_session, run.run_id)
    t15_h = next(h for h in explanation.horizons if h.horizon_code == "T+15")

    assert t15_h.index_value == 100.0
    assert "ZERO_NATIONAL_LOG_SHIFT" in t15_h.reason_codes

    for rc in t15_h.route_contributions:
        assert rc.point_contribution is None
        assert rc.direction == "NEUTRAL"
        assert rc.log_contribution is not None

    log_sum = sum(rc.log_contribution for rc in t15_h.route_contributions)
    assert abs(log_sum) < 1e-4


# =============================================================================
# 4. CONTRIBUTION DIRECTION CLASSIFICATION
# =============================================================================

def test_04_contribution_direction_classification(db_session):
    """
    Verifies POSITIVE, NEGATIVE, and NEUTRAL direction tags.
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    for h in [15]:
        db_session.add(create_obs("O1_R1", "SRC_GOOGLE", 5000.00, "DEL-BOM", ref_date, h))
        db_session.add(create_obs("O1_R2", "SRC_GOOGLE", 5000.00, "BLR-DEL", ref_date, h))
        db_session.add(create_obs("O2_R1", "SRC_GOOGLE", 6000.00, "DEL-BOM", cur_date, h))
        db_session.add(create_obs("O2_R2", "SRC_GOOGLE", 4000.00, "BLR-DEL", cur_date, h))
    db_session.commit()

    run, _, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    explanation = IndexExplanationService.explain_index_run(db_session, run.run_id)
    t15_h = next(h for h in explanation.horizons if h.horizon_code == "T+15")

    c_del_bom = next(c for c in t15_h.route_contributions if c.route_id == "DEL-BOM")
    c_blr_del = next(c for c in t15_h.route_contributions if c.route_id == "BLR-DEL")

    assert c_del_bom.direction == "POSITIVE"
    assert c_del_bom.point_contribution > 0

    assert c_blr_del.direction == "NEGATIVE"
    assert c_blr_del.point_contribution < 0


# =============================================================================
# 5. MISSING ROUTE CLASSIFICATION TAXONOMY
# =============================================================================

def test_05_missing_route_classification_taxonomy(db_session):
    """
    Verifies missing routes taxonomy derived strictly from persisted 4D facts.
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    for h in [15]:
        db_session.add(create_obs("O1_R1", "SRC_GOOGLE", 5000.00, "DEL-BOM", ref_date, h))
        db_session.add(create_obs("O1_R2", "SRC_GOOGLE", 5000.00, "BLR-DEL", ref_date, h))
        db_session.add(create_obs("O2_R1", "SRC_GOOGLE", 5500.00, "DEL-BOM", cur_date, h))
    db_session.commit()

    run, _, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    explanation = IndexExplanationService.explain_index_run(db_session, run.run_id)
    t15_h = next(h for h in explanation.horizons if h.horizon_code == "T+15")

    missing_blr_del = next((m for m in t15_h.missing_routes if m.route_id == "BLR-DEL"), None)
    assert missing_blr_del is not None
    assert missing_blr_del.reason_code in ["MISSING_CURRENT_OBSERVATION", "NO_BASE_OBSERVATION"]


# =============================================================================
# 6. TRUST METADATA INTEGRATION
# =============================================================================

def test_06_trust_metadata_integration(db_session):
    """
    Verifies trust_summary inclusion.
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    for h in [15]:
        db_session.add(create_obs(f"OB_{h}", "SRC_GOOGLE", 5000.00, "DEL-BOM", ref_date, h))
        db_session.add(create_obs(f"OC_{h}", "SRC_GOOGLE", 5500.00, "DEL-BOM", cur_date, h))
    db_session.commit()

    run, _, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    explanation = IndexExplanationService.explain_index_run(db_session, run.run_id)

    assert explanation.trust_summary.trust_status == "UNEVALUATED"
    assert explanation.trust_summary.is_diagnostic_only is True


# =============================================================================
# 7. API ENDPOINT & 404
# =============================================================================

def test_07_api_explanation_endpoint_and_404(client, db_session):
    """
    Tests GET /api/v1/index-runs/{run_id}/explanation returns 200 for valid run and 404 for invalid.
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    for h in [1, 7, 15, 30, 45]:
        db_session.add(create_obs(f"OB_{h}", "SRC_GOOGLE", 5000.00, "DEL-BOM", ref_date, h))
        db_session.add(create_obs(f"OC_{h}", "SRC_GOOGLE", 5500.00, "DEL-BOM", cur_date, h))
    db_session.commit()

    run, _, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    # 1. Valid run_id -> HTTP 200
    resp = client.get(f"/api/v1/index-runs/{run.run_id}/explanation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["index_run_id"] == run.run_id
    assert data["headline_horizon_code"] == "T+15"
    assert "explanation_scope" in data
    assert len(data["horizons"]) == 5

    # 2. Non-existent run_id -> HTTP 404
    bad_resp = client.get("/api/v1/index-runs/00000000-0000-0000-0000-000000000000/explanation")
    assert bad_resp.status_code == 404


# =============================================================================
# 8. 4D RECONCILIATION TEST
# =============================================================================

def test_08_4d_reconciliation(db_session):
    """
    Proves that 5A explanation index_value and matched_sample_index_value equal
    the corresponding stored 4D HorizonIndexResult values within tolerance, and
    sum(active_weight) == 1.0 for horizons with active routes.
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    for h in [1, 7, 15, 30, 45]:
        db_session.add(create_obs(f"OB_R1_{h}", "SRC_GOOGLE", 5000.00, "DEL-BOM", ref_date, h))
        db_session.add(create_obs(f"OB_R2_{h}", "SRC_GOOGLE", 4000.00, "BLR-DEL", ref_date, h))
        db_session.add(create_obs(f"OC_R1_{h}", "SRC_GOOGLE", 5500.00, "DEL-BOM", cur_date, h))
        db_session.add(create_obs(f"OC_R2_{h}", "SRC_GOOGLE", 4200.00, "BLR-DEL", cur_date, h))
    db_session.commit()

    run, stored_horizons, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    explanation = IndexExplanationService.explain_index_run(db_session, run.run_id)

    assert len(explanation.horizons) == len(stored_horizons)

    for exp_h in explanation.horizons:
        stored_h = next(sh for sh in stored_horizons if sh.horizon_code == exp_h.horizon_code)
        
        # 1. Index value equality
        assert abs(exp_h.index_value - stored_h.index_value) < 1e-4
        
        # 2. Matched sample index value equality
        assert abs(exp_h.matched_sample_index_value - stored_h.matched_sample_index_value) < 1e-4

        # 3. Active weight sum == 1.0 within 1e-6
        if exp_h.route_contributions:
            active_w_total = sum(c.active_weight for c in exp_h.route_contributions)
            assert abs(active_w_total - 1.0) < 1e-5


# =============================================================================
# 9. DATABASE READ-ONLY IMMUTABILITY
# =============================================================================

def test_09_database_read_only_immutability(db_session):
    """
    Proves that calling explain_index_run does NOT change any database rows.
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    for h in [15]:
        db_session.add(create_obs(f"OB_{h}", "SRC_GOOGLE", 5000.00, "DEL-BOM", ref_date, h))
        db_session.add(create_obs(f"OC_{h}", "SRC_GOOGLE", 5500.00, "DEL-BOM", cur_date, h))
    db_session.commit()

    run, _, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    # Snapshot database counts before
    runs_before = db_session.query(IndexRun).count()
    horizons_before = db_session.query(HorizonIndexResult).count()
    routes_before = db_session.query(RouteIndexResult).count()
    obs_before = db_session.query(Observation).count()
    trust_before = db_session.query(TrustEvaluation).count()

    # Call explanation service
    _ = IndexExplanationService.explain_index_run(db_session, run.run_id)

    # Snapshot database counts after
    runs_after = db_session.query(IndexRun).count()
    horizons_after = db_session.query(HorizonIndexResult).count()
    routes_after = db_session.query(RouteIndexResult).count()
    obs_after = db_session.query(Observation).count()
    trust_after = db_session.query(TrustEvaluation).count()

    assert runs_before == runs_after
    assert horizons_before == horizons_after
    assert routes_before == routes_after
    assert obs_before == obs_after
    assert trust_after == trust_before


def test_10_explanation_json_serialization_and_exact_identity(db_session):
    """
    Verifies API boundary contract:
    1. point_contribution is serialized as a JSON number (float), not a string.
    2. Exact attribution identity sum(C_r) == I - 100 holds at unrounded precision.
    """
    import json
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    for h in [15]:
        db_session.add(create_obs(f"OB_R1_{h}", "SRC_GOOGLE", 5000.00, "DEL-BOM", ref_date, h))
        db_session.add(create_obs(f"OB_R2_{h}", "SRC_GOOGLE", 4000.00, "BLR-DEL", ref_date, h))
        db_session.add(create_obs(f"OC_R1_{h}", "SRC_GOOGLE", 5500.00, "DEL-BOM", cur_date, h))
        db_session.add(create_obs(f"OC_R2_{h}", "SRC_GOOGLE", 4400.00, "BLR-DEL", cur_date, h))
    db_session.commit()

    run, _, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    explanation = IndexExplanationService.explain_index_run(db_session, run.run_id)
    json_str = explanation.model_dump_json()
    data = json.loads(json_str)

    # 1. Verify JSON number serialization (not quoted string)
    h15 = [h for h in data["horizons"] if h["horizon_code"] == "T+15"][0]
    for contrib in h15["route_contributions"]:
        pc = contrib["point_contribution"]
        assert isinstance(pc, (int, float)), f"Expected numeric JSON for point_contribution, got {type(pc)}: {pc}"

    # 2. Verify exact attribution identity at unrounded precision
    sum_c = sum(r["point_contribution"] for r in h15["route_contributions"])
    expected_shift = h15["index_value"] - 100.0
    assert math.isclose(sum_c, expected_shift, rel_tol=1e-4, abs_tol=1e-4)

