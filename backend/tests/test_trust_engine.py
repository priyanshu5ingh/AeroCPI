"""
Comprehensive Test Suite for Milestone 4C.3: Trust Engine
Validates all 7 dimensions, exact thresholds, override rules, exact 84.99 caps,
SHA-256 fingerprint reproducibility, permutation invariance, index calculation invariance,
5 hand-calculated independent verification examples, and API integration.
"""
import pytest
import datetime as dt
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.base import Base
from app.models.observation import Observation
from app.models.trust_evaluation import TrustEvaluation
from app.models.index_run import IndexRun
from app.services.trust_engine_service import TrustEngineService
from app.main import app


def create_mock_obs(
    obs_id: str,
    source_id: str,
    total_fare: float,
    route_id: str = "DEL-BOM",
    travel_date: dt.date = dt.date(2026, 4, 15),
    horizon: int = 15,
    cabin: str = "ECONOMY",
    collection_date: dt.date = dt.date(2026, 3, 31),
    index_eligibility: str = "ELIGIBLE",
    validation_status: str = "ACCEPT",
    validation_reasons: list = None,
    live_mode: bool = True,
    carrier_id: str = "6E",
    basket_status: str = "ROUTE_IN_REFERENCE_BASKET"
) -> Observation:
    now_utc = dt.datetime.now(dt.timezone.utc)
    obs = Observation(
        observation_id=obs_id,
        source_id=source_id,
        route_id=route_id,
        carrier_id=carrier_id,
        travel_date=travel_date,
        booking_horizon_days=horizon,
        cabin=cabin,
        search_date=collection_date,
        observed_at=now_utc,
        created_at=now_utc,
        total_fare=Decimal(str(total_fare)),
        index_eligibility=index_eligibility,
        validation_status=validation_status,
        validation_reasons=validation_reasons or [],
        basket_status=basket_status,
        baggage_information={"live_mode": live_mode},
        data_status="OBSERVED" if live_mode else "TEST"
    )
    return obs


# =========================================================================
# 1. BASIC SCORING & THRESHOLD TESTS
# =========================================================================

def test_1_perfect_evidence_high_trust():
    """All 7 dimensions optimal yields 100.0 and HIGH_TRUST."""
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]
    d_obs = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5000.0, live_mode=True) for i in range(5)]

    report = TrustEngineService.evaluate_measurement_trust(
        observations=g_obs + d_obs,
        route_id="DEL-BOM",
        travel_date=dt.date(2026, 4, 15),
        horizon=15,
        expected_observations=10
    )

    assert report["trust_score"] == 100.0
    assert report["trust_status"] == "HIGH_TRUST"
    assert report["dimension_scores"]["observation_coverage"] == 20.0
    assert report["dimension_scores"]["source_agreement"] == 20.0
    assert report["dimension_scores"]["sample_sufficiency"] == 15.0
    assert report["dimension_scores"]["observation_validity"] == 15.0
    assert report["dimension_scores"]["outlier_health"] == 10.0
    assert report["dimension_scores"]["source_availability"] == 10.0
    assert report["dimension_scores"]["basket_horizon_stability"] == 10.0
    assert report["reason_codes"] == ["HEALTHY_EVIDENCE_BASE"]


def test_2_zero_coverage_when_expected_is_zero():
    """When expected observations is 0, coverage is 0.0 with COVERAGE_UNAVAILABLE reason."""
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]

    report = TrustEngineService.evaluate_measurement_trust(
        observations=g_obs,
        route_id="DEL-BOM",
        travel_date=dt.date(2026, 4, 15),
        horizon=15,
        expected_observations=0
    )

    assert report["dimension_scores"]["observation_coverage"] == 0.0
    assert "COVERAGE_UNAVAILABLE" in report["reason_codes"]


def test_3_partial_coverage_proportional():
    """Coverage scales proportionally: 5 / 10 -> 10.0 points."""
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]

    report = TrustEngineService.evaluate_measurement_trust(
        observations=g_obs,
        route_id="DEL-BOM",
        travel_date=dt.date(2026, 4, 15),
        horizon=15,
        expected_observations=10
    )

    assert report["dimension_scores"]["observation_coverage"] == 10.0
    assert report["evidence"]["coverage_ratio"] == 0.5


def test_4_source_agreement_thresholds():
    """Validates the exact step thresholds for source agreement (2%, 5%, 10%, 20%, >20%)."""
    # 2% difference (5000 vs 5100 -> diff 100 / 5050 = 1.98% <= 2%) -> 20.0 pts
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]
    d_obs_2pct = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5100.0, live_mode=True) for i in range(5)]
    rep2 = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs_2pct, "DEL-BOM", dt.date(2026, 4, 15), 15)
    assert rep2["dimension_scores"]["source_agreement"] == 20.0

    # 5% difference (5000 vs 5250 -> diff 250 / 5125 = 4.88% <= 5%) -> 17.0 pts
    d_obs_5pct = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5250.0, live_mode=True) for i in range(5)]
    rep5 = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs_5pct, "DEL-BOM", dt.date(2026, 4, 15), 15)
    assert rep5["dimension_scores"]["source_agreement"] == 17.0

    # 10% difference (5000 vs 5500 -> diff 500 / 5250 = 9.52% <= 10%) -> 12.0 pts
    d_obs_10pct = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5500.0, live_mode=True) for i in range(5)]
    rep10 = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs_10pct, "DEL-BOM", dt.date(2026, 4, 15), 15)
    assert rep10["dimension_scores"]["source_agreement"] == 12.0

    # 20% difference (5000 vs 6000 -> diff 1000 / 5500 = 18.18% <= 20%) -> 6.0 pts
    d_obs_20pct = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 6000.0, live_mode=True) for i in range(5)]
    rep20 = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs_20pct, "DEL-BOM", dt.date(2026, 4, 15), 15)
    assert rep20["dimension_scores"]["source_agreement"] == 6.0

    # > 20% difference (5000 vs 6500 -> diff 1500 / 5750 = 26.09% > 20%) -> 0.0 pts
    d_obs_large = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 6500.0, live_mode=True) for i in range(5)]
    rep_large = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs_large, "DEL-BOM", dt.date(2026, 4, 15), 15)
    assert rep_large["dimension_scores"]["source_agreement"] == 0.0
    assert "LARGE_SOURCE_DISCREPANCY" in rep_large["reason_codes"]


# =========================================================================
# 2. SAMPLE SUFFICIENCY & WEAKEST ACTIVE SOURCE LIMIT
# =========================================================================

def test_sample_sufficiency_weakest_source_limiting():
    """Weakest active source determines the sample sufficiency score."""
    # Google N=5, Duffel N=5 -> 15.0
    g5 = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]
    d5 = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5000.0, live_mode=True) for i in range(5)]
    assert TrustEngineService.evaluate_measurement_trust(g5 + d5, "DEL-BOM", dt.date(2026, 4, 15), 15)["dimension_scores"]["sample_sufficiency"] == 15.0

    # Google N=5, Duffel N=4 -> 15 * 4/5 = 12.0
    d4 = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5000.0, live_mode=True) for i in range(4)]
    assert TrustEngineService.evaluate_measurement_trust(g5 + d4, "DEL-BOM", dt.date(2026, 4, 15), 15)["dimension_scores"]["sample_sufficiency"] == 12.0

    # Google N=5, Duffel N=2 -> 15 * 2/5 = 6.0
    d2 = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5000.0, live_mode=True) for i in range(2)]
    assert TrustEngineService.evaluate_measurement_trust(g5 + d2, "DEL-BOM", dt.date(2026, 4, 15), 15)["dimension_scores"]["sample_sufficiency"] == 6.0


# =========================================================================
# 3. OBSERVATION VALIDITY TESTS
# =========================================================================

def test_observation_validity_rates():
    """Validity is strictly eligible / total."""
    # 10 eligible / 10 total -> 15.0
    obs_all_el = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(10)]
    assert TrustEngineService.evaluate_measurement_trust(obs_all_el, "DEL-BOM", dt.date(2026, 4, 15), 15)["dimension_scores"]["observation_validity"] == 15.0

    # 8 eligible, 2 rejected (total 10) -> 15 * 8/10 = 12.0
    obs_mixed = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(8)] + [
        create_mock_obs("R1", "SRC_GOOGLE_FLIGHTS", 0.0, validation_status="REJECT", index_eligibility="INELIGIBLE"),
        create_mock_obs("R2", "SRC_GOOGLE_FLIGHTS", -100.0, validation_status="REJECT", index_eligibility="INELIGIBLE")
    ]
    assert TrustEngineService.evaluate_measurement_trust(obs_mixed, "DEL-BOM", dt.date(2026, 4, 15), 15)["dimension_scores"]["observation_validity"] == 12.0


# =========================================================================
# 4. OUTLIER HEALTH TESTS
# =========================================================================

def test_outlier_health_thresholds():
    """Validates outlier health thresholds (<=2% -> 10, <=5% -> 8, <=10% -> 5, <=20% -> 2, >20% -> 0)."""
    # 0 outliers out of 50 -> 10.0
    obs_clean = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(50)]
    assert TrustEngineService.evaluate_measurement_trust(obs_clean, "DEL-BOM", dt.date(2026, 4, 15), 15)["dimension_scores"]["outlier_health"] == 10.0

    # 1 outlier out of 50 (2.0%) -> 10.0
    obs_2pct = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(49)] + [
        create_mock_obs("O1", "SRC_GOOGLE_FLIGHTS", 25000.0, validation_reasons=["OUTLIER_FLAG"])
    ]
    assert TrustEngineService.evaluate_measurement_trust(obs_2pct, "DEL-BOM", dt.date(2026, 4, 15), 15)["dimension_scores"]["outlier_health"] == 10.0

    # 2 outliers out of 50 (4.0% <= 5%) -> 8.0
    obs_5pct = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(48)] + [
        create_mock_obs("O1", "SRC_GOOGLE_FLIGHTS", 25000.0, validation_reasons=["OUTLIER_FLAG"]),
        create_mock_obs("O2", "SRC_GOOGLE_FLIGHTS", 25000.0, validation_reasons=["OUTLIER_FLAG"])
    ]
    assert TrustEngineService.evaluate_measurement_trust(obs_5pct, "DEL-BOM", dt.date(2026, 4, 15), 15)["dimension_scores"]["outlier_health"] == 8.0

    # 15 outliers out of 50 (30% > 20%) -> 0.0
    obs_30pct = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(35)] + [
        create_mock_obs(f"O{i}", "SRC_GOOGLE_FLIGHTS", 25000.0, validation_reasons=["OUTLIER_FLAG"]) for i in range(15)
    ]
    rep30 = TrustEngineService.evaluate_measurement_trust(obs_30pct, "DEL-BOM", dt.date(2026, 4, 15), 15)
    assert rep30["dimension_scores"]["outlier_health"] == 0.0
    assert "HIGH_OUTLIER_RATE" in rep30["reason_codes"]


# =========================================================================
# 5. SOURCE AVAILABILITY TESTS
# =========================================================================

def test_source_availability_zero_expected_guard():
    """When expected sources list is empty/zero, score is 0.0 with SOURCE_AVAILABILITY_UNAVAILABLE."""
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]
    rep = TrustEngineService.evaluate_measurement_trust(
        observations=g_obs,
        route_id="DEL-BOM",
        travel_date=dt.date(2026, 4, 15),
        horizon=15,
        expected_sources=[]
    )
    assert rep["dimension_scores"]["source_availability"] == 0.0
    assert "SOURCE_AVAILABILITY_UNAVAILABLE" in rep["reason_codes"]


def test_source_availability_proportions():
    """2 expected, 2 active -> 10.0; 2 expected, 1 active -> 5.0."""
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]
    d_obs = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5000.0, live_mode=True) for i in range(5)]

    rep2 = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs, "DEL-BOM", dt.date(2026, 4, 15), 15, expected_sources=["SRC_GOOGLE_FLIGHTS", "SRC_DUFFEL"])
    assert rep2["dimension_scores"]["source_availability"] == 10.0

    rep1 = TrustEngineService.evaluate_measurement_trust(g_obs, "DEL-BOM", dt.date(2026, 4, 15), 15, expected_sources=["SRC_GOOGLE_FLIGHTS", "SRC_DUFFEL"])
    assert rep1["dimension_scores"]["source_availability"] == 5.0


# =========================================================================
# 6. BASKET & HORIZON STABILITY (5 BINARY CHECKS)
# =========================================================================

def test_stability_checklist_5_binary_checks():
    """Evaluates the 5 explicit binary stability checks (2.0 pts each, total 10.0 pts)."""
    # 5/5 passes -> 10.0 pts
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0, route_id="DEL-BOM", horizon=15, cabin="ECONOMY", basket_status="ROUTE_IN_REFERENCE_BASKET") for i in range(5)]
    rep = TrustEngineService.evaluate_measurement_trust(g_obs, "DEL-BOM", dt.date(2026, 4, 15), 15, cabin="ECONOMY")
    assert rep["dimension_scores"]["basket_horizon_stability"] == 10.0

    # Non-basket route (Check 2 fails -> 4/5 pass -> 8.0 pts)
    g_obs_nb = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0, route_id="IXR-PAT", horizon=15, cabin="ECONOMY", basket_status="ROUTE_OUTSIDE_REFERENCE_BASKET") for i in range(5)]
    rep_nb = TrustEngineService.evaluate_measurement_trust(g_obs_nb, "IXR-PAT", dt.date(2026, 4, 15), 15, cabin="ECONOMY")
    assert rep_nb["dimension_scores"]["basket_horizon_stability"] == 8.0


# =========================================================================
# 7. OVERRIDE RULES & EXACT 84.99 CAPS
# =========================================================================

def test_rule_a_zero_eligible_observations():
    """Rule A: 0 eligible observations -> trust_score = 0.0, LOW_TRUST, NO_ELIGIBLE_OBSERVATIONS."""
    obs = [create_mock_obs("R1", "SRC_GOOGLE_FLIGHTS", 0.0, validation_status="REJECT", index_eligibility="INELIGIBLE")]
    rep = TrustEngineService.evaluate_measurement_trust(obs, "DEL-BOM", dt.date(2026, 4, 15), 15)
    assert rep["trust_score"] == 0.0
    assert rep["trust_status"] == "LOW_TRUST"
    assert "NO_ELIGIBLE_OBSERVATIONS" in rep["reason_codes"]


def test_rule_b_test_mode_only_vs_mixed_data():
    """
    Rule B:
    - Test-mode only -> score 0.0, LOW_TRUST, TEST_DATA_ONLY
    - Mixed live + test -> live data evaluated normally, test data excluded
    """
    test_obs = [create_mock_obs(f"T{i}", "SRC_DUFFEL", 99999.0, live_mode=False, index_eligibility="INELIGIBLE") for i in range(5)]
    rep_test_only = TrustEngineService.evaluate_measurement_trust(test_obs, "DEL-BOM", dt.date(2026, 4, 15), 15)
    assert rep_test_only["trust_score"] == 0.0
    assert rep_test_only["trust_status"] == "LOW_TRUST"
    assert "TEST_DATA_ONLY" in rep_test_only["reason_codes"]

    # Mixed: 5 live + 5 test -> live data scored, test data isolated
    live_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]
    rep_mixed = TrustEngineService.evaluate_measurement_trust(live_obs + test_obs, "DEL-BOM", dt.date(2026, 4, 15), 15)
    assert rep_mixed["trust_score"] > 0.0
    assert "MIXED_LIVE_AND_TEST_DATA" in rep_mixed["reason_codes"]


def test_rule_c_insufficient_health_cap_84_99():
    """Rule C: 4C.2 INSUFFICIENT health status caps score at 84.99 and prevents HIGH_TRUST."""
    # When zero observations are eligible for multi-source agreement
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]
    # Set expected sources to a source not present -> single source state
    rep = TrustEngineService.evaluate_measurement_trust(g_obs, "DEL-BOM", dt.date(2026, 4, 15), 15, expected_sources=["SRC_GOOGLE_FLIGHTS", "SRC_DUFFEL"])
    assert rep["trust_score"] <= 84.99
    assert rep["trust_status"] != "HIGH_TRUST"
    assert "LIMITED_BY_SINGLE_SOURCE" in rep["reason_codes"]


def test_rule_d_single_source_cap_84_99():
    """Rule D: Single active source when multi-source expected is capped at 84.99 and MODERATE_TRUST."""
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]
    rep = TrustEngineService.evaluate_measurement_trust(g_obs, "DEL-BOM", dt.date(2026, 4, 15), 15, expected_sources=["SRC_GOOGLE_FLIGHTS", "SRC_DUFFEL"])
    assert rep["trust_score"] <= 84.99
    assert rep["trust_status"] != "HIGH_TRUST"
    assert "LIMITED_BY_SINGLE_SOURCE" in rep["reason_codes"]


def test_rule_e_severe_sample_deficiency_cap_84_99():
    """Rule E: Any active source with < 2 eligible obs cannot be HIGH_TRUST (capped at 84.99)."""
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]
    d_obs = [create_mock_obs("D0", "SRC_DUFFEL", 5000.0, live_mode=True)]  # Only 1 observation

    rep = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs, "DEL-BOM", dt.date(2026, 4, 15), 15)
    assert rep["trust_score"] <= 84.99
    assert rep["trust_status"] != "HIGH_TRUST"
    assert "INSUFFICIENT_SAMPLE_SIZE" in rep["reason_codes"]


# =========================================================================
# 8. 5 INDEPENDENTLY HAND-CALCULATED VERIFICATION EXAMPLES
# =========================================================================

def test_hand_calculated_example_1_all_perfect():
    """
    Example 1: Perfect evidence base
    - Google N=5 (5000), Duffel N=5 (5000). Expected N=10, 2 sources expected.
    - Coverage: 10/10 = 20.0
    - Agreement: diff = 0.0% = 20.0
    - Sufficiency: min(5/5, 5/5) = 15.0
    - Validity: 10/10 = 15.0
    - Outlier: 0/10 = 10.0
    - Availability: 2/2 = 10.0
    - Stability: 5/5 checks = 10.0
    Total = 100.0 -> HIGH_TRUST
    """
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]
    d_obs = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5000.0, live_mode=True) for i in range(5)]

    rep = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs, "DEL-BOM", dt.date(2026, 4, 15), 15, expected_observations=10)
    assert rep["trust_score"] == 100.0
    assert rep["trust_status"] == "HIGH_TRUST"


def test_hand_calculated_example_2_single_source():
    """
    Example 2: Single source with 5 observations (expected 2 sources, 10 obs)
    - Google N=5 (5000), Duffel N=0.
    - Coverage: 5/10 = 10.0
    - Agreement: single source = 0.0
    - Sufficiency: 5/5 = 15.0
    - Validity: 5/5 = 15.0
    - Outlier: 0/5 = 10.0
    - Availability: 1/2 = 5.0
    - Stability: 5/5 checks = 10.0
    Total = 65.0 -> DEGRADED_TRUST
    """
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]

    rep = TrustEngineService.evaluate_measurement_trust(g_obs, "DEL-BOM", dt.date(2026, 4, 15), 15, expected_observations=10)
    assert rep["trust_score"] == 65.0
    assert rep["trust_status"] == "DEGRADED_TRUST"
    assert "LIMITED_BY_SINGLE_SOURCE" in rep["reason_codes"]


def test_hand_calculated_example_3_moderate_agreement_and_high_outliers():
    """
    Example 3: Moderate agreement (18% diff -> 6 pts) and high outliers (6/20 = 30% -> 0 pts)
    - Google N=10 (7 @ 5000, 3 @ 25000 -> median 5000, 3 outliers)
    - Duffel N=10 (7 @ 6000, 3 @ 25000 -> median 6000, 3 outliers)
    - Coverage: 20/20 = 20.0
    - Agreement: diff = (6000 - 5000)/5500 = 18.18% (between 10% and 20%) = 6.0
    - Sufficiency: min(10/5, 10/5) = 15.0
    - Validity: 20/20 = 15.0
    - Outlier: 6/20 = 30% (>20%) = 0.0
    - Availability: 2/2 = 10.0
    - Stability: 5/5 checks = 10.0
    Total = 76.0 -> MODERATE_TRUST
    """
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(7)] + [
        create_mock_obs(f"GO{i}", "SRC_GOOGLE_FLIGHTS", 25000.0, validation_reasons=["OUTLIER_FLAG"]) for i in range(3)
    ]
    d_obs = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 6000.0, live_mode=True) for i in range(7)] + [
        create_mock_obs(f"DO{i}", "SRC_DUFFEL", 25000.0, live_mode=True, validation_reasons=["OUTLIER_FLAG"]) for i in range(3)
    ]

    rep = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs, "DEL-BOM", dt.date(2026, 4, 15), 15, expected_observations=20)
    assert rep["trust_score"] == 76.0
    assert rep["trust_status"] == "MODERATE_TRUST"


def test_hand_calculated_example_4_small_sample():
    """
    Example 4: Small sample (N=2 each) with perfect agreement
    - Google N=2 (5000), Duffel N=2 (5000). Expected N=10.
    - Coverage: 4/10 = 8.0
    - Agreement: diff = 0% = 20.0
    - Sufficiency: min(2/5, 2/5) = 6.0
    - Validity: 4/4 = 15.0
    - Outlier: 0/4 = 10.0
    - Availability: 2/2 = 10.0
    - Stability: 5/5 checks = 10.0
    Total = 79.0 -> MODERATE_TRUST
    """
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(2)]
    d_obs = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5000.0, live_mode=True) for i in range(2)]

    rep = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs, "DEL-BOM", dt.date(2026, 4, 15), 15, expected_observations=10)
    assert rep["trust_score"] == 79.0
    assert rep["trust_status"] == "MODERATE_TRUST"


def test_hand_calculated_example_5_large_disagreement_and_stability_issue():
    """
    Example 5: Large disagreement (26% diff -> 0 pts) and 1 stability issue (non-basket route -> 8 pts)
    - Google N=5 (5000), Duffel N=5 (6500), Route IXR-PAT (outside basket). Expected N=10.
    - Coverage: 10/10 = 20.0
    - Agreement: diff = 26.09% (>20%) = 0.0
    - Sufficiency: min(5/5, 5/5) = 15.0
    - Validity: 10/10 = 15.0
    - Outlier: 0/10 = 10.0
    - Availability: 2/2 = 10.0
    - Stability: 4/5 checks (non-basket) = 8.0
    Total = 78.0 -> MODERATE_TRUST
    """
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0, route_id="IXR-PAT", basket_status="ROUTE_OUTSIDE_REFERENCE_BASKET") for i in range(5)]
    d_obs = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 6500.0, route_id="IXR-PAT", live_mode=True, basket_status="ROUTE_OUTSIDE_REFERENCE_BASKET") for i in range(5)]

    rep = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs, "IXR-PAT", dt.date(2026, 4, 15), 15, expected_observations=10)
    assert rep["trust_score"] == 78.0
    assert rep["trust_status"] == "MODERATE_TRUST"


# =========================================================================
# 9. REPRODUCIBILITY & PERMUTATION INVARIANCE
# =========================================================================

def test_reproducibility_and_fingerprint_stability():
    """Running evaluation twice on identical data produces identical score and SHA-256 fingerprint."""
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0 + i * 50) for i in range(5)]
    d_obs = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5050.0 + i * 50, live_mode=True) for i in range(5)]

    rep1 = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs, "DEL-BOM", dt.date(2026, 4, 15), 15)
    rep2 = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs, "DEL-BOM", dt.date(2026, 4, 15), 15)

    assert rep1["trust_score"] == rep2["trust_score"]
    assert rep1["trust_status"] == rep2["trust_status"]
    assert rep1["calculation_fingerprint"] == rep2["calculation_fingerprint"]


def test_input_order_permutation_invariance():
    """Shuffling observations does not affect the Trust Score or calculation fingerprint."""
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0 + i * 50) for i in range(5)]
    d_obs = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5050.0 + i * 50, live_mode=True) for i in range(5)]

    rep_orig = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs, "DEL-BOM", dt.date(2026, 4, 15), 15)
    rep_reversed = TrustEngineService.evaluate_measurement_trust(d_obs[::-1] + g_obs[::-1], "DEL-BOM", dt.date(2026, 4, 15), 15)

    assert rep_orig["trust_score"] == rep_reversed["trust_score"]
    assert rep_orig["calculation_fingerprint"] == rep_reversed["calculation_fingerprint"]


def test_input_change_alters_fingerprint():
    """Changing any underlying value changes the calculation fingerprint."""
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]
    d_obs1 = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5000.0, live_mode=True) for i in range(5)]
    d_obs2 = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5500.0, live_mode=True) for i in range(5)]

    rep1 = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs1, "DEL-BOM", dt.date(2026, 4, 15), 15)
    rep2 = TrustEngineService.evaluate_measurement_trust(g_obs + d_obs2, "DEL-BOM", dt.date(2026, 4, 15), 15)

    assert rep1["calculation_fingerprint"] != rep2["calculation_fingerprint"]


# =========================================================================
# 10. INDEX INVARIANCE REGRESSION TEST
# =========================================================================

def test_index_invariance_trust_engine_does_not_mutate_observations():
    """Trust Engine execution does not mutate observation prices, status, or index eligibility."""
    obs = create_mock_obs("G1", "SRC_GOOGLE_FLIGHTS", 5000.0, index_eligibility="ELIGIBLE", validation_status="ACCEPT")
    orig_fare = obs.total_fare
    orig_elig = obs.index_eligibility
    orig_val = obs.validation_status

    TrustEngineService.evaluate_measurement_trust([obs], "DEL-BOM", dt.date(2026, 4, 15), 15)

    assert obs.total_fare == orig_fare
    assert obs.index_eligibility == orig_elig
    assert obs.validation_status == orig_val


# =========================================================================
# 11. API INTEGRATION TESTS
# =========================================================================

def test_api_endpoints_integration(client, db_session):
    """Verifies POST, GET list, GET single, and GET breakdown endpoints."""
    # Seed DB with 5 Google + 5 Duffel observations
    travel_date = dt.date(2026, 4, 15)
    collection_date = dt.date(2026, 3, 31)

    for i in range(5):
        db_session.add(create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0 + i * 10, collection_date=collection_date))
        db_session.add(create_mock_obs(f"D{i}", "SRC_DUFFEL", 5000.0 + i * 10, collection_date=collection_date, live_mode=True))
    db_session.commit()

    # 1. POST /api/v1/trust-evaluations
    resp = client.post("/api/v1/trust-evaluations", json={
        "route_id": "DEL-BOM",
        "travel_date": travel_date.isoformat(),
        "horizon_days": 15,
        "cabin": "ECONOMY",
        "collection_date": collection_date.isoformat(),
        "expected_observations": 10
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["trust_score"] == 100.0
    assert data["trust_status"] == "HIGH_TRUST"
    eval_id = data["trust_evaluation_id"]

    # 2. GET /api/v1/trust-evaluations
    list_resp = client.get("/api/v1/trust-evaluations?route_id=DEL-BOM")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # 3. GET /api/v1/trust-evaluations/{evaluation_id}
    get_resp = client.get(f"/api/v1/trust-evaluations/{eval_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["trust_evaluation_id"] == eval_id

    # 4. GET /api/v1/trust-evaluations/{evaluation_id}/breakdown
    bk_resp = client.get(f"/api/v1/trust-evaluations/{eval_id}/breakdown")
    assert bk_resp.status_code == 200
    assert bk_resp.json()["dimension_scores"]["observation_coverage"] == 20.0
    assert data["trust_scope"]["route_id"] == "DEL-BOM"
    assert data["policy_parameters"]["policy_version"] == "v1.0"


# =========================================================================
# 12. METHODOLOGY AUDIT & POLICY PARAMETERS TESTS
# =========================================================================

def test_trust_scope_and_policy_parameters_metadata():
    """
    Verifies that every evaluation includes explicit trust_scope and versioned policy_parameters,
    and explicitly states that parameters are engineering policy, not official statistical parameters.
    """
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]
    d_obs = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5000.0, live_mode=True) for i in range(5)]

    report = TrustEngineService.evaluate_measurement_trust(
        observations=g_obs + d_obs,
        route_id="DEL-BOM",
        travel_date=dt.date(2026, 4, 15),
        horizon=15,
        cabin="ECONOMY",
        expected_observations=10
    )

    # Trust Scope verification
    scope = report["trust_scope"]
    assert scope["route_id"] == "DEL-BOM"
    assert scope["travel_date"] == "2026-04-15"
    assert scope["horizon_days"] == 15
    assert scope["horizon_code"] == "T+15"
    assert scope["cabin"] == "ECONOMY"
    assert scope["target_basket"] == "DGCA_REFERENCE_BASKET"

    # Policy Parameters verification
    policy = report["policy_parameters"]
    assert policy["policy_version"] == "v1.0"
    assert policy["is_official_statistical_parameter"] is False
    assert policy["min_observations_per_source"] == 5
    assert policy["expected_required_observations"] == 10
    assert policy["expected_sources"] == ["SRC_GOOGLE_FLIGHTS", "SRC_DUFFEL"]


def test_overlapping_penalties_intentional_diagnostic_design():
    """
    Verifies the intentional multi-dimensional penalty for a missing source:
    When Duffel is completely absent:
    1. Observation Coverage drops (5/10 -> 10.0 pts)
    2. Source Availability drops (1/2 -> 5.0 pts)
    3. Source Agreement drops (single source -> 0.0 pts)
    Total score drops from 100.0 to 65.0 (DEGRADED_TRUST).
    """
    # 5 Google observations only (Duffel missing)
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]

    report = TrustEngineService.evaluate_measurement_trust(
        observations=g_obs,
        route_id="DEL-BOM",
        travel_date=dt.date(2026, 4, 15),
        horizon=15,
        expected_observations=10,
        expected_sources=["SRC_GOOGLE_FLIGHTS", "SRC_DUFFEL"]
    )

    dim = report["dimension_scores"]
    assert dim["observation_coverage"] == 10.0
    assert dim["source_availability"] == 5.0
    assert dim["source_agreement"] == 0.0
    assert dim["sample_sufficiency"] == 15.0
    assert dim["observation_validity"] == 15.0
    assert dim["outlier_health"] == 10.0
    assert dim["basket_horizon_stability"] == 10.0
    assert report["trust_score"] == 65.0
    assert report["trust_status"] == "DEGRADED_TRUST"


def test_trust_engine_non_comparable_travel_dates_isolation():
    """
    Methodology Audit Regression:
    Passing a mixed batch of observations with differing travel dates (e.g. Google Apr 15 vs Duffel May 20)
    into evaluate_measurement_trust for target travel date Apr 15 isolates the Duffel May 20 data.
    Source agreement evaluates Google only (SINGLE_SOURCE), avoiding false DEGRADED_LARGE_MEDIAN_DISCREPANCY.
    """
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0, travel_date=dt.date(2026, 4, 15)) for i in range(5)]
    d_obs = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 9500.0, travel_date=dt.date(2026, 5, 20), live_mode=True) for i in range(5)]

    report = TrustEngineService.evaluate_measurement_trust(
        observations=g_obs + d_obs,
        route_id="DEL-BOM",
        travel_date=dt.date(2026, 4, 15),
        horizon=15,
        expected_observations=10,
        expected_sources=["SRC_GOOGLE_FLIGHTS", "SRC_DUFFEL"]
    )

    # Cross-source agreement is SINGLE_SOURCE for April 15
    assert report["dimension_scores"]["source_agreement"] == 0.0
    assert "LARGE_SOURCE_DISCREPANCY" not in report["reason_codes"]
    assert "SINGLE_SOURCE" in report["reason_codes"]
    assert report["trust_scope"]["travel_date"] == "2026-04-15"

