import os
import sys

# Add backend directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import SessionLocal
from app.services.index_engine_service import IndexEngineService

def verify():
    db = SessionLocal()
    try:
        r_daily, _ = IndexEngineService.execute_index_run(db, '2026-08-01', '2026-09-01', frequency='DAILY')
        r_weekly, _ = IndexEngineService.execute_index_run(db, '2026-08-01', '2026-09-01', frequency='WEEKLY')
        r_monthly, _ = IndexEngineService.execute_index_run(db, '2026-08-01', '2026-09-01', frequency='MONTHLY')

        print("==================================================")
        print("     AEROCPI HARDENING VERIFICATION RESULTS      ")
        print("==================================================")
        print(f"DAILY Run ID:     {r_daily.run_id}")
        print(f"DAILY Frequency:  {r_daily.frequency}")
        print(f"DAILY Index Val:  {r_daily.index_value}\n")

        print(f"WEEKLY Run ID:    {r_weekly.run_id}")
        print(f"WEEKLY Frequency: {r_weekly.frequency}")
        print(f"WEEKLY Index Val: {r_weekly.index_value}\n")

        print(f"MONTHLY Run ID:   {r_monthly.run_id}")
        print(f"MONTHLY Freq:     {r_monthly.frequency}")
        print(f"MONTHLY Index Val:{r_monthly.index_value}\n")

        print("ROUTE x HORIZON COVERAGE METRICS:")
        print(f"  Expected Pairs:   {r_monthly.expected_route_horizon_pairs}")
        print(f"  Calculated Pairs: {r_monthly.calculated_route_horizon_pairs}")
        print(f"  Unavailable Pairs:{r_monthly.unavailable_route_horizon_pairs}")

        print("\nQUALITY STATUS BREAKDOWN:")
        print(f"  Valid Observations:               {r_monthly.valid_count}")
        print(f"  Outlier Flagged Observations:     {r_monthly.outlier_flagged_count}")
        print(f"  Retained With Warning:            {r_monthly.retained_with_warning_count}")
        print(f"  Excluded Observations:            {r_monthly.excluded_count}")

        print("\nCALCULATION MANIFEST VERIFICATION:")
        manifest = r_monthly.calculation_manifest
        print(f"  Manifest Frequency:     {manifest['frequency']}")
        print(f"  Total Considered:       {manifest['total_observations_considered']}")
        print(f"  Eligible Used:          {manifest['eligible_observations_used']}")
        print(f"  Canonical Fingerprint:  {r_monthly.canonical_run_fingerprint}")
        print("==================================================")

    finally:
        db.close()

if __name__ == "__main__":
    verify()
