"""Tests for standardized ModelCard and documentary boundaries."""

from decimal import Decimal

import pytest

from btg_ai_trader.ml_engine.domain import (
    EvaluationScope,
    TargetContract,
)
from btg_ai_trader.ml_engine.features import FeatureSchema, FeatureSpec, FeatureType
from btg_ai_trader.ml_engine.model_card import ModelCard
from btg_ai_trader.ml_engine.provenance import EnvironmentFingerprint
from btg_ai_trader.statistical_baselines.domain import TargetSemantics


def test_model_card_generation_and_constraints() -> None:
    contract = TargetContract(
        target_name="returns_15m",
        target_semantics=TargetSemantics.CONTINUOUS,
        forecast_horizon_steps=15,
    )
    schema = FeatureSchema([FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)])
    env = EnvironmentFingerprint.capture()

    card = ModelCard(
        model_id="ml:ridge_regression:abc123",
        family="ridge_regression",
        target_contract=contract,
        feature_schema=schema,
        training_boundary_digest="bound_123",
        hyperparameters={"alpha": Decimal("1.0")},
        rng_context=None,
        environment_fingerprint=env,
        validation_metrics={"mae": Decimal("0.05")},
        evaluation_scope=EvaluationScope.MODEL,
        known_limitations=("Linear model cannot capture complex non-linear interactions",),
    )

    assert card.candidate_id == "ml:ridge_regression:abc123"
    assert card.model_id == "ml:ridge_regression:abc123"
    assert card.evaluation_scope == "MODEL"
    assert "NOT a trading strategy" in card.non_assessment_claims
    assert "NO financial authority" in card.non_assessment_claims

    json_str = card.to_json()
    assert "ml:ridge_regression:abc123" in json_str
    assert "NOT_ASSESSED" in json_str


def test_model_card_scope_enforcement() -> None:
    contract = TargetContract(
        target_name="returns_15m",
        target_semantics=TargetSemantics.CONTINUOUS,
        forecast_horizon_steps=15,
    )
    schema = FeatureSchema([FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)])
    env = EnvironmentFingerprint.capture()

    with pytest.raises(ValueError, match="evaluation_scope must be EvaluationScope.MODEL"):
        ModelCard(
            model_id="ml:ridge_regression:abc123",
            family="ridge_regression",
            target_contract=contract,
            feature_schema=schema,
            training_boundary_digest="bound_123",
            hyperparameters={"alpha": Decimal("1.0")},
            rng_context=None,
            environment_fingerprint=env,
            validation_metrics={"mae": Decimal("0.05")},
            evaluation_scope=EvaluationScope.STRATEGY,  # Strictly forbidden!
        )
