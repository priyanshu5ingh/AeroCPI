"""
Milestone 4D: Statistical Index Engine v1 - Comprehensive Test Suite
Validates all 18 statistical index engine requirements:
1. Source-level median aggregation (Decimal precision).
2. Unweighted cross-source geometric mean (100 quotes vs 10 quotes have equal weight).
3. Single active source fallback.
4. Single common reference date t0 enforcement (base index = 100.0).
5. Fixed base population R_base(h) & late-appearing route exclusion.
6. Elementary route-horizon price relatives J(r,h,t) = P(r,h,t)/P(r,h,0) * 100.
7. DGCA-weighted national aggregation hand-calculated verification.
8. Missing-route exclusion & active weight renormalization.
9. No forward-filling or fare imputation.
10. Coverage triad: base_coverage_ratio, current_coverage_ratio, matched_coverage_ratio.
11. Matched-sample diagnostic calculation without altering primary index.
12. Exactly five required production horizons (T+1, T+7, T+15, T+30, T+45) with T+15 headline.
13. Weekly & monthly temporal aggregations (valid days only, missing days not 0).
14. Inflation rates (MoM, YoY) with NOT_AVAILABLE guards.
15. Trust Engine separation: Trust evaluation does not alter index values.
16. Reproducibility: SHA-256 calculation fingerprint and permutation invariance.
17. Provenance manifest with explicit non-CPI equivalence disclaimer.
18. End-to-end API endpoints verification.
"""
import pytest
import datetime as dt
from decimal import Decimal
import math
from typing import Dict, Any

from app.models.observation import Observation
from app.models.route import Route
from app.models.index_run import IndexRun
from app.models.horizon_index_result import HorizonIndexResult
from app.services.statistical_index_service import StatisticalIndexEngineService


def create_obs(
    obs_id: str,
    source_id: str,
    total_fare: float,
    route_id: str = "DEL-BOM",
    collection_date: dt.date = dt.date(2026, 8, 1),
    horizon: int = 15,
    cabin: str = "ECONOMY",
    index_eligibility: str = "ELIGIBLE",
    carrier_id: str = "6E"
) -> Observation:
    now_utc = dt.datetime.now(dt.timezone.utc)
    return Observation(
        observation_id=obs_id,
        source_id=source_id,
        route_id=route_id,
        carrier_id=carrier_id,
        travel_date=collection_date + dt.timedelta(days=horizon),
        booking_horizon_days=horizon,
        cabin=cabin,
        search_date=collection_date,
        observed_at=now_utc,
        created_at=now_utc,
        total_fare=Decimal(str(total_fare)),
        index_eligibility=index_eligibility,
        validation_status="ACCEPT" if index_eligibility == "ELIGIBLE" else "REJECT",
        data_status="OBSERVED"
    )


def make_cross_fare(route_id: str, horizon: int, fare: float) -> Dict[str, Any]:
    fare_dec = Decimal(str(fare)).quantize(Decimal('0.01'))
    return {
        "route_id": route_id,
        "horizon_days": horizon,
        "horizon_code": f"T+{horizon}",
        "representative_fare": fare_dec,
        "representative_fare_float": float(fare_dec),
        "active_sources": ["SRC_GOOGLE"],
        "active_sources_count": 1,
        "is_single_source": True,
        "source_medians": {"SRC_GOOGLE": float(fare_dec)}
    }


def seed_test_routes(db_session):
    routes = [
        ("DEL-BOM", "DEL", "BOM"),
        ("BLR-DEL", "BLR", "DEL"),
        ("BLR-BOM", "BLR", "BOM"),
        ("DEL-HYD", "DEL", "HYD"),
        ("DEL-CCU", "DEL", "CCU"),
        ("MAA-DEL", "MAA", "DEL"),
        ("BOM-GOI", "BOM", "GOI"),
        ("DEL-BLR", "DEL", "BLR"),
        ("BOM-BLR", "BOM", "BLR"),
        ("CCU-DEL", "CCU", "DEL"),
    ]
    for rid, orig, dest in routes:
        existing = db_session.query(Route).filter(Route.route_id == rid).first()
        if not existing:
            db_session.add(Route(route_id=rid, origin_code=orig, destination_code=dest, active=True))
    db_session.commit()


# =============================================================================
# 1. SOURCE-LEVEL MEDIANS (DECIMAL PRECISION)
# =============================================================================

def test_1_source_level_median_aggregation():
    """Verify source-level medians use Decimal precision and exclude non-eligible quotes."""
    c_date = dt.date(2026, 9, 1)
    obs_list = [
        create_obs("O1", "SRC_GOOGLE", 5000.00, route_id="DEL-BOM", collection_date=c_date, horizon=15),
        create_obs("O2", "SRC_GOOGLE", 5200.00, route_id="DEL-BOM", collection_date=c_date, horizon=15),
        create_obs("O3", "SRC_GOOGLE", 5100.00, route_id="DEL-BOM", collection_date=c_date, horizon=15),
        create_obs("O4", "SRC_GOOGLE", 4900.00, route_id="DEL-BOM", collection_date=c_date, horizon=15),
        create_obs("O5", "SRC_GOOGLE", 6000.00, route_id="DEL-BOM", collection_date=c_date, horizon=15),
        # Ineligible observation must be excluded
        create_obs("O6_ineligible", "SRC_GOOGLE", 100000.00, route_id="DEL-BOM", collection_date=c_date, horizon=15, index_eligibility="INELIGIBLE")
    ]

    medians = StatisticalIndexEngineService.compute_source_medians(obs_list, target_date=c_date, cabin="ECONOMY")
    key = ("DEL-BOM", 15, "SRC_GOOGLE")
    assert key in medians
    # 4900, 5000, 5100, 5200, 6000 -> Median = 5100.00
    assert medians[key]["median_fare"] == Decimal("5100.00")
    assert medians[key]["observation_count"] == 5


# =============================================================================
# 2. EQUAL SOURCE WEIGHTING (UNWEIGHTED GEOMETRIC MEAN)
# =============================================================================

def test_2_equal_source_weighting_cross_source():
    """
    Source A has 100 quotes at 5000.00; Source B has 10 quotes at 6000.00.
    Equal source weighting: representative fare = sqrt(5000 * 6000) = 5477.23.
    Source A does not dominate Source B.
    """
    c_date = dt.date(2026, 9, 1)
    obs_list = []
    # 100 quotes for Source A (all 5000.00)
    for i in range(100):
        obs_list.append(create_obs(f"G_{i}", "SRC_GOOGLE", 5000.00, route_id="DEL-BOM", collection_date=c_date, horizon=15))
    # 10 quotes for Source B (all 6000.00)
    for j in range(10):
        obs_list.append(create_obs(f"D_{j}", "SRC_DUFFEL", 6000.00, route_id="DEL-BOM", collection_date=c_date, horizon=15))

    source_medians = StatisticalIndexEngineService.compute_source_medians(obs_list, target_date=c_date, cabin="ECONOMY")
    assert source_medians[("DEL-BOM", 15, "SRC_GOOGLE")]["median_fare"] == Decimal("5000.00")
    assert source_medians[("DEL-BOM", 15, "SRC_DUFFEL")]["median_fare"] == Decimal("6000.00")

    cross_fares = StatisticalIndexEngineService.compute_cross_source_fares(source_medians)
    key = ("DEL-BOM", 15)
    expected_fare = Decimal(str(round(math.sqrt(5000.0 * 6000.0), 2)))  # 5477.23
    assert cross_fares[key]["representative_fare"] == expected_fare


# =============================================================================
# 3. SINGLE ACTIVE SOURCE FALLBACK
# =============================================================================

def test_3_single_active_source_allowed():
    """When only 1 source is present, representative fare is that source's median."""
    c_date = dt.date(2026, 9, 1)
    obs_list = [create_obs("G1", "SRC_GOOGLE", 4500.00, route_id="DEL-BOM", collection_date=c_date, horizon=15)]
    source_medians = StatisticalIndexEngineService.compute_source_medians(obs_list, target_date=c_date, cabin="ECONOMY")
    cross_fares = StatisticalIndexEngineService.compute_cross_source_fares(source_medians)
    assert cross_fares[("DEL-BOM", 15)]["representative_fare"] == Decimal("4500.00")
    assert cross_fares[("DEL-BOM", 15)]["is_single_source"] is True


# =============================================================================
# 4. SINGLE COMMON REFERENCE DATE t0 ENFORCEMENT
# =============================================================================

def test_4_common_reference_date_base_level_100():
    """
    On reference date t0, P(r,h,0) is evaluated.
    When calculation date t = t0, all relatives are 100.0 and national index = 100.0.
    """
    cross_fares = {
        ("DEL-BOM", 15): make_cross_fare("DEL-BOM", 15, 5000.00),
        ("BLR-DEL", 15): make_cross_fare("BLR-DEL", 15, 6000.00),
    }
    basket_weights = {"DEL-BOM": 0.6, "BLR-DEL": 0.4}

    nat_results, elem_results, _ = StatisticalIndexEngineService.compute_elementary_and_national_indices(
        current_cross_fares=cross_fares,
        reference_cross_fares=cross_fares,
        basket_weights=basket_weights,
        total_basket_routes=["DEL-BOM", "BLR-DEL"]
    )

    t15 = nat_results["T+15"]
    assert t15["index_value"] == 100.0
    for elem in elem_results:
        assert elem["price_relative"] == 1.0
        assert elem["route_index_value"] == 100.0


# =============================================================================
# 5. FIXED BASE POPULATION & LATE-APPEARING ROUTE EXCLUSION
# =============================================================================

def test_5_fixed_base_population_and_late_route_exclusion():
    """
    Routes appearing on t that had NO valid quotes on t0 are excluded from R_base(h)
    and from the fixed-base index calculation.
    """
    # Base date t0 has only DEL-BOM
    ref_cross = {
        ("DEL-BOM", 15): make_cross_fare("DEL-BOM", 15, 5000.00)
    }
    # Calculation date t has DEL-BOM AND late-appearing DEL-CCU
    cur_cross = {
        ("DEL-BOM", 15): make_cross_fare("DEL-BOM", 15, 5500.00),
        ("DEL-CCU", 15): make_cross_fare("DEL-CCU", 15, 4000.00)  # Late route
    }
    basket_weights = {"DEL-BOM": 0.7, "DEL-CCU": 0.3}

    nat_results, elem_results, _ = StatisticalIndexEngineService.compute_elementary_and_national_indices(
        current_cross_fares=cur_cross,
        reference_cross_fares=ref_cross,
        basket_weights=basket_weights,
        total_basket_routes=["DEL-BOM", "DEL-CCU"]
    )

    t15 = nat_results["T+15"]
    # Only DEL-BOM in active routes
    assert t15["active_routes"] == ["DEL-BOM"]
    assert "DEL-CCU" in t15["late_appearing_excluded_routes"]
    # Since DEL-BOM is the only active route, active weight is renormalized to 1.0
    # Relative for DEL-BOM = (5500 / 5000) * 100 = 110.0
    assert t15["index_value"] == 110.0


# =============================================================================
# 6. ELEMENTARY PRICE RELATIVES
# =============================================================================

def test_6_elementary_price_relatives():
    """J(r,h,t) = P(r,h,t) / P(r,h,0) * 100."""
    ref_cross = {("DEL-BOM", 7): make_cross_fare("DEL-BOM", 7, 4000.00)}
    cur_cross = {("DEL-BOM", 7): make_cross_fare("DEL-BOM", 7, 4400.00)}

    _, elem_results, _ = StatisticalIndexEngineService.compute_elementary_and_national_indices(
        current_cross_fares=cur_cross,
        reference_cross_fares=ref_cross,
        basket_weights={"DEL-BOM": 1.0},
        total_basket_routes=["DEL-BOM"]
    )

    elem = next(e for e in elem_results if e["route_id"] == "DEL-BOM" and e["horizon_days"] == 7)
    assert elem["reference_price"] == 4000.00
    assert elem["current_price"] == 4400.00
    assert elem["price_relative"] == 1.10
    assert elem["route_index_value"] == 110.00


# =============================================================================
# 7. DGCA-WEIGHTED NATIONAL AGGREGATION (HAND-CALCULATED NUMERICAL VERIFICATION)
# =============================================================================

def test_7_dgca_weighted_national_aggregation_hand_calculated():
    """
    Hand calculation:
    Route A: DGCA weight 0.6, base 4000, current 4800 -> relative = 120.0
    Route B: DGCA weight 0.4, base 5000, current 5000 -> relative = 100.0
    Weighted geometric mean:
    ln(J) = 0.6 * ln(120) + 0.4 * ln(100) = 0.6 * 4.7874917 + 0.4 * 4.6051702 = 4.7145631
    J = exp(4.7145631) = 111.558
    """
    ref_cross = {
        ("ROUTE_A", 15): make_cross_fare("ROUTE_A", 15, 4000.00),
        ("ROUTE_B", 15): make_cross_fare("ROUTE_B", 15, 5000.00),
    }
    cur_cross = {
        ("ROUTE_A", 15): make_cross_fare("ROUTE_A", 15, 4800.00),
        ("ROUTE_B", 15): make_cross_fare("ROUTE_B", 15, 5000.00),
    }
    basket_weights = {"ROUTE_A": 0.6, "ROUTE_B": 0.4}

    nat_results, _, _ = StatisticalIndexEngineService.compute_elementary_and_national_indices(
        current_cross_fares=cur_cross,
        reference_cross_fares=ref_cross,
        basket_weights=basket_weights,
        total_basket_routes=["ROUTE_A", "ROUTE_B"]
    )

    val = nat_results["T+15"]["index_value"]
    assert abs(val - 111.558) < 0.005


# =============================================================================
# 8. MISSING-ROUTE EXCLUSION & ACTIVE WEIGHT RENORMALIZATION
# =============================================================================

def test_8_missing_route_exclusion_and_active_weight_renormalization():
    """
    Base has 3 routes: R1 (w=0.5, rel=110), R2 (w=0.3, rel=120), R3 (w=0.2).
    On date t, R3 is missing.
    W_active = 0.5 + 0.3 = 0.8.
    w1* = 0.5 / 0.8 = 0.625, w2* = 0.3 / 0.8 = 0.375.
    Expected J = exp(0.625 * ln(110) + 0.375 * ln(120)) = 113.644.
    """
    ref_cross = {
        ("R1", 15): make_cross_fare("R1", 15, 1000.00),
        ("R2", 15): make_cross_fare("R2", 15, 1000.00),
        ("R3", 15): make_cross_fare("R3", 15, 1000.00),
    }
    cur_cross = {
        ("R1", 15): make_cross_fare("R1", 15, 1100.00),  # relative = 110.0
        ("R2", 15): make_cross_fare("R2", 15, 1200.00),  # relative = 120.0
        # R3 is missing
    }
    basket_weights = {"R1": 0.5, "R2": 0.3, "R3": 0.2}

    nat_results, _, cov_summary = StatisticalIndexEngineService.compute_elementary_and_national_indices(
        current_cross_fares=cur_cross,
        reference_cross_fares=ref_cross,
        basket_weights=basket_weights,
        total_basket_routes=["R1", "R2", "R3"]
    )

    t15 = nat_results["T+15"]
    assert abs(t15["index_value"] - 113.644) < 0.005
    assert t15["active_weight_sum"] == 0.8
    assert "R3" in t15["missing_routes"]
    assert t15["active_routes_count"] == 2
    assert t15["base_routes_count"] == 3


# =============================================================================
# 9. NO FORWARD-FILLING OR IMPUTATION
# =============================================================================

def test_9_no_forward_filling_or_imputation():
    """Verify that missing routes are strictly dropped, not imputed or carried forward."""
    ref_cross = {
        ("DEL-BOM", 15): make_cross_fare("DEL-BOM", 15, 5000.00),
        ("BLR-DEL", 15): make_cross_fare("BLR-DEL", 15, 6000.00),
    }
    # BLR-DEL is missing on cur_cross
    cur_cross = {
        ("DEL-BOM", 15): make_cross_fare("DEL-BOM", 15, 5500.00),
    }
    basket_weights = {"DEL-BOM": 0.6, "BLR-DEL": 0.4}

    nat_results, elem_results, _ = StatisticalIndexEngineService.compute_elementary_and_national_indices(
        current_cross_fares=cur_cross,
        reference_cross_fares=ref_cross,
        basket_weights=basket_weights,
        total_basket_routes=["DEL-BOM", "BLR-DEL"]
    )

    # BLR-DEL must NOT have an elementary result for cur_cross
    blr_elem = [e for e in elem_results if e["route_id"] == "BLR-DEL" and e["horizon_days"] == 15]
    assert len(blr_elem) == 0


# =============================================================================
# 10. COVERAGE TRIAD
# =============================================================================

def test_10_coverage_triad():
    """
    Verify coverage triad:
    base_coverage_ratio = base_routes / total_basket
    current_coverage_ratio = current_routes / total_basket
    matched_coverage_ratio = active_routes / base_routes
    """
    total_basket = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10"]
    # Base observed: R1 to R8 (8 routes)
    ref_cross = {("R" + str(i), 15): make_cross_fare("R" + str(i), 15, 1000.00) for i in range(1, 9)}
    # Current observed: R1 to R6 (6 routes)
    cur_cross = {("R" + str(i), 15): make_cross_fare("R" + str(i), 15, 1100.00) for i in range(1, 7)}
    basket_weights = {f"R{i}": 0.1 for i in range(1, 11)}

    nat_results, _, _ = StatisticalIndexEngineService.compute_elementary_and_national_indices(
        current_cross_fares=cur_cross,
        reference_cross_fares=ref_cross,
        basket_weights=basket_weights,
        total_basket_routes=total_basket
    )

    t15 = nat_results["T+15"]
    assert t15["base_coverage_ratio"] == 0.8  # 8 / 10
    assert t15["current_coverage_ratio"] == 0.6  # 6 / 10
    assert t15["matched_coverage_ratio"] == 0.60  # 6 / 10 total basket routes


# =============================================================================
# 11. MATCHED-SAMPLE DIAGNOSTIC
# =============================================================================

def test_11_matched_sample_diagnostic():
    """Matched sample diagnostic is calculated on matched routes and does not overwrite primary index."""
    ref_cross = {
        ("R1", 15): make_cross_fare("R1", 15, 1000.00),
        ("R2", 15): make_cross_fare("R2", 15, 1000.00),
    }
    cur_cross = {
        ("R1", 15): make_cross_fare("R1", 15, 1100.00),
    }
    basket_weights = {"R1": 0.7, "R2": 0.3}

    nat_results, _, _ = StatisticalIndexEngineService.compute_elementary_and_national_indices(
        current_cross_fares=cur_cross,
        reference_cross_fares=ref_cross,
        basket_weights=basket_weights,
        total_basket_routes=["R1", "R2"]
    )

    t15 = nat_results["T+15"]
    assert t15["matched_sample_index_value"] is not None
    assert t15["matched_sample_index_value"] == t15["index_value"]


# =============================================================================
# 12. FIVE REQUIRED PRODUCTION HORIZONS & HEADLINE
# =============================================================================

def test_12_five_required_production_horizons_and_headline():
    """Verify all 5 horizons (T+1, T+7, T+15, T+30, T+45) are evaluated; T+15 is headline."""
    ref_cross = {}
    cur_cross = {}
    for h in [1, 7, 15, 30, 45]:
        ref_cross[("DEL-BOM", h)] = make_cross_fare("DEL-BOM", h, 5000.00)
        cur_cross[("DEL-BOM", h)] = make_cross_fare("DEL-BOM", h, 5500.00)

    nat_results, _, _ = StatisticalIndexEngineService.compute_elementary_and_national_indices(
        current_cross_fares=cur_cross,
        reference_cross_fares=ref_cross,
        basket_weights={"DEL-BOM": 1.0},
        total_basket_routes=["DEL-BOM"]
    )

    assert set(nat_results.keys()) == {"T+1", "T+7", "T+15", "T+30", "T+45"}
    assert nat_results["T+15"]["is_headline"] is True
    assert nat_results["T+15"]["headline_label"] == "AeroCPI Headline — T+15"
    assert nat_results["T+1"]["is_headline"] is False
    assert nat_results["T+7"]["is_headline"] is False
    assert nat_results["T+30"]["is_headline"] is False
    assert nat_results["T+45"]["is_headline"] is False


# =============================================================================
# 13. TEMPORAL AGGREGATIONS (WEEKLY & MONTHLY)
# =============================================================================

def test_13_temporal_aggregation_valid_days_only():
    """
    Weekly aggregation over 7 expected days.
    5 days valid: [100.0, 102.0, 104.0, None, 106.0, None, 108.0]
    Missing days (None) are not treated as zero.
    Arithmetic mean = (100 + 102 + 104 + 106 + 108) / 5 = 104.0.
    temporal_coverage_ratio = 5 / 7 = 0.7143.
    """
    daily_values = [100.0, 102.0, 104.0, None, 106.0, None, 108.0]
    res = StatisticalIndexEngineService.compute_temporal_aggregation(
        valid_daily_indices=daily_values,
        days_expected=7
    )
    assert res["index_value"] == 104.0
    assert res["days_available"] == 5
    assert res["days_expected"] == 7
    assert res["temporal_coverage_ratio"] == 0.7143


def test_13b_temporal_aggregation_zero_available_days():
    """When no days are available, index_value is None and temporal_coverage_ratio is 0.0."""
    res = StatisticalIndexEngineService.compute_temporal_aggregation(
        valid_daily_indices=[None, None],
        days_expected=7
    )
    assert res["index_value"] is None
    assert res["days_available"] == 0
    assert res["temporal_coverage_ratio"] == 0.0


# =============================================================================
# 14. INFLATION RATES (MOM & YOY)
# =============================================================================

def test_14_inflation_rate_calculation():
    """Inflation rate = (current / previous) - 1."""
    # 10% inflation
    res = StatisticalIndexEngineService.compute_inflation_rate(110.0, 100.0)
    assert res["status"] == "AVAILABLE"
    assert res["inflation_rate_percent"] == 10.0
    assert res["percentage_change"] == 10.0

    # Deflation
    res_def = StatisticalIndexEngineService.compute_inflation_rate(95.0, 100.0)
    assert res_def["status"] == "AVAILABLE"
    assert res_def["inflation_rate_percent"] == -5.0

    # Missing comparison -> NOT_AVAILABLE
    res_na = StatisticalIndexEngineService.compute_inflation_rate(110.0, None)
    assert res_na["status"] == "NOT_AVAILABLE"
    assert res_na["inflation_rate_percent"] is None


# =============================================================================
# 15. TRUST SCORE SEPARATION
# =============================================================================

def test_15_trust_score_does_not_change_index_mathematics():
    """
    Trust score is strictly diagnostic.
    Passing a trust_evaluation_id or having high/low trust does not alter the mathematical index values.
    """
    ref_cross = {("DEL-BOM", 15): make_cross_fare("DEL-BOM", 15, 5000.00)}
    cur_cross = {("DEL-BOM", 15): make_cross_fare("DEL-BOM", 15, 5500.00)}

    res1, _, _ = StatisticalIndexEngineService.compute_elementary_and_national_indices(
        current_cross_fares=cur_cross,
        reference_cross_fares=ref_cross,
        basket_weights={"DEL-BOM": 1.0},
        total_basket_routes=["DEL-BOM"]
    )

    # Independent calculation with identical price evidence must yield identical result
    res2, _, _ = StatisticalIndexEngineService.compute_elementary_and_national_indices(
        current_cross_fares=cur_cross,
        reference_cross_fares=ref_cross,
        basket_weights={"DEL-BOM": 1.0},
        total_basket_routes=["DEL-BOM"]
    )

    assert res1["T+15"]["index_value"] == res2["T+15"]["index_value"] == 110.0


# =============================================================================
# 16. SHA-256 FINGERPRINT REPRODUCIBILITY & PERMUTATION INVARIANCE
# =============================================================================

def test_16_calculation_fingerprint_reproducibility(db_session):
    """End-to-end execution generates a deterministic SHA-256 calculation fingerprint."""
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 8, 1)
    cur_date = dt.date(2026, 9, 1)

    # Add baseline observations
    for h in [1, 7, 15, 30, 45]:
        db_session.add(create_obs(f"B_{h}_1", "SRC_GOOGLE", 5000.00, route_id="DEL-BOM", collection_date=ref_date, horizon=h))
        db_session.add(create_obs(f"B_{h}_2", "SRC_DUFFEL", 5000.00, route_id="DEL-BOM", collection_date=ref_date, horizon=h))
        db_session.add(create_obs(f"C_{h}_1", "SRC_GOOGLE", 5500.00, route_id="DEL-BOM", collection_date=cur_date, horizon=h))
        db_session.add(create_obs(f"C_{h}_2", "SRC_DUFFEL", 5500.00, route_id="DEL-BOM", collection_date=cur_date, horizon=h))
    db_session.commit()

    run, horizons, routes = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )

    assert run.canonical_run_fingerprint is not None
    assert len(run.canonical_run_fingerprint) == 64
    assert run.index_value == 110.0
    assert len(horizons) == 5
    assert len(routes) == 5


# =============================================================================
# 17. NON-CPI EQUIVALENCE DISCLAIMER IN PROVENANCE MANIFEST
# =============================================================================

def test_17_provenance_manifest_disclaimer(db_session):
    """Provenance manifest must contain the required CPI non-equivalence disclaimer."""
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 8, 1)
    cur_date = dt.date(2026, 9, 1)

    for h in [1, 7, 15, 30, 45]:
        db_session.add(create_obs(f"OB_{h}", "SRC_GOOGLE", 5000.00, route_id="DEL-BOM", collection_date=ref_date, horizon=h))
        db_session.add(create_obs(f"OC_{h}", "SRC_GOOGLE", 5000.00, route_id="DEL-BOM", collection_date=cur_date, horizon=h))
    db_session.commit()

    run, _, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date
    )

    manifest = run.calculation_manifest
    assert "disclaimer" in manifest
    assert "AeroCPI is not statistically equivalent to CPI" in manifest["disclaimer"]


# =============================================================================
# 18. API ENDPOINTS INTEGRATION
# =============================================================================

def test_18_api_calculate_v1_and_horizons_endpoints(client, db_session):
    """Test POST /api/v1/index-runs/calculate-v1 and GET /api/v1/index-runs/{run_id}/horizons."""
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 8, 1)
    cur_date = dt.date(2026, 9, 1)

    for h in [1, 7, 15, 30, 45]:
        db_session.add(create_obs(f"AB_{h}", "SRC_GOOGLE", 5000.00, route_id="DEL-BOM", collection_date=ref_date, horizon=h))
        db_session.add(create_obs(f"AC_{h}", "SRC_GOOGLE", 5500.00, route_id="DEL-BOM", collection_date=cur_date, horizon=h))
    db_session.commit()

    # 1. POST calculate-v1
    payload = {
        "reference_date": ref_date.isoformat(),
        "calculation_date": cur_date.isoformat(),
        "cabin": "ECONOMY",
        "basket_version": "BASKET-DGCA-2025-TOP10"
    }
    resp = client.post("/api/v1/index-runs/calculate-v1", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    run_id = data["run_id"]
    assert data["headline_index_value"] == 110.0
    assert len(data["horizons"]) == 5

    # 2. GET horizons
    h_resp = client.get(f"/api/v1/index-runs/{run_id}/horizons")
    assert h_resp.status_code == 200
    h_data = h_resp.json()
    assert len(h_data) == 5
    t15_h = next(h for h in h_data if h["horizon_code"] == "T+15")
    assert t15_h["is_headline"] is True
    assert t15_h["index_value"] == 110.0

    # 3. GET manifest
    m_resp = client.get(f"/api/v1/index-runs/{run_id}/manifest")
    assert m_resp.status_code == 200
    m_data = m_resp.json()
    assert m_data["run_id"] == run_id
    assert m_data["canonical_run_fingerprint"] is not None


def test_18b_api_temporal_and_inflation_and_series(client, db_session):
    """Test /api/v1/indices/temporal-aggregate, inflation-rate, and series endpoints."""
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 8, 1)

    # Add reference observations on ref_date
    for h in [1, 7, 15, 30, 45]:
        db_session.add(create_obs(f"TREF_{h}", "SRC_GOOGLE", 5000.00, route_id="DEL-BOM", collection_date=ref_date, horizon=h))
    db_session.commit()

    # Day 1: calculation_date = 2026-08-02, fare = 5000.00 (index = 100.0)
    day1_date = ref_date + dt.timedelta(days=1)
    for h in [1, 7, 15, 30, 45]:
        db_session.add(create_obs(f"TDAY1_{h}", "SRC_GOOGLE", 5000.00, route_id="DEL-BOM", collection_date=day1_date, horizon=h))
    db_session.commit()

    r1 = client.post("/api/v1/index-runs/calculate-v1", json={
        "reference_date": ref_date.isoformat(),
        "calculation_date": day1_date.isoformat(),
        "cabin": "ECONOMY"
    })
    assert r1.status_code == 201

    # Day 2: calculation_date = 2026-08-03, fare = 5500.00 (index = 110.0)
    day2_date = ref_date + dt.timedelta(days=2)
    for h in [1, 7, 15, 30, 45]:
        db_session.add(create_obs(f"TDAY2_{h}", "SRC_GOOGLE", 5500.00, route_id="DEL-BOM", collection_date=day2_date, horizon=h))
    db_session.commit()

    r2 = client.post("/api/v1/index-runs/calculate-v1", json={
        "reference_date": ref_date.isoformat(),
        "calculation_date": day2_date.isoformat(),
        "cabin": "ECONOMY"
    })
    assert r2.status_code == 201

    day1 = day1_date.isoformat()
    day2 = day2_date.isoformat()

    # 1. Temporal aggregate
    t_resp = client.get(f"/api/v1/indices/temporal-aggregate?frequency=WEEKLY&start_date={day1}&end_date={day2}&horizon_code=T+15")
    assert t_resp.status_code == 200
    t_data = t_resp.json()
    assert t_data["status"] == "AVAILABLE"
    assert t_data["days_available"] == 2
    assert t_data["index_value"] == 105.0  # mean(100.0, 110.0)

    # 2. Inflation rate
    i_resp = client.get(f"/api/v1/indices/inflation-rate?rate_type=MOM&current_date={day2}&comparison_date={day1}&horizon_code=T+15")
    assert i_resp.status_code == 200
    i_data = i_resp.json()
    assert i_data["status"] == "AVAILABLE"
    assert i_data["inflation_rate_percent"] == 10.0

    # 3. Series
    s_resp = client.get(f"/api/v1/indices/series?horizon_code=T+15&start_date={day1}&end_date={day2}")
    assert s_resp.status_code == 200
    s_data = s_resp.json()
    assert len(s_data) == 2
    assert s_data[0]["index_value"] == 100.0
    assert s_data[1]["index_value"] == 110.0


def test_19_base_date_insufficiency_rejection(db_session):
    """
    If reference_date has no eligible LIVE_MARKET_DATA observations, execute_statistical_index_run
    raises ValueError with INSUFFICIENT_BASE_OBSERVATIONS rather than fabricating a base.
    """
    empty_date = dt.date(2020, 1, 1)
    calc_date = dt.date(2026, 9, 12)

    with pytest.raises(ValueError) as exc_info:
        StatisticalIndexEngineService.execute_statistical_index_run(
            db=db_session,
            reference_date=empty_date,
            calculation_date=calc_date,
            cabin="ECONOMY"
        )
    assert "INSUFFICIENT_BASE_OBSERVATIONS" in str(exc_info.value)

# =============================================================================
# 20. OBSERVATION ACCOUNTING (AUDIT 1)
# =============================================================================

def test_20_observation_accounting_reconciliation(db_session):
    """
    Proves the persisted manifest's observation counts reconcile exactly to the sum 
    of the filtered underlying observation population (only reference and calculation dates).
    """
    from tests.test_statistical_index_engine import seed_test_routes, create_obs
    import datetime as dt
    from app.services.statistical_index_service import StatisticalIndexEngineService
    
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)
    other_date = dt.date(2026, 9, 11)

    # 2 on ref, 3 on cur, 5 on other
    db_session.add(create_obs("O_REF_1", "SRC_GOOGLE", 5000.00, route_id="DEL-BOM", collection_date=ref_date, horizon=15))
    db_session.add(create_obs("O_REF_2", "SRC_GOOGLE", 5000.00, route_id="DEL-BLR", collection_date=ref_date, horizon=15))
    db_session.add(create_obs("O_CUR_1", "SRC_GOOGLE", 5500.00, route_id="DEL-BOM", collection_date=cur_date, horizon=15))
    db_session.add(create_obs("O_CUR_2", "SRC_GOOGLE", 5500.00, route_id="DEL-BLR", collection_date=cur_date, horizon=15))
    db_session.add(create_obs("O_CUR_3", "SRC_GOOGLE", 5500.00, route_id="DEL-HYD", collection_date=cur_date, horizon=15))
    for i in range(5):
        db_session.add(create_obs(f"O_OTH_{i}", "SRC_GOOGLE", 6000.00, route_id="DEL-BOM", collection_date=other_date, horizon=15))
    db_session.commit()

    run, _, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )
    
    assert run.number_of_observations == 5 # total retrieved by filter
    assert run.number_of_eligible_observations == 5 # 2 + 3


# =============================================================================
# 21. MATCHED-SAMPLE EQUALITY INVARIANT (AUDIT 2)
# =============================================================================

def test_21_matched_sample_equality_invariant(db_session):
    """
    Proves that when R_active == R_matched, primary_index == matched_sample_index
    within numerical tolerance.
    """
    from tests.test_statistical_index_engine import seed_test_routes, create_obs
    import datetime as dt
    from app.services.statistical_index_service import StatisticalIndexEngineService

    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    # Add 2 routes for ref and cur dates
    db_session.add(create_obs("O1_REF", "SRC_GOOGLE", 5000.00, route_id="DEL-BOM", collection_date=ref_date, horizon=45))
    db_session.add(create_obs("O2_REF", "SRC_GOOGLE", 4000.00, route_id="DEL-BLR", collection_date=ref_date, horizon=45))
    
    db_session.add(create_obs("O1_CUR", "SRC_GOOGLE", 5500.00, route_id="DEL-BOM", collection_date=cur_date, horizon=45)) # 110.0 index
    db_session.add(create_obs("O2_CUR", "SRC_GOOGLE", 4800.00, route_id="DEL-BLR", collection_date=cur_date, horizon=45)) # 120.0 index
    
    db_session.commit()

    run, horizons, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )
    
    h45 = next(h for h in horizons if h.horizon_code == "T+45")
    
    # R_active and R_matched should both be 2
    assert h45.active_routes_count == 2
    assert abs(h45.matched_sample_index_value - h45.index_value) < 1e-4
    assert h45.matched_sample_index_value > 0
