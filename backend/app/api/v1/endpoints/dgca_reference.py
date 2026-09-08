from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.dgca_basket_service import DGCABasketService
from app.validation_data.dgca_schemas import DGCACoverageSummary, RouteBasketRecord, DGCARefObservationRecord

router = APIRouter()

@router.get("/reference/dgca/coverage", response_model=DGCACoverageSummary)
def get_dgca_traffic_coverage(
    dataset_id: str = "DS-DGCA-TRAFFIC-2025",
    db: Session = Depends(get_db)
):
    """
    Retrieves coverage summary for official DGCA domestic city-pair traffic reference data.
    Exposes months expected vs available, completeness status, file hashes, and dataset source status.
    """
    try:
        coverage = DGCABasketService.get_coverage_summary(db, dataset_id=dataset_id)
        return coverage
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

@router.get("/reference/dgca/basket/{basket_id}", response_model=RouteBasketRecord)
def get_dgca_route_basket(
    basket_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves the AeroCPI DGCA Traffic-Derived Route Basket (e.g. BASKET-DGCA-2025-TOP10).
    Includes member routes, passenger volumes, traffic shares (DGCA_TRAFFIC_PROXY_WEIGHT), and ranks.
    """
    try:
        basket = DGCABasketService.get_route_basket(db, basket_id=basket_id)
        return basket
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

@router.get("/reference/dgca/provenance/{dataset_id}")
def get_dgca_dataset_provenance(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves provenance record for a DGCA traffic reference dataset.
    Maintains strict PROVENANCE_PARTIAL status unless raw file and download URL are verified.
    """
    try:
        prov = DGCABasketService.get_provenance_record(db, dataset_id=dataset_id)
        return prov
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

@router.get("/reference/dgca/traffic", response_model=List[DGCARefObservationRecord])
def get_dgca_traffic_observations(
    year: Optional[int] = Query(None, description="Filter by year (e.g. 2025)"),
    month: Optional[int] = Query(None, description="Filter by month (1 to 12)"),
    city: Optional[str] = Query(None, description="Filter by city code or name (e.g. DELHI, BOM)"),
    route: Optional[str] = Query(None, description="Filter by canonical route key (e.g. DELHI::MUMBAI)"),
    dataset_id: str = "DS-DGCA-TRAFFIC-2025",
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Retrieves normalized, deduplicated DGCA route-month passenger traffic observations.
    Guarantees no double-counting across reverse-direction city pairs.
    """
    obs = DGCABasketService.get_traffic_observations(
        db=db,
        dataset_id=dataset_id,
        year=year,
        month=month,
        city=city,
        route=route,
        limit=limit
    )
    return obs
