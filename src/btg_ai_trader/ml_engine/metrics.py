"""Deterministic evaluation metrics for binary classification and continuous regression."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, localcontext

from btg_ai_trader.statistical_baselines.metrics import NumericPolicy


def apply_numeric_policy(value: Decimal, policy: NumericPolicy) -> Decimal:
    """Normalize and round Decimal according to NumericPolicy context."""
    with localcontext(policy.get_context()):
        return +value


@dataclass(frozen=True, slots=True)
class BinaryMetricsReport:
    """Comprehensive metric report for binary classification / probabilistic forecasting."""

    brier_score: Decimal
    log_loss: Decimal
    roc_auc: Decimal | None
    base_rate: Decimal
    sample_count: int


@dataclass(frozen=True, slots=True)
class ContinuousMetricsReport:
    """Comprehensive metric report for continuous point forecasting."""

    mae: Decimal
    mse: Decimal
    rmse: Decimal
    mean_bias: Decimal
    r2_score: Decimal | None
    sample_count: int


@dataclass(frozen=True, slots=True)
class CalibrationBinResult:
    """Diagnostic calibration data for a single probability bin."""

    bin_index: int
    lower_bound: Decimal
    upper_bound: Decimal
    sample_count: int
    mean_predicted: Decimal
    observed_frequency: Decimal


@dataclass(frozen=True, slots=True)
class CalibrationDiagnostics:
    """Reliability curve and calibration error diagnostics."""

    ece: Decimal
    mce: Decimal
    bins: tuple[CalibrationBinResult, ...]


def compute_brier_score(
    y_true: Sequence[Decimal | int],
    y_prob: Sequence[Decimal],
    policy: NumericPolicy,
) -> Decimal:
    """Compute Brier Score with exact Decimal arithmetic."""
    if len(y_true) != len(y_prob):
        raise ValueError("y_true and y_prob must have identical length")
    if not y_true:
        raise ValueError("Cannot compute Brier Score on empty sequences")

    total = Decimal(0)
    for yt, yp in zip(y_true, y_prob, strict=True):
        t = Decimal(yt)
        diff = yp - t
        total += diff * diff

    mean_brier = total / Decimal(len(y_true))
    return apply_numeric_policy(mean_brier, policy)


def compute_log_loss(
    y_true: Sequence[Decimal | int],
    y_prob: Sequence[Decimal],
    policy: NumericPolicy,
    eps: Decimal = Decimal("1e-15"),
) -> Decimal:
    """Compute Log Loss with explicit clipping bounds."""
    if len(y_true) != len(y_prob):
        raise ValueError("y_true and y_prob must have identical length")
    if not y_true:
        raise ValueError("Cannot compute Log Loss on empty sequences")
    if eps <= Decimal(0) or eps >= Decimal("0.5"):
        raise ValueError("Clipping epsilon must be strictly in (0, 0.5)")

    total = Decimal(0)
    one = Decimal(1)

    for yt, yp in zip(y_true, y_prob, strict=True):
        t = Decimal(yt)
        p = max(eps, min(one - eps, yp))
        p_float = float(p)
        if t == one:
            loss = -math.log(p_float)
        else:
            loss = -math.log(1.0 - p_float)
        total += Decimal(str(loss))

    mean_loss = total / Decimal(len(y_true))
    return apply_numeric_policy(mean_loss, policy)


def compute_roc_auc(
    y_true: Sequence[Decimal | int],
    y_prob: Sequence[Decimal],
    policy: NumericPolicy,
) -> Decimal:
    """Compute ROC-AUC with deterministic rank ordering and tie-handling.

    Raises ValueError if y_true contains only a single class.
    """
    if len(y_true) != len(y_prob):
        raise ValueError("y_true and y_prob must have identical length")
    if not y_true:
        raise ValueError("Cannot compute ROC-AUC on empty sequences")

    classes = {int(yt) for yt in y_true}
    if classes != {0, 1}:
        raise ValueError(
            f"ROC-AUC is mathematically undefined for single-class data or non-binary labels: "
            f"{classes}"
        )

    indexed = sorted(enumerate(y_prob), key=lambda x: x[1])

    n = len(indexed)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j

    pos_ranks_sum = sum(ranks[idx] for idx, yt in enumerate(y_true) if int(yt) == 1)
    n_pos = sum(1 for yt in y_true if int(yt) == 1)
    n_neg = n - n_pos

    auc = (pos_ranks_sum - (n_pos * (n_pos + 1)) / 2.0) / (n_pos * n_neg)
    return apply_numeric_policy(Decimal(str(auc)), policy)


def compute_calibration_diagnostics(
    y_true: Sequence[Decimal | int],
    y_prob: Sequence[Decimal],
    policy: NumericPolicy,
    n_bins: int = 10,
) -> CalibrationDiagnostics:
    """Compute reliability curve, ECE, and MCE calibration diagnostics."""
    if len(y_true) != len(y_prob):
        raise ValueError("y_true and y_prob must have identical length")
    if not y_true:
        raise ValueError("Cannot compute calibration diagnostics on empty sequences")
    if n_bins <= 0:
        raise ValueError("n_bins must be positive")

    total_samples = Decimal(len(y_true))
    bin_width = Decimal(1) / Decimal(n_bins)
    bins: list[CalibrationBinResult] = []
    ece = Decimal(0)
    mce = Decimal(0)

    for b in range(n_bins):
        lower = Decimal(b) * bin_width
        upper = Decimal(b + 1) * bin_width
        bin_preds: list[Decimal] = []
        bin_trues: list[Decimal] = []

        for yt, yp in zip(y_true, y_prob, strict=True):
            if b == n_bins - 1:
                in_bin = lower <= yp <= upper
            else:
                in_bin = lower <= yp < upper

            if in_bin:
                bin_preds.append(yp)
                bin_trues.append(Decimal(yt))

        count = len(bin_preds)
        if count > 0:
            mean_pred = apply_numeric_policy(sum(bin_preds, Decimal(0)) / Decimal(count), policy)
            obs_freq = apply_numeric_policy(sum(bin_trues, Decimal(0)) / Decimal(count), policy)
            gap = abs(mean_pred - obs_freq)
            weight = Decimal(count) / total_samples
            ece += weight * gap
            if gap > mce:
                mce = gap
        else:
            mean_pred = Decimal(0)
            obs_freq = Decimal(0)

        bins.append(
            CalibrationBinResult(
                bin_index=b,
                lower_bound=apply_numeric_policy(lower, policy),
                upper_bound=apply_numeric_policy(upper, policy),
                sample_count=count,
                mean_predicted=mean_pred,
                observed_frequency=obs_freq,
            )
        )

    return CalibrationDiagnostics(
        ece=apply_numeric_policy(ece, policy),
        mce=apply_numeric_policy(mce, policy),
        bins=tuple(bins),
    )


def compute_continuous_metrics(
    y_true: Sequence[Decimal],
    y_pred: Sequence[Decimal],
    policy: NumericPolicy,
) -> ContinuousMetricsReport:
    """Compute MAE, MSE, RMSE, Mean Bias, and R² for continuous targets."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have identical length")
    if not y_true:
        raise ValueError("Cannot compute continuous metrics on empty sequences")

    n = Decimal(len(y_true))
    abs_errors = [abs(yt - yp) for yt, yp in zip(y_true, y_pred, strict=True)]
    sq_errors = [(yt - yp) * (yt - yp) for yt, yp in zip(y_true, y_pred, strict=True)]
    bias_errors = [yp - yt for yt, yp in zip(y_true, y_pred, strict=True)]

    with localcontext(policy.get_context()):
        mae = sum(abs_errors, Decimal(0)) / n
        mse = sum(sq_errors, Decimal(0)) / n
        rmse = mse.sqrt()
        mean_bias = sum(bias_errors, Decimal(0)) / n

        mean_true = sum(y_true, Decimal(0)) / n
        ss_tot = sum(((yt - mean_true) * (yt - mean_true) for yt in y_true), Decimal(0))
        ss_res = sum(sq_errors, Decimal(0))

        if ss_tot == Decimal(0):
            r2: Decimal | None = None
        else:
            r2_val = Decimal(1) - (ss_res / ss_tot)
            r2 = +r2_val

    return ContinuousMetricsReport(
        mae=+mae,
        mse=+mse,
        rmse=+rmse,
        mean_bias=+mean_bias,
        r2_score=r2,
        sample_count=len(y_true),
    )

