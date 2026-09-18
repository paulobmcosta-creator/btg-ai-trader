"""Tests for ML Engine quantitative evaluation metrics."""

from decimal import Decimal

import pytest

from btg_ai_trader.ml_engine.metrics import (
    compute_brier_score,
    compute_calibration_diagnostics,
    compute_continuous_metrics,
    compute_log_loss,
    compute_roc_auc,
)
from btg_ai_trader.statistical_baselines.metrics import NumericPolicy


def test_brier_score() -> None:
    policy = NumericPolicy(precision=6)
    y_true = [1, 0, 1, 1]
    y_prob = [Decimal("0.9"), Decimal("0.1"), Decimal("0.8"), Decimal("0.4")]

    # Errors: (0.9-1)^2 = 0.01, (0.1-0)^2 = 0.01, (0.8-1)^2 = 0.04, (0.4-1)^2 = 0.36
    # Total = 0.42 / 4 = 0.105
    score = compute_brier_score(y_true, y_prob, policy)
    assert score == Decimal("0.105")


def test_log_loss() -> None:
    policy = NumericPolicy(precision=6)
    y_true = [1, 0]
    y_prob = [Decimal("0.9"), Decimal("0.1")]

    loss = compute_log_loss(y_true, y_prob, policy)
    assert loss > Decimal(0)

    with pytest.raises(ValueError, match="Clipping epsilon must be strictly in"):
        compute_log_loss(y_true, y_prob, policy, eps=Decimal("0.6"))


def test_roc_auc_and_ties() -> None:
    policy = NumericPolicy(precision=6)
    y_true = [0, 0, 1, 1]
    # Perfect ranking
    y_prob = [Decimal("0.1"), Decimal("0.2"), Decimal("0.8"), Decimal("0.9")]
    auc = compute_roc_auc(y_true, y_prob, policy)
    assert auc == Decimal("1.0")

    # Ties ranking
    y_prob_ties = [Decimal("0.5"), Decimal("0.5"), Decimal("0.5"), Decimal("0.5")]
    auc_ties = compute_roc_auc(y_true, y_prob_ties, policy)
    assert auc_ties == Decimal("0.5")

    # Single class error
    with pytest.raises(ValueError, match="single-class data"):
        compute_roc_auc([1, 1], [Decimal("0.5"), Decimal("0.6")], policy)


def test_calibration_diagnostics() -> None:
    policy = NumericPolicy(precision=6)
    y_true = [1, 0, 1, 0]
    y_prob = [Decimal("0.85"), Decimal("0.15"), Decimal("0.75"), Decimal("0.25")]

    diag = compute_calibration_diagnostics(y_true, y_prob, policy, n_bins=5)
    assert diag.ece >= Decimal(0)
    assert diag.mce >= Decimal(0)
    assert len(diag.bins) == 5


def test_continuous_metrics() -> None:
    policy = NumericPolicy(precision=6)
    y_true = [Decimal("10.0"), Decimal("20.0"), Decimal("30.0")]
    y_pred = [Decimal("12.0"), Decimal("18.0"), Decimal("32.0")]

    # abs errors: 2, 2, 2 -> mae = 2.0
    # sq errors: 4, 4, 4 -> mse = 4.0, rmse = 2.0
    # bias: 2, -2, 2 -> mean_bias = 0.666667
    report = compute_continuous_metrics(y_true, y_pred, policy)
    assert report.mae == Decimal("2.0")
    assert report.mse == Decimal("4.0")
    assert report.rmse == Decimal("2.0")
    assert report.sample_count == 3
    assert report.r2_score is not None

    # Zero variance target -> r2 is None
    y_const = [Decimal("10.0"), Decimal("10.0")]
    y_pred_const = [Decimal("11.0"), Decimal("9.0")]
    rep_const = compute_continuous_metrics(y_const, y_pred_const, policy)
    assert rep_const.r2_score is None
