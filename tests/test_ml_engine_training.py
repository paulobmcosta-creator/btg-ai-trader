"""Tests for ModelTrainer, TrainingResult, and causal training boundaries."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from btg_ai_trader.ml_engine.domain import (
    MLCandidateSpec,
    RNGContext,
    TargetContract,
)
from btg_ai_trader.ml_engine.features import (
    FeaturePipelineSpec,
    FeatureSchema,
    FeatureSpec,
    FeatureType,
)
from btg_ai_trader.ml_engine.training import ModelTrainer
from btg_ai_trader.statistical_baselines.domain import (
    CausalLeakageError,
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY


def _make_sample(
    sample_id: str,
    target_dt: datetime,
    semantics: TargetSemantics = TargetSemantics.BINARY_PROBABILITY,
    val: Decimal = Decimal(1),
) -> StatisticalSample:
    return StatisticalSample(
        sample_id=sample_id,
        feature_knowledge_time=target_dt,
        target_knowledge_time=target_dt,
        target_value=val,
        target_semantics=semantics,
        feature_metadata={"f1": "1.23"},
    )


def test_model_trainer_end_to_end() -> None:
    f1 = FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)
    schema = FeatureSchema([f1])
    pipe_spec = FeaturePipelineSpec(schema=schema)

    contract = TargetContract(
        target_name="direction",
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        forecast_horizon_steps=5,
    )
    cand_spec = MLCandidateSpec(
        family="logistic_regression",
        hyperparameters={},
        target_contract=contract,
        feature_pipeline_spec_digest=pipe_spec.spec_digest,
        rng_context=RNGContext(algorithm="numpy_pcg64", seed=42),
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev_1",
    )

    t1 = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    t2 = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    cutoff = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)

    samples = [
        _make_sample("s1", t1, val=Decimal(0)),
        _make_sample("s2", t2, val=Decimal(1)),
    ]

    trainer = ModelTrainer()
    result = trainer.fit(
        candidate_spec=cand_spec,
        pipeline_spec=pipe_spec,
        samples=samples,
        knowledge_cutoff=cutoff,
        code_revision="rev_1",
    )

    assert result.candidate_id == cand_spec.candidate_id
    assert result.fitted_candidate.is_fitted
    assert result.manifest is not None
    assert result.boundary.knowledge_cutoff == cutoff
    assert result.training_duration >= 0.0


def test_model_trainer_causal_leakage_rejection() -> None:
    f1 = FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)
    pipe_spec = FeaturePipelineSpec(schema=FeatureSchema([f1]))
    contract = TargetContract(
        target_name="direction",
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        forecast_horizon_steps=5,
    )
    cand_spec = MLCandidateSpec(
        family="logistic_regression",
        hyperparameters={},
        target_contract=contract,
        feature_pipeline_spec_digest=pipe_spec.spec_digest,
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev_1",
    )

    t_future = datetime(2025, 1, 1, 13, 0, tzinfo=UTC)
    cutoff = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)

    samples = [_make_sample("s_future", t_future)]
    trainer = ModelTrainer()

    with pytest.raises(CausalLeakageError, match="Future label leakage detected"):
        trainer.fit(
            candidate_spec=cand_spec,
            pipeline_spec=pipe_spec,
            samples=samples,
            knowledge_cutoff=cutoff,
            code_revision="rev_1",
        )
