"""Candidate comparison, search families, and protected test non-selection invariants."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from btg_ai_trader.statistical_baselines.domain import (
    CandidateIdentity,
    EvaluationRole,
    ParityViolationError,
    ProtectedEvidenceReuseError,
    TargetSemantics,
    _freeze_mapping,
)
from btg_ai_trader.statistical_baselines.evaluation import (
    AggregateEvaluationResult,
)


@dataclass(frozen=True, slots=True)
class SearchFamily:
    """A collection of candidate models with complete search lineage and provenance."""

    family_name: str
    target_semantics: TargetSemantics
    candidates: tuple[CandidateIdentity, ...]
    description: str = ""
    candidate_ids_considered: tuple[str, ...] = ()
    configurations_considered: tuple[Mapping[str, Any], ...] = ()
    selection_domain: str = ""
    selection_metric: str = ""
    baseline_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.family_name:
            raise ValueError("family_name cannot be empty")
        if not self.candidates:
            raise ValueError("candidates cannot be empty")
        for c in self.candidates:
            if c.target_semantics != self.target_semantics:
                raise ValueError(
                    f"Candidate {c.candidate_id} semantics {c.target_semantics} does not match "
                    f"family target semantics {self.target_semantics}"
                )

        if not self.candidate_ids_considered:
            object.__setattr__(
                self, "candidate_ids_considered", tuple(c.candidate_id for c in self.candidates)
            )
        if not self.configurations_considered:
            object.__setattr__(
                self,
                "configurations_considered",
                tuple(c.parameters for c in self.candidates),
            )
        else:
            object.__setattr__(
                self,
                "configurations_considered",
                tuple(_freeze_mapping(cfg) for cfg in self.configurations_considered),
            )
        if not self.baseline_ids:
            object.__setattr__(
                self,
                "baseline_ids",
                tuple(sorted({c.baseline_type for c in self.candidates})),
            )

    def to_canonical_dict(self) -> dict[str, Any]:
        """Convert SearchFamily to canonical dictionary representation for manifests."""
        return {
            "family_name": self.family_name,
            "target_semantics": self.target_semantics.value,
            "description": self.description,
            "candidate_ids_considered": list(self.candidate_ids_considered),
            "configurations_considered": [
                dict(cfg) for cfg in self.configurations_considered
            ],
            "selection_domain": self.selection_domain,
            "selection_metric": self.selection_metric,
            "baseline_ids": list(self.baseline_ids),
        }


@dataclass(frozen=True, slots=True)
class ProtectedEvidenceUse:
    """Record of an evaluation of a candidate on a protected boundary."""

    candidate_id: str
    protected_boundary_id: str
    evaluation_role: EvaluationRole
    informed_adaptation: bool = False
    parent_candidate_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProtectedEvidenceConsumption:
    """Record that protected evidence was consumed to derive a new candidate."""

    protected_boundary_id: str
    source_candidate_id: str
    derived_candidate_id: str


class EvaluationHistory:
    """Tracks protected evaluations and later evidence consumption across candidate lineage."""

    def __init__(
        self,
        records: Sequence[ProtectedEvidenceUse] = (),
        consumptions: Sequence[ProtectedEvidenceConsumption] = (),
    ) -> None:
        self._records: list[ProtectedEvidenceUse] = list(records)
        self._consumptions: list[ProtectedEvidenceConsumption] = list(consumptions)

    @property
    def records(self) -> tuple[ProtectedEvidenceUse, ...]:
        return tuple(self._records)

    @property
    def consumptions(self) -> tuple[ProtectedEvidenceConsumption, ...]:
        return tuple(self._consumptions)

    def record_evaluation(
        self,
        candidate_id: str,
        protected_boundary_id: str,
        role: EvaluationRole,
        informed_adaptation: bool = False,
        parent_candidate_ids: tuple[str, ...] = (),
    ) -> None:
        """Record an evaluation event in historical provenance."""
        record = ProtectedEvidenceUse(
            candidate_id=candidate_id,
            protected_boundary_id=protected_boundary_id,
            evaluation_role=role,
            informed_adaptation=informed_adaptation,
            parent_candidate_ids=tuple(parent_candidate_ids),
        )
        self._records.append(record)

    def record_protected_evidence_consumption(
        self,
        protected_boundary_id: str,
        source_candidate_id: str,
        derived_candidate_id: str,
    ) -> None:
        """Record that evidence from a protected evaluation informed a derived candidate."""
        if not protected_boundary_id or not source_candidate_id or not derived_candidate_id:
            raise ValueError(
                "protected_boundary_id, source_candidate_id, and derived_candidate_id are required"
            )
        source_was_evaluated = any(
            rec.protected_boundary_id == protected_boundary_id
            and rec.candidate_id == source_candidate_id
            and rec.evaluation_role is EvaluationRole.PROTECTED_TEST
            for rec in self._records
        )
        if not source_was_evaluated:
            raise ValueError(
                f"Cannot consume protected evidence for candidate {source_candidate_id}: "
                f"no protected evaluation recorded on boundary {protected_boundary_id}"
            )
        self._consumptions.append(
            ProtectedEvidenceConsumption(
                protected_boundary_id=protected_boundary_id,
                source_candidate_id=source_candidate_id,
                derived_candidate_id=derived_candidate_id,
            )
        )

    def check_admissibility(
        self,
        candidate_id: str,
        protected_boundary_id: str,
        role: EvaluationRole,
        parent_candidate_ids: tuple[str, ...] = (),
    ) -> None:
        """Validate that candidate is epistemologically admissible on protected boundary."""
        if role is not EvaluationRole.PROTECTED_TEST:
            return

        for consumption in self._consumptions:
            if (
                consumption.protected_boundary_id == protected_boundary_id
                and consumption.derived_candidate_id == candidate_id
            ):
                raise ProtectedEvidenceReuseError(
                    f"Protected evidence reuse violation: candidate {candidate_id} was derived "
                    f"using evidence from boundary {protected_boundary_id} consumed by "
                    f"parent {consumption.source_candidate_id}"
                )

        # Backward-compatible guard for records that explicitly marked adaptation at evaluation time.
        for rec in self._records:
            if (
                rec.protected_boundary_id == protected_boundary_id
                and rec.evaluation_role is EvaluationRole.PROTECTED_TEST
            ):
                if rec.candidate_id == candidate_id and rec.informed_adaptation:
                    raise ProtectedEvidenceReuseError(
                        f"Protected evidence reuse violation: candidate {candidate_id} was already "
                        f"evaluated on boundary {protected_boundary_id} and informed adaptation"
                    )
                if rec.informed_adaptation and rec.candidate_id in parent_candidate_ids:
                    raise ProtectedEvidenceReuseError(
                        f"Protected evidence reuse violation: candidate {candidate_id} was adapted "
                        f"from parent {rec.candidate_id} which consumed protected boundary "
                        f"{protected_boundary_id} (Protocol 0E-C, C-HQI-08, S4-NC-17)"
                    )


@dataclass(frozen=True, slots=True)
class ModelComparisonResult:
    """Ranked comparison of candidates across temporal evaluation folds."""

    evaluation_role: EvaluationRole
    metric_name: str
    higher_is_better: bool
    rankings: tuple[tuple[str, Decimal], ...]
    winner_candidate_id: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.rankings:
            raise ValueError("rankings cannot be empty")
        # Invariant: PROTECTED_TEST must never have a winner populated
        if (
            self.evaluation_role is EvaluationRole.PROTECTED_TEST
            and self.winner_candidate_id is not None
        ):
            raise ValueError(
                "winner_candidate_id must be None for PROTECTED_TEST evaluation role "
                "(Protocol 0E-C, C-HQI-08, S4-NC-17)"
            )
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


class Comparator:
    """Comparator ranking candidate models with strict protected test safety guarantees and full
    parity checks.
    """

    @classmethod
    def compare_candidates(
        cls,
        results: Sequence[AggregateEvaluationResult],
        metric_name: str,
        higher_is_better: bool = False,
    ) -> ModelComparisonResult:
        """Rank candidates based on aggregate metric, enforcing role invariants and full parity."""
        if not results:
            raise ValueError("Cannot compare empty results sequence")

        first = results[0]
        first_role = first.evaluation_role
        first_fold_ids = [f.fold_id for f in first.fold_results]
        first_fp = first.evaluation_context_fingerprint
        first_agg_policy = first.aggregation_policy
        first_numeric_policy = first.numeric_policy

        # Verify experimental parity: all candidates must have identical experimental context
        for r in results:
            if r.evaluation_role != first_role:
                raise ParityViolationError(
                    f"Mixed evaluation roles in comparison: {r.evaluation_role} != {first_role}"
                )
            r_fold_ids = [f.fold_id for f in r.fold_results]
            if r_fold_ids != first_fold_ids:
                raise ParityViolationError(
                    f"Experimental parity violation: candidate {r.candidate_id} evaluated on folds "
                    f"{r_fold_ids}, expected {first_fold_ids}"
                )
            if r.aggregation_policy != first_agg_policy:
                raise ParityViolationError(
                    f"Experimental parity violation: aggregation policies differ "
                    f"({r.aggregation_policy} != {first_agg_policy})"
                )
            if r.numeric_policy != first_numeric_policy:
                raise ParityViolationError(
                    f"Experimental parity violation: numeric policies differ "
                    f"({r.numeric_policy} != {first_numeric_policy})"
                )
            if r.evaluation_context_fingerprint != first_fp:
                raise ParityViolationError(
                    f"NOT_COMPARABLE: Evaluation context parity mismatch between {r.candidate_id} "
                    f"and {first.candidate_id}"
                )
            if metric_name not in r.aggregate_metrics:
                raise ValueError(
                    f"Metric {metric_name} missing from candidate {r.candidate_id} "
                    f"aggregate metrics"
                )

        # Sort candidates deterministically: by metric value, tie-broken by candidate_id
        def sort_key(res: AggregateEvaluationResult) -> tuple[Decimal, str]:
            val = res.aggregate_metrics[metric_name]
            return (-val if higher_is_better else val, res.candidate_id)

        sorted_results = sorted(results, key=sort_key)
        rankings = tuple(
            (r.candidate_id, r.aggregate_metrics[metric_name]) for r in sorted_results
        )

        # Invariant: Never select or identify a winner on PROTECTED_TEST
        if first_role is EvaluationRole.PROTECTED_TEST:
            winner_id = None
        else:
            winner_id = rankings[0][0]

        return ModelComparisonResult(
            evaluation_role=first_role,
            metric_name=metric_name,
            higher_is_better=higher_is_better,
            rankings=rankings,
            winner_candidate_id=winner_id,
        )

    @classmethod
    def select_best_candidate(cls, comparison_result: ModelComparisonResult) -> str:
        """Select the best candidate from comparison result, strictly rejecting PROTECTED_TEST."""
        if comparison_result.evaluation_role is EvaluationRole.PROTECTED_TEST:
            raise ValueError(
                "Selecting a winner or promoting a candidate based on PROTECTED_TEST evaluation "
                "is strictly forbidden (Protocol 0E-C, C-HQI-08, S4-NC-17)"
            )
        if comparison_result.winner_candidate_id is None:
            raise ValueError("Comparison result does not have an admissible winner candidate")
        return comparison_result.winner_candidate_id
