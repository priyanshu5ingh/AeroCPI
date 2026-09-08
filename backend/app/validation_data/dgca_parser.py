import re
from typing import Dict, Tuple, Optional, List, Any

# Standard city to airport mapping table
CITY_TO_AIRPORT_DEFAULT: Dict[str, Tuple[str, str, str]] = {
    # Raw City Name: (Canonical City, Primary Airport Code, Metro Area Code)
    "DELHI": ("DELHI", "DEL", "DEL"),
    "NEW DELHI": ("DELHI", "DEL", "DEL"),
    "MUMBAI": ("MUMBAI", "BOM", "BOM"),
    "BOMBAY": ("MUMBAI", "BOM", "BOM"),
    "BANGALORE": ("BENGALURU", "BLR", "BLR"),
    "BENGALURU": ("BENGALURU", "BLR", "BLR"),
    "HYDERABAD": ("HYDERABAD", "HYD", "HYD"),
    "CHENNAI": ("CHENNAI", "MAA", "MAA"),
    "MADRAS": ("CHENNAI", "MAA", "MAA"),
    "KOLKATA": ("KOLKATA", "CCU", "CCU"),
    "CALCUTTA": ("KOLKATA", "CCU", "CCU"),
    "GOA": ("GOA", "GOI", "GOI"),
    "MOPA": ("GOA", "GOX", "GOI"),
    "AHMEDABAD": ("AHMEDABAD", "AMD", "AMD"),
    "PUNE": ("PUNE", "PNQ", "PNQ"),
    "GUWAHATI": ("GUWAHATI", "GAU", "GAU"),
    "JAIPUR": ("JAIPUR", "JAI", "JAI"),
    "LUCKNOW": ("LUCKNOW", "LKO", "LKO"),
    "PATNA": ("PATNA", "PAT", "PAT"),
    "KOCHI": ("COCHIN", "COK", "COK"),
    "COCHIN": ("COCHIN", "COK", "COK"),
    "TRIVANDRUM": ("THIRUVANANTHAPURAM", "TRV", "TRV"),
    "THIRUVANANTHAPURAM": ("THIRUVANANTHAPURAM", "TRV", "TRV"),
    "SRINAGAR": ("SRINAGAR", "SXR", "SXR"),
    "BHUBANESWAR": ("BHUBANESWAR", "BBI", "BBI"),
    "INDORE": ("INDORE", "IDR", "IDR"),
    "BAGDOGRA": ("BAGDOGRA", "IXB", "IXB"),
    "CHANDIGARH": ("CHANDIGARH", "IXC", "IXC"),
    "VARANASI": ("VARANASI", "VNS", "VNS"),
}

def normalize_city_name(raw_name: str) -> str:
    if not raw_name:
        return "UNKNOWN"
    cleaned = raw_name.strip().upper()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned

def map_city_to_airport(raw_city: str) -> Tuple[str, str, str]:
    """
    Maps a raw DGCA city string to (Canonical City, Primary Airport Code, Metro Area Code).
    """
    norm = normalize_city_name(raw_city)
    if norm in CITY_TO_AIRPORT_DEFAULT:
        return CITY_TO_AIRPORT_DEFAULT[norm]
    # Fallback heuristic for unlisted cities
    clean_code = norm[:3] if len(norm) >= 3 else "XXX"
    return (norm, clean_code, clean_code)

def parse_numeric_passenger_value(raw_val: Any) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Parses a passenger numeric value according to strict dash semantics:
    - Dash symbol ("-") -> (None, "-", "SOURCE_SYMBOL_DASH")
    - Valid integer/float string -> (int_val, raw_str, "PARSED_OK")
    - None / Blank -> (None, None, "MISSING_VALUE")
    """
    if raw_val is None:
        return (None, None, "MISSING_VALUE")
    
    val_str = str(raw_val).strip()
    if val_str == "" or val_str == "None":
        return (None, None, "MISSING_VALUE")
    
    if val_str == "-" or val_str == "--" or val_str == "N/A" or val_str == "NA":
        return (None, val_str, "SOURCE_SYMBOL_DASH")
    
    try:
        # Strip commas and whitespace
        clean_num_str = val_str.replace(",", "").replace(" ", "")
        float_val = float(clean_num_str)
        if float_val < 0:
            return (None, val_str, "NEGATIVE_VALUE_REJECTED")
        return (int(round(float_val)), val_str, "PARSED_OK")
    except ValueError:
        return (None, val_str, "NON_NUMERIC_PARSE_ERROR")

def make_canonical_route_key(city_a: str, city_b: str) -> str:
    """
    Returns an order-independent canonical route key: min(city1, city2) + "::" + max(city1, city2)
    """
    c1 = normalize_city_name(city_a)
    c2 = normalize_city_name(city_b)
    if c1 <= c2:
        return f"{c1}::{c2}"
    else:
        return f"{c2}::{c1}"

def deduplicate_and_merge_route_month_observations(
    dataset_id: str,
    year: int,
    month: int,
    raw_rows: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Aggregates raw rows for a single (year, month) into normalized route-month records.
    Prevents the reverse-route double-counting bug by grouping all directional entries
    (A->B and B->A) under the canonical route key and combining them exactly once per route-month.
    """
    ref_period = f"{year:04d}-{month:02d}"
    route_groups: Dict[str, Dict[str, Any]] = {}

    for row_idx, raw_row in enumerate(raw_rows, 1):
        c1_raw = raw_row.get("city1") or raw_row.get("City1") or ""
        c2_raw = raw_row.get("city2") or raw_row.get("City2") or ""

        c1_canon, apt1, metro1 = map_city_to_airport(c1_raw)
        c2_canon, apt2, metro2 = map_city_to_airport(c2_raw)

        if not c1_canon or not c2_canon or c1_canon == c2_canon:
            continue # Reject invalid or intra-city pairs

        route_key = make_canonical_route_key(c1_canon, c2_canon)

        pax_to_val, raw_to_str, reason_to = parse_numeric_passenger_value(raw_row.get("pax_to") or raw_row.get("PaxToCity2"))
        pax_from_val, raw_from_str, reason_from = parse_numeric_passenger_value(raw_row.get("pax_from") or raw_row.get("PaxFromCity2"))

        # Determine directional assignment relative to canonical ordering (city1 <= city2)
        if c1_canon <= c2_canon:
            canon_c1, canon_c2 = c1_canon, c2_canon
            canon_apt1, canon_apt2 = apt1, apt2
            pax_c1_c2 = pax_to_val
            pax_c2_c1 = pax_from_val
        else:
            canon_c1, canon_c2 = c2_canon, c1_canon
            canon_apt1, canon_apt2 = apt2, apt1
            pax_c1_c2 = pax_from_val
            pax_c2_c1 = pax_to_val

        if route_key not in route_groups:
            route_groups[route_key] = {
                "dataset_id": dataset_id,
                "year": year,
                "month": month,
                "reference_period": ref_period,
                "canonical_route_key": route_key,
                "city1_code": canon_c1,
                "city2_code": canon_c2,
                "origin_airport": canon_apt1,
                "destination_airport": canon_apt2,
                "pax_c1_c2": pax_c1_c2,
                "pax_c2_c1": pax_c2_c1,
                "raw_sources_count": 1,
                "raw_passenger_values": [f"Row {row_idx}: to={raw_to_str}, from={raw_from_str}"],
                "reasons": [reason_to, reason_from],
            }
        else:
            # Reverse-direction or duplicate raw row found for this route-month!
            grp = route_groups[route_key]
            grp["raw_sources_count"] += 1
            grp["raw_passenger_values"].append(f"Row {row_idx}: to={raw_to_str}, from={raw_from_str}")
            grp["reasons"].extend([reason_to, reason_from])

            # Accumulate pax safely (handling None values)
            if pax_c1_c2 is not None:
                grp["pax_c1_c2"] = (grp["pax_c1_c2"] or 0) + pax_c1_c2
            if pax_c2_c1 is not None:
                grp["pax_c2_c1"] = (grp["pax_c2_c1"] or 0) + pax_c2_c1

    # Convert groups to normalized records
    normalized_list = []
    for r_key, grp in route_groups.items():
        p1 = grp["pax_c1_c2"]
        p2 = grp["pax_c2_c1"]

        if p1 is None and p2 is None:
            combined = None
            norm_reason = "SOURCE_SYMBOL_DASH"
        else:
            combined = (p1 or 0) + (p2 or 0)
            norm_reason = "PARSED_OK"

        agg_mode = "BIDIRECTIONAL_MERGED" if grp["raw_sources_count"] > 1 else "SINGLE_ROW_PAIR"
        obs_id = f"OBS-DGCA-{grp['reference_period']}-{grp['origin_airport']}-{grp['destination_airport']}"

        normalized_list.append({
            "obs_id": obs_id,
            "dataset_id": dataset_id,
            "year": year,
            "month": month,
            "reference_period": grp["reference_period"],
            "canonical_route_key": r_key,
            "city1_code": grp["city1_code"],
            "city2_code": grp["city2_code"],
            "origin_airport": grp["origin_airport"],
            "destination_airport": grp["destination_airport"],
            "passengers_city1_to_city2": p1,
            "passengers_city2_to_city1": p2,
            "combined_passengers": combined,
            "aggregation_mode": agg_mode,
            "deduplication_status": "DEDUPLICATED",
            "raw_passenger_value": "; ".join(grp["raw_passenger_values"]),
            "normalization_reason": norm_reason,
            "source_status": "PROVENANCE_PARTIAL",
            "notes": f"Aggregated from {grp['raw_sources_count']} raw source entry(ies) without double counting.",
        })

    return normalized_list
