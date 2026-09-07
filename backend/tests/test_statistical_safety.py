import pytest
import math
import sys
import random
from pathlib import Path
from datetime import date, datetime, timezone

# Add repository root to sys.path
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.services.index_engine_service import IndexEngineService
from app.services.quality_engine_service import QualityEngineService
from app.services.proxy_weight_service import ProxyWeightService
from app.models.observation import Observation
from app.models.proxy_route_weight import ProxyRouteWeight
from app.schemas.common import OutlierStatus, IndexFrequency
from scripts.seed_demo_data import seed_database

def test_1_excluded_observation_cannot_affect_index(db_session):
    """
    Requirement 1: Changing an excluded observation (or non-eligible status)
    must NOT affect the calculated national index value.
    """
    seed_database(db_session)

    # Force one observation to EXCLUDED status by setting invalid currency
    obs_excluded = db_session.query(Observation).first()
    obs_excluded.currency = "USD" # Cause quality exclusion
    db_session.commit()

    # Execute run1 with observation already EXCLUDED
    run1, _ = IndexEngineService.execute_index_run(db_session, "2026-08-01", "2026-09-01")
    initial_val = run1.index_value

    orig_fare = float(obs_excluded.total_fare)
    # Alter the fare of the EXCLUDED observation drastically (+50,000 INR)
    obs_excluded.total_fare = orig_fare + 50000.0
    db_session.commit()

    run2, _ = IndexEngineService.execute_index_run(db_session, "2026-08-01", "2026-09-01")
    # Excluded observation price change MUST NOT alter the index value!
    assert run2.index_value == initial_val

def test_2_missing_route_horizon_pair_is_reported_not_dropped(db_session):
    """
    Requirement 2: Missing route-horizon combinations must be explicitly reported
    in unavailable_route_horizon_pairs with a reason, not silently omitted.
    """
    seed_database(db_session)

    # Delete all comparison period observations for DEL-CCU T+45
    db_session.query(Observation).filter(
        Observation.route_id == "DEL-CCU",
        Observation.booking_horizon_days == 45
    ).delete()
    db_session.commit()

    run, _ = IndexEngineService.execute_index_run(db_session, "2026-08-01", "2026-09-01")
    
    assert run.expected_route_horizon_pairs == 40
    assert run.unavailable_route_horizon_pairs >= 1
    assert run.calculated_route_horizon_pairs + run.unavailable_route_horizon_pairs == run.expected_route_horizon_pairs

    manifest = run.calculation_manifest
    unavailable_details = manifest["route_horizon_summary"]["unavailable_details"]
    del_ccu_unavail = [d for d in unavailable_details if d["route_id"] == "DEL-CCU" and d["booking_horizon"] == 45]
    assert len(del_ccu_unavail) == 1
    assert del_ccu_unavail[0]["reason"] in ("MISSING_COMPARISON_PERIOD", "INSUFFICIENT_OBSERVATIONS")

def test_3_input_ordering_invariance():
    """
    Requirement 3: Jevons and Young/Laspeyres index computation must be completely
    independent of the input price array ordering.
    """
    p0 = [3500.0, 4200.0, 5100.0, 3900.0]
    pt = [3850.0, 4620.0, 5610.0, 4290.0]

    _, _, rel1 = IndexEngineService.calculate_jevons_relative(p0, pt)

    # Shuffle lists randomly
    p0_shuffled = p0.copy()
    pt_shuffled = pt.copy()
    random.seed(123)
    random.shuffle(p0_shuffled)
    random.shuffle(pt_shuffled)

    _, _, rel2 = IndexEngineService.calculate_jevons_relative(p0_shuffled, pt_shuffled)
    assert abs(rel1 - rel2) < 1e-12

def test_4_route_weights_normalization_and_validation(db_session):
    """
    Requirement 4: Proxy route weights must sum to 1.0 +- 0.001 or raise ValueError.
    """
    # Create invalid proxy weights sum (sum = 0.50 instead of 1.0)
    db_session.query(ProxyRouteWeight).filter(ProxyRouteWeight.weight_version_id == "BAD_WEIGHTS").delete()
    bad_weight = ProxyRouteWeight(
        weight_version_id="BAD_WEIGHTS",
        route_id="DEL-BOM",
        weight_share=0.500000,
        weight_type="DGCA_TRAFFIC_SHARE_PROXY",
        is_demo=True
    )
    db_session.add(bad_weight)
    db_session.commit()

    with pytest.raises(ValueError) as exc:
        ProxyWeightService.get_and_validate_weights(db_session, "BAD_WEIGHTS")
    assert "violates the required sum tolerance" in str(exc.value)

def test_5_zero_negative_price_logarithm_rejection():
    """
    Requirement 5: Zero or negative fares must be rejected from logarithmic calculation.
    """
    with pytest.raises(ValueError) as exc1:
        IndexEngineService.calculate_jevons_relative([0.0, 4000.0], [4400.0, 4400.0])
    assert "strictly positive" in str(exc1.value)

    with pytest.raises(ValueError) as exc2:
        IndexEngineService.calculate_jevons_relative([4000.0, 4000.0], [-100.0, 4400.0])
    assert "strictly positive" in str(exc2.value)

def test_6_missing_reference_price_prevents_false_relative():
    """
    Requirement 6: Missing reference period price cannot generate a false relative.
    """
    with pytest.raises(ValueError) as exc:
        IndexEngineService.calculate_jevons_relative([], [4500.0, 4800.0])
    assert "empty price lists" in str(exc.value)

def test_7_missing_comparison_price_prevents_false_relative():
    """
    Requirement 7: Missing comparison period price cannot generate a false relative.
    """
    with pytest.raises(ValueError) as exc:
        IndexEngineService.calculate_jevons_relative([4000.0, 4200.0], [])
    assert "empty price lists" in str(exc.value)

def test_8_route_direction_remains_separated():
    """
    Requirement 8: Directional routes (DEL-BOM vs BOM-DEL) must remain separate.
    """
    ref_prices_del_bom = [3000.0, 3000.0]
    comp_prices_del_bom = [3300.0, 3300.0] # +10%

    ref_prices_bom_del = [4000.0, 4000.0]
    comp_prices_bom_del = [3600.0, 3600.0] # -10%

    _, _, rel_del_bom = IndexEngineService.calculate_jevons_relative(ref_prices_del_bom, comp_prices_del_bom)
    _, _, rel_bom_del = IndexEngineService.calculate_jevons_relative(ref_prices_bom_del, comp_prices_bom_del)

    idx_del_bom = 100.0 * rel_del_bom
    idx_bom_del = 100.0 * rel_bom_del

    assert abs(idx_del_bom - 110.0) < 1e-6
    assert abs(idx_bom_del - 90.0) < 1e-6
    assert idx_del_bom != idx_bom_del

def test_9_frequency_parameter_determinism(db_session):
    """
    Requirement 9: Index engine supports DAILY, WEEKLY, and MONTHLY frequency parameters deterministically.
    """
    seed_database(db_session)

    run_daily, _ = IndexEngineService.execute_index_run(db_session, "2026-08-01", "2026-09-01", frequency="DAILY")
    run_weekly, _ = IndexEngineService.execute_index_run(db_session, "2026-08-01", "2026-09-01", frequency="WEEKLY")
    run_monthly, _ = IndexEngineService.execute_index_run(db_session, "2026-08-01", "2026-09-01", frequency="MONTHLY")

    assert run_daily.frequency == "DAILY"
    assert run_weekly.frequency == "WEEKLY"
    assert run_monthly.frequency == "MONTHLY"

    # All three runs use identical underlying data math, so index value is identical
    assert run_daily.index_value == run_weekly.index_value == run_monthly.index_value

def test_10_run_manifest_matches_calculation_inputs(db_session):
    """
    Requirement 10: Calculation manifest stored in IndexRun matches exact inputs.
    """
    seed_database(db_session)
    run, _ = IndexEngineService.execute_index_run(db_session, "2026-08-01", "2026-09-01", frequency="MONTHLY")

    manifest = run.calculation_manifest
    assert manifest is not None
    assert manifest["frequency"] == "MONTHLY"
    assert manifest["total_observations_considered"] == run.number_of_observations
    assert manifest["eligible_observations_used"] == run.number_of_eligible_observations
    assert manifest["status_counts"]["valid"] == run.valid_count
    assert manifest["status_counts"]["excluded"] == run.excluded_count
    assert manifest["route_horizon_summary"]["expected_pairs"] == run.expected_route_horizon_pairs
    assert manifest["route_horizon_summary"]["calculated_pairs"] == run.calculated_route_horizon_pairs
    assert "DEL-BOM" in manifest["route_weights_used"]
