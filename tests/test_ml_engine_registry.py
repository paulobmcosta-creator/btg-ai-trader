"""Tests for immutable research registry evidence."""

# ruff: noqa: I001 -- explicit grouping retained for audit readability.

from __future__ import annotations

from dataclasses import replace

import pytest

from btg_ai_trader.ml_engine.model_card import ModelCard
from btg_ai_trader.ml_engine.provenance import ModelTrainingManifest
from btg_ai_trader.ml_engine.registry import ModelRecord, ResearchModelRegistry
from btg_ai_trader.ml_engine.training import ModelTrainer
from btg_ai_trader.statistical_baselines.domain import TargetSemantics
from tests.ml_engine_helpers import (
    make_binary_samples,
    make_candidate_spec,
    make_model_card,
    make_pipeline,
)


def _verified_evidence() -> tuple[ModelTrainingManifest, ModelCard]:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression", pipeline, TargetSemantics.BINARY_PROBABILITY
    )
    result = ModelTrainer().fit(
        candidate_spec=spec,
        pipeline_spec=pipeline,
        samples=make_binary_samples()[:8],
        knowledge_cutoff=make_binary_samples()[7].target_knowledge_time,
        code_revision=spec.code_revision,
    )
    return result.manifest, make_model_card(result, pipeline)


def test_registry_record_requires_real_card_and_is_idempotent() -> None:
    manifest, card = _verified_evidence()
    record = ModelRecord.from_manifest(
        manifest,
        model_card=card,
        evaluation_refs=("eval-1",),
    )
    registry = ResearchModelRegistry()
    digest = registry.register(record)
    assert registry.register(record) == digest
    assert registry.get(digest) == record
    assert registry.contains(digest)
    assert len(registry) == 1
    assert record.to_canonical_dict()["model_card_digest"] == card.card_digest


def test_registry_rejects_fake_or_mismatched_model_card_evidence() -> None:
    manifest, card = _verified_evidence()

    with pytest.raises(TypeError, match="ModelCard"):
        ModelRecord.from_manifest(
            manifest,
            model_card="c" * 64,  # type: ignore[arg-type]
        )

    mismatched_card = replace(card, training_boundary_digest="f" * 64)
    with pytest.raises(ValueError, match="does not match"):
        ModelRecord.from_manifest(
            manifest,
            model_card=mismatched_card,
        )

    record = ModelRecord.from_manifest(manifest, model_card=card)
    with pytest.raises(ValueError, match="SHA-256"):
        replace(record, model_card_digest="placeholder_card_digest")


def test_registry_alias_and_missing_record_rejections() -> None:
    registry = ResearchModelRegistry()
    for alias in ("latest", "production", "champion"):
        with pytest.raises(ValueError, match="strictly forbidden"):
            registry.get(alias)
    with pytest.raises(KeyError, match="not found"):
        registry.get("0" * 64)
