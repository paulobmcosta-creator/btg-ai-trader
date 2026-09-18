"""Tests for all governed S5 scikit-learn candidate families."""

# ruff: noqa: I001 -- explicit grouping retained for audit readability.

from __future__ import annotations

from decimal import Decimal

import numpy as np
import pytest
import sklearn

from btg_ai_trader.ml_engine.domain import (
    MLCandidateSpec,
    ModelNotFittedError,
    RNGContext,
    TrainingFailureError,
)
from btg_ai_trader.ml_engine.features import FittedFeaturePipeline
from btg_ai_trader.ml_engine.models import create_candidate, extract_model_state_digest
from btg_ai_trader.statistical_baselines.domain import TargetSemantics
from tests.ml_engine_helpers import (
    make_binary_samples,
    make_candidate_spec,
    make_continuous_samples,
    make_pipeline,
)


@pytest.mark.parametrize(
    ("family", "semantics"),
    [
        ("logistic_regression", TargetSemantics.BINARY_PROBABILITY),
        ("random_forest_classifier", TargetSemantics.BINARY_PROBABILITY),
        ("gradient_boosting_classifier", TargetSemantics.BINARY_PROBABILITY),
        ("ridge_regression", TargetSemantics.CONTINUOUS),
        ("random_forest_regressor", TargetSemantics.CONTINUOUS),
        ("gradient_boosting_regressor", TargetSemantics.CONTINUOUS),
    ],
)
def test_all_candidates_fit_predict_and_empty_prediction(
    family: str, semantics: TargetSemantics
) -> None:
    pipeline = make_pipeline(two_features=False)
    params: dict[str, object] = (
        {"n_estimators": 4}
        if "forest" in family or "boosting" in family
        else {}
    )
    spec = make_candidate_spec(
        family, pipeline, semantics, hyperparameters=params
    )
    candidate = create_candidate(spec)
    samples = (
        make_binary_samples()[:8]
        if semantics is TargetSemantics.BINARY_PROBABILITY
        else make_continuous_samples()[:8]
    )
    fitted = FittedFeaturePipeline.fit(pipeline, samples)
    inputs = [sample.to_prediction_input() for sample in samples]
    X = fitted.transform(inputs)
    y = np.asarray(
        [float(sample.target_value) for sample in samples],
        dtype=np.int64 if semantics is TargetSemantics.BINARY_PROBABILITY else np.float64,
    )
    with pytest.raises(ModelNotFittedError):
        candidate.predict([], fitted)
    candidate.fit(X, y)
    assert candidate.is_fitted
    assert len(candidate.model_state_digest) == 64
    assert candidate.predict([], fitted) == []
    predictions = candidate.predict(inputs, fitted)
    assert len(predictions) == len(inputs)
    if semantics is TargetSemantics.BINARY_PROBABILITY:
        assert all(item.predicted_probability is not None for item in predictions)
    else:
        assert all(isinstance(item.predicted_value, Decimal) for item in predictions)


def test_factory_family_hyperparameter_semantics_and_rng_validation() -> None:
    pipeline = make_pipeline()
    binary = make_candidate_spec(
        "logistic_regression", pipeline, TargetSemantics.BINARY_PROBABILITY
    )
    bad_family = MLCandidateSpec(
        family="neural_network",
        hyperparameters={},
        target_contract=binary.target_contract,
        feature_pipeline_spec_digest=pipeline.spec_digest,
        rng_context=None,
        numeric_policy=binary.numeric_policy,
        code_revision=binary.code_revision,
    )
    with pytest.raises(ValueError, match="Unknown family"):
        create_candidate(bad_family)

    bad_param = MLCandidateSpec(
        family="logistic_regression",
        hyperparameters={"not_allowed": 1},
        target_contract=binary.target_contract,
        feature_pipeline_spec_digest=pipeline.spec_digest,
        rng_context=None,
        numeric_policy=binary.numeric_policy,
        code_revision=binary.code_revision,
    )
    with pytest.raises(ValueError, match="Unknown hyperparameters"):
        create_candidate(bad_param)

    continuous_contract = make_candidate_spec(
        "ridge_regression", pipeline, TargetSemantics.CONTINUOUS
    ).target_contract
    wrong_semantics = MLCandidateSpec(
        family="logistic_regression",
        hyperparameters={},
        target_contract=continuous_contract,
        feature_pipeline_spec_digest=pipeline.spec_digest,
        rng_context=None,
        numeric_policy=binary.numeric_policy,
        code_revision=binary.code_revision,
    )
    with pytest.raises(ValueError, match="BINARY_PROBABILITY"):
        create_candidate(wrong_semantics)

    no_rng = MLCandidateSpec(
        family="random_forest_classifier",
        hyperparameters={"n_estimators": 2},
        target_contract=binary.target_contract,
        feature_pipeline_spec_digest=pipeline.spec_digest,
        rng_context=None,
        numeric_policy=binary.numeric_policy,
        code_revision=binary.code_revision,
    )
    with pytest.raises(ValueError, match="requires explicit RNGContext"):
        create_candidate(no_rng)

    wrong_version = MLCandidateSpec(
        family="random_forest_classifier",
        hyperparameters={"n_estimators": 2},
        target_contract=binary.target_contract,
        feature_pipeline_spec_digest=pipeline.spec_digest,
        rng_context=RNGContext(
            "sklearn_random_state", 1, library_version="0.0.0"
        ),
        numeric_policy=binary.numeric_policy,
        code_revision=binary.code_revision,
    )
    with pytest.raises(ValueError, match="library_version"):
        create_candidate(wrong_version)

    correct_rng = RNGContext(
        "sklearn_random_state", 1, library_version=sklearn.__version__
    )
    assert correct_rng.seed == 1


def test_training_failure_and_unfitted_digest() -> None:
    pipeline = make_pipeline(two_features=False)
    spec = make_candidate_spec(
        "logistic_regression", pipeline, TargetSemantics.BINARY_PROBABILITY
    )
    candidate = create_candidate(spec)
    with pytest.raises(ModelNotFittedError):
        _ = candidate.model_state_digest
    with pytest.raises(TrainingFailureError, match="empty"):
        candidate.fit(np.empty((0, 1)), np.empty((0,), dtype=int))
    with pytest.raises(TrainingFailureError, match="2 classes"):
        candidate.fit(np.ones((2, 1)), np.ones((2,), dtype=int))


def test_model_state_digest_binds_dtype_shape_and_text_values() -> None:
    class FakeEstimator:
        coef_: np.ndarray
        classes_: np.ndarray
        n_features_in_: int

    first = FakeEstimator()
    first.coef_ = np.asarray([[1.0, 2.0]], dtype=np.float64)
    first.classes_ = np.asarray(["A", "B"])
    first.n_features_in_ = 2

    second = FakeEstimator()
    second.coef_ = np.asarray([1.0, 2.0], dtype=np.float64)
    second.classes_ = np.asarray(["A", "B"])
    second.n_features_in_ = 2

    third = FakeEstimator()
    third.coef_ = np.asarray([[1.0, 2.0]], dtype=np.float32)
    third.classes_ = np.asarray(["A", "C"])
    third.n_features_in_ = 2

    digest_first = extract_model_state_digest(first)
    assert digest_first == extract_model_state_digest(first)
    assert digest_first != extract_model_state_digest(second)
    assert digest_first != extract_model_state_digest(third)
