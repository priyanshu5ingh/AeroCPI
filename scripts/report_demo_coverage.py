import os
import sys
from datetime import datetime, timezone

# Add backend directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import SessionLocal
from app.models.observation import Observation
from app.services.quality_engine_service import QualityEngineService

def generate_demo_coverage_report(db=None):
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        all_obs = db.query(Observation).order_by(Observation.observation_id).all()
        if not all_obs:
            print("No observations found in database. Please run scripts/seed_demo_data.py first.")
            return

        quality_results = QualityEngineService.evaluate_observation_batch(db, all_obs)
        qr_map = {qr.observation_id: qr for qr in quality_results}

        ref_obs = [
            o for o in all_obs
            if (o.observed_at and str(o.observed_at).startswith("2026-08")) or
               (o.raw_reference and "2026-08-01" in o.raw_reference) or
               (str(o.travel_date).startswith("2026-08"))
        ]
        comp_obs = [
            o for o in all_obs
            if (o.observed_at and str(o.observed_at).startswith("2026-09")) or
               (o.raw_reference and "2026-09-01" in o.raw_reference) or
               (str(o.travel_date).startswith("2026-09"))
        ]

        routes = sorted(list(set(o.route_id for o in all_obs)))
        horizons = [1, 7, 15, 30, 45]

        ref_groups = {}
        comp_groups = {}

        for o in ref_obs:
            qr = qr_map.get(o.observation_id)
            if qr and qr.eligible:
                ref_groups.setdefault((o.route_id, o.booking_horizon_days), []).append(o)

        for o in comp_obs:
            qr = qr_map.get(o.observation_id)
            if qr and qr.eligible:
                comp_groups.setdefault((o.route_id, o.booking_horizon_days), []).append(o)

        print("\n==================================================")
        print("     AEROCPI DEMO DATASET COVERAGE REPORT        ")
        print("==================================================")
        print(f"Total Observations Considered:     {len(all_obs)}")
        print(f"Reference Period Observations:     {len(ref_obs)}")
        print(f"Comparison Period Observations:    {len(comp_obs)}")
        print(f"Total Eligible Observations:       {sum(1 for qr in quality_results if qr.eligible)}")
        print(f"Total Excluded Observations:       {sum(1 for qr in quality_results if not qr.eligible)}")
        print(f"Unique Routes Tracked:             {len(routes)}")
        print(f"Lead-Time Horizons Tracked:        {horizons}")

        print("\nRoute-Horizon Availability Matrix (Grid):")
        print("-" * 55)
        header = f"{'Route':<12}" + "".join([f"T+{h:<8}" for h in horizons])
        print(header)
        print("-" * 55)

        total_pairs = len(routes) * len(horizons)
        available_pairs = 0

        for r in routes:
            row = f"{r:<12}"
            for h in horizons:
                ref_count = len(ref_groups.get((r, h), []))
                comp_count = len(comp_groups.get((r, h), []))
                if ref_count > 0 and comp_count > 0:
                    row += f"{'[OK]':<9}"
                    available_pairs += 1
                else:
                    row += f"{'[--]':<9}"
            print(row)

        print("-" * 55)
        print(f"Available Route-Horizon Pairs: {available_pairs} / {total_pairs} ({(available_pairs/total_pairs)*100:.1f}% Coverage)")
        print("==================================================\n")

    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    generate_demo_coverage_report()
