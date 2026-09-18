"""Deterministic scikit-learn candidate implementations and canonical learned-state digests."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from decimal import Decimal, localcontext
from typing import Any

import numpy as np
from sklearn import __version__ as sklearn_version
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

SUPPORTED_FAMILIES = frozenset(
    {
        "gradient_boosting_classifier",
        "gradient_boosting_regressor",
        "logistic_regression",
        "random_forest_classifier",
        "random_forest_regressor",
        "ridge_regression",
    }
)

ALLOWED_HYPERPARAMETERS: dict[str, frozenset[str]] = {
    "logistic_regression": frozenset({"penalty", "C", "solver", "max_iter", "tol"}),
    "ridge_regression": frozenset({"alpha", "solver", "max_iter", "tol"}),
    "random_forest_classifier": frozenset(
        {"n_estimators", "max_depth", "min_samples_split", "min_samples_leaf", "max_features"}
    ),
    "random_forest_regressor": frozenset(
        {"n_estimators", "max_depth", "min_samples_split", "min_samples_leaf", "max_features"}
    ),
    "gradient_boosting_classifier": frozenset(
        {
            "n_estimators",
            "learning_rate",
            "max_depth",
            "min_samples_split",
            "min_samples_leaf",
            "subsample",
        }
    ),
    "gradient_boosting_regressor": frozenset(
        {
            "n_estimators",
            "learning_rate",
            "max_depth",
            "min_samples_split",
            "min_samples_leaf",
            "subsample",
        }
    ),
}


def _update_array_digest(hasher: Any, label: str, value: Any) -> None:
    array = np.asarray(value)
    hasher.update(label.encode())
    hasher.update(b"\x00")
    hasher.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii"))
    hasher.update(b"\x00")

    if array.dtype.kind in {"O", "U", "S"}:
        hasher.update(b"text")
        values = np.asarray(array, dtype=str).tolist()
        hasher.update(
            json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode()
        )
        return

    canonical_dtype = array.dtype.newbyteorder("<")
    canonical = np.ascontiguousarray(array.astype(canonical_dtype, copy=False))
    hasher.update(canonical_dtype.str.encode("ascii"))
    hasher.update(b"\x00")
    hasher.update(canonical.tobytes(order="C"))


def extract_model_state_digest(estimator: Any) -> str:
    """Hash the supported estimator's learned state with explicit array metadata."""

    hasher = hashlib.sha256()
    hasher.update(
        f"{estimator.__class__.__module__}.{estimator.__class__.__qualname__}".encode()
    )

    for name in ("coef_", "intercept_", "classes_", "train_score_", "feature_importances_"):
        if hasattr(estimator, name):
            _update_array_digest(hasher, name, getattr(estimator, name))

    if hasattr(estimator, "n_features_in_"):
        hasher.update(
            f"n_features_in_:{int(estimator.n_features_in_)}".encode("ascii")
        )

    if hasattr(estimator, "estimators_"):
        estimators = np.asarray(estimator.estimators_, dtype=object).ravel()
        hasher.update(f"estimator_count:{len(estimators)}".encode("ascii"))
        for index, sub_estimator in enumerate(estimators):
            hasher.update(f"estimator:{index}".encode("ascii"))
            if hasattr(sub_estimator, "tree_"):
                tree = sub_estimator.tree_
                for name in (
                    "children_left",
                    "children_right",
                    "feature",
                    "threshold",
                    "value",
                ):
                    _update_array_digest(hasher, f"tree.{name}", getattr(tree, name))

    for scalar_name in ("n_classes_", "n_outputs_", "n_trees_per_iteration_"):
        if hasattr(estimator, scalar_name):
            value = getattr(estimator, scalar_name)
            scalar_payload = json.dumps(
                np.asarray(value).tolist(),
                separators=(",", ":"),
            )
            hasher.update(f"{scalar_name}:{scalar_payload}".encode())

    return hasher.hexdigest()


def _convert_prediction_to_decimal(value: float, policy: NumericPolicy) -> Decimal:
    if not np.isfinite(value):
        raise ValueError("Non-finite model prediction is forbidden")
    with localcontext(policy.get_context()):
        return +Decimal(format(value, ".17g"))


def _validate_rng(spec: MLCandidateSpec, required: bool) -> int | None:
    context = spec.rng_context
    if context is None:
        if required:
            raise ValueError(
                f"Candidate family '{spec.family}' requires explicit RNGContext"
            )
        return None
    if context.algorithm != "sklearn_random_state":
        raise ValueError("RNGContext must describe sklearn_random_state semantics")
    if context.library_version and context.library_version != sklearn_version:
        raise ValueError(
            "RNGContext library_version does not match installed scikit-learn"
        )
    return context.seed


class BasePredictiveCandidate:
    """Common candidate validation and fitted-state surface."""

    def __init__(self, spec: MLCandidateSpec) -> None:
        if spec.family not in SUPPORTED_FAMILIES:
            raise ValueError(
                f"Unsupported family '{spec.family}'. Must be one of {sorted(SUPPORTED_FAMILIES)}"
            )
        unknown = set(spec.hyperparameters) - set(ALLOWED_HYPERPARAMETERS[spec.family])
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
            raise ModelNotFittedError(
                "Model is not fitted; model_state_digest is unavailable"
            )
        return self._model_state_digest

    @property
    def estimator(self) -> Any:
        return self._estimator

    def _finish_fit(self) -> None:
        self._is_fitted = True
        self._model_state_digest = extract_model_state_digest(self._estimator)

    def _matrix(
        self, inputs: Sequence[PredictionInput], pipeline: FittedFeaturePipeline
    ) -> np.ndarray:
        if not self._is_fitted:
            raise ModelNotFittedError("Cannot predict with unfitted model")
        return pipeline.transform(inputs)


class LogisticRegressionCandidate(BasePredictiveCandidate):
    def __init__(self, spec: MLCandidateSpec) -> None:
        if spec.family != "logistic_regression":
            raise ValueError("Spec family must be 'logistic_regression'")
        if spec.target_contract.target_semantics is not TargetSemantics.BINARY_PROBABILITY:
            raise ValueError("LogisticRegressionCandidate requires BINARY_PROBABILITY")
        super().__init__(spec)
        kwargs = dict(spec.hyperparameters)
        kwargs.setdefault("solver", "lbfgs")
        kwargs.setdefault("max_iter", 1000)
        kwargs.setdefault("tol", 1e-4)
        self._estimator = LogisticRegression(
            random_state=_validate_rng(spec, required=False), **kwargs
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        if len(X) == 0 or len(y) == 0:
            raise TrainingFailureError("Cannot fit LogisticRegression on empty data")
        if len(np.unique(y)) < 2:
            raise TrainingFailureError("LogisticRegression requires at least 2 classes")
        try:
            with threadpool_limits(limits=1):
                self._estimator.fit(X, y)
        except Exception as exc:
            raise TrainingFailureError(f"LogisticRegression fit failed: {exc}") from exc
        self._finish_fit()

    def predict(
        self, inputs: Sequence[PredictionInput], fitted_pipeline: FittedFeaturePipeline
    ) -> list[PredictionResult]:
        if not inputs:
            if not self._is_fitted:
                raise ModelNotFittedError("Cannot predict with unfitted model")
            return []
        X = self._matrix(inputs, fitted_pipeline)
        with threadpool_limits(limits=1):
            probabilities = self._estimator.predict_proba(X)
        class_index = int(np.where(self._estimator.classes_ == 1)[0][0])
        results: list[PredictionResult] = []
        for item, row in zip(inputs, probabilities, strict=True):
            probability = _convert_prediction_to_decimal(
                float(row[class_index]), self.spec.numeric_policy
            )
            results.append(
                PredictionResult(
                    sample_id=item.sample_id,
                    prediction_time=item.feature_knowledge_time,
                    predicted_value=probability,
                    predicted_probability=probability,
                    predicted_class="1" if probability >= Decimal("0.5") else "0",
                )
            )
        return results


class RidgeRegressionCandidate(BasePredictiveCandidate):
    def __init__(self, spec: MLCandidateSpec) -> None:
        if spec.family != "ridge_regression":
            raise ValueError("Spec family must be 'ridge_regression'")
        if spec.target_contract.target_semantics is not TargetSemantics.CONTINUOUS:
            raise ValueError("RidgeRegressionCandidate requires CONTINUOUS")
        super().__init__(spec)
        kwargs = dict(spec.hyperparameters)
        kwargs.setdefault("alpha", 1.0)
        self._estimator = Ridge(
            random_state=_validate_rng(spec, required=False), **kwargs
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        if len(X) == 0 or len(y) == 0:
            raise TrainingFailureError("Cannot fit RidgeRegression on empty data")
        try:
            with threadpool_limits(limits=1):
                self._estimator.fit(X, y)
        except Exception as exc:
            raise TrainingFailureError(f"RidgeRegression fit failed: {exc}") from exc
        self._finish_fit()

    def predict(
        self, inputs: Sequence[PredictionInput], fitted_pipeline: FittedFeaturePipeline
    ) -> list[PredictionResult]:
        if not inputs:
            if not self._is_fitted:
                raise ModelNotFittedError("Cannot predict with unfitted model")
            return []
        X = self._matrix(inputs, fitted_pipeline)
        with threadpool_limits(limits=1):
            predictions = self._estimator.predict(X)
        return [
            PredictionResult(
                sample_id=item.sample_id,
                prediction_time=item.feature_knowledge_time,
                predicted_value=_convert_prediction_to_decimal(
                    float(value), self.spec.numeric_policy
                ),
            )
            for item, value in zip(inputs, predictions, strict=True)
        ]


class RandomForestClassifierCandidate(BasePredictiveCandidate):
    def __init__(self, spec: MLCandidateSpec) -> None:
        if spec.family != "random_forest_classifier":
            raise ValueError("Spec family must be 'random_forest_classifier'")
        if spec.target_contract.target_semantics is not TargetSemantics.BINARY_PROBABILITY:
            raise ValueError("RandomForestClassifierCandidate requires BINARY_PROBABILITY")
        super().__init__(spec)
        kwargs = dict(spec.hyperparameters)
        kwargs.setdefault("n_estimators", 100)
        self._estimator = RandomForestClassifier(
            random_state=_validate_rng(spec, required=True),
            n_jobs=1,
            **kwargs,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        if len(X) == 0 or len(y) == 0:
            raise TrainingFailureError("Cannot fit RandomForestClassifier on empty data")
        if len(np.unique(y)) < 2:
            raise TrainingFailureError("RandomForestClassifier requires at least 2 classes")
        try:
            with threadpool_limits(limits=1):
                self._estimator.fit(X, y)
        except Exception as exc:
            raise TrainingFailureError(f"RandomForestClassifier fit failed: {exc}") from exc
        self._finish_fit()

    def predict(
        self, inputs: Sequence[PredictionInput], fitted_pipeline: FittedFeaturePipeline
    ) -> list[PredictionResult]:
        if not inputs:
            if not self._is_fitted:
                raise ModelNotFittedError("Cannot predict with unfitted model")
            return []
        X = self._matrix(inputs, fitted_pipeline)
        with threadpool_limits(limits=1):
            probabilities = self._estimator.predict_proba(X)
        class_index = int(np.where(self._estimator.classes_ == 1)[0][0])
        output: list[PredictionResult] = []
        for item, row in zip(inputs, probabilities, strict=True):
            probability = _convert_prediction_to_decimal(
                float(row[class_index]), self.spec.numeric_policy
            )
            output.append(
                PredictionResult(
                    sample_id=item.sample_id,
                    prediction_time=item.feature_knowledge_time,
                    predicted_value=probability,
                    predicted_probability=probability,
                    predicted_class="1" if probability >= Decimal("0.5") else "0",
                )
            )
        return output


class RandomForestRegressorCandidate(BasePredictiveCandidate):
    def __init__(self, spec: MLCandidateSpec) -> None:
        if spec.family != "random_forest_regressor":
            raise ValueError("Spec family must be 'random_forest_regressor'")
        if spec.target_contract.target_semantics is not TargetSemantics.CONTINUOUS:
            raise ValueError("RandomForestRegressorCandidate requires CONTINUOUS")
        super().__init__(spec)
        kwargs = dict(spec.hyperparameters)
        kwargs.setdefault("n_estimators", 100)
        self._estimator = RandomForestRegressor(
            random_state=_validate_rng(spec, required=True),
            n_jobs=1,
            **kwargs,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        if len(X) == 0 or len(y) == 0:
            raise TrainingFailureError("Cannot fit RandomForestRegressor on empty data")
        try:
            with threadpool_limits(limits=1):
                self._estimator.fit(X, y)
        except Exception as exc:
            raise TrainingFailureError(f"RandomForestRegressor fit failed: {exc}") from exc
        self._finish_fit()

    def predict(
        self, inputs: Sequence[PredictionInput], fitted_pipeline: FittedFeaturePipeline
    ) -> list[PredictionResult]:
        if not inputs:
            if not self._is_fitted:
                raise ModelNotFittedError("Cannot predict with unfitted model")
            return []
        X = self._matrix(inputs, fitted_pipeline)
        with threadpool_limits(limits=1):
            predictions = self._estimator.predict(X)
        return [
            PredictionResult(
                sample_id=item.sample_id,
                prediction_time=item.feature_knowledge_time,
                predicted_value=_convert_prediction_to_decimal(
                    float(value), self.spec.numeric_policy
                ),
            )
            for item, value in zip(inputs, predictions, strict=True)
        ]


class GradientBoostingClassifierCandidate(BasePredictiveCandidate):
    def __init__(self, spec: MLCandidateSpec) -> None:
        if spec.family != "gradient_boosting_classifier":
            raise ValueError("Spec family must be 'gradient_boosting_classifier'")
        if spec.target_contract.target_semantics is not TargetSemantics.BINARY_PROBABILITY:
            raise ValueError("GradientBoostingClassifierCandidate requires BINARY_PROBABILITY")
        super().__init__(spec)
        kwargs = dict(spec.hyperparameters)
        kwargs.setdefault("n_estimators", 100)
        self._estimator = GradientBoostingClassifier(
            random_state=_validate_rng(spec, required=True), **kwargs
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        if len(X) == 0 or len(y) == 0:
            raise TrainingFailureError("Cannot fit GradientBoostingClassifier on empty data")
        if len(np.unique(y)) < 2:
            raise TrainingFailureError("GradientBoostingClassifier requires at least 2 classes")
        try:
            with threadpool_limits(limits=1):
                self._estimator.fit(X, y)
        except Exception as exc:
            raise TrainingFailureError(f"GradientBoostingClassifier fit failed: {exc}") from exc
        self._finish_fit()

    def predict(
        self, inputs: Sequence[PredictionInput], fitted_pipeline: FittedFeaturePipeline
    ) -> list[PredictionResult]:
        if not inputs:
            if not self._is_fitted:
                raise ModelNotFittedError("Cannot predict with unfitted model")
            return []
        X = self._matrix(inputs, fitted_pipeline)
        with threadpool_limits(limits=1):
            probabilities = self._estimator.predict_proba(X)
        class_index = int(np.where(self._estimator.classes_ == 1)[0][0])
        output: list[PredictionResult] = []
        for item, row in zip(inputs, probabilities, strict=True):
            probability = _convert_prediction_to_decimal(
                float(row[class_index]), self.spec.numeric_policy
            )
            output.append(
                PredictionResult(
                    sample_id=item.sample_id,
                    prediction_time=item.feature_knowledge_time,
                    predicted_value=probability,
                    predicted_probability=probability,
                    predicted_class="1" if probability >= Decimal("0.5") else "0",
                )
            )
        return output


class GradientBoostingRegressorCandidate(BasePredictiveCandidate):
    def __init__(self, spec: MLCandidateSpec) -> None:
        if spec.family != "gradient_boosting_regressor":
            raise ValueError("Spec family must be 'gradient_boosting_regressor'")
        if spec.target_contract.target_semantics is not TargetSemantics.CONTINUOUS:
            raise ValueError("GradientBoostingRegressorCandidate requires CONTINUOUS")
        super().__init__(spec)
        kwargs = dict(spec.hyperparameters)
        kwargs.setdefault("n_estimators", 100)
        self._estimator = GradientBoostingRegressor(
            random_state=_validate_rng(spec, required=True), **kwargs
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        if len(X) == 0 or len(y) == 0:
            raise TrainingFailureError("Cannot fit GradientBoostingRegressor on empty data")
        try:
            with threadpool_limits(limits=1):
                self._estimator.fit(X, y)
        except Exception as exc:
            raise TrainingFailureError(f"GradientBoostingRegressor fit failed: {exc}") from exc
        self._finish_fit()

    def predict(
        self, inputs: Sequence[PredictionInput], fitted_pipeline: FittedFeaturePipeline
    ) -> list[PredictionResult]:
        if not inputs:
            if not self._is_fitted:
                raise ModelNotFittedError("Cannot predict with unfitted model")
            return []
        X = self._matrix(inputs, fitted_pipeline)
        with threadpool_limits(limits=1):
            predictions = self._estimator.predict(X)
        return [
            PredictionResult(
                sample_id=item.sample_id,
                prediction_time=item.feature_knowledge_time,
                predicted_value=_convert_prediction_to_decimal(
                    float(value), self.spec.numeric_policy
                ),
            )
            for item, value in zip(inputs, predictions, strict=True)
        ]


def create_candidate(spec: MLCandidateSpec) -> PredictiveCandidate:
    mapping: dict[str, type[BasePredictiveCandidate]] = {
        "gradient_boosting_classifier": GradientBoostingClassifierCandidate,
        "gradient_boosting_regressor": GradientBoostingRegressorCandidate,
        "logistic_regression": LogisticRegressionCandidate,
        "random_forest_classifier": RandomForestClassifierCandidate,
        "random_forest_regressor": RandomForestRegressorCandidate,
        "ridge_regression": RidgeRegressionCandidate,
    }
    try:
        candidate_type = mapping[spec.family]
    except KeyError as exc:
        raise ValueError(f"Unknown family '{spec.family}'") from exc
    return candidate_type(spec)
