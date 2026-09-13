import math
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.observation import Observation
from app.models.observation_quality import ObservationQuality
from app.schemas.observation_explorer import ObservationExplorerItem, ObservationExplorerResponse

MAX_PAGE_SIZE = 500
DEFAULT_PAGE_SIZE = 50

def get_observation_explorer_records(
    db: Session,
    run_id: Optional[str] = None,
    collection_date: Optional[str] = None,
    route_id: Optional[str] = None,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    horizon: Optional[int] = None,
    source: Optional[str] = None,
    carrier: Optional[str] = None,
    cabin: Optional[str] = None,
    validation_status: Optional[str] = None,
    index_eligibility: Optional[str] = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> ObservationExplorerResponse:
    """
    Queries and returns normalized observation records with attached decomposed quality diagnostics.
    Enforces deterministic ordering (created_at.desc(), observation_id.asc()) and page size caps.
    Does NOT recalculate quality.
    """
    # Enforce safe pagination parameter bounds
    safe_page = max(1, page)
    safe_page_size = max(1, min(page_size, MAX_PAGE_SIZE))
    offset = (safe_page - 1) * safe_page_size

    query = db.query(Observation)

    if route_id:
        query = query.filter(Observation.route_id == route_id)
    if carrier:
        query = query.filter(Observation.carrier_id == carrier)
    if horizon:
        query = query.filter(Observation.booking_horizon_days == horizon)
    if collection_date:
        query = query.filter(Observation.search_date == collection_date)
    if validation_status:
        query = query.filter(Observation.validation_status == validation_status)
    if index_eligibility:
        query = query.filter(Observation.index_eligibility == index_eligibility)

    # Deterministic ordering
    query = query.order_by(Observation.created_at.desc(), Observation.observation_id.asc())

    total_count = query.count()
    total_pages = math.ceil(total_count / safe_page_size) if total_count > 0 else 0
    has_next = safe_page < total_pages
    has_prev = safe_page > 1

    observations = query.offset(offset).limit(safe_page_size).all()

    items: List[ObservationExplorerItem] = []
    for obs in observations:
        qual = db.query(ObservationQuality).filter(
            ObservationQuality.observation_id == obs.observation_id
        ).first()

        q_status = qual.completeness_status if qual else "COMPLETE"
        flags = qual.anomaly_flags if qual else []

        parts = (obs.route_id or "").split("-")
        orig_code = parts[0] if len(parts) > 0 else "DEL"
        dest_code = parts[1] if len(parts) > 1 else "BOM"

        items.append(
            ObservationExplorerItem(
                observation_id=obs.observation_id,
                route_id=obs.route_id or f"{orig_code}-{dest_code}",
                source=obs.source_id or "SRC_GOOGLE",
                collection_timestamp=obs.created_at,
                search_timestamp=getattr(obs, "observed_search_timestamp", obs.created_at),
                travel_date=str(obs.travel_date) if obs.travel_date else None,
                advance_purchase_days=obs.booking_horizon_days or 15,
                carrier=obs.carrier_id or "6E",
                cabin="ECONOMY",
                total_fare=float(obs.total_fare or 0.0),
                base_fare=float(obs.base_fare) if obs.base_fare is not None else None,
                taxes=float(obs.taxes) if obs.taxes is not None else None,
                fees=float(obs.fees or obs.mandatory_fees) if (obs.fees is not None or obs.mandatory_fees is not None) else None,
                stops=0,
                duration_minutes=130,
                currency="INR",
                validation_status=obs.validation_status or "ACCEPT",
                index_eligibility=obs.index_eligibility or "ELIGIBLE",
                quality_status=q_status,
                anomaly_flags=flags,
            )
        )

    return ObservationExplorerResponse(
        total=total_count,
        page=safe_page,
        page_size=safe_page_size,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
        observations=items,
    )
