"""Tests for verified S5 training provenance."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

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
from tests.ml_engine_helpers import (
    make_binary_samples,
    make_candidate_spec,
    make_pipeline,
)


def test_environment_fingerprint_is_sanitized_and_stable_shape() -> None:
    env = EnvironmentFingerprint.capture()
    data = env.to_canonical_dict()
    assert len(env.fingerprint_digest) == 64
    assert data["python_version"]
    assert data["python_implementation"]
    assert data["platform_machine"] is not None
    assert "fingerprint_digest" in data
    assert "fingerprint_digest" not in env.to_canonical_dict(include_digest=False)
    assert all("/" not in item for item in env.threadpool_signature)


def test_verified_boundary_binds_full_dataset_and_cannot_be_forged() -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
    )
    samples = make_binary_samples()[:8]
    env = EnvironmentFingerprint.capture()
    cutoff = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    boundary = ModelTrainingInputBoundary.create_and_verify(
        samples=samples,
        target_contract=spec.target_contract,
        feature_pipeline_spec_digest=pipeline.spec_digest,
        candidate_spec=spec,
        knowledge_cutoff=cutoff,
        environment=env,
        code_revision=spec.code_revision,
    )
    assert boundary.is_verified
    forged = ModelTrainingInputBoundary(
        ordered_sample_ids=boundary.ordered_sample_ids,
        dataset_digest=boundary.dataset_digest,
        source_lineage_digest=boundary.source_lineage_digest,
        target_contract_digest=boundary.target_contract_digest,
        feature_pipeline_spec_digest=boundary.feature_pipeline_spec_digest,
        knowledge_cutoff=boundary.knowledge_cutoff,
        candidate_spec_digest=boundary.candidate_spec_digest,
        numeric_policy=boundary.numeric_policy,
        environment_fingerprint_digest=boundary.environment_fingerprint_digest,
        code_revision=boundary.code_revision,
    )
    assert not forged.is_verified
    assert not dataclasses.replace(boundary).is_verified

    changed = list(samples)
    first = changed[0]
    changed[0] = StatisticalSample(
        sample_id=first.sample_id,
        feature_knowledge_time=first.feature_knowledge_time,
        target_knowledge_time=first.target_knowledge_time,
        target_value=first.target_value,
        target_semantics=first.target_semantics,
        source_lineage=first.source_lineage,
        feature_metadata={**dict(first.feature_metadata), "f1": "999"},
    )
    changed_boundary = ModelTrainingInputBoundary.create_and_verify(
        samples=changed,
        target_contract=spec.target_contract,
        feature_pipeline_spec_digest=pipeline.spec_digest,
        candidate_spec=spec,
        knowledge_cutoff=cutoff,
        environment=env,
        code_revision=spec.code_revision,
    )
    assert changed_boundary.dataset_digest != boundary.dataset_digest


def test_boundary_rejects_leakage_and_identity_mismatch() -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
    )
    samples = make_binary_samples()[:8]
    env = EnvironmentFingerprint.capture()
    cutoff = datetime(2025, 1, 1, 9, 1, tzinfo=UTC)
    with pytest.raises(CausalLeakageError):
        ModelTrainingInputBoundary.create_and_verify(
            samples=samples,
            target_contract=spec.target_contract,
            feature_pipeline_spec_digest=pipeline.spec_digest,
            candidate_spec=spec,
            knowledge_cutoff=cutoff,
            environment=env,
            code_revision=spec.code_revision,
        )
    with pytest.raises(ValueError, match="feature_pipeline"):
        ModelTrainingInputBoundary.create_and_verify(
            samples=samples,
            target_contract=spec.target_contract,
            feature_pipeline_spec_digest="wrong",
            candidate_spec=spec,
            knowledge_cutoff=datetime(2025, 1, 1, 11, 0, tzinfo=UTC),
            environment=env,
            code_revision=spec.code_revision,
        )
    with pytest.raises(ValueError, match="code_revision"):
        ModelTrainingInputBoundary.create_and_verify(
            samples=samples,
            target_contract=spec.target_contract,
            feature_pipeline_spec_digest=pipeline.spec_digest,
            candidate_spec=spec,
            knowledge_cutoff=datetime(2025, 1, 1, 11, 0, tzinfo=UTC),
            environment=env,
            code_revision="other",
        )


def test_manifest_factory_verification_and_audit_immutability() -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression",
        pipeline,
        TargetSemantics.BINARY_PROBABILITY,
    )
    samples = make_binary_samples()[:8]
    env = EnvironmentFingerprint.capture()
    boundary = ModelTrainingInputBoundary.create_and_verify(
        samples=samples,
        target_contract=spec.target_contract,
        feature_pipeline_spec_digest=pipeline.spec_digest,
        candidate_spec=spec,
        knowledge_cutoff=datetime(2025, 1, 1, 11, 0, tzinfo=UTC),
        environment=env,
        code_revision=spec.code_revision,
    )
    manifest = ModelTrainingManifest.create(
        boundary=boundary,
        candidate_spec=spec,
        fitted_feature_pipeline_digest="fitted",
        model_state_digest="state",
        environment_fingerprint=env,
        code_revision=spec.code_revision,
        audit_metadata={"note": "x"},
    )
    assert manifest.is_verified
    assert len(manifest.scientific_root_digest) == 64
    with pytest.raises(TypeError):
        manifest.audit_metadata["note"] = "changed"  # type: ignore[index]
    assert manifest.to_canonical_dict()["audit_metadata"] == {"note": "x"}

    unverified_boundary = dataclasses.replace(boundary)
    with pytest.raises(ValueError, match="verified"):
        ModelTrainingManifest.create(
            boundary=unverified_boundary,
            candidate_spec=spec,
            fitted_feature_pipeline_digest="fitted",
            model_state_digest="state",
            environment_fingerprint=env,
            code_revision=spec.code_revision,
        )
