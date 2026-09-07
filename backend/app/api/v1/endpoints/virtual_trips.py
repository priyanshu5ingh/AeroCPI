from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.virtual_trip import VirtualTripCreate, VirtualTripResponse
from app.services.virtual_trip_service import VirtualTripService

router = APIRouter()

@router.post("/virtual-trips", response_model=VirtualTripResponse, status_code=status.HTTP_201_CREATED)
def create_virtual_trip(
    trip_in: VirtualTripCreate,
    db: Session = Depends(get_db)
):
    try:
        trip = VirtualTripService.create_virtual_trip(db=db, trip_data=trip_in)
        return trip
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create virtual trip: {str(e)}")

@router.get("/virtual-trips/{virtual_trip_id}", response_model=VirtualTripResponse)
def get_virtual_trip(
    virtual_trip_id: str,
    db: Session = Depends(get_db)
):
    trip = VirtualTripService.get_virtual_trip_by_id(db=db, spec_id=virtual_trip_id)
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Virtual trip specification '{virtual_trip_id}' not found")
    return trip
