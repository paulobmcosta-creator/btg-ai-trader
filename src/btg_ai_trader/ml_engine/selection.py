"""Finite search spaces, immutable search history, and validation-only selection."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from btg_ai_trader.ml_engine.domain import MetricDirection, MLCandidateSpec
from btg_ai_trader.statistical_baselines.domain import EvaluationRole, _freeze_mapping


def _seed_independent_key(candidate: MLCandidateSpec) -> str:
    payload = {
        "code_revision": candidate.code_revision,
        "family": candidate.family,
        "feature_pipeline_spec_digest": candidate.feature_pipeline_spec_digest,
        "hyperparameters": dict(candidate.hyperparameters),
        "numeric_policy": candidate.numeric_policy.to_canonical_dict(),
        "target_contract_digest": candidate.target_contract.contract_digest,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ModelComplexityDescriptor:
    """Factual complexity descriptors; no universal penalty is implied."""

    family: str
    feature_count: int
    parameter_count: int | None = None
    tree_count: int | None = None
    max_depth: int | None = None

    def __post_init__(self) -> None:
        if not self.family:
            raise ValueError("family must be non-empty")
        if self.feature_count < 0:
            raise ValueError("feature_count cannot be negative")

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "feature_count": self.feature_count,
            "max_depth": self.max_depth,
            "parameter_count": self.parameter_count,
            "tree_count": self.tree_count,
        }


@dataclass(frozen=True, slots=True)
class ModelSearchSpace:
    """Finite predeclared candidate set with structural best-seed rejection."""

    candidates: tuple[MLCandidateSpec, ...]
    max_candidates_limit: int = 100
    search_space_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.candidates:
            raise ValueError("ModelSearchSpace cannot be empty")
        if self.max_candidates_limit <= 0:
            raise ValueError("max_candidates_limit must be positive")
        if len(self.candidates) > self.max_candidates_limit:
            raise ValueError(
                f"Candidate count {len(self.candidates)} exceeds limit "
                f"{self.max_candidates_limit}"
            )
        ordered = tuple(sorted(self.candidates, key=lambda item: item.candidate_id))
        candidate_ids = [candidate.candidate_id for candidate in ordered]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("ModelSearchSpace cannot contain duplicate candidates")

        seed_groups: dict[str, set[int | None]] = {}
        for candidate in ordered:
            seed = candidate.rng_context.seed if candidate.rng_context else None
            seed_groups.setdefault(_seed_independent_key(candidate), set()).add(seed)
        if any(len(seeds) > 1 for seeds in seed_groups.values()):
            raise ValueError(
                "Search space attempts best-seed selection: candidates that differ only "
                "by random seed are forbidden in Sprint 5"
            )

        object.__setattr__(self, "candidates", ordered)
        serialized = json.dumps(
            [candidate.spec_digest for candidate in ordered],
            separators=(",", ":"),
        )
        object.__setattr__(
            self,
            "search_space_digest",
            hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        )

    def __len__(self) -> int:
        return len(self.candidates)


@dataclass(frozen=True, slots=True)
class SearchAttemptRecord:
    """Immutable evidence for one fit/evaluation attempt."""

    candidate_spec: MLCandidateSpec
    fit_status: str
    evaluation_role: EvaluationRole
    evaluation_context_fingerprint: str
    failure_reason: str | None = None
    validation_metrics: Mapping[str, Decimal] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.fit_status not in {"SUCCESS", "FAILED"}:
            raise ValueError("fit_status must be 'SUCCESS' or 'FAILED'")
        if self.fit_status == "SUCCESS" and not self.evaluation_context_fingerprint:
            raise ValueError(
                "successful search records require evaluation_context_fingerprint"
            )
        object.__setattr__(
            self,
            "validation_metrics",
            _freeze_mapping(dict(self.validation_metrics)),
        )


@dataclass(slots=True)
class ModelSearchHistory:
    """Append-only attempt history bound to one immutable search space."""

    search_space: ModelSearchSpace
    _records: list[SearchAttemptRecord] = field(default_factory=list)

    @property
    def search_space_digest(self) -> str:
        return self.search_space.search_space_digest

    @property
    def records(self) -> tuple[SearchAttemptRecord, ...]:
        return tuple(self._records)

    def record_attempt(
        self,
        *,
        candidate_spec: MLCandidateSpec,
        fit_status: str,
        evaluation_role: EvaluationRole,
        evaluation_context_fingerprint: str = "",
        failure_reason: str | None = None,
        validation_metrics: Mapping[str, Decimal] | None = None,
    ) -> None:
        allowed_ids = {candidate.candidate_id for candidate in self.search_space.candidates}
        if candidate_spec.candidate_id not in allowed_ids:
            raise ValueError("candidate is not a member of the bound ModelSearchSpace")
        self._records.append(
            SearchAttemptRecord(
                candidate_spec=candidate_spec,
                fit_status=fit_status,
                evaluation_role=evaluation_role,
                evaluation_context_fingerprint=evaluation_context_fingerprint,
                failure_reason=failure_reason,
                validation_metrics=dict(validation_metrics or {}),
            )
        )

    @property
    def total_attempts(self) -> int:
        return len(self._records)

    @property
    def successful_attempts(self) -> int:
        return sum(record.fit_status == "SUCCESS" for record in self._records)

    @property
    def failed_attempts(self) -> int:
        return sum(record.fit_status == "FAILED" for record in self._records)


@dataclass(frozen=True, slots=True)
class ModelSelectionPolicy:
    """Select a candidate only from validation-selection evidence."""

    metric_name: str
    direction: MetricDirection

    def __post_init__(self) -> None:
        if not self.metric_name:
            raise ValueError("metric_name must be a non-empty string")
        if not isinstance(self.direction, MetricDirection):
            raise TypeError(f"direction must be MetricDirection, got {type(self.direction)}")

    def select_best(self, history: ModelSearchHistory) -> MLCandidateSpec:
        eligible = [
            record
            for record in history.records
            if record.fit_status == "SUCCESS"
            and self.metric_name in record.validation_metrics
        ]
        if not eligible:
            raise ValueError(
                f"No successful candidates with metric '{self.metric_name}'"
            )
        if any(
            record.evaluation_role is not EvaluationRole.VALIDATION_SELECTION
            for record in eligible
        ):
            raise ValueError(
                "Model selection may use VALIDATION_SELECTION evidence only; "
                "protected/training evidence is forbidden"
            )
        contexts = {
            record.evaluation_context_fingerprint for record in eligible
        }
        if len(contexts) != 1:
            raise ValueError(
                "Model selection requires one identical validation experimental context"
            )

        def sort_key(record: SearchAttemptRecord) -> tuple[Decimal, str]:
            value = record.validation_metrics[self.metric_name]
            ordered = value if self.direction is MetricDirection.MINIMIZE else -value
            return (ordered, record.candidate_spec.candidate_id)

        return sorted(eligible, key=sort_key)[0].candidate_spec
