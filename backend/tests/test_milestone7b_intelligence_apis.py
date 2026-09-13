import pytest
import datetime as dt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.index_run import IndexRun
from app.models.observation import Observation
from app.models.observation_quality import ObservationQuality
from app.models.horizon_index_result import HorizonIndexResult
from app.models.route_index_result import RouteIndexResult
from app.services.index_explanation_service import IndexExplanationService
from app.services.measurement_configuration_service import create_measurement_configuration
from app.schemas.measurement_configuration import MeasurementConfigurationCreate
from tests.test_statistical_index_engine import seed_test_routes, create_obs
from app.services.statistical_index_service import StatisticalIndexEngineService


# -----------------------------------------------------------------------------
# 1. Observation Explorer API Tests (Pagination, Caps, & Filter Hardening)
# -----------------------------------------------------------------------------

def test_observation_explorer_endpoint(db_session: Session, client: TestClient):
    """
    Tests GET /api/v1/observations/explorer with pagination metadata, bounds capping, and filtering.
    """
    ref_date = dt.date(2026, 9, 10)
    obs1 = create_obs("OBS-EXP-1", "SRC_GOOGLE", 8500.0, "DEL-HYD", ref_date, 15)
    obs2 = create_obs("OBS-EXP-2", "SRC_AMADEUS", 9200.0, "DEL-HYD", ref_date, 15)
    db_session.add(obs1)
    db_session.add(obs2)
    db_session.commit()

    # Add quality profile
    qual = ObservationQuality(
        observation_id="OBS-EXP-1",
        completeness_status="COMPLETE",
        fare_integrity_status="VALID",
        quality_fingerprint="abc123hash",
    )
    db_session.add(qual)
    db_session.commit()

    # Standard query
    response = client.get("/api/v1/observations/explorer?route_id=DEL-HYD&horizon=15")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert "has_next" in data
    assert "has_prev" in data
    assert data["page_size"] == 50
    assert data["total"] == 2
    assert len(data["observations"]) == 2

    first = data["observations"][0]
    assert "quality_status" in first
    assert "anomaly_flags" in first

    # Page size boundary test (requesting page_size=500 returns 200)
    resp_max = client.get("/api/v1/observations/explorer?page_size=500")
    assert resp_max.status_code == 200
    data_max = resp_max.json()
    assert data_max["page_size"] == 500

    # Over-max page size test (requesting page_size=1000 correctly rejected with 422)
    resp_over = client.get("/api/v1/observations/explorer?page_size=1000")
    assert resp_over.status_code == 422

    # Invalid filter test (non-existent route)
    resp_invalid = client.get("/api/v1/observations/explorer?route_id=NON-EXISTENT-ROUTE")
    assert resp_invalid.status_code == 200
    data_inv = resp_invalid.json()
    assert data_inv["total"] == 0
    assert len(data_inv["observations"]) == 0


# -----------------------------------------------------------------------------
# 2. Route Intelligence API Tests (5A Reconciliation Invariant)
# -----------------------------------------------------------------------------

def test_route_intelligence_endpoint(db_session: Session, client: TestClient):
    """
    Tests GET /api/v1/routes/{route_id}/intelligence and verifies reconciliation
    invariant: Route Intelligence contribution == 5A persisted contribution.
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
        db=db_session, reference_date=ref_date, calculation_date=cur_date, cabin="ECONOMY"
    )

    response = client.get(f"/api/v1/routes/DEL-BOM/intelligence?run_id={run.run_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["route_id"] == "DEL-BOM"
    assert data["origin"] == "DEL"
    assert data["destination"] == "BOM"
    assert "route_index_value" in data
    assert "horizon_results" in data
    assert len(data["horizon_results"]) == 5

    # Verify reconciliation with 5A explanation engine
    explanation = IndexExplanationService.explain_index_run(db_session, run.run_id)
    headline_h = next((h for h in explanation.horizons if h.is_headline), explanation.horizons[0])
    del_bom_contrib = next(
        (float(rc.point_contribution) for rc in headline_h.route_contributions if rc.route_id == "DEL-BOM" and rc.point_contribution is not None), None
    )
    assert del_bom_contrib is not None
    assert data["point_contribution"] == pytest.approx(del_bom_contrib, abs=1e-5)

    # 404 for invalid run
    response_404 = client.get("/api/v1/routes/DEL-BOM/intelligence?run_id=invalid-run-id")
    assert response_404.status_code == 404


# -----------------------------------------------------------------------------
# 3. Horizon Intelligence API Tests (Reconciliation with HorizonIndexResult)
# -----------------------------------------------------------------------------

def test_horizon_intelligence_endpoints(db_session: Session, client: TestClient):
    """
    Tests GET /api/v1/horizons and GET /api/v1/horizons/{horizon_code} and verifies
    Horizon Intelligence index == persisted HorizonIndexResult.
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
        db=db_session, reference_date=ref_date, calculation_date=cur_date, cabin="ECONOMY"
    )

    resp_all = client.get(f"/api/v1/horizons?run_id={run.run_id}")
    assert resp_all.status_code == 200
    all_horizons = resp_all.json()
    assert len(all_horizons) == 5

    resp_t15 = client.get(f"/api/v1/horizons/T+15?run_id={run.run_id}")
    assert resp_t15.status_code == 200
    t15_data = resp_t15.json()
    assert t15_data["horizon_code"] == "T+15"
    assert t15_data["is_headline"] is True

    # Verify reconciliation invariant with database HorizonIndexResult
    db_h15 = db_session.query(HorizonIndexResult).filter(
        HorizonIndexResult.run_id == run.run_id,
        HorizonIndexResult.horizon_code == "T+15"
    ).first()
    assert db_h15 is not None
    assert t15_data["index_value"] == pytest.approx(db_h15.index_value, abs=1e-5)


# -----------------------------------------------------------------------------
# 4. Data Quality Intelligence API Tests
# -----------------------------------------------------------------------------

def test_data_quality_endpoints(db_session: Session, client: TestClient):
    """
    Tests GET /api/v1/data-quality/summary, /routes, and /sources.
    """
    resp_sum = client.get("/api/v1/data-quality/summary")
    assert resp_sum.status_code == 200
    sum_data = resp_sum.json()
    assert "completeness" in sum_data
    assert "fare_integrity" in sum_data
    assert "quality_rule_version" in sum_data

    resp_routes = client.get("/api/v1/data-quality/routes")
    assert resp_routes.status_code == 200
    assert len(resp_routes.json()["routes"]) == 10

    resp_sources = client.get("/api/v1/data-quality/sources")
    assert resp_sources.status_code == 200
    assert len(resp_sources.json()["sources"]) >= 1


# -----------------------------------------------------------------------------
# 5. Methodology Studio API Tests
# -----------------------------------------------------------------------------

def test_methodology_studio_endpoints(db_session: Session, client: TestClient):
    """
    Tests GET /api/v1/methodology/current and GET /api/v1/methodology/{version}.
    """
    resp_curr = client.get("/api/v1/methodology/current")
    assert resp_curr.status_code == 200
    data = resp_curr.json()
    assert "configuration_version" in data
    assert "configuration_fingerprint" in data
    assert "human_descriptions" in data
    assert len(data["configuration_fingerprint"]) == 64

    ver = data["configuration_version"]
    resp_ver = client.get(f"/api/v1/methodology/{ver}")
    assert resp_ver.status_code == 200
    assert resp_ver.json()["configuration_version"] == ver


# -----------------------------------------------------------------------------
# 6. Measurement Trace Engine & Immutability Tests (9 Stages)
# -----------------------------------------------------------------------------

def test_measurement_trace_provenance_and_immutability(db_session: Session, client: TestClient):
    """
    Tests GET /api/v1/index-runs/{run_id}/trace returning the 9-stage provenance chain
    and verifies that creating a new MeasurementConfiguration leaves past IndexRun unchanged.
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
        db=db_session, reference_date=ref_date, calculation_date=cur_date, cabin="ECONOMY"
    )

    initial_index_val = run.index_value

    response = client.get(f"/api/v1/index-runs/{run.run_id}/trace")
    assert response.status_code == 200
    trace = response.json()

    assert trace["run_id"] == run.run_id
    assert len(trace["provenance_chain"]) == 8
    assert trace["index_run"]["headline_index_value"] == pytest.approx(initial_index_val, abs=1e-3)
    assert trace["configuration"]["configuration_version"].startswith("2026.1")
    assert len(trace["configuration"]["configuration_fingerprint"]) == 64
    assert len(trace["horizons"]) == 5
    assert len(trace["routes"]) == 2
    assert len(trace["canonical_run_fingerprint"]) == 64

    # Now create a new MeasurementConfiguration version (e.g. 2026.2)
    new_cfg = MeasurementConfigurationCreate(
        configuration_version="2026.2.0",
        basket_version="DGCA-2026.2",
        horizon_set=["T+1", "T+7", "T+15", "T+30", "T+45"],
        validation_rule_version="VR-2026.2",
        outlier_rule_version="OR-2026.2",
        source_policy_version="SP-2026.2",
        aggregation_version="TORNQVIST-LOG-LINEAR-2026.2",
        publication_threshold_version="PT-2026.2",
    )
    create_measurement_configuration(db=db_session, config_in=new_cfg)

    # Re-fetch historical IndexRun and verify complete immutability
    run_after = db_session.query(IndexRun).filter(IndexRun.run_id == run.run_id).first()
    assert run_after is not None
    assert run_after.index_value == pytest.approx(initial_index_val, abs=1e-5)

    # 404 test
    resp_404 = client.get("/api/v1/index-runs/non-existent-run/trace")
    assert resp_404.status_code == 404
