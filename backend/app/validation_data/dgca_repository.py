from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import json

from app.models.dgca_reference import DGCAReferenceDataset, DGCARawObservation, DGCARouteMonthObservation, DGCAProvenanceRecord
from app.models.route_basket import RouteBasket, RouteBasketMember
from app.models.city_airport_mapping import CityAirportMapping
from app.validation_data.dgca_schemas import DGCACoverageSummary, DGCARefObservationRecord, RouteBasketRecord, RouteBasketMemberRecord

class DGCARepository:
    def __init__(self, db: Session):
        self.db = db

    def get_dataset(self, dataset_id: str) -> Optional[DGCAReferenceDataset]:
        return self.db.query(DGCAReferenceDataset).filter(DGCAReferenceDataset.dataset_id == dataset_id).first()

    def get_provenance(self, dataset_id: str) -> Optional[DGCAProvenanceRecord]:
        return self.db.query(DGCAProvenanceRecord).filter(DGCAProvenanceRecord.dataset_id == dataset_id).first()

    def get_coverage(self, dataset_id: str = "DS-DGCA-TRAFFIC-2025") -> Optional[DGCACoverageSummary]:
        ds = self.get_dataset(dataset_id)
        if not ds:
            return None
        
        prov = self.get_provenance(dataset_id)

        raw_count = self.db.query(DGCARawObservation).filter(DGCARawObservation.dataset_id == dataset_id).count()
        norm_count = self.db.query(DGCARouteMonthObservation).filter(DGCARouteMonthObservation.dataset_id == dataset_id).count()
        unique_routes = self.db.query(DGCARouteMonthObservation.canonical_route_key).filter(DGCARouteMonthObservation.dataset_id == dataset_id).distinct().count()

        missing_list = json.loads(ds.months_missing) if ds.months_missing else []

        hashes = []
        if prov:
            hashes.append({
                "source_file_sha256": prov.source_file_sha256,
                "canonical_dataset_sha256": prov.canonical_dataset_sha256
            })

        return DGCACoverageSummary(
            publisher=ds.publisher,
            dataset_id=ds.dataset_id,
            reference_period_start=ds.reference_period_start,
            reference_period_end=ds.reference_period_end,
            months_expected=ds.months_expected,
            months_available=ds.months_available,
            months_missing=missing_list,
            completeness_status=ds.completeness_status,
            total_raw_records=raw_count,
            total_normalized_route_months=norm_count,
            unique_routes_count=unique_routes,
            source_files_count=ds.months_available,
            source_hashes=hashes,
            source_status=ds.source_status
        )

    def filter_traffic_observations(
        self,
        dataset_id: str = "DS-DGCA-TRAFFIC-2025",
        year: Optional[int] = None,
        month: Optional[int] = None,
        city: Optional[str] = None,
        route_key: Optional[str] = None,
        limit: int = 100
    ) -> List[DGCARouteMonthObservation]:
        query = self.db.query(DGCARouteMonthObservation).filter(DGCARouteMonthObservation.dataset_id == dataset_id)

        if year:
            query = query.filter(DGCARouteMonthObservation.year == year)
        if month:
            query = query.filter(DGCARouteMonthObservation.month == month)
        if route_key:
            query = query.filter(DGCARouteMonthObservation.canonical_route_key == route_key)
        if city:
            c_upper = city.upper()
            query = query.filter(
                (DGCARouteMonthObservation.city1_code == c_upper) |
                (DGCARouteMonthObservation.city2_code == c_upper) |
                (DGCARouteMonthObservation.origin_airport == c_upper) |
                (DGCARouteMonthObservation.destination_airport == c_upper)
            )

        return query.order_by(DGCARouteMonthObservation.combined_passengers.desc()).limit(limit).all()

    def get_route_basket(self, basket_id: str) -> Optional[RouteBasketRecord]:
        b = self.db.query(RouteBasket).filter(RouteBasket.basket_id == basket_id).first()
        if not b:
            return None
        
        members = (
            self.db.query(RouteBasketMember)
            .filter(RouteBasketMember.basket_id == basket_id)
            .order_by(RouteBasketMember.rank.asc())
            .all()
        )

        member_records = [RouteBasketMemberRecord.model_validate(m) for m in members]

        return RouteBasketRecord(
            basket_id=b.basket_id,
            basket_name=b.basket_name,
            reference_period_type=b.reference_period_type,
            reference_period_start=b.reference_period_start,
            reference_period_end=b.reference_period_end,
            selection_method=b.selection_method,
            basket_size=b.basket_size,
            total_period_passengers=b.total_period_passengers,
            total_all_eligible_routes_passengers=b.total_all_eligible_routes_passengers,
            source_dataset_id=b.source_dataset_id,
            methodology_version=b.methodology_version,
            relationship_to_mospi=b.relationship_to_mospi,
            status=b.status,
            created_at=b.created_at,
            members=member_records
        )
