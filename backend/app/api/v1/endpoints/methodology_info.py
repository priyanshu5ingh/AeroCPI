from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.methodology_info import MethodologyInfoResponse
from app.services.measurement_configuration_service import (
    get_latest_measurement_configuration,
    get_measurement_configuration_by_version,
)

router = APIRouter(prefix="/methodology", tags=["Methodology Studio"])

HUMAN_DESCRIPTIONS = {
    "basket_version": "DGCA 10 Top Indian Domestic Routes Basket based on annual passenger traffic",
    "horizon_set": "5 Advance Purchase Booking Windows: T+1 (Spot), T+7 (1 Wk), T+15 (Headline 2 Wks), T+30 (1 Mo), T+45 (6 Wks)",
    "validation_rule_version": "Structural Validation Rule Suite V1 (Cabin Y-class, Non-stop priority, INR currency)",
    "outlier_rule_version": "Interquartile Range (IQR 1.5x) Outlier Detection Engine",
    "source_policy_version": "Multi-Source Agreement & Aggregation Policy",
    "aggregation_version": "Weighted Geometric National Aggregation with Active Weight Renormalization",
    "publication_threshold_version": "Minimum 80% Basket Coverage & 85% Active Weight Sum Publication Threshold",
}

@router.get("/current", response_model=MethodologyInfoResponse)
def get_current_methodology_configuration(db: Session = Depends(get_db)):
    """
    Returns the active measurement configuration with human-readable descriptions.
    """
    config = get_latest_measurement_configuration(db)
    return MethodologyInfoResponse(
        configuration_version=config.configuration_version,
        configuration_fingerprint=config.configuration_fingerprint,
        basket_version=config.basket_version,
        horizon_set=config.horizon_set,
        validation_rule_version=config.validation_rule_version,
        outlier_rule_version=config.outlier_rule_version,
        source_policy_version=config.source_policy_version,
        aggregation_version=config.aggregation_version,
        publication_threshold_version=config.publication_threshold_version,
        effective_from=config.effective_from,
        effective_to=config.effective_to,
        human_descriptions=HUMAN_DESCRIPTIONS,
    )

@router.get("/{configuration_version}", response_model=MethodologyInfoResponse)
def get_methodology_configuration_by_version(
    configuration_version: str, db: Session = Depends(get_db)
):
    """
    Returns a specific measurement configuration version with human-readable descriptions.
    """
    config = get_measurement_configuration_by_version(db, configuration_version)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Methodology configuration version '{configuration_version}' not found",
        )
    return MethodologyInfoResponse(
        configuration_version=config.configuration_version,
        configuration_fingerprint=config.configuration_fingerprint,
        basket_version=config.basket_version,
        horizon_set=config.horizon_set,
        validation_rule_version=config.validation_rule_version,
        outlier_rule_version=config.outlier_rule_version,
        source_policy_version=config.source_policy_version,
        aggregation_version=config.aggregation_version,
        publication_threshold_version=config.publication_threshold_version,
        effective_from=config.effective_from,
        effective_to=config.effective_to,
        human_descriptions=HUMAN_DESCRIPTIONS,
    )
