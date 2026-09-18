"""Unit tests for deterministic Decimal quantitative metrics."""

from decimal import Decimal

import pytest

from btg_ai_trader.statistical_baselines.metrics import (
    accuracy_score,
    base_rate,
    brier_score,
    class_prevalence,
    confusion_matrix_counts,
    mean_absolute_error,
    mean_bias,
    mean_squared_error,
    root_mean_squared_error,
)


def test_continuous_metrics_valid() -> None:
    preds = [Decimal("10.0"), Decimal("22.0"), Decimal("29.0")]
    targs = [Decimal("12.0"), Decimal("20.0"), Decimal("30.0")]
    # Errors: -2, +2, -1
    # Abs errors: 2, 2, 1 -> sum = 5 / 3
    # Sq errors: 4, 4, 1 -> sum = 9 / 3 = 3
    # Bias: (-2 + 2 - 1) / 3 = -1 / 3

    assert mean_absolute_error(preds, targs) == Decimal("5") / Decimal("3")
    assert mean_squared_error(preds, targs) == Decimal("3")
    assert root_mean_squared_error(preds, targs) == Decimal("3").sqrt()
    assert mean_bias(preds, targs) == Decimal("-1") / Decimal("3")


def test_continuous_metrics_empty_and_mismatched() -> None:
    with pytest.raises(ValueError, match="empty sequence"):
        mean_absolute_error([], [])
    with pytest.raises(ValueError, match="empty sequence"):
        mean_squared_error([], [])
    with pytest.raises(ValueError, match="empty sequence"):
        mean_bias([], [])

    with pytest.raises(ValueError, match="Length mismatch"):
        mean_absolute_error([Decimal("1")], [Decimal("1"), Decimal("2")])
    with pytest.raises(ValueError, match="Length mismatch"):
        mean_squared_error([Decimal("1")], [Decimal("1"), Decimal("2")])
    with pytest.raises(ValueError, match="Length mismatch"):
        mean_bias([Decimal("1")], [Decimal("1"), Decimal("2")])


def test_brier_score_valid() -> None:
    # Probabilities: [0.8, 0.2]
    # Targets: [1, 0]
    # Errors: (0.8 - 1)^2 = 0.04, (0.2 - 0)^2 = 0.04 -> mean = 0.04
    probs = [Decimal("0.8"), Decimal("0.2")]
    targs = [Decimal("1"), Decimal("0")]
    assert brier_score(probs, targs) == Decimal("0.04")


def test_brier_score_validation() -> None:
    with pytest.raises(ValueError, match="empty sequence"):
        brier_score([], [])
    with pytest.raises(ValueError, match="Length mismatch"):
        brier_score([Decimal("0.5")], [])
    with pytest.raises(ValueError, match="must be in"):
        brier_score([Decimal("1.5")], [Decimal("1")])
    with pytest.raises(ValueError, match="must be in"):
        brier_score([Decimal("-0.1")], [Decimal("1")])
    with pytest.raises(ValueError, match="Binary targets must be 0 or 1"):
        brier_score([Decimal("0.5")], [Decimal("2")])


def test_base_rate() -> None:
    with pytest.raises(ValueError, match="empty sequence"):
        base_rate([])
    with pytest.raises(ValueError, match="Binary targets must be 0 or 1"):
        base_rate([Decimal("3")])

    targs = [Decimal("1"), Decimal("0"), Decimal("1"), Decimal("1")]
    assert base_rate(targs) == Decimal("0.75")


def test_accuracy_score() -> None:
    with pytest.raises(ValueError, match="empty sequence"):
        accuracy_score([], [])
    with pytest.raises(ValueError, match="Length mismatch"):
        accuracy_score(["A"], ["A", "B"])

    preds = ["BUY", "SELL", "HOLD", "BUY"]
    targs = ["BUY", "BUY", "HOLD", "BUY"]
    # 3 correct out of 4
    assert accuracy_score(preds, targs) == Decimal("0.75")


def test_class_prevalence() -> None:
    with pytest.raises(ValueError, match="empty sequence"):
        class_prevalence([])

    targs = ["BUY", "BUY", "SELL", "HOLD"]
    prev = class_prevalence(targs)
    assert prev["BUY"] == Decimal("0.5")
    assert prev["SELL"] == Decimal("0.25")
    assert prev["HOLD"] == Decimal("0.25")


def test_confusion_matrix_counts() -> None:
    preds = ["BUY", "SELL", "BUY", "HOLD"]
    targs = ["BUY", "BUY", "SELL", "HOLD"]

    # Auto inferred labels
    cm = confusion_matrix_counts(preds, targs)
    assert cm[("BUY", "BUY")] == 1
    assert cm[("BUY", "SELL")] == 1
    assert cm[("SELL", "BUY")] == 1
    assert cm[("HOLD", "HOLD")] == 1
    assert cm[("HOLD", "BUY")] == 0

    # Explicit labels with unlisted target/pred
    cm_explicit = confusion_matrix_counts(preds, targs, labels=["BUY", "SELL", "HOLD", "OTHER"])
    assert cm_explicit[("OTHER", "OTHER")] == 0
    assert cm_explicit[("BUY", "BUY")] == 1

    # Pred or target not in explicit labels
    cm_subset = confusion_matrix_counts(["BUY", "UNKNOWN"], ["BUY", "BUY"], labels=["BUY"])
    assert cm_subset[("BUY", "UNKNOWN")] == 1
