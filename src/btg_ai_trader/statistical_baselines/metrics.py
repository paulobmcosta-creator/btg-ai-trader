"""Deterministic Decimal-based quantitative and statistical metrics."""

from __future__ import annotations

import decimal
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from typing import Any


@dataclass(frozen=True, slots=True)
class NumericPolicy:
    """Explicit decimal arithmetic policy defining precision, rounding, and serialization."""

    precision: int = 28
    rounding_mode: str = "ROUND_HALF_EVEN"
    serialization_mode: str = "CANONICAL_STRING"

    def __post_init__(self) -> None:
        if self.precision <= 0:
            raise ValueError(f"precision must be positive, got {self.precision}")
        valid_roundings = {
            "ROUND_CEILING",
            "ROUND_DOWN",
            "ROUND_FLOOR",
            "ROUND_HALF_DOWN",
            "ROUND_HALF_EVEN",
            "ROUND_HALF_UP",
            "ROUND_UP",
            "ROUND_05UP",
        }
        if self.rounding_mode not in valid_roundings:
            raise ValueError(
                f"Invalid rounding_mode: {self.rounding_mode}. "
                f"Must be one of {sorted(valid_roundings)}"
            )

    def get_context(self) -> Context:
        """Create a decimal.Context matching this policy."""
        return Context(
            prec=self.precision,
            rounding=getattr(decimal, self.rounding_mode),
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        """Convert policy to canonical serializable dictionary."""
        return {
            "precision": self.precision,
            "rounding_mode": self.rounding_mode,
            "serialization_mode": self.serialization_mode,
        }


DEFAULT_NUMERIC_POLICY = NumericPolicy()


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
    predictions: Sequence[Decimal],
    targets: Sequence[Decimal],
    policy: NumericPolicy = DEFAULT_NUMERIC_POLICY,
) -> Decimal:
    """Compute Mean Absolute Error (MAE) using Decimal arithmetic."""
    with localcontext(policy.get_context()):
        n = _validate_lengths(predictions, targets)
        total = sum((abs(p - t) for p, t in zip(predictions, targets, strict=False)), Decimal(0))
        return total / Decimal(n)


def mean_squared_error(
    predictions: Sequence[Decimal],
    targets: Sequence[Decimal],
    policy: NumericPolicy = DEFAULT_NUMERIC_POLICY,
) -> Decimal:
    """Compute Mean Squared Error (MSE) using Decimal arithmetic."""
    with localcontext(policy.get_context()):
        n = _validate_lengths(predictions, targets)
        total = sum(((p - t) ** 2 for p, t in zip(predictions, targets, strict=False)), Decimal(0))
        return total / Decimal(n)


def root_mean_squared_error(
    predictions: Sequence[Decimal],
    targets: Sequence[Decimal],
    policy: NumericPolicy = DEFAULT_NUMERIC_POLICY,
) -> Decimal:
    """Compute Root Mean Squared Error (RMSE) using Decimal square root."""
    with localcontext(policy.get_context()):
        mse = mean_squared_error(predictions, targets, policy=policy)
        return mse.sqrt()


def mean_bias(
    predictions: Sequence[Decimal],
    targets: Sequence[Decimal],
    policy: NumericPolicy = DEFAULT_NUMERIC_POLICY,
) -> Decimal:
    """Compute Mean Bias (mean error = mean(predictions - targets))."""
    with localcontext(policy.get_context()):
        n = _validate_lengths(predictions, targets)
        total = sum((p - t for p, t in zip(predictions, targets, strict=False)), Decimal(0))
        return total / Decimal(n)


def compute_continuous_metrics(
    predictions: Sequence[Decimal],
    targets: Sequence[Decimal],
    policy: NumericPolicy = DEFAULT_NUMERIC_POLICY,
) -> dict[str, Decimal]:
    """Compute full set of continuous prediction metrics under explicit NumericPolicy."""
    with localcontext(policy.get_context()):
        return {
            "mae": mean_absolute_error(predictions, targets, policy=policy),
            "mse": mean_squared_error(predictions, targets, policy=policy),
            "rmse": root_mean_squared_error(predictions, targets, policy=policy),
            "mean_bias": mean_bias(predictions, targets, policy=policy),
        }


def brier_score(
    probabilities: Sequence[Decimal],
    targets: Sequence[Decimal],
    policy: NumericPolicy = DEFAULT_NUMERIC_POLICY,
) -> Decimal:
    """Compute Brier Score for probability forecasts against binary targets in {0, 1}."""
    with localcontext(policy.get_context()):
        n = _validate_lengths(probabilities, targets, pred_name="probabilities")
        for p in probabilities:
            if not (Decimal(0) <= p <= Decimal(1)):
                raise ValueError(f"Probabilities must be in [0, 1], got {p}")
        for t in targets:
            if t not in (Decimal(0), Decimal(1)):
                raise ValueError(f"Binary targets must be 0 or 1, got {t}")

        total = sum(
            ((p - t) ** 2 for p, t in zip(probabilities, targets, strict=False)),
            Decimal(0),
        )
        return total / Decimal(n)


def base_rate(
    targets: Sequence[Decimal],
    policy: NumericPolicy = DEFAULT_NUMERIC_POLICY,
) -> Decimal:
    """Compute empirical base rate P(Y=1) for binary targets."""
    with localcontext(policy.get_context()):
        if len(targets) == 0:
            raise ValueError("Cannot compute base rate on empty sequence")
        for t in targets:
            if t not in (Decimal(0), Decimal(1)):
                raise ValueError(f"Binary targets must be 0 or 1, got {t}")
        return sum(targets, Decimal(0)) / Decimal(len(targets))


def accuracy_score(
    predictions: Sequence[str],
    targets: Sequence[str],
    policy: NumericPolicy = DEFAULT_NUMERIC_POLICY,
) -> Decimal:
    """Compute categorical accuracy score."""
    with localcontext(policy.get_context()):
        n = _validate_lengths(predictions, targets)
        correct = sum((1 for p, t in zip(predictions, targets, strict=False) if p == t), 0)
        return Decimal(correct) / Decimal(n)


def class_prevalence(
    targets: Sequence[str],
    policy: NumericPolicy = DEFAULT_NUMERIC_POLICY,
) -> dict[str, Decimal]:
    """Compute prevalence (relative frequency) of each class in targets."""
    with localcontext(policy.get_context()):
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
