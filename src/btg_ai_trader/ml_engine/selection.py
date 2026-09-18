"""Finite candidate search space, append-only history, and validation-only selection."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from btg_ai_trader.ml_engine.domain import (
    MetricDirection,
    MLCandidateSpec,
)


@dataclass(frozen=True, slots=True)
class ModelComplexityDescriptor:
    """Factual complexity metrics for a candidate specification."""

    family: str
    feature_count: int
    parameter_count: int | None = None
    tree_count: int | None = None
    max_depth: int | None = None

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
    """Predeclared, finite, content-addressed collection of candidate specifications."""

    candidates: tuple[MLCandidateSpec, ...]
    search_space_digest: str = field(init=False)
    max_candidates_limit: int = 100

    def __post_init__(self) -> None:
        if not self.candidates:
            raise ValueError("ModelSearchSpace cannot be empty")
        if len(self.candidates) > self.max_candidates_limit:
            raise ValueError(
                f"Candidate count {len(self.candidates)} exceeds limit {self.max_candidates_limit}"
            )

        # Enforce canonical ordering by candidate_id
        sorted_candidates = tuple(sorted(self.candidates, key=lambda c: c.candidate_id))
        object.__setattr__(self, "candidates", sorted_candidates)

        canonical_ids = [c.spec_digest for c in sorted_candidates]
        serialized = json.dumps(canonical_ids, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        object.__setattr__(self, "search_space_digest", digest)

    def __len__(self) -> int:
        return len(self.candidates)


@dataclass(frozen=True, slots=True)
class SearchAttemptRecord:
    """Record of an individual candidate training and validation attempt."""

    candidate_spec: MLCandidateSpec
    fit_status: str  # "SUCCESS" or "FAILED"
    failure_reason: str | None = None
    validation_metrics: dict[str, Decimal] = field(default_factory=dict)
    replicate_group_id: str | None = None


@dataclass(slots=True)
class ModelSearchHistory:
    """Append-only history tracking all explored candidates, configurations, and failures."""

    search_space_digest: str
    _records: list[SearchAttemptRecord] = field(default_factory=list)

    @property
    def records(self) -> tuple[SearchAttemptRecord, ...]:
        return tuple(self._records)

    def record_attempt(
        self,
        candidate_spec: MLCandidateSpec,
        fit_status: str,
        failure_reason: str | None = None,
        validation_metrics: dict[str, Decimal] | None = None,
        replicate_group_id: str | None = None,
    ) -> None:
        """Append an attempt to the history. Failures must never be discarded."""
        if fit_status not in ("SUCCESS", "FAILED"):
            raise ValueError(f"fit_status must be 'SUCCESS' or 'FAILED', got '{fit_status}'")

        self._records.append(
            SearchAttemptRecord(
                candidate_spec=candidate_spec,
                fit_status=fit_status,
                failure_reason=failure_reason,
                validation_metrics=dict(validation_metrics) if validation_metrics else {},
                replicate_group_id=replicate_group_id,
            )
        )

    @property
    def total_attempts(self) -> int:
        return len(self._records)

    @property
    def successful_attempts(self) -> int:
        return sum(1 for r in self._records if r.fit_status == "SUCCESS")

    @property
    def failed_attempts(self) -> int:
        return sum(1 for r in self._records if r.fit_status == "FAILED")


@dataclass(frozen=True, slots=True)
class ModelSelectionPolicy:
    """Policy governing candidate selection strictly on validation domain evidence."""

    metric_name: str
    direction: MetricDirection
    penalize_complexity: bool = False

    def __post_init__(self) -> None:
        if not self.metric_name:
            raise ValueError("metric_name must be a non-empty string")
        if not isinstance(self.direction, MetricDirection):
            raise TypeError(f"direction must be MetricDirection, got {type(self.direction)}")

    @staticmethod
    def assert_no_best_seed_selection(search_space: ModelSearchSpace) -> None:
        """Adversarial check: reject search space if identical candidates differ only by seed."""
        configs: dict[str, list[int]] = {}
        for cand in search_space.candidates:
            # Hash configuration excluding seed
            config_key = f"{cand.family}:{json.dumps(dict(cand.hyperparameters), sort_keys=True)}"
            seed = cand.rng_context.seed if cand.rng_context else 0
            configs.setdefault(config_key, []).append(seed)

        for config_key, seeds in configs.items():
            if len(seeds) > 1 and len(set(seeds)) > 1:
                raise ValueError(
                    f"Search space attempts to select best seed across identical "
                    f"configuration {config_key}: seeds={seeds}. "
                    f"Seed cherry-picking is strictly prohibited."
                )

    def select_best(
        self,
        history: ModelSearchHistory,
    ) -> MLCandidateSpec:
        """Select the best candidate from validation search history."""
        successful_records = [
            r
            for r in history.records
            if r.fit_status == "SUCCESS" and self.metric_name in r.validation_metrics
        ]

        if not successful_records:
            raise ValueError(
                f"No successful candidates in search history with metric '{self.metric_name}'"
            )

        # Deterministic sorting: primary = metric value, secondary = candidate_id
        def sort_key(rec: SearchAttemptRecord) -> tuple[Decimal, str]:
            val = rec.validation_metrics[self.metric_name]
            metric_order = val if self.direction is MetricDirection.MINIMIZE else -val
            return (metric_order, rec.candidate_spec.candidate_id)

        sorted_records = sorted(successful_records, key=sort_key)
        return sorted_records[0].candidate_spec
