import os
import json
import hashlib
import pathlib
import pytest
from unittest.mock import patch, MagicMock

from app.services.duffel_client_service import DuffelClientService

FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "duffel_offer_request_response.json"


def test_missing_token_error_handling(monkeypatch):
    with patch("app.services.duffel_client_service.load_dotenv"):
        monkeypatch.delenv("DUFFEL_API_TOKEN", raising=False)
        with pytest.raises(ValueError, match="DUFFEL_API_TOKEN environment variable is not set"):
            DuffelClientService.get_api_token()


def test_header_and_credential_safety(monkeypatch):
    monkeypatch.setenv("DUFFEL_API_TOKEN", "duffel_test_mock_token_12345")
    token = DuffelClientService.get_api_token()
    assert token == "duffel_test_mock_token_12345"
    assert "Bearer" not in token  # Ensure clean token value without prepended scheme in env


def test_raw_response_sha256_determinism():
    with open(FIXTURE_PATH, "rb") as f:
        raw_bytes = f.read()

    digest1 = hashlib.sha256(raw_bytes).hexdigest()
    digest2 = hashlib.sha256(raw_bytes).hexdigest()
    assert digest1 == digest2
    assert len(digest1) == 64


def test_live_mode_false_classified_as_test_data():
    sample_data = {
        "data": {
            "id": "orq_test_123",
            "live_mode": False,
            "offers": []
        }
    }
    audit = DuffelClientService.audit_offer_request_response(sample_data)
    assert audit["live_mode"] is False
    assert audit["data_classification"] == "TEST_DATA"


def test_live_mode_true_classified_as_live_market_data():
    sample_data = {
        "data": {
            "id": "orq_live_123",
            "live_mode": True,
            "offers": []
        }
    }
    audit = DuffelClientService.audit_offer_request_response(sample_data)
    assert audit["live_mode"] is True
    assert audit["data_classification"] == "LIVE_MARKET_DATA"


def test_nested_segment_field_extraction():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    audit = DuffelClientService.audit_offer_request_response(data)
    assert audit["offer_request_id"] == "orq_0000AcX1Y2Z3A4B5C6D7E8"
    assert audit["offers_count"] == 2

    offer0 = audit["offers"][0]
    assert offer0["offer_id"] == "off_0000AcX1Y2Z3A4B5C6D7E1"
    assert offer0["owner_code"] == "6E"
    assert offer0["total_amount"] == "5312.00"
    assert offer0["base_amount"] == "4500.00"
    assert offer0["tax_amount"] == "812.00"

    slices = offer0["slices"]
    assert len(slices) == 1
    assert slices[0]["duration"] == "PT2H15M"

    segments = slices[0]["segments"]
    assert len(segments) == 1
    seg0 = segments[0]
    assert seg0["flight_number"] == "6E-2131"
    assert seg0["origin_iata"] == "DEL"
    assert seg0["destination_iata"] == "BOM"
    assert seg0["departing_at"] == "2026-09-25T08:00:00"
    assert seg0["arriving_at"] == "2026-09-25T10:15:00"


def test_nullable_tax_and_no_value_inference():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    audit = DuffelClientService.audit_offer_request_response(data)
    offer1 = audit["offers"][1]  # Air India offer with null tax/base amounts in fixture

    assert offer1["total_amount"] == "6100.00"
    # Verify strict nullability: missing base/tax amounts are kept as None, NOT inferred or calculated
    assert offer1["base_amount"] is None
    assert offer1["tax_amount"] is None
    assert offer1["base_currency"] is None
    assert offer1["tax_currency"] is None


def test_fixture_response_audit_completeness():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    audit = DuffelClientService.audit_offer_request_response(data)
    avail = audit["component_availability"]

    assert avail["has_offer_request_id"] is True
    assert avail["has_live_mode"] is True
    assert avail["has_offers"] is True
    assert avail["has_base_amount"] is True
    assert avail["has_tax_amount"] is True
    assert avail["has_total_amount"] is True
    assert avail["has_flight_number"] is True
    assert avail["has_offer_expiry"] is True


def test_create_offer_request_mocked_http(monkeypatch):
    monkeypatch.setenv("DUFFEL_API_TOKEN", "duffel_test_token_999")

    mock_resp_json = {
        "data": {
            "id": "orq_mock_123",
            "live_mode": False,
            "offers": []
        }
    }

    mock_httpx_resp = MagicMock()
    mock_httpx_resp.status_code = 200
    mock_httpx_resp.content = json.dumps(mock_resp_json).encode("utf-8")
    mock_httpx_resp.json.return_value = mock_resp_json

    with patch("httpx.Client.post", return_value=mock_httpx_resp) as mock_post:
        metadata, raw_bytes, resp_json, audit_report = DuffelClientService.create_offer_request(
            origin="DEL",
            dest="BOM",
            departure_date="2026-09-25"
        )

        assert metadata["http_status"] == 200
        assert metadata["offer_request_id"] == "orq_mock_123"
        assert metadata["data_classification"] == "TEST_DATA"
        assert audit_report["live_mode"] is False

        # Verify request parameters
        call_args, call_kwargs = mock_post.call_args
        headers = call_kwargs.get("headers", {})
        assert headers["Authorization"] == "Bearer duffel_test_token_999"
        assert headers["Duffel-Version"] == "v2"
