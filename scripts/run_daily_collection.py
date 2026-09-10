"""
AeroCPI Live Collection CLI Runner & Scheduler Script
Usage:
  Manual Single Route Test (Dry-run):
    python scripts/run_daily_collection.py --manual --origin DEL --dest BOM --apw 15 --dry-run

  Manual Single Route Real Collection & Ingestion:
    python scripts/run_daily_collection.py --manual --origin DEL --dest BOM --apw 15

  Manual Full Sweep (10 Basket Routes x 5 Production APWs):
    python scripts/run_daily_collection.py --manual --full-sweep

  Scheduled Execution (Windows Task Scheduler Entry Point):
    python scripts/run_daily_collection.py --scheduled
"""
import sys
import os
import argparse
import pathlib
from datetime import datetime, timezone

# Ensure backend directory is in sys.path
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal
from app.services.live_collector_service import (
    LiveCollectorService,
    DEFAULT_BASKET_ROUTES,
    PRODUCTION_APW_SET
)

def main():
    parser = argparse.ArgumentParser(description="AeroCPI Live Fare Observation Collector")
    parser.add_argument("--manual", action="store_true", help="Execute manual collection run")
    parser.add_argument("--scheduled", action="store_true", help="Execute scheduled daily collection sweep")
    parser.add_argument("--full-sweep", action="store_true", help="Run full sweep over all 10 basket routes x 5 production APWs")
    parser.add_argument("--origin", type=str, default="DEL", help="Origin IATA code (e.g. DEL)")
    parser.add_argument("--dest", type=str, default="BOM", help="Destination IATA code (e.g. BOM)")
    parser.add_argument("--apw", type=int, default=15, help="Advance purchase window days (1, 7, 15, 30, 45)")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and parse quotes without ingesting into database")

    args = parser.parse_args()

    if not args.manual and not args.scheduled:
        print("Please specify either --manual or --scheduled. Run with --help for options.")
        sys.exit(1)

    db = SessionLocal() if not args.dry_run else None

    try:
        if args.full_sweep or args.scheduled:
            print("Executing Full Daily Collection Sweep over 10 Basket Routes x 5 Production APWs...")
            result = LiveCollectorService.execute_daily_collection_sweep(
                db=db,
                routes=DEFAULT_BASKET_ROUTES,
                apws=PRODUCTION_APW_SET,
                dry_run=args.dry_run
            )
            print("Sweep Summary:", result)
        else:
            print(f"Executing Single Collection: {args.origin}-{args.dest} APW{args.apw:02d} (Dry-run: {args.dry_run})...")
            rows, raw_path, digest, status = LiveCollectorService.collect_single_route(
                origin=args.origin,
                dest=args.dest,
                apw=args.apw,
                cabin="ECONOMY",
                dry_run=args.dry_run,
                db=db
            )
            print(f"Status: {status}")
            print(f"SUCCESS: Collected {len(rows)} quotes for {args.origin}-{args.dest} APW{args.apw:02d}")
            print(f"Raw capture file: {raw_path}")
            print(f"Uncompressed Raw SHA-256: {digest}")
            if rows:
                safe_airline = str(rows[0]['airline']).encode('ascii', 'ignore').decode('ascii')
                print(f"Sample Quote: {rows[0]['origin_raw']} -> {rows[0]['destination_raw']} INR {rows[0]['total_fare']} ({safe_airline})")

    except Exception as e:
        print(f"ERROR: Collection failed: {type(e).__name__}: {str(e)}")
        sys.exit(1)
    finally:
        if db is not None:
            db.close()

if __name__ == "__main__":
    main()
