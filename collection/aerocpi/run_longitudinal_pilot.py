"""AeroGuide Longitudinal Collection Pilot CLI.
Executes a persistent fixed-travel-date panel collection run across 10 DGCA Core Corridors x 14 Pinned Travel Dates.
Records observations, manifests, source health, and target readiness.
"""
import os
import sys
import json
import pathlib
import datetime as dt

# Set up paths
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal
from app.services.longitudinal_service import (
    execute_longitudinal_pilot_collection,
    calculate_readiness_metrics,
    DEFAULT_PINNED_TRAVEL_DATES
)
from app.core.aeroguide_registry import TIER_1_DGCA_CORE

def main():
    print("=" * 70)
    print(" AEROGUIDE — LONGITUDINAL COLLECTION PILOT RUNNER")
    print("=" * 70)
    print(f"Execution Timestamp (UTC): {dt.datetime.now(dt.timezone.utc).isoformat()}")
    print(f"Tier-1 Route Count:       {len(TIER_1_DGCA_CORE)} routes")
    print(f"Pinned Travel Dates:       {len(DEFAULT_PINNED_TRAVEL_DATES)} dates ({DEFAULT_PINNED_TRAVEL_DATES[0]} to {DEFAULT_PINNED_TRAVEL_DATES[-1]})")
    print(f"Search Contract:           1 Adult, Economy, One-Way, INR")
    print("-" * 70)
    
    db = SessionLocal()
    try:
        # Pre-collection metrics
        pre_metrics = calculate_readiness_metrics(db)
        print(f"Pre-Collection Total Observations:  {pre_metrics['total_observations']:,}")
        print(f"Pre-Collection 7-Day Target Pairs:   {pre_metrics['seven_day_target_pairs']}")
        print(f"Pre-Collection Model Status:         {pre_metrics['model_training_status']}")
        print("-" * 70)
        
        # Execute Pilot Collection Run
        print("Executing collection queries across all route x pinned date pairs...")
        result = execute_longitudinal_pilot_collection(db)
        
        print("\nCOLLECTION RUN MANIFEST:")
        print(f"  Run ID:                {result['run_id']}")
        print(f"  Status:                {result['run_status']}")
        print(f"  Queries Requested:     {result['queries_requested']}")
        print(f"  Queries Successful:    {result['queries_successful']}")
        print(f"  Queries Failed:        {result['queries_failed']}")
        print(f"  Observations Created:  {result['observations_created']}")
        print(f"  Raw Payloads Preserved:{result['raw_payload_count']}")
        print("-" * 70)
        
        # Post-collection metrics
        post_metrics = calculate_readiness_metrics(db)
        print("POST-COLLECTION EMPIRICAL READINESS REPORT:")
        print(f"  Total Observations:          {post_metrics['total_observations']:,}")
        print(f"  Unique Routes Monitored:     {post_metrics['unique_routes']}")
        print(f"  Unique Travel Dates:         {post_metrics['unique_travel_dates']}")
        print(f"  Unique Search Dates:         {post_metrics['unique_search_dates']}")
        print(f"  Tracked Trajectories:        {post_metrics['longitudinal_pairs_count']}")
        print(f"  Repeated Trajectories (>=2): {post_metrics['repeated_trajectories']}")
        print(f"  >=3-Search Trajectories:     {post_metrics['trajectories_with_gte_3_searches']}")
        print(f"  7-Day Target Pairs:          {post_metrics['seven_day_target_pairs']}")
        print(f"  14-Day Target Pairs:         {post_metrics['fourteen_day_target_pairs']}")
        print(f"  Longest History Span:        {post_metrics['longest_history_days']} days")
        print(f"  Dataset Classification:      {post_metrics['dataset_classification']}")
        print(f"  Model Training Status:       {post_metrics['model_training_status']}")
        print("=" * 70)
        
        # Save run manifest to data/out
        out_dir = REPO_ROOT / "data" / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = out_dir / f"longitudinal_pilot_manifest_{result['run_id'][:8]}.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump({
                "collection_run": result,
                "readiness_after_run": post_metrics
            }, f, indent=2)
        print(f"Run manifest saved to: {manifest_file}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
