"""Adversarial leakage tests: proving no future labels or cross-fold information leaks."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from btg_ai_trader.statistical_baselines.baselines import HistoricalMeanBaseline
from btg_ai_trader.statistical_baselines.boundaries import (
    EvaluationBoundary,
    TemporalFold,
)
from btg_ai_trader.statistical_baselines.comparison import Comparator, ModelComparisonResult
from btg_ai_trader.statistical_baselines.domain import (
    EvaluationRole,
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.splits import (
    EmbargoPolicy,
    PurgePolicy,
    WalkForwardPlanner,
)


def _make_sample(
    sample_id: str,
    feature_time: datetime,
    target_time: datetime,
    target_val: Decimal | str,
    info_interval: tuple[datetime, datetime] | None = None,
) -> StatisticalSample:
    return StatisticalSample(
        sample_id=sample_id,
        feature_knowledge_time=feature_time,
        target_knowledge_time=target_time,
        target_value=target_val,
        target_semantics=TargetSemantics.CONTINUOUS,
        information_interval=info_interval,
    )


def test_adversarial_future_target_injection_rejected() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    cutoff = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)
    eval_end = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    fold = TemporalFold(
        fold_id="f_leakage",
        development_boundary=EvaluationBoundary(t0, eval_end, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, cutoff, knowledge_cutoff=t0),
        protected_evaluation_boundary=EvaluationBoundary(cutoff, eval_end, knowledge_cutoff=cutoff),
        knowledge_cutoff=cutoff,
        window_policy_name="EXPANDING",
    )

    # Legitimate training sample
    s_legit = _make_sample("s_legit", t0, cutoff - timedelta(minutes=10), Decimal("10"))

    # Adversarial sample: feature_time is in train window, but target_knowledge_time is after cutoff
    s_future_leak = _make_sample(
        "s_adversarial_future_leak",
        cutoff - timedelta(minutes=1),
        cutoff + timedelta(minutes=30),
        Decimal("9999"),
    )

    # 1. WalkForwardPlanner must strictly exclude it from the train set
    train_set, _, _ = WalkForwardPlanner.partition_samples(
        [s_legit, s_future_leak],
        fold,
        PurgePolicy(default_horizon=timedelta(minutes=10)),
        EmbargoPolicy(duration=timedelta(0)),
    )
    assert len(train_set) == 1
    assert train_set[0].sample_id == "s_legit"

    # 2. If directly forced into baseline.fit, fit must raise ValueError and reject it
    baseline = HistoricalMeanBaseline()
    with pytest.raises(ValueError, match="not causally admissible at cutoff"):
        baseline.fit([s_legit, s_future_leak], knowledge_cutoff=cutoff)


def test_adversarial_overlapping_information_interval_purged() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    cutoff = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)
    eval_end = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    fold = TemporalFold(
        fold_id="f_purge",
        development_boundary=EvaluationBoundary(t0, eval_end, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, cutoff, knowledge_cutoff=t0),
        protected_evaluation_boundary=EvaluationBoundary(cutoff, eval_end, knowledge_cutoff=cutoff),
        knowledge_cutoff=cutoff,
        window_policy_name="EXPANDING",
    )

    # Target knowledge time is before cutoff, but information interval crosses into eval
    s_overlapping = _make_sample(
        "s_overlapping",
        cutoff - timedelta(minutes=30),
        cutoff - timedelta(minutes=5),
        Decimal("50"),
        info_interval=(cutoff - timedelta(minutes=30), cutoff + timedelta(minutes=15)),
    )

    train_set, _, _ = WalkForwardPlanner.partition_samples(
        [s_overlapping],
        fold,
        PurgePolicy(purge_overlapping=True),
        EmbargoPolicy(duration=timedelta(0)),
    )
    # Must be purged
    assert len(train_set) == 0


def test_adversarial_embargo_violation_blocked() -> None:
    t0 = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    t_train_end = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)
    t_val_end = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    t_test_end = datetime(2026, 9, 1, 13, 0, tzinfo=UTC)

    val_b = EvaluationBoundary(t_train_end, t_val_end, knowledge_cutoff=t_train_end)
    eval_b = EvaluationBoundary(t_val_end, t_test_end, knowledge_cutoff=t_val_end)
    fold = TemporalFold(
        fold_id="f_embargo",
        development_boundary=EvaluationBoundary(t0, t_test_end, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, t_train_end, knowledge_cutoff=t0),
        validation_boundary=val_b,
        protected_evaluation_boundary=eval_b,
        knowledge_cutoff=t_train_end,
        window_policy_name="EXPANDING",
        embargo_interval=(t_train_end, t_train_end + timedelta(minutes=15)),
    )

    # Sample falling squarely inside the 15-minute post-training embargo interval
    s_in_embargo = _make_sample(
        "s_in_embargo",
        t_train_end + timedelta(minutes=5),
        t_train_end + timedelta(minutes=10),
        Decimal("10"),
    )

    # Sample after embargo
    s_after_embargo = _make_sample(
        "s_after_embargo",
        t_train_end + timedelta(minutes=20),
        t_train_end + timedelta(minutes=25),
        Decimal("20"),
    )

    _, val_set, _ = WalkForwardPlanner.partition_samples(
        [s_in_embargo, s_after_embargo],
        fold,
        PurgePolicy(),
        EmbargoPolicy(duration=timedelta(minutes=15)),
    )
    assert val_set is not None
    assert len(val_set) == 1
    assert val_set[0].sample_id == "s_after_embargo"


def test_adversarial_winner_selection_on_protected_test_strictly_blocked() -> None:
    comp_test = ModelComparisonResult(
        evaluation_role=EvaluationRole.PROTECTED_TEST,
        metric_name="mae",
        higher_is_better=False,
        rankings=(("cand1", Decimal("1.0")), ("cand2", Decimal("2.0"))),
        winner_candidate_id=None,
    )
    with pytest.raises(
        ValueError,
        match="Selecting a winner or promoting a candidate based on PROTECTED_TEST",
    ):
        Comparator.select_best_candidate(comp_test)
