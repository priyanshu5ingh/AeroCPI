import os
import sys
import datetime as dt

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import func
from app.db.session import SessionLocal
from app.models.observation import Observation
from app.services.forecast_dataset_service import ForecastDatasetService
from app.services.model_registry_service import ModelRegistryService

def generate_report():
    db = SessionLocal()
    
    # 1. Real-Data Observability (Today)
    now = dt.datetime.now(dt.timezone.utc)
    today = now.date()
    
    today_obs = db.query(Observation).filter(Observation.search_date == today)
    collected_today = today_obs.count()
    accepted_today = today_obs.filter(Observation.validation_status == "ACCEPT").count()
    rejected_today = today_obs.filter(Observation.validation_status == "REJECT").count()
    # duplicates is trickier in this schema, we can proxy it if needed
    
    # 2. Source Health
    # We query the DB for actual sources
    sources = db.query(Observation.source_id).distinct().all()
    source_stats = []
    
    for (src,) in sources:
        src_obs = db.query(Observation).filter(Observation.source_id == src)
        total = src_obs.count()
        accepted = src_obs.filter(Observation.validation_status == "ACCEPT").count()
        failed = src_obs.filter(Observation.validation_status == "REJECT").count()
        last_success = db.query(func.max(Observation.search_timestamp)).filter(
            Observation.source_id == src, Observation.validation_status == "ACCEPT"
        ).scalar()
        source_stats.append({
            "source": src,
            "accepted": accepted,
            "parser_failures": failed,
            "last_success": last_success.strftime("%H:%M") if last_success else "--"
        })
        
    print("SOURCE                  LAST SUCCESS    ACCEPTED   PARSER FAILURES")
    for s in source_stats:
        print(f"{s['source']:<23} {s['last_success']:<15} {s['accepted']:<10} {s['parser_failures']}")
    
    print("Duffel                  unavailable     0          --")
    print("IndiGo NDC              unavailable     0          --")
    print("Air India NDC           unavailable     0          --")

if __name__ == "__main__":
    generate_report()
