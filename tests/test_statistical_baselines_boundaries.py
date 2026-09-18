"""Unit tests for EvaluationBoundary, TemporalFold, and WalkForwardPlan."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from btg_ai_trader.statistical_baselines.boundaries import (
    EvaluationBoundary,
    TemporalFold,
    WalkForwardPlan,
)
from btg_ai_trader.statistical_baselines.domain import (
    StatisticalSample,
    TargetSemantics,
)


def test_evaluation_boundary_valid() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    t2 = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)

    b = EvaluationBoundary(
        start_time=t1,
        end_time=t2,
        knowledge_cutoff=t0,
        start_inclusive=True,
        end_inclusive=False,
    )
    assert b.contains_timestamp(t1) is True
    assert b.contains_timestamp(t2) is False
    assert b.contains_timestamp(t1 + timedelta(minutes=30)) is True
    assert b.contains_timestamp(t0) is False


def test_evaluation_boundary_inclusive_endpoints() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    t2 = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)

    b = EvaluationBoundary(
        start_time=t1,
        end_time=t2,
        knowledge_cutoff=t0,
        start_inclusive=False,
        end_inclusive=True,
    )
    assert b.contains_timestamp(t1) is False
    assert b.contains_timestamp(t2) is True


def test_evaluation_boundary_contains_sample() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_feat = datetime(2026, 9, 1, 10, 15, tzinfo=UTC)
    t_tgt = datetime(2026, 9, 1, 10, 45, tzinfo=UTC)

    b = EvaluationBoundary(
        start_time=datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
        end_time=datetime(2026, 9, 1, 10, 30, tzinfo=UTC),
        knowledge_cutoff=t0,
    )
    sample = StatisticalSample(
        sample_id="s_b1",
        feature_knowledge_time=t_feat,
        target_knowledge_time=t_tgt,
        target_value=Decimal("100"),
        target_semantics=TargetSemantics.CONTINUOUS,
    )
    assert b.contains_sample(sample, by_feature_time=True) is True
    assert b.contains_sample(sample, by_feature_time=False) is False


def test_evaluation_boundary_invariants() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)
    naive_t = datetime(2026, 9, 1, 10, 0)

    # Naive start
    with pytest.raises(ValueError, match="timezone-aware"):
        EvaluationBoundary(start_time=naive_t, end_time=t1, knowledge_cutoff=t0)

    # Naive end
    with pytest.raises(ValueError, match="timezone-aware"):
        EvaluationBoundary(start_time=t0, end_time=naive_t, knowledge_cutoff=t0)

    # Naive cutoff
    with pytest.raises(ValueError, match="timezone-aware"):
        EvaluationBoundary(start_time=t0, end_time=t1, knowledge_cutoff=naive_t)

    # start >= end
    with pytest.raises(ValueError, match="earlier than end_time"):
        EvaluationBoundary(start_time=t1, end_time=t0, knowledge_cutoff=t0)
    with pytest.raises(ValueError, match="earlier than end_time"):
        EvaluationBoundary(start_time=t0, end_time=t0, knowledge_cutoff=t0)

    # cutoff > start
    with pytest.raises(ValueError, match="cannot be after start"):
        EvaluationBoundary(start_time=t0, end_time=t1, knowledge_cutoff=t1)


def test_temporal_fold_valid() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_train_start = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_train_end = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    t_val_start = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    t_val_end = datetime(2026, 9, 1, 13, 0, tzinfo=UTC)
    t_test_start = datetime(2026, 9, 1, 13, 0, tzinfo=UTC)
    t_test_end = datetime(2026, 9, 1, 15, 0, tzinfo=UTC)

    dev_b = EvaluationBoundary(t_train_start, t_test_end, knowledge_cutoff=t0)
    train_b = EvaluationBoundary(t_train_start, t_train_end, knowledge_cutoff=t0)
    val_b = EvaluationBoundary(t_val_start, t_val_end, knowledge_cutoff=t_train_end)
    test_b = EvaluationBoundary(t_test_start, t_test_end, knowledge_cutoff=t_val_end)

    fold = TemporalFold(
        fold_id="fold_001",
        development_boundary=dev_b,
        training_boundary=train_b,
        validation_boundary=val_b,
        protected_evaluation_boundary=test_b,
        knowledge_cutoff=t_train_end,
        window_policy_name="EXPANDING",
        purge_interval=(t_train_end - timedelta(minutes=15), t_train_end),
        embargo_interval=(t_train_end, t_train_end + timedelta(minutes=15)),
    )
    assert fold.fold_id == "fold_001"
    assert fold.window_policy_name == "EXPANDING"


def test_temporal_fold_validation_failures() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_train_start = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_train_end = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    t_test_start = datetime(2026, 9, 1, 13, 0, tzinfo=UTC)
    t_test_end = datetime(2026, 9, 1, 15, 0, tzinfo=UTC)

    dev_b = EvaluationBoundary(t_train_start, t_test_end, knowledge_cutoff=t0)
    train_b = EvaluationBoundary(t_train_start, t_train_end, knowledge_cutoff=t0)
    test_b = EvaluationBoundary(t_test_start, t_test_end, knowledge_cutoff=t_train_end)

    # Empty fold_id
    with pytest.raises(ValueError, match="fold_id must be a non-empty string"):
        TemporalFold("", dev_b, train_b, test_b, t_train_end, "ROLLING")

    # Empty window_policy_name
    with pytest.raises(ValueError, match="window_policy_name must be a non-empty string"):
        TemporalFold("f1", dev_b, train_b, test_b, t_train_end, "")

    # Train end > test start
    train_overlap = EvaluationBoundary(t_train_start, t_test_end, knowledge_cutoff=t0)
    with pytest.raises(
        ValueError, match="cannot be later than protected_evaluation_boundary start_time"
    ):
        TemporalFold("f1", dev_b, train_overlap, test_b, t_train_end, "ROLLING")

    # Validation boundary ordering invalid
    val_early = EvaluationBoundary(t0, t_train_start + timedelta(hours=1), knowledge_cutoff=t0)
    with pytest.raises(ValueError, match="cannot be later than validation_boundary start_time"):
        TemporalFold(
            "f1", dev_b, train_b, test_b, t_train_end, "ROLLING", validation_boundary=val_early
        )

    val_late = EvaluationBoundary(
        t_test_end, t_test_end + timedelta(hours=1), knowledge_cutoff=t_train_end
    )
    with pytest.raises(
        ValueError, match="cannot be later than protected_evaluation_boundary start_time"
    ):
        TemporalFold(
            "f1", dev_b, train_b, test_b, t_train_end, "ROLLING", validation_boundary=val_late
        )

    # Purge interval start > end
    with pytest.raises(ValueError, match="purge_interval start"):
        TemporalFold(
            "f1",
            dev_b,
            train_b,
            test_b,
            t_train_end,
            "ROLLING",
            purge_interval=(t_train_end, t_train_start),
        )

    # Embargo interval start > end
    with pytest.raises(ValueError, match="embargo_interval start"):
        TemporalFold(
            "f1",
            dev_b,
            train_b,
            test_b,
            t_train_end,
            "ROLLING",
            embargo_interval=(t_test_end, t_test_start),
        )


def test_walk_forward_plan() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_train1_end = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)
    t_test1_end = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    t_train2_end = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    t_test2_end = datetime(2026, 9, 1, 13, 0, tzinfo=UTC)

    f1 = TemporalFold(
        fold_id="f1",
        development_boundary=EvaluationBoundary(t0, t_test1_end, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, t_train1_end, knowledge_cutoff=t0),
        protected_evaluation_boundary=EvaluationBoundary(
            t_train1_end, t_test1_end, knowledge_cutoff=t_train1_end
        ),
        knowledge_cutoff=t_train1_end,
        window_policy_name="EXPANDING",
    )
    f2 = TemporalFold(
        fold_id="f2",
        development_boundary=EvaluationBoundary(t0, t_test2_end, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, t_train2_end, knowledge_cutoff=t0),
        protected_evaluation_boundary=EvaluationBoundary(
            t_train2_end, t_test2_end, knowledge_cutoff=t_train2_end
        ),
        knowledge_cutoff=t_train2_end,
        window_policy_name="EXPANDING",
    )

    plan = WalkForwardPlan(plan_id="plan_001", window_policy_name="EXPANDING", folds=(f1, f2))
    assert plan.plan_id == "plan_001"
    assert len(plan.folds) == 2


def test_walk_forward_plan_validation() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_train1_end = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)
    t_test1_end = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    f1 = TemporalFold(
        fold_id="f1",
        development_boundary=EvaluationBoundary(t0, t_test1_end, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, t_train1_end, knowledge_cutoff=t0),
        protected_evaluation_boundary=EvaluationBoundary(
            t_train1_end, t_test1_end, knowledge_cutoff=t_train1_end
        ),
        knowledge_cutoff=t_train1_end,
        window_policy_name="EXPANDING",
    )

    with pytest.raises(ValueError, match="plan_id must be a non-empty string"):
        WalkForwardPlan("", "EXPANDING", (f1,))

    with pytest.raises(ValueError, match="window_policy_name must be a non-empty string"):
        WalkForwardPlan("p1", "", (f1,))

    with pytest.raises(ValueError, match="at least one fold"):
        WalkForwardPlan("p1", "EXPANDING", ())

    # Duplicate fold_id
    with pytest.raises(ValueError, match="Duplicate fold_id"):
        WalkForwardPlan("p1", "EXPANDING", (f1, f1))

    # Out of chronological order
    t_train0_end = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    t_test0_end = datetime(2026, 9, 1, 10, 30, tzinfo=UTC)
    f_earlier = TemporalFold(
        fold_id="f_earlier",
        development_boundary=EvaluationBoundary(t0, t_test0_end, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, t_train0_end, knowledge_cutoff=t0),
        protected_evaluation_boundary=EvaluationBoundary(
            t_train0_end, t_test0_end, knowledge_cutoff=t_train0_end
        ),
        knowledge_cutoff=t_train0_end,
        window_policy_name="EXPANDING",
    )
    with pytest.raises(ValueError, match="chronological order"):
        WalkForwardPlan("p1", "EXPANDING", (f1, f_earlier))
