"""Unit tests for probability calibration diagnostics and reliability metrics."""

from decimal import Decimal

import pytest

from btg_ai_trader.statistical_baselines.calibration import (
    CalibrationBin,
    CalibrationReport,
    compute_calibration,
)


def test_calibration_bin_validation() -> None:
    with pytest.raises(ValueError, match="bin_index cannot be negative"):
        CalibrationBin(
            bin_index=-1,
            bin_lower=Decimal("0.0"),
            bin_upper=Decimal("0.1"),
            sample_count=10,
            mean_predicted_probability=Decimal("0.05"),
            observed_frequency=Decimal("0.1"),
        )

    with pytest.raises(ValueError, match="Bin bounds must be within"):
        CalibrationBin(
            bin_index=0,
            bin_lower=Decimal("-0.1"),
            bin_upper=Decimal("0.1"),
            sample_count=10,
            mean_predicted_probability=Decimal("0.05"),
            observed_frequency=Decimal("0.1"),
        )

    with pytest.raises(ValueError, match="cannot be greater than bin_upper"):
        CalibrationBin(
            bin_index=0,
            bin_lower=Decimal("0.5"),
            bin_upper=Decimal("0.2"),
            sample_count=10,
            mean_predicted_probability=Decimal("0.05"),
            observed_frequency=Decimal("0.1"),
        )

    with pytest.raises(ValueError, match="sample_count cannot be negative"):
        CalibrationBin(
            bin_index=0,
            bin_lower=Decimal("0.0"),
            bin_upper=Decimal("0.1"),
            sample_count=-5,
            mean_predicted_probability=Decimal("0.05"),
            observed_frequency=Decimal("0.1"),
        )


def test_calibration_report_validation() -> None:
    with pytest.raises(ValueError, match="num_bins must be positive"):
        CalibrationReport(
            bins=(),
            num_bins=0,
            expected_calibration_error=Decimal("0.0"),
            maximum_calibration_error=Decimal("0.0"),
        )

    with pytest.raises(ValueError, match="expected_calibration_error must be in"):
        CalibrationReport(
            bins=(),
            num_bins=5,
            expected_calibration_error=Decimal("1.5"),
            maximum_calibration_error=Decimal("0.0"),
        )

    with pytest.raises(ValueError, match="maximum_calibration_error must be in"):
        CalibrationReport(
            bins=(),
            num_bins=5,
            expected_calibration_error=Decimal("0.1"),
            maximum_calibration_error=Decimal("-0.1"),
        )


def test_compute_calibration_validation_errors() -> None:
    with pytest.raises(ValueError, match="num_bins must be positive"):
        compute_calibration([Decimal("0.5")], [Decimal("1")], num_bins=0)

    with pytest.raises(ValueError, match="empty sequence"):
        compute_calibration([], [], num_bins=5)

    with pytest.raises(ValueError, match="Length mismatch"):
        compute_calibration([Decimal("0.5")], [], num_bins=5)

    with pytest.raises(ValueError, match="must be in"):
        compute_calibration([Decimal("1.2")], [Decimal("1")], num_bins=5)

    with pytest.raises(ValueError, match="Targets must be binary"):
        compute_calibration([Decimal("0.5")], [Decimal("2")], num_bins=5)


def test_compute_calibration_perfect() -> None:
    probs = [Decimal("0.0"), Decimal("1.0")]
    targs = [Decimal("0"), Decimal("1")]

    report = compute_calibration(probs, targs, num_bins=2)
    assert report.num_bins == 2
    assert len(report.bins) == 2
    assert report.expected_calibration_error == Decimal("0")
    assert report.maximum_calibration_error == Decimal("0")

    bin0 = report.bins[0]
    assert bin0.sample_count == 1
    assert bin0.mean_predicted_probability == Decimal("0")
    assert bin0.observed_frequency == Decimal("0")

    bin1 = report.bins[1]
    assert bin1.sample_count == 1
    assert bin1.mean_predicted_probability == Decimal("1")
    assert bin1.observed_frequency == Decimal("1")


def test_compute_calibration_with_empty_bins() -> None:
    # All samples in bin 0
    probs = [Decimal("0.05"), Decimal("0.08")]
    targs = [Decimal("1"), Decimal("0")]

    report = compute_calibration(probs, targs, num_bins=5)
    assert report.num_bins == 5
    # Bin 0 has 2 samples; Bins 1, 2, 3, 4 are empty
    assert report.bins[0].sample_count == 2
    assert report.bins[1].sample_count == 0
    assert report.bins[1].mean_predicted_probability is None
    assert report.bins[1].observed_frequency is None
