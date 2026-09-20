"""AeroGuide National Collection Orchestrator Service.
Source-independent, quota-driven collection engine with strict failure isolation,
provenance preservation, and longitudinal panel manifest maintenance.
"""
from __future__ import annotations
import os
import time
import uuid
import hashlib
import random
import datetime as dt
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.observation import Observation
from app.models.collection_orchestration import CollectionRun, CollectionAttempt
from app.models.longitudinal_panel import LongitudinalPanelManifest
from app.services.source_adapters.registry import MultiSourceRegistry
from app.services.source_adapters.base import SourceStatus
from app.core.aeroguide_registry import (
    TIER_1_DGCA_CORE,
    TIER_2_NATIONAL_HIGH_TRAFFIC,
    generate_comparability_id
)
from app.services.observation_service import ObservationService
from app.services.canonical_normalization_service import CanonicalNormalizationService
from app.validation.canonical_validation_rules import CanonicalValidationRules
from app.schemas.observation import RawQuoteInput

DEFAULT_PINNED_DATES = [
    "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04",
    "2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08",
    "2026-10-09", "2026-10-10", "2026-10-11", "2026-10-12",
    "2026-10-13", "2026-10-14"
]

CARRIER_BASELINES = {
    "6E": ("IndiGo", 1.00),
    "AI": ("Air India", 1.06),
    "QP": ("Akasa Air", 0.96),
    "SG": ("SpiceJet", 0.94)
}

ROUTE_BASELINES = {
    "DEL-BOM": 6420.0, "BOM-DEL": 6450.0,
    "BLR-DEL": 6880.0, "DEL-BLR": 6850.0,
    "BOM-BLR": 4820.0, "BLR-BOM": 4800.0,
    "DEL-HYD": 5600.0, "HYD-DEL": 5620.0,
    "DEL-CCU": 6120.0, "CCU-DEL": 6100.0,
    "DEL-MAA": 6550.0, "MAA-DEL": 6520.0,
    "BOM-GOI": 3890.0, "GOI-BOM": 3910.0,
    "BLR-HYD": 3450.0, "HYD-BLR": 3440.0,
    "DEL-PAT": 5200.0, "PAT-DEL": 5210.0,
    "BLR-CCU": 6750.0, "CCU-BLR": 6780.0
}


class CollectionOrchestratorService:
    """Orchestrates multi-source queries, collects quotes, isolates failures, and updates panel manifests."""

    @classmethod
    def execute_collection_sweep(
        cls,
        db: Session,
        routes: Optional[List[Tuple[str, str]]] = None,
        travel_dates: Optional[List[str]] = None,
        source_ids: Optional[List[str]] = None,
        run_type: str = "LONGITUDINAL_PANEL",
        search_timestamp: Optional[dt.datetime] = None
    ) -> Dict[str, Any]:
        registry = MultiSourceRegistry.get_instance()
        now_utc = search_timestamp or dt.datetime.now(dt.timezone.utc)
        search_date_val = now_utc.date()
        search_date_str = search_date_val.isoformat()

        target_routes = routes or TIER_1_DGCA_CORE
        target_dates = travel_dates or DEFAULT_PINNED_DATES
        
        # Determine available sources
        if source_ids:
            active_sources = [s for s in source_ids if registry.get_adapter(s)]
        else:
            active_sources = ["SRC_GOOGLE_FLIGHTS"]

        run_id = str(uuid.uuid4())
        coll_run = CollectionRun(
            run_id=run_id,
            run_type=run_type,
            started_at=now_utc,
            routes_attempted=len(target_routes),
            sources_attempted=len(active_sources),
            queries_total=len(target_routes) * len(target_dates) * len(active_sources),
            status="RUNNING"
        )
        db.add(coll_run)
        db.commit()

        queries_success = 0
        queries_failed = 0
        observations_saved = 0
        errors_by_source: Dict[str, List[str]] = {s: [] for s in active_sources}

        for origin, destination in target_routes:
            route_id = f"{origin}-{destination}"
            base_route_fare = ROUTE_BASELINES.get(route_id, 6200.0)

            for t_date_str in target_dates:
                try:
                    t_date = dt.datetime.strptime(t_date_str, "%Y-%m-%d").date()
                except ValueError:
                    continue

                lead_days = (t_date - search_date_val).days
                if lead_days < 0:
                    lead_days = 15

                for s_id in active_sources:
                    adapter = registry.get_adapter(s_id)
                    if not adapter:
                        continue

                    attempt_id = str(uuid.uuid4())
                    t_start = dt.datetime.now(dt.timezone.utc)
                    t0 = time.perf_counter()

                    try:
                        status = adapter.get_status()
                        if status in [SourceStatus.CREDENTIALS_REQUIRED, SourceStatus.PARTNER_ACCESS_REQUIRED]:
                            # Log attempt as credential-gated, never fabricate
                            attempt = CollectionAttempt(
                                attempt_id=attempt_id,
                                run_id=run_id,
                                source_id=s_id,
                                origin=origin,
                                destination=destination,
                                route_id=route_id,
                                travel_date=t_date,
                                apw=lead_days,
                                started_at=t_start,
                                finished_at=dt.datetime.now(dt.timezone.utc),
                                latency_ms=(time.perf_counter() - t0) * 1000.0,
                                status=status.value,
                                error_detail="Source is configured as partner-restricted; credentials not provided in environment.",
                                observations_count=0
                            )
                            db.add(attempt)
                            db.commit()
                            continue

                        # Ingest quotes directly via live Source Adapter
                        quotes_created_for_attempt = 0
                        raw_quotes = adapter.fetch_quotes(
                            origin=origin,
                            destination=destination,
                            travel_date=t_date_str,
                            cabin="ECONOMY",
                            adults=1
                        )

                        for raw_quote in raw_quotes:
                            raw_dict = raw_quote.model_dump() if hasattr(raw_quote, "model_dump") else dict(raw_quote)
                            raw_dict["search_timestamp"] = now_utc.isoformat()
                            raw_dict["search_date"] = search_date_str
                            raw_dict["collected_at"] = now_utc.isoformat()

                            canon_dict = CanonicalNormalizationService.normalize_raw_quote(raw_dict)
                            val_status, val_reasons = CanonicalValidationRules.evaluate_observation(canon_dict)
                            index_elig, index_elig_reasons = CanonicalValidationRules.evaluate_index_eligibility(canon_dict, val_status, val_reasons)

                            adv_days = canon_dict.get("advance_purchase_days")
                            if adv_days is None:
                                adv_days = lead_days
                            horizon_days = adv_days if adv_days is not None and adv_days >= 0 else lead_days

                            ObservationService.ensure_reference_entities(
                                db=db,
                                source_id=canon_dict["source_id"],
                                route_id=canon_dict["route_id"],
                                carrier_id=canon_dict.get("carrier_id") or canon_dict["airline"],
                                horizon_days=horizon_days
                            )

                            obs_id = str(uuid.uuid4())
                            comp_id = generate_comparability_id(
                                origin,
                                destination,
                                t_date_str,
                                canon_dict.get("cabin") or "ECONOMY",
                                canon_dict.get("stops") or 0,
                                canon_dict.get("duration_minutes") or 135
                            )

                            fare_val = float(canon_dict["total_fare"]) if canon_dict.get("total_fare") is not None else 0.0

                            obs = Observation(
                                observation_id=obs_id,
                                source_id=canon_dict["source_id"],
                                source_name=canon_dict.get("source_name") or adapter.display_name,
                                source_url=canon_dict.get("source_url"),
                                search_timestamp=now_utc,
                                search_date=search_date_val,
                                collected_at=now_utc,
                                observed_at=now_utc,
                                travel_date=t_date,
                                advance_purchase_days=adv_days,
                                booking_horizon_days=horizon_days,
                                origin_raw=canon_dict.get("origin_raw") or origin,
                                destination_raw=canon_dict.get("destination_raw") or destination,
                                origin_airport=canon_dict.get("origin_airport") or origin,
                                destination_airport=canon_dict.get("destination_airport") or destination,
                                route_id=canon_dict.get("route_id") or route_id,
                                carrier_id=canon_dict.get("carrier_id") or canon_dict.get("airline", "UNKNOWN"),
                                airline=canon_dict.get("airline", "UNKNOWN"),
                                flight_number=canon_dict.get("flight_number"),
                                cabin=canon_dict.get("cabin") or "ECONOMY",
                                fare_class=canon_dict.get("fare_class") or "STANDARD",
                                trip_type=canon_dict.get("trip_type") or "ONE_WAY",
                                stops=canon_dict.get("stops", 0),
                                stops_status=canon_dict.get("stops_status") or ("OBSERVED_NON_STOP" if canon_dict.get("stops") == 0 else "OBSERVED_STOPS"),
                                duration_minutes=canon_dict.get("duration_minutes") or 135,
                                raw_total_fare=canon_dict.get("raw_total_fare"),
                                raw_base_fare=canon_dict.get("raw_base_fare"),
                                raw_taxes=canon_dict.get("raw_taxes"),
                                raw_fees=canon_dict.get("raw_fees"),
                                base_fare=float(canon_dict["base_fare"]) if canon_dict.get("base_fare") is not None else None,
                                taxes=float(canon_dict["taxes"]) if canon_dict.get("taxes") is not None else None,
                                mandatory_fees=float(canon_dict["fees"]) if canon_dict.get("fees") is not None else None,
                                fees=float(canon_dict["fees"]) if canon_dict.get("fees") is not None else None,
                                total_fare=fare_val,
                                currency=canon_dict.get("currency") or "INR",
                                stop_type="NON_STOP" if (canon_dict.get("stops") == 0 or canon_dict.get("stops") is None) else "ONE_STOP",
                                raw_payload_hash=canon_dict.get("raw_payload_hash"),
                                raw_payload_sha256=canon_dict.get("raw_payload_sha256"),
                                stored_file_sha256=canon_dict.get("stored_file_sha256"),
                                observation_key=canon_dict.get("observation_key"),
                                quote_fingerprint=canon_dict.get("quote_fingerprint"),
                                breakdown_status=canon_dict.get("breakdown_status") or "TOTAL_ONLY",
                                arithmetic_status=canon_dict.get("arithmetic_status") or "ARITHMETIC_UNCHECKABLE",
                                horizon_code=canon_dict.get("horizon_code") or (f"T+{lead_days}" if lead_days in [0, 1, 3, 7, 15, 30] else "OFF_HORIZON"),
                                route_mapping_status=canon_dict.get("route_mapping_status") or "CANONICAL_MAPPED",
                                basket_status=canon_dict.get("basket_status") or "BASKET_MEMBER",
                                validation_status=val_status,
                                validation_reasons=val_reasons,
                                index_eligibility=index_elig,
                                index_eligibility_reasons=index_elig_reasons,
                                data_status="OBSERVED" if val_status != "REJECT" else "REJECTED",
                                collection_run_id=run_id,
                                collection_attempt_id=attempt_id,
                                comparability_id=comp_id,
                                adapter_version=adapter.adapter_version,
                                capture_method="html_fetch:scrapy" if "WEB" in s_id else "API_ORCHESTRATED",
                                source_status_at_capture=status.value,
                                created_at=now_utc
                            )
                            db.add(obs)
                            observations_saved += 1
                            quotes_created_for_attempt += 1

                        queries_success += 1

                        attempt = CollectionAttempt(
                            attempt_id=attempt_id,
                            run_id=run_id,
                            source_id=s_id,
                            origin=origin,
                            destination=destination,
                            route_id=route_id,
                            travel_date=t_date,
                            apw=lead_days,
                            started_at=t_start,
                            finished_at=dt.datetime.now(dt.timezone.utc),
                            latency_ms=(time.perf_counter() - t0) * 1000.0,
                            status="SUCCESS" if quotes_created_for_attempt > 0 else "ZERO_QUOTES_RETURNED",
                            observations_count=quotes_created_for_attempt
                        )
                        db.add(attempt)

                        # Update Longitudinal Panel Manifest for this route × date
                        cls._upsert_panel_manifest(db, route_id, t_date, search_date_str, now_utc, quotes_created_for_attempt)
                        db.commit()
                        print(f"[{queries_success + queries_failed}/{coll_run.queries_total}] {s_id} {route_id} {t_date_str}: {quotes_created_for_attempt} quotes ({time.perf_counter() - t0:.2f}s)", flush=True)

                    except Exception as e:
                        queries_failed += 1
                        err_msg = f"{type(e).__name__}: {str(e)}"
                        errors_by_source[s_id].append(f"{route_id} ({t_date_str}): {err_msg}")
                        print(f"[{queries_success + queries_failed}/{coll_run.queries_total}] FAILED {s_id} {route_id} {t_date_str}: {err_msg[:80]}", flush=True)
                        
                        attempt = CollectionAttempt(
                            attempt_id=attempt_id,
                            run_id=run_id,
                            source_id=s_id,
                            origin=origin,
                            destination=destination,
                            route_id=route_id,
                            travel_date=t_date,
                            apw=lead_days,
                            started_at=t_start,
                            finished_at=dt.datetime.now(dt.timezone.utc),
                            latency_ms=(time.perf_counter() - t0) * 1000.0,
                            status="FAILED",
                            error_class=type(e).__name__,
                            error_detail=err_msg[:500],
                            observations_count=0
                        )
                        db.add(attempt)

        # Finalize run record
        coll_run.finished_at = dt.datetime.now(dt.timezone.utc)
        coll_run.queries_success = queries_success
        coll_run.queries_failed = queries_failed
        coll_run.observations_saved = observations_saved
        coll_run.errors_by_source = errors_by_source
        coll_run.status = "COMPLETED" if queries_failed == 0 else "PARTIAL_SUCCESS"
        db.commit()

        return {
            "run_id": run_id,
            "status": coll_run.status,
            "started_at": coll_run.started_at.isoformat(),
            "finished_at": coll_run.finished_at.isoformat() if coll_run.finished_at else None,
            "routes_attempted": len(target_routes),
            "sources_attempted": len(active_sources),
            "queries_total": coll_run.queries_total,
            "queries_success": queries_success,
            "queries_failed": queries_failed,
            "observations_saved": observations_saved,
            "errors_by_source": errors_by_source
        }

    @classmethod
    def _upsert_panel_manifest(
        cls,
        db: Session,
        route_id: str,
        travel_date: dt.date,
        search_date_str: str,
        now_utc: dt.datetime,
        quotes_count: int
    ):
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
            s_dates = list(manifest.search_dates) if manifest.search_dates else []
            if search_date_str not in s_dates:
                s_dates.append(search_date_str)
                s_dates.sort()
                manifest.search_dates = s_dates
                manifest.search_count = len(s_dates)

            last_obs = manifest.last_observed_at
            if last_obs and last_obs.tzinfo is not None:
                last_obs = last_obs.astimezone(dt.timezone.utc).replace(tzinfo=None)
            first_obs = manifest.first_observed_at
            if first_obs and first_obs.tzinfo is not None:
                first_obs = first_obs.astimezone(dt.timezone.utc).replace(tzinfo=None)
            now_naive = now_utc.astimezone(dt.timezone.utc).replace(tzinfo=None) if now_utc.tzinfo else now_utc

            if last_obs is None or now_naive > last_obs:
                manifest.last_observed_at = now_utc
            if first_obs is None or now_naive < first_obs:
                manifest.first_observed_at = now_utc

            manifest.observation_count = (manifest.observation_count or 0) + quotes_count

            if len(s_dates) >= 2:
                d_min = dt.datetime.strptime(s_dates[0], "%Y-%m-%d").date()
                d_max = dt.datetime.strptime(s_dates[-1], "%Y-%m-%d").date()
                manifest.history_span_days = (d_max - d_min).days

                has_7d = any(
                    (dt.datetime.strptime(d2, "%Y-%m-%d").date() - dt.datetime.strptime(d1, "%Y-%m-%d").date()).days >= 7
                    for i, d1 in enumerate(s_dates)
                    for d2 in s_dates[i+1:]
                )
                has_14d = any(
                    (dt.datetime.strptime(d2, "%Y-%m-%d").date() - dt.datetime.strptime(d1, "%Y-%m-%d").date()).days >= 14
                    for i, d1 in enumerate(s_dates)
                    for d2 in s_dates[i+1:]
                )
                manifest.has_7_day_pair = has_7d
                manifest.has_14_day_pair = has_14d
                manifest.eligible_for_forecasting = has_7d

            manifest.has_3_searches = len(s_dates) >= 3
            manifest.updated_at = now_utc
            db.flush()
