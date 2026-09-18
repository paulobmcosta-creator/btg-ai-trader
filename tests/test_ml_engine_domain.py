"""Tests for ML Engine domain contracts, schemas, and specifications."""

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


def test_target_contract_continuous() -> None:
    contract = TargetContract(
        target_name="returns_5m",
        target_semantics=TargetSemantics.CONTINUOUS,
        forecast_horizon_steps=5,
        knowledge_delay_steps=1,
        description="5-minute forward return",
    )
    assert contract.target_name == "returns_5m"
    assert contract.target_semantics == TargetSemantics.CONTINUOUS
    assert contract.forecast_horizon_steps == 5
    assert contract.knowledge_delay_steps == 1
    assert contract.contract_digest is not None
    assert len(contract.contract_digest) == 64

    # Idempotent canonical dict
    d = contract.to_canonical_dict()
    assert d["target_name"] == "returns_5m"
    assert d["target_semantics"] == "CONTINUOUS"
    assert d["forecast_horizon_steps"] == 5
    assert d["knowledge_delay_steps"] == 1


def test_target_contract_binary() -> None:
    contract = TargetContract(
        target_name="direction_up_15m",
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        forecast_horizon_steps=15,
    )
    assert contract.target_semantics == TargetSemantics.BINARY_PROBABILITY
    assert contract.forecast_horizon_steps == 15


def test_target_contract_validation_errors() -> None:
    with pytest.raises(ValueError, match="target_name must be a non-empty string"):
        TargetContract(
            target_name="",
            target_semantics=TargetSemantics.CONTINUOUS,
            forecast_horizon_steps=1,
        )

    with pytest.raises(TypeError, match="target_semantics must be TargetSemantics"):
        TargetContract(
            target_name="t",
            target_semantics="CONTINUOUS",  # type: ignore[arg-type]
            forecast_horizon_steps=1,
        )

    with pytest.raises(ValueError, match="forecast_horizon_steps must be positive"):
        TargetContract(
            target_name="t",
            target_semantics=TargetSemantics.CONTINUOUS,
            forecast_horizon_steps=0,
        )

    with pytest.raises(ValueError, match="knowledge_delay_steps must be non-negative"):
        TargetContract(
            target_name="t",
            target_semantics=TargetSemantics.CONTINUOUS,
            forecast_horizon_steps=1,
            knowledge_delay_steps=-1,
        )


def test_rng_context_and_child_generation() -> None:
    rng = RNGContext(algorithm="numpy_pcg64", seed=42, stream_semantics="model_training")
    assert rng.seed == 42
    assert rng.stream_semantics == "model_training"
    assert rng.algorithm == "numpy_pcg64"
    assert rng.context_digest is not None

    d = rng.to_canonical_dict()
    assert d["seed"] == 42
    assert d["stream_semantics"] == "model_training"
    assert d["algorithm"] == "numpy_pcg64"

    child1 = rng.child_context("fold_0")
    child2 = rng.child_context("fold_0")
    child3 = rng.child_context("fold_1")

    assert child1.seed == child2.seed
    assert child1.seed != child3.seed
    assert child1.stream_semantics == "model_training:fold_0"

    with pytest.raises(ValueError, match="seed must be non-negative"):
        RNGContext(algorithm="numpy_pcg64", seed=-1, stream_semantics="invalid")


def test_ml_candidate_spec() -> None:
    contract = TargetContract(
        target_name="direction_up",
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        forecast_horizon_steps=5,
    )
    rng = RNGContext(algorithm="numpy_pcg64", seed=100, stream_semantics="spec_test")
    policy = NumericPolicy(precision=28)

    spec = MLCandidateSpec(
        family="logistic_regression",
        hyperparameters={"C": Decimal("1.5"), "penalty": "l2"},
        target_contract=contract,
        feature_pipeline_spec_digest="digest_abc123",
        rng_context=rng,
        numeric_policy=policy,
        code_revision="git_sha_s5",
    )

    assert spec.family == "logistic_regression"
    assert spec.spec_digest is not None
    assert spec.candidate_id.startswith("ml:logistic_regression:")
    assert spec.hyperparameters["C"] == "1.5"

    canonical = spec.to_canonical_dict()
    assert canonical["family"] == "logistic_regression"
    assert canonical["code_revision"] == "git_sha_s5"
    assert canonical["hyperparameters"]["penalty"] == "l2"


def test_ml_candidate_spec_validation_errors() -> None:
    contract = TargetContract(
        target_name="direction_up",
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        forecast_horizon_steps=5,
    )

    with pytest.raises(ValueError, match="family must be a non-empty string"):
        MLCandidateSpec(
            family="",
            hyperparameters={},
            target_contract=contract,
            feature_pipeline_spec_digest="digest",
            rng_context=None,
            numeric_policy=DEFAULT_NUMERIC_POLICY,
            code_revision="rev",
        )

    with pytest.raises(ValueError, match="code_revision must be a non-empty string"):
        MLCandidateSpec(
            family="logistic_regression",
            hyperparameters={},
            target_contract=contract,
            feature_pipeline_spec_digest="digest",
            rng_context=None,
            numeric_policy=DEFAULT_NUMERIC_POLICY,
            code_revision="",
        )

    with pytest.raises(ValueError, match="feature_pipeline_spec_digest must be non-empty"):
        MLCandidateSpec(
            family="logistic_regression",
            hyperparameters={},
            target_contract=contract,
            feature_pipeline_spec_digest="",
            rng_context=None,
            numeric_policy=DEFAULT_NUMERIC_POLICY,
            code_revision="rev",
        )


def test_apply_numeric_policy() -> None:
    policy = NumericPolicy(precision=6, rounding_mode="ROUND_HALF_EVEN")
    val = Decimal("1.23456789")
    rounded = apply_numeric_policy(val, policy)
    assert rounded == Decimal("1.23457")


def test_freeze_mapping() -> None:
    m = {"a": 1, "nested": {"b": 2, "arr": [3, 4]}}
    frozen = freeze_mapping(m)
    assert frozen["a"] == 1
    assert frozen["nested"]["b"] == 2
    with pytest.raises(TypeError):
        frozen["a"] = 10  # type: ignore[index]
