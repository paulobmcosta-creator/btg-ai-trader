"""Tests for ML Engine provenance, environment fingerprinting, and training manifests."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from btg_ai_trader.ml_engine.domain import (
    MLCandidateSpec,
    RNGContext,
    TargetContract,
)
from btg_ai_trader.ml_engine.provenance import (
    EnvironmentFingerprint,
    ModelTrainingInputBoundary,
    ModelTrainingManifest,
)
from btg_ai_trader.statistical_baselines.domain import (
    CausalLeakageError,
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY


def _make_sample(
    sample_id: str,
    target_dt: datetime,
) -> StatisticalSample:
    feat_dt = target_dt
    return StatisticalSample(
        sample_id=sample_id,
        feature_knowledge_time=feat_dt,
        target_knowledge_time=target_dt,
        target_value=Decimal(1),
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
    )


def test_environment_fingerprint_capture() -> None:
    env = EnvironmentFingerprint.capture()
    assert env.python_version is not None
    assert env.scikit_learn_version is not None
    assert env.numpy_version is not None
    assert env.fingerprint_digest is not None
    assert len(env.fingerprint_digest) == 64

    d = env.to_canonical_dict()
    assert d["sklearn_version"] == env.sklearn_version


def test_model_training_input_boundary() -> None:
    contract = TargetContract(
        target_name="up",
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        forecast_horizon_steps=5,
    )
    spec = MLCandidateSpec(
        family="logistic_regression",
        hyperparameters={},
        target_contract=contract,
        feature_pipeline_spec_digest="pipe_d",
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev_1",
    )

    t1 = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    t2 = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    cutoff = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)

    samples = [_make_sample("s1", t1), _make_sample("s2", t2)]

    boundary = ModelTrainingInputBoundary.create_and_verify(
        samples=samples,
        target_contract=contract,
        feature_schema_digest="schema_d",
        candidate_spec=spec,
        knowledge_cutoff=cutoff,
        code_revision="rev_1",
    )

    assert boundary.boundary_digest is not None
    assert boundary.ordered_sample_ids == ("s1", "s2")

    # Future leakage check
    past_cutoff = datetime(2025, 1, 1, 10, 30, tzinfo=UTC)
    with pytest.raises(CausalLeakageError, match="Future label leakage detected"):
        ModelTrainingInputBoundary.create_and_verify(
            samples=samples,
            target_contract=contract,
            feature_schema_digest="schema_d",
            candidate_spec=spec,
            knowledge_cutoff=past_cutoff,
            code_revision="rev_1",
        )


def test_model_training_manifest() -> None:
    env = EnvironmentFingerprint.capture()
    rng = RNGContext(algorithm="numpy_pcg64", seed=42)

    manifest = ModelTrainingManifest(
        candidate_id="ml:logistic_regression:abc123",
        boundary_digest="boundary_digest_123",
        model_state_digest="state_digest_123",
        fitted_feature_pipeline_digest="pipe_digest_123",
        target_contract_digest="contract_digest_123",
        environment_fingerprint=env,
        rng_context=rng,
        code_revision="rev_1",
    )

    assert manifest.scientific_root_digest is not None
    assert len(manifest.scientific_root_digest) == 64

    d = manifest.to_canonical_dict()
    assert d["candidate_id"] == "ml:logistic_regression:abc123"
    assert d["scientific_root_digest"] == manifest.scientific_root_digest
