"""Unit tests for walk-forward planning, rolling/expanding windows, purging and embargo."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from btg_ai_trader.statistical_baselines.boundaries import (
    EvaluationBoundary,
    TemporalFold,
)
from btg_ai_trader.statistical_baselines.domain import (
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.splits import (
    EmbargoPolicy,
    PurgePolicy,
    SplitPlanConfig,
    WalkForwardPlanner,
    WindowPolicy,
)


def test_window_policy_enum() -> None:
    assert WindowPolicy.EXPANDING.value == "EXPANDING"
    assert WindowPolicy.ROLLING.value == "ROLLING"


def test_purge_policy_validation() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        PurgePolicy(default_horizon=timedelta(minutes=-1))


def test_purge_policy_behavior() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    t_target = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)
    eval_start = datetime(2026, 9, 1, 10, 30, tzinfo=UTC)

    sample = StatisticalSample(
        sample_id="s1",
        feature_knowledge_time=t0,
        target_knowledge_time=t_target,
        target_value=Decimal("100"),
        target_semantics=TargetSemantics.CONTINUOUS,
    )

    # When purge_overlapping is False
    no_purge = PurgePolicy(purge_overlapping=False)
    assert no_purge.should_purge(sample, eval_start) is False

    # When purge_overlapping is True, target crosses eval_start -> Purged
    purge_active = PurgePolicy(purge_overlapping=True)
    assert purge_active.should_purge(sample, eval_start) is True

    # Target before eval_start -> not purged
    eval_start_later = datetime(2026, 9, 1, 11, 30, tzinfo=UTC)
    assert purge_active.should_purge(sample, eval_start_later) is False

    # Information interval crossing eval_start -> Purged
    sample_with_info = StatisticalSample(
        sample_id="s2",
        feature_knowledge_time=t0,
        target_knowledge_time=t0,
        target_value=Decimal("100"),
        target_semantics=TargetSemantics.CONTINUOUS,
        information_interval=(t0, t0 + timedelta(hours=2)),
    )
    assert purge_active.should_purge(sample_with_info, eval_start) is True

    # Default horizon crossing eval_start -> Purged
    purge_with_default = PurgePolicy(default_horizon=timedelta(hours=1))
    sample_no_info = StatisticalSample(
        sample_id="s3",
        feature_knowledge_time=t0,
        target_knowledge_time=t0,
        target_value=Decimal("100"),
        target_semantics=TargetSemantics.CONTINUOUS,
    )
    assert purge_with_default.should_purge(sample_no_info, eval_start) is True

    # Info interval ending before or at eval_start -> Not purged
    sample_info_ok = StatisticalSample(
        sample_id="s4",
        feature_knowledge_time=t0,
        target_knowledge_time=t0,
        target_value=Decimal("100"),
        target_semantics=TargetSemantics.CONTINUOUS,
        information_interval=(t0, eval_start),
    )
    assert purge_active.should_purge(sample_info_ok, eval_start) is False

    # Default horizon ending before or at eval_start -> Not purged
    eval_start_far = t0 + timedelta(hours=3)
    assert purge_with_default.should_purge(sample_no_info, eval_start_far) is False


def test_embargo_policy() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        EmbargoPolicy(duration=timedelta(minutes=-5))

    with pytest.raises(TypeError):
        EmbargoPolicy()  # type: ignore[call-arg]

    zero_embargo = EmbargoPolicy(duration=timedelta(0))
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    assert zero_embargo.is_in_embargo(t0, t0) is False

    positive_embargo = EmbargoPolicy(duration=timedelta(minutes=15))
    assert positive_embargo.is_in_embargo(t0 + timedelta(minutes=5), t0) is True
    assert positive_embargo.is_in_embargo(t0 + timedelta(minutes=15), t0) is False
    assert positive_embargo.is_in_embargo(t0 - timedelta(minutes=1), t0) is False


def test_split_plan_config_validation() -> None:
    with pytest.raises(ValueError, match="train_duration must be positive"):
        SplitPlanConfig(
            window_policy=WindowPolicy.EXPANDING,
            train_duration=timedelta(0),
            test_duration=timedelta(hours=1),
            step_duration=timedelta(hours=1),
        )

    with pytest.raises(ValueError, match="test_duration must be positive"):
        SplitPlanConfig(
            window_policy=WindowPolicy.EXPANDING,
            train_duration=timedelta(hours=1),
            test_duration=timedelta(0),
            step_duration=timedelta(hours=1),
        )

    with pytest.raises(ValueError, match="step_duration must be positive"):
        SplitPlanConfig(
            window_policy=WindowPolicy.EXPANDING,
            train_duration=timedelta(hours=1),
            test_duration=timedelta(hours=1),
            step_duration=timedelta(0),
        )

    with pytest.raises(ValueError, match="validation_duration must be positive"):
        SplitPlanConfig(
            window_policy=WindowPolicy.EXPANDING,
            train_duration=timedelta(hours=1),
            test_duration=timedelta(hours=1),
            step_duration=timedelta(hours=1),
            validation_duration=timedelta(0),
        )


def test_forbid_random_shuffle() -> None:
    with pytest.raises(ValueError, match="Random shuffle cross-validation is forbidden"):
        WalkForwardPlanner.forbid_random_shuffle(shuffle=True, k=5)


def test_generate_plan_expanding_and_rolling() -> None:
    t_start = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_end = datetime(2026, 9, 1, 15, 0, tzinfo=UTC)

    cfg_exp = SplitPlanConfig(
        window_policy=WindowPolicy.EXPANDING,
        train_duration=timedelta(hours=2),
        test_duration=timedelta(hours=1),
        step_duration=timedelta(hours=1),
    )
    plan_exp = WalkForwardPlanner.generate_plan(t_start, t_end, cfg_exp, plan_id="exp_plan")
    assert len(plan_exp.folds) == 4
    # Expanding window: all folds start training at t_start
    for fold in plan_exp.folds:
        assert fold.training_boundary.start_time == t_start

    cfg_roll = SplitPlanConfig(
        window_policy=WindowPolicy.ROLLING,
        train_duration=timedelta(hours=2),
        test_duration=timedelta(hours=1),
        step_duration=timedelta(hours=1),
    )
    plan_roll = WalkForwardPlanner.generate_plan(t_start, t_end, cfg_roll, plan_id="roll_plan")
    assert len(plan_roll.folds) == 4
    # Rolling window: training start advances each fold
    assert plan_roll.folds[0].training_boundary.start_time == t_start
    assert plan_roll.folds[1].training_boundary.start_time == t_start + timedelta(hours=1)


def test_generate_plan_with_validation_and_embargo() -> None:
    t_start = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_end = datetime(2026, 9, 1, 15, 0, tzinfo=UTC)

    cfg = SplitPlanConfig(
        window_policy=WindowPolicy.EXPANDING,
        train_duration=timedelta(hours=2),
        validation_duration=timedelta(hours=1),
        test_duration=timedelta(hours=1),
        step_duration=timedelta(hours=1),
        embargo_policy=EmbargoPolicy(duration=timedelta(minutes=15)),
    )
    plan = WalkForwardPlanner.generate_plan(t_start, t_end, cfg, plan_id="val_emb_plan")
    assert len(plan.folds) > 0
    fold0 = plan.folds[0]
    assert fold0.validation_boundary is not None
    assert fold0.embargo_interval is not None


def test_generate_plan_validation_errors() -> None:
    t_start = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_end = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    cfg = SplitPlanConfig(
        window_policy=WindowPolicy.EXPANDING,
        train_duration=timedelta(hours=2),
        test_duration=timedelta(hours=1),
        step_duration=timedelta(hours=1),
    )
    # Start >= end
    with pytest.raises(ValueError, match="earlier than end_time"):
        WalkForwardPlanner.generate_plan(t_end, t_start, cfg, "p")

    # Span smaller than required
    with pytest.raises(ValueError, match="smaller than minimum required"):
        WalkForwardPlanner.generate_plan(t_start, t_end, cfg, "p")


def test_partition_samples() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_train_end = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)
    t_test_end = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    dev_b = EvaluationBoundary(t0, t_test_end, knowledge_cutoff=t0)
    train_b = EvaluationBoundary(t0, t_train_end, knowledge_cutoff=t0)
    test_b = EvaluationBoundary(t_train_end, t_test_end, knowledge_cutoff=t_train_end)

    fold = TemporalFold(
        fold_id="f1",
        development_boundary=dev_b,
        training_boundary=train_b,
        protected_evaluation_boundary=test_b,
        knowledge_cutoff=t_train_end,
        window_policy_name="EXPANDING",
    )

    # Sample 1: Admissible train
    s1 = StatisticalSample(
        sample_id="s1",
        feature_knowledge_time=t0 + timedelta(minutes=10),
        target_knowledge_time=t0 + timedelta(minutes=30),
        target_value=Decimal("10"),
        target_semantics=TargetSemantics.CONTINUOUS,
    )
    # Sample 2: In train window but future target beyond cutoff -> excluded
    s2_future = StatisticalSample(
        sample_id="s2_fut",
        feature_knowledge_time=t0 + timedelta(minutes=20),
        target_knowledge_time=t_train_end + timedelta(minutes=10),
        target_value=Decimal("20"),
        target_semantics=TargetSemantics.CONTINUOUS,
    )
    # Sample 3: In train window but purged because information interval crosses eval_start
    s3_purged = StatisticalSample(
        sample_id="s3_purge",
        feature_knowledge_time=t0 + timedelta(minutes=50),
        target_knowledge_time=t_train_end - timedelta(minutes=5),
        target_value=Decimal("30"),
        target_semantics=TargetSemantics.CONTINUOUS,
        information_interval=(t0 + timedelta(minutes=50), t_train_end + timedelta(minutes=15)),
    )
    # Sample 4: Valid test sample
    s4_test = StatisticalSample(
        sample_id="s4_test",
        feature_knowledge_time=t_train_end + timedelta(minutes=10),
        target_knowledge_time=t_train_end + timedelta(minutes=30),
        target_value=Decimal("40"),
        target_semantics=TargetSemantics.CONTINUOUS,
    )
    # Sample 5: Outside all boundaries (after test end)
    s5_outside = StatisticalSample(
        sample_id="s5_out",
        feature_knowledge_time=t_test_end + timedelta(minutes=10),
        target_knowledge_time=t_test_end + timedelta(minutes=20),
        target_value=Decimal("50"),
        target_semantics=TargetSemantics.CONTINUOUS,
    )

    purge_pol = PurgePolicy(purge_overlapping=True)
    embargo_pol = EmbargoPolicy(duration=timedelta(0))

    train_set, val_set, test_set = WalkForwardPlanner.partition_samples(
        [s1, s2_future, s3_purged, s4_test, s5_outside],
        fold,
        purge_pol,
        embargo_pol,
    )

    assert len(train_set) == 1
    assert train_set[0].sample_id == "s1"
    assert val_set is None
    assert len(test_set) == 1
    assert test_set[0].sample_id == "s4_test"

    # Test embargo on eval samples when no validation set exists
    embargo_eval_pol = EmbargoPolicy(duration=timedelta(minutes=15))
    s_early_test = StatisticalSample(
        sample_id="s_early",
        feature_knowledge_time=t_train_end + timedelta(minutes=5),
        target_knowledge_time=t_train_end + timedelta(minutes=10),
        target_value=Decimal("15"),
        target_semantics=TargetSemantics.CONTINUOUS,
    )
    s_late_test = StatisticalSample(
        sample_id="s_late",
        feature_knowledge_time=t_train_end + timedelta(minutes=20),
        target_knowledge_time=t_train_end + timedelta(minutes=25),
        target_value=Decimal("18"),
        target_semantics=TargetSemantics.CONTINUOUS,
    )
    _, _, test_emb = WalkForwardPlanner.partition_samples(
        [s_early_test, s_late_test],
        fold,
        purge_pol,
        embargo_eval_pol,
    )
    assert len(test_emb) == 1
    assert test_emb[0].sample_id == "s_late"


def test_partition_samples_duplicate_id_rejected() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_train_end = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)
    t_test_end = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    eval_b = EvaluationBoundary(t_train_end, t_test_end, knowledge_cutoff=t_train_end)
    fold = TemporalFold(
        fold_id="f1",
        development_boundary=EvaluationBoundary(t0, t_test_end, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, t_train_end, knowledge_cutoff=t0),
        protected_evaluation_boundary=eval_b,
        knowledge_cutoff=t_train_end,
        window_policy_name="EXPANDING",
    )
    s1 = StatisticalSample(
        sample_id="dup_id",
        feature_knowledge_time=t0 + timedelta(minutes=10),
        target_knowledge_time=t0 + timedelta(minutes=30),
        target_value=Decimal("10"),
        target_semantics=TargetSemantics.CONTINUOUS,
    )
    with pytest.raises(ValueError, match="Duplicate sample_id"):
        WalkForwardPlanner.partition_samples(
            [s1, s1], fold, PurgePolicy(), EmbargoPolicy(duration=timedelta(0))
        )


def test_partition_samples_with_validation_and_embargo() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_train_end = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)
    t_val_end = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    t_test_end = datetime(2026, 9, 1, 13, 0, tzinfo=UTC)

    val_b = EvaluationBoundary(t_train_end, t_val_end, knowledge_cutoff=t_train_end)
    test_b = EvaluationBoundary(t_val_end, t_test_end, knowledge_cutoff=t_val_end)
    fold = TemporalFold(
        fold_id="f1",
        development_boundary=EvaluationBoundary(t0, t_test_end, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, t_train_end, knowledge_cutoff=t0),
        validation_boundary=val_b,
        protected_evaluation_boundary=test_b,
        knowledge_cutoff=t_train_end,
        window_policy_name="EXPANDING",
    )

    s_embargoed = StatisticalSample(
        sample_id="s_emb",
        feature_knowledge_time=t_train_end + timedelta(minutes=5),
        target_knowledge_time=t_train_end + timedelta(minutes=10),
        target_value=Decimal("10"),
        target_semantics=TargetSemantics.CONTINUOUS,
    )
    s_val = StatisticalSample(
        sample_id="s_val",
        feature_knowledge_time=t_train_end + timedelta(minutes=25),
        target_knowledge_time=t_train_end + timedelta(minutes=30),
        target_value=Decimal("20"),
        target_semantics=TargetSemantics.CONTINUOUS,
    )

    embargo_pol = EmbargoPolicy(duration=timedelta(minutes=15))
    train_set, val_set, test_set = WalkForwardPlanner.partition_samples(
        [s_embargoed, s_val],
        fold,
        PurgePolicy(),
        embargo_pol,
    )
    assert val_set is not None
    assert len(val_set) == 1
    assert val_set[0].sample_id == "s_val"
