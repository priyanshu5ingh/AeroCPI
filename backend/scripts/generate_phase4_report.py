import os
import sys
import datetime as dt

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import func
from app.db.session import SessionLocal
from app.models.observation import Observation
from app.models.index_run import IndexRun
from app.services.forecast_dataset_service import ForecastDatasetService
from app.services.model_registry_service import ModelRegistryService

def generate_report():
    db = SessionLocal()
    
    total_obs = db.query(Observation).count()
    eligible_obs = db.query(Observation).filter(Observation.index_eligibility == "ELIGIBLE").count()
    synthetic_obs = db.query(Observation).filter(Observation.capture_method == "SYNTHETIC").count()
    rejected_obs = db.query(Observation).filter(Observation.validation_status == "REJECT").count()
    
    unique_routes = db.query(func.count(func.distinct(Observation.route_id))).scalar()
    unique_travel_dates = db.query(func.count(func.distinct(Observation.travel_date))).scalar()
    unique_search_dates = db.query(func.count(func.distinct(Observation.search_date))).scalar()
    
    source_counts = db.query(Observation.source_id, func.count(Observation.observation_id)).group_by(Observation.source_id).all()
    carrier_counts = db.query(Observation.carrier_id, func.count(Observation.observation_id)).group_by(Observation.carrier_id).all()
    
    examples_7 = ForecastDatasetService.build_examples(db, horizon_days=7)
    examples_14 = ForecastDatasetService.build_examples(db, horizon_days=14)
    
    earliest_obs = db.query(func.min(Observation.search_timestamp)).scalar()
    latest_obs = db.query(func.max(Observation.search_timestamp)).scalar()
    
    latest_index_run = db.query(IndexRun).order_by(IndexRun.run_timestamp.desc()).first()
    index_run_status = "NONE"
    if latest_index_run:
        if hasattr(latest_index_run, "status"):
            index_run_status = getattr(latest_index_run, "status")
        else:
            index_run_status = "PUBLISHED (Implicit)"

    prod_model = ModelRegistryService.load_production()
    model_status = "PROMOTED" if prod_model else "NONE"
    
    print("--- DB METRICS ---")
    print(f"Total Observations: {total_obs}")
    print(f"Eligible Observations: {eligible_obs}")
    print(f"Synthetic Observations: {synthetic_obs}")
    print(f"Rejected Observations: {rejected_obs}")
    print(f"Unique Routes: {unique_routes}")
    print(f"Unique Travel Dates: {unique_travel_dates}")
    print(f"Unique Search Dates: {unique_search_dates}")
    print(f"Sources: {source_counts}")
    print(f"Carriers: {carrier_counts}")
    print(f"7-day pairs: {len(examples_7)}")
    print(f"14-day pairs: {len(examples_14)}")
    print(f"Earliest Obs: {earliest_obs}")
    print(f"Latest Obs: {latest_obs}")
    print(f"Current Index Run Status: {index_run_status}")
    print(f"Production Model Status: {model_status}")

if __name__ == "__main__":
    generate_report()
