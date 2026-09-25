"""AeroCPI Operational Metrics & Alert Governance Service.
Provides live observation growth metrics, longitudinal panel trajectory counts, and operational alerts.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from app.models.observation import Observation
from app.models.collection_orchestration import CollectionRun, CollectionAttempt
from app.models.longitudinal_panel import LongitudinalPanelManifest
from app.services.source_health_service import SourceHealthService
from app.services.forecast_dataset_service import ForecastDatasetService


class OperationalMetricsService:
    """Live database operational metrics and health alert evaluation."""

    @classmethod
    def get_growth_metrics(cls, db: Session) -> Dict[str, Any]:
        now_utc = dt.datetime.now(dt.timezone.utc)
        
        # 1. Total & Filtered Counts
        total_obs = db.query(Observation).count()
        accepted_obs = db.query(Observation).filter(Observation.validation_status == "ACCEPT").count()
        eligible_obs = db.query(Observation).filter(Observation.index_eligibility == "ELIGIBLE").count()
        synthetic_obs = db.query(Observation).filter(Observation.capture_method == "SYNTHETIC").count()

        # 2. Latest Capture Age
        latest_search_ts = db.query(func.max(Observation.search_timestamp)).scalar()
        capture_age_minutes = None
        if latest_search_ts:
            ts = latest_search_ts.replace(tzinfo=dt.timezone.utc) if latest_search_ts.tzinfo is None else latest_search_ts
            capture_age_minutes = round((now_utc - ts).total_seconds() / 60.0, 1)

        # 3. Observations by Day
        by_day_rows = db.query(
            Observation.search_date,
            func.count(Observation.observation_id)
        ).group_by(Observation.search_date).order_by(Observation.search_date.desc()).limit(14).all()
        by_day = [{"date": str(r[0]), "count": r[1]} for r in by_day_rows if r[0]]

        # 4. Observations by Source
        by_src_rows = db.query(
            Observation.source_id,
            func.count(Observation.observation_id)
        ).group_by(Observation.source_id).all()
        by_source = [{"source_id": r[0] or "UNKNOWN", "count": r[1]} for r in by_src_rows]

        # 5. Observations by Route (Top 10)
        by_route_rows = db.query(
            Observation.route_id,
            func.count(Observation.observation_id)
        ).group_by(Observation.route_id).order_by(func.count(Observation.observation_id).desc()).limit(10).all()
        by_route = [{"route_id": r[0] or "UNKNOWN", "count": r[1]} for r in by_route_rows]

        # 6. Distinct Carriers and Routes Coverage
        distinct_routes = db.query(func.count(distinct(Observation.route_id))).scalar() or 0
        distinct_carriers = db.query(func.count(distinct(Observation.carrier_id))).scalar() or 0

        # 7. Longitudinal Trajectories & Pairs (Exact Live DB calculation)
        panel_manifests = db.query(LongitudinalPanelManifest).all()
        total_trajectories = len(panel_manifests)
        trajectories_with_gte_2 = sum(1 for m in panel_manifests if m.search_count >= 2)
        valid_7d_pairs = sum(1 for m in panel_manifests if m.has_7_day_pair)
        valid_14d_pairs = sum(1 for m in panel_manifests if m.has_14_day_pair)

        # Build empirical training dataset examples
        examples = ForecastDatasetService.build_examples(db, horizon_days=7)
        summary = ForecastDatasetService.dataset_summary(examples)

        return {
            "timestamp": now_utc.isoformat(),
            "total_observations": total_obs,
            "accepted_observations": accepted_obs,
            "eligible_observations": eligible_obs,
            "synthetic_observations": synthetic_obs,
            "latest_search_timestamp": latest_search_ts.isoformat() if latest_search_ts else None,
            "latest_capture_age_minutes": capture_age_minutes,
            "distinct_routes_covered": distinct_routes,
            "distinct_carriers_observed": distinct_carriers,
            "observations_by_day": by_day,
            "observations_by_source": by_source,
            "observations_by_route": by_route,
            "panel": {
                "total_trajectories": total_trajectories,
                "trajectories_with_gte_2_observations": trajectories_with_gte_2,
                "valid_7d_pairs": valid_7d_pairs,
                "valid_14d_pairs": valid_14d_pairs,
                "dataset_examples": summary.get("examples", 0),
                "class_counts": summary.get("class_counts", {"up": 0, "stable": 0, "down": 0}),
                "readiness_status": summary.get("readiness_status", "INSUFFICIENT_DATA"),
                "readiness_reasons": summary.get("readiness_reasons", ["INSUFFICIENT_LONGITUDINAL_PAIRS"]),
            }
        }

    @classmethod
    def evaluate_operational_alerts(cls, db: Session) -> List[Dict[str, Any]]:
        """Evaluates deterministic alert conditions without fake health signals."""
        alerts: List[Dict[str, Any]] = []
        now_utc = dt.datetime.now(dt.timezone.utc)
        
        health_data = SourceHealthService.get_source_health_summary(db)
        metrics = cls.get_growth_metrics(db)

        # Alert 1: Capture Stagnation (> 24 hours without accepted observations)
        age = metrics.get("latest_capture_age_minutes")
        if age is not None and age > 1440:
            alerts.append({
                "alert_id": "ALERT_CAPTURE_STALE",
                "severity": "WARNING",
                "title": "Data Capture Stagnation",
                "message": f"Latest observation capture is {age:.0f} minutes old (> 24 hours). Scheduler may be inactive.",
                "triggered_at": now_utc.isoformat()
            })

        # Alert 2: Parser Failure Ratio
        for src in health_data.get("sources", []):
            if src["is_operational"] and src["total_observations"] > 50:
                if src["parser_success_rate_pct"] < 50.0:
                    alerts.append({
                        "alert_id": f"ALERT_PARSER_DEGRADATION_{src['source_id']}",
                        "severity": "CRITICAL",
                        "title": f"Parser Degradation on {src['name']}",
                        "message": f"Parser success rate dropped to {src['parser_success_rate_pct']}%. Check DOM / schema changes.",
                        "triggered_at": now_utc.isoformat()
                    })

        # Alert 3: Longitudinal Readiness Blockers
        panel = metrics.get("panel", {})
        if panel.get("valid_7d_pairs", 0) == 0:
            alerts.append({
                "alert_id": "ALERT_LONGITUDINAL_INSUFFICIENT_HISTORY",
                "severity": "INFO",
                "title": "ML Promotion Blocked: Longitudinal Accumulation Active",
                "message": "0 valid 7-day longitudinal pairs exist in production database. Forecasting remains in honest MODEL_NOT_READY state.",
                "triggered_at": now_utc.isoformat()
            })

        return alerts
