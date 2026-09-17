"""Unit tests for model comparison, search families, and protected test invariants."""

from decimal import Decimal

import pytest

from btg_ai_trader.statistical_baselines.comparison import (
    Comparator,
    ModelComparisonResult,
    SearchFamily,
)
from btg_ai_trader.statistical_baselines.domain import (
    CandidateIdentity,
    EvaluationRole,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.evaluation import (
    AggregateEvaluationResult,
    FoldEvaluationResult,
)


def _make_candidate(
    name: str, semantics: TargetSemantics = TargetSemantics.CONTINUOUS
) -> CandidateIdentity:
    return CandidateIdentity(
        baseline_type=name,
        parameters={},
        target_semantics=semantics,
        code_revision="v1.0.0",
    )


def _make_aggregate_result(
    candidate_id: str,
    role: EvaluationRole,
    fold_ids: list[str],
    metrics: dict[str, Decimal],
) -> AggregateEvaluationResult:
    fold_res = [
        FoldEvaluationResult(
            fold_id=fid,
            candidate_id=candidate_id,
            evaluation_role=role,
            metrics=metrics,
            sample_count=10,
            cold_start_count=0,
        )
        for fid in fold_ids
    ]
    return AggregateEvaluationResult(
        candidate_id=candidate_id,
        evaluation_role=role,
        fold_results=tuple(fold_res),
        aggregate_metrics=metrics,
        total_samples=len(fold_ids) * 10,
        total_cold_starts=0,
    )


def test_search_family_validation() -> None:
    c1 = _make_candidate("c1", TargetSemantics.CONTINUOUS)
    c2 = _make_candidate("c2", TargetSemantics.CONTINUOUS)
    c_bin = _make_candidate("c_bin", TargetSemantics.BINARY_PROBABILITY)

    with pytest.raises(ValueError, match="family_name cannot be empty"):
        SearchFamily(family_name="", target_semantics=TargetSemantics.CONTINUOUS, candidates=(c1,))

    with pytest.raises(ValueError, match="candidates cannot be empty"):
        SearchFamily(family_name="fam", target_semantics=TargetSemantics.CONTINUOUS, candidates=())

    with pytest.raises(ValueError, match="does not match family target semantics"):
        SearchFamily(
            family_name="fam",
            target_semantics=TargetSemantics.CONTINUOUS,
            candidates=(c1, c_bin),
        )

    fam = SearchFamily(
        family_name="baselines",
        target_semantics=TargetSemantics.CONTINUOUS,
        candidates=(c1, c2),
        description="Continuous baselines",
    )
    assert fam.family_name == "baselines"
    assert len(fam.candidates) == 2


def test_model_comparison_result_validation() -> None:
    with pytest.raises(ValueError, match="rankings cannot be empty"):
        ModelComparisonResult(
            evaluation_role=EvaluationRole.VALIDATION_SELECTION,
            metric_name="mae",
            higher_is_better=False,
            rankings=(),
        )

    # Invariant violation: winner populated on PROTECTED_TEST
    with pytest.raises(ValueError, match="winner_candidate_id must be None for PROTECTED_TEST"):
        ModelComparisonResult(
            evaluation_role=EvaluationRole.PROTECTED_TEST,
            metric_name="mae",
            higher_is_better=False,
            rankings=(("c1", Decimal("1.0")),),
            winner_candidate_id="c1",
        )


def test_comparator_validation_errors() -> None:
    with pytest.raises(ValueError, match="Cannot compare empty results"):
        Comparator.compare_candidates([], metric_name="mae")

    # Mixed roles
    role_val = EvaluationRole.VALIDATION_SELECTION
    role_test = EvaluationRole.PROTECTED_TEST
    res_val = _make_aggregate_result("c1", role_val, ["f1"], {"mae": Decimal("1")})
    res_test = _make_aggregate_result("c2", role_test, ["f1"], {"mae": Decimal("2")})
    with pytest.raises(ValueError, match="Mixed evaluation roles"):
        Comparator.compare_candidates([res_val, res_test], metric_name="mae")

    # Parity violation: different folds
    res_f1 = _make_aggregate_result("c1", role_val, ["f1"], {"mae": Decimal("1")})
    res_f2 = _make_aggregate_result("c2", role_val, ["f2"], {"mae": Decimal("2")})
    with pytest.raises(ValueError, match="Experimental parity violation"):
        Comparator.compare_candidates([res_f1, res_f2], metric_name="mae")

    # Missing metric
    res_no_metric = _make_aggregate_result("c2", role_val, ["f1"], {"mse": Decimal("2")})
    with pytest.raises(ValueError, match="Metric mae missing"):
        Comparator.compare_candidates([res_f1, res_no_metric], metric_name="mae")


def test_comparator_validation_selection() -> None:
    res1 = _make_aggregate_result(
        "candidate_A",
        EvaluationRole.VALIDATION_SELECTION,
        ["f1", "f2"],
        {"mae": Decimal("2.5"), "acc": Decimal("0.70")},
    )
    res2 = _make_aggregate_result(
        "candidate_B",
        EvaluationRole.VALIDATION_SELECTION,
        ["f1", "f2"],
        {"mae": Decimal("1.5"), "acc": Decimal("0.85")},
    )

    # Lower is better (MAE): candidate_B wins
    comp_mae = Comparator.compare_candidates(
        [res1, res2], metric_name="mae", higher_is_better=False
    )
    assert comp_mae.winner_candidate_id == "candidate_B"
    assert comp_mae.rankings[0] == ("candidate_B", Decimal("1.5"))
    assert comp_mae.rankings[1] == ("candidate_A", Decimal("2.5"))
    assert Comparator.select_best_candidate(comp_mae) == "candidate_B"

    # Higher is better (acc): candidate_B wins
    comp_acc = Comparator.compare_candidates(
        [res1, res2], metric_name="acc", higher_is_better=True
    )
    assert comp_acc.winner_candidate_id == "candidate_B"
    assert Comparator.select_best_candidate(comp_acc) == "candidate_B"

    # Tie breaking: identical metric breaks tie deterministically by candidate_id
    res_tie1 = _make_aggregate_result(
        "cand_Z", EvaluationRole.VALIDATION_SELECTION, ["f1"], {"mae": Decimal("1.0")}
    )
    res_tie2 = _make_aggregate_result(
        "cand_A", EvaluationRole.VALIDATION_SELECTION, ["f1"], {"mae": Decimal("1.0")}
    )
    comp_tie = Comparator.compare_candidates(
        [res_tie1, res_tie2], metric_name="mae", higher_is_better=False
    )
    assert comp_tie.winner_candidate_id == "cand_A"


def test_comparator_protected_test_invariant() -> None:
    res1 = _make_aggregate_result(
        "candidate_A",
        EvaluationRole.PROTECTED_TEST,
        ["f1"],
        {"mae": Decimal("2.0")},
    )
    res2 = _make_aggregate_result(
        "candidate_B",
        EvaluationRole.PROTECTED_TEST,
        ["f1"],
        {"mae": Decimal("1.0")},
    )

    # Comparison succeeds and ranks candidates
    comp_test = Comparator.compare_candidates(
        [res1, res2], metric_name="mae", higher_is_better=False
    )
    assert comp_test.evaluation_role == EvaluationRole.PROTECTED_TEST
    assert len(comp_test.rankings) == 2
    # But winner_candidate_id MUST be None
    assert comp_test.winner_candidate_id is None

    # Attempting to select a winner on PROTECTED_TEST is strictly forbidden and raises ValueError
    with pytest.raises(
        ValueError,
        match="Selecting a winner or promoting a candidate based on PROTECTED_TEST",
    ):
        Comparator.select_best_candidate(comp_test)

    # Calling select_best_candidate on a result with winner_candidate_id=None raises ValueError
    res_none_winner = ModelComparisonResult(
        evaluation_role=EvaluationRole.DEVELOPMENT,
        metric_name="mae",
        higher_is_better=False,
        rankings=(("c1", Decimal("1.0")),),
        winner_candidate_id=None,
    )
    with pytest.raises(ValueError, match="does not have an admissible winner"):
        Comparator.select_best_candidate(res_none_winner)
