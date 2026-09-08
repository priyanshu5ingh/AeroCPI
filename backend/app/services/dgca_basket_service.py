from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.validation_data.dgca_repository import DGCARepository
from app.validation_data.dgca_schemas import DGCACoverageSummary, RouteBasketRecord, DGCARefObservationRecord

class DGCABasketService:
    @staticmethod
    def get_coverage_summary(db: Session, dataset_id: str = "DS-DGCA-TRAFFIC-2025") -> DGCACoverageSummary:
        repo = DGCARepository(db)
        coverage = repo.get_coverage(dataset_id=dataset_id)
        if not coverage:
            raise ValueError(f"DGCA Reference Dataset '{dataset_id}' not found.")
        return coverage

    @staticmethod
    def get_route_basket(db: Session, basket_id: str = "BASKET-DGCA-2025-TOP10") -> RouteBasketRecord:
        repo = DGCARepository(db)
        basket = repo.get_route_basket(basket_id=basket_id)
        if not basket:
            raise ValueError(f"Route Basket '{basket_id}' not found.")
        return basket

    @staticmethod
    def get_traffic_observations(
        db: Session,
        dataset_id: str = "DS-DGCA-TRAFFIC-2025",
        year: Optional[int] = None,
        month: Optional[int] = None,
        city: Optional[str] = None,
        route: Optional[str] = None,
        limit: int = 100
    ) -> List[DGCARefObservationRecord]:
        repo = DGCARepository(db)
        obs_list = repo.filter_traffic_observations(
            dataset_id=dataset_id,
            year=year,
            month=month,
            city=city,
            route_key=route,
            limit=limit
        )
        return [DGCARefObservationRecord.model_validate(o) for o in obs_list]

    @staticmethod
    def get_provenance_record(db: Session, dataset_id: str = "DS-DGCA-TRAFFIC-2025") -> Dict[str, Any]:
        repo = DGCARepository(db)
        prov = repo.get_provenance(dataset_id=dataset_id)
        if not prov:
            raise ValueError(f"DGCA Provenance Record for '{dataset_id}' not found.")
        
        return {
            "provenance_id": prov.provenance_id,
            "dataset_id": prov.dataset_id,
            "publisher": prov.publisher,
            "source_type": prov.source_type,
            "source_url": prov.source_url,
            "secondary_discovery_repo": prov.secondary_discovery_repo,
            "download_timestamp": prov.download_timestamp.isoformat() if prov.download_timestamp else None,
            "source_file_sha256": prov.source_file_sha256,
            "canonical_dataset_sha256": prov.canonical_dataset_sha256,
            "parser_version": prov.parser_version,
            "schema_version": prov.schema_version,
            "source_status": prov.source_status,
            "verification_notes": prov.verification_notes
        }
