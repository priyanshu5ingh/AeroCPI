"""AeroGuide Market State & 'What Changed?' Attribution Bridge Service.
Reads persisted AeroCPI index runs and 5A log-linear attributions to determine
national and corridor market states without mutating historical calculations.
"""
from __future__ import annotations
import statistics
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.models.index_run import IndexRun
from app.models.horizon_index_result import HorizonIndexResult
from app.models.route_index_result import RouteIndexResult
from app.models.trust_evaluation import TrustEvaluation
from app.services.index_explanation_service import IndexExplanationService


class MarketStateService:
    """Calculates national and route market state and builds 'What Changed?' attribution bridge."""

    @classmethod
    def get_national_market_state(cls, db: Session, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculates national market condition based on latest or specified AeroCPI measurement run."""
        if run_id:
            run = db.query(IndexRun).filter(IndexRun.run_id == run_id).first()
        else:
            run = db.query(IndexRun).order_by(IndexRun.run_timestamp.desc()).first()

        if not run:
            return {
                "market_state": "INSUFFICIENT_DATA",
                "headline_index": 100.0,
                "point_change": 0.0,
                "percentage_change": 0.0,
                "horizon_code": "T+15",
                "run_id": "NONE",
                "summary": "No completed AeroCPI index runs found in database.",
                "trust_status": "UNEVALUATED"
            }

        idx_val = float(run.index_value) if run.index_value is not None else 100.0
        delta = idx_val - 100.0
        pct_change = delta # Base period is 100.0

        horizons = db.query(HorizonIndexResult).filter(HorizonIndexResult.run_id == run.run_id).all()
        h_values = [float(h.index_value) for h in horizons if h.index_value is not None]
        h_std = statistics.stdev(h_values) if len(h_values) > 1 else 0.0

        trust = db.query(TrustEvaluation).filter(TrustEvaluation.index_run_id == run.run_id).first()
        trust_status = trust.trust_status if trust else "HIGH_CONFIDENCE"

        # 6-State Classification: NORMAL / RISING / FALLING / VOLATILE / ANOMALOUS / INSUFFICIENT_DATA
        if trust_status == "DEGRADED" or abs(delta) > 30.0:
            state = "ANOMALOUS"
            desc = "Airfare index shift exceeds statistical safety envelope or contains degraded coverage."
        elif h_std > 8.0:
            state = "VOLATILE"
            desc = "Significant price divergence observed across advance purchase booking horizons."
        elif delta > 3.0:
            state = "RISING"
            desc = "Domestic airfares are elevated compared to the reference base period."
        elif delta < -3.0:
            state = "FALLING"
            desc = "Domestic airfares are softer/below the reference base period."
        else:
            state = "NORMAL"
            desc = "Domestic airfares are stable and aligned with typical baseline levels."

        return {
            "market_state": state,
            "headline_index": round(idx_val, 2),
            "point_change": round(delta, 2),
            "percentage_change": round(pct_change, 2),
            "horizon_code": "T+15",
            "run_id": run.run_id,
            "reference_period": str(run.reference_period),
            "comparison_period": str(run.comparison_period),
            "summary": desc,
            "trust_status": trust_status
        }

    @classmethod
    def get_what_changed_summary(cls, db: Session, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Builds complete 'What Changed?' attribution bridge linking national movement to route drivers."""
        national = cls.get_national_market_state(db, run_id=run_id)
        active_run_id = national["run_id"]

        if active_run_id == "NONE":
            return {
                "national_state": national,
                "top_positive_drivers": [],
                "top_negative_drivers": [],
                "all_routes": []
            }

        # Query 5A attribution service
        explanation_data = IndexExplanationService.explain_index_run(db=db, run_id=active_run_id)
        
        # Find headline horizon contributions
        headline_h = next((h for h in explanation_data.horizons if h.is_headline), None)
        if not headline_h and explanation_data.horizons:
            headline_h = explanation_data.horizons[0]
            
        contributions = headline_h.route_contributions if headline_h else []
        route_dicts = [
            c.model_dump() if hasattr(c, "model_dump") else c.dict()
            for c in contributions
        ]
        
        positive_drivers = [c for c in route_dicts if c.get("direction") == "POSITIVE"]
        positive_drivers.sort(key=lambda x: float(x.get("point_contribution") or 0.0), reverse=True)
        
        negative_drivers = [c for c in route_dicts if c.get("direction") == "NEGATIVE"]
        negative_drivers.sort(key=lambda x: float(x.get("point_contribution") or 0.0))
        
        return {
            "national_state": national,
            "top_positive_drivers": positive_drivers[:5],
            "top_negative_drivers": negative_drivers[:5],
            "all_routes": route_dicts,
            "mathematical_identity": "5A Log-Linear Geometric Attribution: sum(point_contributions) == headline_change"
        }
