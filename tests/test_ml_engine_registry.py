"""Tests for ResearchModelRegistry and immutable ModelRecord."""

import pytest

from btg_ai_trader.ml_engine.provenance import EnvironmentFingerprint, ModelTrainingManifest
from btg_ai_trader.ml_engine.registry import ModelRecord, ResearchModelRegistry


def _make_dummy_manifest(cand_id: str) -> ModelTrainingManifest:
    env = EnvironmentFingerprint.capture()
    return ModelTrainingManifest(
        candidate_id=cand_id,
        boundary_digest="bound_1",
        model_state_digest="state_1",
        fitted_feature_pipeline_digest="pipe_1",
        target_contract_digest="contract_1",
        rng_context=None,
        environment_fingerprint=env,
        code_revision="rev_1",
    )


def test_model_record_and_registry() -> None:
    manifest = _make_dummy_manifest("ml:logistic_regression:001")
    record = ModelRecord.from_manifest(manifest)

    assert record.record_digest is not None
    assert len(record.record_digest) == 64

    registry = ResearchModelRegistry()
    digest = registry.register(record)
    assert digest == record.record_digest
    assert registry.contains(digest)

    # Idempotent re-registration
    assert registry.register(record) == digest

    # Retrieval
    retrieved = registry.get(digest)
    assert retrieved.record_digest == record.record_digest


def test_registry_mutable_alias_prohibition() -> None:
    registry = ResearchModelRegistry()
    banned_aliases = ["latest", "production", "staging", "champion", "challenger", "active"]

    for alias in banned_aliases:
        with pytest.raises(ValueError, match="strictly forbidden in ResearchModelRegistry"):
            registry.get(alias)


def test_registry_key_error() -> None:
    registry = ResearchModelRegistry()
    with pytest.raises(KeyError, match="not found in registry"):
        registry.get("0" * 64)
