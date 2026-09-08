from typing import List, Dict, Tuple, Any
from app.validation_data.schemas import ExternalReferenceDataRecord

EXPECTED_REGRESSION_FIXTURES: Dict[str, Tuple[float, float]] = {
    "2026-03": (123.55, 14.20),
    "2026-04": (123.27, 11.11),
    "2026-07": (125.46, 22.94)
}

class MoSPIReferenceValidator:
    """
    Deterministic validation engine for official MoSPI CPI-2024 Airfare series.
    Separates general structural & statistical rules from regression test fixtures.
    """

    @classmethod
    def validate_dataset(cls, records: List[ExternalReferenceDataRecord]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        if not records:
            return False, ["Validation Failed: Reference dataset is empty"]

        months_seen = set()

        for idx, rec in enumerate(records):
            # Rule 1: Item Code
            if rec.item_code != "07.3.3.1.2.01":
                errors.append(f"Record {idx} ({rec.reference_period}): Invalid item_code '{rec.item_code}', expected '07.3.3.1.2.01'")

            # Rule 2: Base Year
            if rec.base_year != 2024:
                errors.append(f"Record {idx} ({rec.reference_period}): Invalid base_year {rec.base_year}, expected 2024")

            # Rule 3: Series Type
            if rec.series_type != "CURRENT":
                errors.append(f"Record {idx} ({rec.reference_period}): Invalid series_type '{rec.series_type}', expected 'CURRENT'")

            # Rule 4: Geography
            if rec.geography != "All India":
                errors.append(f"Record {idx} ({rec.reference_period}): Invalid geography '{rec.geography}', expected 'All India'")

            # Rule 5: Sector
            if rec.sector != "Combined":
                errors.append(f"Record {idx} ({rec.reference_period}): Invalid sector '{rec.sector}', expected 'Combined'")

            # Rule 6: Unique Month
            if rec.reference_period in months_seen:
                errors.append(f"Record {idx}: Duplicate month record found for '{rec.reference_period}'")
            months_seen.add(rec.reference_period)

            # Rule 7: Positive Index
            if rec.index_value is None or rec.index_value <= 0:
                errors.append(f"Record {idx} ({rec.reference_period}): Invalid non-positive index_value {rec.index_value}")

            # Rule 8: Inflation Type YOY
            if rec.inflation_value is not None and rec.inflation_type != "YOY":
                errors.append(f"Record {idx} ({rec.reference_period}): Invalid inflation_type '{rec.inflation_type}', expected 'YOY'")

        # Rule 9: Coverage Bounds (Must start 2025-01 and extend to 2026-07)
        sorted_periods = sorted(list(months_seen))
        if sorted_periods[0] != "2025-01":
            errors.append(f"Invalid series start period '{sorted_periods[0]}', expected '2025-01'")
        if sorted_periods[-1] != "2026-07":
            errors.append(f"Invalid series end period '{sorted_periods[-1]}', expected '2026-07'")

        # Rule 10: Regression Fixture Verification
        rec_map = {r.reference_period: r for r in records}
        for month, (expected_idx, expected_yoy) in EXPECTED_REGRESSION_FIXTURES.items():
            if month not in rec_map:
                errors.append(f"Regression Fixture Error: Missing expected benchmark month '{month}'")
            else:
                r = rec_map[month]
                if abs(r.index_value - expected_idx) > 1e-4:
                    errors.append(f"Regression Fixture Error for {month}: Got index {r.index_value}, expected {expected_idx}")
                if r.inflation_value is not None and abs(r.inflation_value - expected_yoy) > 1e-2:
                    errors.append(f"Regression Fixture Error for {month}: Got YoY inflation {r.inflation_value}, expected {expected_yoy}")

        is_valid = len(errors) == 0
        return is_valid, errors
