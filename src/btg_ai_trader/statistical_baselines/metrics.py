"""Deterministic Decimal-based quantitative and statistical metrics."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from decimal import Decimal
from typing import Any


def _validate_lengths(
    predictions: Sequence[Any], targets: Sequence[Any], pred_name: str = "predictions"
) -> int:
    n_preds = len(predictions)
    n_targets = len(targets)
    if n_preds == 0:
        raise ValueError("Cannot compute metric on empty sequence")
    if n_preds != n_targets:
        raise ValueError(
            f"Length mismatch: {pred_name} has {n_preds} elements, "
            f"targets has {n_targets} elements"
        )
    return n_preds


def mean_absolute_error(
    predictions: Sequence[Decimal], targets: Sequence[Decimal]
) -> Decimal:
    """Compute Mean Absolute Error (MAE) using Decimal arithmetic."""
    n = _validate_lengths(predictions, targets)
    total = sum((abs(p - t) for p, t in zip(predictions, targets, strict=False)), Decimal(0))
    return total / Decimal(n)


def mean_squared_error(
    predictions: Sequence[Decimal], targets: Sequence[Decimal]
) -> Decimal:
    """Compute Mean Squared Error (MSE) using Decimal arithmetic."""
    n = _validate_lengths(predictions, targets)
    total = sum(((p - t) ** 2 for p, t in zip(predictions, targets, strict=False)), Decimal(0))
    return total / Decimal(n)


def root_mean_squared_error(
    predictions: Sequence[Decimal], targets: Sequence[Decimal]
) -> Decimal:
    """Compute Root Mean Squared Error (RMSE) using Decimal square root."""
    mse = mean_squared_error(predictions, targets)
    return mse.sqrt()


def mean_bias(
    predictions: Sequence[Decimal], targets: Sequence[Decimal]
) -> Decimal:
    """Compute Mean Bias (mean error = mean(predictions - targets))."""
    n = _validate_lengths(predictions, targets)
    total = sum((p - t for p, t in zip(predictions, targets, strict=False)), Decimal(0))
    return total / Decimal(n)


def brier_score(
    probabilities: Sequence[Decimal], targets: Sequence[Decimal]
) -> Decimal:
    """Compute Brier Score for probability forecasts against binary targets in {0, 1}."""
    n = _validate_lengths(probabilities, targets, pred_name="probabilities")
    for p in probabilities:
        if not (Decimal(0) <= p <= Decimal(1)):
            raise ValueError(f"Probabilities must be in [0, 1], got {p}")
    for t in targets:
        if t not in (Decimal(0), Decimal(1)):
            raise ValueError(f"Binary targets must be 0 or 1, got {t}")

    total = sum(((p - t) ** 2 for p, t in zip(probabilities, targets, strict=False)), Decimal(0))
    return total / Decimal(n)


def base_rate(targets: Sequence[Decimal]) -> Decimal:
    """Compute empirical base rate P(Y=1) for binary targets."""
    if len(targets) == 0:
        raise ValueError("Cannot compute base rate on empty sequence")
    for t in targets:
        if t not in (Decimal(0), Decimal(1)):
            raise ValueError(f"Binary targets must be 0 or 1, got {t}")
    return sum(targets, Decimal(0)) / Decimal(len(targets))


def accuracy_score(
    predictions: Sequence[str], targets: Sequence[str]
) -> Decimal:
    """Compute categorical accuracy score."""
    n = _validate_lengths(predictions, targets)
    correct = sum((1 for p, t in zip(predictions, targets, strict=False) if p == t), 0)
    return Decimal(correct) / Decimal(n)


def class_prevalence(targets: Sequence[str]) -> dict[str, Decimal]:
    """Compute prevalence (relative frequency) of each class in targets."""
    n = len(targets)
    if n == 0:
        raise ValueError("Cannot compute class prevalence on empty sequence")
    counts = Counter(targets)
    return {k: Decimal(v) / Decimal(n) for k, v in sorted(counts.items())}


def confusion_matrix_counts(
    predictions: Sequence[str],
    targets: Sequence[str],
    labels: Sequence[str] | None = None,
) -> dict[tuple[str, str], int]:
    """Compute confusion matrix counts mapping (target_class, predicted_class) -> count."""
    _validate_lengths(predictions, targets)
    if labels is None:
        unique_labels = sorted(set(predictions) | set(targets))
    else:
        unique_labels = list(labels)

    matrix: dict[tuple[str, str], int] = {
        (t_lbl, p_lbl): 0 for t_lbl in unique_labels for p_lbl in unique_labels
    }
    for p, t in zip(predictions, targets, strict=False):
        key = (t, p)
        if key in matrix:
            matrix[key] += 1
        else:
            matrix[key] = 1
    return matrix
