"""Tests for deterministic research ModelCard boundaries."""

from decimal import Decimal

import pytest

from btg_ai_trader.ml_engine.domain import EvaluationScope
from btg_ai_trader.ml_engine.features import FeatureSchema, FeatureSpec, FeatureType
from btg_ai_trader.ml_engine.model_card import ModelCard
from btg_ai_trader.ml_engine.provenance import EnvironmentFingerprint
from btg_ai_trader.statistical_baselines.domain import TargetSemantics
from tests.ml_engine_helpers import make_contract


def _kwargs() -> dict[str, object]:
    return {
        "model_id": "ml:ridge:abc",
        "family": "ridge_regression",
        "target_contract": make_contract(TargetSemantics.CONTINUOUS),
        "feature_schema": FeatureSchema((FeatureSpec("f1", FeatureType.NUMERIC),)),
        "training_boundary_digest": "b" * 64,
        "hyperparameters": {"alpha": Decimal("1")},
        "rng_context": None,
        "environment_fingerprint": EnvironmentFingerprint.capture(),
        "validation_metrics": {"mae": Decimal("0.1")},
        "search_space_digest": "s" * 64,
        "validation_context_fingerprint": "v" * 64,
        "known_limitations": ("research only",),
        "calibration_refs": ("cal-1",),
        "ablation_refs": ("abl-1",),
        "audit_metadata": {"note": "audit"},
    }


def test_model_card_generation_digest_and_immutability() -> None:
    kwargs = _kwargs()
    card = ModelCard(**kwargs)  # type: ignore[arg-type]
    assert card.evaluation_scope == "MODEL"
    assert len(card.card_digest) == 64
    assert card.candidate_id == "ml:ridge:abc"
    assert "NOT a trading strategy" in card.non_assessment_claims
    assert "card_digest" in card.to_canonical_dict()
    assert "NOT_ASSESSED" in card.to_json()
    with pytest.raises(TypeError):
        card.validation_metrics["mae"] = Decimal("9")  # type: ignore[index]
    with pytest.raises(TypeError):
        card.audit_metadata["note"] = "changed"  # type: ignore[index]


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("model_id", "", "model_id"),
        ("family", "", "family"),
        ("training_boundary_digest", "", "training_boundary"),
        ("evaluation_scope", EvaluationScope.STRATEGY, "evaluation_scope"),
        ("strategy_value", "ASSESSED", "strategy_value"),
        ("economic_value", "ASSESSED", "economic_value"),
        ("paper_eligibility", "ELIGIBLE", "paper_eligibility"),
        ("live_readiness", "READY", "live_readiness"),
    ],
)
def test_model_card_rejects_scope_and_operational_claims(
    field: str, value: object, match: str
) -> None:
    kwargs = _kwargs()
    kwargs[field] = value
    with pytest.raises(ValueError, match=match):
        ModelCard(**kwargs)  # type: ignore[arg-type]


def test_protected_metrics_require_context() -> None:
    kwargs = _kwargs()
    kwargs["protected_metrics"] = {"mae": Decimal("0.2")}
    with pytest.raises(ValueError, match="protected_context"):
        ModelCard(**kwargs)  # type: ignore[arg-type]
    kwargs["protected_context_fingerprint"] = "p" * 64
    kwargs["protected_evidence_consumed"] = True
    card = ModelCard(**kwargs)  # type: ignore[arg-type]
    assert card.protected_evidence_consumed
