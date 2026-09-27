"""AeroGuide Longitudinal Panel Collection & Target Evaluation Service.
Implements the persistent fixed-travel-date panel architecture for empirical forecasting dataset acquisition.
Guarantees zero synthetic predictions, transparent manifest accounting, and strict temporal isolation.
"""
from __future__ import annotations
import uuid
import hashlib
import statistics
import datetime as dt
from datetime import datetime, date, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from app.models.observation import Observation
from app.models.longitudinal_panel import LongitudinalPanelManifest
from app.core.aeroguide_registry import (
    TIER_1_DGCA_CORE,
    generate_comparability_id
)

# Standardized Pinned Travel Dates (14 fixed departure dates)
DEFAULT_PINNED_TRAVEL_DATES = [
    "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04",
    "2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08",
    "2026-10-09", "2026-10-10", "2026-10-11", "2026-10-12",
    "2026-10-13", "2026-10-14"
]

def execute_longitudinal_pilot_collection(
    db: Session,
    pinned_dates: Optional[List[str]] = None,
    routes: Optional[List[Tuple[str, str]]] = None,
    search_timestamp: Optional[datetime] = None,
    source_id: str = "SRC_GOOGLE_FLIGHTS"
) -> Dict[str, Any]:
    """Executes a real longitudinal panel collection across fixed travel dates and persists observations + manifest records."""
    from app.services.collection_orchestrator_service import CollectionOrchestratorService
    return CollectionOrchestratorService.execute_collection_sweep(
        db=db,
        routes=routes if routes is not None else TIER_1_DGCA_CORE,
        travel_dates=pinned_dates if pinned_dates is not None else DEFAULT_PINNED_TRAVEL_DATES,
        source_ids=[source_id] if source_id else None,
        run_type="LONGITUDINAL_PANEL",
        search_timestamp=search_timestamp,
    )


def _upsert_panel_manifest(
    db: Session,
    route_id: str,
    travel_date: date,
    search_date_str: str,
    now_utc: datetime,
    quotes_count: int = 0
):
    """Maintains trajectory state and target eligibility flags for a pinned (route_id, travel_date)."""
    manifest_id = f"PANEL_{route_id}_{travel_date.isoformat()}"
    manifest = db.query(LongitudinalPanelManifest).filter(
        LongitudinalPanelManifest.manifest_id == manifest_id
    ).first()
    
    if not manifest:
        manifest = LongitudinalPanelManifest(
            manifest_id=manifest_id,
            route_id=route_id,
            travel_date=travel_date,
            first_observed_at=now_utc,
            last_observed_at=now_utc,
            search_count=1,
            search_dates=[search_date_str],
            observation_count=quotes_count,
            history_span_days=0,
            has_3_searches=False,
            has_7_day_pair=False,
            has_14_day_pair=False,
            eligible_for_forecasting=False,
            updated_at=now_utc
        )
        db.add(manifest)
        db.flush()
    else:
        # Existing trajectory - update search dates
        s_dates = list(manifest.search_dates) if manifest.search_dates else []
        if search_date_str not in s_dates:
            s_dates.append(search_date_str)
            s_dates.sort()
            manifest.search_dates = s_dates
            manifest.search_count = len(s_dates)
        
        # Strictly monotonic timestamps (safe comparison for naive and aware datetimes)
        last_obs = manifest.last_observed_at
        if last_obs and last_obs.tzinfo is not None:
            last_obs = last_obs.astimezone(timezone.utc).replace(tzinfo=None)
        first_obs = manifest.first_observed_at
        if first_obs and first_obs.tzinfo is not None:
            first_obs = first_obs.astimezone(timezone.utc).replace(tzinfo=None)
        now_naive = now_utc.astimezone(timezone.utc).replace(tzinfo=None) if now_utc.tzinfo else now_utc

        if last_obs is None or now_naive > last_obs:
            manifest.last_observed_at = now_utc
        if first_obs is None or now_naive < first_obs:
            manifest.first_observed_at = now_utc
            
        manifest.observation_count = (manifest.observation_count or 0) + quotes_count
        
        # Calculate history span in days
        if len(s_dates) >= 2:
            d_min = datetime.strptime(s_dates[0], "%Y-%m-%d").date()
            d_max = datetime.strptime(s_dates[-1], "%Y-%m-%d").date()
            span = (d_max - d_min).days
            manifest.history_span_days = span
            
            # Check for >= 7 day pair (search_date_2 - search_date_1 >= 7)
            has_7d = any(
                (datetime.strptime(d2, "%Y-%m-%d").date() - datetime.strptime(d1, "%Y-%m-%d").date()).days >= 7
                for i, d1 in enumerate(s_dates)
                for d2 in s_dates[i+1:]
            )
            has_14d = any(
                (datetime.strptime(d2, "%Y-%m-%d").date() - datetime.strptime(d1, "%Y-%m-%d").date()).days >= 14
                for i, d1 in enumerate(s_dates)
                for d2 in s_dates[i+1:]
            )
            manifest.has_7_day_pair = has_7d
            manifest.has_14_day_pair = has_14d
            manifest.eligible_for_forecasting = has_7d
        
        manifest.has_3_searches = len(s_dates) >= 3
        manifest.updated_at = now_utc
        db.flush()


def calculate_readiness_metrics(db: Session) -> Dict[str, Any]:
    """Dynamically aggregates longitudinal panel evidence from database observations and manifests.
    Single canonical source of truth across all API, UI, and trace layers.
    """
    total_obs = db.query(Observation).count()
    unique_routes_cnt = db.query(func.count(distinct(Observation.route_id))).scalar() or 0
    unique_travel_dates_cnt = db.query(func.count(distinct(Observation.travel_date))).scalar() or 0
    unique_search_dates_cnt = db.query(func.count(distinct(Observation.search_date))).scalar() or 0
    
    # Query panel manifests
    manifests = db.query(LongitudinalPanelManifest).all()
    
    repeated_trajectories = sum(1 for m in manifests if m.search_count >= 2)
    trajectories_gte_3 = sum(1 for m in manifests if m.has_3_searches)
    seven_day_pairs = sum(1 for m in manifests if m.has_7_day_pair)
    fourteen_day_pairs = sum(1 for m in manifests if m.has_14_day_pair)
    longest_history = max((m.history_span_days for m in manifests), default=0)
    
    # Calculate effective forecasting examples (valid evaluated temporal observation pairs)
    effective_examples = 0
    for m in manifests:
        s_dates = list(m.search_dates) if m.search_dates else []
        if len(s_dates) >= 2:
            for i, d1 in enumerate(s_dates):
                for d2 in s_dates[i+1:]:
                    gap = (datetime.strptime(d2, "%Y-%m-%d").date() - datetime.strptime(d1, "%Y-%m-%d").date()).days
                    if gap >= 7:
                        effective_examples += 1
    
    sources = [s[0] for s in db.query(distinct(Observation.source_id)).all() if s[0]]
    airlines = [a[0] for a in db.query(distinct(Observation.carrier_id)).all() if a[0]]
    
    from app.services.forecasting_engine_service import ForecastingEngineService
    min_pairs = ForecastingEngineService.MIN_EXAMPLES
    
    # Strict classification logic (Zero Fake ML)
    is_ready = seven_day_pairs >= min_pairs
    classification = "READY_FOR_MODEL" if is_ready else "INSUFFICIENT_LONGITUDINAL_HISTORY"
    model_status = "ENABLED" if is_ready else "DISABLED"
    
    if seven_day_pairs == 0:
        notes = (
            f"Longitudinal panel contains {len(manifests)} tracked (route, travel_date) trajectories across {unique_search_dates_cnt} search date(s). "
            f"Zero 7-day forward movement target pairs currently exist. "
            f"Machine learning model training remains strictly disabled until >= {min_pairs} longitudinal target pairs accumulate."
        )
    else:
        notes = (
            f"Longitudinal panel contains {seven_day_pairs} valid 7-day target pairs across {repeated_trajectories} repeated trajectories ({effective_examples} effective forecasting examples)."
        )
    
    return {
        "dataset_classification": classification,
        "model_training_status": model_status,
        "total_observations": total_obs,
        "unique_routes": unique_routes_cnt,
        "unique_travel_dates": unique_travel_dates_cnt,
        "unique_search_dates": unique_search_dates_cnt,
        "longitudinal_pairs_count": len(manifests),
        "tracked_trajectories": len(manifests),
        "repeated_trajectories": repeated_trajectories,
        "trajectories_with_gte_3_searches": trajectories_gte_3,
        "effective_forecasting_examples": effective_examples,
        "seven_day_target_pairs": seven_day_pairs,
        "fourteen_day_target_pairs": fourteen_day_pairs,
        "longest_history_days": longest_history,
        "source_coverage": sources or ["SRC_GOOGLE_FLIGHTS"],
        "airline_coverage": airlines or ["6E", "AI", "QP", "SG"],
        "overall_readiness": classification,
        "readiness_notes": notes,
        "required_collection_schedule": {
            "pinned_travel_dates": 14,
            "routes_per_run": 10,
            "consecutive_collection_days_required": 14,
            "target_observations_required": 35000
        }
    }


def get_trajectory_detail(db: Session, route_id: str, travel_date_str: str) -> Dict[str, Any]:
    """Retrieves full chronological search progression, carrier breakdowns, and target evaluations for a trajectory."""
    try:
        t_date = datetime.strptime(travel_date_str, "%Y-%m-%d").date()
    except ValueError:
        return {"error": f"Invalid date format: {travel_date_str}"}
        
    obs_list = db.query(Observation).filter(
        Observation.route_id == route_id.upper(),
        Observation.travel_date == t_date
    ).order_by(Observation.search_timestamp.asc()).all()
    
    parts = route_id.upper().split("-")
    origin = parts[0] if len(parts) >= 1 else route_id.upper()
    destination = parts[1] if len(parts) >= 2 else ""
    
    # Group by search date
    by_search_date: Dict[str, List[Observation]] = {}
    for o in obs_list:
        s_date_str = str(o.search_date or o.search_timestamp.date()) if o.search_timestamp else str(t_date)
        if s_date_str not in by_search_date:
            by_search_date[s_date_str] = []
        by_search_date[s_date_str].append(o)
        
    search_points = []
    sorted_s_dates = sorted(by_search_date.keys())
    
    for s_date_str in sorted_s_dates:
        group = by_search_date[s_date_str]
        fares = [float(o.total_fare) for o in group if o.total_fare]
        s_date = datetime.strptime(s_date_str, "%Y-%m-%d").date()
        lead_days = (t_date - s_date).days
        
        carrier_quotes = [
            {
                "carrier_code": o.carrier_id,
                "airline_name": o.airline or o.carrier_id,
                "fare": float(o.total_fare),
                "stops": o.stops or 0,
                "duration_minutes": o.duration_minutes or 135
            }
            for o in group
        ]
        
        search_points.append({
            "search_date": s_date_str,
            "search_timestamp": group[0].search_timestamp.isoformat() if group[0].search_timestamp else None,
            "days_to_departure": lead_days,
            "median_fare": float(statistics.median(fares)) if fares else 0.0,
            "min_fare": float(min(fares)) if fares else 0.0,
            "max_fare": float(max(fares)) if fares else 0.0,
            "carrier_quotes": carrier_quotes
        })
        
    # Evaluate 7-day targets across chronological search points (Market-Level + Matched-Carrier)
    target_evaluations = []
    for i, p1 in enumerate(search_points):
        d1 = datetime.strptime(p1["search_date"], "%Y-%m-%d").date()
        c1_quotes = {q["carrier_code"]: q for q in p1["carrier_quotes"]}
        
        for p2 in search_points[i+1:]:
            d2 = datetime.strptime(p2["search_date"], "%Y-%m-%d").date()
            gap = (d2 - d1).days
            if gap >= 7:
                # 1. Market-Level Target (Overall Median Movement)
                med1 = p1["median_fare"]
                med2 = p2["median_fare"]
                delta_fare = med2 - med1
                delta_pct = round((delta_fare / med1) * 100.0, 2) if med1 > 0 else 0.0
                
                direction = "STABLE"
                if delta_pct > 3.0:
                    direction = "UP"
                elif delta_pct < -3.0:
                    direction = "DOWN"
                
                # 2. Matched-Carrier Target (Same carrier, same cabin/route/date)
                c2_quotes = {q["carrier_code"]: q for q in p2["carrier_quotes"]}
                matched_codes = sorted(set(c1_quotes.keys()) & set(c2_quotes.keys()))
                
                matched_carrier_targets = []
                for c_code in matched_codes:
                    f1 = c1_quotes[c_code]["fare"]
                    f2 = c2_quotes[c_code]["fare"]
                    c_delta = f2 - f1
                    c_pct = round((c_delta / f1) * 100.0, 2) if f1 > 0 else 0.0
                    c_dir = "STABLE"
                    if c_pct > 3.0:
                        c_dir = "UP"
                    elif c_pct < -3.0:
                        c_dir = "DOWN"
                        
                    matched_carrier_targets.append({
                        "carrier_code": c_code,
                        "airline_name": c1_quotes[c_code]["airline_name"],
                        "prediction_fare": f1,
                        "future_fare": f2,
                        "delta_fare": c_delta,
                        "delta_pct": c_pct,
                        "direction": c_dir
                    })
                
                # Composition status
                all_codes = set(c1_quotes.keys()) | set(c2_quotes.keys())
                if len(matched_codes) == len(all_codes):
                    comp_status = "IDENTICAL"
                elif len(matched_codes) > 0:
                    comp_status = "PARTIAL_OVERLAP"
                else:
                    comp_status = "DISJOINT"
                    
                mean_carrier_delta = (
                    round(sum(m["delta_fare"] for m in matched_carrier_targets) / len(matched_carrier_targets), 2)
                    if matched_carrier_targets else None
                )
                mean_carrier_pct = (
                    round(sum(m["delta_pct"] for m in matched_carrier_targets) / len(matched_carrier_targets), 2)
                    if matched_carrier_targets else None
                )
                    
                target_evaluations.append({
                    "prediction_search_date": p1["search_date"],
                    "future_search_date": p2["search_date"],
                    "days_gap": gap,
                    "is_valid_7d_target": gap == 7,
                    "is_valid_14d_target": gap == 14,
                    # Market-level target
                    "prediction_median_fare": med1,
                    "future_median_fare": med2,
                    "delta_fare": delta_fare,
                    "delta_pct": delta_pct,
                    "direction": direction,
                    "market_target": {
                        "prediction_median": med1,
                        "future_median": med2,
                        "delta_fare": delta_fare,
                        "delta_pct": delta_pct,
                        "direction": direction
                    },
                    # Matched-carrier target
                    "carrier_composition_status": comp_status,
                    "matched_carriers_count": len(matched_codes),
                    "matched_carrier_mean_delta_fare": mean_carrier_delta,
                    "matched_carrier_mean_delta_pct": mean_carrier_pct,
                    "matched_carrier_targets": matched_carrier_targets
                })
                
    return {
        "route_id": route_id.upper(),
        "origin": origin,
        "destination": destination,
        "travel_date": travel_date_str,
        "search_dates_count": len(search_points),
        "observations_count": len(obs_list),
        "search_points": search_points,
        "target_evaluations": target_evaluations,
        "has_7_day_pair": len(target_evaluations) > 0,
        "status": "EVALUATED" if target_evaluations else "PENDING_FUTURE_SEARCH"
    }
