"""Production AeroGuide forecasting engine."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import statistics
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, log_loss, mean_absolute_error
from sklearn.pipeline import Pipeline

from app.services.feature_builder_service import FeatureBuilderService
from app.services.forecast_dataset_service import (
    ForecastDatasetService,
    MODEL_NUMERIC_FEATURES,
    TARGET_VERSION,
    FEATURE_VERSION,
    FORECAST_HORIZON_DAYS,
)
from app.services.longitudinal_service import calculate_readiness_metrics
from app.services.model_registry_service import ModelRegistryService


class PersistenceBaselineModel:
    model_name = "PERSISTENCE_BASELINE"

    def predict_direction(self, features: Dict[str, Any]) -> str:
        return "STABLE"

    def predict_proba(self, features: Dict[str, Any]) -> Dict[str, float]:
        return {"up": 0.0, "stable": 1.0, "down": 0.0}


class ForecastingEngineService:
    """Real supervised training, chronological validation and artifact promotion."""

    MIN_EXAMPLES = 200
    MIN_ROUTES = 3
    MIN_PREDICTION_DAYS = 14
    MIN_PER_CLASS = 3
    MIN_FOLDS = 3
    MIN_F1_LIFT = 0.02

    MODEL_VERSION = "AEROGUIDE_ML_V1"

    @classmethod
    def get_model_status(cls, db: Session) -> Dict[str, Any]:
        loaded = ModelRegistryService.load_production()
        examples = ForecastDatasetService.build_examples(db)
        summary = ForecastDatasetService.dataset_summary(examples)
        can_train = summary.get("readiness_status") == "READY"
        return {
            "model_status": "PRODUCTION" if loaded else "INSUFFICIENT_DATA",
            "can_train_live": can_train,
            "training_examples": summary.get("examples", 0),
            "production_model": loaded["manifest"].get("model_version") if loaded else None,
            "readiness_status": summary.get("readiness_status", "INSUFFICIENT_DATA")
        }

    @staticmethod
    def _date_folds(examples: List[Dict[str, Any]], n_splits: int = 3) -> List[Tuple[List[int], List[int]]]:
        dates = sorted({example["prediction_date"] for example in examples})
        if len(dates) < n_splits + 1:
            return []
        folds = []
        for fold_idx in range(n_splits):
            train_end = max(1, round(len(dates) * (fold_idx + 1) / (n_splits + 1)))
            test_end = round(len(dates) * (fold_idx + 2) / (n_splits + 1)) if fold_idx < n_splits - 1 else len(dates)
            train_dates = set(dates[:train_end])
            test_dates = set(dates[train_end:test_end])
            train_idx = [i for i, e in enumerate(examples) if e["prediction_date"] in train_dates]
            test_idx = [i for i, e in enumerate(examples) if e["prediction_date"] in test_dates]
            if train_idx and test_idx:
                folds.append((train_idx, test_idx))
        return folds

    @staticmethod
    def _classifier(kind: str):
        if kind == "LOGISTIC_REGRESSION":
            estimator = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)
        elif kind == "RANDOM_FOREST":
            estimator = RandomForestClassifier(
                n_estimators=350,
                max_depth=8,
                min_samples_leaf=2,
                class_weight="balanced_subsample",
                random_state=42,
                n_jobs=-1,
            )
        else:
            raise ValueError(f"Unknown classifier: {kind}")
        return Pipeline([
            ("vectorizer", DictVectorizer(sparse=True)),
            ("model", estimator),
        ])

    @staticmethod
    def _regressor(kind: str):
        if kind == "RIDGE":
            estimator = Ridge(alpha=2.0)
        elif kind == "RANDOM_FOREST_REGRESSOR":
            estimator = RandomForestRegressor(
                n_estimators=350,
                max_depth=10,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            )
        else:
            raise ValueError(f"Unknown regressor: {kind}")
        return Pipeline([
            ("vectorizer", DictVectorizer(sparse=True)),
            ("model", estimator),
        ])

    @staticmethod
    def _brier(y_true: List[str], probabilities: List[List[float]], classes: List[str]) -> float:
        index = {label: i for i, label in enumerate(classes)}
        scores = []
        for truth, prob in zip(y_true, probabilities):
            target = [0.0] * len(classes)
            target[index[truth]] = 1.0
            scores.append(sum((float(p) - float(t)) ** 2 for p, t in zip(prob, target)))
        return float(statistics.mean(scores)) if scores else float("nan")

    @classmethod
    def _evaluate_classifier(cls, examples, kind, folds):
        results = []
        for train_idx, test_idx in folds:
            y_train = [examples[i]["target_direction"] for i in train_idx]
            y_test = [examples[i]["target_direction"] for i in test_idx]
            if len(set(y_train)) < 2:
                continue
            model = cls._classifier(kind)
            model.fit([examples[i]["features"] for i in train_idx], y_train)
            predictions = model.predict([examples[i]["features"] for i in test_idx]).tolist()
            probabilities = model.predict_proba([examples[i]["features"] for i in test_idx]).tolist()
            classes = [str(c) for c in model.named_steps["model"].classes_]
            results.append({
                "accuracy": accuracy_score(y_test, predictions),
                "balanced_accuracy": balanced_accuracy_score(y_test, predictions),
                "macro_f1": f1_score(y_test, predictions, labels=["DOWN", "STABLE", "UP"], average="macro", zero_division=0),
                "log_loss": log_loss(y_test, probabilities, labels=classes),
                "brier": cls._brier(y_test, probabilities, classes),
            })
        if not results:
            raise ValueError(f"No valid temporal folds for {kind}")
        return {
            "model": kind,
            "folds_evaluated": len(results),
            "accuracy": round(statistics.mean(r["accuracy"] for r in results), 4),
            "balanced_accuracy": round(statistics.mean(r["balanced_accuracy"] for r in results), 4),
            "macro_f1": round(statistics.mean(r["macro_f1"] for r in results), 4),
            "log_loss": round(statistics.mean(r["log_loss"] for r in results), 4),
            "brier_score": round(statistics.mean(r["brier"] for r in results), 4),
            "fold_scores": results,
        }

    @classmethod
    def _evaluate_baseline(cls, examples, folds):
        results = []
        for _, test_idx in folds:
            y_test = [examples[i]["target_direction"] for i in test_idx]
            predictions = ["STABLE"] * len(y_test)
            probabilities = [[0.0, 1.0, 0.0] for _ in y_test]
            results.append({
                "accuracy": accuracy_score(y_test, predictions),
                "balanced_accuracy": balanced_accuracy_score(y_test, predictions),
                "macro_f1": f1_score(y_test, predictions, labels=["DOWN", "STABLE", "UP"], average="macro", zero_division=0),
                "log_loss": log_loss(y_test, probabilities, labels=["DOWN", "STABLE", "UP"]),
                "brier": cls._brier(y_test, probabilities, ["DOWN", "STABLE", "UP"]),
            })
        return {
            "model": "PERSISTENCE_BASELINE",
            "folds_evaluated": len(results),
            "accuracy": round(statistics.mean(r["accuracy"] for r in results), 4),
            "balanced_accuracy": round(statistics.mean(r["balanced_accuracy"] for r in results), 4),
            "macro_f1": round(statistics.mean(r["macro_f1"] for r in results), 4),
            "log_loss": round(statistics.mean(r["log_loss"] for r in results), 4),
            "brier_score": round(statistics.mean(r["brier"] for r in results), 4),
            "fold_scores": results,
        }

    @classmethod
    def _evaluate_regressor(cls, examples, kind, folds):
        results = []
        for train_idx, test_idx in folds:
            model = cls._regressor(kind)
            model.fit(
                [examples[i]["features"] for i in train_idx],
                [float(examples[i]["target_delta_pct"]) for i in train_idx],
            )
            predictions = model.predict([examples[i]["features"] for i in test_idx])
            actuals = [float(examples[i]["target_delta_pct"]) for i in test_idx]
            results.append({"mae": mean_absolute_error(actuals, predictions)})
        if not results:
            raise ValueError(f"No valid temporal folds for {kind}")
        return {
            "model": kind,
            "folds_evaluated": len(results),
            "mae": round(statistics.mean(r["mae"] for r in results), 4),
            "fold_scores": results,
        }

    @classmethod
    def _gate_reasons(cls, summary):
        reasons = []
        if summary["examples"] < cls.MIN_EXAMPLES:
            reasons.append(f"Need at least {cls.MIN_EXAMPLES} valid 7-day examples; currently {summary['examples']}.")
        if summary["routes"] < cls.MIN_ROUTES:
            reasons.append(f"Need at least {cls.MIN_ROUTES} routes; currently {summary['routes']}.")
        if summary["prediction_date_span_days"] < cls.MIN_PREDICTION_DAYS:
            reasons.append(f"Need at least {cls.MIN_PREDICTION_DAYS} days of prediction history; currently {summary['prediction_date_span_days']}.")
        for label, count in summary["label_counts"].items():
            if count < cls.MIN_PER_CLASS:
                reasons.append(f"Need at least {cls.MIN_PER_CLASS} examples for {label}; currently {count}.")
        return reasons

    @classmethod
    def get_model_status(cls, db: Session) -> Dict[str, Any]:
        examples = ForecastDatasetService.build_examples(db)
        summary = ForecastDatasetService.dataset_summary(examples)
        production = ModelRegistryService.load_production()
        readiness = calculate_readiness_metrics(db)

        if production:
            return {
                "model_status": "PRODUCTION",
                "training_gate": "OPEN_FOR_INFERENCE",
                "can_train_live": True,
                "production_model_version": production["manifest"].get("model_version"),
                "dataset": summary,
                "reason": "A validated production artifact is available.",
                "readiness": readiness,
            }

        reasons = cls._gate_reasons(summary)
        return {
            "model_status": "INSUFFICIENT_DATA" if reasons else "READY_TO_TRAIN",
            "training_gate": "LOCKED" if reasons else "OPEN_FOR_TRAINING",
            "can_train_live": not bool(reasons),
            "production_model_version": None,
            "dataset": summary,
            "gate_reasons": reasons,
            "reason": "Training is locked until empirical evidence is sufficient." if reasons else "Training gate satisfied.",
            "readiness": readiness,
        }

    @classmethod
    def evaluate_walk_forward(cls, db: Session) -> Dict[str, Any]:
        examples = ForecastDatasetService.build_examples(db)
        summary = ForecastDatasetService.dataset_summary(examples)
        folds = cls._date_folds(examples, 3)

        if len(examples) < 10 or len(folds) < cls.MIN_FOLDS:
            return {
                "status": "INSUFFICIENT_TEMPORAL_EVIDENCE",
                "dataset": summary,
                "folds": len(folds),
                "required_folds": cls.MIN_FOLDS,
            }

        baseline = cls._evaluate_baseline(examples, folds)
        classifiers = []
        for kind in ("LOGISTIC_REGRESSION", "RANDOM_FOREST"):
            try:
                classifiers.append(cls._evaluate_classifier(examples, kind, folds))
            except Exception as exc:
                classifiers.append({"model": kind, "status": "FAILED", "error": str(exc)})
        valid = [x for x in classifiers if x.get("status") != "FAILED"]
        best_classifier = min(valid, key=lambda x: (-x["macro_f1"], x["log_loss"], x["brier_score"])) if valid else None

        regressors = []
        for kind in ("RIDGE", "RANDOM_FOREST_REGRESSOR"):
            try:
                regressors.append(cls._evaluate_regressor(examples, kind, folds))
            except Exception as exc:
                regressors.append({"model": kind, "status": "FAILED", "error": str(exc)})
        valid_reg = [x for x in regressors if x.get("status") != "FAILED"]
        best_regressor = min(valid_reg, key=lambda x: x["mae"]) if valid_reg else None

        gate_reasons = cls._gate_reasons(summary)
        promotion_eligible = bool(
            best_classifier
            and best_classifier["folds_evaluated"] >= cls.MIN_FOLDS
            and best_classifier["macro_f1"] >= baseline["macro_f1"] + cls.MIN_F1_LIFT
            and best_classifier["brier_score"] < baseline["brier_score"]
            and not gate_reasons
        )

        return {
            "status": "PROMOTION_ELIGIBLE" if promotion_eligible else "VALIDATED_NOT_PROMOTABLE",
            "dataset": summary,
            "folds": len(folds),
            "baseline": baseline,
            "classifiers": classifiers,
            "best_classifier": best_classifier,
            "regressors": regressors,
            "best_regressor": best_regressor,
            "promotion_gate": {
                "eligible": promotion_eligible,
                "min_f1_lift": cls.MIN_F1_LIFT,
                "gate_reasons": gate_reasons,
            },
            "validation_strategy": "EXPANDING_TIME_WINDOWS_BY_PREDICTION_DATE",
        }

    @classmethod
    def train_live(cls, db: Session) -> Dict[str, Any]:
        examples = ForecastDatasetService.build_examples(db)
        summary = ForecastDatasetService.dataset_summary(examples)
        reasons = cls._gate_reasons(summary)
        if reasons:
            return {
                "status": "LOCKED",
                "model_status": "INSUFFICIENT_DATA",
                "dataset": summary,
                "gate_reasons": reasons,
                "message": "No model was trained.",
            }

        evaluation = cls.evaluate_walk_forward(db)
        if evaluation.get("status") != "PROMOTION_ELIGIBLE":
            return {
                "status": "LOCKED",
                "model_status": "VALIDATED_NOT_PROMOTABLE",
                "evaluation": evaluation,
                "message": "Candidate models did not satisfy the promotion gate.",
            }

        best_name = evaluation["best_classifier"]["model"]
        classifier = cls._classifier(best_name)
        x_all = [e["features"] for e in examples]
        y_class = [e["target_direction"] for e in examples]
        classifier.fit(x_all, y_class)

        calibrated = CalibratedClassifierCV(estimator=classifier, method="sigmoid", cv=3)
        calibrated.fit(x_all, y_class)

        best_reg_name = evaluation["best_regressor"]["model"] if evaluation.get("best_regressor") else None
        regressor = None
        residual_q90 = None

        if best_reg_name:
            regressor = cls._regressor(best_reg_name)
            y_reg = [float(e["target_delta_pct"]) for e in examples]
            regressor.fit(x_all, y_reg)
            residuals = []
            for train_idx, test_idx in cls._date_folds(examples, 3):
                fold_model = cls._regressor(best_reg_name)
                fold_model.fit(
                    [examples[i]["features"] for i in train_idx],
                    [float(examples[i]["target_delta_pct"]) for i in train_idx],
                )
                predictions = fold_model.predict([examples[i]["features"] for i in test_idx])
                actuals = [float(examples[i]["target_delta_pct"]) for i in test_idx]
                residuals.extend(abs(a - float(p)) for a, p in zip(actuals, predictions))
            if residuals:
                residuals.sort()
                residual_q90 = float(residuals[min(len(residuals) - 1, math.ceil(0.90 * len(residuals)) - 1)])

        fingerprint_payload = {
            "dataset": summary,
            "evaluation": evaluation,
            "target_version": TARGET_VERSION,
            "feature_version": FEATURE_VERSION,
        }
        fingerprint = hashlib.sha256(
            json.dumps(fingerprint_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

        manifest = {
            "status": "CANDIDATE",
            "model_version": cls.MODEL_VERSION,
            "classifier_name": best_name,
            "regressor_name": best_reg_name,
            "target_version": TARGET_VERSION,
            "feature_version": FEATURE_VERSION,
            "training_cutoff": max(e["prediction_timestamp"] for e in examples),
            "dataset_fingerprint": fingerprint,
            "dataset_summary": summary,
            "evaluation": evaluation,
            "probability_calibration": "SIGMOID_CV_3_AFTER_TEMPORAL_SELECTION",
            "regression_residual_band": {
                "coverage_label": "90P_EMPIRICAL_BACKTEST_RESIDUAL_BAND",
                "absolute_delta_pct": residual_q90,
            },
        }

        bundle = {
            "classifier": calibrated,
            "regressor": regressor,
            "model_manifest": manifest,
            "feature_names": MODEL_NUMERIC_FEATURES,
        }
        candidate = ModelRegistryService.save_candidate(bundle, manifest, cls.MODEL_VERSION)
        production = ModelRegistryService.promote(candidate)

        return {
            "status": "PROMOTED",
            "model_status": "PRODUCTION",
            "model_version": cls.MODEL_VERSION,
            "candidate": candidate,
            "production": production,
            "evaluation": evaluation,
        }

    @classmethod
    def predict_route(cls, db: Session, route_id: str, travel_date: str, prediction_timestamp: Optional[dt.datetime] = None) -> Dict[str, Any]:
        loaded = ModelRegistryService.load_production()
        if not loaded:
            return {
                "status": "INSUFFICIENT_EVIDENCE",
                "model_status": "NOT_READY",
                "route_id": route_id.upper(),
                "travel_date": travel_date,
                "probabilities": None,
                "expected_delta_pct": None,
                "prediction_interval": None,
                "message": "No promoted empirical model is available.",
            }

        prediction_ts = prediction_timestamp or dt.datetime.now(dt.timezone.utc)
        features = FeatureBuilderService.build_feature_vector_at_timestamp(
            db=db,
            route_id=route_id,
            travel_date_str=travel_date,
            prediction_timestamp=prediction_ts,
            carrier_code=None,
            cabin="ECONOMY",
        )
        if features.get("current_fare") is None:
            return {
                "status": "INSUFFICIENT_EVIDENCE",
                "model_status": "PRODUCTION",
                "model_version": loaded["manifest"].get("model_version"),
                "route_id": route_id.upper(),
                "travel_date": travel_date,
                "probabilities": None,
                "expected_delta_pct": None,
                "prediction_interval": None,
                "message": "No contemporaneous observed fare exists for this route and departure date.",
            }

        feature_vector = [
            float(features.get(key, 0.0) if features.get(key) is not None else 0.0)
            for key in MODEL_NUMERIC_FEATURES
        ]

        classifier = loaded["bundle"]["classifier"]
        try:
            raw_probabilities = classifier.predict_proba([feature_vector])[0]
        except Exception:
            feature_row = {key: (0.0 if features.get(key) is None else features.get(key)) for key in MODEL_NUMERIC_FEATURES}
            raw_probabilities = classifier.predict_proba([feature_row])[0]

        classes = [str(label) for label in classifier.classes_]
        probabilities = {
            label.lower(): round(float(probability), 4)
            for label, probability in zip(classes, raw_probabilities)
        }
        direction = max(zip(classes, raw_probabilities), key=lambda pair: float(pair[1]))[0]

        expected_delta = None
        prediction_interval = None
        regressor = loaded["bundle"].get("regressor")
        if regressor is not None:
            try:
                expected_delta = round(float(regressor.predict([feature_vector])[0]), 2)
            except Exception:
                expected_delta = round(float(regressor.predict([feature_row])[0]), 2)
            q90 = loaded["manifest"].get("regression_residual_band", {}).get("absolute_delta_pct")
            if q90 is not None:
                q90 = float(q90)
                prediction_interval = {
                    "lower": round(expected_delta - q90, 2),
                    "upper": round(expected_delta + q90, 2),
                    "type": "90P_EMPIRICAL_BACKTEST_RESIDUAL_BAND",
                }

        return {
            "status": "MODEL_PREDICTION",
            "model_status": "PRODUCTION",
            "model_version": loaded["manifest"].get("model_version"),
            "route_id": route_id.upper(),
            "travel_date": travel_date,
            "prediction_timestamp": prediction_ts.isoformat(),
            "forecast_horizon_days": FORECAST_HORIZON_DAYS,
            "direction": direction,
            "probabilities": probabilities,
            "expected_delta_pct": expected_delta,
            "prediction_interval": prediction_interval,
            "current_fare": features.get("current_fare"),
            "fare_percentile": features.get("fare_percentile"),
            "recent_7d_change_pct": features.get("recent_7d_change_pct"),
            "source_median_spread_pct": features.get("source_median_spread_pct"),
            "training_examples": loaded["manifest"].get("dataset_summary", {}).get("examples"),
            "dataset_fingerprint": loaded["manifest"].get("dataset_fingerprint"),
            "message": "Prediction generated from the promoted empirical AeroGuide model.",
        }
