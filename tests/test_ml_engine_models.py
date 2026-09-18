"""Tests for ML candidate models, factory, and state digest extraction."""

from datetime import UTC, datetime
from decimal import Decimal

import numpy as np
import pytest

from btg_ai_trader.ml_engine.domain import (
    MLCandidateSpec,
    ModelNotFittedError,
    RNGContext,
    TargetContract,
)
from btg_ai_trader.ml_engine.features import (
    FeaturePipelineSpec,
    FeatureSchema,
    FeatureSpec,
    FeatureType,
    FittedFeaturePipeline,
)
from btg_ai_trader.ml_engine.models import (
    create_candidate,
)
from btg_ai_trader.statistical_baselines.domain import (
    PredictionInput,
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY


def _make_dummy_pipeline() -> tuple[FittedFeaturePipeline, list[PredictionInput]]:
    f1 = FeatureSpec(name="x1", feature_type=FeatureType.NUMERIC)
    schema = FeatureSchema([f1])
    spec = FeaturePipelineSpec(schema=schema)

    t = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    samples = [
        StatisticalSample(
            sample_id=f"s{i}",
            feature_knowledge_time=t,
            target_knowledge_time=t,
            target_value=Decimal(i % 2),
            target_semantics=TargetSemantics.BINARY_PROBABILITY,
            feature_metadata={"x1": str(float(i))},
        )
        for i in range(10)
    ]
    pipe = FittedFeaturePipeline.fit(spec, samples)
    inputs = [s.to_prediction_input() for s in samples]
    return pipe, inputs


def test_unfitted_model_errors() -> None:
    contract = TargetContract(
        target_name="y",
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        forecast_horizon_steps=5,
    )
    spec = MLCandidateSpec(
        family="logistic_regression",
        hyperparameters={},
        target_contract=contract,
        feature_pipeline_spec_digest="d",
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev",
    )
    cand = create_candidate(spec)
    assert not cand.is_fitted

    pipe, inputs = _make_dummy_pipeline()
    with pytest.raises(ModelNotFittedError):
        cand.predict(inputs, pipe)

    with pytest.raises(ModelNotFittedError):
        _ = cand.model_state_digest


def test_invalid_family_and_hyperparameters() -> None:
    contract = TargetContract(
        target_name="y",
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        forecast_horizon_steps=5,
    )
    spec_bad_family = MLCandidateSpec(
        family="deep_neural_network",
        hyperparameters={},
        target_contract=contract,
        feature_pipeline_spec_digest="d",
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev",
    )
    with pytest.raises(ValueError, match="Unknown family"):
        create_candidate(spec_bad_family)

    spec_bad_param = MLCandidateSpec(
        family="logistic_regression",
        hyperparameters={"invalid_hyperparam": 123},
        target_contract=contract,
        feature_pipeline_spec_digest="d",
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev",
    )
    with pytest.raises(ValueError, match="Unknown hyperparameters"):
        create_candidate(spec_bad_param)


def test_classification_candidates_fit_and_predict() -> None:
    contract = TargetContract(
        target_name="direction",
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        forecast_horizon_steps=5,
    )
    rng = RNGContext(algorithm="numpy_pcg64", seed=42)
    pipe, inputs = _make_dummy_pipeline()
    X = np.array([[float(i)] for i in range(10)], dtype=np.float64)
    y = np.array([i % 2 for i in range(10)], dtype=np.int64)

    families = [
        "logistic_regression",
        "random_forest_classifier",
        "gradient_boosting_classifier",
    ]

    for fam in families:
        spec = MLCandidateSpec(
            family=fam,
            hyperparameters={"n_estimators": 5} if "forest" in fam or "boosting" in fam else {},
            target_contract=contract,
            feature_pipeline_spec_digest="d",
            rng_context=rng,
            numeric_policy=DEFAULT_NUMERIC_POLICY,
            code_revision="rev",
        )
        cand = create_candidate(spec)
        cand.fit(X, y)
        assert cand.is_fitted
        digest = cand.model_state_digest
        assert digest is not None and len(digest) == 64

        preds = cand.predict(inputs, pipe)
        assert len(preds) == 10
        for p in preds:
            assert p.predicted_probability is not None
            assert Decimal(0) <= p.predicted_probability <= Decimal(1)


def test_regression_candidates_fit_and_predict() -> None:
    contract = TargetContract(
        target_name="returns",
        target_semantics=TargetSemantics.CONTINUOUS,
        forecast_horizon_steps=5,
    )
    rng = RNGContext(algorithm="numpy_pcg64", seed=42)
    pipe, inputs = _make_dummy_pipeline()
    X = np.array([[float(i)] for i in range(10)], dtype=np.float64)
    y = np.array([float(i) * 0.5 for i in range(10)], dtype=np.float64)

    families = [
        "ridge_regression",
        "random_forest_regressor",
        "gradient_boosting_regressor",
    ]

    for fam in families:
        spec = MLCandidateSpec(
            family=fam,
            hyperparameters={"n_estimators": 5} if "forest" in fam or "boosting" in fam else {},
            target_contract=contract,
            feature_pipeline_spec_digest="d",
            rng_context=rng,
            numeric_policy=DEFAULT_NUMERIC_POLICY,
            code_revision="rev",
        )
        cand = create_candidate(spec)
        cand.fit(X, y)
        assert cand.is_fitted
        digest = cand.model_state_digest
        assert digest is not None and len(digest) == 64

        preds = cand.predict(inputs, pipe)
        assert len(preds) == 10
        for p in preds:
            assert p.predicted_value is not None
            assert isinstance(p.predicted_value, Decimal)
