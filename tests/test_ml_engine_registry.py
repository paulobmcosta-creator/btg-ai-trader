"""Tests for immutable research registry evidence."""

from __future__ import annotations

import objectpath  # type: ignore[import-not-found]

import pytest

from btg_ai_trader.ml_engine.registry import ModelRecord, ResearchModelRegistry
from btg_ai_trader.ml_engine.training import ModelTrainer
from btg_ai_trader.statistical_baselines.domain import TargetSemantics
from tests.ml_engine_helpers import make_binary_samples, make_candidate_spec, make_pipeline


def _verified_manifest():
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
    return result.manifest


def test_registry_record_requires_real_card_and_is_idempotent() -> None:
    manifest = _verified_manifest()
    record = ModelRecord.from_manifest(
        manifest,
        model_card_digest="c" * 64,
        evaluation_refs=("eval-1",),
    )
    registry = ResearchModelRegistry()
    digest = registry.register(record)
    assert registry.register(record) == digest
    assert registry.get(digest) == record
    assert registry.contains(digest)
    assert len(registry) == 1
    assert record.to_canonical_dict()["model_card_digest"] == "c" * 64


def test_registry_alias_missing_and_placeholder_rejections() -> None:
    manifest = _verified_manifest()
    with pytest.raises(ValueError, match="placeholder"):
        ModelRecord.from_manifest(
            manifest,
            model_card_digest="placeholder_card_digest",
        )
    registry = ResearchModelRegistry()
    for alias in ("latest", "production", "champion"):
        with pytest.raises(ValueError, match="strictly forbidden"):
            registry.get(alias)
    with pytest.raises(KeyError, match="not found"):
        registry.get("0" * 64)
