import os
import sys
import json
import random
from datetime import date, datetime, timedelta, timezone

# Add backend directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import SessionLocal, engine
from app.models import Base
from app.schemas.observation import ObservationCreate
from app.schemas.common import DataStatus
from app.services.observation_service import ObservationService
from app.services.virtual_trip_service import VirtualTripService
from app.schemas.virtual_trip import VirtualTripCreate
from app.services.proxy_weight_service import ProxyWeightService

ROUTES = [
    ("DEL-BOM", "DEL", "BOM"),
    ("BOM-DEL", "BOM", "DEL"),
    ("DEL-BLR", "DEL", "BLR"),
    ("BLR-DEL", "BLR", "DEL"),
    ("BOM-BLR", "BOM", "BLR"),
    ("DEL-CCU", "DEL", "CCU"),
    ("BLR-HYD", "BLR", "HYD"),
    ("MAA-DEL", "MAA", "DEL")
]

CARRIERS = [
    ("6E", "IndiGo"),
    ("AI", "Air India"),
    ("QP", "Akasa Air"),
    ("IX", "Air India Express"),
    ("I5", "AIX Connect")
]

HORIZONS = [1, 7, 15, 30, 45]

PERIODS = [
    ("2026-08-01", date(2026, 8, 1), 1.00), # Reference Period (Base)
    ("2026-09-01", date(2026, 9, 1), 1.08)  # Comparison Period (+8% average market price shift)
]

def seed_database(db=None):
    close_db = False
    if db is None:
        print("Initializing database tables for Milestone 2 demo data seeding...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        close_db = True

    # Deterministic random seed
    random.seed(42)

    try:
        now = datetime.now(timezone.utc)

        print("1. Seeding DGCA-Derived Proxy Route Weights...")
        ProxyWeightService.seed_demo_proxy_weights(db)

        print("2. Seeding Virtual Trip Specifications...")
        for route_id, origin, dest in ROUTES:
            for h in HORIZONS:
                v_trip_in = VirtualTripCreate(
                    origin=origin,
                    destination=dest,
                    travel_date=date(2026, 9, 1) + timedelta(days=h),
                    passengers=1,
                    cabin="ECONOMY",
                    trip_type="ONE_WAY",
                    booking_horizon=h,
                    baggage_requirement="15KG_CHECKIN_7KG_CARRYON",
                    eligible_stop_type="NON_STOP"
                )
                VirtualTripService.create_virtual_trip(db, v_trip_in)

        print("3. Seeding Observations for Reference (2026-08-01) and Comparison (2026-09-01) periods...")
        created_obs_count = 0
        raw_samples = []

        for period_str, base_date, price_multiplier in PERIODS:
            for route_id, origin, dest in ROUTES:
                for carrier_id, c_name in CARRIERS:
                    for h in HORIZONS:
                        travel_date = base_date + timedelta(days=h)
                        
                        # Deterministic price generation
                        base_val = 3500.0 + (45 - h) * 40.0 + random.uniform(-100, 100)
                        if carrier_id == "6E":
                            base_val *= 0.95
                        elif carrier_id == "AI":
                            base_val *= 1.05

                        # Apply period market multiplier (+8% for comparison period)
                        base_val *= price_multiplier

                        base_fare = round(base_val, 2)
                        taxes = round(base_fare * 0.12, 2)
                        mandatory_fees = 350.0
                        total_fare = round(base_fare + taxes + mandatory_fees, 2)

                        # Data status mapping
                        if period_str == "2026-08-01":
                            status = DataStatus.FROZEN
                            source_id = "INDIGO_DIRECT" if carrier_id == "6E" else "MAKE_MY_TRIP"
                        else:
                            status = DataStatus.OBSERVED if h in (7, 15, 30) else DataStatus.DEMO
                            source_id = "AIRINDIA_DIRECT" if carrier_id == "AI" else "SYNTHETIC_SIMULATOR"

                        obs_in = ObservationCreate(
                            source_id=source_id,
                            route_id=route_id,
                            carrier_id=carrier_id,
                            travel_date=travel_date,
                            observed_at=datetime.combine(base_date, datetime.min.time(), tzinfo=timezone.utc),
                            booking_horizon_days=h,
                            cabin="ECONOMY",
                            base_fare=base_fare,
                            taxes=taxes,
                            mandatory_fees=mandatory_fees,
                            total_fare=total_fare,
                            currency="INR",
                            data_status=status,
                            baggage_information={"checkin_kg": 15, "carryon_kg": 7},
                            raw_reference=f"QUOTE-{period_str}-{route_id}-{carrier_id}-T{h}"
                        )

                        obs = ObservationService.create_observation(db, obs_in)
                        created_obs_count += 1

                        raw_samples.append({
                            "observation_id": obs.observation_id,
                            "period": period_str,
                            "route_id": route_id,
                            "carrier_id": carrier_id,
                            "booking_horizon_days": h,
                            "travel_date": str(travel_date),
                            "total_fare": total_fare,
                            "data_status": status.value,
                            "disclaimer": "Experimental Demo Data - Not Official MoSPI Statistics"
                        })

        print(f"Successfully seeded {created_obs_count} demo observations into database.")

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        demo_dir = os.path.join(base_dir, "data", "demo")
        raw_dir = os.path.join(base_dir, "data", "raw")
        os.makedirs(demo_dir, exist_ok=True)
        os.makedirs(raw_dir, exist_ok=True)

        with open(os.path.join(demo_dir, "seed_demo_observations.json"), "w", encoding="utf-8") as f:
            json.dump(raw_samples, f, indent=2)

        with open(os.path.join(raw_dir, "raw_sample_quotes.json"), "w", encoding="utf-8") as f:
            json.dump(raw_samples[:10], f, indent=2)

        print("Exported data/demo/seed_demo_observations.json and data/raw/raw_sample_quotes.json.")

    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    seed_database()
