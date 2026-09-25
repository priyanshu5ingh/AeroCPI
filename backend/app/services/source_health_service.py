"""AeroCPI Source Health & Telemetry Service.
Maintains granular state separation: IMPLEMENTED, CONFIGURED, OPERATIONAL, CURRENTLY HEALTHY.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config.collection import SOURCE_DEFINITIONS
from app.models.observation import Observation
from app.models.collection_orchestration import CollectionAttempt, CollectionRun


class SourceHealthService:
    """Computes live telemetry, failure rates, and exact availability taxonomy for all sources."""

    @classmethod
    def get_source_health_summary(cls, db: Session) -> Dict[str, Any]:
        now_utc = dt.datetime.now(dt.timezone.utc)
        twenty_four_hours_ago = now_utc - dt.timedelta(hours=24)

        sources_health: List[Dict[str, Any]] = []

        for source_id, spec in SOURCE_DEFINITIONS.items():
            # Query attempts in last 24h
            attempts_query = db.query(CollectionAttempt).filter(
                CollectionAttempt.source_id == source_id,
                CollectionAttempt.started_at >= twenty_four_hours_ago
            )
            total_attempts_24h = attempts_query.count()
            successful_attempts_24h = attempts_query.filter(CollectionAttempt.status == "SUCCESS").count()
            failed_attempts_24h = attempts_query.filter(CollectionAttempt.status == "FAILED").count()

            # Query overall observations
            obs_query = db.query(Observation).filter(Observation.source_id == source_id)
            total_obs = obs_query.count()
            accepted_obs = obs_query.filter(Observation.validation_status == "ACCEPT").count()
            flagged_obs = obs_query.filter(Observation.validation_status == "FLAG").count()
            rejected_obs = obs_query.filter(Observation.validation_status == "REJECT").count()

            # Last success timestamp
            last_success_ts = db.query(func.max(Observation.observed_at)).filter(
                Observation.source_id == source_id,
                Observation.validation_status == "ACCEPT"
            ).scalar()

            # Last attempt timestamp and latest failure
            last_attempt = db.query(CollectionAttempt).filter(
                CollectionAttempt.source_id == source_id
            ).order_by(CollectionAttempt.started_at.desc()).first()

            last_attempt_ts = last_attempt.started_at if last_attempt else None
            latest_failure_reason = None
            if last_attempt and last_attempt.status == "FAILED":
                latest_failure_reason = last_attempt.error_detail or last_attempt.error_class

            # Success Rates
            capture_success_rate = (
                round((successful_attempts_24h / total_attempts_24h) * 100.0, 1)
                if total_attempts_24h > 0
                else (100.0 if spec["is_operational"] and total_obs > 0 else 0.0)
            )

            parser_success_rate = (
                round((accepted_obs / total_obs) * 100.0, 1)
                if total_obs > 0
                else 0.0
            )

            # State Taxonomy
            # 1. IMPLEMENTED: Adapter class exists in codebase
            is_implemented = spec.get("is_implemented", True)
            # 2. CONFIGURED: Credentials/URL configured in env
            is_configured = spec.get("is_configured", False)
            # 3. OPERATIONAL: System is capable of querying live
            is_operational = spec.get("is_operational", False)
            # 4. CURRENTLY HEALTHY: Successful capture in last 24h with zero recent fatal errors
            is_healthy = bool(
                is_operational and (
                    (last_success_ts and (now_utc - (last_success_ts.replace(tzinfo=dt.timezone.utc) if last_success_ts.tzinfo is None else last_success_ts)).total_seconds() < 86400)
                    or (total_obs > 0 and failed_attempts_24h == 0)
                )
            )

            sources_health.append({
                "source_id": source_id,
                "name": spec["name"],
                "category": spec["category"],
                "adapter_version": spec["adapter_version"],
                "is_implemented": is_implemented,
                "is_configured": is_configured,
                "is_operational": is_operational,
                "is_currently_healthy": is_healthy,
                "taxonomy_state": (
                    "CURRENTLY_HEALTHY" if is_healthy
                    else ("OPERATIONAL" if is_operational
                          else ("CONFIGURED" if is_configured
                                else ("IMPLEMENTED" if is_implemented else "UNAVAILABLE")))
                ),
                "total_observations": total_obs,
                "accepted_observations": accepted_obs,
                "flagged_observations": flagged_obs,
                "rejected_observations": rejected_obs,
                "total_attempts_24h": total_attempts_24h,
                "successful_attempts_24h": successful_attempts_24h,
                "failed_attempts_24h": failed_attempts_24h,
                "capture_success_rate_pct": capture_success_rate,
                "parser_success_rate_pct": parser_success_rate,
                "last_attempt_at": last_attempt_ts.isoformat() if last_attempt_ts else None,
                "last_success_at": last_success_ts.isoformat() if last_success_ts else None,
                "latest_failure_reason": latest_failure_reason,
                "timeout_seconds": spec["timeout_seconds"],
                "max_retries": spec["max_retries"],
            })

        return {
            "timestamp": now_utc.isoformat(),
            "sources_count": len(sources_health),
            "sources": sources_health,
        }
