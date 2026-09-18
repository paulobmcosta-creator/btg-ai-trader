"""Tests for immutable Sprint 5 domain contracts."""

from decimal import Decimal

import pytest

from btg_ai_trader.ml_engine.domain import (
    MLCandidateSpec,
    RNGContext,
    TargetContract,
    apply_numeric_policy,
    freeze_mapping,
)
from btg_ai_trader.statistical_baselines.domain import TargetSemantics
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY, NumericPolicy


def _contract() -> TargetContract:
    return TargetContract(
        target_name="returns",
        target_semantics=TargetSemantics.CONTINUOUS,
        forecast_horizon_steps=5,
        knowledge_delay_steps=1,
        description="fixture",
    )


def test_target_contract_identity_and_validation() -> None:
    contract = _contract()
    assert contract.to_canonical_dict()["target_semantics"] == "CONTINUOUS"
    assert len(contract.contract_digest) == 64
    with pytest.raises(ValueError, match="target_name"):
        TargetContract("", TargetSemantics.CONTINUOUS, 1)
    with pytest.raises(TypeError, match="TargetSemantics"):
        TargetContract("x", "CONTINUOUS", 1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="positive"):
        TargetContract("x", TargetSemantics.CONTINUOUS, 0)
    with pytest.raises(ValueError, match="non-negative"):
        TargetContract("x", TargetSemantics.CONTINUOUS, 1, -1)


def test_rng_context_is_factual_and_deterministic() -> None:
    rng = RNGContext(
        algorithm="sklearn_random_state",
        seed=42,
        stream_semantics="fit",
        library_version="1.2.3",
    )
    assert len(rng.context_digest) == 64
    assert rng.to_canonical_dict()["seed"] == 42
    assert rng.child_context("fold-1") == rng.child_context("fold-1")
    assert rng.child_context("fold-1").seed != rng.child_context("fold-2").seed
    with pytest.raises(ValueError, match="sklearn_random_state"):
        RNGContext("numpy_pcg64", 1)
    with pytest.raises(TypeError, match="integer"):
        RNGContext("sklearn_random_state", True)
    with pytest.raises(ValueError, match="non-negative"):
        RNGContext("sklearn_random_state", -1)
    with pytest.raises(ValueError, match="stream_semantics"):
        RNGContext("sklearn_random_state", 1, "")
    with pytest.raises(ValueError, match="stream_qualifier"):
        rng.child_context("")


def test_candidate_identity_and_deep_freeze() -> None:
    contract = _contract()
    spec = MLCandidateSpec(
        family="ridge_regression",
        hyperparameters={"alpha": Decimal("1.5"), "nested": {"v": [1, 2]}},
        target_contract=contract,
        feature_pipeline_spec_digest="pipe",
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev",
    )
    assert spec.hyperparameters["alpha"] == "1.5"
    assert spec.candidate_id.startswith("ml:ridge_regression:")
    assert len(spec.spec_digest) == 64
    assert spec.to_canonical_dict()["code_revision"] == "rev"
    with pytest.raises(TypeError):
        spec.hyperparameters["x"] = 1  # type: ignore[index]
    with pytest.raises(ValueError, match="family"):
        MLCandidateSpec("", {}, contract, "pipe", None, DEFAULT_NUMERIC_POLICY, "rev")
    with pytest.raises(ValueError, match="code_revision"):
        MLCandidateSpec("ridge_regression", {}, contract, "pipe", None, DEFAULT_NUMERIC_POLICY, "")
    with pytest.raises(ValueError, match="feature_pipeline"):
        MLCandidateSpec("ridge_regression", {}, contract, "", None, DEFAULT_NUMERIC_POLICY, "rev")


def test_freeze_mapping_and_numeric_policy() -> None:
    frozen = freeze_mapping({"a": {"b": [1, 2]}})
    assert frozen["a"]["b"] == (1, 2)
    with pytest.raises(TypeError):
        frozen["a"]["b"] = (3,)  # type: ignore[index]
    value = apply_numeric_policy(
        Decimal("1.23456789"),
        NumericPolicy(precision=6, rounding_mode="ROUND_HALF_EVEN"),
    )
    assert value == Decimal("1.23457")
