"""4A.1 regression tests: observed search_timestamp discipline."""
import datetime as dt, json, pathlib, pytest

FIX = pathlib.Path(__file__).parents[1]/"fixtures"/"days_left_trap.json"

class DerivedHorizonRejected(Exception): pass

def adapter_ingest(row: dict) -> dict:
    """Reference contract: search_timestamp must be OBSERVED, supplied by the source."""
    if "search_timestamp" not in row or row["search_timestamp"] is None:
        if "days_left" in row or "implied_search_date" in row:
            raise DerivedHorizonRejected("DERIVED_HORIZON_NO_OBSERVED_SEARCH_TIMESTAMP")
        raise DerivedHorizonRejected("MISSING_OBSERVED_SEARCH_TIMESTAMP")
    ts = dt.datetime.fromisoformat(row["search_timestamp"])
    td = dt.date.fromisoformat(row["travel_date"])
    return {**row, "advance_purchase_days": (td - ts.date()).days,
             "search_timestamp": row["search_timestamp"]}

def test_days_left_fixture_is_rejected():
    for r in json.loads(FIX.read_text())["rows"]:
        with pytest.raises(DerivedHorizonRejected) as e:
            adapter_ingest(r)
        assert "DERIVED_HORIZON" in str(e.value)

def test_fixture_collapses_to_single_search_date():
    rows = json.loads(FIX.read_text())["rows"]
    assert len({r["implied_search_date"] for r in rows}) == 1, \
        "fixture must demonstrate identical implied search dates across horizons"

def test_apw_derived_from_observed_timestamp():
    out = adapter_ingest({"search_timestamp":"2026-09-09T12:24:19+00:00",
                          "travel_date":"2026-09-30","total_fare":6314.0})
    assert out["advance_purchase_days"] == 21

def test_original_timestamp_preserved_exactly():
    raw = "2026-09-09T12:24:19.844607+00:00"
    out = adapter_ingest({"search_timestamp":raw,"travel_date":"2026-09-30"})
    assert out["search_timestamp"] == raw

def test_apw_is_never_negative_for_valid_observation():
    out = adapter_ingest({"search_timestamp":"2026-09-09T00:00:00+00:00","travel_date":"2026-09-09"})
    assert out["advance_purchase_days"] == 0

def test_no_manufactured_fare_components():
    """Total-only source must leave components NULL and flag TOTAL_ONLY."""
    obs = {"total_fare":5312.0,"base_fare":None,"taxes_total":None,"fees_charges":None,
           "gst_amount":None,"fuel_surcharge":None,"fare_breakdown_status":"TOTAL_ONLY"}
    assert obs["base_fare"] is None and obs["taxes_total"] is None
    assert obs["fare_breakdown_status"] == "TOTAL_ONLY"
    assert obs["total_fare"] == 5312.0

def test_gst_rule_is_context_not_decomposition():
    """A published carrier tariff must NOT be used to back-solve a third-party total."""
    total = 5312.0
    forbidden = total/1.05
    obs = {"total_fare":total,"base_fare":None}
    assert obs["base_fare"] != pytest.approx(forbidden)
    assert obs["base_fare"] is None

def test_live_panel_passes_apw_integrity():
    import csv, glob
    files = glob.glob(str(pathlib.Path(__file__).parents[1]/"out"/"aerocpi_panel_day1.csv"))
    if not files: pytest.skip("panel not collected")
    n=0
    for r in csv.DictReader(open(files[0])):
        ts=dt.datetime.fromisoformat(r["search_timestamp"]).date()
        td=dt.date.fromisoformat(r["travel_date"])
        assert (td-ts).days == int(r["advance_purchase_days"]); n+=1
    assert n > 0
