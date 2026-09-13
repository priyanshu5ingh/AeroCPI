from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.measurement_configuration import MeasurementConfiguration
from app.schemas.measurement_configuration import (
    MeasurementConfigurationCreate,
    MeasurementConfigurationSchema,
)
from app.services.measurement_configuration_service import (
    create_measurement_configuration,
    get_measurement_configuration_by_version,
    get_latest_measurement_configuration,
)

router = APIRouter(prefix="/configurations", tags=["Measurement Configurations"])

@router.get("", response_model=List[MeasurementConfigurationSchema])
def list_configurations(db: Session = Depends(get_db)):
    """
    Returns list of all registered measurement configurations.
    """
    return db.query(MeasurementConfiguration).order_by(MeasurementConfiguration.created_at.desc()).all()

@router.get("/latest", response_model=MeasurementConfigurationSchema)
def get_latest_configuration(db: Session = Depends(get_db)):
    """
    Returns the active/latest measurement configuration.
    """
    return get_latest_measurement_configuration(db)

@router.get("/{version}", response_model=MeasurementConfigurationSchema)
def get_configuration_by_version(version: str, db: Session = Depends(get_db)):
    """
    Returns a specific measurement configuration by version identifier.
    """
    config = get_measurement_configuration_by_version(db, version)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Measurement configuration version '{version}' not found",
        )
    return config

@router.post("", response_model=MeasurementConfigurationSchema, status_code=status.HTTP_201_CREATED)
def create_configuration(
    config_in: MeasurementConfigurationCreate, db: Session = Depends(get_db)
):
    """
    Registers a new versioned measurement configuration.
    """
    existing = get_measurement_configuration_by_version(db, config_in.configuration_version)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration version '{config_in.configuration_version}' already exists",
        )
    return create_measurement_configuration(db, config_in)
