"""Tests for ModelEvaluationEngine, baseline comparison, and feature ablation."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from btg_ai_trader.ml_engine.domain import (
    MLCandidateSpec,
    RNGContext,
    TargetContract,
)
from btg_ai_trader.ml_engine.evaluation import (
    FeatureAblationSpec,
    ModelEvaluationEngine,
)
from btg_ai_trader.ml_engine.features import (
    FeaturePipelineSpec,
    FeatureSchema,
    FeatureSpec,
    FeatureType,
)
from btg_ai_trader.ml_engine.models import create_candidate
from btg_ai_trader.statistical_baselines.baselines import HistoricalPriorProbabilityBaseline
from btg_ai_trader.statistical_baselines.boundaries import (
    EvaluationBoundary,
    TemporalFold,
    WalkForwardPlan,
)
from btg_ai_trader.statistical_baselines.domain import (
    EvaluationRole,
    ParityViolationError,
    ProtectedEvidenceReuseError,
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY


def _build_test_plan() -> WalkForwardPlan:
    t0 = datetime(2025, 1, 1, 9, 0, tzinfo=UTC)
    t1 = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    t2 = datetime(2025, 1, 1, 13, 0, tzinfo=UTC)
    t3 = datetime(2025, 1, 1, 14, 0, tzinfo=UTC)

    dev_boundary = EvaluationBoundary(start_time=t0, end_time=t3, knowledge_cutoff=t0)
    train_boundary = EvaluationBoundary(start_time=t0, end_time=t1, knowledge_cutoff=t0)
    val_boundary = EvaluationBoundary(start_time=t1, end_time=t2, knowledge_cutoff=t1)
    test_boundary = EvaluationBoundary(start_time=t2, end_time=t3, knowledge_cutoff=t2)

    fold = TemporalFold(
        fold_id="fold_0",
        development_boundary=dev_boundary,
        training_boundary=train_boundary,
        protected_evaluation_boundary=test_boundary,
        knowledge_cutoff=t1,
        window_policy_name="EXPANDING",
        validation_boundary=val_boundary,
    )

    return WalkForwardPlan(
        plan_id="plan_test_01",
        window_policy_name="EXPANDING",
        folds=(fold,),
    )


def _build_test_samples() -> list[StatisticalSample]:
    samples = []
    # 10 train samples between 9:00 and 11:30
    for i in range(10):
        t = datetime(2025, 1, 1, 9, 0, tzinfo=UTC) + timedelta(minutes=15 * i)
        samples.append(
            StatisticalSample(
                sample_id=f"train_{i}",
                feature_knowledge_time=t,
                target_knowledge_time=t,
                target_value=Decimal(i % 2),
                target_semantics=TargetSemantics.BINARY_PROBABILITY,
                feature_metadata={"f1": str(float(i)), "f2": str(float(i * 2))},
            )
        )
    # 4 validation samples between 12:00 and 12:45
    for i in range(4):
        t = datetime(2025, 1, 1, 12, 0, tzinfo=UTC) + timedelta(minutes=10 * i)
        samples.append(
            StatisticalSample(
                sample_id=f"val_{i}",
                feature_knowledge_time=t,
                target_knowledge_time=t,
                target_value=Decimal(i % 2),
                target_semantics=TargetSemantics.BINARY_PROBABILITY,
                feature_metadata={"f1": str(float(i + 10)), "f2": str(float(i * 2 + 10))},
            )
        )
    # 4 protected test samples between 13:00 and 13:45
    for i in range(4):
        t = datetime(2025, 1, 1, 13, 0, tzinfo=UTC) + timedelta(minutes=10 * i)
        samples.append(
            StatisticalSample(
                sample_id=f"test_{i}",
                feature_knowledge_time=t,
                target_knowledge_time=t,
                target_value=Decimal(i % 2),
                target_semantics=TargetSemantics.BINARY_PROBABILITY,
                feature_metadata={"f1": str(float(i + 20)), "f2": str(float(i * 2 + 20))},
            )
        )
    return samples


def test_evaluate_candidate_and_protected_reuse() -> None:
    f1 = FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)
    f2 = FeatureSpec(name="f2", feature_type=FeatureType.NUMERIC)
    schema = FeatureSchema([f1, f2])
    pipe_spec = FeaturePipelineSpec(schema=schema)

    contract = TargetContract(
        target_name="dir",
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
    cand = create_candidate(cand_spec)
    plan = _build_test_plan()
    samples = _build_test_samples()

    engine = ModelEvaluationEngine()

    # 1. Validation evaluation
    report_val = engine.evaluate_candidate(
        cand, pipe_spec, plan, samples, role=EvaluationRole.VALIDATION_SELECTION
    )
    assert "brier_score" in report_val.mean_metrics
    assert not report_val.consumed_protected_boundary

    # 2. Protected test evaluation (first time)
    report_test = engine.evaluate_candidate(
        cand, pipe_spec, plan, samples, role=EvaluationRole.PROTECTED_TEST
    )
    assert report_test.consumed_protected_boundary

    # 3. Protected test evaluation (second time MUST FAIL with ProtectedEvidenceReuseError)
    with pytest.raises(ProtectedEvidenceReuseError):
        engine.evaluate_candidate(
            cand, pipe_spec, plan, samples, role=EvaluationRole.PROTECTED_TEST
        )


def test_compare_with_baseline_parity() -> None:
    f1 = FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)
    pipe_spec = FeaturePipelineSpec(schema=FeatureSchema([f1]))
    contract = TargetContract(
        target_name="dir",
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
    cand = create_candidate(cand_spec)
    plan = _build_test_plan()
    samples = _build_test_samples()

    engine = ModelEvaluationEngine()
    report = engine.evaluate_candidate(
        cand, pipe_spec, plan, samples, role=EvaluationRole.VALIDATION_SELECTION
    )

    baseline = HistoricalPriorProbabilityBaseline(
        code_revision="rev_s4",
    )

    comp = engine.compare_with_baseline(
        candidate_report=report,
        baseline=baseline,
        metric_name="brier_score",
    )
    assert comp.is_comparable
    assert comp.metric_name == "brier_score"
    assert comp.baseline_id.startswith("HistoricalPriorProbabilityBaseline:")

    with pytest.raises(ParityViolationError, match="not present in candidate evaluation report"):
        engine.compare_with_baseline(
            candidate_report=report,
            baseline=baseline,
            metric_name="non_existent_metric",
        )


def test_feature_ablation() -> None:
    f1 = FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)
    f2 = FeatureSpec(name="f2", feature_type=FeatureType.NUMERIC)
    schema = FeatureSchema([f1, f2])
    pipe_spec = FeaturePipelineSpec(schema=schema)

    contract = TargetContract(
        target_name="dir",
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
    cand = create_candidate(cand_spec)
    plan = _build_test_plan()
    samples = _build_test_samples()

    engine = ModelEvaluationEngine()
    ablation_spec = FeatureAblationSpec(ablated_feature_name="f2")

    result = engine.run_ablation(
        candidate=cand,
        full_pipeline_spec=pipe_spec,
        ablation_spec=ablation_spec,
        plan=plan,
        samples=samples,
        metric_name="brier_score",
    )
    assert result.ablated_feature == "f2"
    assert result.metric_name == "brier_score"
    assert isinstance(result.delta, Decimal)
