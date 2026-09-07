from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.carrier import Carrier
from app.schemas.carrier import CarrierResponse

router = APIRouter()

@router.get("/carriers", response_model=List[CarrierResponse])
def get_carriers(db: Session = Depends(get_db)):
    carriers = db.query(Carrier).all()
    return carriers
