"""
Tests for Milestone 4C.2: Source Agreement & Data Health Service.
Validates multi-source comparison, statistical agreement, sample sufficiency,
imbalance metrics, health classification reason codes, and strict test-mode isolation.
"""
import pytest
import datetime as dt
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.observation import Observation
from app.services.source_agreement_service import SourceAgreementService


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
    live_mode: bool = True,
    carrier_id: str = "6E"
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
        baggage_information={"live_mode": live_mode},
        data_status="OBSERVED" if live_mode else "TEST"
    )
    return obs


def test_insufficient_sample_size_agreement_available_but_degraded():
    """
    When sources have strong agreement (e.g. 1% diff) but N < min_observations_per_source (e.g. N=2 each),
    agreement is AGREEMENT_AVAILABLE, but health status is DEGRADED with DEGRADED_INSUFFICIENT_SAMPLE_SIZE.
    """
    route_id = "DEL-BOM"
    travel_date = dt.date(2026, 4, 15)
    horizon = 15

    # 2 Google observations
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(2)]
    # 2 Duffel observations
    d_obs = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5050.0, live_mode=True) for i in range(2)]

    report = SourceAgreementService.evaluate_source_agreement(
        observations=g_obs + d_obs,
        route_id=route_id,
        travel_date=travel_date,
        horizon=horizon,
        min_observations_per_source=5
    )

    assert report["health_evaluation"]["health_status"] == "DEGRADED"
    assert report["health_evaluation"]["agreement_state"] == "AGREEMENT_AVAILABLE"
    assert "DEGRADED_INSUFFICIENT_SAMPLE_SIZE" in report["health_evaluation"]["health_reasons"]
    assert report["cross_source_agreement"]["sample_sufficiency"]["is_sample_sufficient"] is False
    assert report["cross_source_agreement"]["sample_sufficiency"]["min_required_per_source"] == 5
    assert report["cross_source_agreement"]["percentage_median_difference"] == 1.0


def test_adequate_sample_size_equal_medians_healthy():
    """When both sources meet minimum sample size (N >= 5) and agree within 10%, report is HEALTHY."""
    route_id = "DEL-BOM"
    travel_date = dt.date(2026, 4, 15)
    horizon = 15

    # 5 Google observations around 5000 (median 5000)
    g_obs = [
        create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", fare)
        for i, fare in enumerate([4800.0, 4900.0, 5000.0, 5100.0, 5200.0])
    ]
    # 5 Duffel observations around 5000 (median 5000)
    d_obs = [
        create_mock_obs(f"D{i}", "SRC_DUFFEL", fare, live_mode=True)
        for i, fare in enumerate([4850.0, 4950.0, 5000.0, 5050.0, 5150.0])
    ]

    report = SourceAgreementService.evaluate_source_agreement(
        observations=g_obs + d_obs,
        route_id=route_id,
        travel_date=travel_date,
        horizon=horizon,
        min_observations_per_source=5
    )

    assert report["health_evaluation"]["health_status"] == "HEALTHY"
    assert report["health_evaluation"]["agreement_state"] == "AGREEMENT_AVAILABLE"
    assert "HEALTHY_MULTI_SOURCE_AGREEMENT" in report["health_evaluation"]["health_reasons"]
    assert report["cross_source_agreement"]["active_eligible_sources_count"] == 2
    assert report["cross_source_agreement"]["absolute_median_difference"] == 0.0
    assert report["cross_source_agreement"]["percentage_median_difference"] == 0.0
    assert report["cross_source_agreement"]["source_coverage_ratio"] == 1.0
    assert report["cross_source_agreement"]["observation_count_imbalance_ratio"] == 1.0
    assert report["cross_source_agreement"]["sample_sufficiency"]["is_sample_sufficient"] is True


def test_adequate_sample_size_small_disagreement_within_threshold_healthy():
    """Small discrepancy within 10% tolerance with N >= 5 remains HEALTHY."""
    route_id = "DEL-BOM"
    travel_date = dt.date(2026, 4, 15)
    horizon = 15

    # Google median = 5000, N = 5
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]
    # Duffel median = 5200 (diff = 200, average = 5100, pct diff = 3.92% <= 10%), N = 5
    d_obs = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5200.0, live_mode=True) for i in range(5)]

    report = SourceAgreementService.evaluate_source_agreement(
        observations=g_obs + d_obs,
        route_id=route_id,
        travel_date=travel_date,
        horizon=horizon,
        min_observations_per_source=5
    )

    assert report["health_evaluation"]["health_status"] == "HEALTHY"
    assert report["cross_source_agreement"]["absolute_median_difference"] == 200.0
    assert report["cross_source_agreement"]["percentage_median_difference"] == 3.92
    assert "HEALTHY_MULTI_SOURCE_AGREEMENT" in report["health_evaluation"]["health_reasons"]
    assert report["cross_source_agreement"]["sample_sufficiency"]["is_sample_sufficient"] is True


def test_adequate_sample_size_large_disagreement_degraded():
    """Discrepancy > 10% with N >= 5 triggers DEGRADED and DEGRADED_LARGE_MEDIAN_DISCREPANCY."""
    route_id = "DEL-BOM"
    travel_date = dt.date(2026, 4, 15)
    horizon = 15

    # Google median = 5000, N = 5
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]
    # Duffel median = 6500 (diff = 1500, average = 5750, pct diff = 26.09% > 10%), N = 5
    d_obs = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 6500.0, live_mode=True) for i in range(5)]

    report = SourceAgreementService.evaluate_source_agreement(
        observations=g_obs + d_obs,
        route_id=route_id,
        travel_date=travel_date,
        horizon=horizon,
        min_observations_per_source=5
    )

    assert report["health_evaluation"]["health_status"] == "DEGRADED"
    assert report["health_evaluation"]["agreement_state"] == "AGREEMENT_AVAILABLE"
    assert "DEGRADED_LARGE_MEDIAN_DISCREPANCY" in report["health_evaluation"]["health_reasons"]
    assert report["cross_source_agreement"]["percentage_median_difference"] == 26.09
    assert report["cross_source_agreement"]["sample_sufficiency"]["is_sample_sufficient"] is True


def test_sample_size_imbalance_degraded():
    """Sample size ratio > 4.0 triggers DEGRADED_SAMPLE_SIZE_IMBALANCE."""
    route_id = "DEL-BOM"
    travel_date = dt.date(2026, 4, 15)
    horizon = 15

    # Google has 25 observations, median = 5000
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(25)]
    # Duffel has 5 observations, median = 5000 (ratio = 5.0 > 4.0)
    d_obs = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5000.0, live_mode=True) for i in range(5)]

    report = SourceAgreementService.evaluate_source_agreement(
        observations=g_obs + d_obs,
        route_id=route_id,
        travel_date=travel_date,
        horizon=horizon,
        min_observations_per_source=5
    )

    assert report["health_evaluation"]["health_status"] == "DEGRADED"
    assert "DEGRADED_SAMPLE_SIZE_IMBALANCE" in report["health_evaluation"]["health_reasons"]
    assert report["cross_source_agreement"]["observation_count_imbalance_ratio"] == 5.0


def test_single_source_only_degraded():
    """When only one source has eligible observations, state is SINGLE_SOURCE and DEGRADED."""
    route_id = "DEL-BOM"
    travel_date = dt.date(2026, 4, 15)
    horizon = 15

    # Only Google observations available
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]

    report = SourceAgreementService.evaluate_source_agreement(
        observations=g_obs,
        route_id=route_id,
        travel_date=travel_date,
        horizon=horizon
    )

    assert report["health_evaluation"]["health_status"] == "DEGRADED"
    assert report["health_evaluation"]["agreement_state"] == "SINGLE_SOURCE"
    assert "DEGRADED_SINGLE_SOURCE_ONLY" in report["health_evaluation"]["health_reasons"]
    assert report["cross_source_agreement"]["active_eligible_sources_count"] == 1
    assert report["cross_source_agreement"]["source_coverage_ratio"] == 0.5
    assert report["cross_source_agreement"]["absolute_median_difference"] is None


def test_zero_observations_insufficient():
    """When 0 observations are present, status is INSUFFICIENT."""
    report = SourceAgreementService.evaluate_source_agreement(
        observations=[],
        route_id="DEL-BOM",
        travel_date=dt.date(2026, 4, 15),
        horizon=15
    )

    assert report["health_evaluation"]["health_status"] == "INSUFFICIENT"
    assert report["health_evaluation"]["agreement_state"] == "INSUFFICIENT_COMPARABLE_DATA"
    assert "INSUFFICIENT_NO_OBSERVATIONS" in report["health_evaluation"]["health_reasons"]
    assert report["cross_source_agreement"]["active_eligible_sources_count"] == 0


def test_zero_eligible_observations_insufficient():
    """When observations exist but none are eligible (e.g. all REJECT), status is INSUFFICIENT."""
    obs = [
        create_mock_obs("G1", "SRC_GOOGLE_FLIGHTS", 5000.0, validation_status="REJECT", index_eligibility="INELIGIBLE"),
        create_mock_obs("D1", "SRC_DUFFEL", 5000.0, validation_status="REJECT", index_eligibility="INELIGIBLE")
    ]

    report = SourceAgreementService.evaluate_source_agreement(
        observations=obs,
        route_id="DEL-BOM",
        travel_date=dt.date(2026, 4, 15),
        horizon=15
    )

    assert report["health_evaluation"]["health_status"] == "INSUFFICIENT"
    assert report["health_evaluation"]["agreement_state"] == "INSUFFICIENT_COMPARABLE_DATA"
    assert "INSUFFICIENT_NO_ELIGIBLE_DATA" in report["health_evaluation"]["health_reasons"]


def test_test_mode_source_isolation_from_agreement():
    """Test-mode Duffel data (live_mode=false / TEST_DATA) is strictly excluded from production cross-source agreement."""
    route_id = "DEL-BOM"
    travel_date = dt.date(2026, 4, 15)
    horizon = 15

    # 5 Google live observations
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(5)]
    # 5 Duffel test-mode observations (marked TEST_DATA / INELIGIBLE)
    d_obs = [
        create_mock_obs(
            f"D{i}",
            "SRC_DUFFEL",
            99999.0,  # Ridiculous test fare
            index_eligibility="INELIGIBLE",
            live_mode=False
        )
        for i in range(5)
    ]

    report = SourceAgreementService.evaluate_source_agreement(
        observations=g_obs + d_obs,
        route_id=route_id,
        travel_date=travel_date,
        horizon=horizon
    )

    # Duffel is in source-wise metrics (total=5, eligible=0)
    assert report["source_wise_metrics"]["SRC_DUFFEL"]["total_observations_count"] == 5
    assert report["source_wise_metrics"]["SRC_DUFFEL"]["eligible_observations_count"] == 0
    assert report["source_wise_metrics"]["SRC_DUFFEL"]["has_eligible_data"] is False
    assert report["source_wise_metrics"]["SRC_DUFFEL"]["median_fare"] is None

    # Test isolation metrics confirm test data presence and exclusion
    assert report["test_mode_isolation"]["test_data_observations_count"] == 5
    assert report["test_mode_isolation"]["test_data_excluded_from_production_agreement"] is True

    # Cross-source agreement only considers the 1 active eligible source (Google Flights)
    assert report["cross_source_agreement"]["active_eligible_sources_count"] == 1
    assert report["cross_source_agreement"]["active_eligible_sources"] == ["SRC_GOOGLE_FLIGHTS"]
    assert report["health_evaluation"]["agreement_state"] == "SINGLE_SOURCE"
    assert report["health_evaluation"]["health_status"] == "DEGRADED"
    assert "DEGRADED_SINGLE_SOURCE_ONLY" in report["health_evaluation"]["health_reasons"]


def test_configurable_min_observations_threshold():
    """Verifies that configurable min_observations_per_source (e.g. N=2) allows smaller samples to be HEALTHY."""
    route_id = "DEL-BOM"
    travel_date = dt.date(2026, 4, 15)
    horizon = 15

    # 2 Google observations
    g_obs = [create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0) for i in range(2)]
    # 2 Duffel observations
    d_obs = [create_mock_obs(f"D{i}", "SRC_DUFFEL", 5000.0, live_mode=True) for i in range(2)]

    # With min=2, N=2 should be HEALTHY
    report = SourceAgreementService.evaluate_source_agreement(
        observations=g_obs + d_obs,
        route_id=route_id,
        travel_date=travel_date,
        horizon=horizon,
        min_observations_per_source=2
    )

    assert report["health_evaluation"]["health_status"] == "HEALTHY"
    assert "HEALTHY_MULTI_SOURCE_AGREEMENT" in report["health_evaluation"]["health_reasons"]
    assert report["cross_source_agreement"]["sample_sufficiency"]["is_sample_sufficient"] is True


def test_db_session_query_integration():
    """Verifies calculate_route_health_report executes cleanly against SQLite in-memory DB."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    travel_date = dt.date(2026, 4, 15)
    collection_date = dt.date(2026, 3, 31)

    obs_list = []
    # 5 Google observations
    for i in range(5):
        obs_list.append(create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0 + i * 50, collection_date=collection_date))
    # 5 Duffel observations
    for i in range(5):
        obs_list.append(create_mock_obs(f"D{i}", "SRC_DUFFEL", 5000.0 + i * 50, collection_date=collection_date, live_mode=True))

    session.add_all(obs_list)
    session.commit()

    report = SourceAgreementService.calculate_route_health_report(
        db=session,
        route_id="DEL-BOM",
        travel_date=travel_date,
        horizon=15,
        cabin="ECONOMY",
        collection_date=collection_date,
        min_observations_per_source=5
    )


    assert report["health_evaluation"]["health_status"] == "HEALTHY"
    assert report["cross_source_agreement"]["active_eligible_sources_count"] == 2
    assert report["source_wise_metrics"]["SRC_GOOGLE_FLIGHTS"]["eligible_observations_count"] == 5
    assert report["source_wise_metrics"]["SRC_DUFFEL"]["eligible_observations_count"] == 5
    assert report["cross_source_agreement"]["sample_sufficiency"]["is_sample_sufficient"] is True

    session.close()


def test_non_comparable_different_travel_dates_not_disagreement():
    """
    Regression Test:
    When Google has observations for 2026-04-15 (fare 5000) and Duffel has observations for 2026-05-20 (fare 9000),
    evaluating 2026-04-15 MUST isolate the Duffel observations as non-comparable.
    It must NOT compare 5000 vs 9000 or falsely trigger DEGRADED_LARGE_MEDIAN_DISCREPANCY.
    Instead, it must cleanly yield SINGLE_SOURCE (Google only) with 0 median discrepancy.
    """
    target_travel_date = dt.date(2026, 4, 15)
    other_travel_date = dt.date(2026, 5, 20)

    # 5 Google observations for April 15 (target date) @ fare 5000
    g_obs = [
        create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0, travel_date=target_travel_date)
        for i in range(5)
    ]
    # 5 Duffel observations for May 20 (different date) @ fare 9000
    d_obs = [
        create_mock_obs(f"D{i}", "SRC_DUFFEL", 9000.0, travel_date=other_travel_date, live_mode=True)
        for i in range(5)
    ]

    report = SourceAgreementService.evaluate_source_agreement(
        observations=g_obs + d_obs,
        route_id="DEL-BOM",
        travel_date=target_travel_date,
        horizon=15,
        cabin="ECONOMY",
        min_observations_per_source=5
    )

    # Verify comparability audit metadata
    assert report["comparability_audit"]["total_input_observations"] == 10
    assert report["comparability_audit"]["comparable_observations_count"] == 5
    assert report["comparability_audit"]["non_comparable_observations_excluded_count"] == 5
    assert report["comparability_audit"]["is_fully_comparable"] is False

    # Verify source-wise metrics: Google has 5 eligible, Duffel has 0 eligible for this slice
    assert report["source_wise_metrics"]["SRC_GOOGLE_FLIGHTS"]["eligible_observations_count"] == 5
    assert report["source_wise_metrics"]["SRC_GOOGLE_FLIGHTS"]["median_fare"] == 5000.0
    assert report["source_wise_metrics"]["SRC_DUFFEL"]["total_observations_count"] == 0
    assert report["source_wise_metrics"]["SRC_DUFFEL"]["eligible_observations_count"] == 0
    assert report["source_wise_metrics"]["SRC_DUFFEL"]["median_fare"] is None

    # Cross-source agreement is SINGLE_SOURCE (not AGREEMENT_AVAILABLE)
    assert report["cross_source_agreement"]["active_eligible_sources_count"] == 1
    assert report["cross_source_agreement"]["active_eligible_sources"] == ["SRC_GOOGLE_FLIGHTS"]
    assert report["cross_source_agreement"]["absolute_median_difference"] is None
    assert report["cross_source_agreement"]["percentage_median_difference"] is None

    # Health status is DEGRADED due to SINGLE_SOURCE only, NOT false price discrepancy
    assert report["health_evaluation"]["health_status"] == "DEGRADED"
    assert report["health_evaluation"]["agreement_state"] == "SINGLE_SOURCE"
    assert "DEGRADED_SINGLE_SOURCE_ONLY" in report["health_evaluation"]["health_reasons"]
    assert "DEGRADED_LARGE_MEDIAN_DISCREPANCY" not in report["health_evaluation"]["health_reasons"]


def test_non_comparable_different_cabin_or_horizon_isolation():
    """
    Regression Test:
    When observations have different cabins or horizons (e.g. Google Economy T+15 vs Duffel Business T+30),
    evaluating Economy T+15 excludes the Business T+30 observations without false cross-source discrepancy.
    """
    target_date = dt.date(2026, 4, 15)

    # 5 Google observations for Economy, Horizon 15 @ fare 5000
    g_obs = [
        create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0, travel_date=target_date, horizon=15, cabin="ECONOMY")
        for i in range(5)
    ]
    # 5 Duffel observations for Business, Horizon 30 @ fare 25000
    d_obs = [
        create_mock_obs(f"D{i}", "SRC_DUFFEL", 25000.0, travel_date=target_date, horizon=30, cabin="BUSINESS", live_mode=True)
        for i in range(5)
    ]

    report = SourceAgreementService.evaluate_source_agreement(
        observations=g_obs + d_obs,
        route_id="DEL-BOM",
        travel_date=target_date,
        horizon=15,
        cabin="ECONOMY",
        min_observations_per_source=5
    )

    assert report["comparability_audit"]["comparable_observations_count"] == 5
    assert report["comparability_audit"]["non_comparable_observations_excluded_count"] == 5
    assert report["source_wise_metrics"]["SRC_GOOGLE_FLIGHTS"]["eligible_observations_count"] == 5
    assert report["source_wise_metrics"]["SRC_DUFFEL"]["eligible_observations_count"] == 0
    assert report["cross_source_agreement"]["active_eligible_sources_count"] == 1
    assert "DEGRADED_LARGE_MEDIAN_DISCREPANCY" not in report["health_evaluation"]["health_reasons"]


def test_entirely_non_comparable_batch_yields_insufficient():
    """
    When all provided observations belong to a different travel date than queried,
    comparable count is 0 and status is INSUFFICIENT with INSUFFICIENT_NO_COMPARABLE_OBSERVATIONS.
    """
    other_date = dt.date(2026, 6, 1)
    target_date = dt.date(2026, 4, 15)

    obs = [
        create_mock_obs(f"G{i}", "SRC_GOOGLE_FLIGHTS", 5000.0, travel_date=other_date)
        for i in range(5)
    ]

    report = SourceAgreementService.evaluate_source_agreement(
        observations=obs,
        route_id="DEL-BOM",
        travel_date=target_date,
        horizon=15,
        cabin="ECONOMY"
    )

    assert report["comparability_audit"]["total_input_observations"] == 5
    assert report["comparability_audit"]["comparable_observations_count"] == 0
    assert report["comparability_audit"]["non_comparable_observations_excluded_count"] == 5
    assert report["health_evaluation"]["health_status"] == "INSUFFICIENT"
    assert report["health_evaluation"]["agreement_state"] == "INSUFFICIENT_COMPARABLE_DATA"
    assert "INSUFFICIENT_NO_COMPARABLE_OBSERVATIONS" in report["health_evaluation"]["health_reasons"]

