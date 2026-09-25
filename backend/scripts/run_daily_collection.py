"""AeroCPI Production Daily Collection Scheduler.
Executes deterministic collection sweeps across configured routes and dates with process lock protection.

Invocation on Operating System:
- Windows Task Scheduler:
    Action: Start a program
    Program: C:\\Users\\priya\\Downloads\\AeroCPI\\backend\\.venv\\Scripts\\python.exe
    Arguments: C:\\Users\\priya\\Downloads\\AeroCPI\\backend\\scripts\\run_daily_collection.py
    Schedule: Daily at 02:00 UTC (07:30 IST)

- Linux / POSIX cron:
    0 2 * * * cd /opt/aerocpi/backend && ./venv/bin/python scripts/run_daily_collection.py >> /var/log/aerocpi/scheduler.log 2>&1
"""
from __future__ import annotations

import os
import sys
import time
import atexit
import argparse
import datetime as dt
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.services.collection_orchestrator_service import CollectionOrchestratorService
from app.config.collection import ACTIVE_PRODUCTION_ROUTES, PINNED_LONGITUDINAL_DATES, SOURCE_DEFINITIONS

LOCK_FILE = Path(__file__).resolve().parent / ".collector.lock"


def acquire_process_lock() -> bool:
    """Acquires an exclusive PID lock file to prevent overlapping collection sweeps."""
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            # Check if process is still running (Windows & POSIX)
            if os.name == "nt":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(1, False, pid)
                if handle != 0:
                    kernel32.CloseHandle(handle)
                    return False
            else:
                os.kill(pid, 0)
                return False
        except (ValueError, OSError):
            pass  # Stale lock file, safe to claim

    LOCK_FILE.write_text(str(os.getpid()))
    return True


def release_process_lock():
    """Removes the process lock file."""
    if LOCK_FILE.exists():
        try:
            LOCK_FILE.unlink()
        except OSError:
            pass


atexit.register(release_process_lock)


def run_scheduler(dry_run: bool = False, sources: list[str] | None = None) -> int:
    print(f"[{dt.datetime.now(dt.timezone.utc).isoformat()}] AeroCPI Production Collection Scheduler Initializing...", flush=True)

    if not acquire_process_lock():
        print(f"[ERROR] Another collection sweep is currently executing (Lock: {LOCK_FILE}). Aborting to prevent overlap.", file=sys.stderr)
        return 2

    active_sources = [s_id for s_id, spec in SOURCE_DEFINITIONS.items() if spec["is_operational"]]
    target_sources = sources or active_sources

    print(f"Target Routes: {len(ACTIVE_PRODUCTION_ROUTES)} corridors")
    print(f"Target Dates: {len(PINNED_LONGITUDINAL_DATES)} pinned departure dates")
    print(f"Configured Sources: {list(SOURCE_DEFINITIONS.keys())}")
    print(f"Active Operational Sources: {active_sources}")
    print(f"Sweep Sources: {target_sources}")

    db = SessionLocal()
    try:
        res = CollectionOrchestratorService.execute_collection_sweep(
            db=db,
            routes=ACTIVE_PRODUCTION_ROUTES,
            travel_dates=PINNED_LONGITUDINAL_DATES,
            source_ids=target_sources,
            run_type="DAILY_OPERATIONAL_SWEEP"
        )

        print("\n=== SWEEP EXECUTION TELEMETRY ===")
        print(f"Run ID: {res['run_id']}")
        print(f"Status: {res['status']}")
        print(f"Total Queries: {res['queries_total']}")
        print(f"Successful Queries: {res['queries_success']}")
        print(f"Failed Queries: {res['queries_failed']}")
        print(f"Observations Saved: {res['observations_saved']}")
        
        if res.get("errors_by_source"):
            for s_id, errs in res["errors_by_source"].items():
                if errs:
                    print(f"  [Errors on {s_id}]: {len(errs)} failures (Latest: {errs[-1][:100]})")

        return 0 if res["status"] in ["COMPLETED", "PARTIAL_SUCCESS"] else 1

    except Exception as exc:
        print(f"[FATAL] Scheduler encountered uncaught exception: {type(exc).__name__}: {str(exc)}", file=sys.stderr)
        return 1
    finally:
        db.close()
        release_process_lock()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AeroCPI Daily Collection Scheduler")
    parser.add_argument("--dry-run", action="store_true", help="Run without persisting to DB")
    parser.add_argument("--sources", nargs="+", help="Explicit source IDs to execute")
    args = parser.parse_args()

    exit_code = run_scheduler(dry_run=args.dry_run, sources=args.sources)
    sys.exit(exit_code)
