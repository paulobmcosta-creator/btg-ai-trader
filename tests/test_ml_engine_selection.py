"""Tests for finite model search space, search history, and validation selection."""

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

import pytest

from btg_ai_trader.ml_engine.domain import (
    MetricDirection,
    MLCandidateSpec,
    RNGContext,
    TargetContract,
)
from btg_ai_trader.ml_engine.selection import (
    ModelComplexityDescriptor,
    ModelSearchHistory,
    ModelSearchSpace,
    ModelSelectionPolicy,
)
from btg_ai_trader.statistical_baselines.domain import TargetSemantics
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY


def _make_spec(
    family: str,
    hyperparams: Mapping[str, Any],
    seed: int = 42,
) -> MLCandidateSpec:
    contract = TargetContract(
        target_name="up",
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        forecast_horizon_steps=5,
    )
    rng = RNGContext(algorithm="numpy_pcg64", seed=seed)
    return MLCandidateSpec(
        family=family,
        hyperparameters=hyperparams,
        target_contract=contract,
        feature_pipeline_spec_digest="digest_p",
        rng_context=rng,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev_1",
    )


def test_model_complexity_descriptor() -> None:
    desc = ModelComplexityDescriptor(
        family="logistic_regression",
        feature_count=5,
        parameter_count=6,
    )
    assert desc.family == "logistic_regression"
    assert desc.feature_count == 5
    assert desc.parameter_count == 6


def test_search_space_best_seed_prohibition() -> None:
    spec_seed_1 = _make_spec("logistic_regression", {"C": Decimal("1.0")}, seed=1)
    spec_seed_2 = _make_spec("logistic_regression", {"C": Decimal("1.0")}, seed=2)

    space = ModelSearchSpace((spec_seed_1, spec_seed_2))
    with pytest.raises(ValueError, match="Seed cherry-picking is strictly prohibited"):
        ModelSelectionPolicy.assert_no_best_seed_selection(space)


def test_model_selection_policy_select_best() -> None:
    spec_a = _make_spec("logistic_regression", {"C": Decimal("0.1")}, seed=42)
    spec_b = _make_spec("logistic_regression", {"C": Decimal("1.0")}, seed=42)

    history = ModelSearchHistory(search_space_digest="space_test")
    history.record_attempt(
        candidate_spec=spec_a,
        fit_status="SUCCESS",
        validation_metrics={"brier_score": Decimal("0.24")},
    )
    history.record_attempt(
        candidate_spec=spec_b,
        fit_status="SUCCESS",
        validation_metrics={"brier_score": Decimal("0.18")},
    )

    policy = ModelSelectionPolicy(
        metric_name="brier_score",
        direction=MetricDirection.MINIMIZE,
    )

    best = policy.select_best(history)
    # Lower brier score is better -> spec_b (0.18 < 0.24)
    assert best.candidate_id == spec_b.candidate_id
