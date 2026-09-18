"""Deterministic ML candidate model implementations and canonical model state extraction."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from decimal import Decimal, localcontext
from typing import Any

import numpy as np
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression, Ridge
from threadpoolctl import threadpool_limits

from btg_ai_trader.ml_engine.domain import (
    MLCandidateSpec,
    ModelNotFittedError,
    PredictiveCandidate,
    TrainingFailureError,
)
from btg_ai_trader.ml_engine.features import FittedFeaturePipeline
from btg_ai_trader.statistical_baselines.domain import (
    PredictionInput,
    PredictionResult,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.metrics import NumericPolicy

SUPPORTED_FAMILIES = {
    "logistic_regression",
    "ridge_regression",
    "random_forest_classifier",
    "random_forest_regressor",
    "gradient_boosting_classifier",
    "gradient_boosting_regressor",
}

ALLOWED_HYPERPARAMETERS: dict[str, set[str]] = {
    "logistic_regression": {"penalty", "C", "solver", "max_iter", "tol"},
    "ridge_regression": {"alpha", "solver", "max_iter", "tol"},
    "random_forest_classifier": {
        "n_estimators",
        "max_depth",
        "min_samples_split",
        "min_samples_leaf",
        "max_features",
    },
    "random_forest_regressor": {
        "n_estimators",
        "max_depth",
        "min_samples_split",
        "min_samples_leaf",
        "max_features",
    },
    "gradient_boosting_classifier": {
        "n_estimators",
        "learning_rate",
        "max_depth",
        "min_samples_split",
        "min_samples_leaf",
        "subsample",
    },
    "gradient_boosting_regressor": {
        "n_estimators",
        "learning_rate",
        "max_depth",
        "min_samples_split",
        "min_samples_leaf",
        "subsample",
    },
}


def _canonicalize_float(val: float) -> str:
    """Format float into stable scientific notation string to eliminate formatting variances."""
    if np.isnan(val):
        return "NaN"
    if np.isneginf(val):
        return "-Infinity"
    if np.isposinf(val):
        return "Infinity"
    return f"{val:.10e}"


def extract_model_state_digest(estimator: Any) -> str:
    """Extract canonical SHA-256 digest from fitted scikit-learn estimator learned parameters."""
    hasher = hashlib.sha256()

    # Linear models
    if hasattr(estimator, "coef_"):
        coef = np.asarray(estimator.coef_, dtype=np.float64)
        hasher.update(b"coef:")
        hasher.update(coef.tobytes())

    if hasattr(estimator, "intercept_"):
        intercept = np.asarray(estimator.intercept_, dtype=np.float64)
        hasher.update(b"intercept:")
        hasher.update(intercept.tobytes())

    if hasattr(estimator, "classes_"):
        classes = np.asarray(estimator.classes_)
        hasher.update(b"classes:")
        hasher.update(classes.tobytes())

    if hasattr(estimator, "n_features_in_"):
        hasher.update(f"n_features_in:{estimator.n_features_in_}".encode("ascii"))

    # Tree ensemble models
    if hasattr(estimator, "estimators_"):
        hasher.update(b"estimators:")
        est_list = np.asarray(estimator.estimators_).ravel()
        for idx, sub_tree in enumerate(est_list):
            hasher.update(f"tree_{idx}:".encode("ascii"))
            if hasattr(sub_tree, "tree_"):
                tree_obj = sub_tree.tree_
                hasher.update(tree_obj.feature.tobytes())
                hasher.update(tree_obj.threshold.tobytes())
                hasher.update(tree_obj.children_left.tobytes())
                hasher.update(tree_obj.children_right.tobytes())
                hasher.update(tree_obj.value.tobytes())

    # Gradient Boosting estimators have train_score_
    if hasattr(estimator, "train_score_"):
        train_score = np.asarray(estimator.train_score_, dtype=np.float64)
        hasher.update(b"train_score:")
        hasher.update(train_score.tobytes())

    return hasher.hexdigest()


def _convert_prediction_to_decimal(val: float, policy: NumericPolicy) -> Decimal:
    """Convert a floating-point prediction to exact quantized Decimal via NumericPolicy."""
    formatted = f"{val:.10f}"
    with localcontext(policy.get_context()):
        return +Decimal(formatted)



class BasePredictiveCandidate:
    """Base class providing validation, threadpool control, and state management for ML models."""

    def __init__(self, spec: MLCandidateSpec) -> None:
        if spec.family not in SUPPORTED_FAMILIES:
            raise ValueError(
                f"Unsupported family '{spec.family}'. Must be one of {sorted(SUPPORTED_FAMILIES)}"
            )

        allowed = ALLOWED_HYPERPARAMETERS[spec.family]
        unknown = set(spec.hyperparameters.keys()) - allowed
        if unknown:
            raise ValueError(
                f"Unknown hyperparameters for family '{spec.family}': {sorted(unknown)}"
            )

        self._spec = spec
        self._estimator: Any = None
        self._is_fitted = False
        self._model_state_digest = ""

    @property
    def spec(self) -> MLCandidateSpec:
        return self._spec

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    @property
    def model_state_digest(self) -> str:
        if not self._is_fitted:
            raise ModelNotFittedError("Model is not fitted; model_state_digest is unavailable")
        return self._model_state_digest

    @property
    def estimator(self) -> Any:
        return self._estimator


class LogisticRegressionCandidate(BasePredictiveCandidate):
    """Logistic Regression binary classification candidate."""

    def __init__(self, spec: MLCandidateSpec) -> None:
        if spec.family != "logistic_regression":
            raise ValueError(f"Spec family must be 'logistic_regression', got '{spec.family}'")
        if spec.target_contract.target_semantics != TargetSemantics.BINARY_PROBABILITY:
            raise ValueError(
                "LogisticRegressionCandidate requires BINARY_PROBABILITY target semantics"
            )
        super().__init__(spec)

        kwargs: dict[str, Any] = dict(spec.hyperparameters)
        kwargs.setdefault("solver", "lbfgs")
        kwargs.setdefault("max_iter", 1000)
        kwargs.setdefault("tol", 1e-4)
        seed = spec.rng_context.seed if spec.rng_context else None
        self._estimator = LogisticRegression(random_state=seed, **kwargs)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        if len(X) == 0 or len(y) == 0:
            raise TrainingFailureError("Cannot fit LogisticRegression on empty data")
        unique_classes = np.unique(y)
        if len(unique_classes) < 2:
            raise TrainingFailureError(
                f"LogisticRegression requires at least 2 classes, got {len(unique_classes)}"
            )

        try:
            with threadpool_limits(limits=1):
                self._estimator.fit(X, y)
        except Exception as e:
            raise TrainingFailureError(f"LogisticRegression fit failed: {e}") from e

        self._is_fitted = True
        self._model_state_digest = extract_model_state_digest(self._estimator)

    def predict(
        self,
        inputs: Sequence[PredictionInput],
        fitted_pipeline: FittedFeaturePipeline,
    ) -> list[PredictionResult]:
        if not self._is_fitted:
            raise ModelNotFittedError("Cannot predict with unfitted model")
        if not inputs:
            return []

        X = fitted_pipeline.transform(inputs)
        with threadpool_limits(limits=1):
            probs = self._estimator.predict_proba(X)

        # Class 1 probability
        class_1_idx = 1 if 1 in self._estimator.classes_ else (len(self._estimator.classes_) - 1)
        results: list[PredictionResult] = []
        for inp, p_row in zip(inputs, probs, strict=True):
            p1 = float(p_row[class_1_idx])
            prob_dec = _convert_prediction_to_decimal(p1, self._spec.numeric_policy)
            results.append(
                PredictionResult(
                    sample_id=inp.sample_id,
                    prediction_time=inp.feature_knowledge_time,
                    predicted_value=prob_dec,
                    predicted_probability=prob_dec,
                    predicted_class="1" if prob_dec >= Decimal("0.5") else "0",
                    is_cold_start=False,
                )
            )
        return results


class RidgeRegressionCandidate(BasePredictiveCandidate):
    """Ridge Regression continuous target candidate."""

    def __init__(self, spec: MLCandidateSpec) -> None:
        if spec.family != "ridge_regression":
            raise ValueError(f"Spec family must be 'ridge_regression', got '{spec.family}'")
        if spec.target_contract.target_semantics != TargetSemantics.CONTINUOUS:
            raise ValueError("RidgeRegressionCandidate requires CONTINUOUS target semantics")
        super().__init__(spec)

        kwargs: dict[str, Any] = dict(spec.hyperparameters)
        kwargs.setdefault("alpha", 1.0)
        seed = spec.rng_context.seed if spec.rng_context else None
        self._estimator = Ridge(random_state=seed, **kwargs)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        if len(X) == 0 or len(y) == 0:
            raise TrainingFailureError("Cannot fit RidgeRegression on empty data")

        try:
            with threadpool_limits(limits=1):
                self._estimator.fit(X, y)
        except Exception as e:
            raise TrainingFailureError(f"RidgeRegression fit failed: {e}") from e

        self._is_fitted = True
        self._model_state_digest = extract_model_state_digest(self._estimator)

    def predict(
        self,
        inputs: Sequence[PredictionInput],
        fitted_pipeline: FittedFeaturePipeline,
    ) -> list[PredictionResult]:
        if not self._is_fitted:
            raise ModelNotFittedError("Cannot predict with unfitted model")
        if not inputs:
            return []

        X = fitted_pipeline.transform(inputs)
        with threadpool_limits(limits=1):
            preds = self._estimator.predict(X)

        results: list[PredictionResult] = []
        for inp, pred_val in zip(inputs, preds, strict=True):
            val_dec = _convert_prediction_to_decimal(float(pred_val), self._spec.numeric_policy)
            results.append(
                PredictionResult(
                    sample_id=inp.sample_id,
                    prediction_time=inp.feature_knowledge_time,
                    predicted_value=val_dec,
                    predicted_probability=None,
                    predicted_class=None,
                    is_cold_start=False,
                )
            )
        return results


class RandomForestClassifierCandidate(BasePredictiveCandidate):
    """Random Forest binary classification candidate."""

    def __init__(self, spec: MLCandidateSpec) -> None:
        if spec.family != "random_forest_classifier":
            raise ValueError(f"Spec family must be 'random_forest_classifier', got '{spec.family}'")
        if spec.target_contract.target_semantics != TargetSemantics.BINARY_PROBABILITY:
            raise ValueError(
                "RandomForestClassifierCandidate requires BINARY_PROBABILITY target semantics"
            )
        if not spec.rng_context:
            raise ValueError("RandomForestClassifier requires an explicit RNGContext")
        super().__init__(spec)

        kwargs: dict[str, Any] = dict(spec.hyperparameters)
        kwargs.setdefault("n_estimators", 10)
        self._estimator = RandomForestClassifier(
            random_state=spec.rng_context.seed,
            n_jobs=1,
            **kwargs,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        if len(X) == 0 or len(y) == 0:
            raise TrainingFailureError("Cannot fit RandomForestClassifier on empty data")
        unique_classes = np.unique(y)
        if len(unique_classes) < 2:
            raise TrainingFailureError(
                f"RandomForestClassifier requires at least 2 classes, got {len(unique_classes)}"
            )

        try:
            with threadpool_limits(limits=1):
                self._estimator.fit(X, y)
        except Exception as e:
            raise TrainingFailureError(f"RandomForestClassifier fit failed: {e}") from e

        self._is_fitted = True
        self._model_state_digest = extract_model_state_digest(self._estimator)

    def predict(
        self,
        inputs: Sequence[PredictionInput],
        fitted_pipeline: FittedFeaturePipeline,
    ) -> list[PredictionResult]:
        if not self._is_fitted:
            raise ModelNotFittedError("Cannot predict with unfitted model")
        if not inputs:
            return []

        X = fitted_pipeline.transform(inputs)
        with threadpool_limits(limits=1):
            probs = self._estimator.predict_proba(X)

        class_1_idx = 1 if 1 in self._estimator.classes_ else (len(self._estimator.classes_) - 1)
        results: list[PredictionResult] = []
        for inp, p_row in zip(inputs, probs, strict=True):
            p1 = float(p_row[class_1_idx])
            prob_dec = _convert_prediction_to_decimal(p1, self._spec.numeric_policy)
            results.append(
                PredictionResult(
                    sample_id=inp.sample_id,
                    prediction_time=inp.feature_knowledge_time,
                    predicted_value=prob_dec,
                    predicted_probability=prob_dec,
                    predicted_class="1" if prob_dec >= Decimal("0.5") else "0",
                    is_cold_start=False,
                )
            )
        return results


class RandomForestRegressorCandidate(BasePredictiveCandidate):
    """Random Forest continuous target candidate."""

    def __init__(self, spec: MLCandidateSpec) -> None:
        if spec.family != "random_forest_regressor":
            raise ValueError(f"Spec family must be 'random_forest_regressor', got '{spec.family}'")
        if spec.target_contract.target_semantics != TargetSemantics.CONTINUOUS:
            raise ValueError("RandomForestRegressorCandidate requires CONTINUOUS target semantics")
        if not spec.rng_context:
            raise ValueError("RandomForestRegressor requires an explicit RNGContext")
        super().__init__(spec)

        kwargs: dict[str, Any] = dict(spec.hyperparameters)
        kwargs.setdefault("n_estimators", 10)
        self._estimator = RandomForestRegressor(
            random_state=spec.rng_context.seed,
            n_jobs=1,
            **kwargs,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        if len(X) == 0 or len(y) == 0:
            raise TrainingFailureError("Cannot fit RandomForestRegressor on empty data")

        try:
            with threadpool_limits(limits=1):
                self._estimator.fit(X, y)
        except Exception as e:
            raise TrainingFailureError(f"RandomForestRegressor fit failed: {e}") from e

        self._is_fitted = True
        self._model_state_digest = extract_model_state_digest(self._estimator)

    def predict(
        self,
        inputs: Sequence[PredictionInput],
        fitted_pipeline: FittedFeaturePipeline,
    ) -> list[PredictionResult]:
        if not self._is_fitted:
            raise ModelNotFittedError("Cannot predict with unfitted model")
        if not inputs:
            return []

        X = fitted_pipeline.transform(inputs)
        with threadpool_limits(limits=1):
            preds = self._estimator.predict(X)

        results: list[PredictionResult] = []
        for inp, pred_val in zip(inputs, preds, strict=True):
            val_dec = _convert_prediction_to_decimal(float(pred_val), self._spec.numeric_policy)
            results.append(
                PredictionResult(
                    sample_id=inp.sample_id,
                    prediction_time=inp.feature_knowledge_time,
                    predicted_value=val_dec,
                    predicted_probability=None,
                    predicted_class=None,
                    is_cold_start=False,
                )
            )
        return results


class GradientBoostingClassifierCandidate(BasePredictiveCandidate):
    """Gradient Boosting binary classification candidate."""

    def __init__(self, spec: MLCandidateSpec) -> None:
        if spec.family != "gradient_boosting_classifier":
            raise ValueError(
                f"Spec family must be 'gradient_boosting_classifier', got '{spec.family}'"
            )
        if spec.target_contract.target_semantics != TargetSemantics.BINARY_PROBABILITY:
            raise ValueError(
                "GradientBoostingClassifierCandidate requires BINARY_PROBABILITY target semantics"
            )
        if not spec.rng_context:
            raise ValueError("GradientBoostingClassifier requires an explicit RNGContext")
        super().__init__(spec)

        kwargs: dict[str, Any] = dict(spec.hyperparameters)
        kwargs.setdefault("n_estimators", 10)
        self._estimator = GradientBoostingClassifier(
            random_state=spec.rng_context.seed,
            **kwargs,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        if len(X) == 0 or len(y) == 0:
            raise TrainingFailureError("Cannot fit GradientBoostingClassifier on empty data")
        unique_classes = np.unique(y)
        if len(unique_classes) < 2:
            raise TrainingFailureError(
                f"GradientBoostingClassifier requires at least 2 classes, got {len(unique_classes)}"
            )

        try:
            with threadpool_limits(limits=1):
                self._estimator.fit(X, y)
        except Exception as e:
            raise TrainingFailureError(f"GradientBoostingClassifier fit failed: {e}") from e

        self._is_fitted = True
        self._model_state_digest = extract_model_state_digest(self._estimator)

    def predict(
        self,
        inputs: Sequence[PredictionInput],
        fitted_pipeline: FittedFeaturePipeline,
    ) -> list[PredictionResult]:
        if not self._is_fitted:
            raise ModelNotFittedError("Cannot predict with unfitted model")
        if not inputs:
            return []

        X = fitted_pipeline.transform(inputs)
        with threadpool_limits(limits=1):
            probs = self._estimator.predict_proba(X)

        class_1_idx = 1 if 1 in self._estimator.classes_ else (len(self._estimator.classes_) - 1)
        results: list[PredictionResult] = []
        for inp, p_row in zip(inputs, probs, strict=True):
            p1 = float(p_row[class_1_idx])
            prob_dec = _convert_prediction_to_decimal(p1, self._spec.numeric_policy)
            results.append(
                PredictionResult(
                    sample_id=inp.sample_id,
                    prediction_time=inp.feature_knowledge_time,
                    predicted_value=prob_dec,
                    predicted_probability=prob_dec,
                    predicted_class="1" if prob_dec >= Decimal("0.5") else "0",
                    is_cold_start=False,
                )
            )
        return results


class GradientBoostingRegressorCandidate(BasePredictiveCandidate):
    """Gradient Boosting continuous target candidate."""

    def __init__(self, spec: MLCandidateSpec) -> None:
        if spec.family != "gradient_boosting_regressor":
            raise ValueError(
                f"Spec family must be 'gradient_boosting_regressor', got '{spec.family}'"
            )
        if spec.target_contract.target_semantics != TargetSemantics.CONTINUOUS:
            raise ValueError(
                "GradientBoostingRegressorCandidate requires CONTINUOUS target semantics"
            )
        if not spec.rng_context:
            raise ValueError("GradientBoostingRegressor requires an explicit RNGContext")
        super().__init__(spec)

        kwargs: dict[str, Any] = dict(spec.hyperparameters)
        kwargs.setdefault("n_estimators", 10)
        self._estimator = GradientBoostingRegressor(
            random_state=spec.rng_context.seed,
            **kwargs,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        if len(X) == 0 or len(y) == 0:
            raise TrainingFailureError("Cannot fit GradientBoostingRegressor on empty data")

        try:
            with threadpool_limits(limits=1):
                self._estimator.fit(X, y)
        except Exception as e:
            raise TrainingFailureError(f"GradientBoostingRegressor fit failed: {e}") from e

        self._is_fitted = True
        self._model_state_digest = extract_model_state_digest(self._estimator)

    def predict(
        self,
        inputs: Sequence[PredictionInput],
        fitted_pipeline: FittedFeaturePipeline,
    ) -> list[PredictionResult]:
        if not self._is_fitted:
            raise ModelNotFittedError("Cannot predict with unfitted model")
        if not inputs:
            return []

        X = fitted_pipeline.transform(inputs)
        with threadpool_limits(limits=1):
            preds = self._estimator.predict(X)

        results: list[PredictionResult] = []
        for inp, pred_val in zip(inputs, preds, strict=True):
            val_dec = _convert_prediction_to_decimal(float(pred_val), self._spec.numeric_policy)
            results.append(
                PredictionResult(
                    sample_id=inp.sample_id,
                    prediction_time=inp.feature_knowledge_time,
                    predicted_value=val_dec,
                    predicted_probability=None,
                    predicted_class=None,
                    is_cold_start=False,
                )
            )
        return results


def create_candidate(spec: MLCandidateSpec) -> PredictiveCandidate:
    """Factory creating a candidate instance from a validated specification."""
    if spec.family == "logistic_regression":
        return LogisticRegressionCandidate(spec)
    elif spec.family == "ridge_regression":
        return RidgeRegressionCandidate(spec)
    elif spec.family == "random_forest_classifier":
        return RandomForestClassifierCandidate(spec)
    elif spec.family == "random_forest_regressor":
        return RandomForestRegressorCandidate(spec)
    elif spec.family == "gradient_boosting_classifier":
        return GradientBoostingClassifierCandidate(spec)
    elif spec.family == "gradient_boosting_regressor":
        return GradientBoostingRegressorCandidate(spec)
    else:
        raise ValueError(f"Unknown family '{spec.family}'")
