"""Deterministic Model Card schema with explicit scientific boundary and non-assessment claims."""

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
    """Standardized scientific documentation container for an ML candidate under Protocol 0E-F."""

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
    comparators: tuple[str, ...] = field(default_factory=tuple)
    known_limitations: tuple[str, ...] = field(default_factory=tuple)
    evaluation_scope: EvaluationScope | str = "MODEL"
    strategy_value: str = "NOT_ASSESSED"
    economic_value: str = "NOT_ASSESSED"
    paper_eligibility: str = "NOT_ASSESSED"
    live_readiness: str = "NOT_ASSESSED"
    card_digest: str = field(init=False)
    audit_metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.model_id:
            raise ValueError("model_id must be non-empty")
        scope_str = (
            self.evaluation_scope.value
            if isinstance(self.evaluation_scope, EvaluationScope)
            else str(self.evaluation_scope)
        )
        if scope_str != "MODEL":
            raise ValueError("evaluation_scope must be EvaluationScope.MODEL")
        object.__setattr__(self, "evaluation_scope", scope_str)
        if self.strategy_value != "NOT_ASSESSED":
            raise ValueError("strategy_value must remain 'NOT_ASSESSED' in ModelCard")
        if self.economic_value != "NOT_ASSESSED":
            raise ValueError("economic_value must remain 'NOT_ASSESSED' in ModelCard")
        if self.paper_eligibility != "NOT_ASSESSED":
            raise ValueError("paper_eligibility must remain 'NOT_ASSESSED' in ModelCard")
        if self.live_readiness != "NOT_ASSESSED":
            raise ValueError("live_readiness must remain 'NOT_ASSESSED' in ModelCard")

        object.__setattr__(self, "hyperparameters", freeze_mapping(self.hyperparameters))
        object.__setattr__(self, "validation_metrics", freeze_mapping(self.validation_metrics))
        if self.protected_metrics is not None:
            object.__setattr__(self, "protected_metrics", freeze_mapping(self.protected_metrics))
        object.__setattr__(self, "audit_metadata", freeze_mapping(self.audit_metadata))

        canonical_scientific_root = {
            "comparators": sorted(self.comparators),
            "economic_value": self.economic_value,
            "environment_fingerprint_digest": self.environment_fingerprint.fingerprint_digest,
            "evaluation_scope": self.evaluation_scope,
            "family": self.family,
            "feature_schema_digest": self.feature_schema.schema_digest,
            "hyperparameters": {
                k: str(v) if isinstance(v, Decimal) else v
                for k, v in sorted(self.hyperparameters.items())
            },
            "known_limitations": sorted(self.known_limitations),
            "live_readiness": self.live_readiness,
            "model_id": self.model_id,
            "paper_eligibility": self.paper_eligibility,
            "protected_metrics": {k: str(v) for k, v in sorted(self.protected_metrics.items())}
            if self.protected_metrics
            else None,
            "rng_context": self.rng_context.to_canonical_dict() if self.rng_context else None,
            "strategy_value": self.strategy_value,
            "target_contract_digest": self.target_contract.contract_digest,
            "training_boundary_digest": self.training_boundary_digest,
            "validation_metrics": {k: str(v) for k, v in sorted(self.validation_metrics.items())},
        }
        serialized = json.dumps(canonical_scientific_root, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        object.__setattr__(self, "card_digest", digest)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "audit_metadata": dict(self.audit_metadata),
            "card_digest": self.card_digest,
            "comparators": list(self.comparators),
            "economic_value": self.economic_value,
            "environment_fingerprint": self.environment_fingerprint.to_canonical_dict(),
            "evaluation_scope": self.evaluation_scope,
            "family": self.family,
            "feature_schema_digest": self.feature_schema.schema_digest,
            "hyperparameters": {
                k: str(v) if isinstance(v, Decimal) else v
                for k, v in self.hyperparameters.items()
            },
            "known_limitations": list(self.known_limitations),
            "live_readiness": self.live_readiness,
            "model_id": self.model_id,
            "paper_eligibility": self.paper_eligibility,
            "protected_metrics": {k: str(v) for k, v in self.protected_metrics.items()}
            if self.protected_metrics
            else None,
            "rng_context": self.rng_context.to_canonical_dict() if self.rng_context else None,
            "strategy_value": self.strategy_value,
            "target_contract_digest": self.target_contract.contract_digest,
            "training_boundary_digest": self.training_boundary_digest,
            "validation_metrics": {k: str(v) for k, v in self.validation_metrics.items()},
        }

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

    def to_json(self) -> str:
        return json.dumps(self.to_canonical_dict(), indent=2, sort_keys=True)
