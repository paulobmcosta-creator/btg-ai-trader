"""Complete metric behavior tests for Sprint 5."""

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


def test_binary_metrics_and_error_contracts() -> None:
    policy = NumericPolicy(precision=8)
    truth = [1, 0, 1, 0]
    probs = [Decimal("0.9"), Decimal("0.1"), Decimal("0.8"), Decimal("0.2")]
    assert compute_brier_score(truth, probs, policy) == Decimal("0.025")
    assert compute_log_loss(truth, probs, policy) > 0
    assert compute_roc_auc(truth, probs, policy) == Decimal("1.0")
    assert compute_roc_auc(
        truth, [Decimal("0.5")] * 4, policy
    ) == Decimal("0.5")

    for function in (compute_brier_score, compute_log_loss, compute_roc_auc):
        with pytest.raises(ValueError, match="identical length"):
            function([1], [], policy)
        with pytest.raises(ValueError, match="empty"):
            function([], [], policy)
    with pytest.raises(ValueError, match="single-class"):
        compute_roc_auc([1, 1], [Decimal("0.5"), Decimal("0.6")], policy)
    with pytest.raises(ValueError, match="epsilon"):
        compute_log_loss([1], [Decimal("0.5")], policy, eps=Decimal("0"))
    with pytest.raises(ValueError, match="epsilon"):
        compute_log_loss([1], [Decimal("0.5")], policy, eps=Decimal("0.5"))


def test_calibration_bins_and_errors() -> None:
    policy = NumericPolicy(precision=8)
    diagnostics = compute_calibration_diagnostics(
        [1, 0, 1, 0],
        [Decimal("0.9"), Decimal("0.1"), Decimal("0.7"), Decimal("0.3")],
        policy,
        n_bins=8,
    )
    assert len(diagnostics.bins) == 8
    assert diagnostics.ece >= 0
    assert diagnostics.mce >= 0
    assert any(item.sample_count == 0 for item in diagnostics.bins)
    with pytest.raises(ValueError, match="identical length"):
        compute_calibration_diagnostics([1], [], policy)
    with pytest.raises(ValueError, match="empty"):
        compute_calibration_diagnostics([], [], policy)
    with pytest.raises(ValueError, match="positive"):
        compute_calibration_diagnostics([1], [Decimal("0.5")], policy, n_bins=0)


def test_continuous_metrics_and_errors() -> None:
    policy = NumericPolicy(precision=8)
    report = compute_continuous_metrics(
        [Decimal("1"), Decimal("2"), Decimal("3")],
        [Decimal("1"), Decimal("2.5"), Decimal("2.5")],
        policy,
    )
    assert report.sample_count == 3
    assert report.r2_score is not None
    constant = compute_continuous_metrics(
        [Decimal("1"), Decimal("1")],
        [Decimal("0"), Decimal("2")],
        policy,
    )
    assert constant.r2_score is None
    with pytest.raises(ValueError, match="identical length"):
        compute_continuous_metrics([Decimal("1")], [], policy)
    with pytest.raises(ValueError, match="empty"):
        compute_continuous_metrics([], [], policy)
