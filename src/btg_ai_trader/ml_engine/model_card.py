"""Deterministic research Model Card with explicit non-operational claim boundaries."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from btg_ai_trader.ml_engine.domain import (
    EvaluationScope,
    RNGContext,
    TargetContract,
    freeze_mapping,
)
from btg_ai_trader.ml_engine.features import FeatureSchema
from btg_ai_trader.ml_engine.provenance import EnvironmentFingerprint


@dataclass(frozen=True, slots=True)
class ModelCard:
    """Research-only model documentation; never deployment or strategy approval."""

    model_id: str
    family: str
    target_contract: TargetContract
    feature_schema: FeatureSchema
    training_boundary_digest: str
    hyperparameters: Mapping[str, Any]
    rng_context: RNGContext | None
    environment_fingerprint: EnvironmentFingerprint
    validation_metrics: Mapping[str, Decimal]
    protected_metrics: Mapping[str, Decimal] | None = None
    comparators: tuple[str, ...] = ()
    known_limitations: tuple[str, ...] = ()
    search_space_digest: str = ""
    validation_context_fingerprint: str = ""
    protected_context_fingerprint: str = ""
    protected_evidence_consumed: bool = False
    calibration_refs: tuple[str, ...] = ()
    ablation_refs: tuple[str, ...] = ()
    evaluation_scope: EvaluationScope | str = EvaluationScope.MODEL
    strategy_value: str = "NOT_ASSESSED"
    economic_value: str = "NOT_ASSESSED"
    paper_eligibility: str = "NOT_ASSESSED"
    live_readiness: str = "NOT_ASSESSED"
    audit_metadata: Mapping[str, str] = field(default_factory=dict)
    card_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.model_id:
            raise ValueError("model_id must be non-empty")
        if not self.family:
            raise ValueError("family must be non-empty")
        if not self.training_boundary_digest:
            raise ValueError("training_boundary_digest must be non-empty")
        scope = (
            self.evaluation_scope.value
            if isinstance(self.evaluation_scope, EvaluationScope)
            else str(self.evaluation_scope)
        )
        if scope != EvaluationScope.MODEL.value:
            raise ValueError("evaluation_scope must be EvaluationScope.MODEL")
        object.__setattr__(self, "evaluation_scope", scope)

        non_assessed = {
            "strategy_value": self.strategy_value,
            "economic_value": self.economic_value,
            "paper_eligibility": self.paper_eligibility,
            "live_readiness": self.live_readiness,
        }
        for name, value in non_assessed.items():
            if value != "NOT_ASSESSED":
                raise ValueError(f"{name} must remain 'NOT_ASSESSED' in Sprint 5")

        if self.protected_metrics is not None and not self.protected_context_fingerprint:
            raise ValueError(
                "protected_metrics require a protected_context_fingerprint"
            )

        object.__setattr__(self, "hyperparameters", freeze_mapping(self.hyperparameters))
        object.__setattr__(
            self, "validation_metrics", freeze_mapping(self.validation_metrics)
        )
        if self.protected_metrics is not None:
            object.__setattr__(
                self, "protected_metrics", freeze_mapping(self.protected_metrics)
            )
        object.__setattr__(self, "audit_metadata", freeze_mapping(self.audit_metadata))
        object.__setattr__(self, "comparators", tuple(self.comparators))
        object.__setattr__(self, "known_limitations", tuple(self.known_limitations))
        object.__setattr__(self, "calibration_refs", tuple(self.calibration_refs))
        object.__setattr__(self, "ablation_refs", tuple(self.ablation_refs))

        payload = {
            "ablation_refs": sorted(self.ablation_refs),
            "calibration_refs": sorted(self.calibration_refs),
            "comparators": sorted(self.comparators),
            "economic_value": self.economic_value,
            "environment_fingerprint_digest": (
                self.environment_fingerprint.fingerprint_digest
            ),
            "evaluation_scope": self.evaluation_scope,
            "family": self.family,
            "feature_schema_digest": self.feature_schema.schema_digest,
            "hyperparameters": {
                key: str(value) if isinstance(value, Decimal) else value
                for key, value in sorted(self.hyperparameters.items())
            },
            "known_limitations": sorted(self.known_limitations),
            "live_readiness": self.live_readiness,
            "model_id": self.model_id,
            "paper_eligibility": self.paper_eligibility,
            "protected_context_fingerprint": self.protected_context_fingerprint,
            "protected_evidence_consumed": self.protected_evidence_consumed,
            "protected_metrics": (
                {
                    key: str(value)
                    for key, value in sorted(self.protected_metrics.items())
                }
                if self.protected_metrics is not None
                else None
            ),
            "rng_context": self.rng_context.to_canonical_dict() if self.rng_context else None,
            "search_space_digest": self.search_space_digest,
            "strategy_value": self.strategy_value,
            "target_contract_digest": self.target_contract.contract_digest,
            "training_boundary_digest": self.training_boundary_digest,
            "validation_context_fingerprint": self.validation_context_fingerprint,
            "validation_metrics": {
                key: str(value)
                for key, value in sorted(self.validation_metrics.items())
            },
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        object.__setattr__(
            self, "card_digest", hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        )

    @property
    def candidate_id(self) -> str:
        return self.model_id

    @property
    def non_assessment_claims(self) -> str:
        return (
            "This artifact is an ML model card for research evaluation only "
            "(evaluation_scope = MODEL). It is NOT a trading strategy, has "
            "NO financial authority, and makes no economic claims."
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "ablation_refs": list(self.ablation_refs),
            "audit_metadata": dict(self.audit_metadata),
            "calibration_refs": list(self.calibration_refs),
            "card_digest": self.card_digest,
            "comparators": list(self.comparators),
            "economic_value": self.economic_value,
            "environment_fingerprint": self.environment_fingerprint.to_canonical_dict(),
            "evaluation_scope": self.evaluation_scope,
            "family": self.family,
            "feature_schema_digest": self.feature_schema.schema_digest,
            "hyperparameters": {
                key: str(value) if isinstance(value, Decimal) else value
                for key, value in self.hyperparameters.items()
            },
            "known_limitations": list(self.known_limitations),
            "live_readiness": self.live_readiness,
            "model_id": self.model_id,
            "paper_eligibility": self.paper_eligibility,
            "protected_context_fingerprint": self.protected_context_fingerprint,
            "protected_evidence_consumed": self.protected_evidence_consumed,
            "protected_metrics": (
                {key: str(value) for key, value in self.protected_metrics.items()}
                if self.protected_metrics is not None
                else None
            ),
            "rng_context": self.rng_context.to_canonical_dict() if self.rng_context else None,
            "search_space_digest": self.search_space_digest,
            "strategy_value": self.strategy_value,
            "target_contract_digest": self.target_contract.contract_digest,
            "training_boundary_digest": self.training_boundary_digest,
            "validation_context_fingerprint": self.validation_context_fingerprint,
            "validation_metrics": {
                key: str(value) for key, value in self.validation_metrics.items()
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.to_canonical_dict(), indent=2, sort_keys=True)
