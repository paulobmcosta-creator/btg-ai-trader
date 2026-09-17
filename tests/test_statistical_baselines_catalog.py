"""Unit tests for deterministic statistical baseline catalog."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from btg_ai_trader.statistical_baselines.baselines import (
    ConstantBaseline,
    HistoricalMeanBaseline,
    HistoricalMedianBaseline,
    HistoricalPriorProbabilityBaseline,
    LastKnownClassBaseline,
    MajorityClassBaseline,
    PersistenceBaseline,
)
from btg_ai_trader.statistical_baselines.domain import (
    StatisticalSample,
    TargetSemantics,
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


def test_constant_baseline() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)

    b = ConstantBaseline(constant_value=Decimal("42.0"))
    assert b.identity.baseline_type == "ConstantBaseline"
    assert b.is_fitted is False
    assert TargetSemantics.CONTINUOUS in b.supported_semantics

    # Unfitted predict raises RuntimeError
    eval_sample = _make_sample("s_eval", t1, t1 + timedelta(hours=1), Decimal("0"))
    with pytest.raises(RuntimeError, match="must be fitted before predict"):
        b.predict(eval_sample)

    # Fit empty
    b.fit([], knowledge_cutoff=t0)
    assert b.is_fitted is True
    pred_cold = b.predict(eval_sample)
    assert pred_cold.predicted_value == Decimal("42.0")
    assert pred_cold.is_cold_start is True

    # Fit with samples
    train_sample = _make_sample("s_train", t0 - timedelta(hours=1), t0, Decimal("10"))
    b.fit([train_sample], knowledge_cutoff=t0)
    assert b.is_fitted is True
    pred_warm = b.predict(eval_sample)
    assert pred_warm.predicted_value == Decimal("42.0")
    assert pred_warm.is_cold_start is False

    # Constant baseline with probability and class
    b_prob = ConstantBaseline(
        constant_class="UP",
        constant_probability=Decimal("0.7"),
        semantics=TargetSemantics.CATEGORICAL,
    )
    b_prob.fit([], knowledge_cutoff=t0)
    eval_cat = _make_sample(
        "s_cat", t1, t1 + timedelta(hours=1), "UP", TargetSemantics.CATEGORICAL
    )
    pred_prob = b_prob.predict(eval_cat)
    assert pred_prob.predicted_class == "UP"
    assert pred_prob.predicted_probability == Decimal("0.7")


def test_persistence_baseline() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    cutoff = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    b = PersistenceBaseline()
    assert b.supported_semantics == frozenset([TargetSemantics.CONTINUOUS])

    # Empty fit
    b.fit([], knowledge_cutoff=cutoff)
    eval_s = _make_sample(
        "s_eval", cutoff + timedelta(hours=1), cutoff + timedelta(hours=2), Decimal("0")
    )
    pred_empty = b.predict(eval_s)
    assert pred_empty.is_cold_start is True
    assert pred_empty.predicted_value is None

    # Normal fit with 3 samples
    s1 = _make_sample("s1", t0, t0 + timedelta(minutes=10), Decimal("100.0"))
    s2 = _make_sample("s2", t0, t0 + timedelta(minutes=30), Decimal("105.0"))
    s3 = _make_sample("s3", t0, t0 + timedelta(minutes=20), Decimal("102.0"))

    b.fit([s1, s2, s3], knowledge_cutoff=cutoff)
    pred = b.predict(eval_s)
    assert pred.is_cold_start is False
    # s2 has latest target_knowledge_time (minutes=30)
    assert pred.predicted_value == Decimal("105.0")
    assert pred.predicted_probability is None


def test_historical_mean_baseline() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    cutoff = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    b = HistoricalMeanBaseline()
    b.fit([], knowledge_cutoff=cutoff)
    eval_s = _make_sample(
        "s_eval", cutoff + timedelta(hours=1), cutoff + timedelta(hours=2), Decimal("0")
    )
    assert b.predict(eval_s).predicted_value is None

    s1 = _make_sample("s1", t0, t0 + timedelta(minutes=10), Decimal("10.0"))
    s2 = _make_sample("s2", t0, t0 + timedelta(minutes=20), Decimal("20.0"))
    s3 = _make_sample("s3", t0, t0 + timedelta(minutes=30), Decimal("30.0"))

    b.fit([s1, s2, s3], knowledge_cutoff=cutoff)
    pred = b.predict(eval_s)
    assert pred.predicted_value == Decimal("20.0")


def test_historical_median_baseline() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    cutoff = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    b = HistoricalMedianBaseline()
    b.fit([], knowledge_cutoff=cutoff)
    eval_s = _make_sample(
        "s_eval", cutoff + timedelta(hours=1), cutoff + timedelta(hours=2), Decimal("0")
    )
    assert b.predict(eval_s).predicted_value is None

    # Odd count
    s1 = _make_sample("s1", t0, t0 + timedelta(minutes=10), Decimal("30.0"))
    s2 = _make_sample("s2", t0, t0 + timedelta(minutes=20), Decimal("10.0"))
    s3 = _make_sample("s3", t0, t0 + timedelta(minutes=30), Decimal("20.0"))

    b.fit([s1, s2, s3], knowledge_cutoff=cutoff)
    assert b.predict(eval_s).predicted_value == Decimal("20.0")

    # Even count
    s4 = _make_sample("s4", t0, t0 + timedelta(minutes=40), Decimal("40.0"))
    b.fit([s1, s2, s3, s4], knowledge_cutoff=cutoff)
    # (20 + 30) / 2 = 25
    assert b.predict(eval_s).predicted_value == Decimal("25.0")


def test_historical_prior_probability_baseline() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    cutoff = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    b = HistoricalPriorProbabilityBaseline()
    b.fit([], knowledge_cutoff=cutoff)
    eval_s = _make_sample(
        "s_eval",
        cutoff + timedelta(hours=1),
        cutoff + timedelta(hours=2),
        Decimal("1"),
        semantics=TargetSemantics.BINARY_PROBABILITY,
    )
    pred_empty = b.predict(eval_s)
    assert pred_empty.predicted_probability is None
    assert pred_empty.predicted_value is None

    # 3 ones, 1 zero -> prior = 0.75 >= 0.5 -> predicted_value = 1
    s1 = _make_sample(
        "s1", t0, t0 + timedelta(minutes=1), Decimal("1"), TargetSemantics.BINARY_PROBABILITY
    )
    s2 = _make_sample(
        "s2", t0, t0 + timedelta(minutes=2), Decimal("1"), TargetSemantics.BINARY_PROBABILITY
    )
    s3 = _make_sample(
        "s3", t0, t0 + timedelta(minutes=3), Decimal("1"), TargetSemantics.BINARY_PROBABILITY
    )
    s4 = _make_sample(
        "s4", t0, t0 + timedelta(minutes=4), Decimal("0"), TargetSemantics.BINARY_PROBABILITY
    )

    b.fit([s1, s2, s3, s4], knowledge_cutoff=cutoff)
    pred_high = b.predict(eval_s)
    assert pred_high.predicted_probability == Decimal("0.75")
    assert pred_high.predicted_value == Decimal("1")
    assert pred_high.predicted_class == "1"

    # 1 one, 3 zeros -> prior = 0.25 < 0.5 -> predicted_value = 0
    b.fit([s1, s4, s4, s4], knowledge_cutoff=cutoff)
    pred_low = b.predict(eval_s)
    assert pred_low.predicted_probability == Decimal("0.25")
    assert pred_low.predicted_value == Decimal("0")
    assert pred_low.predicted_class == "0"


def test_majority_class_baseline() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    cutoff = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    b = MajorityClassBaseline()
    b.fit([], knowledge_cutoff=cutoff)
    eval_s = _make_sample(
        "s_eval",
        cutoff + timedelta(hours=1),
        cutoff + timedelta(hours=2),
        "BUY",
        semantics=TargetSemantics.CATEGORICAL,
    )
    assert b.predict(eval_s).predicted_class is None

    # Clear winner
    s1 = _make_sample("s1", t0, t0 + timedelta(minutes=1), "BUY", TargetSemantics.CATEGORICAL)
    s2 = _make_sample("s2", t0, t0 + timedelta(minutes=2), "BUY", TargetSemantics.CATEGORICAL)
    s3 = _make_sample("s3", t0, t0 + timedelta(minutes=3), "SELL", TargetSemantics.CATEGORICAL)

    b.fit([s1, s2, s3], knowledge_cutoff=cutoff)
    pred = b.predict(eval_s)
    assert pred.predicted_class == "BUY"
    assert pred.predicted_probability is None

    # Tie breaking: BUY vs SELL (2 each) -> BUY is alphabetically first
    s4 = _make_sample("s4", t0, t0 + timedelta(minutes=4), "SELL", TargetSemantics.CATEGORICAL)
    b.fit([s1, s2, s3, s4], knowledge_cutoff=cutoff)
    pred_tie = b.predict(eval_s)
    assert pred_tie.predicted_class == "BUY"


def test_last_known_class_baseline() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    cutoff = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    b = LastKnownClassBaseline()
    b.fit([], knowledge_cutoff=cutoff)
    eval_s = _make_sample(
        "s_eval",
        cutoff + timedelta(hours=1),
        cutoff + timedelta(hours=2),
        "BUY",
        semantics=TargetSemantics.CATEGORICAL,
    )
    assert b.predict(eval_s).predicted_class is None

    s1 = _make_sample("s1", t0, t0 + timedelta(minutes=1), "BUY", TargetSemantics.CATEGORICAL)
    s2 = _make_sample("s2", t0, t0 + timedelta(minutes=5), "SELL", TargetSemantics.CATEGORICAL)
    s3 = _make_sample("s3", t0, t0 + timedelta(minutes=3), "HOLD", TargetSemantics.CATEGORICAL)

    b.fit([s1, s2, s3], knowledge_cutoff=cutoff)
    pred = b.predict(eval_s)
    assert pred.predicted_class == "SELL"


def test_baseline_causal_and_semantic_enforcement() -> None:
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    cutoff = datetime(2026, 9, 1, 11, 0, tzinfo=UTC)

    b = PersistenceBaseline()

    # Naive knowledge_cutoff rejected
    with pytest.raises(ValueError, match="timezone-aware"):
        b.fit([], knowledge_cutoff=datetime(2026, 9, 1, 11, 0))

    # Causal violation: target_knowledge_time > cutoff
    future_sample = _make_sample(
        "s_fut",
        t0,
        cutoff + timedelta(minutes=5),
        Decimal("100.0"),
    )
    with pytest.raises(ValueError, match="not causally admissible"):
        b.fit([future_sample], knowledge_cutoff=cutoff)

    # Incompatible semantics in fit
    cat_sample = _make_sample(
        "s_cat",
        t0,
        t0 + timedelta(minutes=5),
        "UP",
        semantics=TargetSemantics.CATEGORICAL,
    )
    with pytest.raises(ValueError, match="semantics TargetSemantics.CATEGORICAL not supported"):
        b.fit([cat_sample], knowledge_cutoff=cutoff)

    # Incompatible semantics in predict
    b.fit([], knowledge_cutoff=cutoff)
    with pytest.raises(ValueError, match="semantics TargetSemantics.CATEGORICAL not supported"):
        b.predict(cat_sample)
