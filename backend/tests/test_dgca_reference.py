import pytest
import sys
from pathlib import Path

# Add repository root to sys.path
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.models.dgca_reference import DGCAReferenceDataset, DGCARawObservation, DGCARouteMonthObservation, DGCAProvenanceRecord
from app.models.route_basket import RouteBasket, RouteBasketMember
from app.models.city_airport_mapping import CityAirportMapping
from app.validation_data.dgca_parser import (
    deduplicate_and_merge_route_month_observations,
    map_city_to_airport,
    parse_numeric_passenger_value,
    make_canonical_route_key
)
from app.validation_data.dgca_validator import DGCAValidator
from app.validation_data.dgca_repository import DGCARepository
from app.services.dgca_basket_service import DGCABasketService
from scripts.seed_dgca_traffic import seed_dgca_reference_data
from scripts.seed_mospi_cpi2024 import seed_mospi_reference_data


def test_seed_dgca_traffic_records_count_and_completeness(db_session):
    """
    Verifies that DGCA seeder populates dataset, 12 months, raw rows, normalized route-months, and top 10 basket.
    """
    seed_dgca_reference_data(db_session)
    repo = DGCARepository(db_session)

    cov = repo.get_coverage("DS-DGCA-TRAFFIC-2025")
    assert cov is not None
    assert cov.publisher == "DGCA"
    assert cov.completeness_status == "COMPLETE"
    assert cov.months_expected == 12
    assert cov.months_available == 12
    assert len(cov.months_missing) == 0


def test_reverse_route_rows_do_not_double_count(db_session):
    """
    Requirement 17 (Critical Fix): Verifies that reverse-direction raw rows (e.g. DEL->BOM and BOM->DEL)
    within the same month are deduplicated into a SINGLE route-month observation and NOT double-counted.
    """
    raw_rows_with_reverse = [
        {"year": 2025, "month": 1, "city1": "NEW DELHI", "city2": "BOMBAY", "pax_to": "100000", "pax_from": "95000"},
        {"year": 2025, "month": 1, "city1": "BOMBAY", "city2": "NEW DELHI", "pax_to": "5000", "pax_from": "4000"},
    ]

    dataset_id = "TEST-DS-DEDUP"
    norm_obs = deduplicate_and_merge_route_month_observations(dataset_id, 2025, 1, raw_rows_with_reverse)

    # Must produce exactly ONE route-month observation for DELHI::MUMBAI
    assert len(norm_obs) == 1
    rec = norm_obs[0]

    assert rec["canonical_route_key"] == "DELHI::MUMBAI"
    assert rec["aggregation_mode"] == "BIDIRECTIONAL_MERGED"

    # Total combined passengers = (100000 + 4000) + (95000 + 5000) = 204000 (NOT double counted)
    assert rec["combined_passengers"] == 204000
    assert rec["passengers_city1_to_city2"] == 104000
    assert rec["passengers_city2_to_city1"] == 100000


def test_city_to_airport_mapping_resolution():
    """
    Verifies that raw DGCA city names map to canonical cities and airport codes explicitly.
    """
    canon_city, apt, metro = map_city_to_airport("NEW DELHI")
    assert canon_city == "DELHI"
    assert apt == "DEL"

    canon_city_bom, apt_bom, metro_bom = map_city_to_airport("BOMBAY")
    assert canon_city_bom == "MUMBAI"
    assert apt_bom == "BOM"


def test_dash_symbol_semantics_and_missing_handling():
    """
    Verifies that raw dash symbol ("-") is stored as NULL / MISSING and NOT converted to 0.
    """
    pax_val, raw_str, reason = parse_numeric_passenger_value("-")
    assert pax_val is None
    assert raw_str == "-"
    assert reason == "SOURCE_SYMBOL_DASH"

    pax_val2, raw_str2, reason2 = parse_numeric_passenger_value("45,120")
    assert pax_val2 == 45120
    assert reason2 == "PARSED_OK"


def test_traffic_shares_sum_to_approximately_one(db_session):
    """
    Requirement 10: Basket weights (dgca_basket_weight) across basket members sum to approximately 1.0.
    """
    seed_dgca_reference_data(db_session)
    repo = DGCARepository(db_session)
    basket = repo.get_route_basket("BASKET-DGCA-2025-TOP10")

    assert basket is not None
    assert basket.basket_size == 10
    assert len(basket.members) == 10

    weights = [m.dgca_basket_weight for m in basket.members]
    total_weight = sum(weights)

    assert abs(total_weight - 1.0) < 1e-4
    assert basket.members[0].rank == 1
    assert basket.members[0].dgca_basket_weight > basket.members[-1].dgca_basket_weight


def test_cpi_weight_never_enters_dgca_traffic_weight_calculation(db_session):
    """
    Requirement 14 & 15: DGCA traffic proxy weight is strictly separated from MoSPI CPI expenditure weight.
    """
    seed_dgca_reference_data(db_session)
    seed_mospi_reference_data(db_session)

    repo = DGCARepository(db_session)
    basket = repo.get_route_basket("BASKET-DGCA-2025-TOP10")

    for member in basket.members:
        assert member.dgca_basket_weight_unit == "weight_within_selected_basket"
        assert member.dgca_route_traffic_share_unit == "share_of_all_eligible_traffic"
        assert not hasattr(member, "cpi_weight")
        assert not hasattr(member, "cpi_weight_value")


def test_all_20_validation_rules_on_seeded_data(db_session):
    """
    Requirement 20: Validates dataset and basket using DGCAValidator enforcing all 20 rules.
    """
    seed_dgca_reference_data(db_session)
    repo = DGCARepository(db_session)

    ds = repo.get_dataset("DS-DGCA-TRAFFIC-2025")
    raw_rows = db_session.query(DGCARawObservation).filter(DGCARawObservation.dataset_id == "DS-DGCA-TRAFFIC-2025").all()
    norm_obs = db_session.query(DGCARouteMonthObservation).filter(DGCARouteMonthObservation.dataset_id == "DS-DGCA-TRAFFIC-2025").all()

    ds_meta = {
        "publisher": ds.publisher,
        "canonical_dataset_sha256": ds.canonical_dataset_sha256,
        "months_expected": ds.months_expected,
        "months_available": ds.months_available,
        "completeness_status": ds.completeness_status,
    }
    raw_dicts = [{"year": r.year, "month": r.month} for r in raw_rows]
    norm_dicts = [
        {
            "canonical_route_key": o.canonical_route_key,
            "passengers_city1_to_city2": o.passengers_city1_to_city2,
            "passengers_city2_to_city1": o.passengers_city2_to_city1,
            "combined_passengers": o.combined_passengers,
            "reference_period": o.reference_period,
        }
        for o in norm_obs
    ]

    is_ds_valid, ds_errors = DGCAValidator.validate_dataset_and_observations(ds_meta, raw_dicts, norm_dicts)
    assert is_ds_valid is True, f"Dataset validation failed: {ds_errors}"

    basket = repo.get_route_basket("BASKET-DGCA-2025-TOP10")
    b_meta = {"basket_size": basket.basket_size}
    b_members = [
        {
            "rank": m.rank,
            "route_id": m.route_id,
            "canonical_route_key": m.canonical_route_key,
            "dgca_route_traffic_share": m.dgca_route_traffic_share,
            "dgca_basket_weight": m.dgca_basket_weight,
            "dgca_route_traffic_share_unit": m.dgca_route_traffic_share_unit,
            "dgca_basket_weight_unit": m.dgca_basket_weight_unit,
        }
        for m in basket.members
    ]

    is_bk_valid, bk_errors = DGCAValidator.validate_route_basket(b_meta, b_members)
    assert is_bk_valid is True, f"Basket validation failed: {bk_errors}"


def test_dgca_api_endpoints(db_session, client):
    """
    Verifies HTTP GET endpoints for DGCA reference data (/coverage, /basket/{id}, /provenance/{id}, /traffic).
    """
    seed_dgca_reference_data(db_session)

    # 1. /coverage
    res_cov = client.get("/api/v1/reference/dgca/coverage")
    assert res_cov.status_code == 200
    cov_data = res_cov.json()
    assert cov_data["publisher"] == "DGCA"
    assert cov_data["completeness_status"] == "COMPLETE"

    # 2. /basket/{id}
    res_bk = client.get("/api/v1/reference/dgca/basket/BASKET-DGCA-2025-TOP10")
    assert res_bk.status_code == 200
    bk_data = res_bk.json()
    assert bk_data["basket_size"] == 10
    assert len(bk_data["members"]) == 10
    assert "dgca_route_traffic_share" in bk_data["members"][0]
    assert "dgca_basket_weight" in bk_data["members"][0]

    # 3. /provenance/{id}
    res_prov = client.get("/api/v1/reference/dgca/provenance/DS-DGCA-TRAFFIC-2025")
    assert res_prov.status_code == 200
    prov_data = res_prov.json()
    assert prov_data["publisher"] == "DGCA"

    # 4. /traffic
    res_tr = client.get("/api/v1/reference/dgca/traffic?city=DELHI&limit=5")
    assert res_tr.status_code == 200
    tr_data = res_tr.json()
    assert len(tr_data) > 0


def test_adversarial_publisher_rejection():
    """Adversarial Test 1: Validator rejects datasets where publisher is not DGCA."""
    ds_meta = {"publisher": "INVALID_PUB", "canonical_dataset_sha256": "abc", "months_expected": 12, "months_available": 12, "completeness_status": "COMPLETE"}
    is_valid, errors = DGCAValidator.validate_dataset_and_observations(ds_meta, [], [])
    assert is_valid is False
    assert any("Publisher must be 'DGCA'" in e for e in errors)


def test_adversarial_incomplete_source_period_rejection():
    """Adversarial Test 2: Validator rejects datasets illegally marked COMPLETE when months are missing."""
    ds_meta = {"publisher": "DGCA", "canonical_dataset_sha256": "abc", "months_expected": 12, "months_available": 10, "completeness_status": "COMPLETE"}
    is_valid, errors = DGCAValidator.validate_dataset_and_observations(ds_meta, [], [])
    assert is_valid is False
    assert any("illegally marked 'COMPLETE'" in e for e in errors)


def test_adversarial_negative_passenger_value_rejection():
    """Adversarial Test 3: Validator rejects negative passenger counts."""
    ds_meta = {"publisher": "DGCA", "canonical_dataset_sha256": "abc", "months_expected": 12, "months_available": 12, "completeness_status": "COMPLETE"}
    norm_obs = [{
        "canonical_route_key": "DELHI::MUMBAI",
        "passengers_city1_to_city2": -500,
        "passengers_city2_to_city1": 1000,
        "combined_passengers": 500,
        "reference_period": "2025-01"
    }]
    is_valid, errors = DGCAValidator.validate_dataset_and_observations(ds_meta, [], norm_obs)
    assert is_valid is False
    assert any("Negative passenger count" in e for e in errors)


def test_adversarial_combined_passenger_mismatch_rejection():
    """Adversarial Test 4: Validator rejects incorrect combined passenger sums."""
    ds_meta = {"publisher": "DGCA", "canonical_dataset_sha256": "abc", "months_expected": 12, "months_available": 12, "completeness_status": "COMPLETE"}
    norm_obs = [{
        "canonical_route_key": "DELHI::MUMBAI",
        "passengers_city1_to_city2": 500,
        "passengers_city2_to_city1": 1000,
        "combined_passengers": 9999, # False combined sum!
        "reference_period": "2025-01"
    }]
    is_valid, errors = DGCAValidator.validate_dataset_and_observations(ds_meta, [], norm_obs)
    assert is_valid is False
    assert any("Combined passengers mismatch" in e for e in errors)


def test_adversarial_duplicate_route_month_deduplication_failure():
    """Adversarial Test 5: Validator rejects duplicate normalized route-month entries if deduplication failed."""
    ds_meta = {"publisher": "DGCA", "canonical_dataset_sha256": "abc", "months_expected": 12, "months_available": 12, "completeness_status": "COMPLETE"}
    norm_obs = [
        {"canonical_route_key": "DELHI::MUMBAI", "passengers_city1_to_city2": 500, "passengers_city2_to_city1": 1000, "combined_passengers": 1500, "reference_period": "2025-01"},
        {"canonical_route_key": "DELHI::MUMBAI", "passengers_city1_to_city2": 500, "passengers_city2_to_city1": 1000, "combined_passengers": 1500, "reference_period": "2025-01"}
    ]
    is_valid, errors = DGCAValidator.validate_dataset_and_observations(ds_meta, [], norm_obs)
    assert is_valid is False
    assert any("Duplicate route-month observation key" in e for e in errors)


def test_adversarial_basket_traffic_share_sum_rejection():
    """Adversarial Test 6: Validator rejects route baskets where basket weights do not sum to ~1.0."""
    b_meta = {"basket_size": 2}
    members = [
        {"rank": 1, "route_id": "DEL-BOM", "canonical_route_key": "DELHI::MUMBAI", "dgca_route_traffic_share": 0.3, "dgca_basket_weight": 0.6, "dgca_route_traffic_share_unit": "share_of_all_eligible_traffic", "dgca_basket_weight_unit": "weight_within_selected_basket"},
        {"rank": 2, "route_id": "DEL-BLR", "canonical_route_key": "BENGALURU::DELHI", "dgca_route_traffic_share": 0.1, "dgca_basket_weight": 0.2, "dgca_route_traffic_share_unit": "share_of_all_eligible_traffic", "dgca_basket_weight_unit": "weight_within_selected_basket"},
    ]
    is_valid, errors = DGCAValidator.validate_route_basket(b_meta, members)
    assert is_valid is False
    assert any("Basket weights sum to" in e for e in errors)


def test_adversarial_basket_duplicate_rank_rejection():
    """Adversarial Test 7: Validator rejects route baskets with duplicate ranks."""
    b_meta = {"basket_size": 2}
    members = [
        {"rank": 1, "route_id": "DEL-BOM", "canonical_route_key": "DELHI::MUMBAI", "dgca_route_traffic_share": 0.3, "dgca_basket_weight": 0.5, "dgca_route_traffic_share_unit": "share_of_all_eligible_traffic", "dgca_basket_weight_unit": "weight_within_selected_basket"},
        {"rank": 1, "route_id": "DEL-BLR", "canonical_route_key": "BENGALURU::DELHI", "dgca_route_traffic_share": 0.3, "dgca_basket_weight": 0.5, "dgca_route_traffic_share_unit": "share_of_all_eligible_traffic", "dgca_basket_weight_unit": "weight_within_selected_basket"},
    ]
    is_valid, errors = DGCAValidator.validate_route_basket(b_meta, members)
    assert is_valid is False
    assert any("Duplicate ranks found" in e for e in errors)


def test_adversarial_basket_cpi_weight_injection_rejection():
    """Adversarial Test 8: Validator rejects route baskets where CPI weight field is illegally injected."""
    b_meta = {"basket_size": 1}
    members = [
        {"rank": 1, "route_id": "DEL-BOM", "canonical_route_key": "DELHI::MUMBAI", "dgca_route_traffic_share": 0.3, "dgca_basket_weight": 1.0, "dgca_route_traffic_share_unit": "share_of_all_eligible_traffic", "dgca_basket_weight_unit": "weight_within_selected_basket", "cpi_weight": 0.03},
    ]
    is_valid, errors = DGCAValidator.validate_route_basket(b_meta, members)
    assert is_valid is False
    assert any("CPI weight field illegally injected" in e for e in errors)


def test_adversarial_nondeterministic_ranking_rejection():
    """Adversarial Test 9: Validator rejects route baskets that are not sorted in strict rank order."""
    b_meta = {"basket_size": 2}
    members = [
        {"rank": 2, "route_id": "DEL-BLR", "canonical_route_key": "BENGALURU::DELHI", "dgca_route_traffic_share": 0.2, "dgca_basket_weight": 0.4, "dgca_route_traffic_share_unit": "share_of_all_eligible_traffic", "dgca_basket_weight_unit": "weight_within_selected_basket"},
        {"rank": 1, "route_id": "DEL-BOM", "canonical_route_key": "DELHI::MUMBAI", "dgca_route_traffic_share": 0.3, "dgca_basket_weight": 0.6, "dgca_route_traffic_share_unit": "share_of_all_eligible_traffic", "dgca_basket_weight_unit": "weight_within_selected_basket"},
    ]
    is_valid, errors = DGCAValidator.validate_route_basket(b_meta, members)
    assert is_valid is False
    assert any("members are not sorted in strict rank order" in e for e in errors)


# ==============================================================================
# SPECIFIC REGRESSION TESTS FOR MILESTONE 3B CORRECTION PASS
# ==============================================================================

def test_dgca_dual_denominators_exposed(db_session):
    """Regression Test 1: Verify dgca_route_traffic_share and dgca_basket_weight are both exposed."""
    seed_dgca_reference_data(db_session)
    repo = DGCARepository(db_session)
    basket = repo.get_route_basket("BASKET-DGCA-2025-TOP10")

    assert basket is not None
    for member in basket.members:
        assert hasattr(member, "dgca_route_traffic_share")
        assert hasattr(member, "dgca_basket_weight")
        assert member.dgca_route_traffic_share > 0.0
        assert member.dgca_basket_weight > 0.0
        # Basket weight must be strictly greater than national route share for top-N basket
        assert member.dgca_basket_weight > member.dgca_route_traffic_share


def test_dgca_basket_weights_sum_to_one(db_session):
    """Regression Test 2: Verify dgca_basket_weight sums to 1.0 (100%)."""
    seed_dgca_reference_data(db_session)
    repo = DGCARepository(db_session)
    basket = repo.get_route_basket("BASKET-DGCA-2025-TOP10")

    basket_weights = [m.dgca_basket_weight for m in basket.members]
    total_basket_weight = sum(basket_weights)
    assert abs(total_basket_weight - 1.0) < 1e-5


def test_dgca_national_shares_sum_less_than_one(db_session):
    """Regression Test 3: Verify dgca_route_traffic_share sums to strictly less than 1.0 (national total)."""
    seed_dgca_reference_data(db_session)
    repo = DGCARepository(db_session)
    basket = repo.get_route_basket("BASKET-DGCA-2025-TOP10")

    national_shares = [m.dgca_route_traffic_share for m in basket.members]
    total_national_share = sum(national_shares)

    # National traffic share across Top 10 routes should be ~91.76% (< 1.0)
    assert total_national_share < 1.0
    assert 0.80 < total_national_share < 0.95


def test_dgca_reverse_direction_deduplication_exact_counts(db_session):
    """Regression Test 4: Verify exact passenger counts after Month 1 reverse merge (142500+400=142900, 141200+500=141700, combined=284600)."""
    seed_dgca_reference_data(db_session)
    repo = DGCARepository(db_session)
    obs_list = repo.filter_traffic_observations(dataset_id="DS-DGCA-TRAFFIC-2025", year=2025, month=1, route_key="DELHI::MUMBAI")

    assert len(obs_list) == 1
    obs = obs_list[0]

    assert obs.passengers_city1_to_city2 == 142900
    assert obs.passengers_city2_to_city1 == 141700
    assert obs.combined_passengers == 284600


def test_dgca_record_count_reconciliation_equation(db_session):
    """Regression Test 5: Verify mathematical record audit reconciliation equation (146 raw - 1 reverse merge = 145 normalized)."""
    seed_dgca_reference_data(db_session)
    raw_count = db_session.query(DGCARawObservation).filter(DGCARawObservation.dataset_id == "DS-DGCA-TRAFFIC-2025").count()
    norm_count = db_session.query(DGCARouteMonthObservation).filter(DGCARouteMonthObservation.dataset_id == "DS-DGCA-TRAFFIC-2025").count()

    headers = 0
    invalids = 0
    duplicates = 0
    reverse_pairs_merged = 1

    assert raw_count == 146
    assert norm_count == 145
    assert raw_count - headers - invalids - duplicates - reverse_pairs_merged == norm_count


def test_dgca_provenance_actual_filenames(db_session):
    """Regression Test 6: Verify raw observations store actual publication filenames and URLs."""
    seed_dgca_reference_data(db_session)
    raw_m1 = db_session.query(DGCARawObservation).filter(DGCARawObservation.dataset_id == "DS-DGCA-TRAFFIC-2025", DGCARawObservation.month == 1).first()

    assert raw_m1 is not None
    assert raw_m1.source_filename == "DOM CITYPAIR DATA, JANUARY 2025.xlsx"
    assert "DOM%20CITYPAIR%20DATA%2C%20JANUARY%202025.xlsx" in raw_m1.source_url


def test_dgca_exact_numerical_reconciliation_integrity(db_session):
    """
    Final Mandatory Numerical Reconciliation Test:
    Asserts:
    1. sum(top10_passengers) == basket_passengers_total (19,773,500)
    2. sum(basket_weights) == 1 within numerical tolerance (1.000000)
    3. sum(route_traffic_share for top10) < 1 (~0.914783)
    4. every displayed percentage equals its underlying formula within tolerance
    """
    seed_dgca_reference_data(db_session)
    repo = DGCARepository(db_session)
    basket = repo.get_route_basket("BASKET-DGCA-2025-TOP10")

    assert basket is not None
    assert basket.basket_size == 10

    top10_passengers = [m.period_passengers for m in basket.members]
    basket_weights = [m.dgca_basket_weight for m in basket.members]
    national_shares = [m.dgca_route_traffic_share for m in basket.members]

    # Assertion 1: sum(top10_passengers) == basket_passengers_total
    assert sum(top10_passengers) == basket.total_period_passengers
    assert basket.total_period_passengers == 19773500

    # Assertion 2: sum(basket_weights) == 1 within numerical tolerance
    assert abs(sum(basket_weights) - 1.0) < 1e-5

    # Assertion 3: sum(route_traffic_share for top10) < 1
    assert sum(national_shares) < 1.0
    assert abs(sum(national_shares) - (19773500 / basket.total_all_eligible_routes_passengers)) < 1e-6

    # Assertion 4: every displayed percentage equals its underlying formula within tolerance
    for m in basket.members:
        expected_weight = m.period_passengers / basket.total_period_passengers
        expected_share = m.period_passengers / basket.total_all_eligible_routes_passengers

        assert abs(m.dgca_basket_weight - expected_weight) < 1e-6
        assert abs(m.dgca_route_traffic_share - expected_share) < 1e-6


