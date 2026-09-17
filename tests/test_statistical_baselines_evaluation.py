"""Unit tests for temporal fold evaluation engine and aggregate metric calculation."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from btg_ai_trader.statistical_baselines.baselines import (
    HistoricalMeanBaseline,
    HistoricalPriorProbabilityBaseline,
    MajorityClassBaseline,
)
from btg_ai_trader.statistical_baselines.boundaries import (
    EvaluationBoundary,
    TemporalFold,
)
from btg_ai_trader.statistical_baselines.domain import (
    EvaluationRole,
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.evaluation import (
    AggregateEvaluationResult,
    FoldEvaluationResult,
    StatisticalEvaluationEngine,
)
from btg_ai_trader.statistical_baselines.splits import (
    EmbargoPolicy,
    PurgePolicy,
    SplitPlanConfig,
    WalkForwardPlanner,
    WindowPolicy,
)


def _make_sample(
    sample_id: str,
    feature_time: datetime,
    target_time: datetime,
    target_val: Decimal | str,
    semantics: TargetSemantics = TargetSemantics.CONTINUOUS,
) -> StatisticalSample:
    return StatisticalSample(
        sample_id=sample_id,
        feature_knowledge_time=feature_time,
        target_knowledge_time=target_time,
        target_value=target_val,
        target_semantics=semantics,
    )


def test_fold_evaluation_result_validation() -> None:
    with pytest.raises(ValueError, match="sample_count cannot be negative"):
        FoldEvaluationResult(
            fold_id="f1",
            candidate_id="c1",
            evaluation_role=EvaluationRole.VALIDATION_SELECTION,
            metrics={},
            sample_count=-1,
            cold_start_count=0,
        )

    with pytest.raises(ValueError, match="cold_start_count"):
        FoldEvaluationResult(
            fold_id="f1",
            candidate_id="c1",
            evaluation_role=EvaluationRole.VALIDATION_SELECTION,
            metrics={},
            sample_count=5,
            cold_start_count=6,
        )

    with pytest.raises(ValueError, match="cold_start_count"):
        FoldEvaluationResult(
            fold_id="f1",
            candidate_id="c1",
            evaluation_role=EvaluationRole.VALIDATION_SELECTION,
            metrics={},
            sample_count=5,
            cold_start_count=-1,
        )


def test_aggregate_evaluation_result_validation() -> None:
    with pytest.raises(ValueError, match="total_samples cannot be negative"):
        AggregateEvaluationResult(
            candidate_id="c1",
            evaluation_role=EvaluationRole.VALIDATION_SELECTION,
            fold_results=(),
            aggregate_metrics={},
            total_samples=-1,
            total_cold_starts=0,
        )

    with pytest.raises(ValueError, match="total_cold_starts must be between"):
        AggregateEvaluationResult(
            candidate_id="c1",
            evaluation_role=EvaluationRole.VALIDATION_SELECTION,
            fold_results=(),
            aggregate_metrics={},
            total_samples=5,
            total_cold_starts=6,
        )

    with pytest.raises(ValueError, match="total_cold_starts must be between"):
        AggregateEvaluationResult(
            candidate_id="c1",
            evaluation_role=EvaluationRole.VALIDATION_SELECTION,
            fold_results=(),
            aggregate_metrics={},
            total_samples=5,
            total_cold_starts=-1,
        )


def test_evaluate_candidate_on_fold_empty_eval() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    fold = TemporalFold(
        fold_id="f1",
        development_boundary=EvaluationBoundary(t0, t1, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, t1, knowledge_cutoff=t0),
        protected_evaluation_boundary=EvaluationBoundary(
            t1, t1 + timedelta(hours=1), knowledge_cutoff=t1
        ),
        knowledge_cutoff=t1,
        window_policy_name="EXPANDING",
    )
    b = HistoricalMeanBaseline()
    res = StatisticalEvaluationEngine.evaluate_candidate_on_fold(
        baseline=b,
        fold=fold,
        train_samples=[],
        eval_samples=[],
        role=EvaluationRole.PROTECTED_TEST,
    )
    assert res.sample_count == 0
    assert res.cold_start_count == 0
    assert len(res.metrics) == 0


def test_evaluate_candidate_on_fold_continuous() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)
    t2 = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    fold = TemporalFold(
        fold_id="f1",
        development_boundary=EvaluationBoundary(t0, t2, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, t1, knowledge_cutoff=t0),
        protected_evaluation_boundary=EvaluationBoundary(t1, t2, knowledge_cutoff=t1),
        knowledge_cutoff=t1,
        window_policy_name="EXPANDING",
    )

    # Train: 10, 20 -> mean = 15
    t_tr1 = t0 + timedelta(minutes=10)
    t_tr2 = t0 + timedelta(minutes=20)
    s_tr1 = _make_sample("tr1", t0, t_tr1, Decimal("10"))
    s_tr2 = _make_sample("tr2", t_tr1, t_tr2, Decimal("20"))

    # Test: target values 12, 18
    # Baseline predicts 15 for both
    # Errors: 15 - 12 = 3, 15 - 18 = -3
    # MAE = 3, MSE = 9, RMSE = 3, Mean Bias = 0
    t_te1 = t1 + timedelta(minutes=10)
    t_te2 = t1 + timedelta(minutes=20)
    s_te1 = _make_sample("te1", t1 + timedelta(minutes=5), t_te1, Decimal("12"))
    s_te2 = _make_sample("te2", t1 + timedelta(minutes=15), t_te2, Decimal("18"))

    b = HistoricalMeanBaseline()
    res = StatisticalEvaluationEngine.evaluate_candidate_on_fold(
        baseline=b,
        fold=fold,
        train_samples=[s_tr1, s_tr2],
        eval_samples=[s_te1, s_te2],
        role=EvaluationRole.PROTECTED_TEST,
    )

    assert res.sample_count == 2
    assert res.cold_start_count == 0
    assert res.metrics["mae"] == Decimal("3")
    assert res.metrics["mse"] == Decimal("9")
    assert res.metrics["rmse"] == Decimal("3")
    assert res.metrics["mean_bias"] == Decimal("0")


def test_evaluate_candidate_on_fold_binary_probability() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)
    t2 = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    fold = TemporalFold(
        fold_id="f1",
        development_boundary=EvaluationBoundary(t0, t2, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, t1, knowledge_cutoff=t0),
        protected_evaluation_boundary=EvaluationBoundary(t1, t2, knowledge_cutoff=t1),
        knowledge_cutoff=t1,
        window_policy_name="EXPANDING",
    )

    # Train 3 ones, 1 zero -> prior = 0.75
    s_tr1 = _make_sample(
        "tr1", t0, t0 + timedelta(minutes=1), Decimal("1"), TargetSemantics.BINARY_PROBABILITY
    )
    s_tr2 = _make_sample(
        "tr2", t0, t0 + timedelta(minutes=2), Decimal("1"), TargetSemantics.BINARY_PROBABILITY
    )
    s_tr3 = _make_sample(
        "tr3", t0, t0 + timedelta(minutes=3), Decimal("1"), TargetSemantics.BINARY_PROBABILITY
    )
    s_tr4 = _make_sample(
        "tr4", t0, t0 + timedelta(minutes=4), Decimal("0"), TargetSemantics.BINARY_PROBABILITY
    )

    # Test 1 one, 1 zero
    s_te1 = _make_sample(
        "te1",
        t1 + timedelta(minutes=5),
        t1 + timedelta(minutes=10),
        Decimal("1"),
        TargetSemantics.BINARY_PROBABILITY,
    )
    s_te2 = _make_sample(
        "te2",
        t1 + timedelta(minutes=15),
        t1 + timedelta(minutes=20),
        Decimal("0"),
        TargetSemantics.BINARY_PROBABILITY,
    )

    b = HistoricalPriorProbabilityBaseline()
    res = StatisticalEvaluationEngine.evaluate_candidate_on_fold(
        baseline=b,
        fold=fold,
        train_samples=[s_tr1, s_tr2, s_tr3, s_tr4],
        eval_samples=[s_te1, s_te2],
        role=EvaluationRole.PROTECTED_TEST,
    )

    assert res.sample_count == 2
    assert "brier_score" in res.metrics
    assert "base_rate" in res.metrics
    assert "ece" in res.metrics
    assert "mce" in res.metrics
    assert res.calibration_report is not None


def test_evaluate_candidate_on_fold_categorical() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)
    t2 = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    fold = TemporalFold(
        fold_id="f1",
        development_boundary=EvaluationBoundary(t0, t2, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, t1, knowledge_cutoff=t0),
        protected_evaluation_boundary=EvaluationBoundary(t1, t2, knowledge_cutoff=t1),
        knowledge_cutoff=t1,
        window_policy_name="EXPANDING",
    )

    # Train: BUY, BUY, SELL -> majority is BUY
    s_tr1 = _make_sample("tr1", t0, t0 + timedelta(minutes=1), "BUY", TargetSemantics.CATEGORICAL)
    s_tr2 = _make_sample("tr2", t0, t0 + timedelta(minutes=2), "BUY", TargetSemantics.CATEGORICAL)
    s_tr3 = _make_sample("tr3", t0, t0 + timedelta(minutes=3), "SELL", TargetSemantics.CATEGORICAL)

    # Test: BUY, SELL -> accuracy is 0.5
    s_te1 = _make_sample(
        "te1",
        t1 + timedelta(minutes=5),
        t1 + timedelta(minutes=10),
        "BUY",
        TargetSemantics.CATEGORICAL,
    )
    s_te2 = _make_sample(
        "te2",
        t1 + timedelta(minutes=15),
        t1 + timedelta(minutes=20),
        "SELL",
        TargetSemantics.CATEGORICAL,
    )

    b = MajorityClassBaseline()
    res = StatisticalEvaluationEngine.evaluate_candidate_on_fold(
        baseline=b,
        fold=fold,
        train_samples=[s_tr1, s_tr2, s_tr3],
        eval_samples=[s_te1, s_te2],
        role=EvaluationRole.PROTECTED_TEST,
    )

    assert res.sample_count == 2
    assert res.metrics["accuracy"] == Decimal("0.5")


def test_evaluate_candidate_on_fold_cold_starts() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)
    t2 = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    fold = TemporalFold(
        fold_id="f1",
        development_boundary=EvaluationBoundary(t0, t2, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, t1, knowledge_cutoff=t0),
        protected_evaluation_boundary=EvaluationBoundary(t1, t2, knowledge_cutoff=t1),
        knowledge_cutoff=t1,
        window_policy_name="EXPANDING",
    )

    # Cold start continuous: 0 training samples -> predictions have predicted_value is None
    s_te_cont = _make_sample(
        "te_c", t1 + timedelta(minutes=5), t1 + timedelta(minutes=10), Decimal("10")
    )
    b_cont = HistoricalMeanBaseline()
    res_cont = StatisticalEvaluationEngine.evaluate_candidate_on_fold(
        baseline=b_cont,
        fold=fold,
        train_samples=[],
        eval_samples=[s_te_cont],
        role=EvaluationRole.PROTECTED_TEST,
    )
    assert res_cont.cold_start_count == 1
    assert "mae" not in res_cont.metrics

    # Cold start binary probability
    s_te_bin = _make_sample(
        "te_b",
        t1 + timedelta(minutes=5),
        t1 + timedelta(minutes=10),
        Decimal("1"),
        TargetSemantics.BINARY_PROBABILITY,
    )
    b_bin = HistoricalPriorProbabilityBaseline()
    res_bin = StatisticalEvaluationEngine.evaluate_candidate_on_fold(
        baseline=b_bin,
        fold=fold,
        train_samples=[],
        eval_samples=[s_te_bin],
        role=EvaluationRole.PROTECTED_TEST,
    )
    assert res_bin.cold_start_count == 1
    assert "brier_score" not in res_bin.metrics

    # Cold start categorical
    s_te_cat = _make_sample(
        "te_cat",
        t1 + timedelta(minutes=5),
        t1 + timedelta(minutes=10),
        "BUY",
        TargetSemantics.CATEGORICAL,
    )
    b_cat = MajorityClassBaseline()
    res_cat = StatisticalEvaluationEngine.evaluate_candidate_on_fold(
        baseline=b_cat,
        fold=fold,
        train_samples=[],
        eval_samples=[s_te_cat],
        role=EvaluationRole.PROTECTED_TEST,
    )
    assert res_cat.cold_start_count == 1
    assert "accuracy" not in res_cat.metrics


def test_evaluate_candidate_on_plan_walk_forward() -> None:
    t_start = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_end = datetime(2026, 9, 1, 13, 0, tzinfo=UTC)

    cfg = SplitPlanConfig(
        window_policy=WindowPolicy.EXPANDING,
        train_duration=timedelta(hours=2),
        test_duration=timedelta(hours=1),
        step_duration=timedelta(hours=1),
    )
    plan = WalkForwardPlanner.generate_plan(t_start, t_end, cfg, plan_id="wf_plan")
    assert len(plan.folds) == 2

    # Samples across the timeline
    samples = [
        _make_sample(
            "s1", t_start + timedelta(minutes=30), t_start + timedelta(minutes=40), Decimal("10")
        ),
        _make_sample(
            "s2",
            t_start + timedelta(hours=1, minutes=30),
            t_start + timedelta(hours=1, minutes=40),
            Decimal("20"),
        ),
        _make_sample(
            "s3",
            t_start + timedelta(hours=2, minutes=30),
            t_start + timedelta(hours=2, minutes=40),
            Decimal("30"),
        ),
        _make_sample(
            "s4",
            t_start + timedelta(hours=3, minutes=30),
            t_start + timedelta(hours=3, minutes=40),
            Decimal("40"),
        ),
    ]

    purge_pol = PurgePolicy(default_horizon=timedelta(minutes=10))
    embargo_pol = EmbargoPolicy(duration=timedelta(0))

    # VALIDATION_SELECTION role error when no validation boundary
    with pytest.raises(ValueError, match="Cannot evaluate on VALIDATION_SELECTION"):
        StatisticalEvaluationEngine.evaluate_candidate_on_plan(
            baseline_factory=HistoricalMeanBaseline,
            plan=plan,
            samples=samples,
            role=EvaluationRole.VALIDATION_SELECTION,
            purge_policy=purge_pol,
            embargo_policy=embargo_pol,
        )

    # PROTECTED_TEST role
    agg_res = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
        baseline_factory=HistoricalMeanBaseline,
        plan=plan,
        samples=samples,
        role=EvaluationRole.PROTECTED_TEST,
        purge_policy=purge_pol,
        embargo_policy=embargo_pol,
    )

    assert len(agg_res.fold_results) == 2
    assert agg_res.total_samples > 0
    assert "mean_mae" in agg_res.aggregate_metrics

    # Plan with validation duration
    cfg_val = SplitPlanConfig(
        window_policy=WindowPolicy.EXPANDING,
        train_duration=timedelta(hours=1),
        validation_duration=timedelta(hours=1),
        test_duration=timedelta(hours=1),
        step_duration=timedelta(hours=1),
    )
    plan_val = WalkForwardPlanner.generate_plan(t_start, t_end, cfg_val, plan_id="wf_val_plan")
    agg_val = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
        baseline_factory=HistoricalMeanBaseline,
        plan=plan_val,
        samples=samples,
        role=EvaluationRole.VALIDATION_SELECTION,
        purge_policy=purge_pol,
        embargo_policy=embargo_pol,
    )
    assert len(agg_val.fold_results) > 0
    assert agg_val.evaluation_role == EvaluationRole.VALIDATION_SELECTION
