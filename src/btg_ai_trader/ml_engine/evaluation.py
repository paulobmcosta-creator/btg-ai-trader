"""Causal ML evaluation reusing Sprint 4 partitioning and protected-evidence semantics."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

import numpy as np

from btg_ai_trader.ml_engine.domain import (
    EvaluationScope,
    ModelEvaluationDisposition,
    PredictiveCandidate,
)
from btg_ai_trader.ml_engine.features import (
    FeaturePipelineSpec,
    FeatureSchema,
    FittedFeaturePipeline,
)
from btg_ai_trader.ml_engine.metrics import (
    apply_numeric_policy,
    compute_brier_score,
    compute_calibration_diagnostics,
    compute_continuous_metrics,
    compute_log_loss,
    compute_roc_auc,
)
from btg_ai_trader.ml_engine.models import create_candidate
from btg_ai_trader.statistical_baselines.boundaries import WalkForwardPlan
from btg_ai_trader.statistical_baselines.comparison import EvaluationHistory
from btg_ai_trader.statistical_baselines.domain import (
    EvaluationRole,
    ParityViolationError,
    StatisticalSample,
    TargetSemantics,
    _freeze_mapping,
)
from btg_ai_trader.statistical_baselines.evaluation import (
    AggregateEvaluationResult,
    FoldAggregationPolicy,
)
from btg_ai_trader.statistical_baselines.metrics import NumericPolicy
from btg_ai_trader.statistical_baselines.provenance import (
    StatisticalEvaluationInputBoundary,
    StatisticalEvaluationManifest,
)
from btg_ai_trader.statistical_baselines.splits import WalkForwardPlanner


@dataclass(frozen=True, slots=True)
class FoldModelEvaluation:
    """Metrics for one canonical temporal fold."""

    fold_id: str
    role: EvaluationRole
    metrics: Mapping[str, Decimal]
    sample_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "metrics", _freeze_mapping(dict(self.metrics)))


@dataclass(frozen=True, slots=True)
class ModelEvaluationReport:
    """Aggregated model evidence with candidate-independent experimental context."""

    candidate_id: str
    evaluation_scope: EvaluationScope
    role: EvaluationRole
    target_semantics: TargetSemantics
    fold_evaluations: tuple[FoldModelEvaluation, ...]
    mean_metrics: Mapping[str, Decimal]
    aggregation_policy: FoldAggregationPolicy
    numeric_policy: NumericPolicy
    dataset_digest: str
    plan_digest: str
    target_contract_digest: str
    experimental_context_fingerprint: str
    disposition: ModelEvaluationDisposition
    protected_boundary_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "mean_metrics", _freeze_mapping(dict(self.mean_metrics)))


@dataclass(frozen=True, slots=True)
class BaselineComparisonResult:
    """Real ML-vs-S4-baseline metric comparison under verified parity."""

    candidate_id: str
    baseline_id: str
    metric_name: str
    candidate_metric: Decimal
    baseline_metric: Decimal
    improvement: Decimal
    is_comparable: bool
    candidate_context_fingerprint: str
    baseline_context_fingerprint: str


@dataclass(frozen=True, slots=True)
class FeatureAblationSpec:
    """One explicitly named feature-removal experiment."""

    ablated_feature_name: str


@dataclass(frozen=True, slots=True)
class AblationResult:
    """Full-vs-ablated validation evidence."""

    ablated_feature: str
    metric_name: str
    full_metric: Decimal
    ablated_metric: Decimal
    delta: Decimal


def _experimental_context_fingerprint(
    *,
    samples: Sequence[StatisticalSample],
    plan: WalkForwardPlan,
    target_contract_digest: str,
    role: EvaluationRole,
    aggregation_policy: FoldAggregationPolicy,
    numeric_policy: NumericPolicy,
) -> tuple[str, str, str]:
    dataset_digest = StatisticalEvaluationInputBoundary.compute_dataset_digest(samples)
    source_lineage_digest = (
        StatisticalEvaluationInputBoundary.compute_source_lineage_digest(samples)
    )
    plan_digest = StatisticalEvaluationManifest.compute_plan_digest(plan)
    payload = {
        "aggregation_policy": aggregation_policy.value,
        "dataset_digest": dataset_digest,
        "fold_ids": [fold.fold_id for fold in plan.folds],
        "numeric_policy": numeric_policy.to_canonical_dict(),
        "plan_digest": plan_digest,
        "role": role.value,
        "source_lineage_digest": source_lineage_digest,
        "target_contract_digest": target_contract_digest,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return (
        hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        dataset_digest,
        plan_digest,
    )


def _expected_s4_context_fingerprint(
    *,
    baseline_result: AggregateEvaluationResult,
    samples: Sequence[StatisticalSample],
    plan: WalkForwardPlan,
) -> str:
    dataset_digest = StatisticalEvaluationInputBoundary.compute_dataset_digest(samples)
    source_lineage_digest = (
        StatisticalEvaluationInputBoundary.compute_source_lineage_digest(samples)
    )
    plan_digest = StatisticalEvaluationManifest.compute_plan_digest(plan)
    metric_names = sorted(
        {
            name
            for fold_result in baseline_result.fold_results
            for name in fold_result.metrics
        }
    )
    payload = {
        "aggregation_policy": baseline_result.aggregation_policy.value,
        "calibration_config": (
            {"num_bins": 10}
            if any(
                fold_result.calibration_report is not None
                for fold_result in baseline_result.fold_results
            )
            else {}
        ),
        "code_revision": baseline_result.code_revision,
        "dataset_digest": dataset_digest,
        "metric_names": metric_names,
        "numeric_policy": baseline_result.numeric_policy.to_canonical_dict(),
        "plan_digest": plan_digest,
        "role": baseline_result.evaluation_role.value,
        "source_lineage_digest": source_lineage_digest,
        "target_contract_id": baseline_result.target_contract_id,
        "target_semantics": samples[0].target_semantics.value if samples else "UNKNOWN",
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ModelEvaluationEngine:
    """Evaluate predictive candidates using canonical S4 temporal partitions."""

    def evaluate_candidate(
        self,
        candidate: PredictiveCandidate,
        pipeline_spec: FeaturePipelineSpec,
        plan: WalkForwardPlan,
        samples: Sequence[StatisticalSample],
        role: EvaluationRole = EvaluationRole.VALIDATION_SELECTION,
        *,
        aggregation_policy: FoldAggregationPolicy = FoldAggregationPolicy.EQUAL_FOLD,
        evaluation_history: EvaluationHistory | None = None,
        protected_boundary_id: str | None = None,
        parent_candidate_ids: Sequence[str] = (),
        informed_adaptation: bool = False,
    ) -> ModelEvaluationReport:
        if role not in {
            EvaluationRole.VALIDATION_SELECTION,
            EvaluationRole.PROTECTED_TEST,
        }:
            raise ValueError(
                "Model evaluation accepts VALIDATION_SELECTION or PROTECTED_TEST only"
            )
        if not samples:
            raise ValueError("Cannot evaluate candidate on empty samples")
        if plan.purge_policy is None or plan.embargo_policy is None:
            raise ValueError(
                "WalkForwardPlan must bind explicit purge_policy and embargo_policy"
            )
        StatisticalEvaluationInputBoundary.validate_dataset(samples)
        if candidate.spec.feature_pipeline_spec_digest != pipeline_spec.spec_digest:
            raise ValueError(
                "candidate feature_pipeline_spec_digest does not match evaluation pipeline"
            )

        boundary_id = protected_boundary_id or f"{plan.plan_id}:protected"
        if role is EvaluationRole.PROTECTED_TEST:
            if evaluation_history is None:
                raise ValueError(
                    "PROTECTED_TEST evaluation requires EvaluationHistory"
                )
            evaluation_history.check_admissibility(
                candidate_id=candidate.spec.candidate_id,
                protected_boundary_id=boundary_id,
                role=role,
                parent_candidate_ids=tuple(parent_candidate_ids),
            )

        fold_results: list[FoldModelEvaluation] = []
        metric_values: dict[str, list[tuple[Decimal, int]]] = {}

        for fold in plan.folds:
            train_samples, validation_samples, protected_samples = (
                WalkForwardPlanner.partition_samples(
                    samples,
                    fold,
                    plan.purge_policy,
                    plan.embargo_policy,
                )
            )
            if not train_samples:
                raise ValueError(
                    f"Fold '{fold.fold_id}' has zero training samples after purge/embargo"
                )
            if role is EvaluationRole.VALIDATION_SELECTION:
                if validation_samples is None:
                    raise ValueError(
                        f"Fold '{fold.fold_id}' has no validation boundary"
                    )
                evaluation_samples = validation_samples
            else:
                evaluation_samples = protected_samples

            if not evaluation_samples:
                fold_results.append(
                    FoldModelEvaluation(
                        fold_id=fold.fold_id,
                        role=role,
                        metrics={},
                        sample_count=0,
                    )
                )
                continue

            fitted_pipeline = FittedFeaturePipeline.fit(
                pipeline_spec, train_samples
            )
            X_train = fitted_pipeline.transform(
                [sample.to_prediction_input() for sample in train_samples]
            )
            semantics = candidate.spec.target_contract.target_semantics
            if semantics is TargetSemantics.BINARY_PROBABILITY:
                y_train = np.asarray(
                    [int(sample.target_value) for sample in train_samples],
                    dtype=np.int64,
                )
            else:
                y_train = np.asarray(
                    [float(sample.target_value) for sample in train_samples],
                    dtype=np.float64,
                )

            fold_candidate = create_candidate(candidate.spec)
            fold_candidate.fit(X_train, y_train)
            predictions = fold_candidate.predict(
                [sample.to_prediction_input() for sample in evaluation_samples],
                fitted_pipeline,
            )
            metrics: dict[str, Decimal] = {}

            if semantics is TargetSemantics.BINARY_PROBABILITY:
                probabilities = [
                    prediction.predicted_probability for prediction in predictions
                ]
                if any(probability is None for probability in probabilities):
                    raise ValueError(
                        "Binary candidate produced prediction without probability"
                    )
                clean_probabilities = [
                    probability
                    for probability in probabilities
                    if probability is not None
                ]
                y_true = [int(sample.target_value) for sample in evaluation_samples]
                metrics["brier_score"] = compute_brier_score(
                    y_true, clean_probabilities, candidate.spec.numeric_policy
                )
                metrics["log_loss"] = compute_log_loss(
                    y_true, clean_probabilities, candidate.spec.numeric_policy
                )
                calibration = compute_calibration_diagnostics(
                    y_true, clean_probabilities, candidate.spec.numeric_policy
                )
                metrics["ece"] = calibration.ece
                metrics["mce"] = calibration.mce
                if set(y_true) == {0, 1}:
                    metrics["roc_auc"] = compute_roc_auc(
                        y_true, clean_probabilities, candidate.spec.numeric_policy
                    )
            else:
                predicted_values = [
                    prediction.predicted_value for prediction in predictions
                ]
                if any(value is None for value in predicted_values):
                    raise ValueError(
                        "Continuous candidate produced prediction without value"
                    )
                report = compute_continuous_metrics(
                    [Decimal(str(sample.target_value)) for sample in evaluation_samples],
                    [value for value in predicted_values if value is not None],
                    candidate.spec.numeric_policy,
                )
                metrics.update(
                    {
                        "mae": report.mae,
                        "mean_bias": report.mean_bias,
                        "mse": report.mse,
                        "rmse": report.rmse,
                    }
                )
                if report.r2_score is not None:
                    metrics["r2_score"] = report.r2_score

            sample_count = len(evaluation_samples)
            fold_results.append(
                FoldModelEvaluation(
                    fold_id=fold.fold_id,
                    role=role,
                    metrics=metrics,
                    sample_count=sample_count,
                )
            )
            for name, value in metrics.items():
                metric_values.setdefault(name, []).append((value, sample_count))

        aggregate: dict[str, Decimal] = {}
        for name, pairs in metric_values.items():
            if aggregation_policy is FoldAggregationPolicy.EQUAL_FOLD:
                raw = sum((value for value, _ in pairs), Decimal(0)) / Decimal(
                    len(pairs)
                )
            else:
                weight = sum(count for _, count in pairs)
                raw = sum(
                    (value * Decimal(count) for value, count in pairs), Decimal(0)
                ) / Decimal(weight)
            aggregate[name] = apply_numeric_policy(
                raw, candidate.spec.numeric_policy
            )

        context_fp, dataset_digest, plan_digest = _experimental_context_fingerprint(
            samples=samples,
            plan=plan,
            target_contract_digest=candidate.spec.target_contract.contract_digest,
            role=role,
            aggregation_policy=aggregation_policy,
            numeric_policy=candidate.spec.numeric_policy,
        )

        if role is EvaluationRole.PROTECTED_TEST:
            assert evaluation_history is not None
            evaluation_history.record_evaluation(
                candidate_id=candidate.spec.candidate_id,
                protected_boundary_id=boundary_id,
                role=role,
                informed_adaptation=informed_adaptation,
                parent_candidate_ids=tuple(parent_candidate_ids),
            )

        return ModelEvaluationReport(
            candidate_id=candidate.spec.candidate_id,
            evaluation_scope=EvaluationScope.MODEL,
            role=role,
            target_semantics=candidate.spec.target_contract.target_semantics,
            fold_evaluations=tuple(fold_results),
            mean_metrics=aggregate,
            aggregation_policy=aggregation_policy,
            numeric_policy=candidate.spec.numeric_policy,
            dataset_digest=dataset_digest,
            plan_digest=plan_digest,
            target_contract_digest=candidate.spec.target_contract.contract_digest,
            experimental_context_fingerprint=context_fp,
            disposition=ModelEvaluationDisposition.INCONCLUSIVE,
            protected_boundary_id=boundary_id if role is EvaluationRole.PROTECTED_TEST else "",
        )

    def compare_with_baseline(
        self,
        *,
        candidate_report: ModelEvaluationReport,
        baseline_result: AggregateEvaluationResult,
        metric_name: str,
        plan: WalkForwardPlan,
        samples: Sequence[StatisticalSample],
        higher_is_better: bool = False,
    ) -> BaselineComparisonResult:
        if metric_name not in candidate_report.mean_metrics:
            raise ParityViolationError(
                f"Metric '{metric_name}' not present in candidate report"
            )
        if baseline_result.evaluation_role is not candidate_report.role:
            raise ParityViolationError("Candidate and baseline evaluation roles differ")
        if baseline_result.aggregation_policy is not candidate_report.aggregation_policy:
            raise ParityViolationError("Candidate and baseline aggregation policies differ")
        if baseline_result.numeric_policy != candidate_report.numeric_policy:
            raise ParityViolationError("Candidate and baseline numeric policies differ")
        if baseline_result.target_contract_id != candidate_report.target_contract_digest:
            raise ParityViolationError("Candidate and baseline target contracts differ")

        candidate_fold_ids = [
            fold.fold_id for fold in candidate_report.fold_evaluations
        ]
        baseline_fold_ids = [
            fold.fold_id for fold in baseline_result.fold_results
        ]
        if candidate_fold_ids != baseline_fold_ids:
            raise ParityViolationError("Candidate and baseline fold identities differ")

        expected_baseline_fp = _expected_s4_context_fingerprint(
            baseline_result=baseline_result,
            samples=samples,
            plan=plan,
        )
        if baseline_result.evaluation_context_fingerprint != expected_baseline_fp:
            raise ParityViolationError(
                "Baseline result does not match the supplied population/plan context"
            )

        expected_candidate_fp, expected_dataset, expected_plan = (
            _experimental_context_fingerprint(
                samples=samples,
                plan=plan,
                target_contract_digest=candidate_report.target_contract_digest,
                role=candidate_report.role,
                aggregation_policy=candidate_report.aggregation_policy,
                numeric_policy=candidate_report.numeric_policy,
            )
        )
        if (
            candidate_report.experimental_context_fingerprint
            != expected_candidate_fp
            or candidate_report.dataset_digest != expected_dataset
            or candidate_report.plan_digest != expected_plan
        ):
            raise ParityViolationError(
                "Candidate report does not match the supplied population/plan context"
            )

        prefix = (
            "mean_"
            if baseline_result.aggregation_policy is FoldAggregationPolicy.EQUAL_FOLD
            else "weighted_mean_"
        )
        baseline_metric_name = f"{prefix}{metric_name}"
        if baseline_metric_name not in baseline_result.aggregate_metrics:
            raise ParityViolationError(
                f"Metric '{baseline_metric_name}' not present in baseline result"
            )

        candidate_metric = candidate_report.mean_metrics[metric_name]
        baseline_metric = baseline_result.aggregate_metrics[baseline_metric_name]
        improvement = (
            candidate_metric - baseline_metric
            if higher_is_better
            else baseline_metric - candidate_metric
        )
        return BaselineComparisonResult(
            candidate_id=candidate_report.candidate_id,
            baseline_id=baseline_result.candidate_id,
            metric_name=metric_name,
            candidate_metric=candidate_metric,
            baseline_metric=baseline_metric,
            improvement=improvement,
            is_comparable=True,
            candidate_context_fingerprint=(
                candidate_report.experimental_context_fingerprint
            ),
            baseline_context_fingerprint=baseline_result.evaluation_context_fingerprint,
        )

    def run_ablation(
        self,
        *,
        candidate: PredictiveCandidate,
        full_pipeline_spec: FeaturePipelineSpec,
        ablation_spec: FeatureAblationSpec,
        plan: WalkForwardPlan,
        samples: Sequence[StatisticalSample],
        metric_name: str,
        aggregation_policy: FoldAggregationPolicy = FoldAggregationPolicy.EQUAL_FOLD,
    ) -> AblationResult:
        names = {
            feature.name for feature in full_pipeline_spec.schema.features
        }
        if ablation_spec.ablated_feature_name not in names:
            raise ValueError(
                f"Feature '{ablation_spec.ablated_feature_name}' is not in the schema"
            )

        full_report = self.evaluate_candidate(
            candidate,
            full_pipeline_spec,
            plan,
            samples,
            role=EvaluationRole.VALIDATION_SELECTION,
            aggregation_policy=aggregation_policy,
        )
        if metric_name not in full_report.mean_metrics:
            raise ValueError(
                f"Metric '{metric_name}' not available for full candidate"
            )

        remaining = tuple(
            feature
            for feature in full_pipeline_spec.schema.features
            if feature.name != ablation_spec.ablated_feature_name
        )
        if not remaining:
            raise ValueError("Cannot ablate all features from schema")
        ablated_pipeline = FeaturePipelineSpec(
            schema=FeatureSchema(remaining),
            normalize=full_pipeline_spec.normalize,
        )
        candidate_type = candidate.spec.__class__
        ablated_spec = candidate_type(
            family=candidate.spec.family,
            hyperparameters=candidate.spec.hyperparameters,
            target_contract=candidate.spec.target_contract,
            feature_pipeline_spec_digest=ablated_pipeline.spec_digest,
            rng_context=candidate.spec.rng_context,
            numeric_policy=candidate.spec.numeric_policy,
            code_revision=candidate.spec.code_revision,
        )
        ablated_candidate = create_candidate(ablated_spec)
        ablated_report = self.evaluate_candidate(
            ablated_candidate,
            ablated_pipeline,
            plan,
            samples,
            role=EvaluationRole.VALIDATION_SELECTION,
            aggregation_policy=aggregation_policy,
        )
        if metric_name not in ablated_report.mean_metrics:
            raise ValueError(
                f"Metric '{metric_name}' not available for ablated candidate"
            )
        full_metric = full_report.mean_metrics[metric_name]
        ablated_metric = ablated_report.mean_metrics[metric_name]
        return AblationResult(
            ablated_feature=ablation_spec.ablated_feature_name,
            metric_name=metric_name,
            full_metric=full_metric,
            ablated_metric=ablated_metric,
            delta=apply_numeric_policy(
                full_metric - ablated_metric, candidate.spec.numeric_policy
            ),
        )
