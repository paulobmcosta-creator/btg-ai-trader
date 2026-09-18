"""Adversarial invariants for Sprint 5 research ML."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import numpy as np
import pytest

from btg_ai_trader.ml_engine.domain import EvaluationScope, FeatureType
from btg_ai_trader.ml_engine.features import (
    FeaturePipelineSpec,
    FeatureSchema,
    FeatureSpec,
    FittedFeaturePipeline,
)
from btg_ai_trader.ml_engine.model_card import ModelCard
from btg_ai_trader.ml_engine.models import create_candidate
from btg_ai_trader.ml_engine.provenance import EnvironmentFingerprint
from btg_ai_trader.ml_engine.selection import ModelSearchSpace
from btg_ai_trader.ml_engine.training import ModelTrainer
from btg_ai_trader.statistical_baselines.domain import (
    CausalLeakageError,
    StatisticalSample,
    TargetSemantics,
)
from tests.ml_engine_helpers import (
    make_binary_samples,
    make_candidate_spec,
    make_continuous_samples,
    make_pipeline,
)


def test_adversarial_future_label_rejected_and_prediction_surface_has_no_target() -> None:
    pipeline = make_pipeline(two_features=False)
    spec = make_candidate_spec(
        "logistic_regression", pipeline, TargetSemantics.BINARY_PROBABILITY
    )
    cutoff = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    leaked = StatisticalSample(
        sample_id="future",
        feature_knowledge_time=cutoff,
        target_knowledge_time=cutoff + timedelta(seconds=1),
        target_value=Decimal(1),
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        feature_metadata={"f1": "1"},
    )
    with pytest.raises(CausalLeakageError):
        ModelTrainer().fit(
            candidate_spec=spec,
            pipeline_spec=pipeline,
            samples=[leaked],
            knowledge_cutoff=cutoff,
            code_revision=spec.code_revision,
        )
    safe = leaked.to_prediction_input()
    assert not hasattr(safe, "target_value")
    assert not hasattr(safe, "target_knowledge_time")


def test_adversarial_best_seed_is_rejected_at_search_space_construction() -> None:
    pipeline = make_pipeline()
    first = make_candidate_spec(
        "random_forest_classifier",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
        seed=1,
        hyperparameters={"n_estimators": 3},
    )
    second = make_candidate_spec(
        "random_forest_classifier",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
        seed=2,
        hyperparameters={"n_estimators": 3},
    )
    with pytest.raises(ValueError, match="best-seed"):
        ModelSearchSpace((first, second))


def test_adversarial_twenty_repeated_fits_are_digest_identical() -> None:
    binary = make_binary_samples()[:8]
    continuous = make_continuous_samples()[:8]
    pipeline = make_pipeline(two_features=False)
    fitted_binary = FittedFeaturePipeline.fit(pipeline, binary)
    fitted_continuous = FittedFeaturePipeline.fit(pipeline, continuous)
    X_binary = fitted_binary.transform([sample.to_prediction_input() for sample in binary])
    X_continuous = fitted_continuous.transform(
        [sample.to_prediction_input() for sample in continuous]
    )
    y_binary = np.asarray([int(sample.target_value) for sample in binary], dtype=np.int64)
    y_continuous = np.asarray(
        [float(sample.target_value) for sample in continuous], dtype=np.float64
    )

    cases = (
        ("logistic_regression", TargetSemantics.BINARY_PROBABILITY, X_binary, y_binary, {}),
        ("ridge_regression", TargetSemantics.CONTINUOUS, X_continuous, y_continuous, {}),
        (
            "random_forest_classifier",
            TargetSemantics.BINARY_PROBABILITY,
            X_binary,
            y_binary,
            {"n_estimators": 3},
        ),
        (
            "random_forest_regressor",
            TargetSemantics.CONTINUOUS,
            X_continuous,
            y_continuous,
            {"n_estimators": 3},
        ),
        (
            "gradient_boosting_classifier",
            TargetSemantics.BINARY_PROBABILITY,
            X_binary,
            y_binary,
            {"n_estimators": 3},
        ),
        (
            "gradient_boosting_regressor",
            TargetSemantics.CONTINUOUS,
            X_continuous,
            y_continuous,
            {"n_estimators": 3},
        ),
    )
    for family, semantics, X, y, parameters in cases:
        spec = make_candidate_spec(
            family,
            pipeline,
            semantics,
            seed=123,
            hyperparameters=parameters,
        )
        digests: list[str] = []
        for _ in range(20):
            candidate = create_candidate(spec)
            candidate.fit(X, y)
            digests.append(candidate.model_state_digest)
        assert len(set(digests)) == 1


def test_adversarial_hundred_feature_pipeline_replays_are_identical() -> None:
    pipeline = make_pipeline()
    samples = make_binary_samples()[:8]
    inputs = [sample.to_prediction_input() for sample in samples]
    digests: list[str] = []
    matrices: list[bytes] = []
    for _ in range(100):
        fitted = FittedFeaturePipeline.fit(pipeline, samples)
        digests.append(fitted.pipeline_digest)
        matrices.append(fitted.transform(inputs).tobytes())
    assert len(set(digests)) == 1
    assert len(set(matrices)) == 1


def test_adversarial_model_card_rejects_strategy_scope() -> None:
    schema = FeatureSchema((FeatureSpec("f1", FeatureType.NUMERIC),))
    with pytest.raises(ValueError, match="evaluation_scope"):
        ModelCard(
            model_id="ml:test",
            family="ridge_regression",
            target_contract=make_candidate_spec(
                "ridge_regression",
                FeaturePipelineSpec(schema),
                TargetSemantics.CONTINUOUS,
            ).target_contract,
            feature_schema=schema,
            training_boundary_digest="bound",
            hyperparameters={},
            rng_context=None,
            environment_fingerprint=EnvironmentFingerprint.capture(),
            validation_metrics={"mae": Decimal("0.1")},
            evaluation_scope=EvaluationScope.STRATEGY,
        )
