"""Tests for finite model search and validation-only selection."""

from decimal import Decimal

import pytest

from btg_ai_trader.ml_engine.domain import MetricDirection
from btg_ai_trader.ml_engine.selection import (
    ModelComplexityDescriptor,
    ModelSearchHistory,
    ModelSearchSpace,
    ModelSelectionPolicy,
)
from btg_ai_trader.statistical_baselines.domain import EvaluationRole, TargetSemantics
from tests.ml_engine_helpers import make_candidate_spec, make_pipeline


def test_complexity_descriptor_validation() -> None:
    descriptor = ModelComplexityDescriptor("logistic_regression", 2, parameter_count=3)
    assert descriptor.to_canonical_dict()["parameter_count"] == 3
    with pytest.raises(ValueError, match="family"):
        ModelComplexityDescriptor("", 1)
    with pytest.raises(ValueError, match="feature_count"):
        ModelComplexityDescriptor("x", -1)


def test_search_space_is_finite_deduplicated_and_best_seed_fails_closed() -> None:
    pipeline = make_pipeline()
    first = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
        hyperparameters={"C": 0.5},
    )
    second = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
        hyperparameters={"C": 1.0},
    )
    space = ModelSearchSpace((first, second))
    assert len(space) == 2
    assert len(space.search_space_digest) == 64
    with pytest.raises(ValueError, match="empty"):
        ModelSearchSpace(())
    with pytest.raises(ValueError, match="positive"):
        ModelSearchSpace((first,), max_candidates_limit=0)
    with pytest.raises(ValueError, match="exceeds"):
        ModelSearchSpace((first, second), max_candidates_limit=1)
    with pytest.raises(ValueError, match="duplicate"):
        ModelSearchSpace((first, first))

    rf1 = make_candidate_spec(
        "random_forest_classifier",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
        seed=1,
        hyperparameters={"n_estimators": 3},
    )
    rf2 = make_candidate_spec(
        "random_forest_classifier",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
        seed=2,
        hyperparameters={"n_estimators": 3},
    )
    with pytest.raises(ValueError, match="best-seed"):
        ModelSearchSpace((rf1, rf2))


def test_history_is_immutable_bound_and_counts_failures() -> None:
    pipeline = make_pipeline()
    candidate = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
    )
    other = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
        hyperparameters={"C": 2.0},
    )
    history = ModelSearchHistory(ModelSearchSpace((candidate,)))
    history.record_attempt(
        candidate_spec=candidate,
        fit_status="SUCCESS",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        evaluation_context_fingerprint="context",
        validation_metrics={"brier_score": Decimal("0.2")},
    )
    history.record_attempt(
        candidate_spec=candidate,
        fit_status="FAILED",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        failure_reason="fit failed",
    )
    assert history.total_attempts == 2
    assert history.successful_attempts == 1
    assert history.failed_attempts == 1
    with pytest.raises(TypeError):
        history.records[0].validation_metrics["brier_score"] = Decimal("0")  # type: ignore[index]
    with pytest.raises(ValueError, match="not a member"):
        history.record_attempt(
            candidate_spec=other,
            fit_status="FAILED",
            evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        )
    with pytest.raises(ValueError, match="fit_status"):
        history.record_attempt(
            candidate_spec=candidate,
            fit_status="UNKNOWN",
            evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        )


def test_selection_enforces_validation_role_context_and_direction() -> None:
    pipeline = make_pipeline()
    a = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
        hyperparameters={"C": 0.5},
    )
    b = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
        hyperparameters={"C": 1.0},
    )
    space = ModelSearchSpace((a, b))
    history = ModelSearchHistory(space)
    for candidate, metric in ((a, Decimal("0.3")), (b, Decimal("0.2"))):
        history.record_attempt(
            candidate_spec=candidate,
            fit_status="SUCCESS",
            evaluation_role=EvaluationRole.VALIDATION_SELECTION,
            evaluation_context_fingerprint="same",
            validation_metrics={"score": metric},
        )
    assert ModelSelectionPolicy("score", MetricDirection.MINIMIZE).select_best(history) == b
    assert ModelSelectionPolicy("score", MetricDirection.MAXIMIZE).select_best(history) == a

    protected = ModelSearchHistory(space)
    protected.record_attempt(
        candidate_spec=a,
        fit_status="SUCCESS",
        evaluation_role=EvaluationRole.PROTECTED_TEST,
        evaluation_context_fingerprint="same",
        validation_metrics={"score": Decimal("0.1")},
    )
    with pytest.raises(ValueError, match="VALIDATION_SELECTION"):
        ModelSelectionPolicy("score", MetricDirection.MINIMIZE).select_best(protected)

    mixed = ModelSearchHistory(space)
    mixed.record_attempt(
        candidate_spec=a,
        fit_status="SUCCESS",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        evaluation_context_fingerprint="a",
        validation_metrics={"score": Decimal("0.1")},
    )
    mixed.record_attempt(
        candidate_spec=b,
        fit_status="SUCCESS",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        evaluation_context_fingerprint="b",
        validation_metrics={"score": Decimal("0.2")},
    )
    with pytest.raises(ValueError, match="identical"):
        ModelSelectionPolicy("score", MetricDirection.MINIMIZE).select_best(mixed)

    with pytest.raises(ValueError, match="No successful"):
        ModelSelectionPolicy("missing", MetricDirection.MINIMIZE).select_best(history)
    with pytest.raises(ValueError, match="metric_name"):
        ModelSelectionPolicy("", MetricDirection.MINIMIZE)
    with pytest.raises(TypeError, match="MetricDirection"):
        ModelSelectionPolicy("x", "MINIMIZE")  # type: ignore[arg-type]
