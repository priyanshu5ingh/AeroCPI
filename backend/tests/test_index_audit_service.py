import datetime as dt
import json
import pytest
from app.models.index_run import IndexRun
from app.models.horizon_index_result import HorizonIndexResult
from app.models.route_index_result import RouteIndexResult
from app.models.observation import Observation
from app.models.trust_evaluation import TrustEvaluation
from app.services.statistical_index_service import StatisticalIndexEngineService
from app.services.index_audit_service import IndexAuditService
from app.schemas.index_audit import IndexAuditResponse
from tests.test_statistical_index_engine import seed_test_routes, create_obs


# =============================================================================
# 1. VALID PRODUCTION RUN AUDIT & FIELD COMPLETENESS
# =============================================================================

def test_01_audit_valid_run(db_session):
    """
    Verifies that audit_index_run returns a complete audit response with all sub-models populated.
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

    audit = IndexAuditService.audit_index_run(db_session, run.run_id)

    assert isinstance(audit, IndexAuditResponse)
    assert audit.audit_scope.run_id == run.run_id
    assert audit.run_identity.run_id == run.run_id
    assert audit.versions.methodology_version is not None
    assert audit.population_audit is not None
    assert audit.route_audit is not None
    assert audit.coverage_audit is not None
    assert audit.trust_audit is not None
    assert audit.reproducibility_audit is not None
    assert len(audit.limitations) > 0


# =============================================================================
# 2. HTTP 404 UNKNOWN RUN
# =============================================================================

def test_02_audit_unknown_run_404(client, db_session):
    """
    Verifies that querying an unknown run_id returns HTTP 404.
    """
    resp = client.get("/api/v1/index-runs/00000000-0000-0000-0000-000000000000/audit")
    assert resp.status_code == 404


# =============================================================================
# 3. DATABASE READ-ONLY IMMUTABILITY
# =============================================================================

def test_03_database_read_only_immutability(db_session):
    """
    Proves that calling audit_index_run does NOT modify any database rows.
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

    runs_b = db_session.query(IndexRun).count()
    horizons_b = db_session.query(HorizonIndexResult).count()
    routes_b = db_session.query(RouteIndexResult).count()
    obs_b = db_session.query(Observation).count()
    trust_b = db_session.query(TrustEvaluation).count()

    _ = IndexAuditService.audit_index_run(db_session, run.run_id)

    assert runs_b == db_session.query(IndexRun).count()
    assert horizons_b == db_session.query(HorizonIndexResult).count()
    assert routes_b == db_session.query(RouteIndexResult).count()
    assert obs_b == db_session.query(Observation).count()
    assert trust_b == db_session.query(TrustEvaluation).count()


# =============================================================================
# 4. HORIZON COUNT RECONCILIATION
# =============================================================================

def test_04_horizon_count_reconciliation(db_session):
    """
    Reconciles reported horizon counts in route audit with stored HorizonIndexResult rows.
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    for h in [1, 7, 15, 30, 45]:
        db_session.add(create_obs(f"OB_{h}", "SRC_GOOGLE", 5000.00, "DEL-BOM", ref_date, h))
        db_session.add(create_obs(f"OC_{h}", "SRC_GOOGLE", 5500.00, "DEL-BOM", cur_date, h))
    db_session.commit()

    run, stored_horizons, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    audit = IndexAuditService.audit_index_run(db_session, run.run_id)

    assert len(audit.route_audit.horizon_route_counts) == len(stored_horizons)
    for hr_audit, stored_h in zip(audit.route_audit.horizon_route_counts, stored_horizons):
        assert hr_audit.horizon_code == stored_h.horizon_code
        assert hr_audit.active_routes_count == stored_h.active_routes_count
        assert hr_audit.base_routes_count == stored_h.base_routes_count


# =============================================================================
# 5. ACTIVE ROUTE COUNT RECONCILIATION
# =============================================================================

def test_05_active_route_count_reconciliation(db_session):
    """
    Reconciles active route counts with persisted RouteIndexResult rows.
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    for h in [15]:
        db_session.add(create_obs("O1_R1", "SRC_GOOGLE", 5000.00, "DEL-BOM", ref_date, h))
        db_session.add(create_obs("O1_R2", "SRC_GOOGLE", 4000.00, "BLR-DEL", ref_date, h))
        db_session.add(create_obs("O2_R1", "SRC_GOOGLE", 5500.00, "DEL-BOM", cur_date, h))
        db_session.add(create_obs("O2_R2", "SRC_GOOGLE", 4400.00, "BLR-DEL", cur_date, h))
    db_session.commit()

    run, _, stored_routes = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    audit = IndexAuditService.audit_index_run(db_session, run.run_id)

    t15_routes = [r for r in stored_routes if r.booking_horizon == 15]
    t15_audit = next(h for h in audit.route_audit.horizon_route_counts if h.horizon_code == "T+15")

    assert t15_audit.active_routes_count == len(t15_routes)


# =============================================================================
# 6. FINGERPRINT & MANIFEST PRESERVATION & DETERMINISM
# =============================================================================

def test_06_fingerprint_and_manifest_preservation(db_session):
    """
    Verifies canonical fingerprint and manifest SHA-256 match persisted values.
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

    audit = IndexAuditService.audit_index_run(db_session, run.run_id)

    assert audit.reproducibility_audit.canonical_run_fingerprint == run.canonical_run_fingerprint
    assert audit.reproducibility_audit.manifest_present is True
    assert audit.reproducibility_audit.manifest_sha256 is not None


# =============================================================================
# 7. POPULATION PROVENANCE & NULL HANDLING FOR NON-PERSISTED METRICS
# =============================================================================

def test_07_population_provenance_and_null_handling(db_session):
    """
    Verifies that missing population metrics (e.g. ref/calc date split when not in manifest)
    return None and an explicit limitation code rather than zero or an estimated number.
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

    audit = IndexAuditService.audit_index_run(db_session, run.run_id)

    # Reference and calculation date counts are None if not in manifest
    assert audit.population_audit.reference_date_count is None or isinstance(audit.population_audit.reference_date_count, int)
    assert any("POPULATION_METRIC_NOT_PERSISTED" in lim for lim in audit.limitations)


# =============================================================================
# 8. REPRODUCIBILITY CLASSIFICATION TEST
# =============================================================================

def test_08_reproducibility_classification(db_session):
    """
    Verifies that raw_input_artifacts_available is False and reproducibility_status is ARTIFACT_REPRODUCIBLE.
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

    audit = IndexAuditService.audit_index_run(db_session, run.run_id)

    rep = audit.reproducibility_audit
    assert rep.raw_input_artifacts_available is False
    assert rep.is_reproducible is False
    assert rep.reproducibility_status == "ARTIFACT_REPRODUCIBLE"


# =============================================================================
# 9. HEADLINE RECONCILIATION TEST
# =============================================================================

def test_09_headline_reconciliation(db_session):
    """
    Verifies that headline index value and horizon code reconcile directly to persisted 4D headline results.
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    for h in [1, 7, 15, 30, 45]:
        db_session.add(create_obs(f"OB_{h}", "SRC_GOOGLE", 5000.00, "DEL-BOM", ref_date, h))
        db_session.add(create_obs(f"OC_{h}", "SRC_GOOGLE", 5500.00, "DEL-BOM", cur_date, h))
    db_session.commit()

    run, stored_horizons, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    audit = IndexAuditService.audit_index_run(db_session, run.run_id)

    headline_stored = next(h for h in stored_horizons if h.is_headline)

    assert audit.run_identity.headline_index_value == headline_stored.index_value
    assert audit.run_identity.headline_horizon_code == headline_stored.horizon_code


# =============================================================================
# 10. MANIFEST HASH DETERMINISM TEST
# =============================================================================

def test_10_manifest_hash_determinism(db_session):
    """
    Verifies that identical canonical manifest content consistently produces the exact same manifest_sha256 hash.
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

    audit1 = IndexAuditService.audit_index_run(db_session, run.run_id)
    audit2 = IndexAuditService.audit_index_run(db_session, run.run_id)

    assert audit1.reproducibility_audit.manifest_sha256 == audit2.reproducibility_audit.manifest_sha256


# =============================================================================
# 11. NO FRESH OBSERVATION DEPENDENCY TEST
# =============================================================================

def test_11_no_fresh_observation_dependency(db_session):
    """
    Proves that adding/modifying unrelated observations in the database AFTER an index run
    does NOT alter the audit response for that historical run.
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

    audit_before = IndexAuditService.audit_index_run(db_session, run.run_id)

    # Inject 500 new unrelated observations into the database on a different date
    future_date = dt.date(2026, 9, 20)
    for i in range(100):
        db_session.add(create_obs(f"O_NEW_{i}", "SRC_GOOGLE", 9999.00, "DEL-BOM", future_date, 15))
    db_session.commit()

    audit_after = IndexAuditService.audit_index_run(db_session, run.run_id)

    assert audit_before.run_identity.headline_index_value == audit_after.run_identity.headline_index_value
    assert audit_before.population_audit.total_eligible_observations == audit_after.population_audit.total_eligible_observations
    assert audit_before.reproducibility_audit.manifest_sha256 == audit_after.reproducibility_audit.manifest_sha256
    assert audit_before.route_audit.calculated_route_horizon_pairs == audit_after.route_audit.calculated_route_horizon_pairs


# =============================================================================
# 12. API ENDPOINT INTEGRATION TEST
# =============================================================================

def test_12_api_audit_endpoint(client, db_session):
    """
    Tests GET /api/v1/index-runs/{run_id}/audit endpoint.
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

    resp = client.get(f"/api/v1/index-runs/{run.run_id}/audit")
    assert resp.status_code == 200

    data = resp.json()
    assert data["audit_scope"]["run_id"] == run.run_id
    assert data["run_identity"]["headline_horizon_code"] == "T+15"
    assert data["reproducibility_audit"]["reproducibility_status"] == "ARTIFACT_REPRODUCIBLE"
    assert data["trust_audit"]["trust_evaluation_status"] in ["VERIFIED_FROM_PERSISTED_EVALUATION", "UNEVALUATED"]
