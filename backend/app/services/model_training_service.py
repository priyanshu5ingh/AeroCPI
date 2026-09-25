"""AeroCPI ML Training and Validation Pipeline."""
from __future__ import annotations

import datetime as dt
import logging
import statistics
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin
from sklearn.metrics import (
    accuracy_score, f1_score, balanced_accuracy_score, 
    log_loss, brier_score_loss, confusion_matrix, 
    mean_absolute_error, mean_squared_error
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sqlalchemy.orm import Session

from app.services.forecast_dataset_service import ForecastDatasetService, FEATURE_VERSION, TARGET_VERSION, MODEL_NUMERIC_FEATURES, classify_direction
from app.services.model_registry_service import ModelRegistryService

logger = logging.getLogger(__name__)

# Constants for strict gates
MIN_TRAINING_EXAMPLES = 50
MIN_ROUTES = 5
MIN_CLASS_SUPPORT = 5
MIN_TEMPORAL_COVERAGE_DAYS = 7
MIN_HOLDOUT_FRACTION = 0.15


class PromotionGateException(Exception):
    """Raised when a candidate model fails strict promotion validation."""
    pass


class TemporalPersistenceRegressor(BaseEstimator, RegressorMixin):
    def __init__(self, feature_idx: int):
        self.feature_idx = feature_idx
    def fit(self, X, y):
        return self
    def predict(self, X):
        return [float(row[self.feature_idx]) for row in X]


class TemporalPersistenceClassifier(BaseEstimator, ClassifierMixin):
    def __init__(self, feature_idx: int, classes_: list):
        self.feature_idx = feature_idx
        self.classes_ = np.array(classes_)
    def fit(self, X, y):
        return self
    def predict(self, X):
        return [classify_direction(float(row[self.feature_idx])) for row in X]
    def predict_proba(self, X):
        y_pred = self.predict(X)
        proba = np.zeros((len(X), len(self.classes_)))
        for i, yp in enumerate(y_pred):
            if yp in self.classes_:
                proba[i, list(self.classes_).index(yp)] = 1.0
        return proba


class ModelTrainingService:
    
    @classmethod
    def train_candidate(cls, db: Session, model_version: str = "AEROGUIDE_ML_V1", allow_synthetic_override: bool = False) -> Dict[str, Any]:
        """
        Trains and validates a candidate model from the production dataset.
        Returns the registry artifact dict. Does NOT promote to production.
        """
        # 1. Fetch eligible data
        examples = ForecastDatasetService.build_examples(db, horizon_days=7)
        summary = ForecastDatasetService.dataset_summary(examples)
        
        # 2. Strict INSUFFICIENT_DATA check
        if not allow_synthetic_override:
            cls._check_dataset_readiness(summary)
            
        if not examples:
            raise PromotionGateException("Dataset is entirely empty. Cannot train.")

        # 3. Temporal Split (Walk-forward + Holdout)
        train_ex, holdout_ex = cls._temporal_split(examples, holdout_fraction=MIN_HOLDOUT_FRACTION)
        
        if not holdout_ex and not allow_synthetic_override:
             raise PromotionGateException("Insufficient temporal depth for a chronological holdout.")

        # 4. Feature Extraction
        X_train, y_train_clf, y_train_reg = cls._extract_matrices(train_ex)
        X_holdout, y_holdout_clf, y_holdout_reg = cls._extract_matrices(holdout_ex)
        
        # 5. Model Definition
        preprocessor = StandardScaler()
        
        clf = Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', HistGradientBoostingClassifier(random_state=42, max_iter=100))
        ])
        
        reg = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', HistGradientBoostingRegressor(random_state=42, max_iter=100))
        ])
        
        # Pre-fit classes for metrics and baselines
        classes_ = np.unique(y_train_clf + y_holdout_clf)
        
        # Meaningful Baselines
        recent_7d_idx = MODEL_NUMERIC_FEATURES.index("recent_7d_change_pct")
        clf_baseline = TemporalPersistenceClassifier(feature_idx=recent_7d_idx, classes_=list(classes_))
        reg_baseline = TemporalPersistenceRegressor(feature_idx=recent_7d_idx)
        
        dummy_clf = DummyClassifier(strategy='prior')
        dummy_reg = DummyRegressor(strategy='mean')

        # 6. Walk-Forward Validation (Expanding Window) on Training Set
        t0 = time.time()
        cv_metrics = []
        if len(X_train) >= 4:
            tscv = TimeSeriesSplit(n_splits=3)
            for train_idx, val_idx in tscv.split(X_train):
                X_f_train = [X_train[i] for i in train_idx]
                y_f_train = [y_train_clf[i] for i in train_idx]
                X_f_val = [X_train[i] for i in val_idx]
                y_f_val = [y_train_clf[i] for i in val_idx]
                
                if len(np.unique(y_f_train)) > 1:
                    fold_clf = Pipeline([('p', StandardScaler()), ('c', HistGradientBoostingClassifier(random_state=42))])
                    fold_clf.fit(X_f_train, y_f_train)
                    y_pred = fold_clf.predict(X_f_val)
                    cv_metrics.append(accuracy_score(y_f_val, y_pred))

        # 7. Final Fit
        clf.fit(X_train, y_train_clf)
        reg.fit(X_train, y_train_reg)
        dummy_clf.fit(X_train, y_train_clf)
        dummy_reg.fit(X_train, y_train_reg)
        fit_time = time.time() - t0

        # 8. Evaluate Metrics on Untouched Holdout
        metrics = cls._evaluate_holdout(
            clf, reg, clf_baseline, reg_baseline, dummy_clf, dummy_reg,
            X_holdout, y_holdout_clf, y_holdout_reg, classes_
        )
        metrics["walk_forward_cv_accuracy"] = cv_metrics
        
        # 9. Registry Bundle
        bundle = {
            "classifier": clf,
            "regressor": reg,
            "clf_baseline": clf_baseline,
            "reg_baseline": reg_baseline,
            "feature_schema": MODEL_NUMERIC_FEATURES,
            "classes": list(clf.classes_) if hasattr(clf, "classes_") else list(classes_)
        }
        
        manifest = {
            "status": "CANDIDATE",
            "model_architecture": "HistGradientBoosting",
            "feature_version": FEATURE_VERSION,
            "target_version": TARGET_VERSION,
            "training_examples": len(train_ex),
            "holdout_examples": len(holdout_ex),
            "walk_forward_folds": 3 if cv_metrics else 0,
            "metrics": metrics,
            "fit_time_seconds": round(fit_time, 2),
            "training_summary": summary
        }
        
        return ModelRegistryService.save_candidate(bundle, manifest, model_version)

    @classmethod
    def evaluate_promotion_gates(cls, candidate: Dict[str, Any]) -> Tuple[bool, List[str]]:
        reasons = []
        manifest = candidate["manifest"]
        
        # Schema checks
        if manifest.get("feature_version") != FEATURE_VERSION:
            reasons.append(f"Feature schema mismatch: {manifest.get('feature_version')} != {FEATURE_VERSION}")
        if manifest.get("target_version") != TARGET_VERSION:
            reasons.append(f"Target schema mismatch: {manifest.get('target_version')} != {TARGET_VERSION}")
            
        metrics = manifest.get("metrics", {})
        if not metrics:
            reasons.append("Missing evaluation metrics.")
            return False, reasons
            
        clf_metrics = metrics.get("classification", {})
        clf_baseline = clf_metrics.get("temporal_baseline", {})
        
        acc = clf_metrics.get("accuracy", 0)
        acc_base = clf_baseline.get("accuracy", 1.0)
        f1 = clf_metrics.get("macro_f1", 0)
        f1_base = clf_baseline.get("macro_f1", 1.0)
        
        if acc <= acc_base and f1 <= f1_base and manifest.get("holdout_examples", 0) > 0:
            reasons.append(f"Candidate classification (acc={acc:.3f}, f1={f1:.3f}) fails to beat temporal persistence (acc={acc_base:.3f}, f1={f1_base:.3f}).")
            
        reg_metrics = metrics.get("regression", {})
        reg_baseline = reg_metrics.get("temporal_baseline", {})
        
        mae = reg_metrics.get("mae", 9999)
        mae_base = reg_baseline.get("mae", 0)
        
        if mae >= mae_base and manifest.get("holdout_examples", 0) > 0:
            reasons.append(f"Candidate regression MAE ({mae:.3f}) fails to beat temporal persistence ({mae_base:.3f}).")
            
        if manifest.get("holdout_examples", 0) == 0:
            reasons.append("Zero holdout examples evaluated. Model cannot be promoted.")
            
        status = manifest.get("status")
        if status not in ["CANDIDATE", "VALIDATED"]:
            reasons.append(f"Invalid model registry state for promotion: {status}")

        return len(reasons) == 0, reasons
        
    @classmethod
    def promote_candidate(cls, candidate: Dict[str, Any]) -> Dict[str, Any]:
        passed, reasons = cls.evaluate_promotion_gates(candidate)
        if not passed:
            raise PromotionGateException(f"Candidate failed promotion gates: {', '.join(reasons)}")
        return ModelRegistryService.promote(candidate)

    # --- Internals ---
    
    @classmethod
    def _check_dataset_readiness(cls, summary: Dict[str, Any]):
        labels = summary.get("label_counts", {})
        span = summary.get("prediction_date_span_days", 0)
        
        if summary.get("examples", 0) < MIN_TRAINING_EXAMPLES:
            raise PromotionGateException(f"INSUFFICIENT_DATA: Requires >= {MIN_TRAINING_EXAMPLES} pairs.")
        if summary.get("routes", 0) < MIN_ROUTES:
            raise PromotionGateException(f"INSUFFICIENT_DATA: Requires >= {MIN_ROUTES} routes.")
        for k in ("UP", "STABLE", "DOWN"):
            if labels.get(k, 0) < MIN_CLASS_SUPPORT:
                 raise PromotionGateException(f"INSUFFICIENT_DATA: Requires > {MIN_CLASS_SUPPORT} '{k}' examples.")
        if span < MIN_TEMPORAL_COVERAGE_DAYS:
            raise PromotionGateException(f"INSUFFICIENT_DATA: Requires >= {MIN_TEMPORAL_COVERAGE_DAYS} days of temporal coverage.")

    @classmethod
    def _temporal_split(cls, examples: List[Dict[str, Any]], holdout_fraction: float) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        if not examples:
            return [], []
            
        sorted_ex = sorted(examples, key=lambda x: x["prediction_timestamp"])
        split_idx = int(len(sorted_ex) * (1.0 - holdout_fraction))
        if split_idx == len(sorted_ex) and len(sorted_ex) > 1:
            split_idx = len(sorted_ex) - 1
            
        train = sorted_ex[:split_idx]
        holdout = sorted_ex[split_idx:]
        return train, holdout

    @classmethod
    def _extract_matrices(cls, examples: List[Dict[str, Any]]) -> Tuple[List[List[float]], List[str], List[float]]:
        X = []
        y_clf = []
        y_reg = []
        for ex in examples:
            row = []
            for col in MODEL_NUMERIC_FEATURES:
                row.append(float(ex["features"].get(col, 0.0)))
            X.append(row)
            y_clf.append(ex["target_direction"])
            y_reg.append(ex["target_delta_pct"])
        return X, y_clf, y_reg

    @classmethod
    def _evaluate_holdout(
        cls, clf, reg, clf_baseline, reg_baseline, dummy_clf, dummy_reg,
        X_holdout, y_holdout_clf, y_holdout_reg, classes
    ) -> Dict[str, Any]:
        if not X_holdout:
            return {}
            
        X_df = X_holdout
        
        y_pred = clf.predict(X_df)
        y_prob = clf.predict_proba(X_df)
        
        y_pred_base = clf_baseline.predict(X_df)
        y_pred_dummy = dummy_clf.predict(X_df)
        
        try:
            ll = log_loss(y_holdout_clf, y_prob, labels=classes)
        except ValueError:
            ll = None
            
        try:
            up_idx = list(classes).index('UP') if 'UP' in classes else None
            if up_idx is not None:
                y_bin = [1 if y == 'UP' else 0 for y in y_holdout_clf]
                bs = brier_score_loss(y_bin, y_prob[:, up_idx])
            else:
                bs = None
        except ValueError:
            bs = None

        try:
            cm = confusion_matrix(y_holdout_clf, y_pred, labels=classes).tolist()
        except ValueError:
            cm = []
        
        clf_metrics = {
            "accuracy": accuracy_score(y_holdout_clf, y_pred),
            "macro_f1": f1_score(y_holdout_clf, y_pred, average='macro', zero_division=0),
            "balanced_accuracy": balanced_accuracy_score(y_holdout_clf, y_pred),
            "log_loss": ll,
            "brier_score_UP": bs,
            "confusion_matrix": cm,
            "temporal_baseline": {
                "accuracy": accuracy_score(y_holdout_clf, y_pred_base),
                "macro_f1": f1_score(y_holdout_clf, y_pred_base, average='macro', zero_division=0),
            },
            "dummy_baseline": {
                "accuracy": accuracy_score(y_holdout_clf, y_pred_dummy),
            }
        }
        
        y_pred_reg = reg.predict(X_df)
        y_pred_reg_base = reg_baseline.predict(X_df)
        y_pred_reg_dummy = dummy_reg.predict(X_df)
        
        reg_metrics = {
            "mae": mean_absolute_error(y_holdout_reg, y_pred_reg),
            "rmse": float(np.sqrt(mean_squared_error(y_holdout_reg, y_pred_reg))),
            "temporal_baseline": {
                "mae": mean_absolute_error(y_holdout_reg, y_pred_reg_base),
                "rmse": float(np.sqrt(mean_squared_error(y_holdout_reg, y_pred_reg_base))),
            },
            "dummy_baseline": {
                "mae": mean_absolute_error(y_holdout_reg, y_pred_reg_dummy),
                "rmse": float(np.sqrt(mean_squared_error(y_holdout_reg, y_pred_reg_dummy))),
            }
        }
        
        return {
            "classification": clf_metrics,
            "regression": reg_metrics
        }
