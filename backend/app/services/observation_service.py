from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.observation import Observation
from app.models.carrier import Carrier
from app.models.route import Route
from app.models.source import Source
from app.models.booking_horizon import BookingHorizon
from app.schemas.observation import ObservationCreate, ObservationFilter, RawQuoteInput
from app.services.normalization_service import NormalizationService
from app.services.quality_service import QualityService
from app.services.canonical_normalization_service import CanonicalNormalizationService
from app.validation.canonical_validation_rules import CanonicalValidationRules

class ObservationService:
    @staticmethod
    def ensure_reference_entities(db: Session, source_id: str, route_id: str, carrier_id: str, horizon_days: int):
        # Ensure Source exists
        source = db.query(Source).filter(Source.source_id == source_id).first()
        if not source:
            source = Source(
                source_id=source_id,
                source_name=source_id.replace("_", " ").title(),
                source_type="AIRLINE_DIRECT" if "DIRECT" in source_id else "OTA_AGGREGATOR",
                collection_policy="ETHICAL_PUBLIC_PERMITTED",
                active=True
            )
            db.add(source)

        # Ensure Carrier exists
        carrier = db.query(Carrier).filter(Carrier.carrier_id == carrier_id).first()
        if not carrier:
            carrier = Carrier(
                carrier_id=carrier_id,
                iata_code=carrier_id[:2].upper(),
                display_name=carrier_id.upper(),
                active=True
            )
            db.add(carrier)

        # Ensure Route exists
        route = db.query(Route).filter(Route.route_id == route_id).first()
        if not route:
            parts = route_id.split("-")
            origin = parts[0] if len(parts) > 0 else "UNKNOWN"
            dest = parts[1] if len(parts) > 1 else "UNKNOWN"
            route = Route(
                route_id=route_id,
                origin_code=origin,
                destination_code=dest,
                directionality="OUTBOUND",
                active=True
            )
            db.add(route)

        # Ensure BookingHorizon exists
        horizon_val = horizon_days if horizon_days is not None and horizon_days >= 0 else 1
        horizon = db.query(BookingHorizon).filter(BookingHorizon.horizon_days == horizon_val).first()
        if not horizon:
            horizon = BookingHorizon(
                horizon_days=horizon_val,
                horizon_code=f"T+{horizon_val}",
                description=f"{horizon_val} Days Lead Time"
            )
            db.add(horizon)

        db.flush()

    @classmethod
    def ingest_raw_quote(cls, db: Session, raw_input: RawQuoteInput) -> Observation:
        raw_dict = raw_input.model_dump()
        canon_dict = CanonicalNormalizationService.normalize_raw_quote(raw_dict)
        val_status, val_reasons = CanonicalValidationRules.evaluate_observation(canon_dict)

        adv_days = canon_dict["advance_purchase_days"]
        horizon_days = adv_days if adv_days is not None and adv_days >= 0 else 1

        cls.ensure_reference_entities(
            db=db,
            source_id=canon_dict["source_id"],
            route_id=canon_dict["route_id"],
            carrier_id=canon_dict["airline"],
            horizon_days=horizon_days
        )

        obs = Observation(
            source_id=canon_dict["source_id"],
            source_name=canon_dict["source_name"],
            source_url=canon_dict["source_url"],
            collected_at=canon_dict["collected_at"],
            observed_at=canon_dict["collected_at"],
            search_timestamp=canon_dict["search_timestamp"],
            search_date=canon_dict["search_date"],
            travel_date=canon_dict["travel_date"],
            advance_purchase_days=canon_dict["advance_purchase_days"],
            booking_horizon_days=horizon_days,
            origin_raw=canon_dict["origin_raw"],
            destination_raw=canon_dict["destination_raw"],
            origin_airport=canon_dict["origin_airport"],
            destination_airport=canon_dict["destination_airport"],
            route_id=canon_dict["route_id"],
            carrier_id=canon_dict["airline"],
            airline=canon_dict["airline"],
            flight_number=canon_dict["flight_number"],
            cabin=canon_dict["cabin"],
            fare_class=canon_dict["fare_class"],
            trip_type=canon_dict["trip_type"],
            stops=canon_dict["stops"],
            stops_status=canon_dict["stops_status"],
            duration_minutes=canon_dict["duration_minutes"],
            raw_total_fare=canon_dict["raw_total_fare"],
            raw_base_fare=canon_dict["raw_base_fare"],
            raw_taxes=canon_dict["raw_taxes"],
            raw_fees=canon_dict["raw_fees"],
            base_fare=canon_dict["base_fare"],
            taxes=canon_dict["taxes"],
            mandatory_fees=canon_dict["fees"],
            fees=canon_dict["fees"],
            total_fare=canon_dict["total_fare"] if canon_dict["total_fare"] is not None else 0.0,
            currency=canon_dict["currency"],
            stop_type="NON_STOP" if canon_dict["stops"] == 0 else "ONE_STOP",
            raw_payload_hash=canon_dict["raw_payload_hash"],
            observation_key=canon_dict["observation_key"],
            quote_fingerprint=canon_dict["quote_fingerprint"],
            breakdown_status=canon_dict["breakdown_status"],
            arithmetic_status=canon_dict["arithmetic_status"],
            horizon_code=canon_dict["horizon_code"],
            route_mapping_status=canon_dict["route_mapping_status"],
            basket_status=canon_dict["basket_status"],
            validation_status=val_status,
            validation_reasons=val_reasons,
            data_status="OBSERVED" if val_status != "REJECT" else "REJECTED",
        )

        db.add(obs)
        db.commit()
        db.refresh(obs)
        return obs

    @classmethod
    def create_observation(cls, db: Session, obs_data: ObservationCreate) -> Observation:
        cls.ensure_reference_entities(
            db=db,
            source_id=obs_data.source_id,
            route_id=obs_data.route_id,
            carrier_id=obs_data.carrier_id,
            horizon_days=obs_data.booking_horizon_days
        )

        obs = Observation(
            source_id=obs_data.source_id,
            route_id=obs_data.route_id,
            carrier_id=obs_data.carrier_id,
            travel_date=obs_data.travel_date,
            observed_at=obs_data.observed_at,
            booking_horizon_days=obs_data.booking_horizon_days,
            cabin=obs_data.cabin,
            fare_class=obs_data.fare_class,
            trip_type=obs_data.trip_type,
            base_fare=obs_data.base_fare,
            taxes=obs_data.taxes,
            mandatory_fees=obs_data.mandatory_fees,
            total_fare=obs_data.total_fare,
            currency=obs_data.currency,
            baggage_information=obs_data.baggage_information,
            stop_type=obs_data.stop_type,
            data_status=obs_data.data_status.value if hasattr(obs_data.data_status, 'value') else str(obs_data.data_status),
            raw_reference=obs_data.raw_reference
        )

        db.add(obs)
        db.flush()

        # Run Normalization
        norm_result = NormalizationService.normalize_observation(obs)
        db.add(norm_result)

        # Run Quality Evaluation
        quality_result = QualityService.evaluate_quality(db, obs)
        db.add(quality_result)

        db.commit()
        db.refresh(obs)
        return obs

    @staticmethod
    def get_observation_by_id(db: Session, observation_id: str) -> Optional[Observation]:
        return db.query(Observation).filter(Observation.observation_id == observation_id).first()

    @staticmethod
    def get_observations(db: Session, filters: ObservationFilter) -> List[Observation]:
        query = db.query(Observation)
        if filters.route_id:
            query = query.filter(Observation.route_id == filters.route_id)
        if filters.carrier_id:
            query = query.filter(Observation.carrier_id == filters.carrier_id)
        if filters.booking_horizon_days:
            query = query.filter(Observation.booking_horizon_days == filters.booking_horizon_days)
        if filters.validation_status:
            query = query.filter(Observation.validation_status == filters.validation_status)
        if filters.basket_status:
            query = query.filter(Observation.basket_status == filters.basket_status)
        if filters.data_status:
            status_str = filters.data_status.value if hasattr(filters.data_status, 'value') else str(filters.data_status)
            query = query.filter(Observation.data_status == status_str)
        if filters.travel_date:
            query = query.filter(Observation.travel_date == filters.travel_date)

        return query.order_by(Observation.created_at.desc()).offset(filters.offset).limit(filters.limit).all()
