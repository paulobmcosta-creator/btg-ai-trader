"""Final targeted branch coverage for Sprint 5 fail-closed invariants."""

# ruff: noqa: I001 -- grouped by subsystem for audit readability.

from __future__ import annotations

import dataclasses
from datetime import datetime
from decimal import Decimal
from typing import Any

import numpy as np
import pytest

import btg_ai_trader.ml_engine.evaluation as evaluation_module
from btg_ai_trader.ml_engine.domain import (
    MLCandidateSpec,
    ModelNotFittedError,
    RNGContext,
)
from btg_ai_trader.ml_engine.evaluation import ModelEvaluationEngine, ModelEvaluationReport
from btg_ai_trader.ml_engine.features import (
    FeaturePipelineSpec,
    FeatureSchema,
    FeatureSpec,
    FittedFeaturePipeline,
)
from btg_ai_trader.ml_engine.models import (
    BasePredictiveCandidate,
    GradientBoostingClassifierCandidate,
    GradientBoostingRegressorCandidate,
    LogisticRegressionCandidate,
    RandomForestClassifierCandidate,
    RandomForestRegressorCandidate,
    RidgeRegressionCandidate,
    create_candidate,
    extract_model_state_digest,
)
from btg_ai_trader.ml_engine.provenance import (
    EnvironmentFingerprint,
    ModelTrainingInputBoundary,
    ModelTrainingManifest,
)
from btg_ai_trader.ml_engine.registry import ModelRecord
from btg_ai_trader.ml_engine.selection import ModelSearchHistory, ModelSearchSpace
from btg_ai_trader.ml_engine.training import ModelTrainer
from btg_ai_trader.statistical_baselines.baselines import HistoricalPriorProbabilityBaseline
from btg_ai_trader.statistical_baselines.domain import (
    EvaluationRole,
    ParityViolationError,
    PredictionInput,
    PredictionResult,
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.evaluation import (
    AggregateEvaluationResult,
    FoldAggregationPolicy,
    StatisticalEvaluationEngine,
)
from btg_ai_trader.statistical_baselines.metrics import NumericPolicy
from tests.ml_engine_helpers import (
    make_binary_samples,
    make_candidate_spec,
    make_continuous_samples,
    make_pipeline,
    make_plan,
)


class _NullProbabilityCandidate:
    def __init__(self, spec: MLCandidateSpec) -> None:
        self.spec = spec

    def fit(self, X: Any, y: Any) -> None:
        return None

    def predict(
        self,
        inputs: list[PredictionInput],
        fitted_pipeline: FittedFeaturePipeline,
    ) -> list[PredictionResult]:
        del fitted_pipeline
        return [
            PredictionResult(
                sample_id=item.sample_id,
                prediction_time=item.feature_knowledge_time,
            )
            for item in inputs
        ]


class _NullValueCandidate(_NullProbabilityCandidate):
    pass


def _binary_context() -> tuple[
    FeaturePipelineSpec,
    MLCandidateSpec,
    ModelEvaluationReport,
    AggregateEvaluationResult,
]:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
    )
    plan = make_plan(plan_id="coverage-parity")
    samples = make_binary_samples()
    engine = ModelEvaluationEngine()
    report = engine.evaluate_candidate(
        create_candidate(spec),
        pipeline,
        plan,
        samples,
        role=EvaluationRole.VALIDATION_SELECTION,
    )
    baseline = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
        baseline_factory=lambda: HistoricalPriorProbabilityBaseline(
            code_revision="coverage-baseline",
            numeric_policy=spec.numeric_policy,
        ),
        plan=plan,
        samples=samples,
        role=EvaluationRole.VALIDATION_SELECTION,
        aggregation_policy=FoldAggregationPolicy.EQUAL_FOLD,
        numeric_policy=spec.numeric_policy,
        target_contract_id=spec.target_contract.contract_digest,
        code_revision="coverage-baseline",
    )
    return pipeline, spec, report, baseline


def _verified_boundary() -> tuple[
    FeaturePipelineSpec,
    MLCandidateSpec,
    EnvironmentFingerprint,
    ModelTrainingInputBoundary,
]:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
    )
    env = EnvironmentFingerprint.capture()
    samples = make_binary_samples()[:8]
    boundary = ModelTrainingInputBoundary.create_and_verify(
        samples=samples,
        target_contract=spec.target_contract,
        feature_pipeline_spec_digest=pipeline.spec_digest,
        candidate_spec=spec,
        knowledge_cutoff=samples[-1].target_knowledge_time,
        environment=env,
        code_revision=spec.code_revision,
    )
    return pipeline, spec, env, boundary


def test_evaluation_rejects_empty_samples_missing_policies_and_pipeline_mismatch() -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
    )
    engine = ModelEvaluationEngine()
    plan = make_plan()
    with pytest.raises(ValueError, match="empty samples"):
        engine.evaluate_candidate(create_candidate(spec), pipeline, plan, [])

    object.__setattr__(plan, "purge_policy", None)
    with pytest.raises(ValueError, match="purge_policy"):
        engine.evaluate_candidate(
            create_candidate(spec),
            pipeline,
            plan,
            make_binary_samples(),
        )

    plan = make_plan()
    other_pipeline = make_pipeline(two_features=False)
    with pytest.raises(ValueError, match="feature_pipeline_spec_digest"):
        engine.evaluate_candidate(
            create_candidate(spec),
            other_pipeline,
            plan,
            make_binary_samples(),
        )


def test_evaluation_partition_fail_closed_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
    )
    engine = ModelEvaluationEngine()
    plan = make_plan()
    samples = make_binary_samples()
    train = tuple(samples[:8])
    validation = tuple(samples[8:12])
    protected = tuple(samples[12:])

    monkeypatch.setattr(
        evaluation_module.WalkForwardPlanner,
        "partition_samples",
        staticmethod(lambda *args: ((), validation, protected)),
    )
    with pytest.raises(ValueError, match="zero training"):
        engine.evaluate_candidate(create_candidate(spec), pipeline, plan, samples)

    monkeypatch.setattr(
        evaluation_module.WalkForwardPlanner,
        "partition_samples",
        staticmethod(lambda *args: (train, None, protected)),
    )
    with pytest.raises(ValueError, match="no validation boundary"):
        engine.evaluate_candidate(create_candidate(spec), pipeline, plan, samples)

    monkeypatch.setattr(
        evaluation_module.WalkForwardPlanner,
        "partition_samples",
        staticmethod(lambda *args: (train, (), protected)),
    )
    report = engine.evaluate_candidate(create_candidate(spec), pipeline, plan, samples)
    assert report.fold_evaluations[0].sample_count == 0
    assert report.fold_evaluations[0].metrics == {}


def test_evaluation_rejects_missing_binary_probability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
    )
    monkeypatch.setattr(
        evaluation_module,
        "create_candidate",
        lambda _spec: _NullProbabilityCandidate(_spec),
    )
    with pytest.raises(ValueError, match="without probability"):
        ModelEvaluationEngine().evaluate_candidate(
            _NullProbabilityCandidate(spec),
            pipeline,
            make_plan(),
            make_binary_samples(),
        )


def test_evaluation_rejects_missing_continuous_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "ridge_regression",
        pipeline,
        TargetSemantics.CONTINUOUS,
    )
    monkeypatch.setattr(
        evaluation_module,
        "create_candidate",
        lambda _spec: _NullValueCandidate(_spec),
    )
    with pytest.raises(ValueError, match="without value"):
        ModelEvaluationEngine().evaluate_candidate(
            _NullValueCandidate(spec),
            pipeline,
            make_plan(),
            make_continuous_samples(),
        )


def test_continuous_constant_target_omits_r2() -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "ridge_regression",
        pipeline,
        TargetSemantics.CONTINUOUS,
    )
    samples = [
        dataclasses.replace(sample, target_value=Decimal("1"))
        for sample in make_continuous_samples()
    ]
    report = ModelEvaluationEngine().evaluate_candidate(
        create_candidate(spec),
        pipeline,
        make_plan(),
        samples,
    )
    assert "r2_score" not in report.mean_metrics


def test_all_baseline_parity_failure_branches() -> None:
    pipeline, spec, report, baseline = _binary_context()
    plan = make_plan(plan_id="coverage-parity")
    samples = make_binary_samples()
    engine = ModelEvaluationEngine()

    with pytest.raises(ParityViolationError, match="not present in candidate"):
        engine.compare_with_baseline(
            candidate_report=report,
            baseline_result=baseline,
            metric_name="missing",
            plan=plan,
            samples=samples,
        )

    with pytest.raises(ParityViolationError, match="roles differ"):
        engine.compare_with_baseline(
            candidate_report=report,
            baseline_result=dataclasses.replace(
                baseline, evaluation_role=EvaluationRole.PROTECTED_TEST
            ),
            metric_name="brier_score",
            plan=plan,
            samples=samples,
        )

    with pytest.raises(ParityViolationError, match="aggregation policies differ"):
        engine.compare_with_baseline(
            candidate_report=report,
            baseline_result=dataclasses.replace(
                baseline,
                aggregation_policy=FoldAggregationPolicy.SAMPLE_WEIGHTED,
            ),
            metric_name="brier_score",
            plan=plan,
            samples=samples,
        )

    with pytest.raises(ParityViolationError, match="numeric policies differ"):
        engine.compare_with_baseline(
            candidate_report=report,
            baseline_result=dataclasses.replace(
                baseline,
                numeric_policy=NumericPolicy(precision=12),
            ),
            metric_name="brier_score",
            plan=plan,
            samples=samples,
        )

    with pytest.raises(ParityViolationError, match="target contracts differ"):
        engine.compare_with_baseline(
            candidate_report=report,
            baseline_result=dataclasses.replace(
                baseline,
                target_contract_id="other-contract",
            ),
            metric_name="brier_score",
            plan=plan,
            samples=samples,
        )

    with pytest.raises(ParityViolationError, match="fold identities differ"):
        engine.compare_with_baseline(
            candidate_report=report,
            baseline_result=dataclasses.replace(baseline, fold_results=()),
            metric_name="brier_score",
            plan=plan,
            samples=samples,
        )

    with pytest.raises(ParityViolationError, match="Candidate report"):
        engine.compare_with_baseline(
            candidate_report=dataclasses.replace(report, dataset_digest="wrong"),
            baseline_result=baseline,
            metric_name="brier_score",
            plan=plan,
            samples=samples,
        )

    aggregate_without_metric = {
        key: value
        for key, value in baseline.aggregate_metrics.items()
        if key != "mean_brier_score"
    }
    with pytest.raises(ParityViolationError, match="not present in baseline"):
        engine.compare_with_baseline(
            candidate_report=report,
            baseline_result=dataclasses.replace(
                baseline,
                aggregate_metrics=aggregate_without_metric,
            ),
            metric_name="brier_score",
            plan=plan,
            samples=samples,
        )

    positive = engine.compare_with_baseline(
        candidate_report=report,
        baseline_result=baseline,
        metric_name="brier_score",
        plan=plan,
        samples=samples,
        higher_is_better=True,
    )
    assert positive.improvement == positive.candidate_metric - positive.baseline_metric
    assert pipeline.spec_digest == spec.feature_pipeline_spec_digest


def test_ablation_missing_metric_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    pipeline, spec, report, _ = _binary_context()
    engine = ModelEvaluationEngine()

    monkeypatch.setattr(
        engine,
        "evaluate_candidate",
        lambda *args, **kwargs: dataclasses.replace(report, mean_metrics={}),
    )
    with pytest.raises(ValueError, match="full candidate"):
        engine.run_ablation(
            candidate=create_candidate(spec),
            full_pipeline_spec=pipeline,
            ablation_spec=evaluation_module.FeatureAblationSpec("f2"),
            plan=make_plan(),
            samples=make_binary_samples(),
            metric_name="brier_score",
        )

    responses = iter(
        (
            report,
            dataclasses.replace(report, mean_metrics={}),
        )
    )
    monkeypatch.setattr(
        engine,
        "evaluate_candidate",
        lambda *args, **kwargs: next(responses),
    )
    with pytest.raises(ValueError, match="ablated candidate"):
        engine.run_ablation(
            candidate=create_candidate(spec),
            full_pipeline_spec=pipeline,
            ablation_spec=evaluation_module.FeatureAblationSpec("f2"),
            plan=make_plan(),
            samples=make_binary_samples(),
            metric_name="brier_score",
        )


def test_feature_remaining_fail_closed_branches() -> None:
    numeric = FeatureSpec("x", evaluation_module.FeatureType.NUMERIC)
    categorical = FeatureSpec("cat", evaluation_module.FeatureType.CATEGORICAL)
    boolean = FeatureSpec("flag", evaluation_module.FeatureType.BOOLEAN)
    assert len(FeatureSchema((numeric,))) == 1

    with pytest.raises(ValueError, match="empty inputs"):
        FittedFeaturePipeline.fit(
            FeaturePipelineSpec(FeatureSchema((numeric,))),
            [],
        )

    sample = make_binary_samples()[0]
    missing = dataclasses.replace(sample, feature_metadata={})

    with pytest.raises(ValueError, match="cat.*missing"):
        FittedFeaturePipeline.fit(
            FeaturePipelineSpec(FeatureSchema((categorical,))),
            [missing],
        )
    with pytest.raises(ValueError, match="flag.*missing"):
        FittedFeaturePipeline.fit(
            FeaturePipelineSpec(FeatureSchema((boolean,))),
            [missing],
        )

    fitted = FittedFeaturePipeline.fit(
        FeaturePipelineSpec(FeatureSchema((numeric,))),
        [dataclasses.replace(sample, feature_metadata={"x": "1"})],
    )
    with pytest.raises(ValueError, match="Missing value"):
        fitted.transform([missing.to_prediction_input()])


def test_model_digest_optional_state_and_estimator_property_branches() -> None:
    class EmptyEstimator:
        pass

    class ChildWithoutTree:
        pass

    class EnsembleOnly:
        estimators_: np.ndarray

    empty = EmptyEstimator()
    assert len(extract_model_state_digest(empty)) == 64

    ensemble = EnsembleOnly()
    ensemble.estimators_ = np.asarray([ChildWithoutTree()], dtype=object)
    assert len(extract_model_state_digest(ensemble)) == 64

    pipeline = make_pipeline(two_features=False)
    spec = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
    )
    candidate = create_candidate(spec)
    assert candidate.estimator is not None  # type: ignore[attr-defined]
    with pytest.raises(ModelNotFittedError):
        candidate._matrix([], FittedFeaturePipeline.fit(  # type: ignore[attr-defined]
            pipeline,
            make_binary_samples()[:2],
        ))


def test_all_model_semantic_guards_and_rng_algorithm_guard() -> None:
    pipeline = make_pipeline()
    binary_contract = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
    ).target_contract
    continuous_contract = make_candidate_spec(
        "ridge_regression",
        pipeline,
        TargetSemantics.CONTINUOUS,
    ).target_contract

    binary_families = (
        LogisticRegressionCandidate,
        RandomForestClassifierCandidate,
        GradientBoostingClassifierCandidate,
    )
    continuous_families = (
        RidgeRegressionCandidate,
        RandomForestRegressorCandidate,
        GradientBoostingRegressorCandidate,
    )
    binary_names = (
        "logistic_regression",
        "random_forest_classifier",
        "gradient_boosting_classifier",
    )
    continuous_names = (
        "ridge_regression",
        "random_forest_regressor",
        "gradient_boosting_regressor",
    )

    for constructor, family in zip(binary_families, binary_names, strict=True):
        rng = (
            RNGContext("sklearn_random_state", 1)
            if family != "logistic_regression"
            else None
        )
        bad = MLCandidateSpec(
            family=family,
            hyperparameters={},
            target_contract=continuous_contract,
            feature_pipeline_spec_digest=pipeline.spec_digest,
            rng_context=rng,
            numeric_policy=make_candidate_spec(
                "ridge_regression", pipeline, TargetSemantics.CONTINUOUS
            ).numeric_policy,
            code_revision="rev-s5",
        )
        with pytest.raises(ValueError, match="requires"):
            constructor(bad)

    for constructor, family in zip(continuous_families, continuous_names, strict=True):
        rng = (
            RNGContext("sklearn_random_state", 1)
            if family != "ridge_regression"
            else None
        )
        bad = MLCandidateSpec(
            family=family,
            hyperparameters={},
            target_contract=binary_contract,
            feature_pipeline_spec_digest=pipeline.spec_digest,
            rng_context=rng,
            numeric_policy=make_candidate_spec(
                "logistic_regression",
                pipeline,
                TargetSemantics.BINARY_PROBABILITY,
            ).numeric_policy,
            code_revision="rev-s5",
        )
        with pytest.raises(ValueError, match="requires"):
            constructor(bad)

    stochastic = make_candidate_spec(
        "random_forest_classifier",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
    )
    assert stochastic.rng_context is not None
    object.__setattr__(stochastic.rng_context, "algorithm", "forged")
    with pytest.raises(ValueError, match="sklearn_random_state"):
        RandomForestClassifierCandidate(stochastic)


def test_provenance_remaining_validation_branches() -> None:
    pipeline, spec, env, boundary = _verified_boundary()
    assert env.scikit_learn_version == env.sklearn_version

    with pytest.raises(ValueError, match="timezone-aware"):
        ModelTrainingInputBoundary(
            ordered_sample_ids=("x",),
            dataset_digest="d",
            source_lineage_digest="s",
            target_contract_digest="t",
            feature_pipeline_spec_digest="p",
            knowledge_cutoff=datetime(2025, 1, 1),
            candidate_spec_digest="c",
            numeric_policy=spec.numeric_policy,
            environment_fingerprint_digest="e",
            code_revision="r",
        )

    other_target = make_candidate_spec(
        "ridge_regression",
        pipeline,
        TargetSemantics.CONTINUOUS,
    ).target_contract
    with pytest.raises(ValueError, match="target contract"):
        ModelTrainingInputBoundary.create_and_verify(
            samples=make_binary_samples()[:8],
            target_contract=other_target,
            feature_pipeline_spec_digest=pipeline.spec_digest,
            candidate_spec=spec,
            knowledge_cutoff=make_binary_samples()[7].target_knowledge_time,
            environment=env,
            code_revision=spec.code_revision,
        )

    with pytest.raises(ValueError, match="TargetContract"):
        ModelTrainingInputBoundary.create_and_verify(
            samples=[make_continuous_samples()[0]],
            target_contract=spec.target_contract,
            feature_pipeline_spec_digest=pipeline.spec_digest,
            candidate_spec=spec,
            knowledge_cutoff=make_continuous_samples()[0].target_knowledge_time,
            environment=env,
            code_revision=spec.code_revision,
        )

    with pytest.raises(ValueError, match="boundary_digest"):
        ModelTrainingManifest(
            boundary_digest="",
            candidate_id="c",
            fitted_feature_pipeline_digest="p",
            model_state_digest="m",
            target_contract_digest="t",
            rng_context=None,
            environment_fingerprint=env,
            code_revision="r",
        )

    checks = (
        ("candidate_spec_digest", "wrong", "candidate identity"),
        ("target_contract_digest", "wrong", "target contract"),
        ("feature_pipeline_spec_digest", "wrong", "feature pipeline"),
        ("environment_fingerprint_digest", "wrong", "environment"),
        ("code_revision", "wrong", "code revision"),
    )
    for field_name, value, message in checks:
        _, current_spec, current_env, current_boundary = _verified_boundary()
        object.__setattr__(current_boundary, field_name, value)
        with pytest.raises(ValueError, match=message):
            ModelTrainingManifest.create(
                boundary=current_boundary,
                candidate_spec=current_spec,
                fitted_feature_pipeline_digest="fit",
                model_state_digest="state",
                environment_fingerprint=current_env,
                code_revision=current_spec.code_revision,
            )

    assert boundary.is_verified


def test_registry_selection_and_continuous_training_remaining_lines() -> None:
    _, spec, env, _ = _verified_boundary()
    with pytest.raises(ValueError, match="candidate_id"):
        ModelRecord(
            candidate_id="",
            model_state_digest="m",
            training_input_boundary_digest="b",
            feature_pipeline_digest="p",
            target_contract_digest="t",
            rng_context=None,
            environment_fingerprint_digest=env.fingerprint_digest,
            training_manifest_digest="manifest",
            evaluation_refs=(),
            model_card_digest="c",
            code_revision="r",
        )

    space = ModelSearchSpace((spec,))
    history = ModelSearchHistory(space)
    assert history.search_space_digest == space.search_space_digest

    pipeline = make_pipeline()
    continuous_spec = make_candidate_spec(
        "ridge_regression",
        pipeline,
        TargetSemantics.CONTINUOUS,
    )
    continuous_samples = make_continuous_samples()[:8]
    result = ModelTrainer().fit(
        candidate_spec=continuous_spec,
        pipeline_spec=pipeline,
        samples=continuous_samples,
        knowledge_cutoff=continuous_samples[-1].target_knowledge_time,
        code_revision=continuous_spec.code_revision,
    )
    assert result.candidate.is_fitted
