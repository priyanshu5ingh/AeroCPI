from decimal import Decimal
from typing import Dict, Any, List, Tuple

class CanonicalValidationRules:
    """
    Decoupled Canonical Validation Engine:
    Takes a normalized CanonicalObservation dict and evaluates:
    - Hard REJECT Rules (Invalid fare, travel date before search date, same O&D, currency != INR, unmappable route)
    - Soft FLAG Warnings (Missing breakdown, arithmetic mismatch, route outside basket, unusual fare/duration)
    - ACCEPT Status
    """

    @staticmethod
    def evaluate_observation(canon_obs: Dict[str, Any]) -> Tuple[str, List[str]]:
        reject_reasons: List[str] = []
        flag_reasons: List[str] = []

        total_fare = canon_obs.get("total_fare")
        base_fare = canon_obs.get("base_fare")
        taxes = canon_obs.get("taxes")
        fees = canon_obs.get("fees")

        search_date = canon_obs.get("search_date")
        travel_date = canon_obs.get("travel_date")
        advance_days = canon_obs.get("advance_purchase_days")

        origin_raw = canon_obs.get("origin_raw")
        destination_raw = canon_obs.get("destination_raw")
        origin_apt = canon_obs.get("origin_airport")
        dest_apt = canon_obs.get("destination_airport")

        currency = canon_obs.get("currency")
        route_mapping_status = canon_obs.get("route_mapping_status")
        basket_status = canon_obs.get("basket_status")
        arithmetic_status = canon_obs.get("arithmetic_status")
        breakdown_status = canon_obs.get("breakdown_status")

        flight_number = canon_obs.get("flight_number")
        fare_class = canon_obs.get("fare_class")
        duration_minutes = canon_obs.get("duration_minutes")
        source_name = canon_obs.get("source_name")
        source_url = canon_obs.get("source_url")

        # =========================================================================
        # 1. HARD REJECT RULES
        # =========================================================================

        # Rule 1: Non-positive total fare
        if total_fare is None or total_fare <= Decimal("0.00"):
            reject_reasons.append("REJECT_TOTAL_FARE_NON_POSITIVE")

        # Rule 2: Negative fare component
        if (base_fare is not None and base_fare < Decimal("0.00")) or \
           (taxes is not None and taxes < Decimal("0.00")) or \
           (fees is not None and fees < Decimal("0.00")):
            reject_reasons.append("REJECT_NEGATIVE_FARE_COMPONENT")

        # Rule 3: Travel date before search date (negative advance purchase)
        if search_date is None or travel_date is None:
            reject_reasons.append("REJECT_MALFORMED_OBSERVATION")
        elif advance_days is not None and advance_days < 0:
            reject_reasons.append("REJECT_TRAVEL_BEFORE_SEARCH")

        # Rule 4: Invalid location input
        if not origin_raw or not destination_raw:
            reject_reasons.append("REJECT_INVALID_LOCATION")

        # Rule 5: Unmappable route
        if route_mapping_status == "UNMAPPABLE" or not origin_apt or not dest_apt:
            reject_reasons.append("REJECT_UNMAPPABLE_ROUTE")

        # Rule 6: Same origin and destination
        if origin_apt and dest_apt and origin_apt == dest_apt:
            reject_reasons.append("REJECT_SAME_ORIGIN_DESTINATION")

        # Rule 7: Unsupported currency (Must be INR, but stored for auditable rejection!)
        if currency != "INR":
            reject_reasons.append("REJECT_UNSUPPORTED_CURRENCY")

        if reject_reasons:
            return ("REJECT", reject_reasons)

        # =========================================================================
        # 2. SOFT FLAG RULES
        # =========================================================================

        # Flag 1: Missing fare component breakdown
        if breakdown_status in ("PARTIAL_BREAKDOWN", "TOTAL_ONLY"):
            flag_reasons.append("FLAG_MISSING_FARE_COMPONENT_BREAKDOWN")

        # Flag 2: Fare arithmetic mismatch
        if arithmetic_status == "ARITHMETIC_MISMATCH":
            flag_reasons.append("FLAG_ARITHMETIC_MISMATCH")

        # Flag 3: Route outside reference basket
        if basket_status == "ROUTE_OUTSIDE_REFERENCE_BASKET":
            flag_reasons.append("FLAG_ROUTE_OUTSIDE_REFERENCE_BASKET")

        # Flag 4: Unusual fare amount (< 500 INR or > 100,000 INR)
        if total_fare is not None:
            if total_fare < Decimal("500.00") or total_fare > Decimal("100000.00"):
                flag_reasons.append("FLAG_UNUSUAL_FARE_AMOUNT")

        # Flag 5: Unusual flight duration (< 30 mins or > 1440 mins)
        if duration_minutes is not None:
            if duration_minutes < 30 or duration_minutes > 1440:
                flag_reasons.append("FLAG_UNUSUAL_DURATION")

        # Flag 6: Missing flight number
        if not flight_number:
            flag_reasons.append("FLAG_MISSING_FLIGHT_NUMBER")

        # Flag 7: Missing fare class
        if not fare_class or fare_class == "UNKNOWN":
            flag_reasons.append("FLAG_MISSING_FARE_CLASS")

        # Flag 8: Incomplete source metadata
        if not source_name:
            flag_reasons.append("FLAG_INCOMPLETE_SOURCE_METADATA")

        # Flag 9: Missing carrier / airline information
        airline = canon_obs.get("airline")
        if not airline or str(airline).strip().upper() in ("UNKNOWN", "NONE", "NULL", ""):
            flag_reasons.append("FLAG_MISSING_CARRIER_INFO")

        if flag_reasons:
            return ("FLAG", flag_reasons)

        return ("ACCEPT", ["VALIDATION_OK"])

    @staticmethod
    def evaluate_index_eligibility(canon_obs: Dict[str, Any], val_status: str, val_reasons: List[str]) -> Tuple[str, List[str]]:
        """
        Evaluates explicit index eligibility separate from validation status.
        Index Eligibility Policy:
        - ACCEPT/FLAG status with valid total fare, canonical basket route, and production APW horizon -> ELIGIBLE.
        - Total-only observations (FLAG_MISSING_FARE_COMPONENT_BREAKDOWN) and missing flight numbers (FLAG_MISSING_FLIGHT_NUMBER) -> ELIGIBLE.
        - Routes outside basket, arithmetic mismatches, off-horizon bookings, or REJECT status -> INELIGIBLE.
        """
        ineligible_reasons: List[str] = []

        if val_status == "REJECT":
            ineligible_reasons.append("INELIGIBLE_REJECTED_OBSERVATION")

        if "FLAG_ROUTE_OUTSIDE_REFERENCE_BASKET" in val_reasons or canon_obs.get("basket_status") == "ROUTE_OUTSIDE_REFERENCE_BASKET":
            ineligible_reasons.append("INELIGIBLE_ROUTE_OUTSIDE_BASKET")

        if "FLAG_ARITHMETIC_MISMATCH" in val_reasons or canon_obs.get("arithmetic_status") == "ARITHMETIC_MISMATCH":
            ineligible_reasons.append("INELIGIBLE_FARE_ARITHMETIC_MISMATCH")

        horizon_code = canon_obs.get("horizon_code")
        if horizon_code not in ("T+1", "T+7", "T+15", "T+30", "T+45"):
            ineligible_reasons.append("INELIGIBLE_OFF_HORIZON")

        total_fare = canon_obs.get("total_fare")
        if total_fare is None or float(total_fare) <= 0:
            ineligible_reasons.append("INELIGIBLE_NON_POSITIVE_TOTAL_FARE")

        if ineligible_reasons:
            return ("INELIGIBLE", ineligible_reasons)

        return ("ELIGIBLE", ["INDEX_ELIGIBLE"])

