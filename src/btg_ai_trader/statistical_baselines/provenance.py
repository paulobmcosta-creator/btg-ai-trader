"""Evaluation provenance, input boundary validation, and cryptographically verifiable manifests."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from btg_ai_trader.statistical_baselines.boundaries import WalkForwardPlan
from btg_ai_trader.statistical_baselines.comparison import ModelComparisonResult
from btg_ai_trader.statistical_baselines.domain import (
    CandidateIdentity,
    StatisticalSample,
    _validate_timezone_aware,
)
from btg_ai_trader.statistical_baselines.evaluation import AggregateEvaluationResult


class StatisticalEvaluationInputBoundary:
    """Read-only boundary verifying market sample datasets before kernel consumption."""

    @classmethod
    def compute_dataset_digest(cls, samples: Sequence[StatisticalSample]) -> str:
        """Compute canonical SHA-256 digest of sample sequence."""
        canonical_items = [
            {
                "sample_id": s.sample_id,
                "feature_knowledge_time": s.feature_knowledge_time.isoformat(),
                "target_knowledge_time": s.target_knowledge_time.isoformat(),
                "target_value": str(s.target_value),
                "target_semantics": s.target_semantics.value,
                "information_interval": (
                    [s.information_interval[0].isoformat(), s.information_interval[1].isoformat()]
                    if s.information_interval is not None
                    else None
                ),
            }
            for s in samples
        ]
        serialized = json.dumps(canonical_items, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def validate_dataset(
        cls, samples: Sequence[StatisticalSample]
    ) -> tuple[StatisticalSample, ...]:
        """Validate input dataset, enforcing uniqueness, causality, and canonical sorting."""
        if not samples:
            raise ValueError("Input sample dataset cannot be empty")

        seen_ids: set[str] = set()
        for s in samples:
            if s.sample_id in seen_ids:
                raise ValueError(f"Duplicate sample_id rejected: {s.sample_id}")
            seen_ids.add(s.sample_id)
            if s.feature_knowledge_time > s.target_knowledge_time:
                raise ValueError(
                    f"Sample {s.sample_id}: feature_knowledge_time cannot be after "
                    f"target_knowledge_time"
                )

        # Sort canonically by (feature_knowledge_time, target_knowledge_time, sample_id)
        sorted_samples = tuple(
            sorted(
                samples,
                key=lambda s: (s.feature_knowledge_time, s.target_knowledge_time, s.sample_id),
            )
        )
        return sorted_samples


@dataclass(frozen=True, slots=True)
class EvaluationProvenanceRecord:
    """Cryptographically verifiable provenance record describing experimental lineage."""

    plan_id: str
    plan_digest: str
    dataset_digest: str
    candidate_identities: tuple[CandidateIdentity, ...]
    code_revision: str
    execution_timestamp: datetime
    manifest_digest: str

    def __post_init__(self) -> None:
        if not self.plan_id:
            raise ValueError("plan_id cannot be empty")
        if not self.plan_digest:
            raise ValueError("plan_digest cannot be empty")
        if not self.dataset_digest:
            raise ValueError("dataset_digest cannot be empty")
        if not self.code_revision:
            raise ValueError("code_revision cannot be empty")
        if not self.manifest_digest:
            raise ValueError("manifest_digest cannot be empty")
        _validate_timezone_aware(self.execution_timestamp, "execution_timestamp")


@dataclass(frozen=True, slots=True)
class StatisticalEvaluationManifest:
    """Canonical verifiable evaluation manifest capturing complete experimental lineage."""

    provenance: EvaluationProvenanceRecord
    aggregate_results: tuple[AggregateEvaluationResult, ...]
    comparison_results: tuple[ModelComparisonResult, ...]

    @classmethod
    def compute_plan_digest(cls, plan: WalkForwardPlan) -> str:
        """Compute SHA-256 digest for a walk forward plan."""
        plan_dict = {
            "plan_id": plan.plan_id,
            "window_policy": plan.window_policy_name,
            "folds": [
                {
                    "fold_id": f.fold_id,
                    "train_start": f.training_boundary.start_time.isoformat(),
                    "train_end": f.training_boundary.end_time.isoformat(),
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
                    "eval_start": f.protected_evaluation_boundary.start_time.isoformat(),
                    "eval_end": f.protected_evaluation_boundary.end_time.isoformat(),
                    "knowledge_cutoff": f.knowledge_cutoff.isoformat(),
                }
                for f in plan.folds
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
    ) -> StatisticalEvaluationManifest:
        """Create a complete evaluation manifest with verified cryptographic root digest."""
        _validate_timezone_aware(execution_timestamp, "execution_timestamp")
        valid_samples = StatisticalEvaluationInputBoundary.validate_dataset(samples)
        plan_digest = cls.compute_plan_digest(plan)
        dataset_digest = StatisticalEvaluationInputBoundary.compute_dataset_digest(valid_samples)

        # Build partial payload for root hashing
        payload = {
            "plan_id": plan.plan_id,
            "plan_digest": plan_digest,
            "dataset_digest": dataset_digest,
            "candidate_identities": [
                {
                    "candidate_id": c.candidate_id,
                    "identity_hash": c.identity_hash,
                }
                for c in candidate_identities
            ],
            "code_revision": code_revision,
            "execution_timestamp": execution_timestamp.isoformat(),
            "aggregate_results": [
                {
                    "candidate_id": r.candidate_id,
                    "role": r.evaluation_role.value,
                    "metrics": {k: str(v) for k, v in sorted(r.aggregate_metrics.items())},
                    "total_samples": r.total_samples,
                    "total_cold_starts": r.total_cold_starts,
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
        root_serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        manifest_digest = hashlib.sha256(root_serialized.encode("utf-8")).hexdigest()

        prov = EvaluationProvenanceRecord(
            plan_id=plan.plan_id,
            plan_digest=plan_digest,
            dataset_digest=dataset_digest,
            candidate_identities=tuple(candidate_identities),
            code_revision=code_revision,
            execution_timestamp=execution_timestamp,
            manifest_digest=manifest_digest,
        )

        return cls(
            provenance=prov,
            aggregate_results=tuple(aggregate_results),
            comparison_results=tuple(comparison_results),
        )

    def verify_manifest_integrity(self) -> bool:
        """Verify that manifest_digest matches the SHA-256 digest of the manifest contents."""
        payload = {
            "plan_id": self.provenance.plan_id,
            "plan_digest": self.provenance.plan_digest,
            "dataset_digest": self.provenance.dataset_digest,
            "candidate_identities": [
                {
                    "candidate_id": c.candidate_id,
                    "identity_hash": c.identity_hash,
                }
                for c in self.provenance.candidate_identities
            ],
            "code_revision": self.provenance.code_revision,
            "execution_timestamp": self.provenance.execution_timestamp.isoformat(),
            "aggregate_results": [
                {
                    "candidate_id": r.candidate_id,
                    "role": r.evaluation_role.value,
                    "metrics": {k: str(v) for k, v in sorted(r.aggregate_metrics.items())},
                    "total_samples": r.total_samples,
                    "total_cold_starts": r.total_cold_starts,
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
        root_serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        expected_digest = hashlib.sha256(root_serialized.encode("utf-8")).hexdigest()
        return expected_digest == self.provenance.manifest_digest

    def to_canonical_dict(self) -> dict[str, Any]:
        """Convert manifest to canonical dictionary representation."""
        return {
            "manifest_digest": self.provenance.manifest_digest,
            "plan_id": self.provenance.plan_id,
            "plan_digest": self.provenance.plan_digest,
            "dataset_digest": self.provenance.dataset_digest,
            "code_revision": self.provenance.code_revision,
            "execution_timestamp": self.provenance.execution_timestamp.isoformat(),
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
                    "aggregate_metrics": {
                        k: str(v) for k, v in sorted(r.aggregate_metrics.items())
                    },
                    "total_samples": r.total_samples,
                    "total_cold_starts": r.total_cold_starts,
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
