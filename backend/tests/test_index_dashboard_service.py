import datetime as dt
from decimal import Decimal
import pytest
from app.models.index_run import IndexRun
from app.models.horizon_index_result import HorizonIndexResult
from app.models.route_index_result import RouteIndexResult
from app.models.observation import Observation
from app.models.trust_evaluation import TrustEvaluation
from app.services.statistical_index_service import StatisticalIndexEngineService
from app.services.index_dashboard_service import IndexDashboardService
from app.schemas.index_dashboard import IndexDashboardResponse
from tests.test_statistical_index_engine import seed_test_routes, create_obs


# =============================================================================
# 1. VALID PRODUCTION RUN DASHBOARD & FIELD COMPLETENESS
# =============================================================================

def test_01_dashboard_valid_run(db_session):
    """
    Verifies that get_dashboard returns a complete IndexDashboardResponse with all 6 sub-models.
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

    dashboard = IndexDashboardService.get_dashboard(db_session, run.run_id)

    assert isinstance(dashboard, IndexDashboardResponse)
    assert dashboard.dashboard_scope.run_id == run.run_id
    assert dashboard.headline is not None
    assert dashboard.drivers is not None
    assert dashboard.coverage is not None
    assert dashboard.trust is not None
    assert dashboard.methodology is not None
    assert dashboard.audit is not None
    assert "AeroCPI" in dashboard.disclaimer


# =============================================================================
# 2. HTTP 404 UNKNOWN RUN
# =============================================================================

def test_02_dashboard_unknown_run_404(client, db_session):
    """
    Verifies that GET /api/v1/index-runs/{non_existent_run_id}/dashboard returns HTTP 404.
    """
    response = client.get("/api/v1/index-runs/non_existent_run_12345/dashboard")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "not found" in detail.lower()


# =============================================================================
# 3. HEADLINE RECONCILIATION
# =============================================================================

def test_03_headline_reconciliation(db_session):
    """
    Verifies change_from_base = round(index_value - 100.0, 3) and correct direction tag.
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

    dashboard = IndexDashboardService.get_dashboard(db_session, run.run_id)

    expected_change = round(dashboard.headline.index_value - 100.0, 3)
    assert dashboard.headline.change_from_base == expected_change
    assert dashboard.headline.direction == "UP"  # Prices rose from 5000->5500 and 4000->4400 (+10%)


# =============================================================================
# 4. DYNAMIC HEADLINE READING
# =============================================================================

def test_04_dynamic_headline_reading(db_session):
    """
    Verifies headline horizon code is dynamically derived from IndexRun/5A (T+15).
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

    dashboard = IndexDashboardService.get_dashboard(db_session, run.run_id)

    assert dashboard.headline.horizon_code == "T+15"
    assert dashboard.coverage.headline_horizon_code == "T+15"
    assert dashboard.methodology.headline_horizon == "T+15"


# =============================================================================
# 5. DRIVER RECONCILIATION AGAINST 5A
# =============================================================================

def test_05_driver_reconciliation_against_5a(db_session):
    """
    Verifies top positive and negative drivers match 5A point contributions.
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    for h in [1, 7, 15, 30, 45]:
        # DEL-BOM rises 20% (+), BLR-DEL falls 10% (-)
        db_session.add(create_obs(f"OB_R1_{h}", "SRC_GOOGLE", 5000.00, "DEL-BOM", ref_date, h))
        db_session.add(create_obs(f"OB_R2_{h}", "SRC_GOOGLE", 4000.00, "BLR-DEL", ref_date, h))
        db_session.add(create_obs(f"OC_R1_{h}", "SRC_GOOGLE", 6000.00, "DEL-BOM", cur_date, h))
        db_session.add(create_obs(f"OC_R2_{h}", "SRC_GOOGLE", 3600.00, "BLR-DEL", cur_date, h))
    db_session.commit()

    run, _, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    dashboard = IndexDashboardService.get_dashboard(db_session, run.run_id)

    pos_drivers = dashboard.drivers.top_positive_drivers
    neg_drivers = dashboard.drivers.top_negative_drivers

    assert len(pos_drivers) == 1
    assert pos_drivers[0].route_id == "DEL-BOM"
    assert pos_drivers[0].point_contribution > 0
    assert pos_drivers[0].direction == "POSITIVE"

    assert len(neg_drivers) == 1
    assert neg_drivers[0].route_id == "BLR-DEL"
    assert neg_drivers[0].point_contribution < 0
    assert neg_drivers[0].direction == "NEGATIVE"


# =============================================================================
# 6. DRIVER RANKING AND LIMITING (MAX 3)
# =============================================================================

def test_06_driver_ranking_and_limiting(db_session):
    """
    Verifies positive drivers sorted descending, negative drivers sorted ascending (most negative first), capped at 3 each.
    """
    # Create extra test routes in DB
    from app.models.route import Route
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    routes_data = [
        ("R1", "DEL", "BOM", 5000, 7000),  # +40%
        ("R2", "BLR", "DEL", 4000, 5000),  # +25%
        ("R3", "MAA", "BOM", 3000, 3600),  # +20%
        ("R4", "HYD", "DEL", 4500, 4950),  # +10%
        ("R5", "CCU", "DEL", 6000, 4800),  # -20%
        ("R6", "BOM", "BLR", 5500, 3850),  # -30%
        ("R7", "DEL", "HYD", 4000, 2400),  # -40%
        ("R8", "BOM", "MAA", 3500, 1750),  # -50%
    ]

    for rid, orig, dest, p_ref, p_cur in routes_data:
        if not db_session.query(Route).filter(Route.route_id == rid).first():
            db_session.add(Route(
                route_id=rid, origin_code=orig, destination_code=dest, active=True
            ))
        for h in [15]:

            db_session.add(create_obs(f"OB_{rid}_{h}", "SRC_GOOGLE", p_ref, rid, ref_date, h))
            db_session.add(create_obs(f"OC_{rid}_{h}", "SRC_GOOGLE", p_cur, rid, cur_date, h))
    db_session.commit()

    run, _, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    dashboard = IndexDashboardService.get_dashboard(db_session, run.run_id)

    pos_drivers = dashboard.drivers.top_positive_drivers
    neg_drivers = dashboard.drivers.top_negative_drivers

    # Must be capped at 3
    assert len(pos_drivers) <= 3
    assert len(neg_drivers) <= 3

    # Positive drivers sorted descending by point_contribution
    pos_contribs = [d.point_contribution for d in pos_drivers]
    assert pos_contribs == sorted(pos_contribs, reverse=True)

    # Negative drivers sorted ascending (most negative first)
    neg_contribs = [d.point_contribution for d in neg_drivers]
    assert neg_contribs == sorted(neg_contribs)


# =============================================================================
# 7. COVERAGE RECONCILIATION
# =============================================================================

def test_07_coverage_reconciliation(db_session):
    """
    Verifies coverage summary matched_coverage_ratio and horizon coverage array match 4D/5A facts.
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

    dashboard = IndexDashboardService.get_dashboard(db_session, run.run_id)

    assert dashboard.coverage.headline_coverage_ratio == 0.2
    assert len(dashboard.coverage.horizon_coverage) == 5
    for hc in dashboard.coverage.horizon_coverage:
        assert hc.matched_coverage_ratio == 0.2
        assert hc.active_routes_count == 2
        assert hc.total_basket_routes_count == 10


# =============================================================================
# 8. TRUST PRESERVATION
# =============================================================================

def test_08_trust_preservation(db_session):
    """
    Verifies trust properties match persisted evaluation and is_diagnostic_only == True.
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

    dashboard = IndexDashboardService.get_dashboard(db_session, run.run_id)

    assert dashboard.trust.is_diagnostic_only is True
    assert dashboard.trust.trust_status == "UNEVALUATED"


# =============================================================================
# 9. AUDIT SUMMARY PRESERVATION
# =============================================================================

def test_09_audit_summary_preservation(db_session):
    """
    Verifies dashboard audit summary matches 5B reproducibility audit.
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

    dashboard = IndexDashboardService.get_dashboard(db_session, run.run_id)

    assert dashboard.audit.canonical_run_fingerprint == run.canonical_run_fingerprint
    assert dashboard.audit.manifest_present is True
    assert dashboard.audit.reproducibility_status == "ARTIFACT_REPRODUCIBLE"


# =============================================================================
# 10. DATABASE IMMUTABILITY
# =============================================================================

def test_10_database_immutability(db_session):
    """
    Verifies that get_dashboard does not add or modify database records.
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

    count_runs_before = db_session.query(IndexRun).count()
    count_horizons_before = db_session.query(HorizonIndexResult).count()
    count_routes_before = db_session.query(RouteIndexResult).count()

    IndexDashboardService.get_dashboard(db_session, run.run_id)

    assert db_session.query(IndexRun).count() == count_runs_before
    assert db_session.query(HorizonIndexResult).count() == count_horizons_before
    assert db_session.query(RouteIndexResult).count() == count_routes_before


# =============================================================================
# 11. DIRECTION TOLERANCE BEHAVIOR
# =============================================================================

def test_11_direction_tolerance_behavior(db_session):
    """
    Verifies direction tag is UP (> 0.001), DOWN (< -0.001), or UNCHANGED (within [-0.001, 0.001]).
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    # Prices stay identical -> index value = 100.0 -> change_from_base = 0.0 -> UNCHANGED
    for h in [1, 7, 15, 30, 45]:
        db_session.add(create_obs(f"OB_R1_{h}", "SRC_GOOGLE", 5000.00, "DEL-BOM", ref_date, h))
        db_session.add(create_obs(f"OB_R2_{h}", "SRC_GOOGLE", 4000.00, "BLR-DEL", ref_date, h))
        db_session.add(create_obs(f"OC_R1_{h}", "SRC_GOOGLE", 5000.00, "DEL-BOM", cur_date, h))
        db_session.add(create_obs(f"OC_R2_{h}", "SRC_GOOGLE", 4000.00, "BLR-DEL", cur_date, h))
    db_session.commit()

    run, _, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    dashboard = IndexDashboardService.get_dashboard(db_session, run.run_id)

    assert dashboard.headline.index_value == 100.0
    assert dashboard.headline.change_from_base == 0.0
    assert dashboard.headline.direction == "UNCHANGED"
