"""Shared deterministic fixtures for Sprint 5 tests."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import sklearn

from btg_ai_trader.ml_engine.domain import MLCandidateSpec, RNGContext, TargetContract
from btg_ai_trader.ml_engine.features import (
    FeaturePipelineSpec,
    FeatureSchema,
    FeatureSpec,
    FeatureType,
)
from btg_ai_trader.statistical_baselines.boundaries import WalkForwardPlan
from btg_ai_trader.statistical_baselines.domain import StatisticalSample, TargetSemantics
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY
from btg_ai_trader.statistical_baselines.splits import (
    EmbargoPolicy,
    PurgePolicy,
    SplitPlanConfig,
    WalkForwardPlanner,
    WindowPolicy,
)


def make_plan(
    *,
    plan_id: str = "s5-test-plan",
    purge_policy: PurgePolicy | None = None,
    embargo_policy: EmbargoPolicy | None = None,
) -> WalkForwardPlan:
    start = datetime(2025, 1, 1, 9, 0, tzinfo=UTC)
    end = datetime(2025, 1, 1, 13, 0, tzinfo=UTC)
    config = SplitPlanConfig(
        window_policy=WindowPolicy.EXPANDING,
        train_duration=timedelta(hours=2),
        validation_duration=timedelta(hours=1),
        test_duration=timedelta(hours=1),
        step_duration=timedelta(hours=1),
        purge_policy=purge_policy
        or PurgePolicy(
            fail_closed_on_unknown=False,
            purge_overlapping=True,
            default_horizon=timedelta(0),
        ),
        embargo_policy=embargo_policy or EmbargoPolicy(duration=timedelta(0)),
    )
    return WalkForwardPlanner.generate_plan(start, end, config, plan_id)


def make_binary_samples() -> list[StatisticalSample]:
    samples: list[StatisticalSample] = []
    periods = (
        ("train", datetime(2025, 1, 1, 9, 0, tzinfo=UTC), 8),
        ("val", datetime(2025, 1, 1, 11, 0, tzinfo=UTC), 4),
        ("test", datetime(2025, 1, 1, 12, 0, tzinfo=UTC), 4),
    )
    offset = 0
    for prefix, start, count in periods:
        for index in range(count):
            timestamp = start + timedelta(minutes=10 * index)
            value = Decimal((index + offset) % 2)
            samples.append(
                StatisticalSample(
                    sample_id=f"{prefix}_{index}",
                    feature_knowledge_time=timestamp,
                    target_knowledge_time=timestamp,
                    target_value=value,
                    target_semantics=TargetSemantics.BINARY_PROBABILITY,
                    source_lineage="fixture:binary",
                    feature_metadata={
                        "f1": str(float(index + offset)),
                        "f2": str(float((index + offset) * 2)),
                        "flag": "true" if index % 2 == 0 else "false",
                        "session": "OTHER" if index % 2 == 0 else "MORNING",
                    },
                )
            )
        offset += count
    return samples


def make_continuous_samples() -> list[StatisticalSample]:
    samples: list[StatisticalSample] = []
    periods = (
        ("train", datetime(2025, 1, 1, 9, 0, tzinfo=UTC), 8),
        ("val", datetime(2025, 1, 1, 11, 0, tzinfo=UTC), 4),
        ("test", datetime(2025, 1, 1, 12, 0, tzinfo=UTC), 4),
    )
    offset = 0
    for prefix, start, count in periods:
        for index in range(count):
            timestamp = start + timedelta(minutes=10 * index)
            numeric = Decimal(str((index + offset) * 0.25))
            samples.append(
                StatisticalSample(
                    sample_id=f"{prefix}_{index}",
                    feature_knowledge_time=timestamp,
                    target_knowledge_time=timestamp,
                    target_value=numeric,
                    target_semantics=TargetSemantics.CONTINUOUS,
                    source_lineage="fixture:continuous",
                    feature_metadata={
                        "f1": str(float(index + offset)),
                        "f2": str(float((index + offset) * 3)),
                    },
                )
            )
        offset += count
    return samples


def make_pipeline(*, two_features: bool = True) -> FeaturePipelineSpec:
    features = [FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)]
    if two_features:
        features.append(FeatureSpec(name="f2", feature_type=FeatureType.NUMERIC))
    return FeaturePipelineSpec(schema=FeatureSchema(tuple(features)), normalize=True)


def make_contract(semantics: TargetSemantics) -> TargetContract:
    return TargetContract(
        target_name="target",
        target_semantics=semantics,
        forecast_horizon_steps=1,
    )


def make_candidate_spec(
    family: str,
    pipeline: FeaturePipelineSpec,
    semantics: TargetSemantics,
    *,
    code_revision: str = "rev-s5",
    seed: int = 42,
    hyperparameters: Mapping[str, object] | None = None,
) -> MLCandidateSpec:
    stochastic = family.startswith("random_forest") or family.startswith(
        "gradient_boosting"
    )
    rng = (
        RNGContext(
            algorithm="sklearn_random_state",
            seed=seed,
            stream_semantics="test",
            library_version=sklearn.__version__,
        )
        if stochastic
        else None
    )
    return MLCandidateSpec(
        family=family,
        hyperparameters=hyperparameters or {},
        target_contract=make_contract(semantics),
        feature_pipeline_spec_digest=pipeline.spec_digest,
        rng_context=rng,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision=code_revision,
    )
