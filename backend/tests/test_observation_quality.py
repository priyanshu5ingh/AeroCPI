import json
import pytest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

from app.services.observation_quality_service import ObservationQualityService, compute_percentile
from app.models.observation import Observation
from app.schemas.observation import RawQuoteInput
from app.services.observation_service import ObservationService
from app.services.duffel_adapter_service import DuffelAdapterService

import pathlib
DUFFEL_FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "duffel_offer_request_response.json"


def test_percentile_computation_helper():
    data = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert compute_percentile(data, 0.0) == 10.0
    assert compute_percentile(data, 0.5) == 30.0
    assert compute_percentile(data, 1.0) == 50.0
    assert compute_percentile(data, 0.25) == 20.0
    assert compute_percentile(data, 0.75) == 40.0

    # Single value
    assert compute_percentile([4500.0], 0.5) == 4500.0
    # Empty
    assert compute_percentile([], 0.5) == 0.0


def test_empty_population():
    report = ObservationQualityService.compute_quality_metrics(
        observations=[],
        route_id="DEL-BOM",
        travel_date=date(2026, 9, 25),
        horizon=15,
        cabin="ECONOMY"
    )

    pop = report["population_summary"]
    assert pop["total_observations"] == 0
    assert pop["accepted_observations"] == 0
    assert pop["flagged_observations"] == 0
    assert pop["rejected_observations"] == 0
    assert pop["index_eligible_observations"] == 0
    assert pop["data_classification_distribution"] == {}

    comp = report["collection_completeness"]
    assert comp["has_data"] is False
    assert comp["has_eligible_data"] is False
    assert comp["acceptance_rate"] == 0.0
    assert comp["flag_rate"] == 0.0
    assert comp["rejection_rate"] == 0.0
    assert comp["index_eligibility_rate"] == 0.0

    pop_prices = report["population_price_metrics"]
    assert pop_prices["price_observations_count"] == 0
    assert pop_prices["min"] is None
    assert pop_prices["median"] is None
    assert pop_prices["dispersion"]["std_dev"] == 0.0

    idx_prices = report["index_eligible_price_metrics"]
    assert idx_prices["price_observations_count"] == 0
    assert idx_prices["min"] is None


def test_single_observation_dispersion_handling():
    obs = MagicMock(spec=Observation)
    obs.source_id = "SRC_GOOGLE_FLIGHTS"
    obs.airline = "6E"
    obs.carrier_id = "6E"
    obs.cabin = "ECONOMY"
    obs.flight_number = "6E-2131"
    obs.duration_minutes = 135
    obs.stops = 0
    obs.source_url = "https://google.com/travel"
    obs.total_fare = 4500.0
    obs.base_fare = None
    obs.taxes = None
    obs.fees = None
    obs.mandatory_fees = None
    obs.quote_fingerprint = "fp_1"
    obs.validation_status = "ACCEPT"
    obs.validation_reasons = []
    obs.index_eligibility = "ELIGIBLE"
    obs.index_eligibility_reasons = ["INDEX_ELIGIBLE"]
    obs.data_status = "OBSERVED"
    obs.arithmetic_status = "ARITHMETIC_UNCHECKABLE"
    obs.breakdown_status = "TOTAL_ONLY"

    report = ObservationQualityService.compute_quality_metrics(
        observations=[obs],
        route_id="DEL-BOM",
        travel_date=date(2026, 9, 25),
        horizon=15,
        cabin="ECONOMY"
    )

    prices = report["population_price_metrics"]
    assert prices["price_observations_count"] == 1
    assert prices["min"] == 4500.0
    assert prices["median"] == 4500.0
    assert prices["max"] == 4500.0
    assert prices["dispersion"]["std_dev"] == 0.0
    assert prices["dispersion"]["iqr"] == 0.0
    assert prices["dispersion"]["range"] == 0.0
    assert prices["dispersion"]["coeff_of_variation"] == 0.0

    idx_prices = report["index_eligible_price_metrics"]
    assert idx_prices["price_observations_count"] == 1
    assert idx_prices["median"] == 4500.0


def test_mixed_accept_flag_reject():
    # 1 ACCEPT, 1 FLAG, 1 REJECT
    o_accept = MagicMock(spec=Observation)
    o_accept.source_id = "SRC_GOOGLE_FLIGHTS"
    o_accept.airline = "6E"
    o_accept.carrier_id = "6E"
    o_accept.cabin = "ECONOMY"
    o_accept.flight_number = "6E-101"
    o_accept.duration_minutes = 120
    o_accept.stops = 0
    o_accept.source_url = "https://google.com"
    o_accept.total_fare = 4500.0
    o_accept.base_fare = 3800.0
    o_accept.taxes = 700.0
    o_accept.fees = None
    o_accept.mandatory_fees = None
    o_accept.quote_fingerprint = "fp_acc"
    o_accept.validation_status = "ACCEPT"
    o_accept.validation_reasons = []
    o_accept.index_eligibility = "ELIGIBLE"
    o_accept.index_eligibility_reasons = ["INDEX_ELIGIBLE"]
    o_accept.data_status = "OBSERVED"
    o_accept.arithmetic_status = "ARITHMETIC_MATCH"
    o_accept.breakdown_status = "COMPLETE_BREAKDOWN"

    o_flag = MagicMock(spec=Observation)
    o_flag.source_id = "SRC_GOOGLE_FLIGHTS"
    o_flag.airline = "AI"
    o_flag.carrier_id = "AI"
    o_flag.cabin = "ECONOMY"
    o_flag.flight_number = None  # Missing flight number -> FLAG
    o_flag.duration_minutes = 130
    o_flag.stops = 0
    o_flag.source_url = "https://google.com"
    o_flag.total_fare = 5000.0
    o_flag.base_fare = None
    o_flag.taxes = None
    o_flag.fees = None
    o_flag.mandatory_fees = None
    o_flag.quote_fingerprint = "fp_flag"
    o_flag.validation_status = "FLAG"
    o_flag.validation_reasons = ["FLAG_MISSING_FLIGHT_NUMBER"]
    o_flag.index_eligibility = "ELIGIBLE"
    o_flag.index_eligibility_reasons = ["INDEX_ELIGIBLE"]
    o_flag.data_status = "OBSERVED"
    o_flag.arithmetic_status = "ARITHMETIC_UNCHECKABLE"
    o_flag.breakdown_status = "TOTAL_ONLY"

    o_reject = MagicMock(spec=Observation)
    o_reject.source_id = "SRC_GOOGLE_FLIGHTS"
    o_reject.airline = "SG"
    o_reject.carrier_id = "SG"
    o_reject.cabin = "ECONOMY"
    o_reject.flight_number = "SG-501"
    o_reject.duration_minutes = 120
    o_reject.stops = 0
    o_reject.source_url = "https://google.com"
    o_reject.total_fare = 0.0  # Zero fare -> REJECT
    o_reject.base_fare = None
    o_reject.taxes = None
    o_reject.fees = None
    o_reject.mandatory_fees = None
    o_reject.quote_fingerprint = "fp_rej"
    o_reject.validation_status = "REJECT"
    o_reject.validation_reasons = ["REJECT_TOTAL_FARE_NON_POSITIVE"]
    o_reject.index_eligibility = "INELIGIBLE"
    o_reject.index_eligibility_reasons = ["INELIGIBLE_REJECTED_OBSERVATION"]
    o_reject.data_status = "REJECTED"
    o_reject.arithmetic_status = "ARITHMETIC_UNCHECKABLE"
    o_reject.breakdown_status = "TOTAL_ONLY"

    report = ObservationQualityService.compute_quality_metrics(
        observations=[o_accept, o_flag, o_reject],
        route_id="DEL-BOM",
        travel_date=date(2026, 9, 25),
        horizon=15,
        cabin="ECONOMY"
    )

    pop = report["population_summary"]
    assert pop["total_observations"] == 3
    assert pop["accepted_observations"] == 1
    assert pop["flagged_observations"] == 1
    assert pop["rejected_observations"] == 1
    assert pop["index_eligible_observations"] == 2
    assert pop["index_ineligible_observations"] == 1

    # Invariants
    assert pop["accepted_observations"] + pop["flagged_observations"] + pop["rejected_observations"] == pop["total_observations"]

    comp = report["collection_completeness"]
    assert comp["acceptance_rate"] == round(1 / 3, 4)
    assert comp["flag_rate"] == round(1 / 3, 4)
    assert comp["rejection_rate"] == round(1 / 3, 4)
    assert comp["index_eligibility_rate"] == round(2 / 3, 4)
    assert round(comp["acceptance_rate"] + comp["flag_rate"] + comp["rejection_rate"], 3) == 1.0


def test_two_population_price_metrics_isolation(db_session):
    now_utc = datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc)
    travel_dt = date(2026, 9, 25)

    # 1. Google Flights Quote: Total 4500, ACCEPT/FLAG (missing components), ELIGIBLE
    google_quote = RawQuoteInput(
        source_id="SRC_GOOGLE_FLIGHTS",
        source_name="Google Flights",
        collected_at=now_utc,
        search_timestamp=now_utc,
        travel_date=travel_dt,
        origin_raw="DEL",
        destination_raw="BOM",
        airline="6E",
        flight_number="6E-2131",
        total_fare=4500.0,
        currency="INR"
    )
    ObservationService.ingest_raw_quote(db_session, google_quote)

    # 2. Duffel Quotes: Total 5312 and 6100, FLAG, INELIGIBLE (test mode data)
    with open(DUFFEL_FIXTURE_PATH, "rb") as f:
        duffel_bytes = f.read()
    DuffelAdapterService.ingest_duffel_fixture_to_database(db_session, duffel_bytes, search_timestamp=now_utc)

    report = ObservationQualityService.calculate_route_quality_report(
        db=db_session,
        route_id="DEL-BOM",
        travel_date=travel_dt,
        horizon=15,
        cabin="ECONOMY"
    )

    pop = report["population_summary"]
    assert pop["total_observations"] == 3
    assert pop["flagged_observations"] == 3  # All 3 have FLAG_MISSING_FARE_COMPONENT_BREAKDOWN
    assert pop["accepted_observations"] == 0
    assert pop["rejected_observations"] == 0
    assert pop["index_eligible_observations"] == 1
    assert pop["index_ineligible_observations"] == 2

    # Verify Data Classification Distribution
    assert pop["data_classification_distribution"]["LIVE_MARKET_DATA"] == 1
    assert pop["data_classification_distribution"]["TEST_DATA"] == 2

    # Population Price Metrics (all 3 observed)
    pop_prices = report["population_price_metrics"]
    assert pop_prices["price_observations_count"] == 3
    assert pop_prices["min"] == 4500.0
    assert pop_prices["median"] == 5312.0
    assert pop_prices["max"] == 6100.0

    # Index Eligible Price Metrics (strictly Google Flights production quote ONLY)
    idx_prices = report["index_eligible_price_metrics"]
    assert idx_prices["price_observations_count"] == 1
    assert idx_prices["min"] == 4500.0
    assert idx_prices["median"] == 4500.0
    assert idx_prices["max"] == 4500.0
    assert idx_prices["dispersion"]["std_dev"] == 0.0

    # Rates
    comp = report["collection_completeness"]
    assert comp["flag_rate"] == 1.0
    assert comp["acceptance_rate"] == 0.0
    assert comp["index_eligibility_rate"] == round(1 / 3, 4)


def test_mathematical_invariants():
    obs_list = []
    # 5 ACCEPT + ELIGIBLE, 3 FLAG + ELIGIBLE, 2 REJECT + INELIGIBLE = 10 total
    for i in range(5):
        o = MagicMock(spec=Observation)
        o.source_id = "SRC_A"
        o.airline = "6E"
        o.carrier_id = "6E"
        o.cabin = "ECONOMY"
        o.flight_number = f"6E-{i}"
        o.duration_minutes = 120
        o.stops = 0
        o.source_url = "https://a.com"
        o.total_fare = 4000.0 + i * 100
        o.base_fare = 3500.0
        o.taxes = 500.0 + i * 100
        o.fees = 0.0
        o.mandatory_fees = 0.0
        o.quote_fingerprint = f"fp_a_{i}"
        o.validation_status = "ACCEPT"
        o.validation_reasons = []
        o.index_eligibility = "ELIGIBLE"
        o.index_eligibility_reasons = []
        o.data_status = "OBSERVED"
        o.arithmetic_status = "ARITHMETIC_MATCH"
        o.breakdown_status = "COMPLETE_BREAKDOWN"
        obs_list.append(o)

    for i in range(3):
        o = MagicMock(spec=Observation)
        o.source_id = "SRC_B"
        o.airline = "AI"
        o.carrier_id = "AI"
        o.cabin = "ECONOMY"
        o.flight_number = f"AI-{i}"
        o.duration_minutes = 130
        o.stops = 0
        o.source_url = "https://b.com"
        o.total_fare = 5000.0 + i * 100
        o.base_fare = None
        o.taxes = None
        o.fees = None
        o.mandatory_fees = None
        o.quote_fingerprint = f"fp_b_{i}"
        o.validation_status = "FLAG"
        o.validation_reasons = ["FLAG_MISSING_FARE_COMPONENT_BREAKDOWN"]
        o.index_eligibility = "ELIGIBLE"
        o.index_eligibility_reasons = []
        o.data_status = "OBSERVED"
        o.arithmetic_status = "ARITHMETIC_UNCHECKABLE"
        o.breakdown_status = "TOTAL_ONLY"
        obs_list.append(o)

    for i in range(2):
        o = MagicMock(spec=Observation)
        o.source_id = "SRC_C"
        o.airline = "SG"
        o.carrier_id = "SG"
        o.cabin = "ECONOMY"
        o.flight_number = f"SG-{i}"
        o.duration_minutes = 140
        o.stops = 0
        o.source_url = "https://c.com"
        o.total_fare = -100.0  # Invalid fare -> REJECT
        o.base_fare = None
        o.taxes = None
        o.fees = None
        o.mandatory_fees = None
        o.quote_fingerprint = f"fp_c_{i}"
        o.validation_status = "REJECT"
        o.validation_reasons = ["REJECT_TOTAL_FARE_NON_POSITIVE"]
        o.index_eligibility = "INELIGIBLE"
        o.index_eligibility_reasons = ["INELIGIBLE_REJECTED_OBSERVATION"]
        o.data_status = "REJECTED"
        o.arithmetic_status = "ARITHMETIC_UNCHECKABLE"
        o.breakdown_status = "TOTAL_ONLY"
        obs_list.append(o)

    report = ObservationQualityService.compute_quality_metrics(
        observations=obs_list,
        route_id="DEL-BOM",
        travel_date=date(2026, 9, 25),
        horizon=15,
        cabin="ECONOMY"
    )

    pop = report["population_summary"]
    comp = report["collection_completeness"]

    # Invariant 1: Sum of mutually exclusive statuses equals total
    assert pop["accepted_observations"] + pop["flagged_observations"] + pop["rejected_observations"] == pop["total_observations"]
    assert pop["total_observations"] == 10
    assert pop["accepted_observations"] == 5
    assert pop["flagged_observations"] == 3
    assert pop["rejected_observations"] == 2

    # Invariant 2: Rates are bounded in [0, 1] and sum to 1.0
    assert 0.0 <= comp["acceptance_rate"] <= 1.0
    assert 0.0 <= comp["flag_rate"] <= 1.0
    assert 0.0 <= comp["rejection_rate"] <= 1.0
    assert 0.0 <= comp["index_eligibility_rate"] <= 1.0
    assert round(comp["acceptance_rate"] + comp["flag_rate"] + comp["rejection_rate"], 4) == 1.0

    # Invariant 3: Rates match exact counts
    assert comp["acceptance_rate"] == 0.50
    assert comp["flag_rate"] == 0.30
    assert comp["rejection_rate"] == 0.20
    assert comp["index_eligibility_rate"] == 0.80

    # Invariant 4: Two price populations
    pop_prices = report["population_price_metrics"]
    idx_prices = report["index_eligible_price_metrics"]
    assert pop_prices["price_observations_count"] == 8  # 5 + 3 (excluding 2 rejected non-positive)
    assert idx_prices["price_observations_count"] == 8   # 5 + 3 (all eligible)


def test_multiple_sources():
    o1 = MagicMock(spec=Observation)
    o1.source_id = "SRC_GOOGLE_FLIGHTS"
    o1.airline = "6E"
    o1.carrier_id = "6E"
    o1.cabin = "ECONOMY"
    o1.flight_number = "6E-101"
    o1.duration_minutes = 120
    o1.stops = 0
    o1.source_url = "https://google.com"
    o1.total_fare = 4500.0
    o1.base_fare = None
    o1.taxes = None
    o1.fees = None
    o1.mandatory_fees = None
    o1.quote_fingerprint = "fp_g1"
    o1.validation_status = "ACCEPT"
    o1.validation_reasons = []
    o1.index_eligibility = "ELIGIBLE"
    o1.index_eligibility_reasons = []
    o1.data_status = "OBSERVED"
    o1.arithmetic_status = "ARITHMETIC_UNCHECKABLE"
    o1.breakdown_status = "TOTAL_ONLY"

    o2 = MagicMock(spec=Observation)
    o2.source_id = "SRC_DUFFEL"
    o2.airline = "6E"
    o2.carrier_id = "6E"
    o2.cabin = "ECONOMY"
    o2.flight_number = "6E-101"
    o2.duration_minutes = 120
    o2.stops = 0
    o2.source_url = None
    o2.total_fare = 5312.0
    o2.base_fare = 4500.0
    o2.taxes = 812.0
    o2.fees = None
    o2.mandatory_fees = None
    o2.quote_fingerprint = "fp_d1"
    o2.validation_status = "FLAG"
    o2.validation_reasons = ["FLAG_MISSING_FARE_COMPONENT_BREAKDOWN"]
    o2.index_eligibility = "INELIGIBLE"
    o2.index_eligibility_reasons = ["INELIGIBLE_TEST_MODE_DATA"]
    o2.data_status = "OBSERVED"
    o2.arithmetic_status = "ARITHMETIC_MATCH"
    o2.breakdown_status = "PARTIAL_BREAKDOWN"

    report = ObservationQualityService.compute_quality_metrics(
        observations=[o1, o2],
        route_id="DEL-BOM",
        travel_date=date(2026, 9, 25),
        horizon=15,
        cabin="ECONOMY"
    )

    src = report["source_metrics"]
    assert src["source_count"] == 2
    assert src["sources_represented"] == ["SRC_DUFFEL", "SRC_GOOGLE_FLIGHTS"]
    assert src["source_wise_observation_counts"]["SRC_GOOGLE_FLIGHTS"] == 1
    assert src["source_wise_observation_counts"]["SRC_DUFFEL"] == 1
    assert src["source_wise_eligible_counts"]["SRC_GOOGLE_FLIGHTS"] == 1
    assert src["source_wise_eligible_counts"].get("SRC_DUFFEL", 0) == 0


def test_duplicate_observations():
    obs_list = []
    # 2 observations with the SAME fingerprint (duplicate)
    for _ in range(2):
        o = MagicMock(spec=Observation)
        o.source_id = "SRC_GOOGLE_FLIGHTS"
        o.airline = "6E"
        o.carrier_id = "6E"
        o.cabin = "ECONOMY"
        o.flight_number = "6E-101"
        o.duration_minutes = 120
        o.stops = 0
        o.source_url = "https://google.com"
        o.total_fare = 4500.0
        o.base_fare = None
        o.taxes = None
        o.fees = None
        o.mandatory_fees = None
        o.quote_fingerprint = "identical_fingerprint_hash"
        o.validation_status = "ACCEPT"
        o.validation_reasons = []
        o.index_eligibility = "ELIGIBLE"
        o.index_eligibility_reasons = []
        o.data_status = "OBSERVED"
        o.arithmetic_status = "ARITHMETIC_UNCHECKABLE"
        o.breakdown_status = "TOTAL_ONLY"
        obs_list.append(o)

    report = ObservationQualityService.compute_quality_metrics(
        observations=obs_list,
        route_id="DEL-BOM",
        travel_date=date(2026, 9, 25),
        horizon=15,
        cabin="ECONOMY"
    )

    dups = report["duplicate_metrics"]
    assert dups["unique_observations_count"] == 1
    assert dups["duplicate_observations_count"] == 1
    assert dups["duplicate_rate"] == 0.50


def test_missing_metadata():
    o = MagicMock(spec=Observation)
    o.source_id = "SRC_GOOGLE_FLIGHTS"
    o.airline = "UNKNOWN"
    o.carrier_id = "UNKNOWN"
    o.cabin = "ECONOMY"
    o.flight_number = None
    o.duration_minutes = None
    o.stops = None
    o.source_url = None
    o.total_fare = 4500.0
    o.base_fare = None
    o.taxes = None
    o.fees = None
    o.mandatory_fees = None
    o.quote_fingerprint = "fp_miss"
    o.validation_status = "FLAG"
    o.validation_reasons = ["FLAG_MISSING_FLIGHT_NUMBER"]
    o.index_eligibility = "ELIGIBLE"
    o.index_eligibility_reasons = []
    o.data_status = "OBSERVED"
    o.arithmetic_status = "ARITHMETIC_UNCHECKABLE"
    o.breakdown_status = "TOTAL_ONLY"

    report = ObservationQualityService.compute_quality_metrics(
        observations=[o],
        route_id="DEL-BOM",
        travel_date=date(2026, 9, 25),
        horizon=15,
        cabin="ECONOMY"
    )

    meta = report["metadata_completeness"]
    assert meta["missing_flight_number_count"] == 1
    assert meta["missing_duration_count"] == 1
    assert meta["missing_stops_count"] == 1
    assert meta["missing_source_url_count"] == 1
    assert meta["missing_carrier_count"] == 1


def test_json_quality_report_reproducibility():
    report = ObservationQualityService.compute_quality_metrics(
        observations=[],
        route_id="DEL-BOM",
        travel_date=date(2026, 9, 25),
        horizon=15,
        cabin="ECONOMY"
    )

    # Must be 100% JSON serializable
    serialized = json.dumps(report, indent=2)
    assert isinstance(serialized, str)
    deserialized = json.loads(serialized)
    assert "metadata" in deserialized
    assert "population_summary" in deserialized
    assert "source_metrics" in deserialized
    assert "population_price_metrics" in deserialized
    assert "index_eligible_price_metrics" in deserialized
    assert "collection_completeness" in deserialized

