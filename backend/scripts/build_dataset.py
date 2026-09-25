import argparse
import datetime as dt
import hashlib
import json
import logging
import os
from typing import Any, Dict, List

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.forecast_dataset_service import ForecastDatasetService
from app.services.production_data_policy import ProductionDataPolicy
from app.models.observation import Observation
from app.services.forecasting_engine_service import ForecastingEngineService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_dataset_and_manifest():
    db = SessionLocal()
    try:
        # 1. Total observations before filtering
        total_obs = db.query(Observation).count()
        
        # 2. Extract eligible examples via ForecastDatasetService
        examples = ForecastDatasetService.build_examples(db, horizon_days=7)
        
        # Manifest calculations
        eligible_obs = ForecastDatasetService.load_observations(db)
        eligible_count = len(eligible_obs)
        excluded_count = total_obs - eligible_count
        
        unique_routes = set(e["route_id"] for e in examples)
        unique_travel_dates = set(e["travel_date"] for e in examples)
        unique_search_dates = set(e["prediction_date"] for e in examples)
        
        # Distribution
        up_count = sum(1 for e in examples if e["target_direction"] == "UP")
        down_count = sum(1 for e in examples if e["target_direction"] == "DOWN")
        stable_count = sum(1 for e in examples if e["target_direction"] == "STABLE")
        
        # Readiness checks based on user's phase 2 rules
        readiness_reasons = []
        if len(examples) < 50:
            readiness_reasons.append("Insufficient total examples (requires >= 50)")
        if len(unique_routes) < 5:
            readiness_reasons.append("Insufficient route diversity (requires >= 5)")
        if len(unique_travel_dates) < 5:
            readiness_reasons.append("Insufficient travel-date diversity (requires >= 5)")
        if not (up_count > 5 and down_count > 5 and stable_count > 5):
            readiness_reasons.append("Insufficient class diversity (requires > 5 in each class)")
            
        prediction_dates = sorted(list(unique_search_dates))
        if len(prediction_dates) >= 2:
            earliest = dt.date.fromisoformat(prediction_dates[0])
            latest = dt.date.fromisoformat(prediction_dates[-1])
            temporal_coverage_days = (latest - earliest).days
            if temporal_coverage_days < 7:
                readiness_reasons.append(f"Insufficient temporal coverage ({temporal_coverage_days} days, requires >= 7)")
                has_holdout = False
            else:
                has_holdout = True
        else:
            earliest = None
            latest = None
            temporal_coverage_days = 0
            readiness_reasons.append("Insufficient temporal coverage (requires >= 7 days)")
            has_holdout = False

        status = "READY" if not readiness_reasons else "INSUFFICIENT_DATA"
        
        dataset_content = json.dumps(examples, sort_keys=True).encode('utf-8')
        dataset_sha256 = hashlib.sha256(dataset_content).hexdigest()
        
        manifest = {
            "dataset_row_count": len(examples),
            "total_observations_scanned": total_obs,
            "eligible_observation_count": eligible_count,
            "excluded_observation_count": excluded_count,
            "exclusion_reasons": ["SYNTHETIC", "NOT_ACCEPTED", "INELIGIBLE"],
            "unique_routes": len(unique_routes),
            "unique_travel_dates": len(unique_travel_dates),
            "unique_search_dates": len(unique_search_dates),
            "up_count": up_count,
            "stable_count": stable_count,
            "down_count": down_count,
            "earliest_prediction_timestamp": prediction_dates[0] if prediction_dates else None,
            "latest_prediction_timestamp": prediction_dates[-1] if prediction_dates else None,
            "7_day_pair_count": len(examples),
            "dataset_version": "V1",
            "feature_schema_version": "AEROGUIDE_FEATURES_V2",
            "production_eligibility_policy_version": "V1",
            "fingerprint_sha256": dataset_sha256,
            "readiness_status": status,
            "readiness_reasons": readiness_reasons,
            "temporal_coverage_days": temporal_coverage_days,
            "temporal_holdout_exists": has_holdout
        }
        
        # Save to disk
        out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "datasets")
        os.makedirs(out_dir, exist_ok=True)
        
        with open(os.path.join(out_dir, "dataset_manifest.json"), "w") as f:
            json.dump(manifest, f, indent=2)
            
        with open(os.path.join(out_dir, "dataset.json"), "w") as f:
            json.dump(examples, f, indent=2)
            
        logger.info(f"Dataset generated. Rows: {len(examples)}. Status: {status}")
        return manifest
        
    finally:
        db.close()

if __name__ == "__main__":
    m = build_dataset_and_manifest()
    print("=== SUMMARY ===")
    print(json.dumps(m, indent=2))
