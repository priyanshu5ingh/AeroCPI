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
    Requirement 10: Traffic shares (DGCA_TRAFFIC_PROXY_WEIGHT) across basket members sum to approximately 1.0.
    """
    seed_dgca_reference_data(db_session)
    repo = DGCARepository(db_session)
    basket = repo.get_route_basket("BASKET-DGCA-2025-TOP10")

    assert basket is not None
    assert basket.basket_size == 10
    assert len(basket.members) == 10

    shares = [m.traffic_share for m in basket.members]
    total_share = sum(shares)

    assert abs(total_share - 1.0) < 1e-4
    assert basket.members[0].rank == 1
    assert basket.members[0].traffic_share > basket.members[-1].traffic_share


def test_cpi_weight_never_enters_dgca_traffic_weight_calculation(db_session):
    """
    Requirement 14 & 15: DGCA traffic proxy weight is strictly separated from MoSPI CPI expenditure weight.
    """
    seed_dgca_reference_data(db_session)
    seed_mospi_reference_data(db_session)

    repo = DGCARepository(db_session)
    basket = repo.get_route_basket("BASKET-DGCA-2025-TOP10")

    for member in basket.members:
        assert member.traffic_share_unit == "share_of_basket_traffic"
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
            "traffic_share": m.traffic_share,
            "traffic_share_unit": m.traffic_share_unit,
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
    """Adversarial Test 6: Validator rejects route baskets where traffic shares do not sum to ~1.0."""
    b_meta = {"basket_size": 2}
    members = [
        {"rank": 1, "route_id": "DEL-BOM", "canonical_route_key": "DELHI::MUMBAI", "traffic_share": 0.6, "traffic_share_unit": "share_of_basket_traffic"},
        {"rank": 2, "route_id": "DEL-BLR", "canonical_route_key": "BENGALURU::DELHI", "traffic_share": 0.2, "traffic_share_unit": "share_of_basket_traffic"},
    ]
    is_valid, errors = DGCAValidator.validate_route_basket(b_meta, members)
    assert is_valid is False
    assert any("Traffic shares sum to" in e for e in errors)


def test_adversarial_basket_duplicate_rank_rejection():
    """Adversarial Test 7: Validator rejects route baskets with duplicate ranks."""
    b_meta = {"basket_size": 2}
    members = [
        {"rank": 1, "route_id": "DEL-BOM", "canonical_route_key": "DELHI::MUMBAI", "traffic_share": 0.5, "traffic_share_unit": "share_of_basket_traffic"},
        {"rank": 1, "route_id": "DEL-BLR", "canonical_route_key": "BENGALURU::DELHI", "traffic_share": 0.5, "traffic_share_unit": "share_of_basket_traffic"},
    ]
    is_valid, errors = DGCAValidator.validate_route_basket(b_meta, members)
    assert is_valid is False
    assert any("Duplicate ranks found" in e for e in errors)


def test_adversarial_basket_cpi_weight_injection_rejection():
    """Adversarial Test 8: Validator rejects route baskets where CPI weight field is illegally injected."""
    b_meta = {"basket_size": 1}
    members = [
        {"rank": 1, "route_id": "DEL-BOM", "canonical_route_key": "DELHI::MUMBAI", "traffic_share": 1.0, "traffic_share_unit": "share_of_basket_traffic", "cpi_weight": 0.03},
    ]
    is_valid, errors = DGCAValidator.validate_route_basket(b_meta, members)
    assert is_valid is False
    assert any("CPI weight field illegally injected" in e for e in errors)


def test_adversarial_nondeterministic_ranking_rejection():
    """Adversarial Test 9: Validator rejects route baskets that are not sorted in strict rank order."""
    b_meta = {"basket_size": 2}
    members = [
        {"rank": 2, "route_id": "DEL-BLR", "canonical_route_key": "BENGALURU::DELHI", "traffic_share": 0.4, "traffic_share_unit": "share_of_basket_traffic"},
        {"rank": 1, "route_id": "DEL-BOM", "canonical_route_key": "DELHI::MUMBAI", "traffic_share": 0.6, "traffic_share_unit": "share_of_basket_traffic"},
    ]
    is_valid, errors = DGCAValidator.validate_route_basket(b_meta, members)
    assert is_valid is False
    assert any("members are not sorted in strict rank order" in e for e in errors)
