"""Candidate comparison, search families, and protected test non-selection invariants."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from btg_ai_trader.statistical_baselines.domain import (
    CandidateIdentity,
    EvaluationRole,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.evaluation import (
    AggregateEvaluationResult,
)


@dataclass(frozen=True, slots=True)
class SearchFamily:
    """A collection of candidate models belonging to the same architectural or baseline family."""

    family_name: str
    target_semantics: TargetSemantics
    candidates: tuple[CandidateIdentity, ...]
    description: str = ""

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


class Comparator:
    """Comparator ranking candidate models with strict protected test safety guarantees."""

    @classmethod
    def compare_candidates(
        cls,
        results: Sequence[AggregateEvaluationResult],
        metric_name: str,
        higher_is_better: bool = False,
    ) -> ModelComparisonResult:
        """Rank candidates based on aggregate metric, enforcing role invariants and parity."""
        if not results:
            raise ValueError("Cannot compare empty results sequence")

        first_role = results[0].evaluation_role
        first_fold_ids = [f.fold_id for f in results[0].fold_results]

        # Verify experimental parity: all candidates must be evaluated on the same folds & role
        for r in results:
            if r.evaluation_role != first_role:
                raise ValueError(
                    f"Mixed evaluation roles in comparison: {r.evaluation_role} != {first_role}"
                )
            r_fold_ids = [f.fold_id for f in r.fold_results]
            if r_fold_ids != first_fold_ids:
                raise ValueError(
                    f"Experimental parity violation: candidate {r.candidate_id} evaluated on folds "
                    f"{r_fold_ids}, expected {first_fold_ids}"
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
