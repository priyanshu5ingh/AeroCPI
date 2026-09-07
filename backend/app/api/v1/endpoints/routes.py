from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.route import Route
from app.schemas.route import RouteResponse

router = APIRouter()

@router.get("/routes", response_model=List[RouteResponse])
def get_routes(db: Session = Depends(get_db)):
    routes = db.query(Route).all()
    return routes
