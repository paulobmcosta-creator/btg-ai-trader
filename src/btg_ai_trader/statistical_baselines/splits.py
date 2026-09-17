"""Walk-forward splitting, rolling/expanding policies, purging and embargo logic."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from btg_ai_trader.statistical_baselines.boundaries import (
    EvaluationBoundary,
    TemporalFold,
    WalkForwardPlan,
)
from btg_ai_trader.statistical_baselines.domain import (
    StatisticalSample,
    _validate_timezone_aware,
)


class WindowPolicy(str, Enum):
    """Temporal window expansion policy."""

    EXPANDING = "EXPANDING"
    ROLLING = "ROLLING"


@dataclass(frozen=True, slots=True)
class PurgePolicy:
    """Purging policy to remove samples whose information interval crosses evaluation boundaries."""

    purge_overlapping: bool = True
    default_horizon: timedelta | None = None
    fail_closed_on_unknown: bool = False

    def __post_init__(self) -> None:
        if self.default_horizon is not None and self.default_horizon < timedelta(0):
            raise ValueError(f"default_horizon cannot be negative, got {self.default_horizon}")

    def should_purge(self, sample: StatisticalSample, eval_start_time: datetime) -> bool:
        """Determine whether training sample has information overlapping evaluation boundary."""
        if not self.purge_overlapping:
            return False

        _validate_timezone_aware(eval_start_time, "eval_start_time")

        # Direct target availability crossing evaluation start
        if sample.target_knowledge_time > eval_start_time:
            return True

        # Information interval crossing evaluation start
        if sample.information_interval is not None:
            _, info_end = sample.information_interval
            return info_end > eval_start_time
        if self.default_horizon is not None:
            effective_end = sample.feature_knowledge_time + self.default_horizon
            return effective_end > eval_start_time

        # Fail-closed on unknown horizon / information interval
        if self.fail_closed_on_unknown:
            return True

        return False


@dataclass(frozen=True, slots=True)
class EmbargoPolicy:
    """Embargo policy specifying a safety buffer immediately following training."""

    duration: timedelta

    def __post_init__(self) -> None:
        if self.duration < timedelta(0):
            raise ValueError(f"Embargo duration cannot be negative, got {self.duration}")

    def is_in_embargo(self, t: datetime, train_end_time: datetime) -> bool:
        """Check whether timestamp falls within the post-training embargo interval."""
        if self.duration == timedelta(0):
            return False
        _validate_timezone_aware(t, "t")
        _validate_timezone_aware(train_end_time, "train_end_time")
        return train_end_time <= t < (train_end_time + self.duration)


@dataclass(frozen=True, slots=True)
class SplitPlanConfig:
    """Configuration for generating walk-forward evaluation plans."""

    window_policy: WindowPolicy
    train_duration: timedelta
    test_duration: timedelta
    step_duration: timedelta
    purge_policy: PurgePolicy
    embargo_policy: EmbargoPolicy
    validation_duration: timedelta | None = None

    def __post_init__(self) -> None:
        if self.train_duration <= timedelta(0):
            raise ValueError("train_duration must be positive")
        if self.test_duration <= timedelta(0):
            raise ValueError("test_duration must be positive")
        if self.step_duration <= timedelta(0):
            raise ValueError("step_duration must be positive")
        if self.validation_duration is not None and self.validation_duration <= timedelta(0):
            raise ValueError("validation_duration must be positive when specified")
        if self.purge_policy is None:
            raise ValueError("purge_policy is required")
        if self.embargo_policy is None:
            raise ValueError("embargo_policy is required")


class WalkForwardPlanner:
    """Planner creating causal walk-forward folds and partitioning samples."""

    @staticmethod
    def forbid_random_shuffle(*args: object, **kwargs: object) -> None:
        """Explicitly block random shuffle cross-validation per Protocol 0E-C (C-HQI-08)."""
        raise ValueError(
            "Random shuffle cross-validation is forbidden for prospective causal validation "
            "(Protocol 0E-C, C-HQI-08, S4-NC-17)"
        )

    @classmethod
    def generate_plan(
        cls,
        start_time: datetime,
        end_time: datetime,
        config: SplitPlanConfig,
        plan_id: str,
    ) -> WalkForwardPlan:
        """Generate a causal walk-forward plan from start_time to end_time."""
        _validate_timezone_aware(start_time, "start_time")
        _validate_timezone_aware(end_time, "end_time")

        if start_time >= end_time:
            raise ValueError(
                f"start_time ({start_time}) must be earlier than end_time ({end_time})"
            )

        folds: list[TemporalFold] = []
        fold_idx = 1
        current_train_start = start_time

        val_dur = config.validation_duration or timedelta(0)
        min_span = config.train_duration + val_dur + config.test_duration
        if (end_time - start_time) < min_span:
            raise ValueError(
                f"Total time span ({end_time - start_time}) is smaller than minimum required "
                f"fold span ({min_span})"
            )

        while True:
            if config.window_policy is WindowPolicy.EXPANDING:
                train_start = start_time
            else:
                train_start = current_train_start
            train_end = current_train_start + config.train_duration

            if config.validation_duration is not None:
                val_start = train_end
                val_end = val_start + config.validation_duration
                eval_start = val_end
            else:
                val_start = None
                val_end = None
                eval_start = train_end

            eval_end = eval_start + config.test_duration

            if eval_end > end_time:
                break

            knowledge_cutoff = train_end
            dev_boundary = EvaluationBoundary(
                start_time=train_start,
                end_time=eval_end,
                knowledge_cutoff=start_time,
                start_inclusive=True,
                end_inclusive=False,
            )
            train_boundary = EvaluationBoundary(
                start_time=train_start,
                end_time=train_end,
                knowledge_cutoff=start_time,
                start_inclusive=True,
                end_inclusive=False,
            )

            val_boundary = None
            if val_start is not None and val_end is not None:
                val_boundary = EvaluationBoundary(
                    start_time=val_start,
                    end_time=val_end,
                    knowledge_cutoff=train_end,
                    start_inclusive=True,
                    end_inclusive=False,
                )

            eval_boundary = EvaluationBoundary(
                start_time=eval_start,
                end_time=eval_end,
                knowledge_cutoff=train_end if val_boundary is None else val_boundary.end_time,
                start_inclusive=True,
                end_inclusive=False,
            )

            embargo_int = None
            if config.embargo_policy.duration > timedelta(0):
                embargo_int = (train_end, train_end + config.embargo_policy.duration)

            fold = TemporalFold(
                fold_id=f"fold_{fold_idx:03d}",
                development_boundary=dev_boundary,
                training_boundary=train_boundary,
                validation_boundary=val_boundary,
                protected_evaluation_boundary=eval_boundary,
                knowledge_cutoff=knowledge_cutoff,
                window_policy_name=config.window_policy.value,
                embargo_interval=embargo_int,
            )
            folds.append(fold)
            fold_idx += 1
            current_train_start += config.step_duration

        return WalkForwardPlan(
            plan_id=plan_id,
            window_policy_name=config.window_policy.value,
            folds=tuple(folds),
            train_duration=config.train_duration,
            test_duration=config.test_duration,
            step_duration=config.step_duration,
            validation_duration=config.validation_duration,
            purge_policy=config.purge_policy,
            embargo_policy=config.embargo_policy,
            window_policy=config.window_policy,
        )

    @classmethod
    def partition_samples(
        cls,
        samples: Sequence[StatisticalSample],
        fold: TemporalFold,
        purge_policy: PurgePolicy,
        embargo_policy: EmbargoPolicy,
    ) -> tuple[
        tuple[StatisticalSample, ...],
        tuple[StatisticalSample, ...] | None,
        tuple[StatisticalSample, ...],
    ]:
        """Partition samples into train, validation, and protected evaluation sets for a fold."""
        # Enforce unique sample_ids
        seen_ids: set[str] = set()
        for s in samples:
            if s.sample_id in seen_ids:
                raise ValueError(f"Duplicate sample_id encountered: {s.sample_id}")
            seen_ids.add(s.sample_id)

        train_samples: list[StatisticalSample] = []
        val_samples: list[StatisticalSample] = []
        eval_samples: list[StatisticalSample] = []

        eval_start = fold.protected_evaluation_boundary.start_time

        for s in samples:
            # Check training admissibility
            if fold.training_boundary.contains_sample(s, by_feature_time=True):
                # Must be causally admissible at knowledge cutoff
                if not s.is_causally_admissible_for_fit(fold.knowledge_cutoff):
                    continue
                # Purge check
                if purge_policy.should_purge(s, eval_start):
                    continue
                train_samples.append(s)

            # Check validation admissibility
            elif fold.validation_boundary is not None and fold.validation_boundary.contains_sample(
                s, by_feature_time=True
            ):
                if not embargo_policy.is_in_embargo(
                    s.feature_knowledge_time, fold.training_boundary.end_time
                ):
                    val_samples.append(s)

            # Check protected evaluation admissibility
            elif fold.protected_evaluation_boundary.contains_sample(s, by_feature_time=True):
                if not embargo_policy.is_in_embargo(
                    s.feature_knowledge_time, fold.training_boundary.end_time
                ):
                    eval_samples.append(s)

        return (
            tuple(train_samples),
            tuple(val_samples) if fold.validation_boundary is not None else None,
            tuple(eval_samples),
        )
