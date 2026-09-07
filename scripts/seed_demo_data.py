import os
import sys
import json
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

ROUTES = [
    ("DEL-BOM", "DEL", "BOM"),
    ("BOM-DEL", "BOM", "DEL"),
    ("BLR-DEL", "BLR", "DEL"),
    ("CCU-DEL", "CCU", "DEL"),
    ("DEL-MAA", "DEL", "MAA")
]

CARRIERS = [
    ("6E", "IndiGo"),
    ("AI", "Air India"),
    ("QP", "Akasa Air"),
    ("IX", "Air India Express"),
    ("I5", "AIX Connect")
]

HORIZONS = [1, 7, 15, 30, 45]

SOURCES = [
    ("INDIGO_DIRECT", "IndiGo Direct Public API", "AIRLINE_DIRECT"),
    ("AIRINDIA_DIRECT", "Air India Direct Public API", "AIRLINE_DIRECT"),
    ("MAKE_MY_TRIP", "MakeMyTrip Partner Feed", "OTA_AGGREGATOR"),
    ("SYNTHETIC_SIMULATOR", "AeroCPI Synthetic Airfare Generator", "SYNTHETIC_GENERATOR")
]

def seed_database():
    print("Initializing database tables for demo data seeding...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)
        today = date.today()

        created_obs_count = 0
        raw_samples = []

        print("Seeding Virtual Trip Specifications...")
        for route_id, origin, dest in ROUTES:
            for h in HORIZONS:
                v_trip_in = VirtualTripCreate(
                    origin=origin,
                    destination=dest,
                    travel_date=today + timedelta(days=h),
                    passengers=1,
                    cabin="ECONOMY",
                    trip_type="ONE_WAY",
                    booking_horizon=h,
                    baggage_requirement="15KG_CHECKIN_7KG_CARRYON",
                    eligible_stop_type="NON_STOP"
                )
                VirtualTripService.create_virtual_trip(db, v_trip_in)

        print("Seeding Observations (OBSERVED, FROZEN, SYNTHETIC, DEMO)...")
        for route_id, origin, dest in ROUTES:
            for carrier_id, c_name in CARRIERS:
                for h in HORIZONS:
                    travel_date = today + timedelta(days=h)
                    
                    # Determine base price based on horizon lead time
                    base_price = 3000.0 + (50 - h) * 45.0
                    if carrier_id == "6E":
                        base_price *= 0.95
                    elif carrier_id == "AI":
                        base_price *= 1.05

                    base_fare = round(base_price, 2)
                    taxes = round(base_fare * 0.12, 2)
                    mandatory_fees = 350.0
                    total_fare = round(base_fare + taxes + mandatory_fees, 2)

                    # Determine data status label
                    if h in (7, 15):
                        status = DataStatus.OBSERVED
                        source_id = "INDIGO_DIRECT" if carrier_id == "6E" else "MAKE_MY_TRIP"
                    elif h == 30:
                        status = DataStatus.FROZEN
                        source_id = "AIRINDIA_DIRECT"
                    else:
                        status = DataStatus.DEMO
                        source_id = "SYNTHETIC_SIMULATOR"

                    obs_in = ObservationCreate(
                        source_id=source_id,
                        route_id=route_id,
                        carrier_id=carrier_id,
                        travel_date=travel_date,
                        observed_at=now,
                        booking_horizon_days=h,
                        cabin="ECONOMY",
                        base_fare=base_fare,
                        taxes=taxes,
                        mandatory_fees=mandatory_fees,
                        total_fare=total_fare,
                        currency="INR",
                        data_status=status,
                        baggage_information={"checkin_kg": 15, "carryon_kg": 7},
                        raw_reference=f"RAW-QUOTE-{route_id}-{carrier_id}-T{h}"
                    )

                    obs = ObservationService.create_observation(db, obs_in)
                    created_obs_count += 1

                    raw_samples.append({
                        "observation_id": obs.observation_id,
                        "route_id": route_id,
                        "carrier_id": carrier_id,
                        "booking_horizon_days": h,
                        "travel_date": str(travel_date),
                        "total_fare": total_fare,
                        "data_status": status.value,
                        "disclaimer": "Integration Demo Data - Not Official MoSPI Statistics"
                    })

        print(f"Successfully seeded {created_obs_count} demo observations into database.")

        # Export sample JSON files to data/demo and data/raw
        os.makedirs("data/demo", exist_ok=True)
        os.makedirs("data/raw", exist_ok=True)

        with open("data/demo/seed_demo_observations.json", "w") as f:
            json.dump(raw_samples, f, indent=2)

        with open("data/raw/raw_sample_quotes.json", "w") as f:
            json.dump(raw_samples[:10], f, indent=2)

        print("Exported data/demo/seed_demo_observations.json and data/raw/raw_sample_quotes.json.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
