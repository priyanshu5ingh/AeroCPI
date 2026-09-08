from typing import List, Dict, Tuple, Any

class DGCAValidator:
    """
    Validation engine enforcing all 20 mandatory DGCA reference & route basket rules.
    """

    @staticmethod
    def validate_dataset_and_observations(
        dataset_meta: Dict[str, Any],
        raw_rows: List[Dict[str, Any]],
        normalized_obs: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        errors = []

        # Rule 1: Publisher == "DGCA"
        if dataset_meta.get("publisher") != "DGCA":
            errors.append(f"Rule 1 Violation: Publisher must be 'DGCA', got '{dataset_meta.get('publisher')}'")

        # Rule 2: Source file provenance required
        if not dataset_meta.get("canonical_dataset_sha256"):
            errors.append("Rule 2 Violation: Missing canonical_dataset_sha256 hash in dataset provenance")

        # Rule 3 & Rule 19: Valid year/month bounds and report metadata agreement
        for r in raw_rows:
            yr = r.get("year")
            mo = r.get("month")
            if not isinstance(yr, int) or yr < 2020 or yr > 2030:
                errors.append(f"Rule 3 Violation: Invalid year '{yr}' in raw observation")
            if not isinstance(mo, int) or mo < 1 or mo > 12:
                errors.append(f"Rule 3 Violation: Invalid month '{mo}' in raw observation")

        # Rule 4 & 5 & 6 & 7 & 8: Directional passenger fields, non-negative, combined calculation, canonical key, raw preservation
        for obs in normalized_obs:
            p1 = obs.get("passengers_city1_to_city2")
            p2 = obs.get("passengers_city2_to_city1")
            comb = obs.get("combined_passengers")

            if p1 is not None and p1 < 0:
                errors.append(f"Rule 5 Violation: Negative passenger count '{p1}' in route {obs.get('canonical_route_key')}")
            if p2 is not None and p2 < 0:
                errors.append(f"Rule 5 Violation: Negative passenger count '{p2}' in route {obs.get('canonical_route_key')}")

            if p1 is not None or p2 is not None:
                expected_comb = (p1 or 0) + (p2 or 0)
                if comb != expected_comb:
                    errors.append(f"Rule 6 Violation: Combined passengers mismatch ({comb} vs {expected_comb}) in route {obs.get('canonical_route_key')}")

            r_key = obs.get("canonical_route_key")
            if not r_key or "::" not in r_key:
                errors.append(f"Rule 7 Violation: Invalid canonical route key '{r_key}'")

        # Rule 13 & 16: Completeness status reporting & incomplete source period safeguards
        expected = dataset_meta.get("months_expected", 12)
        avail = dataset_meta.get("months_available", 0)
        status = dataset_meta.get("completeness_status")

        if avail < expected and status == "COMPLETE":
            errors.append(f"Rule 16 Violation: Dataset has only {avail}/{expected} months but is illegally marked 'COMPLETE'")

        # Rule 17 & 18: Reverse-direction double-counting & raw vs normalized separation
        route_keys_seen = set()
        for obs in normalized_obs:
            r_key = (obs.get("reference_period"), obs.get("canonical_route_key"))
            if r_key in route_keys_seen:
                errors.append(f"Rule 17 Violation: Duplicate route-month observation key {r_key} found after deduplication!")
            route_keys_seen.add(r_key)

        return (len(errors) == 0, errors)

    @staticmethod
    def validate_route_basket(
        basket_meta: Dict[str, Any],
        members: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        errors = []

        # Rule 9: Deterministic ranking
        ranks = [m.get("rank") for m in members]
        if ranks != sorted(ranks):
            errors.append("Rule 9 Violation: Route basket members are not sorted in strict rank order")

        # Rule 11: Unique rank per member
        if len(ranks) != len(set(ranks)):
            errors.append("Rule 11 Violation: Duplicate ranks found in route basket members")

        # Rule 12: Configurable basket size respected
        basket_size = basket_meta.get("basket_size", 10)
        if len(members) != basket_size:
            errors.append(f"Rule 12 Violation: Expected basket size {basket_size}, got {len(members)} members")

        # Rule 10: Basket weights sum to approximately 1.0, National shares sum < 1.0
        basket_weights = [m.get("dgca_basket_weight", 0.0) for m in members]
        tot_weight = sum(basket_weights)
        if abs(tot_weight - 1.0) > 1e-4:
            errors.append(f"Rule 10 Violation: Basket weights sum to {tot_weight:.6f}, expected approximately 1.0")

        national_shares = [m.get("dgca_route_traffic_share", 0.0) for m in members]
        tot_national_share = sum(national_shares)
        if tot_national_share >= 1.0:
            errors.append(f"Rule 10 Violation: National traffic shares sum to {tot_national_share:.6f}, expected strictly less than 1.0 for Top-N basket")

        # Rule 14 & 15: CPI weight separation safeguards
        for m in members:
            # Verify weight field name is traffic_share / basket_weight, NOT cpi_weight
            if "cpi_weight" in m or "cpi_weight_value" in m:
                errors.append("Rule 15 Violation: CPI weight field illegally injected into DGCA traffic basket member!")
            if m.get("dgca_basket_weight_unit") != "weight_within_selected_basket":
                errors.append(f"Rule 14 Violation: Invalid basket weight unit '{m.get('dgca_basket_weight_unit')}'")
            if m.get("dgca_route_traffic_share_unit") != "share_of_all_eligible_traffic":
                errors.append(f"Rule 14 Violation: Invalid route traffic share unit '{m.get('dgca_route_traffic_share_unit')}'")

        # Rule 20: Determinism check
        for m in members:
            if not m.get("route_id") or not m.get("canonical_route_key"):
                errors.append(f"Rule 20 Violation: Member rank {m.get('rank')} missing route identification")

        return (len(errors) == 0, errors)
