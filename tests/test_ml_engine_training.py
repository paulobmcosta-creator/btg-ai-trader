"""Tests for the verified ModelTrainer orchestration."""

# ruff: noqa: I001 -- explicit grouping retained for audit readability.

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from btg_ai_trader.ml_engine.domain import MLCandidateSpec
from btg_ai_trader.ml_engine.training import ModelTrainer
from btg_ai_trader.statistical_baselines.domain import (
    CausalLeakageError,
    StatisticalSample,
    TargetSemantics,
)
from tests.ml_engine_helpers import (
    make_binary_samples,
    make_candidate_spec,
    make_pipeline,
)


def test_model_trainer_end_to_end() -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
    )
    result = ModelTrainer().fit(
        candidate_spec=spec,
        pipeline_spec=pipeline,
        samples=make_binary_samples()[:8],
        knowledge_cutoff=datetime(2025, 1, 1, 11, 0, tzinfo=UTC),
        code_revision=spec.code_revision,
        audit_metadata={"source": "test"},
    )
    assert result.candidate_id == spec.candidate_id
    assert result.fitted_candidate.is_fitted
    assert result.boundary.is_verified
    assert result.manifest.is_verified
    assert result.training_duration == 0.0


def test_trainer_rejects_empty_pipeline_revision_semantics_and_future_labels() -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
    )
    trainer = ModelTrainer()
    with pytest.raises(ValueError, match="empty"):
        trainer.fit(
            candidate_spec=spec,
            pipeline_spec=pipeline,
            samples=[],
            knowledge_cutoff=datetime(2025, 1, 1, 11, 0, tzinfo=UTC),
            code_revision=spec.code_revision,
        )

    other_pipeline = make_pipeline(two_features=False)
    with pytest.raises(ValueError, match="feature_pipeline"):
        trainer.fit(
            candidate_spec=spec,
            pipeline_spec=other_pipeline,
            samples=make_binary_samples()[:8],
            knowledge_cutoff=datetime(2025, 1, 1, 11, 0, tzinfo=UTC),
            code_revision=spec.code_revision,
        )
    with pytest.raises(ValueError, match="code_revision"):
        trainer.fit(
            candidate_spec=spec,
            pipeline_spec=pipeline,
            samples=make_binary_samples()[:8],
            knowledge_cutoff=datetime(2025, 1, 1, 11, 0, tzinfo=UTC),
            code_revision="wrong",
        )

    sample = make_binary_samples()[0]
    future = StatisticalSample(
        sample_id="future",
        feature_knowledge_time=sample.feature_knowledge_time,
        target_knowledge_time=datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
        target_value=Decimal(1),
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        feature_metadata=dict(sample.feature_metadata),
    )
    with pytest.raises(CausalLeakageError):
        trainer.fit(
            candidate_spec=spec,
            pipeline_spec=pipeline,
            samples=[future],
            knowledge_cutoff=datetime(2025, 1, 1, 11, 0, tzinfo=UTC),
            code_revision=spec.code_revision,
        )

    continuous = StatisticalSample(
        sample_id="continuous",
        feature_knowledge_time=sample.feature_knowledge_time,
        target_knowledge_time=sample.target_knowledge_time,
        target_value=Decimal("1.2"),
        target_semantics=TargetSemantics.CONTINUOUS,
        feature_metadata=dict(sample.feature_metadata),
    )
    with pytest.raises(ValueError, match="TargetContract"):
        trainer.fit(
            candidate_spec=spec,
            pipeline_spec=pipeline,
            samples=[continuous],
            knowledge_cutoff=datetime(2025, 1, 1, 11, 0, tzinfo=UTC),
            code_revision=spec.code_revision,
        )


def test_candidate_spec_revision_mismatch_is_identity_failure() -> None:
    pipeline = make_pipeline()
    original = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
    )
    mismatched = MLCandidateSpec(
        family=original.family,
        hyperparameters=original.hyperparameters,
        target_contract=original.target_contract,
        feature_pipeline_spec_digest=original.feature_pipeline_spec_digest,
        rng_context=original.rng_context,
        numeric_policy=original.numeric_policy,
        code_revision="different",
    )
    with pytest.raises(ValueError, match="code_revision"):
        ModelTrainer().fit(
            candidate_spec=mismatched,
            pipeline_spec=pipeline,
            samples=make_binary_samples()[:8],
            knowledge_cutoff=datetime(2025, 1, 1, 11, 0, tzinfo=UTC),
            code_revision="rev-s5",
        )
