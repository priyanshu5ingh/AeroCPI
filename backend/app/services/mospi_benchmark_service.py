from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.index_run import IndexRun
from app.validation_data.repository import ValidationDataRepository

class MospiBenchmarkService:
    """
    Service for comparing AeroCPI market-observed index runs against official MoSPI CPI-2024 Airfare benchmarks.
    Includes mandatory architectural safeguards explaining that this is a BENCHMARK COMPARISON,
    not a reproduction attempt of official MoSPI monthly sampling methodology.
    """

    @classmethod
    def compare_run_with_mospi_benchmark(
        cls,
        db: Session,
        run_id: str
    ) -> Dict[str, Any]:
        index_run = db.query(IndexRun).filter(IndexRun.run_id == run_id).first()
        if not index_run:
            raise ValueError(f"Index run '{run_id}' not found")

        repo = ValidationDataRepository(db)
        
        # Target period from comparison_period
        target_month = index_run.comparison_period[:7] # e.g. "2026-09" or "2026-07"
        
        mospi_rec = repo.get_mospi_airfare_for_month(target_month)

        if not mospi_rec:
            # Fallback to latest available month (e.g. July 2026 if comparison period is Sept 2026)
            latest_records = repo.get_mospi_airfare_series()
            mospi_rec = latest_records[-1] if latest_records else None

        if not mospi_rec:
            return {
                "run_id": run_id,
                "status": "NO_BENCHMARK_DATA_AVAILABLE",
                "message": "No official MoSPI CPI-2024 Airfare reference record available for comparison period."
            }

        aerocpi_val = float(index_run.index_value)
        mospi_val = float(mospi_rec.index_value)
        abs_diff = round(abs(aerocpi_val - mospi_val), 3)
        pct_diff = round(((aerocpi_val - mospi_val) / mospi_val) * 100, 2)

        return {
            "run_id": run_id,
            "aerocpi_reference_period": index_run.reference_period,
            "aerocpi_comparison_period": index_run.comparison_period,
            "aerocpi_frequency": index_run.frequency,
            "aerocpi_index_value": aerocpi_val,
            
            "mospi_benchmark": {
                "item_code": mospi_rec.item_code,
                "item_label": mospi_rec.item_label,
                "publisher": mospi_rec.publisher,
                "base_year": mospi_rec.base_year,
                "series_type": mospi_rec.series_type,
                "geography": mospi_rec.geography,
                "sector": mospi_rec.sector,
                "month": mospi_rec.reference_period,
                "mospi_index_value": mospi_val,
                "mospi_yoy_inflation": mospi_rec.inflation_value,
                "inflation_type": mospi_rec.inflation_type,
                "cpi_weight_value": mospi_rec.cpi_weight_value,
                "cpi_weight_unit": mospi_rec.cpi_weight_unit,
                "data_status": mospi_rec.data_status,
                "provenance_status": mospi_rec.provenance_status
            },
            
            "comparison_metrics": {
                "absolute_difference": abs_diff,
                "percentage_difference": pct_diff,
                "comparison_type": "benchmark",
                "interpretation": "market_measurement_vs_official_monthly_cpi",
                "methodological_difference": True,
                "note": (
                    "AeroCPI is a high-frequency market-observed index capturing real-time domestic airfares. "
                    "Official MoSPI CPI-2024 Airfare (07.3.3.1.2.01) is a monthly published benchmark collected "
                    "via state regional offices per MoSPI sampling protocol. Divergence reflects high-frequency "
                    "market dynamics vs official monthly statistical sampling."
                )
            }
        }
