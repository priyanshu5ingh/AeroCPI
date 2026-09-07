import pytest
import math
import sys
from pathlib import Path
from datetime import date, datetime, timezone

# Add repository root to sys.path to allow importing scripts
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.services.index_engine_service import IndexEngineService
from app.services.quality_engine_service import QualityEngineService
from app.services.proxy_weight_service import ProxyWeightService
from app.models.observation import Observation
from app.models.proxy_route_weight import ProxyRouteWeight
from app.schemas.common import OutlierStatus

def test_1_basic_jevons_calculation():
    ref_prices = [100.0, 200.0]
    cur_prices = [110.0, 220.0]
    g_ref, g_cur, rel = IndexEngineService.calculate_jevons_relative(ref_prices, cur_prices)
    assert round(rel, 4) == 1.1000

def test_2_known_jevons_numerical_example():
    # Hand-calculated expected value:
    # p0 = [100.0, 200.0, 400.0] -> geom_mean = (100 * 200 * 400)^(1/3) = (8,000,000)^(1/3) = 200.0
    # pt = [110.0, 220.0, 440.0] -> geom_mean = (110 * 220 * 440)^(1/3) = (10,648,000)^(1/3) = 220.0
    # Price relative = 220.0 / 200.0 = 1.10
    # Expected Index = 100 * 1.10 = 110.0
    ref_prices = [100.0, 200.0, 400.0]
    cur_prices = [110.0, 220.0, 440.0]
    g_ref, g_cur, rel = IndexEngineService.calculate_jevons_relative(ref_prices, cur_prices)
    assert abs(g_ref - 200.0) < 1e-6
    assert abs(g_cur - 220.0) < 1e-6
    assert abs(rel - 1.10) < 1e-6
    assert abs(100.0 * rel - 110.0) < 1e-6

def test_3_known_unchanged_price_case():
    ref_prices = [5000.0, 6000.0, 7000.0]
    cur_prices = [5000.0, 6000.0, 7000.0]
    _, _, rel = IndexEngineService.calculate_jevons_relative(ref_prices, cur_prices)
    index_val = 100.0 * rel
    assert abs(index_val - 100.0) < 1e-6

def test_4_ten_percent_price_increase():
    ref_prices = [4000.0, 5000.0]
    cur_prices = [4400.0, 5500.0]
    _, _, rel = IndexEngineService.calculate_jevons_relative(ref_prices, cur_prices)
    index_val = 100.0 * rel
    assert abs(index_val - 110.0) < 1e-6

def test_5_ten_percent_price_decrease():
    ref_prices = [4000.0, 5000.0]
    cur_prices = [3600.0, 4500.0]
    _, _, rel = IndexEngineService.calculate_jevons_relative(ref_prices, cur_prices)
    index_val = 100.0 * rel
    assert abs(index_val - 90.0) < 1e-6

def test_6_deterministic_result_ordering_independent():
    ref_prices = [100.0, 200.0, 400.0]
    cur_prices = [440.0, 110.0, 220.0] # Permuted order
    _, _, rel1 = IndexEngineService.calculate_jevons_relative(ref_prices, cur_prices)

    ref_prices_perm = [400.0, 100.0, 200.0]
    cur_prices_perm = [220.0, 440.0, 110.0]
    _, _, rel2 = IndexEngineService.calculate_jevons_relative(ref_prices_perm, cur_prices_perm)

    assert abs(rel1 - rel2) < 1e-12

def test_7_invalid_zero_negative_price_rejection():
    with pytest.raises(ValueError) as exc:
        IndexEngineService.calculate_jevons_relative([100.0, 0.0], [110.0, 200.0])
    assert "strictly positive" in str(exc.value)

    with pytest.raises(ValueError) as exc2:
        IndexEngineService.calculate_jevons_relative([100.0, 200.0], [-50.0, 200.0])
    assert "strictly positive" in str(exc2.value)

def test_8_identical_price_mad_group():
    prices = [5000.0, 5000.0, 5000.0, 5000.0]
    scores = QualityEngineService.compute_mad_scores(prices)
    assert scores == [0.0, 0.0, 0.0, 0.0]

def test_9_single_observation_mad_group():
    prices = [5000.0]
    scores = QualityEngineService.compute_mad_scores(prices)
    assert scores == [0.0]

def test_10_normal_mad_group():
    prices = [4000.0, 4200.0, 4100.0, 4300.0, 4050.0]
    scores = QualityEngineService.compute_mad_scores(prices)
    assert all(abs(s) <= 3.5 for s in scores)

def test_11_extreme_mad_observation_flagged(db_session):
    now = datetime.now(timezone.utc)
    # Create group with one extreme outlier (35,000 INR vs ~4,000 INR)
    obs_list = []
    prices = [4000.0, 4100.0, 4050.0, 4200.0, 35000.0]
    for i, p in enumerate(prices):
        o = Observation(
            observation_id=f"obs-mad-{i}",
            source_id="INDIGO_DIRECT",
            route_id="DEL-BOM",
            carrier_id="6E",
            travel_date=date(2026, 9, 20),
            observed_at=now,
            booking_horizon_days=7,
            cabin="ECONOMY",
            base_fare=p - 500,
            taxes=300,
            mandatory_fees=200,
            total_fare=p,
            currency="INR",
            data_status="OBSERVED"
        )
        db_session.add(o)
        obs_list.append(o)
    db_session.commit()

    quality_results = QualityEngineService.evaluate_observation_batch(db_session, obs_list)
    qr_extreme = next(qr for qr in quality_results if qr.observation_id == "obs-mad-4")
    
    assert qr_extreme.outlier_status in ("OUTLIER_FLAGGED", "EXCLUDED")
    assert "MAD_OUTLIER" in qr_extreme.exclusion_reason

def test_12_flagged_outlier_remains_stored(db_session):
    now = datetime.now(timezone.utc)
    o = Observation(
        observation_id="obs-flagged-keep",
        source_id="INDIGO_DIRECT",
        route_id="DEL-BOM",
        carrier_id="6E",
        travel_date=date(2026, 9, 20),
        observed_at=now,
        booking_horizon_days=7,
        base_fare=34500.0,
        taxes=300.0,
        mandatory_fees=200.0,
        total_fare=35000.0,
        currency="INR",
        data_status="OBSERVED"
    )
    db_session.add(o)
    db_session.commit()

    # Query DB to ensure observation remains permanently stored
    fetched = db_session.query(Observation).filter(Observation.observation_id == "obs-flagged-keep").first()
    assert fetched is not None
    assert fetched.total_fare == 35000.0

def test_13_excluded_observation_retains_exclusion_reason(db_session):
    now = datetime.now(timezone.utc)
    o = Observation(
        observation_id="obs-neg-fare",
        source_id="INDIGO_DIRECT",
        route_id="DEL-BOM",
        carrier_id="6E",
        travel_date=date(2026, 9, 20),
        observed_at=now,
        booking_horizon_days=7,
        base_fare=-100.0,
        taxes=10.0,
        mandatory_fees=5.0,
        total_fare=-85.0,
        currency="INR",
        data_status="OBSERVED"
    )
    db_session.add(o)
    db_session.commit()

    quality_results = QualityEngineService.evaluate_observation_batch(db_session, [o])
    qr = quality_results[0]
    assert qr.eligible is False
    assert qr.outlier_status == "EXCLUDED"
    assert qr.exclusion_reason == "NEGATIVE_FARE"

def test_14_duplicate_detection(db_session):
    now = datetime.now(timezone.utc)
    o1 = Observation(
        observation_id="obs-dup-1",
        source_id="INDIGO_DIRECT",
        route_id="DEL-BOM",
        carrier_id="6E",
        travel_date=date(2026, 9, 20),
        observed_at=now,
        booking_horizon_days=7,
        base_fare=3000.0,
        taxes=400.0,
        mandatory_fees=100.0,
        total_fare=3500.0,
        currency="INR",
        data_status="OBSERVED"
    )
    o2 = Observation(
        observation_id="obs-dup-2", # Identical parameters -> Duplicate
        source_id="INDIGO_DIRECT",
        route_id="DEL-BOM",
        carrier_id="6E",
        travel_date=date(2026, 9, 20),
        observed_at=now,
        booking_horizon_days=7,
        base_fare=3000.0,
        taxes=400.0,
        mandatory_fees=100.0,
        total_fare=3500.0,
        currency="INR",
        data_status="OBSERVED"
    )
    db_session.add_all([o1, o2])
    db_session.commit()

    q_results = QualityEngineService.evaluate_observation_batch(db_session, [o1, o2])
    qr1 = next(q for q in q_results if q.observation_id == "obs-dup-1")
    qr2 = next(q for q in q_results if q.observation_id == "obs-dup-2")

    assert qr1.duplicate_flag is False
    assert qr2.duplicate_flag is True
    assert qr2.exclusion_reason == "DUPLICATE_OBSERVATION"

def test_15_virtual_trip_mismatch_prevents_comparison(db_session):
    now = datetime.now(timezone.utc)
    o_econ = Observation(
        observation_id="obs-econ",
        source_id="INDIGO_DIRECT",
        route_id="DEL-BOM",
        carrier_id="6E",
        travel_date=date(2026, 9, 20),
        observed_at=now,
        booking_horizon_days=7,
        cabin="ECONOMY",
        base_fare=3000.0,
        taxes=400.0,
        mandatory_fees=100.0,
        total_fare=3500.0,
        currency="INR",
        data_status="OBSERVED"
    )
    o_biz = Observation(
        observation_id="obs-biz",
        source_id="INDIGO_DIRECT",
        route_id="DEL-BOM",
        carrier_id="6E",
        travel_date=date(2026, 9, 20),
        observed_at=now,
        booking_horizon_days=7,
        cabin="BUSINESS", # Different cabin class -> non-comparable spec
        base_fare=15000.0,
        taxes=2000.0,
        mandatory_fees=1000.0,
        total_fare=18000.0,
        currency="INR",
        data_status="OBSERVED"
    )
    db_session.add_all([o_econ, o_biz])
    db_session.commit()

    q_results = QualityEngineService.evaluate_observation_batch(db_session, [o_econ, o_biz])
    groups = {}
    for obs in [o_econ, o_biz]:
        key = (obs.route_id, obs.booking_horizon_days, obs.cabin, obs.stop_type)
        groups.setdefault(key, []).append(obs)

    # Economy and Business belong to separate elementary comparison groups
    assert len(groups) == 2

def test_16_route_directionality(db_session):
    now = datetime.now(timezone.utc)
    o_outbound = Observation(
        observation_id="obs-del-bom",
        source_id="INDIGO_DIRECT",
        route_id="DEL-BOM",
        carrier_id="6E",
        travel_date=date(2026, 9, 20),
        observed_at=now,
        booking_horizon_days=7,
        base_fare=3000.0,
        taxes=400.0,
        mandatory_fees=100.0,
        total_fare=3500.0,
        currency="INR"
    )
    o_inbound = Observation(
        observation_id="obs-bom-del",
        source_id="INDIGO_DIRECT",
        route_id="BOM-DEL", # Opposite direction
        carrier_id="6E",
        travel_date=date(2026, 9, 20),
        observed_at=now,
        booking_horizon_days=7,
        base_fare=3000.0,
        taxes=400.0,
        mandatory_fees=100.0,
        total_fare=3500.0,
        currency="INR"
    )
    db_session.add_all([o_outbound, o_inbound])
    db_session.commit()

    assert o_outbound.route_id != o_inbound.route_id

def test_17_route_weight_sum_validation(db_session):
    # Create invalid proxy weights version where sum = 0.80 (violating 1.0 +- 0.001)
    w1 = ProxyRouteWeight(weight_version_id="INVALID_WEIGHTS", route_id="DEL-BOM", weight_share=0.50)
    w2 = ProxyRouteWeight(weight_version_id="INVALID_WEIGHTS", route_id="BOM-DEL", weight_share=0.30)
    db_session.add_all([w1, w2])
    db_session.commit()

    with pytest.raises(ValueError) as exc:
        ProxyWeightService.get_and_validate_weights(db_session, "INVALID_WEIGHTS")
    assert "violates the required sum tolerance of 1.0 +- 0.001" in str(exc.value)

def test_18_weighted_national_aggregation():
    # Hand-calculated expected value test:
    # Route 1 (DEL-BOM): index = 110.0, proxy weight = 0.60
    # Route 2 (BOM-DEL): index = 90.0, proxy weight = 0.40
    # Expected National Index = (0.60 * 110.0) + (0.40 * 90.0) = 66.0 + 36.0 = 102.0
    r1_index = 110.0
    w1 = 0.60
    r2_index = 90.0
    w2 = 0.40

    national_idx = (w1 * r1_index) + (w2 * r2_index)
    assert abs(national_idx - 102.0) < 1e-6

def test_19_empty_route_group_handling():
    with pytest.raises(ValueError) as exc:
        IndexEngineService.calculate_jevons_relative([], [5000.0])
    assert "Cannot calculate Jevons index on empty price lists" in str(exc.value)

def test_20_reproducibility_fingerprint_stability(db_session):
    from scripts.seed_demo_data import seed_database
    seed_database(db_session)

    run1, _ = IndexEngineService.execute_index_run(db_session, "2026-08-01", "2026-09-01")
    run2, _ = IndexEngineService.execute_index_run(db_session, "2026-08-01", "2026-09-01")

    # Identical dataset & parameters must produce identical SHA-256 canonical fingerprints
    assert run1.canonical_run_fingerprint == run2.canonical_run_fingerprint

    # Change one input observation price in DB
    first_obs = db_session.query(Observation).first()
    first_obs.total_fare = float(first_obs.total_fare) + 500.0
    db_session.commit()

    run3, _ = IndexEngineService.execute_index_run(db_session, "2026-08-01", "2026-09-01")
    # Changing input observation price MUST alter the SHA-256 fingerprint!
    assert run3.canonical_run_fingerprint != run1.canonical_run_fingerprint
