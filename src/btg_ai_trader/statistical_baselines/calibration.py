"""Calibration diagnostics, reliability diagram metrics (ECE, MCE)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CalibrationBin:
    """Diagnostic metrics for a single probability calibration bin."""

    bin_index: int
    bin_lower: Decimal
    bin_upper: Decimal
    sample_count: int
    mean_predicted_probability: Decimal | None
    observed_frequency: Decimal | None

    def __post_init__(self) -> None:
        if self.bin_index < 0:
            raise ValueError(f"bin_index cannot be negative, got {self.bin_index}")
        if self.bin_lower < Decimal(0) or self.bin_upper > Decimal(1):
            raise ValueError(
                f"Bin bounds must be within [0, 1], got [{self.bin_lower}, {self.bin_upper}]"
            )
        if self.bin_lower > self.bin_upper:
            raise ValueError(
                f"bin_lower ({self.bin_lower}) cannot be greater than bin_upper ({self.bin_upper})"
            )
        if self.sample_count < 0:
            raise ValueError(f"sample_count cannot be negative, got {self.sample_count}")


@dataclass(frozen=True, slots=True)
class CalibrationReport:
    """Full calibration report containing bin details, ECE, and MCE."""

    bins: tuple[CalibrationBin, ...]
    num_bins: int
    expected_calibration_error: Decimal
    maximum_calibration_error: Decimal

    def __post_init__(self) -> None:
        if self.num_bins <= 0:
            raise ValueError(f"num_bins must be positive, got {self.num_bins}")
        if not (Decimal(0) <= self.expected_calibration_error <= Decimal(1)):
            raise ValueError(
                f"expected_calibration_error must be in [0, 1], "
                f"got {self.expected_calibration_error}"
            )
        if not (Decimal(0) <= self.maximum_calibration_error <= Decimal(1)):
            raise ValueError(
                f"maximum_calibration_error must be in [0, 1], got {self.maximum_calibration_error}"
            )


def compute_calibration(
    probabilities: Sequence[Decimal],
    targets: Sequence[Decimal],
    num_bins: int = 10,
) -> CalibrationReport:
    """Compute calibration bins, ECE and MCE reliability metrics."""
    if num_bins <= 0:
        raise ValueError(f"num_bins must be positive, got {num_bins}")
    n = len(probabilities)
    if n == 0:
        raise ValueError("Cannot compute calibration on empty sequences")
    if len(targets) != n:
        raise ValueError(
            f"Length mismatch: probabilities has {n} items, targets has {len(targets)} items"
        )

    for p in probabilities:
        if not (Decimal(0) <= p <= Decimal(1)):
            raise ValueError(f"Probabilities must be in [0, 1], got {p}")
    for t in targets:
        if t not in (Decimal(0), Decimal(1)):
            raise ValueError(f"Targets must be binary (0 or 1), got {t}")

    step = Decimal(1) / Decimal(num_bins)
    total_n = Decimal(n)

    bins_list: list[CalibrationBin] = []
    ece = Decimal(0)
    mce = Decimal(0)

    for b in range(num_bins):
        lower = Decimal(b) * step
        upper = Decimal(b + 1) * step if b < num_bins - 1 else Decimal(1)

        # Collect points belonging to bin
        bin_probs: list[Decimal] = []
        bin_targets: list[Decimal] = []

        for p, t in zip(probabilities, targets, strict=False):
            if b == num_bins - 1:
                # Include upper bound in last bin
                if lower <= p <= upper:
                    bin_probs.append(p)
                    bin_targets.append(t)
            else:
                if lower <= p < upper:
                    bin_probs.append(p)
                    bin_targets.append(t)

        count = len(bin_probs)
        if count > 0:
            mean_prob = sum(bin_probs, Decimal(0)) / Decimal(count)
            obs_freq = sum(bin_targets, Decimal(0)) / Decimal(count)
            error = abs(mean_prob - obs_freq)
            ece += (Decimal(count) / total_n) * error
            if error > mce:
                mce = error
        else:
            mean_prob = None
            obs_freq = None

        cal_bin = CalibrationBin(
            bin_index=b,
            bin_lower=lower,
            bin_upper=upper,
            sample_count=count,
            mean_predicted_probability=mean_prob,
            observed_frequency=obs_freq,
        )
        bins_list.append(cal_bin)

    return CalibrationReport(
        bins=tuple(bins_list),
        num_bins=num_bins,
        expected_calibration_error=ece,
        maximum_calibration_error=mce,
    )
