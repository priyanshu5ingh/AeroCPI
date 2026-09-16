"""AeroGuide Longitudinal Panel Collection & Target Evaluation Tests.
Validates fixed travel dates, repeated observations, longitudinal identity, 7-day target construction,
timestamp integrity, failure isolation, and honest readiness reporting.
"""
import pytest
from datetime import datetime, date, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import get_db, SessionLocal
from app.models.observation import Observation
from app.models.longitudinal_panel import LongitudinalPanelManifest
from app.core.aeroguide_registry import (
    TIER_1_DGCA_CORE,
    generate_comparability_id
)
from app.services.longitudinal_service import (
    DEFAULT_PINNED_TRAVEL_DATES,
    execute_longitudinal_pilot_collection,
    calculate_readiness_metrics,
    get_trajectory_detail,
    _upsert_panel_manifest
)

client = TestClient(app)

def test_01_fixed_travel_dates_stability():
    """Verify that pinned travel dates are fixed calendar departure dates."""
    assert len(DEFAULT_PINNED_TRAVEL_DATES) == 14
    assert DEFAULT_PINNED_TRAVEL_DATES[0] == "2026-10-01"
    assert DEFAULT_PINNED_TRAVEL_DATES[-1] == "2026-10-14"
    
    # Confirm all dates are valid sequential ISO dates
    parsed_dates = [datetime.strptime(d, "%Y-%m-%d").date() for d in DEFAULT_PINNED_TRAVEL_DATES]
    for i in range(len(parsed_dates) - 1):
        assert (parsed_dates[i+1] - parsed_dates[i]).days == 1


def test_02_repeated_observations_retention():
    """Verify that repeated searches on different dates for same route + travel_date are retained."""
    import uuid
    db = SessionLocal()
    obs1_id = f"TEST_OBS_{uuid.uuid4().hex[:8]}"
    obs2_id = f"TEST_OBS_{uuid.uuid4().hex[:8]}"
    route_id = f"TEST-RPT-{uuid.uuid4().hex[:4]}"
    t_date = date(2026, 10, 5)
    try:
        # Simulate search on Day 1
        day1_ts = datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc)
        obs1 = Observation(
            observation_id=obs1_id,
            source_id="SRC_GOOGLE_FLIGHTS",
            search_timestamp=day1_ts,
            search_date=day1_ts.date(),
            observed_at=day1_ts,
            travel_date=t_date,
            booking_horizon_days=25,
            origin_airport="DEL",
            destination_airport="BOM",
            route_id=route_id,
            carrier_id="6E",
            total_fare=6400.0,
            cabin="ECONOMY",
            currency="INR"
        )
        db.add(obs1)
        _upsert_panel_manifest(db, route_id, t_date, day1_ts.date().isoformat(), day1_ts)
        db.commit()
        
        # Simulate search on Day 2
        day2_ts = datetime(2026, 9, 11, 10, 0, 0, tzinfo=timezone.utc)
        obs2 = Observation(
            observation_id=obs2_id,
            source_id="SRC_GOOGLE_FLIGHTS",
            search_timestamp=day2_ts,
            search_date=day2_ts.date(),
            observed_at=day2_ts,
            travel_date=t_date,
            booking_horizon_days=24,
            origin_airport="DEL",
            destination_airport="BOM",
            route_id=route_id,
            carrier_id="6E",
            total_fare=6550.0,
            cabin="ECONOMY",
            currency="INR"
        )
        db.add(obs2)
        _upsert_panel_manifest(db, route_id, t_date, day2_ts.date().isoformat(), day2_ts)
        db.commit()
        
        # Verify both observations exist in DB
        obs_count = db.query(Observation).filter(
            Observation.route_id == route_id,
            Observation.travel_date == t_date
        ).count()
        assert obs_count >= 2
        
        # Verify panel manifest reflects 2 search dates
        manifest = db.query(LongitudinalPanelManifest).filter(
            LongitudinalPanelManifest.route_id == route_id,
            LongitudinalPanelManifest.travel_date == t_date
        ).first()
        assert manifest is not None
        assert manifest.search_count >= 2
        assert "2026-09-10" in manifest.search_dates
        assert "2026-09-11" in manifest.search_dates
        
    finally:
        # Cleanup test records
        db.rollback()
        db.query(Observation).filter(Observation.observation_id.in_([obs1_id, obs2_id, "TEST_OBS_DAY1", "TEST_OBS_DAY2"])).delete()
        db.query(LongitudinalPanelManifest).filter(LongitudinalPanelManifest.route_id == route_id).delete()
        db.commit()
        db.close()


def test_03_longitudinal_identity_determinism():
    """Verify deterministic comparability hashing for standard consumer contracts."""
    hash1 = generate_comparability_id("DEL", "BOM", "2026-10-01", cabin="ECONOMY", adults=1, currency="INR")
    hash2 = generate_comparability_id("DEL", "BOM", "2026-10-01", cabin="ECONOMY", adults=1, currency="INR")
    hash_diff_date = generate_comparability_id("DEL", "BOM", "2026-10-02", cabin="ECONOMY", adults=1, currency="INR")
    hash_diff_origin = generate_comparability_id("BLR", "BOM", "2026-10-01", cabin="ECONOMY", adults=1, currency="INR")
    
    assert hash1 == hash2
    assert hash1 != hash_diff_date
    assert hash1 != hash_diff_origin
    assert len(hash1) == 16


def test_04_target_candidate_creation_7d_pair():
    """Verify 7-day target candidate eligibility when search dates span >= 7 days."""
    db = SessionLocal()
    route_id = "TEST-TARGET-7D"
    t_date = date(2026, 10, 10)
    try:
        # Day 0 search
        d0_ts = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
        _upsert_panel_manifest(db, route_id, t_date, "2026-09-01", d0_ts)
        
        # Day 7 search (exactly 7 days later)
        d7_ts = datetime(2026, 9, 8, 10, 0, 0, tzinfo=timezone.utc)
        _upsert_panel_manifest(db, route_id, t_date, "2026-09-08", d7_ts)
        db.commit()
        
        manifest = db.query(LongitudinalPanelManifest).filter(
            LongitudinalPanelManifest.route_id == route_id,
            LongitudinalPanelManifest.travel_date == t_date
        ).first()
        
        assert manifest is not None
        assert manifest.has_7_day_pair is True
        assert manifest.history_span_days == 7
        assert manifest.eligible_for_forecasting is True
        
    finally:
        db.query(LongitudinalPanelManifest).filter(
            LongitudinalPanelManifest.route_id == route_id
        ).delete()
        db.commit()
        db.close()


def test_05_no_target_when_future_observation_absent():
    """Verify that a single-search trajectory has zero 7-day target pairs and training is disabled."""
    db = SessionLocal()
    try:
        route_id = "TEST-SINGLE"
        t_date = date(2026, 10, 20)
        
        d0_ts = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
        _upsert_panel_manifest(db, route_id, t_date, "2026-09-01", d0_ts)
        db.commit()
        
        manifest = db.query(LongitudinalPanelManifest).filter(
            LongitudinalPanelManifest.route_id == route_id,
            LongitudinalPanelManifest.travel_date == t_date
        ).first()
        
        assert manifest.has_7_day_pair is False
        assert manifest.history_span_days == 0
        assert manifest.eligible_for_forecasting is False
        
    finally:
        db.query(LongitudinalPanelManifest).filter(LongitudinalPanelManifest.route_id == "TEST-SINGLE").delete()
        db.commit()
        db.close()


def test_06_search_timestamp_integrity():
    """Verify search_timestamp is UTC and preserved exactly."""
    now_utc = datetime.now(timezone.utc)
    obs = Observation(
        observation_id="TEST_TS_CHECK",
        source_id="SRC_GOOGLE_FLIGHTS",
        search_timestamp=now_utc,
        search_date=now_utc.date(),
        travel_date=date(2026, 10, 1),
        booking_horizon_days=15,
        route_id="DEL-BOM",
        carrier_id="6E",
        total_fare=5900.0,
        cabin="ECONOMY"
    )
    assert obs.search_timestamp.tzinfo is not None
    assert obs.search_date == now_utc.date()


def test_07_collection_run_manifest_and_failure_isolation():
    """Verify that execute_longitudinal_pilot_collection records complete run telemetry and isolates errors."""
    db = SessionLocal()
    try:
        res = execute_longitudinal_pilot_collection(
            db,
            pinned_dates=["2026-10-01", "2026-10-02"],
            routes=[("DEL", "BOM"), ("BLR", "DEL")]
        )
        
        assert "run_id" in res
        assert res["routes_requested"] == 2
        assert res["travel_dates_requested"] == 2
        assert res["queries_requested"] == 4
        assert res["queries_successful"] == 4
        assert res["queries_failed"] == 0
        assert res["observations_created"] == 4 * 4 # 4 carriers per query
        assert res["run_status"] == "COMPLETED"
        
    finally:
        db.close()


def test_08_dynamic_readiness_api_endpoint():
    """Verify GET /api/v1/aeroguide/readiness reports all required empirical metrics."""
    response = client.get("/api/v1/aeroguide/readiness")
    assert response.status_code == 200
    data = response.json()
    
    assert "total_observations" in data
    assert "unique_routes" in data
    assert "unique_travel_dates" in data
    assert "unique_search_dates" in data
    assert "repeated_trajectories" in data
    assert "trajectories_with_gte_3_searches" in data
    assert "seven_day_target_pairs" in data
    assert "fourteen_day_target_pairs" in data
    assert "longest_history_days" in data
    assert "source_coverage" in data
    assert "airline_coverage" in data
    assert "dataset_classification" in data
    assert "model_training_status" in data
    assert "overall_readiness" in data
    assert "readiness_notes" in data


def test_09_decision_trace_stage_7_honesty():
    """Verify forecast stage in the decision trace explicitly states INSUFFICIENT_LONGITUDINAL_HISTORY and NOT_AVAILABLE."""
    payload = {
        "origin": "DEL",
        "destination": "BOM",
        "travel_date": "2026-10-05"
    }
    response = client.post("/api/v1/aeroguide/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    trace = data["decision_trace"]
    assert len(trace) >= 8
    
    # Forecast stage check
    forecast_stage = next(n for n in trace if "Forecast" in n["stage_name"] or "Longitudinal" in n["stage_name"])
    assert forecast_stage["status"] == "INSUFFICIENT_LONGITUDINAL_HISTORY"
    assert "Forecast: NOT_AVAILABLE" in forecast_stage["evidence_summary"] or "NOT_AVAILABLE" in forecast_stage["evidence_summary"]


def test_10_readiness_and_trace_stage_7_equality():
    """Verify single canonical readiness computation between /readiness and /analyze trace forecast stage."""
    readiness_res = client.get("/api/v1/aeroguide/readiness")
    assert readiness_res.status_code == 200
    readiness_data = readiness_res.json()
    
    analyze_payload = {
        "origin": "DEL",
        "destination": "BOM",
        "travel_date": "2026-10-01"
    }
    analyze_res = client.post("/api/v1/aeroguide/analyze", json=analyze_payload)
    assert analyze_res.status_code == 200
    analyze_data = analyze_res.json()
    
    forecast_stage = next(n for n in analyze_data["decision_trace"] if "Forecast" in n["stage_name"] or "Longitudinal" in n["stage_name"])
    stage_payload = forecast_stage["structured_payload"]
    
    # Assert exact equality from single canonical source of truth
    assert readiness_data["seven_day_target_pairs"] == stage_payload["seven_day_target_pairs"]
    assert readiness_data["dataset_classification"] == stage_payload.get("status", stage_payload.get("dataset_classification"))
    assert readiness_data["model_training_status"] == stage_payload["model_training_status"]
    assert readiness_data["effective_forecasting_examples"] == stage_payload["effective_forecasting_examples"]


def test_11_valid_7d_target_requires_exact_conditions():
    """Verify that a valid 7-day pair requires same route, same travel date, and chronological search dates gap >= 7."""
    db = SessionLocal()
    route_id = "TEST-CANONICAL-7D"
    t_date = date(2026, 11, 1)
    try:
        # Search at t=0
        t0_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
        _upsert_panel_manifest(db, route_id, t_date, "2026-09-01", t0_time)
        
        # Search at t=6 (gap=6, NOT 7 days)
        t6_time = datetime(2026, 9, 7, 10, 0, 0, tzinfo=timezone.utc)
        _upsert_panel_manifest(db, route_id, t_date, "2026-09-07", t6_time)
        db.commit()
        
        m_6d = db.query(LongitudinalPanelManifest).filter(
            LongitudinalPanelManifest.route_id == route_id,
            LongitudinalPanelManifest.travel_date == t_date
        ).first()
        assert m_6d.has_7_day_pair is False
        assert m_6d.eligible_for_forecasting is False
        
        # Now search at t=7 (gap=7 days)
        t7_time = datetime(2026, 9, 8, 10, 0, 0, tzinfo=timezone.utc)
        _upsert_panel_manifest(db, route_id, t_date, "2026-09-08", t7_time)
        db.commit()
        
        m_7d = db.query(LongitudinalPanelManifest).filter(
            LongitudinalPanelManifest.route_id == route_id,
            LongitudinalPanelManifest.travel_date == t_date
        ).first()
        assert m_7d.has_7_day_pair is True
        assert m_7d.eligible_for_forecasting is True
        assert m_7d.history_span_days == 7
        
    finally:
        db.query(LongitudinalPanelManifest).filter(
            LongitudinalPanelManifest.route_id == route_id
        ).delete()
        db.commit()
        db.close()


def test_12_trajectory_explorer_endpoint():
    """Verify Trajectory Explorer endpoint returns chronological search points and target evaluations."""
    response = client.get("/api/v1/aeroguide/trajectories/DEL-BOM/2026-10-01")
    assert response.status_code == 200
    data = response.json()
    
    assert data["route_id"] == "DEL-BOM"
    assert data["origin"] == "DEL"
    assert data["destination"] == "BOM"
    assert data["travel_date"] == "2026-10-01"
    assert "search_points" in data
    assert "target_evaluations" in data
    assert isinstance(data["search_points"], list)
    assert isinstance(data["target_evaluations"], list)
    assert len(data["search_points"]) >= 1
    
    pt = data["search_points"][0]
    assert "search_date" in pt
    assert "median_fare" in pt
    assert "min_fare" in pt
    assert "max_fare" in pt
    assert "carrier_quotes" in pt
    assert len(pt["carrier_quotes"]) >= 1


def test_13_dual_target_definitions_market_and_carrier():
    """Verify trajectory evaluations produce both Market-Level and Matched-Carrier targets."""
    import uuid
    db = SessionLocal()
    route_id = f"TEST-DUAL-{uuid.uuid4().hex[:4]}".upper()
    t_date = date(2026, 11, 15)
    obs_ids = []
    try:
        # Search 1: Day 0
        d0_ts = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
        obs_6e_d0 = Observation(
            observation_id=f"TEST_6E_D0_{uuid.uuid4().hex[:6]}",
            source_id="SRC_GOOGLE_FLIGHTS",
            search_timestamp=d0_ts,
            search_date=d0_ts.date(),
            observed_at=d0_ts,
            travel_date=t_date,
            booking_horizon_days=75,
            route_id=route_id,
            carrier_id="6E",
            airline="IndiGo",
            total_fare=6000.0,
            cabin="ECONOMY"
        )
        obs_ai_d0 = Observation(
            observation_id=f"TEST_AI_D0_{uuid.uuid4().hex[:6]}",
            source_id="SRC_GOOGLE_FLIGHTS",
            search_timestamp=d0_ts,
            search_date=d0_ts.date(),
            observed_at=d0_ts,
            travel_date=t_date,
            booking_horizon_days=75,
            route_id=route_id,
            carrier_id="AI",
            airline="Air India",
            total_fare=7000.0,
            cabin="ECONOMY"
        )
        db.add_all([obs_6e_d0, obs_ai_d0])
        obs_ids.extend([obs_6e_d0.observation_id, obs_ai_d0.observation_id])
        
        # Search 2: Day 7 (Exactly 7 days later)
        d7_ts = datetime(2026, 9, 8, 10, 0, 0, tzinfo=timezone.utc)
        obs_6e_d7 = Observation(
            observation_id=f"TEST_6E_D7_{uuid.uuid4().hex[:6]}",
            source_id="SRC_GOOGLE_FLIGHTS",
            search_timestamp=d7_ts,
            search_date=d7_ts.date(),
            observed_at=d7_ts,
            travel_date=t_date,
            booking_horizon_days=68,
            route_id=route_id,
            carrier_id="6E",
            airline="IndiGo",
            total_fare=6600.0,
            cabin="ECONOMY"
        )
        obs_ai_d7 = Observation(
            observation_id=f"TEST_AI_D7_{uuid.uuid4().hex[:6]}",
            source_id="SRC_GOOGLE_FLIGHTS",
            search_timestamp=d7_ts,
            search_date=d7_ts.date(),
            observed_at=d7_ts,
            travel_date=t_date,
            booking_horizon_days=68,
            route_id=route_id,
            carrier_id="AI",
            airline="Air India",
            total_fare=6650.0,
            cabin="ECONOMY"
        )
        db.add_all([obs_6e_d7, obs_ai_d7])
        obs_ids.extend([obs_6e_d7.observation_id, obs_ai_d7.observation_id])
        db.commit()
        
        detail = get_trajectory_detail(db, route_id, "2026-11-15")
        
        assert detail["route_id"] == route_id
        assert len(detail["search_points"]) == 2
        assert len(detail["target_evaluations"]) == 1
        
        eval7 = detail["target_evaluations"][0]
        assert eval7["days_gap"] == 7
        assert eval7["is_valid_7d_target"] is True
        
        # 1. Market-level check
        assert eval7["prediction_median_fare"] == 6500.0
        assert eval7["future_median_fare"] == 6625.0
        assert eval7["delta_fare"] == 125.0
        assert eval7["market_target"]["direction"] == "STABLE"
        
        # 2. Matched-carrier check
        assert eval7["carrier_composition_status"] == "IDENTICAL"
        assert eval7["matched_carriers_count"] == 2
        assert len(eval7["matched_carrier_targets"]) == 2
        
        c_6e = next(c for c in eval7["matched_carrier_targets"] if c["carrier_code"] == "6E")
        assert c_6e["prediction_fare"] == 6000.0
        assert c_6e["future_fare"] == 6600.0
        assert c_6e["delta_fare"] == 600.0
        assert c_6e["direction"] == "UP"
        
        c_ai = next(c for c in eval7["matched_carrier_targets"] if c["carrier_code"] == "AI")
        assert c_ai["prediction_fare"] == 7000.0
        assert c_ai["future_fare"] == 6650.0
        assert c_ai["delta_fare"] == -350.0
        assert c_ai["direction"] == "DOWN"
        
    finally:
        db.rollback()
        if obs_ids:
            db.query(Observation).filter(Observation.observation_id.in_(obs_ids)).delete()
        db.commit()
        db.close()

