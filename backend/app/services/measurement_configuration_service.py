import hashlib
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.measurement_configuration import MeasurementConfiguration
from app.schemas.measurement_configuration import MeasurementConfigurationCreate, MeasurementConfigurationSchema

DEFAULT_HORIZONS = ["T+1", "T+7", "T+15", "T+30", "T+45"]

def compute_configuration_fingerprint(
    configuration_version: str,
    basket_version: str,
    horizon_set: List[str],
    validation_rule_version: str,
    outlier_rule_version: str,
    source_policy_version: str,
    aggregation_version: str,
    publication_threshold_version: str,
) -> str:
    """
    Computes a deterministic SHA-256 fingerprint from measurement configuration parameters.
    """
    sorted_horizons = sorted(horizon_set)
    canonical_payload = {
        "aggregation_version": aggregation_version,
        "basket_version": basket_version,
        "configuration_version": configuration_version,
        "horizon_set": sorted_horizons,
        "outlier_rule_version": outlier_rule_version,
        "publication_threshold_version": publication_threshold_version,
        "source_policy_version": source_policy_version,
        "validation_rule_version": validation_rule_version,
    }
    encoded = json.dumps(canonical_payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def create_measurement_configuration(
    db: Session, config_in: MeasurementConfigurationCreate
) -> MeasurementConfiguration:
    fingerprint = compute_configuration_fingerprint(
        configuration_version=config_in.configuration_version,
        basket_version=config_in.basket_version,
        horizon_set=config_in.horizon_set,
        validation_rule_version=config_in.validation_rule_version,
        outlier_rule_version=config_in.outlier_rule_version,
        source_policy_version=config_in.source_policy_version,
        aggregation_version=config_in.aggregation_version,
        publication_threshold_version=config_in.publication_threshold_version,
    )
    
    now = datetime.now(timezone.utc)
    db_obj = MeasurementConfiguration(
        configuration_version=config_in.configuration_version,
        basket_version=config_in.basket_version,
        horizon_set=config_in.horizon_set,
        validation_rule_version=config_in.validation_rule_version,
        outlier_rule_version=config_in.outlier_rule_version,
        source_policy_version=config_in.source_policy_version,
        aggregation_version=config_in.aggregation_version,
        publication_threshold_version=config_in.publication_threshold_version,
        effective_from=config_in.effective_from or now,
        effective_to=config_in.effective_to,
        configuration_fingerprint=fingerprint,
        created_at=now,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_measurement_configuration_by_version(
    db: Session, version: str
) -> Optional[MeasurementConfiguration]:
    return db.query(MeasurementConfiguration).filter(
        MeasurementConfiguration.configuration_version == version
    ).first()

def get_latest_measurement_configuration(
    db: Session
) -> MeasurementConfiguration:
    config = db.query(MeasurementConfiguration).order_by(
        MeasurementConfiguration.created_at.desc()
    ).first()

    if not config:
        # Create default initial configuration
        default_in = MeasurementConfigurationCreate(
            configuration_version="2026.1.0-default",
            basket_version="DGCA-10-2026.1",
            horizon_set=DEFAULT_HORIZONS,
            validation_rule_version="VAL-2026.1",
            outlier_rule_version="IQR-1.5-v1",
            source_policy_version="MULTI-SOURCE-V1",
            aggregation_version="JEVONS-GEOMETRIC-V1",
            publication_threshold_version="PUB-THRESH-V1",
        )
        config = create_measurement_configuration(db, default_in)

    return config
