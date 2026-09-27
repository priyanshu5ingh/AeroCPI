"""Automatic model lifecycle trigger service."""
from __future__ import annotations
import logging
from typing import Dict, Any

from sqlalchemy.orm import Session
from app.services.longitudinal_service import calculate_readiness_metrics
from app.services.model_training_service import ModelTrainingService, PromotionGateException
from app.services.model_registry_service import ModelRegistryService

logger = logging.getLogger(__name__)

class ModelLifecycleService:
    """Evaluates readiness and manages the automated training and promotion lifecycle."""

    @classmethod
    def execute_lifecycle_trigger(cls, db: Session) -> Dict[str, Any]:
        """
        1. Recalculate longitudinal readiness.
        2. If NOT satisfied, do not train.
        3. If satisfied, create CANDIDATE.
        4-8. Evaluate gates and retain or promote.
        """
        logger.info("Executing model lifecycle trigger...")
        
        # 1. Recalculate longitudinal readiness
        readiness = calculate_readiness_metrics(db)
        
        # 2. Check authoritative readiness gate
        if readiness.get("overall_readiness") != "READY_FOR_MODEL":
            msg = f"Longitudinal readiness NOT satisfied. Reason: {readiness.get('readiness_notes')}"
            logger.info(msg)
            return {
                "triggered": False,
                "reason": msg,
                "readiness": readiness
            }
            
        logger.info("Longitudinal readiness SATISFIED. Triggering candidate training.")
        
        # 3. Create CANDIDATE (train_candidate handles temporal split, evaluation, metrics, and persisting artifact)
        try:
            candidate = ModelTrainingService.train_candidate(db, model_version="AEROGUIDE_ML_V1", allow_synthetic_override=False)
        except PromotionGateException as e:
            msg = f"Training failed during candidate generation: {str(e)}"
            logger.error(msg)
            return {
                "triggered": True,
                "training_success": False,
                "reason": msg,
                "readiness": readiness
            }
            
        # 6-7. Evaluate promotion gates
        passed, reasons = ModelTrainingService.evaluate_promotion_gates(candidate)
        
        if not passed:
            # 8. Retain as VALIDATION_FAILED
            msg = f"Candidate failed promotion gates: {', '.join(reasons)}"
            logger.warning(msg)
            candidate["manifest"]["status"] = "VALIDATION_FAILED"
            candidate["manifest"]["rejection_reasons"] = reasons
            # Resave manifest to update status
            ModelRegistryService.update_candidate_manifest(candidate["manifest_path"], candidate["manifest"])
            
            return {
                "triggered": True,
                "training_success": True,
                "promoted": False,
                "reason": msg,
                "manifest": candidate["manifest"],
                "readiness": readiness
            }
            
        # 9. Promote
        logger.info("Candidate PASSED promotion gates. Transitioning to PROMOTED.")
        try:
            promoted = ModelTrainingService.promote_candidate(candidate)
            return {
                "triggered": True,
                "training_success": True,
                "promoted": True,
                "manifest": promoted["manifest"],
                "readiness": readiness
            }
        except PromotionGateException as e:
            msg = f"Promotion failed: {str(e)}"
            logger.error(msg)
            return {
                "triggered": True,
                "training_success": True,
                "promoted": False,
                "reason": msg,
                "manifest": candidate["manifest"],
                "readiness": readiness
            }
