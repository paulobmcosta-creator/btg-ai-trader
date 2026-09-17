"""Temporal fold evaluation engine and aggregate metric calculation."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal, localcontext
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from btg_ai_trader.statistical_baselines.comparison import EvaluationHistory

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
    _freeze_mapping,
)
from btg_ai_trader.statistical_baselines.metrics import (
    DEFAULT_NUMERIC_POLICY,
    NumericPolicy,
    accuracy_score,
    base_rate,
    brier_score,
    mean_absolute_error,
    mean_bias,
    mean_squared_error,
    root_mean_squared_error,
)
from btg_ai_trader.statistical_baselines.splits import (
    WalkForwardPlanner,
)


class FoldAggregationPolicy(str, Enum):
    """Aggregation policy for computing summary metrics across temporal folds."""

    EQUAL_FOLD = "EQUAL_FOLD"
    SAMPLE_WEIGHTED = "SAMPLE_WEIGHTED"


@dataclass(frozen=True, slots=True)
class FoldStabilityDiagnostics:
    """Distributional and stability diagnostics across walk-forward folds."""

    metric_name: str
    min_value: Decimal
    max_value: Decimal
    median_value: Decimal
    dispersion: Decimal
    range_value: Decimal
    worst_fold_id: str
    best_fold_id: str
    sign_consistency: bool
    relative_degradation: Decimal
    has_stability_evidence: bool = True

    def to_canonical_dict(self) -> dict[str, Any]:
        """Convert stability diagnostics to canonical dictionary representation."""
        return {
            "metric_name": self.metric_name,
            "min_value": str(self.min_value),
            "max_value": str(self.max_value),
            "median_value": str(self.median_value),
            "dispersion": str(self.dispersion),
            "range_value": str(self.range_value),
            "worst_fold_id": self.worst_fold_id,
            "best_fold_id": self.best_fold_id,
            "sign_consistency": self.sign_consistency,
            "relative_degradation": str(self.relative_degradation),
            "has_stability_evidence": self.has_stability_evidence,
        }


@dataclass(frozen=True, slots=True)
class FoldEvaluationResult:
    """Evaluation metrics and diagnostics for a single candidate on a single temporal fold."""

    fold_id: str
    candidate_id: str
    evaluation_role: EvaluationRole
    metrics: Mapping[str, Decimal]
    sample_count: int
    cold_start_count: int
    metric_effective_counts: Mapping[str, int] = field(default_factory=dict)
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
        object.__setattr__(self, "metrics", _freeze_mapping(self.metrics))
        object.__setattr__(
            self, "metric_effective_counts", _freeze_mapping(self.metric_effective_counts)
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
    aggregation_policy: FoldAggregationPolicy = FoldAggregationPolicy.EQUAL_FOLD
    numeric_policy: NumericPolicy = DEFAULT_NUMERIC_POLICY
    per_fold_metrics: tuple[Mapping[str, Decimal], ...] = field(default_factory=tuple)
    fold_sample_counts: tuple[int, ...] = field(default_factory=tuple)
    metric_effective_counts: tuple[Mapping[str, int], ...] = field(default_factory=tuple)
    stability_diagnostics: Mapping[str, FoldStabilityDiagnostics] = field(default_factory=dict)
    target_contract_id: str = ""
    code_revision: str = ""
    evaluation_context_fingerprint: str = ""
    protected_evidence_records: tuple[Any, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.total_samples < 0:
            raise ValueError(f"total_samples cannot be negative, got {self.total_samples}")
        if self.total_cold_starts < 0 or self.total_cold_starts > self.total_samples:
            raise ValueError(
                f"total_cold_starts must be between 0 and total_samples, "
                f"got {self.total_cold_starts}"
            )
        object.__setattr__(self, "aggregate_metrics", _freeze_mapping(self.aggregate_metrics))
        object.__setattr__(
            self, "stability_diagnostics", _freeze_mapping(self.stability_diagnostics)
        )
        object.__setattr__(
            self, "protected_evidence_records", tuple(self.protected_evidence_records)
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
        numeric_policy: NumericPolicy = DEFAULT_NUMERIC_POLICY,
    ) -> FoldEvaluationResult:
        """Evaluate a baseline candidate on a single fold, adhering to causal cutoff."""
        with localcontext(numeric_policy.get_context()):
            # Fit baseline model up to knowledge cutoff
            baseline.fit(
                train_samples,
                knowledge_cutoff=fold.knowledge_cutoff,
                numeric_policy=numeric_policy,
            )

            if not eval_samples:
                return FoldEvaluationResult(
                    fold_id=fold.fold_id,
                    candidate_id=baseline.identity.candidate_id,
                    evaluation_role=role,
                    metrics={},
                    sample_count=0,
                    cold_start_count=0,
                    metric_effective_counts={},
                    predictions=(),
                )

            predictions: list[PredictionResult] = []
            cold_starts = 0
            for s in eval_samples:
                pred = baseline.predict(s.to_prediction_input())
                if pred.is_cold_start:
                    cold_starts += 1
                predictions.append(pred)

            metrics: dict[str, Decimal] = {}
            effective_counts: dict[str, int] = {}
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
                    n_eff = len(valid_pairs)
                    metrics["mae"] = mean_absolute_error(
                        preds_val, targs_val, policy=numeric_policy
                    )
                    metrics["mse"] = mean_squared_error(
                        preds_val, targs_val, policy=numeric_policy
                    )
                    metrics["rmse"] = root_mean_squared_error(
                        preds_val, targs_val, policy=numeric_policy
                    )
                    metrics["mean_bias"] = mean_bias(
                        preds_val, targs_val, policy=numeric_policy
                    )
                    for m in ("mae", "mse", "rmse", "mean_bias"):
                        effective_counts[m] = n_eff

            # Binary probability target evaluation
            elif target_sem is TargetSemantics.BINARY_PROBABILITY:
                valid_prob_pairs = [
                    (p.predicted_probability, s.target_value)
                    for p, s in zip(predictions, eval_samples, strict=False)
                    if p.predicted_probability is not None and isinstance(s.target_value, Decimal)
                ]
                if valid_prob_pairs:
                    probs_val, targs_val = zip(*valid_prob_pairs, strict=False)
                    n_eff = len(valid_prob_pairs)
                    metrics["brier_score"] = brier_score(
                        probs_val, targs_val, policy=numeric_policy
                    )
                    metrics["base_rate"] = base_rate(targs_val, policy=numeric_policy)
                    metrics["mae"] = mean_absolute_error(
                        probs_val, targs_val, policy=numeric_policy
                    )
                    cal_report = compute_calibration(
                        probs_val, targs_val, policy=numeric_policy
                    )
                    metrics["ece"] = cal_report.expected_calibration_error
                    metrics["mce"] = cal_report.maximum_calibration_error
                    for m in ("brier_score", "base_rate", "mae", "ece", "mce"):
                        effective_counts[m] = n_eff

            # Categorical target evaluation
            else:
                valid_cat_pairs = [
                    (p.predicted_class, str(s.target_value))
                    for p, s in zip(predictions, eval_samples, strict=False)
                    if p.predicted_class is not None
                ]
                if valid_cat_pairs:
                    preds_cat, targs_cat = zip(*valid_cat_pairs, strict=False)
                    n_eff = len(valid_cat_pairs)
                    metrics["accuracy"] = accuracy_score(
                        preds_cat, targs_cat, policy=numeric_policy
                    )
                    effective_counts["accuracy"] = n_eff

            return FoldEvaluationResult(
                fold_id=fold.fold_id,
                candidate_id=baseline.identity.candidate_id,
                evaluation_role=role,
                metrics=metrics,
                sample_count=len(eval_samples),
                cold_start_count=cold_starts,
                metric_effective_counts=effective_counts,
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
        aggregation_policy: FoldAggregationPolicy = FoldAggregationPolicy.EQUAL_FOLD,
        numeric_policy: NumericPolicy = DEFAULT_NUMERIC_POLICY,
        target_contract_id: str = "generic_target_contract_s4",
        code_revision: str | None = None,
        evaluation_history: EvaluationHistory | None = None,
        protected_boundary_id: str | None = None,
        parent_candidate_ids: Sequence[str] = (),
        informed_adaptation: bool = False,
    ) -> AggregateEvaluationResult:
        """Evaluate candidate across folds of walk-forward plan and compute aggregate metrics."""
        # Enforce evaluation role integrity: only VALIDATION_SELECTION and PROTECTED_TEST allowed
        if role not in (EvaluationRole.VALIDATION_SELECTION, EvaluationRole.PROTECTED_TEST):
            raise ValueError(
                f"evaluate_candidate_on_plan only accepts VALIDATION_SELECTION or "
                f"PROTECTED_TEST, got {role}. DEVELOPMENT and TRAINING_FIT cannot label "
                f"evaluation results (Protocol 0E-C, C-HQI-08, S4-NC-17)"
            )

        # Plan MUST be policy-bound; no implicit defaults or overrides allowed
        if plan.purge_policy is None:
            raise ValueError("WalkForwardPlan must have an explicit purge_policy for evaluation")
        if plan.embargo_policy is None:
            raise ValueError("WalkForwardPlan must have an explicit embargo_policy for evaluation")

        eff_purge = plan.purge_policy
        eff_embargo = plan.embargo_policy

        # Pre-instantiate to extract identity and perform role checks
        dummy_cand = baseline_factory()
        candidate_id = dummy_cand.identity.candidate_id
        eff_code_revision = code_revision or dummy_cand.identity.code_revision

        eff_boundary_id = protected_boundary_id or f"{plan.plan_id}:protected"

        # If role is PROTECTED_TEST and history is provided, check admissibility before execution
        if role is EvaluationRole.PROTECTED_TEST and evaluation_history is not None:
            evaluation_history.check_admissibility(
                candidate_id=candidate_id,
                protected_boundary_id=eff_boundary_id,
                role=role,
                parent_candidate_ids=tuple(parent_candidate_ids),
            )

        fold_results: list[FoldEvaluationResult] = []

        with localcontext(numeric_policy.get_context()):
            for fold in plan.folds:
                train_set, val_set, eval_set = WalkForwardPlanner.partition_samples(
                    samples, fold, eff_purge, eff_embargo
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

                fold_res = cls.evaluate_candidate_on_fold(
                    baseline=baseline_instance,
                    fold=fold,
                    train_samples=train_set,
                    eval_samples=target_eval_set,
                    role=role,
                    numeric_policy=numeric_policy,
                )
                fold_results.append(fold_res)

            tot_samples = sum(f.sample_count for f in fold_results)
            tot_cold = sum(f.cold_start_count for f in fold_results)

            # Extract per-fold metrics and counts
            per_fold_metrics = tuple(f.metrics for f in fold_results)
            fold_sample_counts = tuple(f.sample_count for f in fold_results)
            metric_effective_counts = tuple(f.metric_effective_counts for f in fold_results)

            # Collect unique metric keys across folds
            all_metric_keys = sorted({k for f in fold_results for k in f.metrics.keys()})
            agg_metrics: dict[str, Decimal] = {}

            for k in all_metric_keys:
                fold_pairs: list[tuple[Decimal, int]] = []
                for f in fold_results:
                    if k in f.metrics:
                        eff_cnt = f.metric_effective_counts.get(k, f.sample_count)
                        fold_pairs.append((f.metrics[k], eff_cnt))

                if aggregation_policy is FoldAggregationPolicy.EQUAL_FOLD:
                    # Arithmetic mean across folds with valid metrics
                    vals = [m for m, _ in fold_pairs]
                    agg_metrics[f"mean_{k}"] = sum(vals, Decimal(0)) / Decimal(len(vals))
                else:
                    # Sample-weighted mean using effective metric counts
                    sum_weighted = sum((m * Decimal(w) for m, w in fold_pairs), Decimal(0))
                    sum_weights = sum(w for _, w in fold_pairs)
                    agg_metrics[f"weighted_mean_{k}"] = sum_weighted / Decimal(sum_weights)

            # Compute fold stability diagnostics
            num_folds = len(fold_results)
            stability_diagnostics: dict[str, FoldStabilityDiagnostics] = {}

            for k in all_metric_keys:
                fold_vals: list[tuple[str, Decimal]] = [
                    (f.fold_id, f.metrics[k]) for f in fold_results if k in f.metrics
                ]
                vals_only = [v for _, v in fold_vals]
                min_v = min(vals_only)
                max_v = max(vals_only)
                range_v = max_v - min_v

                # Median
                sorted_vals = sorted(vals_only)
                n_v = len(sorted_vals)
                if n_v % 2 == 1:
                    median_v = sorted_vals[n_v // 2]
                else:
                    median_v = (sorted_vals[n_v // 2 - 1] + sorted_vals[n_v // 2]) / Decimal(2)

                # Dispersion (Mean Absolute Deviation around median)
                dispersion_v = sum(
                    (abs(v - median_v) for v in sorted_vals), Decimal(0)
                ) / Decimal(n_v)

                # Determine best/worst fold
                higher_is_better = k in ("accuracy",)
                if higher_is_better:
                    best_fold = max(fold_vals, key=lambda x: x[1])[0]
                    worst_fold = min(fold_vals, key=lambda x: x[1])[0]
                    best_val = max(vals_only)
                    worst_val = min(vals_only)
                else:
                    best_fold = min(fold_vals, key=lambda x: x[1])[0]
                    worst_fold = max(fold_vals, key=lambda x: x[1])[0]
                    best_val = min(vals_only)
                    worst_val = max(vals_only)

                # Sign consistency: all positive or all negative or all zero
                all_positive = all(v > Decimal(0) for v in vals_only)
                all_negative = all(v < Decimal(0) for v in vals_only)
                all_zero = all(v == Decimal(0) for v in vals_only)
                sign_consistency = all_positive or all_negative or all_zero

                # Relative degradation: (worst - best) / abs(best)
                if best_val != Decimal(0):
                    rel_deg = abs(worst_val - best_val) / abs(best_val)
                else:
                    rel_deg = abs(worst_val - best_val)

                # If population is 1 fold, cannot claim stability evidence
                has_evidence = num_folds >= 2

                stability_diagnostics[k] = FoldStabilityDiagnostics(
                    metric_name=k,
                    min_value=min_v,
                    max_value=max_v,
                    median_value=median_v,
                    dispersion=dispersion_v,
                    range_value=range_v,
                    worst_fold_id=worst_fold,
                    best_fold_id=best_fold,
                    sign_consistency=sign_consistency,
                    relative_degradation=rel_deg,
                    has_stability_evidence=has_evidence,
                )

        # Record evaluation in history if protected test
        protected_records: tuple[Any, ...] = ()
        if role is EvaluationRole.PROTECTED_TEST and evaluation_history is not None:
            from btg_ai_trader.statistical_baselines.comparison import ProtectedEvidenceUse

            evaluation_history.record_evaluation(
                candidate_id=candidate_id,
                protected_boundary_id=eff_boundary_id,
                role=role,
                informed_adaptation=informed_adaptation,
                parent_candidate_ids=tuple(parent_candidate_ids),
            )
            protected_records = (
                ProtectedEvidenceUse(
                    candidate_id=candidate_id,
                    protected_boundary_id=eff_boundary_id,
                    evaluation_role=role,
                    informed_adaptation=informed_adaptation,
                    parent_candidate_ids=tuple(parent_candidate_ids),
                ),
            )

        # Compute evaluation context fingerprint binding full real population and plan
        from btg_ai_trader.statistical_baselines.provenance import (
            StatisticalEvaluationInputBoundary,
            StatisticalEvaluationManifest,
        )

        dataset_digest = (
            StatisticalEvaluationInputBoundary.compute_dataset_digest(samples)
            if samples
            else ""
        )
        source_lineage_digest = (
            StatisticalEvaluationInputBoundary.compute_source_lineage_digest(samples)
            if samples
            else ""
        )
        plan_digest = StatisticalEvaluationManifest.compute_plan_digest(plan)

        target_sem_val = samples[0].target_semantics.value if samples else "UNKNOWN"
        context_payload = {
            "dataset_digest": dataset_digest,
            "source_lineage_digest": source_lineage_digest,
            "target_contract_id": target_contract_id,
            "target_semantics": target_sem_val,
            "plan_digest": plan_digest,
            "role": role.value,
            "aggregation_policy": aggregation_policy.value,
            "numeric_policy": numeric_policy.to_canonical_dict(),
            "code_revision": eff_code_revision,
            "metric_names": all_metric_keys,
            "calibration_config": (
                {"num_bins": 10} if any(f.calibration_report for f in fold_results) else {}
            ),
        }
        context_ser = json.dumps(context_payload, sort_keys=True, separators=(",", ":"))
        context_fp = hashlib.sha256(context_ser.encode("utf-8")).hexdigest()

        return AggregateEvaluationResult(
            candidate_id=candidate_id,
            evaluation_role=role,
            fold_results=tuple(fold_results),
            aggregate_metrics=agg_metrics,
            total_samples=tot_samples,
            total_cold_starts=tot_cold,
            aggregation_policy=aggregation_policy,
            numeric_policy=numeric_policy,
            per_fold_metrics=per_fold_metrics,
            fold_sample_counts=fold_sample_counts,
            metric_effective_counts=metric_effective_counts,
            stability_diagnostics=stability_diagnostics,
            target_contract_id=target_contract_id,
            code_revision=eff_code_revision,
            evaluation_context_fingerprint=context_fp,
            protected_evidence_records=protected_records,
        )
