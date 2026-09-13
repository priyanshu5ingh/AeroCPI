"""
AeroCPI Duffel Connectivity & Response Audit CLI Tool
Usage:
  Offline Fixture Mode (default if DUFFEL_API_TOKEN missing):
    python scripts/audit_duffel_connectivity.py --origin DEL --dest BOM --apw 15

  Live Mode (requires DUFFEL_API_TOKEN in environment):
    python scripts/audit_duffel_connectivity.py --origin DEL --dest BOM --apw 15 --live
"""
import sys
import os
import argparse
import json
import hashlib
import pathlib
import datetime as dt

# Ensure backend directory is in sys.path
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.duffel_client_service import DuffelClientService
from dotenv import load_dotenv

FIXTURE_PATH = BACKEND_DIR / "tests" / "fixtures" / "duffel_offer_request_response.json"
AUDIT_OUT_DIR = PROJECT_ROOT / "data" / "raw" / "duffel_audit"


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="AeroCPI Duffel API Response Audit Tool")
    parser.add_argument("--origin", type=str, default="DEL", help="Origin IATA code")
    parser.add_argument("--dest", type=str, default="BOM", help="Destination IATA code")
    parser.add_argument("--apw", type=int, default=15, help="Advance purchase window days")
    parser.add_argument("--live", action="store_true", help="Force live API call using DUFFEL_API_TOKEN")
    args = parser.parse_args()

    token = os.getenv("DUFFEL_API_TOKEN")
    use_live = args.live or bool(token)

    travel_date = (dt.datetime.now(dt.timezone.utc).date() + dt.timedelta(days=args.apw)).strftime("%Y-%m-%d")

    AUDIT_OUT_DIR.mkdir(parents=True, exist_ok=True)

    if use_live and token:
        print(f"=== Running Live Duffel API Audit for {args.origin}-{args.dest} (APW {args.apw}, Travel Date: {travel_date}) ===")
        try:
            metadata, raw_bytes, resp_json, audit_report = DuffelClientService.create_offer_request(
                origin=args.origin,
                dest=args.dest,
                departure_date=travel_date
            )
        except Exception as e:
            print(f"ERROR: Live Duffel API call failed: {type(e).__name__}: {str(e)}")
            sys.exit(1)
    else:
        print(f"=== Running Offline Fixture Duffel Response Audit for {args.origin}-{args.dest} (APW {args.apw}) ===")
        if not FIXTURE_PATH.exists():
            print(f"ERROR: Fixture file not found at {FIXTURE_PATH}")
            sys.exit(1)

        with open(FIXTURE_PATH, "rb") as ff:
            raw_bytes = ff.read()

        raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        resp_json = json.loads(raw_bytes.decode("utf-8"))
        audit_report = DuffelClientService.audit_offer_request_response(resp_json)

        now_utc = dt.datetime.now(dt.timezone.utc).isoformat()
        metadata = {
            "request_timestamp_utc": now_utc,
            "response_timestamp_utc": now_utc,
            "endpoint": "POST /air/offer_requests?return_offers=true (Offline Fixture)",
            "http_status": 200,
            "offer_request_id": audit_report.get("offer_request_id"),
            "live_mode": audit_report.get("live_mode"),
            "data_classification": audit_report.get("data_classification"),
            "route": f"{args.origin.upper()}-{args.dest.upper()}",
            "travel_date": travel_date,
            "cabin": "economy",
            "passenger_count": 1,
            "raw_response_sha256": raw_sha256
        }

    # Save separated credential-free artifacts
    meta_file = AUDIT_OUT_DIR / "request_metadata.json"
    raw_file = AUDIT_OUT_DIR / "raw_response.json"

    with open(meta_file, "w", encoding="utf-8") as mf:
        json.dump(metadata, mf, indent=2)

    with open(raw_file, "wb") as rf:
        rf.write(raw_bytes)

    # Print Summary Report
    print("\n--- DUFFEL CONNECTIVITY & RESPONSE AUDIT SUMMARY ---")
    print(f"HTTP Status:            {metadata['http_status']}")
    print(f"Offer Request ID:       {audit_report['offer_request_id']}")
    print(f"Live Mode:              {audit_report['live_mode']}")
    print(f"Data Classification:    {audit_report['data_classification']}")
    print(f"Offers Count:           {audit_report['offers_count']}")
    print(f"Raw Response SHA-256:   {metadata['raw_response_sha256']}")
    print(f"Saved Metadata:         {meta_file}")
    print(f"Saved Raw Response:     {raw_file}")
    print("\n--- COMPONENT AVAILABILITY ---")
    for k, v in audit_report["component_availability"].items():
        print(f"  {k}: {v}")

    if audit_report["offers"]:
        sample = audit_report["offers"][0]
        print("\n--- SANITIZED REPRESENTATIVE OFFER SAMPLE ---")
        print(f"  Offer ID:        {sample['offer_id']}")
        print(f"  Carrier:         {sample['owner_name']} ({sample['owner_code']})")
        print(f"  Total Fare:      {sample['total_amount']} {sample['total_currency']}")
        print(f"  Base Fare:       {sample['base_amount']} {sample['base_currency']}")
        print(f"  Tax Amount:      {sample['tax_amount']} {sample['tax_currency']}")
        print(f"  Expiry:          {sample['expires_at']}")
        if sample["slices"]:
            sl0 = sample["slices"][0]
            print(f"  Slice Duration:  {sl0['duration']}")
            if sl0["segments"]:
                seg0 = sl0["segments"][0]
                print(f"  First Segment:   Flight {seg0['flight_number']} | {seg0['origin_iata']} -> {seg0['destination_iata']} | Dep: {seg0['departing_at']} Arr: {seg0['arriving_at']}")

    print("\nAudit Completed Successfully.")


if __name__ == "__main__":
    main()
