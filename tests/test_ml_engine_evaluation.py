"""Tests for canonical temporal ML evaluation and real baseline parity."""

# ruff: noqa: I001 -- explicit grouping retained for audit readability.

from __future__ import annotations

import dataclasses
from datetime import timedelta

import pytest

from btg_ai_trader.ml_engine.domain import MLCandidateSpec
from btg_ai_trader.ml_engine.evaluation import (
    FeatureAblationSpec,
    ModelEvaluationEngine,
)
from btg_ai_trader.ml_engine.models import create_candidate
from btg_ai_trader.statistical_baselines.baselines import (
    HistoricalMeanBaseline,
    HistoricalPriorProbabilityBaseline,
)
from btg_ai_trader.statistical_baselines.comparison import EvaluationHistory
from btg_ai_trader.statistical_baselines.domain import (
    EvaluationRole,
    ParityViolationError,
    ProtectedEvidenceReuseError,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.evaluation import (
    FoldAggregationPolicy,
    StatisticalEvaluationEngine,
)
from btg_ai_trader.statistical_baselines.splits import EmbargoPolicy, PurgePolicy
from tests.ml_engine_helpers import (
    make_binary_samples,
    make_candidate_spec,
    make_continuous_samples,
    make_pipeline,
    make_plan,
)


def test_validation_evaluation_uses_s4_partition_and_aggregation() -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression", pipeline, TargetSemantics.BINARY_PROBABILITY
    )
    report = ModelEvaluationEngine().evaluate_candidate(
        create_candidate(spec),
        pipeline,
        make_plan(),
        make_binary_samples(),
        role=EvaluationRole.VALIDATION_SELECTION,
    )
    assert report.role is EvaluationRole.VALIDATION_SELECTION
    assert report.fold_evaluations[0].sample_count == 4
    assert "brier_score" in report.mean_metrics
    assert "log_loss" in report.mean_metrics
    assert "ece" in report.mean_metrics
    assert report.protected_boundary_id == ""
    assert len(report.experimental_context_fingerprint) == 64


def test_purge_and_embargo_are_inherited_from_s4() -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression", pipeline, TargetSemantics.BINARY_PROBABILITY
    )
    engine = ModelEvaluationEngine()

    base = engine.evaluate_candidate(
        create_candidate(spec),
        pipeline,
        make_plan(plan_id="base"),
        make_binary_samples(),
    )
    embargoed = engine.evaluate_candidate(
        create_candidate(spec),
        pipeline,
        make_plan(
            plan_id="embargo",
            embargo_policy=EmbargoPolicy(duration=timedelta(minutes=30)),
        ),
        make_binary_samples(),
    )
    assert base.fold_evaluations[0].sample_count == 4
    assert embargoed.fold_evaluations[0].sample_count == 1
    assert (
        base.experimental_context_fingerprint
        != embargoed.experimental_context_fingerprint
    )

    purged = engine.evaluate_candidate(
        create_candidate(spec),
        pipeline,
        make_plan(
            plan_id="purged",
            purge_policy=PurgePolicy(
                fail_closed_on_unknown=False,
                purge_overlapping=True,
                default_horizon=timedelta(hours=2),
            ),
        ),
        make_binary_samples(),
    )
    assert purged.candidate_id == spec.candidate_id


def test_protected_lineage_blocks_adapted_candidate_but_allows_independent_boundary() -> None:
    pipeline = make_pipeline()
    first_spec = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
        hyperparameters={"C": 1.0},
    )
    plan = make_plan()
    samples = make_binary_samples()
    history = EvaluationHistory()
    engine = ModelEvaluationEngine()

    first = engine.evaluate_candidate(
        create_candidate(first_spec),
        pipeline,
        plan,
        samples,
        role=EvaluationRole.PROTECTED_TEST,
        evaluation_history=history,
        protected_boundary_id="P",
    )
    assert first.protected_boundary_id == "P"

    second_spec = MLCandidateSpec(
        family=first_spec.family,
        hyperparameters={"C": 2.0},
        target_contract=first_spec.target_contract,
        feature_pipeline_spec_digest=first_spec.feature_pipeline_spec_digest,
        rng_context=first_spec.rng_context,
        numeric_policy=first_spec.numeric_policy,
        code_revision=first_spec.code_revision,
    )
    history.record_protected_evidence_consumption(
        protected_boundary_id="P",
        source_candidate_id=first_spec.candidate_id,
        derived_candidate_id=second_spec.candidate_id,
    )
    with pytest.raises(ProtectedEvidenceReuseError):
        engine.evaluate_candidate(
            create_candidate(second_spec),
            pipeline,
            plan,
            samples,
            role=EvaluationRole.PROTECTED_TEST,
            evaluation_history=history,
            protected_boundary_id="P",
            parent_candidate_ids=(first_spec.candidate_id,),
        )

    independent = engine.evaluate_candidate(
        create_candidate(second_spec),
        pipeline,
        plan,
        samples,
        role=EvaluationRole.PROTECTED_TEST,
        evaluation_history=history,
        protected_boundary_id="Q",
        parent_candidate_ids=(first_spec.candidate_id,),
    )
    assert independent.protected_boundary_id == "Q"


def test_protected_requires_history_and_invalid_role_is_rejected() -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression", pipeline, TargetSemantics.BINARY_PROBABILITY
    )
    engine = ModelEvaluationEngine()
    with pytest.raises(ValueError, match="EvaluationHistory"):
        engine.evaluate_candidate(
            create_candidate(spec),
            pipeline,
            make_plan(),
            make_binary_samples(),
            role=EvaluationRole.PROTECTED_TEST,
        )
    with pytest.raises(ValueError, match="VALIDATION_SELECTION"):
        engine.evaluate_candidate(
            create_candidate(spec),
            pipeline,
            make_plan(),
            make_binary_samples(),
            role=EvaluationRole.TRAINING_FIT,
        )


def test_real_baseline_comparison_and_parity_rejection() -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression", pipeline, TargetSemantics.BINARY_PROBABILITY
    )
    plan = make_plan()
    samples = make_binary_samples()
    engine = ModelEvaluationEngine()
    candidate_report = engine.evaluate_candidate(
        create_candidate(spec),
        pipeline,
        plan,
        samples,
        role=EvaluationRole.VALIDATION_SELECTION,
    )
    baseline_result = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
        baseline_factory=lambda: HistoricalPriorProbabilityBaseline(
            code_revision="baseline-rev",
            numeric_policy=spec.numeric_policy,
        ),
        plan=plan,
        samples=samples,
        role=EvaluationRole.VALIDATION_SELECTION,
        aggregation_policy=FoldAggregationPolicy.EQUAL_FOLD,
        numeric_policy=spec.numeric_policy,
        target_contract_id=spec.target_contract.contract_digest,
        code_revision="baseline-rev",
    )
    comparison = engine.compare_with_baseline(
        candidate_report=candidate_report,
        baseline_result=baseline_result,
        metric_name="brier_score",
        plan=plan,
        samples=samples,
    )
    assert comparison.is_comparable
    assert comparison.baseline_metric == baseline_result.aggregate_metrics["mean_brier_score"]
    assert comparison.improvement == comparison.baseline_metric - comparison.candidate_metric

    wrong_target = dataclasses.replace(baseline_result, target_contract_id="wrong")
    with pytest.raises(ParityViolationError, match="target contracts"):
        engine.compare_with_baseline(
            candidate_report=candidate_report,
            baseline_result=wrong_target,
            metric_name="brier_score",
            plan=plan,
            samples=samples,
        )

    wrong_context = dataclasses.replace(
        baseline_result, evaluation_context_fingerprint="0" * 64
    )
    with pytest.raises(ParityViolationError, match="population/plan"):
        engine.compare_with_baseline(
            candidate_report=candidate_report,
            baseline_result=wrong_context,
            metric_name="brier_score",
            plan=plan,
            samples=samples,
        )


def test_continuous_weighted_evaluation_and_baseline() -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "ridge_regression", pipeline, TargetSemantics.CONTINUOUS
    )
    plan = make_plan(plan_id="continuous")
    samples = make_continuous_samples()
    engine = ModelEvaluationEngine()
    report = engine.evaluate_candidate(
        create_candidate(spec),
        pipeline,
        plan,
        samples,
        aggregation_policy=FoldAggregationPolicy.SAMPLE_WEIGHTED,
    )
    assert {"mae", "mse", "rmse", "mean_bias"} <= set(report.mean_metrics)

    baseline = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
        baseline_factory=lambda: HistoricalMeanBaseline(
            code_revision="baseline-cont",
            numeric_policy=spec.numeric_policy,
        ),
        plan=plan,
        samples=samples,
        role=EvaluationRole.VALIDATION_SELECTION,
        aggregation_policy=FoldAggregationPolicy.SAMPLE_WEIGHTED,
        numeric_policy=spec.numeric_policy,
        target_contract_id=spec.target_contract.contract_digest,
        code_revision="baseline-cont",
    )
    comparison = engine.compare_with_baseline(
        candidate_report=report,
        baseline_result=baseline,
        metric_name="mae",
        plan=plan,
        samples=samples,
    )
    assert comparison.baseline_metric == baseline.aggregate_metrics["weighted_mean_mae"]


def test_ablation_requires_real_feature_and_preserves_validation_scope() -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression", pipeline, TargetSemantics.BINARY_PROBABILITY
    )
    engine = ModelEvaluationEngine()
    result = engine.run_ablation(
        candidate=create_candidate(spec),
        full_pipeline_spec=pipeline,
        ablation_spec=FeatureAblationSpec("f2"),
        plan=make_plan(),
        samples=make_binary_samples(),
        metric_name="brier_score",
    )
    assert result.ablated_feature == "f2"
    with pytest.raises(ValueError, match="not in the schema"):
        engine.run_ablation(
            candidate=create_candidate(spec),
            full_pipeline_spec=pipeline,
            ablation_spec=FeatureAblationSpec("missing"),
            plan=make_plan(),
            samples=make_binary_samples(),
            metric_name="brier_score",
        )

    one_feature = make_pipeline(two_features=False)
    one_spec = make_candidate_spec(
        "logistic_regression", one_feature, TargetSemantics.BINARY_PROBABILITY
    )
    with pytest.raises(ValueError, match="all features"):
        engine.run_ablation(
            candidate=create_candidate(one_spec),
            full_pipeline_spec=one_feature,
            ablation_spec=FeatureAblationSpec("f1"),
            plan=make_plan(),
            samples=make_binary_samples(),
            metric_name="brier_score",
        )
