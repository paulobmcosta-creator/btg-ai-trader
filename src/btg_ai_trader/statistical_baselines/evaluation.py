"""Temporal fold evaluation engine and aggregate metric calculation."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from btg_ai_trader.statistical_baselines.baselines import StatisticalBaseline
from btg_ai_trader.statistical_baselines.boundaries import (
    TemporalFold,
    WalkForwardPlan,
)
from btg_ai_trader.statistical_baselines.calibration import (
    CalibrationReport,
    compute_calibration,
)
from btg_ai_trader.statistical_baselines.domain import (
    EvaluationRole,
    PredictionResult,
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.metrics import (
    accuracy_score,
    base_rate,
    brier_score,
    mean_absolute_error,
    mean_bias,
    mean_squared_error,
    root_mean_squared_error,
)
from btg_ai_trader.statistical_baselines.splits import (
    EmbargoPolicy,
    PurgePolicy,
    WalkForwardPlanner,
)


@dataclass(frozen=True, slots=True)
class FoldEvaluationResult:
    """Evaluation metrics and diagnostics for a single candidate on a single temporal fold."""

    fold_id: str
    candidate_id: str
    evaluation_role: EvaluationRole
    metrics: Mapping[str, Decimal]
    sample_count: int
    cold_start_count: int
    calibration_report: CalibrationReport | None = None
    predictions: tuple[PredictionResult, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.sample_count < 0:
            raise ValueError(f"sample_count cannot be negative, got {self.sample_count}")
        if self.cold_start_count < 0 or self.cold_start_count > self.sample_count:
            raise ValueError(
                f"cold_start_count ({self.cold_start_count}) must be between 0 "
                f"and {self.sample_count}"
            )


@dataclass(frozen=True, slots=True)
class AggregateEvaluationResult:
    """Aggregated evaluation metrics across all folds of a walk-forward plan."""

    candidate_id: str
    evaluation_role: EvaluationRole
    fold_results: tuple[FoldEvaluationResult, ...]
    aggregate_metrics: Mapping[str, Decimal]
    total_samples: int
    total_cold_starts: int

    def __post_init__(self) -> None:
        if self.total_samples < 0:
            raise ValueError(f"total_samples cannot be negative, got {self.total_samples}")
        if self.total_cold_starts < 0 or self.total_cold_starts > self.total_samples:
            raise ValueError(
                f"total_cold_starts must be between 0 and total_samples, "
                f"got {self.total_cold_starts}"
            )


class StatisticalEvaluationEngine:
    """Engine executing prospective causal evaluations on temporal folds."""

    @classmethod
    def evaluate_candidate_on_fold(
        cls,
        baseline: StatisticalBaseline,
        fold: TemporalFold,
        train_samples: Sequence[StatisticalSample],
        eval_samples: Sequence[StatisticalSample],
        role: EvaluationRole,
    ) -> FoldEvaluationResult:
        """Evaluate a baseline candidate on a single fold, adhering to causal cutoff."""
        # Fit baseline model up to knowledge cutoff
        baseline.fit(train_samples, knowledge_cutoff=fold.knowledge_cutoff)

        if not eval_samples:
            return FoldEvaluationResult(
                fold_id=fold.fold_id,
                candidate_id=baseline.identity.candidate_id,
                evaluation_role=role,
                metrics={},
                sample_count=0,
                cold_start_count=0,
                predictions=(),
            )

        predictions: list[PredictionResult] = []
        cold_starts = 0
        for s in eval_samples:
            pred = baseline.predict(s)
            if pred.is_cold_start:
                cold_starts += 1
            predictions.append(pred)

        metrics: dict[str, Decimal] = {}
        cal_report: CalibrationReport | None = None
        target_sem = eval_samples[0].target_semantics

        # Continuous target evaluation
        if target_sem is TargetSemantics.CONTINUOUS:
            valid_pairs = [
                (p.predicted_value, s.target_value)
                for p, s in zip(predictions, eval_samples, strict=False)
                if p.predicted_value is not None and isinstance(s.target_value, Decimal)
            ]
            if valid_pairs:
                preds_val, targs_val = zip(*valid_pairs, strict=False)
                metrics["mae"] = mean_absolute_error(preds_val, targs_val)
                metrics["mse"] = mean_squared_error(preds_val, targs_val)
                metrics["rmse"] = root_mean_squared_error(preds_val, targs_val)
                metrics["mean_bias"] = mean_bias(preds_val, targs_val)

        # Binary probability target evaluation
        elif target_sem is TargetSemantics.BINARY_PROBABILITY:
            valid_prob_pairs = [
                (p.predicted_probability, s.target_value)
                for p, s in zip(predictions, eval_samples, strict=False)
                if p.predicted_probability is not None and isinstance(s.target_value, Decimal)
            ]
            if valid_prob_pairs:
                probs_val, targs_val = zip(*valid_prob_pairs, strict=False)
                metrics["brier_score"] = brier_score(probs_val, targs_val)
                metrics["base_rate"] = base_rate(targs_val)
                metrics["mae"] = mean_absolute_error(probs_val, targs_val)
                cal_report = compute_calibration(probs_val, targs_val)
                metrics["ece"] = cal_report.expected_calibration_error
                metrics["mce"] = cal_report.maximum_calibration_error

        # Categorical target evaluation
        else:
            valid_cat_pairs = [
                (p.predicted_class, str(s.target_value))
                for p, s in zip(predictions, eval_samples, strict=False)
                if p.predicted_class is not None
            ]
            if valid_cat_pairs:
                preds_cat, targs_cat = zip(*valid_cat_pairs, strict=False)
                metrics["accuracy"] = accuracy_score(preds_cat, targs_cat)

        return FoldEvaluationResult(
            fold_id=fold.fold_id,
            candidate_id=baseline.identity.candidate_id,
            evaluation_role=role,
            metrics=metrics,
            sample_count=len(eval_samples),
            cold_start_count=cold_starts,
            calibration_report=cal_report,
            predictions=tuple(predictions),
        )

    @classmethod
    def evaluate_candidate_on_plan(
        cls,
        baseline_factory: Callable[[], StatisticalBaseline],
        plan: WalkForwardPlan,
        samples: Sequence[StatisticalSample],
        role: EvaluationRole,
        purge_policy: PurgePolicy,
        embargo_policy: EmbargoPolicy,
    ) -> AggregateEvaluationResult:
        """Evaluate candidate across folds of walk-forward plan and compute aggregate metrics."""
        fold_results: list[FoldEvaluationResult] = []
        candidate_id: str | None = None

        for fold in plan.folds:
            train_set, val_set, eval_set = WalkForwardPlanner.partition_samples(
                samples, fold, purge_policy, embargo_policy
            )

            if role is EvaluationRole.VALIDATION_SELECTION:
                if val_set is None:
                    raise ValueError(
                        f"Cannot evaluate on VALIDATION_SELECTION: fold {fold.fold_id} "
                        f"has no validation boundary"
                    )
                target_eval_set = val_set
            else:
                target_eval_set = eval_set

            baseline_instance = baseline_factory()
            if candidate_id is None:
                candidate_id = baseline_instance.identity.candidate_id

            fold_res = cls.evaluate_candidate_on_fold(
                baseline=baseline_instance,
                fold=fold,
                train_samples=train_set,
                eval_samples=target_eval_set,
                role=role,
            )
            fold_results.append(fold_res)

        assert candidate_id is not None

        # Compute aggregate metrics (mean across folds having valid metrics)
        metric_sums: dict[str, Decimal] = {}
        metric_counts: dict[str, int] = {}
        tot_samples = 0
        tot_cold = 0

        for f_res in fold_results:
            tot_samples += f_res.sample_count
            tot_cold += f_res.cold_start_count
            for k, v in f_res.metrics.items():
                metric_sums[k] = metric_sums.get(k, Decimal(0)) + v
                metric_counts[k] = metric_counts.get(k, 0) + 1

        agg_metrics: dict[str, Decimal] = {
            f"mean_{k}": metric_sums[k] / Decimal(metric_counts[k])
            for k in sorted(metric_sums.keys())
            if metric_counts[k] > 0
        }

        return AggregateEvaluationResult(
            candidate_id=candidate_id,
            evaluation_role=role,
            fold_results=tuple(fold_results),
            aggregate_metrics=agg_metrics,
            total_samples=tot_samples,
            total_cold_starts=tot_cold,
        )
