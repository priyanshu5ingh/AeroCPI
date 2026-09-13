import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.observation_quality import ObservationQuality
from app.schemas.observation_quality import ObservationQualityCreate, ObservationQualityProfileSchema

def compute_quality_fingerprint(
    observation_id: str,
    completeness_status: str,
    timestamp_status: str,
    fare_integrity_status: str,
    route_mapping_status: str,
    duplicate_risk: str,
    anomaly_flags: List[str],
    source_health_status: str,
    quality_rule_version: str,
) -> str:
    """
    Computes deterministic SHA-256 fingerprint from decomposed observation quality states.
    """
    sorted_flags = sorted(anomaly_flags)
    canonical_payload = {
        "anomaly_flags": sorted_flags,
        "completeness_status": completeness_status,
        "duplicate_risk": duplicate_risk,
        "fare_integrity_status": fare_integrity_status,
        "observation_id": observation_id,
        "quality_rule_version": quality_rule_version,
        "route_mapping_status": route_mapping_status,
        "source_health_status": source_health_status,
        "timestamp_status": timestamp_status,
    }
    encoded = json.dumps(canonical_payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def evaluate_observation_quality(
    observation: Dict[str, Any],
    quality_rule_version: str = "QR-2026.1"
) -> ObservationQualityCreate:
    """
    Evaluates decomposed diagnostic quality states for a given observation record.
    Avoids arbitrary 0-100 confidence scoring.
    """
    obs_id = str(observation.get("id") or observation.get("observation_id") or "unspecified")
    total_fare = observation.get("price") or observation.get("total_fare") or observation.get("fare")
    
    # 1. Fare Integrity
    if total_fare is None or total_fare <= 0:
        fare_status = "ZERO_OR_NEGATIVE"
    else:
        fare_status = "VALID"

    # 2. Completeness
    origin = observation.get("origin") or observation.get("origin_code")
    dest = observation.get("destination") or observation.get("destination_code")
    dep_time = observation.get("departure_time") or observation.get("observed_departure_time")
    
    if origin and dest and dep_time and total_fare is not None:
        completeness = "COMPLETE"
    elif origin or dest or total_fare is not None:
        completeness = "PARTIAL"
    else:
        completeness = "MISSING_FIELDS"

    # 3. Route Mapping
    if origin and dest:
        route_status = "MAPPED"
    elif not origin:
        route_status = "UNMAPPED_ORIGIN"
    else:
        route_status = "UNMAPPED_DEST"

    # 4. Anomaly Flags & Duplicate Risk
    flags: List[str] = []
    if fare_status != "VALID":
        flags.append("INVALID_FARE_VALUE")
    if completeness != "COMPLETE":
        flags.append("INCOMPLETE_OBSERVATION")
    
    is_duplicate = observation.get("is_duplicate", False)
    duplicate_risk = "HIGH_DUPLICATE_KEY" if is_duplicate else "LOW"

    return ObservationQualityCreate(
        observation_id=obs_id,
        completeness_status=completeness,
        timestamp_status="VALID",
        fare_integrity_status=fare_status,
        route_mapping_status=route_status,
        duplicate_risk=duplicate_risk,
        anomaly_flags=flags,
        source_health_status="HEALTHY",
        quality_rule_version=quality_rule_version,
    )

def create_observation_quality_record(
    db: Session, quality_in: ObservationQualityCreate
) -> ObservationQuality:
    fingerprint = compute_quality_fingerprint(
        observation_id=quality_in.observation_id,
        completeness_status=quality_in.completeness_status,
        timestamp_status=quality_in.timestamp_status,
        fare_integrity_status=quality_in.fare_integrity_status,
        route_mapping_status=quality_in.route_mapping_status,
        duplicate_risk=quality_in.duplicate_risk,
        anomaly_flags=quality_in.anomaly_flags,
        source_health_status=quality_in.source_health_status,
        quality_rule_version=quality_in.quality_rule_version,
    )

    now = datetime.now(timezone.utc)
    db_obj = ObservationQuality(
        observation_id=quality_in.observation_id,
        completeness_status=quality_in.completeness_status,
        timestamp_status=quality_in.timestamp_status,
        fare_integrity_status=quality_in.fare_integrity_status,
        route_mapping_status=quality_in.route_mapping_status,
        duplicate_risk=quality_in.duplicate_risk,
        anomaly_flags=quality_in.anomaly_flags,
        source_health_status=quality_in.source_health_status,
        quality_rule_version=quality_in.quality_rule_version,
        quality_fingerprint=fingerprint,
        created_at=now,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
