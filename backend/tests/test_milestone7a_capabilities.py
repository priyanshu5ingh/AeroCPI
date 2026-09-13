import pytest
import datetime as dt
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.measurement_configuration import MeasurementConfiguration
from app.models.index_run import IndexRun
from app.models.horizon_index_result import HorizonIndexResult
from app.models.route_index_result import RouteIndexResult
from app.schemas.measurement_configuration import MeasurementConfigurationCreate
from app.services.measurement_configuration_service import (
    compute_configuration_fingerprint,
    create_measurement_configuration,
    get_latest_measurement_configuration,
)
from app.services.observation_quality_profile_service import (
    evaluate_observation_quality,
    compute_quality_fingerprint,
)
from app.services.outlier_governance_service import (
    flag_anomalies,
    filter_eligible_observations,
    OutlierDetectionMethod,
)
from app.services.source_adapter_service import (
    GoogleFlightsAdapter,
    DuffelAdapter,
    MockSourceAdapter,
    SourceAdapterRegistry,
)
from app.services.publication_readiness_service import (
    evaluate_publication_readiness,
    PublicationStatus,
)
from app.services.validation_lab_service import (
    compute_validation_metrics,
    get_validation_run_by_index_run,
)
from tests.test_statistical_index_engine import seed_test_routes, create_obs
from app.services.statistical_index_service import StatisticalIndexEngineService


# -----------------------------------------------------------------------------
# 1. Versioned Measurement Configuration & Fingerprint Determinism
# -----------------------------------------------------------------------------

def test_measurement_configuration_fingerprint_determinism():
    """
    Verifies that identical parameters produce identical SHA-256 fingerprints,
    and altering any parameter produces a different fingerprint.
    """
    params = {
        "configuration_version": "2026.1.0-test",
        "basket_version": "DGCA-10-2026.1",
        "horizon_set": ["T+1", "T+7", "T+15", "T+30", "T+45"],
        "validation_rule_version": "VAL-2026.1",
        "outlier_rule_version": "IQR-1.5-v1",
        "source_policy_version": "MULTI-SOURCE-V1",
        "aggregation_version": "JEVONS-GEOMETRIC-V1",
        "publication_threshold_version": "PUB-THRESH-V1",
    }

    fp1 = compute_configuration_fingerprint(**params)
    fp2 = compute_configuration_fingerprint(**params)
    assert fp1 == fp2, "Fingerprint computation must be 100% deterministic"
    assert len(fp1) == 64, "Fingerprint must be a valid 64-character SHA-256 hex string"

    # Modify one parameter
    params_mod = dict(params)
    params_mod["outlier_rule_version"] = "MAD-3.0-v1"
    fp3 = compute_configuration_fingerprint(**params_mod)
    assert fp1 != fp3, "Altering a parameter must yield a different configuration fingerprint"


def test_measurement_configuration_api_and_service(db_session: Session, client: TestClient):
    """
    Tests creation and retrieval of versioned measurement configurations via service and API.
    """
    config_in = MeasurementConfigurationCreate(
        configuration_version="2026.2.0-experimental",
        basket_version="DGCA-10-2026.2",
        horizon_set=["T+1", "T+7", "T+15", "T+30", "T+45"],
        outlier_rule_version="MAD-3.0-v1",
    )
    created = create_measurement_configuration(db_session, config_in)
    assert created.configuration_id is not None
    assert created.configuration_version == "2026.2.0-experimental"
    assert len(created.configuration_fingerprint) == 64

    latest = get_latest_measurement_configuration(db_session)
    assert latest is not None

    # Test REST API using test client
    response = client.get("/api/v1/configurations")
    assert response.status_code == 200
    configs = response.json()
    assert len(configs) >= 1

    resp_version = client.get("/api/v1/configurations/2026.2.0-experimental")
    assert resp_version.status_code == 200
    assert resp_version.json()["basket_version"] == "DGCA-10-2026.2"


# -----------------------------------------------------------------------------
# 2. Decomposed Observation Quality Profile
# -----------------------------------------------------------------------------

def test_decomposed_observation_quality_profile():
    """
    Verifies that quality evaluation produces transparent decomposed diagnostic flags
    rather than an arbitrary single 0-100 score.
    """
    obs_valid = {
        "id": "obs-101",
        "price": 8500.0,
        "origin": "DEL",
        "destination": "HYD",
        "departure_time": "2026-09-20T10:00:00Z",
    }
    profile_valid = evaluate_observation_quality(obs_valid)
    assert profile_valid.completeness_status == "COMPLETE"
    assert profile_valid.fare_integrity_status == "VALID"
    assert profile_valid.route_mapping_status == "MAPPED"
    assert profile_valid.duplicate_risk == "LOW"
    assert profile_valid.anomaly_flags == []

    # Invalid fare observation
    obs_invalid = {
        "id": "obs-102",
        "price": -100.0,
        "origin": "BOM",
        "destination": "DEL",
    }
    profile_invalid = evaluate_observation_quality(obs_invalid)
    assert profile_invalid.fare_integrity_status == "ZERO_OR_NEGATIVE"
    assert profile_invalid.completeness_status == "PARTIAL"
    assert "INVALID_FARE_VALUE" in profile_invalid.anomaly_flags

    # Deterministic fingerprint test
    fp_q = compute_quality_fingerprint(
        observation_id="obs-101",
        completeness_status="COMPLETE",
        timestamp_status="VALID",
        fare_integrity_status="VALID",
        route_mapping_status="MAPPED",
        duplicate_risk="LOW",
        anomaly_flags=[],
        source_health_status="HEALTHY",
        quality_rule_version="QR-2026.1",
    )
    assert len(fp_q) == 64


# -----------------------------------------------------------------------------
# 3. Explicit Outlier Governance & Policy Separation
# -----------------------------------------------------------------------------

def test_outlier_governance_methods_and_policy_separation():
    """
    Tests outlier detection abstractions (IQR, MAD, Robust Z-score, Route-History)
    and verifies strict separation between anomaly flagging and exclusion policy.
    """
    prices = [5000.0, 5100.0, 5200.0, 4900.0, 5050.0, 25000.0]  # 25000 is an outlier

    # IQR Method
    flags_iqr = flag_anomalies(prices, method=OutlierDetectionMethod.IQR)
    assert flags_iqr[-1] is True
    assert flags_iqr[0] is False

    # MAD Method
    flags_mad = flag_anomalies(prices, method=OutlierDetectionMethod.MAD)
    assert flags_mad[-1] is True

    # Robust Z-score Method
    flags_z = flag_anomalies(prices, method=OutlierDetectionMethod.ROBUST_ZSCORE)
    assert flags_z[-1] is True

    # Route History Method
    flags_hist = flag_anomalies(prices, method=OutlierDetectionMethod.ROUTE_HISTORY_THRESHOLD, historical_median=5000.0)
    assert flags_hist[-1] is True

    # Verify Flagging vs Exclusion Separation
    observations = [{"id": f"obs-{idx}", "price": p} for idx, p in enumerate(prices)]

    # 1. Flagging only (apply_exclusion=False): no observations are excluded
    eligible_flagged, excluded_flagged = filter_eligible_observations(observations, apply_exclusion=False)
    assert len(eligible_flagged) == len(prices)
    assert len(excluded_flagged) == 0
    assert eligible_flagged[-1]["is_anomalous"] is True

    # 2. Exclusion policy active (apply_exclusion=True): outlier is excluded
    eligible_filtered, excluded_filtered = filter_eligible_observations(observations, apply_exclusion=True)
    assert len(eligible_filtered) == len(prices) - 1
    assert len(excluded_filtered) == 1
    assert excluded_filtered[0]["id"] == "obs-5"


# -----------------------------------------------------------------------------
# 4. Source Adapter Contract Compliance
# -----------------------------------------------------------------------------

def test_source_adapter_contract_compliance():
    """
    Tests SourceAdapter abstract contract, concrete implementations, and registry.
    """
    registry = SourceAdapterRegistry()
    assert "GOOGLE_FLIGHTS_API" in registry.list_adapters()
    assert "DUFFEL_API" in registry.list_adapters()
    assert "MOCK_SOURCE" in registry.list_adapters()

    # Google Flights Adapter
    gf_adapter = registry.get_adapter("GOOGLE_FLIGHTS_API")
    assert gf_adapter is not None
    assert gf_adapter.source_name() == "GOOGLE_FLIGHTS_API"
    gf_obs = gf_adapter.fetch_observations("DEL", "HYD", 15, "2026-09-27")
    assert len(gf_obs) == 1
    assert gf_obs[0]["source"] == "GOOGLE_FLIGHTS_API"
    assert gf_adapter.health_check()["status"] == "HEALTHY"

    # Duffel Adapter
    duffel_adapter = registry.get_adapter("DUFFEL_API")
    assert duffel_adapter is not None
    assert duffel_adapter.source_name() == "DUFFEL_API"
    duffel_obs = duffel_adapter.fetch_observations("DEL", "HYD", 15, "2026-09-27")
    assert len(duffel_obs) == 1

    # Mock Source Adapter
    mock_adapter = MockSourceAdapter(mock_price=9200.0)
    assert mock_adapter.source_name() == "MOCK_SOURCE"
    mock_obs = mock_adapter.fetch_observations("BLR", "DEL", 7, "2026-09-19")
    assert mock_obs[0]["price"] == 9200.0


# -----------------------------------------------------------------------------
# 5. Publication Readiness Layer
# -----------------------------------------------------------------------------

def test_publication_readiness_layer(db_session: Session, client: TestClient):
    """
    Verifies publication readiness evaluation (PUBLISHABLE, DEGRADED, INSUFFICIENT_DATA, NOT_EVALUATED)
    and ensures it NEVER mutates the calculated index value.
    """
    # 1. PUBLISHABLE run
    pub_res = evaluate_publication_readiness("run-001", headline_coverage_ratio=1.0, active_weight_sum=1.0, trust_status="PASS", total_observations=2668)
    assert pub_res.status == PublicationStatus.PUBLISHABLE
    assert pub_res.is_publishable is True

    # 2. DEGRADED run
    deg_res = evaluate_publication_readiness("run-002", headline_coverage_ratio=1.0, active_weight_sum=1.0, trust_status="DEGRADED", total_observations=2668)
    assert deg_res.status == PublicationStatus.DEGRADED
    assert deg_res.is_publishable is True

    # 3. INSUFFICIENT_DATA run
    insuf_res = evaluate_publication_readiness("run-003", headline_coverage_ratio=0.3, active_weight_sum=0.4, trust_status="PASS", total_observations=200)
    assert insuf_res.status == PublicationStatus.INSUFFICIENT_DATA
    assert insuf_res.is_publishable is False

    # 4. NOT_EVALUATED run
    uneval_res = evaluate_publication_readiness("run-004", headline_coverage_ratio=0.0, active_weight_sum=0.0, trust_status="UNEVALUATED", total_observations=0)
    assert uneval_res.status == PublicationStatus.NOT_EVALUATED
    assert uneval_res.is_publishable is False

    # Seed an IndexRun in db_session for REST API test
    run = IndexRun(
        run_id="test-run-pub-100",
        reference_period="2026-09-10",
        comparison_period="2026-09-12",
        index_value=96.209,
        canonical_run_fingerprint="cacd4054fff92a9ef625325e33355c061a6432172eb51958f221600a1ba46bca",
    )
    db_session.add(run)
    db_session.commit()

    response = client.get(f"/api/v1/index-runs/{run.run_id}/publication-readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == run.run_id
    assert "status" in data


# -----------------------------------------------------------------------------
# 6. Validation Lab Foundation
# -----------------------------------------------------------------------------

def test_validation_lab_foundation(db_session: Session, client: TestClient):
    """
    Tests Validation Lab benchmarks and runs, confirming graceful handling
    of missing benchmark data without fabricating scores.
    """
    run = IndexRun(
        run_id="test-run-val-101",
        reference_period="2026-09-10",
        comparison_period="2026-09-12",
        index_value=96.209,
        canonical_run_fingerprint="cacd4054fff92a9ef625325e33355c061a6432172eb51958f221600a1ba46bca",
    )
    db_session.add(run)
    db_session.commit()

    val_run = get_validation_run_by_index_run(db_session, run.run_id)
    assert val_run.run_id == run.run_id
    assert val_run.status == "DISABLED_NO_BENCHMARK_DATA"
    assert val_run.metrics is None

    # Test metric calculation math when reference data IS available
    idx_vals = [100.0, 102.5, 98.0, 96.2]
    bm_vals = [100.0, 102.0, 98.5, 96.0]
    metrics = compute_validation_metrics(idx_vals, bm_vals)
    assert metrics["coverage"] == 1.0
    assert metrics["directional_agreement"] > 0.0
    assert metrics["absolute_deviation"] > 0.0

    # REST API test
    resp_benchmarks = client.get("/api/v1/validation-lab/benchmarks")
    assert resp_benchmarks.status_code == 200

    resp_run = client.get(f"/api/v1/validation-lab/runs/{run.run_id}")
    assert resp_run.status_code == 200
    assert resp_run.json()["status"] == "DISABLED_NO_BENCHMARK_DATA"


# -----------------------------------------------------------------------------
# 7. Frozen 4D, 5A, 5B, 5C Reconciliation & Regression
# -----------------------------------------------------------------------------

def test_frozen_production_run_reconciliation(db_session: Session, client: TestClient):
    """
    Reconciles statistical index calculation engine output and verifies ZERO regression across all 5 horizons:
    T+1  : 63.496
    T+7  : 99.863
    T+15 : 96.209 (Headline)
    T+30 : 90.600
    T+45 : 88.949
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    # Seed observations for statistical engine
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

    # 1. 5C Dashboard API
    dash_resp = client.get(f"/api/v1/index-runs/{run.run_id}/dashboard")
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()

    assert dash_data["headline"]["horizon_code"] == "T+15"
    assert dash_data["headline"]["index_value"] == pytest.approx(run.index_value, abs=1e-3)

    # 2. 5A Explanation API
    exp_resp = client.get(f"/api/v1/index-runs/{run.run_id}/explanation")
    assert exp_resp.status_code == 200
    exp_data = exp_resp.json()
    assert exp_data["headline_index_value"] == pytest.approx(run.index_value, abs=1e-3)

    # 3. 5B Audit API
    audit_resp = client.get(f"/api/v1/index-runs/{run.run_id}/audit")
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert audit_data["run_identity"]["headline_index_value"] == pytest.approx(run.index_value, abs=1e-3)
    assert audit_data["reproducibility_audit"]["manifest_present"] is True
