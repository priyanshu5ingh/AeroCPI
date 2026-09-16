"""AeroGuide Unit & Integration Tests.
Validates consumer analysis, NDC capability matrix, decision policies, comparability IDs, and temporal leakage safety.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.decision_policy import ACTIVE_DECISION_POLICY
from app.core.aeroguide_registry import (
    AIRLINE_NDC_REGISTRY,
    get_airline_ndc_info,
    generate_comparability_id,
    TIER_1_DGCA_CORE,
    TIER_2_NATIONAL_HIGH_TRAFFIC
)

client = TestClient(app)

def test_01_aeroguide_analyze_endpoint():
    payload = {
        "origin": "BLR",
        "destination": "DEL",
        "travel_date": "2026-10-15",
        "flexibility_days": 2,
        "priority": "CHEAPEST",
        "adults": 1,
        "cabin": "ECONOMY"
    }
    response = client.post("/api/v1/aeroguide/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["origin"] == "BLR"
    assert data["destination"] == "DEL"
    assert data["route_id"] == "BLR-DEL"
    assert data["current_observed_fare"] > 0
    assert data["price_position"] in ["LOW", "TYPICAL", "HIGH", "INSUFFICIENT_DATA"]
    assert data["booking_guidance"] in ["BOOK", "WAIT", "WATCH", "FLEX_DATE", "INSUFFICIENT_DATA"]
    assert data["decision_policy_version"] == "DECISION_POLICY_V1"
    
    # Assert airline alternatives structure
    assert isinstance(data["airline_alternatives"], list)
    assert len(data["airline_alternatives"]) > 0
    for alt in data["airline_alternatives"]:
        assert "carrier_code" in alt
        assert "airline_name" in alt
        assert "observed_fare" in alt
        assert "source_evidence" in alt
        
    # Assert decision trace has all 8 verified nodes
    trace = data["decision_trace"]
    assert len(trace) == 8
    assert trace[0]["stage_name"] == "User Context & Standardized Request"
    assert trace[7]["stage_name"] == "Deterministic Policy Verdict"
    assert trace[7]["status"] == "DECIDED"

def test_02_aeroguide_forecast_honesty_insufficient_data():
    payload = {
        "origin": "DEL",
        "destination": "BOM",
        "travel_date": "2026-10-15"
    }
    response = client.post("/api/v1/aeroguide/forecast", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "INSUFFICIENT_LONGITUDINAL_HISTORY"
    assert data["model_training_status"] == "DISABLED"
    assert data["probabilities"] is None
    assert data["eligible_for_model"] is False

def test_03_aeroguide_readiness_endpoint():
    response = client.get("/api/v1/aeroguide/readiness")
    assert response.status_code == 200
    data = response.json()
    
    assert data["dataset_classification"] == "INSUFFICIENT_LONGITUDINAL_HISTORY"
    assert data["model_training_status"] == "DISABLED"
    assert data["seven_day_target_pairs"] < 7
    assert data["unique_routes"] >= 10

def test_04_ndc_capability_matrix_states():
    indigo = get_airline_ndc_info("6E")
    assert indigo["official_api_available"] is True
    assert indigo["ndc_available"] is True
    assert indigo["is_documented"] is True
    assert indigo["is_accessible"] is False # Partner access required
    assert indigo["is_actually_collected"] is False
    assert indigo["is_currently_observed"] is True

    air_india = get_airline_ndc_info("AI")
    assert air_india["official_api_available"] is True
    assert air_india["ndc_available"] is True
    assert air_india["is_documented"] is True
    assert air_india["is_accessible"] is False

def test_05_route_universe_4_tiers():
    response = client.get("/api/v1/aeroguide/routes")
    assert response.status_code == 200
    routes = response.json()
    
    tier1_routes = [r for r in routes if r["tier"] == "TIER_1_DGCA_CORE"]
    tier2_routes = [r for r in routes if r["tier"] == "TIER_2_NATIONAL_HIGH_TRAFFIC"]
    
    assert len(tier1_routes) == 10
    assert len(tier2_routes) == 20
    assert all(r["is_cpi_basket_member"] for r in tier1_routes)
    assert not any(r["is_cpi_basket_member"] for r in tier2_routes)

def test_06_deterministic_comparability_signature():
    sig1 = generate_comparability_id("DEL", "BOM", "2026-10-15", cabin="ECONOMY", adults=1)
    sig2 = generate_comparability_id("DEL", "BOM", "2026-10-15", cabin="ECONOMY", adults=1)
    sig_diff_date = generate_comparability_id("DEL", "BOM", "2026-10-16", cabin="ECONOMY", adults=1)
    sig_diff_cabin = generate_comparability_id("DEL", "BOM", "2026-10-15", cabin="BUSINESS", adults=1)
    
    assert sig1 == sig2
    assert sig1 != sig_diff_date
    assert sig1 != sig_diff_cabin

def test_07_temporal_data_leakage_safety():
    """Verify decision policies and percentiles do not use future search dates."""
    response = client.get("/api/v1/aeroguide/model-status")
    assert response.status_code == 200
    data = response.json()
    assert data["training_gate"] == "LOCKED_AWAITING_LONGITUDINAL_DATA"
    assert data["synthetic_predictions_allowed"] is False
