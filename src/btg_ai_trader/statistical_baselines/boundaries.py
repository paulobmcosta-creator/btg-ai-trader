"""Immutable evaluation boundary abstractions, temporal folds, and walk-forward plans."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from btg_ai_trader.statistical_baselines.domain import (
    StatisticalSample,
    _validate_timezone_aware,
)


@dataclass(frozen=True, slots=True)
class EvaluationBoundary:
    """Explicit, immutable evaluation boundary with endpoint inclusion semantics."""

    start_time: datetime
    end_time: datetime
    knowledge_cutoff: datetime
    start_inclusive: bool = True
    end_inclusive: bool = False

    def __post_init__(self) -> None:
        _validate_timezone_aware(self.start_time, "start_time")
        _validate_timezone_aware(self.end_time, "end_time")
        _validate_timezone_aware(self.knowledge_cutoff, "knowledge_cutoff")

        if self.start_time >= self.end_time:
            raise ValueError(
                f"start_time ({self.start_time}) must be earlier than end_time ({self.end_time})"
            )

        if self.knowledge_cutoff > self.start_time:
            raise ValueError(
                f"knowledge_cutoff ({self.knowledge_cutoff}) cannot be after start "
                f"({self.start_time})"
            )

    def contains_timestamp(self, t: datetime) -> bool:
        """Check whether timestamp falls within boundary."""
        _validate_timezone_aware(t, "t")
        left_ok = self.start_time <= t if self.start_inclusive else self.start_time < t
        right_ok = t <= self.end_time if self.end_inclusive else t < self.end_time
        return left_ok and right_ok

    def contains_sample(self, sample: StatisticalSample, by_feature_time: bool = True) -> bool:
        """Check whether sample falls within boundary based on feature or target knowledge time."""
        t = sample.feature_knowledge_time if by_feature_time else sample.target_knowledge_time
        return self.contains_timestamp(t)


@dataclass(frozen=True, slots=True)
class TemporalFold:
    """Single walk-forward fold with strict causal boundaries between train and test."""

    fold_id: str
    development_boundary: EvaluationBoundary
    training_boundary: EvaluationBoundary
    protected_evaluation_boundary: EvaluationBoundary
    knowledge_cutoff: datetime
    window_policy_name: str
    validation_boundary: EvaluationBoundary | None = None
    purge_interval: tuple[datetime, datetime] | None = None
    embargo_interval: tuple[datetime, datetime] | None = None

    def __post_init__(self) -> None:
        if not self.fold_id or not isinstance(self.fold_id, str):
            raise ValueError("fold_id must be a non-empty string")
        if not self.window_policy_name:
            raise ValueError("window_policy_name must be a non-empty string")

        _validate_timezone_aware(self.knowledge_cutoff, "knowledge_cutoff")

        # Causal sequence: training precedes protected evaluation
        train_end = self.training_boundary.end_time
        eval_start = self.protected_evaluation_boundary.start_time
        if train_end > eval_start:
            raise ValueError(
                f"training_boundary end_time ({train_end}) cannot be later than "
                f"protected_evaluation_boundary start_time ({eval_start})"
            )

        # Validation, if present, must lie between training and protected evaluation
        if self.validation_boundary is not None:
            val_start = self.validation_boundary.start_time
            val_end = self.validation_boundary.end_time
            if train_end > val_start:
                raise ValueError(
                    f"training_boundary end_time ({train_end}) cannot be later than "
                    f"validation_boundary start_time ({val_start})"
                )
            if val_end > eval_start:
                raise ValueError(
                    f"validation_boundary end_time ({val_end}) cannot be later than "
                    f"protected_evaluation_boundary start_time ({eval_start})"
                )

        if self.purge_interval is not None:
            p_start, p_end = self.purge_interval
            _validate_timezone_aware(p_start, "purge_interval.start")
            _validate_timezone_aware(p_end, "purge_interval.end")
            if p_start > p_end:
                raise ValueError(f"purge_interval start ({p_start}) cannot be after end ({p_end})")

        if self.embargo_interval is not None:
            e_start, e_end = self.embargo_interval
            _validate_timezone_aware(e_start, "embargo_interval.start")
            _validate_timezone_aware(e_end, "embargo_interval.end")
            if e_start > e_end:
                raise ValueError(
                    f"embargo_interval start ({e_start}) cannot be after end ({e_end})"
                )


@dataclass(frozen=True, slots=True)
class WalkForwardPlan:
    """Ordered sequence of temporal folds defining an evaluation plan."""

    plan_id: str
    window_policy_name: str
    folds: tuple[TemporalFold, ...]

    def __post_init__(self) -> None:
        if not self.plan_id or not isinstance(self.plan_id, str):
            raise ValueError("plan_id must be a non-empty string")
        if not self.window_policy_name:
            raise ValueError("window_policy_name must be a non-empty string")
        if not self.folds:
            raise ValueError("WalkForwardPlan must contain at least one fold")

        fold_ids = set()
        for i, fold in enumerate(self.folds):
            if fold.fold_id in fold_ids:
                raise ValueError(f"Duplicate fold_id found: {fold.fold_id}")
            fold_ids.add(fold.fold_id)

            if i > 0:
                prev_fold = self.folds[i - 1]
                cur_start = fold.protected_evaluation_boundary.start_time
                prev_start = prev_fold.protected_evaluation_boundary.start_time
                if cur_start < prev_start:
                    raise ValueError(
                        f"Folds must be in chronological order: fold {fold.fold_id} has start "
                        f"{cur_start} < previous fold start {prev_start}"
                    )
