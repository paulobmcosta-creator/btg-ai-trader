"""Evaluation provenance, input boundary validation, and cryptographically verifiable manifests."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from btg_ai_trader.statistical_baselines.boundaries import WalkForwardPlan
from btg_ai_trader.statistical_baselines.comparison import (
    ModelComparisonResult,
    SearchFamily,
)
from btg_ai_trader.statistical_baselines.domain import (
    CandidateIdentity,
    StatisticalSample,
    TargetSemantics,
    _freeze_mapping,
    _validate_timezone_aware,
)
from btg_ai_trader.statistical_baselines.evaluation import (
    AggregateEvaluationResult,
    FoldAggregationPolicy,
)
from btg_ai_trader.statistical_baselines.metrics import (
    DEFAULT_NUMERIC_POLICY,
    NumericPolicy,
)
from btg_ai_trader.statistical_baselines.splits import (
    EmbargoPolicy,
    PurgePolicy,
)


_BOUNDARY_VERIFICATION_TOKEN = object()


@dataclass(frozen=True, slots=True)
class StatisticalEvaluationInputBoundary:
    """Immutable input boundary verifying dataset, plan, and configurations before execution."""

    sample_ids: tuple[str, ...]
    dataset_digest: str
    source_lineage_digest: str
    target_semantics: TargetSemantics
    target_contract_id: str
    candidate_identities: tuple[CandidateIdentity, ...]
    search_family: SearchFamily | None
    plan_digest: str
    fold_definitions: tuple[Mapping[str, Any], ...]
    purge_policy: PurgePolicy
    embargo_policy: EmbargoPolicy
    metric_names: tuple[str, ...]
    calibration_config: Mapping[str, Any]
    aggregation_policy: FoldAggregationPolicy
    numeric_policy: NumericPolicy
    code_revision: str
    logical_evaluation_digest: str
    _verification_token: object = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._verification_token is not _BOUNDARY_VERIFICATION_TOKEN:
            raise ValueError(
                "StatisticalEvaluationInputBoundary must be created via "
                "StatisticalEvaluationInputBoundary.create()"
            )
        object.__setattr__(self, "sample_ids", tuple(self.sample_ids))
        object.__setattr__(self, "candidate_identities", tuple(self.candidate_identities))
        object.__setattr__(self, "metric_names", tuple(sorted(self.metric_names)))
        object.__setattr__(
            self, "calibration_config", _freeze_mapping(dict(self.calibration_config))
        )
        object.__setattr__(
            self,
            "fold_definitions",
            tuple(_freeze_mapping(dict(d)) for d in self.fold_definitions),
        )

        logical_payload = {
            "sample_ids": list(self.sample_ids),
            "dataset_digest": self.dataset_digest,
            "source_lineage_digest": self.source_lineage_digest,
            "target_semantics": self.target_semantics.value,
            "target_contract_id": self.target_contract_id,
            "plan_digest": self.plan_digest,
            "fold_definitions": [dict(d) for d in self.fold_definitions],
            "purge_policy": {
                "purge_overlapping": self.purge_policy.purge_overlapping,
                "default_horizon": (
                    str(self.purge_policy.default_horizon)
                    if self.purge_policy.default_horizon is not None
                    else None
                ),
                "fail_closed_on_unknown": self.purge_policy.fail_closed_on_unknown,
            },
            "embargo_policy": {"duration": str(self.embargo_policy.duration)},
            "candidate_ids": [c.candidate_id for c in self.candidate_identities],
            "search_family": self.search_family.to_canonical_dict() if self.search_family else None,
            "metric_names": sorted(self.metric_names),
            "calibration_config": dict(self.calibration_config),
            "aggregation_policy": self.aggregation_policy.value,
            "numeric_policy": self.numeric_policy.to_canonical_dict(),
            "code_revision": self.code_revision,
        }
        logical_ser = json.dumps(logical_payload, sort_keys=True, separators=(",", ":"))
        expected_digest = hashlib.sha256(logical_ser.encode("utf-8")).hexdigest()
        if self.logical_evaluation_digest != expected_digest:
            raise ValueError(
                f"logical_evaluation_digest mismatch: expected {expected_digest}, "
                f"got {self.logical_evaluation_digest}"
            )

    @classmethod
    def compute_dataset_digest(cls, samples: Sequence[StatisticalSample]) -> str:
        """Compute canonical SHA-256 digest of sample sequence preserving exact input order."""
        canonical_items = [
            {
                "order_index": idx,
                "sample_id": s.sample_id,
                "feature_knowledge_time": s.feature_knowledge_time.isoformat(),
                "target_knowledge_time": s.target_knowledge_time.isoformat(),
                "target_value": str(s.target_value),
                "target_semantics": s.target_semantics.value,
                "reference_value": (
                    str(s.reference_value) if s.reference_value is not None else None
                ),
                "information_interval": (
                    [s.information_interval[0].isoformat(), s.information_interval[1].isoformat()]
                    if s.information_interval is not None
                    else None
                ),
                "source_lineage": s.source_lineage,
                "metadata": {k: str(v) for k, v in sorted(s.metadata.items())},
                "feature_metadata": {k: str(v) for k, v in sorted(s.feature_metadata.items())},
                "audit_metadata": {k: str(v) for k, v in sorted(s.audit_metadata.items())},
            }
            for idx, s in enumerate(samples)
        ]
        serialized = json.dumps(canonical_items, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def compute_source_lineage_digest(cls, samples: Sequence[StatisticalSample]) -> str:
        """Compute digest of raw source lineage strings."""
        lineages = [s.source_lineage for s in samples]
        serialized = json.dumps(lineages, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def validate_dataset(
        cls, samples: Sequence[StatisticalSample]
    ) -> tuple[StatisticalSample, ...]:
        """Validate input dataset, enforcing uniqueness, causality, and strict order validation."""
        if not samples:
            raise ValueError("Input sample dataset cannot be empty")

        seen_ids: set[str] = set()
        for i, s in enumerate(samples):
            if s.sample_id in seen_ids:
                raise ValueError(f"Duplicate sample_id rejected: {s.sample_id}")
            seen_ids.add(s.sample_id)
            if s.feature_knowledge_time > s.target_knowledge_time:
                raise ValueError(
                    f"Sample {s.sample_id}: feature_knowledge_time cannot be after "
                    f"target_knowledge_time"
                )
            if i > 0:
                prev = samples[i - 1]
                if (s.feature_knowledge_time, s.target_knowledge_time, s.sample_id) < (
                    prev.feature_knowledge_time,
                    prev.target_knowledge_time,
                    prev.sample_id,
                ):
                    raise ValueError(
                        f"Sample {s.sample_id} at index {i} is out of chronological order "
                        f"relative to sample {prev.sample_id} at index {i-1}"
                    )

        return tuple(samples)

    @classmethod
    def create(
        cls,
        samples: Sequence[StatisticalSample],
        plan: WalkForwardPlan,
        candidate_identities: Sequence[CandidateIdentity],
        code_revision: str,
        target_contract_id: str = "generic_target_contract_s4",
        search_family: SearchFamily | None = None,
        metric_names: Sequence[str] = (),
        calibration_config: Mapping[str, Any] | None = None,
        aggregation_policy: FoldAggregationPolicy = FoldAggregationPolicy.EQUAL_FOLD,
        numeric_policy: NumericPolicy = DEFAULT_NUMERIC_POLICY,
    ) -> StatisticalEvaluationInputBoundary:
        """Construct a validated, fully bound StatisticalEvaluationInputBoundary."""
        valid_samples = cls.validate_dataset(samples)
        dataset_digest = cls.compute_dataset_digest(valid_samples)
        source_lineage_digest = cls.compute_source_lineage_digest(valid_samples)
        plan_digest = StatisticalEvaluationManifest.compute_plan_digest(plan)

        cal_cfg = dict(calibration_config or {})
        fold_defs = tuple(
            {
                "fold_id": f.fold_id,
                "train_start": f.training_boundary.start_time.isoformat(),
                "train_end": f.training_boundary.end_time.isoformat(),
                "eval_start": f.protected_evaluation_boundary.start_time.isoformat(),
                "eval_end": f.protected_evaluation_boundary.end_time.isoformat(),
                "cutoff": f.knowledge_cutoff.isoformat(),
            }
            for f in plan.folds
        )

        assert plan.purge_policy is not None
        assert plan.embargo_policy is not None
        purge_pol = plan.purge_policy
        embargo_pol = plan.embargo_policy

        logical_payload = {
            "sample_ids": [s.sample_id for s in valid_samples],
            "dataset_digest": dataset_digest,
            "source_lineage_digest": source_lineage_digest,
            "target_semantics": valid_samples[0].target_semantics.value,
            "target_contract_id": target_contract_id,
            "plan_digest": plan_digest,
            "fold_definitions": fold_defs,
            "purge_policy": {
                "purge_overlapping": purge_pol.purge_overlapping,
                "default_horizon": (
                    str(purge_pol.default_horizon)
                    if purge_pol.default_horizon is not None
                    else None
                ),
                "fail_closed_on_unknown": purge_pol.fail_closed_on_unknown,
            },
            "embargo_policy": {"duration": str(embargo_pol.duration)},
            "candidate_ids": [c.candidate_id for c in candidate_identities],
            "search_family": search_family.to_canonical_dict() if search_family else None,
            "metric_names": sorted(metric_names),
            "calibration_config": cal_cfg,
            "aggregation_policy": aggregation_policy.value,
            "numeric_policy": numeric_policy.to_canonical_dict(),
            "code_revision": code_revision,
        }
        logical_ser = json.dumps(logical_payload, sort_keys=True, separators=(",", ":"))
        logical_digest = hashlib.sha256(logical_ser.encode("utf-8")).hexdigest()

        return cls(
            sample_ids=tuple(s.sample_id for s in valid_samples),
            dataset_digest=dataset_digest,
            source_lineage_digest=source_lineage_digest,
            target_semantics=valid_samples[0].target_semantics,
            target_contract_id=target_contract_id,
            candidate_identities=tuple(candidate_identities),
            search_family=search_family,
            plan_digest=plan_digest,
            fold_definitions=fold_defs,
            purge_policy=purge_pol,
            embargo_policy=embargo_pol,
            metric_names=tuple(sorted(metric_names)),
            calibration_config=_freeze_mapping(cal_cfg),
            aggregation_policy=aggregation_policy,
            numeric_policy=numeric_policy,
            code_revision=code_revision,
            logical_evaluation_digest=logical_digest,
            _verification_token=_BOUNDARY_VERIFICATION_TOKEN,
        )


@dataclass(frozen=True, slots=True)
class EvaluationProvenanceRecord:
    """Cryptographically verifiable provenance record describing experimental lineage."""

    plan_id: str
    plan_digest: str
    dataset_digest: str
    candidate_identities: tuple[CandidateIdentity, ...]
    code_revision: str
    manifest_digest: str
    observed_execution_timestamp: datetime
    input_boundary_digest: str = ""
    source_lineage_digest: str = ""

    def __init__(
        self,
        plan_id: str,
        plan_digest: str,
        dataset_digest: str,
        candidate_identities: Sequence[CandidateIdentity],
        code_revision: str,
        manifest_digest: str,
        observed_execution_timestamp: datetime | None = None,
        input_boundary_digest: str = "",
        source_lineage_digest: str = "",
        execution_timestamp: datetime | None = None,
    ) -> None:
        eff_ts = (
            observed_execution_timestamp
            if observed_execution_timestamp is not None
            else execution_timestamp
        )
        if eff_ts is None:
            raise ValueError("observed_execution_timestamp or execution_timestamp must be provided")
        _validate_timezone_aware(eff_ts, "observed_execution_timestamp")
        if not plan_id:
            raise ValueError("plan_id cannot be empty")
        if not plan_digest:
            raise ValueError("plan_digest cannot be empty")
        if not dataset_digest:
            raise ValueError("dataset_digest cannot be empty")
        if not code_revision:
            raise ValueError("code_revision cannot be empty")
        if not manifest_digest:
            raise ValueError("manifest_digest cannot be empty")

        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "plan_digest", plan_digest)
        object.__setattr__(self, "dataset_digest", dataset_digest)
        object.__setattr__(self, "candidate_identities", tuple(candidate_identities))
        object.__setattr__(self, "code_revision", code_revision)
        object.__setattr__(self, "manifest_digest", manifest_digest)
        object.__setattr__(self, "observed_execution_timestamp", eff_ts)
        object.__setattr__(self, "input_boundary_digest", input_boundary_digest)
        object.__setattr__(self, "source_lineage_digest", source_lineage_digest)

    @property
    def execution_timestamp(self) -> datetime:
        """Backward-compatible alias for observed_execution_timestamp."""
        return self.observed_execution_timestamp


@dataclass(frozen=True, slots=True)
class StatisticalEvaluationManifest:
    """Canonical verifiable evaluation manifest capturing complete experimental lineage."""

    provenance: EvaluationProvenanceRecord
    aggregate_results: tuple[AggregateEvaluationResult, ...]
    comparison_results: tuple[ModelComparisonResult, ...]
    input_boundary: StatisticalEvaluationInputBoundary | None = None
    search_family: SearchFamily | None = None

    @classmethod
    def compute_plan_digest(cls, plan: WalkForwardPlan) -> str:
        """Compute comprehensive SHA-256 digest for a walk forward plan closing over all boundaries
        and policies.
        """
        if plan.purge_policy is None:
            raise ValueError(f"Plan {plan.plan_id} must have purge_policy bound")
        if plan.embargo_policy is None:
            raise ValueError(f"Plan {plan.plan_id} must have embargo_policy bound")
        plan_dict = {
            "plan_id": plan.plan_id,
            "window_policy": plan.window_policy_name,
            "train_duration": str(plan.train_duration) if plan.train_duration else None,
            "test_duration": str(plan.test_duration) if plan.test_duration else None,
            "step_duration": str(plan.step_duration) if plan.step_duration else None,
            "validation_duration": (
                str(plan.validation_duration) if plan.validation_duration else None
            ),
            "purge_policy": {
                "purge_overlapping": plan.purge_policy.purge_overlapping,
                "default_horizon": (
                    str(plan.purge_policy.default_horizon)
                    if plan.purge_policy.default_horizon is not None
                    else None
                ),
                "fail_closed_on_unknown": plan.purge_policy.fail_closed_on_unknown,
            },
            "embargo_policy": {
                "duration": str(plan.embargo_policy.duration),
            },
            "folds": [
                {
                    "fold_order": idx,
                    "fold_id": f.fold_id,
                    "dev_start": f.development_boundary.start_time.isoformat(),
                    "dev_end": f.development_boundary.end_time.isoformat(),
                    "dev_start_inc": f.development_boundary.start_inclusive,
                    "dev_end_inc": f.development_boundary.end_inclusive,
                    "train_start": f.training_boundary.start_time.isoformat(),
                    "train_end": f.training_boundary.end_time.isoformat(),
                    "train_start_inc": f.training_boundary.start_inclusive,
                    "train_end_inc": f.training_boundary.end_inclusive,
                    "val_start": (
                        f.validation_boundary.start_time.isoformat()
                        if f.validation_boundary
                        else None
                    ),
                    "val_end": (
                        f.validation_boundary.end_time.isoformat()
                        if f.validation_boundary
                        else None
                    ),
                    "val_start_inc": (
                        f.validation_boundary.start_inclusive
                        if f.validation_boundary
                        else None
                    ),
                    "val_end_inc": (
                        f.validation_boundary.end_inclusive
                        if f.validation_boundary
                        else None
                    ),
                    "eval_start": f.protected_evaluation_boundary.start_time.isoformat(),
                    "eval_end": f.protected_evaluation_boundary.end_time.isoformat(),
                    "eval_start_inc": f.protected_evaluation_boundary.start_inclusive,
                    "eval_end_inc": f.protected_evaluation_boundary.end_inclusive,
                    "knowledge_cutoff": f.knowledge_cutoff.isoformat(),
                    "purge_interval": (
                        [f.purge_interval[0].isoformat(), f.purge_interval[1].isoformat()]
                        if f.purge_interval
                        else None
                    ),
                    "embargo_interval": (
                        [f.embargo_interval[0].isoformat(), f.embargo_interval[1].isoformat()]
                        if f.embargo_interval
                        else None
                    ),
                }
                for idx, f in enumerate(plan.folds)
            ],
        }
        serialized = json.dumps(plan_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def create(
        cls,
        plan: WalkForwardPlan,
        samples: Sequence[StatisticalSample],
        candidate_identities: Sequence[CandidateIdentity],
        aggregate_results: Sequence[AggregateEvaluationResult],
        comparison_results: Sequence[ModelComparisonResult],
        code_revision: str,
        execution_timestamp: datetime,
        search_family: SearchFamily | None = None,
        input_boundary: StatisticalEvaluationInputBoundary | None = None,
    ) -> StatisticalEvaluationManifest:
        """Create a complete evaluation manifest with verified cryptographic root digest."""
        _validate_timezone_aware(execution_timestamp, "execution_timestamp")
        valid_samples = StatisticalEvaluationInputBoundary.validate_dataset(samples)
        plan_digest = cls.compute_plan_digest(plan)
        dataset_digest = StatisticalEvaluationInputBoundary.compute_dataset_digest(valid_samples)
        source_lineage_digest = (
            StatisticalEvaluationInputBoundary.compute_source_lineage_digest(valid_samples)
        )

        first_res = aggregate_results[0] if aggregate_results else None
        eff_agg_policy = (
            first_res.aggregation_policy if first_res else FoldAggregationPolicy.EQUAL_FOLD
        )
        eff_num_policy = first_res.numeric_policy if first_res else DEFAULT_NUMERIC_POLICY
        eff_target_contract = (
            first_res.target_contract_id
            if first_res and first_res.target_contract_id
            else "generic_target_contract_s4"
        )
        eff_metric_names = tuple(
            sorted(
                {
                    metric_name
                    for aggregate in aggregate_results
                    for fold in aggregate.fold_results
                    for metric_name in fold.metrics
                }
            )
        )
        calibration_bin_counts = {
            fold.calibration_report.num_bins
            for aggregate in aggregate_results
            for fold in aggregate.fold_results
            if fold.calibration_report is not None
        }
        if len(calibration_bin_counts) > 1:
            raise ValueError(
                "aggregate_results contain inconsistent calibration bin configurations"
            )
        eff_cal_cfg: dict[str, Any] = (
            {"bins": next(iter(calibration_bin_counts))}
            if calibration_bin_counts
            else {}
        )

        expected_boundary = StatisticalEvaluationInputBoundary.create(
            samples=valid_samples,
            plan=plan,
            candidate_identities=candidate_identities,
            code_revision=code_revision,
            target_contract_id=eff_target_contract,
            search_family=search_family,
            metric_names=eff_metric_names,
            calibration_config=eff_cal_cfg,
            aggregation_policy=eff_agg_policy,
            numeric_policy=eff_num_policy,
        )

        if input_boundary is not None:
            if input_boundary.dataset_digest != dataset_digest:
                raise ValueError(
                    f"input_boundary dataset_digest ({input_boundary.dataset_digest}) "
                    f"does not match dataset_digest of samples ({dataset_digest})"
                )
            if input_boundary.source_lineage_digest != source_lineage_digest:
                raise ValueError(
                    "input_boundary source_lineage_digest does not match samples"
                )
            if input_boundary.plan_digest != plan_digest:
                raise ValueError(
                    f"input_boundary plan_digest ({input_boundary.plan_digest}) does not match "
                    f"plan_digest ({plan_digest})"
                )
            if input_boundary.code_revision != code_revision:
                raise ValueError(
                    f"input_boundary code_revision ({input_boundary.code_revision}) does not match "
                    f"code_revision ({code_revision})"
                )
            expected_cand_ids = tuple(c.candidate_id for c in candidate_identities)
            actual_cand_ids = tuple(c.candidate_id for c in input_boundary.candidate_identities)
            if actual_cand_ids != expected_cand_ids:
                raise ValueError(
                    f"input_boundary candidate_identities ({actual_cand_ids}) does not match "
                    f"expected candidate_identities ({expected_cand_ids})"
                )
            if input_boundary.aggregation_policy != eff_agg_policy:
                raise ValueError(
                    f"input_boundary aggregation_policy ({input_boundary.aggregation_policy}) "
                    f"does not match aggregate_results aggregation_policy ({eff_agg_policy})"
                )
            if (
                input_boundary.logical_evaluation_digest
                != expected_boundary.logical_evaluation_digest
            ):
                raise ValueError(
                    "input_boundary logical_evaluation_digest does not match fully "
                    "reconstructed evaluation boundary"
                )

        else:
            input_boundary = expected_boundary

        # Build scientific payload for root hashing (strictly excluding execution timestamp)
        scientific_payload = {
            "plan_id": plan.plan_id,
            "plan_digest": plan_digest,
            "dataset_digest": dataset_digest,
            "source_lineage_digest": source_lineage_digest,
            "input_boundary_digest": input_boundary.logical_evaluation_digest,
            "candidate_identities": [
                {
                    "candidate_id": c.candidate_id,
                    "identity_hash": c.identity_hash,
                }
                for c in candidate_identities
            ],
            "search_family": search_family.to_canonical_dict() if search_family else None,
            "code_revision": code_revision,
            "per_fold_results": [
                {
                    "candidate_id": r.candidate_id,
                    "role": r.evaluation_role.value,
                    "folds": [
                        {
                            "fold_id": f.fold_id,
                            "metrics": {k: str(v) for k, v in sorted(f.metrics.items())},
                            "sample_count": f.sample_count,
                            "cold_start_count": f.cold_start_count,
                            "effective_counts": {
                                k: v for k, v in sorted(f.metric_effective_counts.items())
                            },
                            "predictions_digest": hashlib.sha256(
                                json.dumps(
                                    [
                                        {
                                            "sample_id": p.sample_id,
                                            "pred_val": (
                                                str(p.predicted_value)
                                                if p.predicted_value is not None
                                                else None
                                            ),
                                            "pred_prob": (
                                                str(p.predicted_probability)
                                                if p.predicted_probability is not None
                                                else None
                                            ),
                                            "pred_cls": p.predicted_class,
                                        }
                                        for p in f.predictions
                                    ],
                                    sort_keys=True,
                                    separators=(",", ":"),
                                ).encode("utf-8")
                            ).hexdigest()
                            if f.predictions
                            else "",
                            "calibration_digest": (
                                hashlib.sha256(
                                    json.dumps(
                                        f.calibration_report.to_canonical_dict()
                                        if hasattr(f.calibration_report, "to_canonical_dict")
                                        else str(f.calibration_report),
                                        sort_keys=True,
                                        separators=(",", ":"),
                                    ).encode("utf-8")
                                ).hexdigest()
                                if f.calibration_report
                                else None
                            ),
                        }
                        for f in r.fold_results
                    ],
                }
                for r in aggregate_results
            ],
            "aggregate_results": [
                {
                    "candidate_id": r.candidate_id,
                    "role": r.evaluation_role.value,
                    "aggregation_policy": r.aggregation_policy.value,
                    "numeric_policy": r.numeric_policy.to_canonical_dict(),
                    "metrics": {k: str(v) for k, v in sorted(r.aggregate_metrics.items())},
                    "total_samples": r.total_samples,
                    "total_cold_starts": r.total_cold_starts,
                    "stability_diagnostics": {
                        k: diag.to_canonical_dict()
                        for k, diag in sorted(r.stability_diagnostics.items())
                    },
                }
                for r in aggregate_results
            ],
            "comparison_results": [
                {
                    "role": cr.evaluation_role.value,
                    "metric_name": cr.metric_name,
                    "rankings": [[cand_id, str(val)] for cand_id, val in cr.rankings],
                    "winner": cr.winner_candidate_id,
                }
                for cr in comparison_results
            ],
        }
        root_serialized = json.dumps(scientific_payload, sort_keys=True, separators=(",", ":"))
        manifest_digest = hashlib.sha256(root_serialized.encode("utf-8")).hexdigest()

        prov = EvaluationProvenanceRecord(
            plan_id=plan.plan_id,
            plan_digest=plan_digest,
            dataset_digest=dataset_digest,
            source_lineage_digest=source_lineage_digest,
            input_boundary_digest=input_boundary.logical_evaluation_digest,
            candidate_identities=tuple(candidate_identities),
            code_revision=code_revision,
            observed_execution_timestamp=execution_timestamp,
            manifest_digest=manifest_digest,
        )

        return cls(
            provenance=prov,
            aggregate_results=tuple(aggregate_results),
            comparison_results=tuple(comparison_results),
            input_boundary=input_boundary,
            search_family=search_family,
        )

    @property
    def manifest_digest(self) -> str:
        """Deterministic scientific digest of the evaluation manifest."""
        return self.provenance.manifest_digest

    @property
    def observed_execution_timestamp(self) -> datetime:
        """Observed execution timestamp of the evaluation manifest."""
        return self.provenance.observed_execution_timestamp

    def verify_manifest_integrity(self) -> bool:
        """Verify that manifest_digest matches the SHA-256 digest of the scientific manifest."""
        scientific_payload = {
            "plan_id": self.provenance.plan_id,
            "plan_digest": self.provenance.plan_digest,
            "dataset_digest": self.provenance.dataset_digest,
            "source_lineage_digest": self.provenance.source_lineage_digest,
            "input_boundary_digest": (
                self.input_boundary.logical_evaluation_digest
                if self.input_boundary
                else self.provenance.input_boundary_digest
            ),
            "candidate_identities": [
                {
                    "candidate_id": c.candidate_id,
                    "identity_hash": c.identity_hash,
                }
                for c in self.provenance.candidate_identities
            ],
            "search_family": self.search_family.to_canonical_dict() if self.search_family else None,
            "code_revision": self.provenance.code_revision,
            "per_fold_results": [
                {
                    "candidate_id": r.candidate_id,
                    "role": r.evaluation_role.value,
                    "folds": [
                        {
                            "fold_id": f.fold_id,
                            "metrics": {k: str(v) for k, v in sorted(f.metrics.items())},
                            "sample_count": f.sample_count,
                            "cold_start_count": f.cold_start_count,
                            "effective_counts": {
                                k: v for k, v in sorted(f.metric_effective_counts.items())
                            },
                            "predictions_digest": hashlib.sha256(
                                json.dumps(
                                    [
                                        {
                                            "sample_id": p.sample_id,
                                            "pred_val": (
                                                str(p.predicted_value)
                                                if p.predicted_value is not None
                                                else None
                                            ),
                                            "pred_prob": (
                                                str(p.predicted_probability)
                                                if p.predicted_probability is not None
                                                else None
                                            ),
                                            "pred_cls": p.predicted_class,
                                        }
                                        for p in f.predictions
                                    ],
                                    sort_keys=True,
                                    separators=(",", ":"),
                                ).encode("utf-8")
                            ).hexdigest()
                            if f.predictions
                            else "",
                            "calibration_digest": (
                                hashlib.sha256(
                                    json.dumps(
                                        f.calibration_report.to_canonical_dict()
                                        if hasattr(f.calibration_report, "to_canonical_dict")
                                        else str(f.calibration_report),
                                        sort_keys=True,
                                        separators=(",", ":"),
                                    ).encode("utf-8")
                                ).hexdigest()
                                if f.calibration_report
                                else None
                            ),
                        }
                        for f in r.fold_results
                    ],
                }
                for r in self.aggregate_results
            ],
            "aggregate_results": [
                {
                    "candidate_id": r.candidate_id,
                    "role": r.evaluation_role.value,
                    "aggregation_policy": r.aggregation_policy.value,
                    "numeric_policy": r.numeric_policy.to_canonical_dict(),
                    "metrics": {k: str(v) for k, v in sorted(r.aggregate_metrics.items())},
                    "total_samples": r.total_samples,
                    "total_cold_starts": r.total_cold_starts,
                    "stability_diagnostics": {
                        k: diag.to_canonical_dict()
                        for k, diag in sorted(r.stability_diagnostics.items())
                    },
                }
                for r in self.aggregate_results
            ],
            "comparison_results": [
                {
                    "role": cr.evaluation_role.value,
                    "metric_name": cr.metric_name,
                    "rankings": [[cand_id, str(val)] for cand_id, val in cr.rankings],
                    "winner": cr.winner_candidate_id,
                }
                for cr in self.comparison_results
            ],
        }
        root_serialized = json.dumps(scientific_payload, sort_keys=True, separators=(",", ":"))
        expected_digest = hashlib.sha256(root_serialized.encode("utf-8")).hexdigest()
        return expected_digest == self.provenance.manifest_digest

    def to_canonical_dict(self) -> dict[str, Any]:
        """Convert manifest to canonical dictionary representation."""
        return {
            "manifest_digest": self.provenance.manifest_digest,
            "plan_id": self.provenance.plan_id,
            "plan_digest": self.provenance.plan_digest,
            "dataset_digest": self.provenance.dataset_digest,
            "source_lineage_digest": self.provenance.source_lineage_digest,
            "input_boundary_digest": self.provenance.input_boundary_digest,
            "code_revision": self.provenance.code_revision,
            "observed_execution_timestamp": (
                self.provenance.observed_execution_timestamp.isoformat()
            ),
            "search_family": self.search_family.to_canonical_dict() if self.search_family else None,
            "candidate_identities": [
                {
                    "candidate_id": c.candidate_id,
                    "baseline_type": c.baseline_type,
                    "identity_hash": c.identity_hash,
                }
                for c in self.provenance.candidate_identities
            ],
            "aggregate_results": [
                {
                    "candidate_id": r.candidate_id,
                    "role": r.evaluation_role.value,
                    "aggregation_policy": r.aggregation_policy.value,
                    "aggregate_metrics": {
                        k: str(v) for k, v in sorted(r.aggregate_metrics.items())
                    },
                    "total_samples": r.total_samples,
                    "total_cold_starts": r.total_cold_starts,
                    "stability_diagnostics": {
                        k: diag.to_canonical_dict()
                        for k, diag in sorted(r.stability_diagnostics.items())
                    },
                }
                for r in self.aggregate_results
            ],
            "comparison_results": [
                {
                    "role": cr.evaluation_role.value,
                    "metric_name": cr.metric_name,
                    "rankings": [[c, str(m)] for c, m in cr.rankings],
                    "winner_candidate_id": cr.winner_candidate_id,
                }
                for cr in self.comparison_results
            ],
        }
