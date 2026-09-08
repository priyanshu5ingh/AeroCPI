from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class DGCARefObservationRecord(BaseModel):
    obs_id: str
    dataset_id: str
    year: int
    month: int
    reference_period: str
    canonical_route_key: str
    city1_code: str
    city2_code: str
    origin_airport: str
    destination_airport: str
    passengers_city1_to_city2: Optional[int] = None
    passengers_city2_to_city1: Optional[int] = None
    combined_passengers: Optional[int] = None
    freight_tons: Optional[float] = None
    mail_tons: Optional[float] = None
    aggregation_mode: str = "BIDIRECTIONAL_MERGED"
    deduplication_status: str = "DEDUPLICATED"
    raw_passenger_value: Optional[str] = None
    normalization_reason: Optional[str] = None
    source_status: str = "PROVENANCE_PARTIAL"
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RouteBasketMemberRecord(BaseModel):
    member_id: str
    basket_id: str
    rank: int
    route_id: str
    canonical_route_key: str
    city_1: str
    city_2: str
    origin_airport: str
    destination_airport: str
    period_passengers: int
    dgca_route_traffic_share: float
    dgca_basket_weight: float
    dgca_route_traffic_share_unit: str = "share_of_all_eligible_traffic"
    dgca_basket_weight_unit: str = "weight_within_selected_basket"
    selection_reason: str
    source_status: str = "PROVENANCE_PARTIAL"

    model_config = ConfigDict(from_attributes=True)


class RouteBasketRecord(BaseModel):
    basket_id: str
    basket_name: str
    reference_period_type: str
    reference_period_start: str
    reference_period_end: str
    selection_method: str
    basket_size: int
    total_period_passengers: int
    total_all_eligible_routes_passengers: int
    source_dataset_id: str
    methodology_version: str
    relationship_to_mospi: str
    status: str
    created_at: datetime
    members: List[RouteBasketMemberRecord] = []

    model_config = ConfigDict(from_attributes=True)


class DGCACoverageSummary(BaseModel):
    publisher: str = "DGCA"
    dataset_id: str
    reference_period_start: str
    reference_period_end: str
    months_expected: int
    months_available: int
    months_missing: List[str] = []
    completeness_status: str
    total_raw_records: int
    total_normalized_route_months: int
    unique_routes_count: int
    source_files_count: int
    source_hashes: List[Dict[str, str]] = []
    source_status: str = "PROVENANCE_PARTIAL"
