"""Immutable, content-addressed Research Model Registry."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from btg_ai_trader.ml_engine.domain import RNGContext
from btg_ai_trader.ml_engine.provenance import ModelTrainingManifest

BANNED_ALIASES = {
    "latest",
    "current",
    "production",
    "champion",
    "active",
    "default",
    "staging",
    "challenger",
}


@dataclass(frozen=True, slots=True)
class ModelRecord:
    """Immutable, content-addressed scientific record of a trained model."""

    candidate_id: str
    model_state_digest: str
    training_input_boundary_digest: str
    feature_pipeline_digest: str
    target_contract_digest: str
    rng_context: RNGContext | None
    environment_fingerprint_digest: str
    training_manifest_digest: str
    evaluation_refs: tuple[str, ...]
    model_card_digest: str
    code_revision: str
    record_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id must be a non-empty string")
        if not self.model_state_digest:
            raise ValueError("model_state_digest must be a non-empty string")
        if not self.code_revision:
            raise ValueError("code_revision must be a non-empty string")

        canonical_dict = {
            "candidate_id": self.candidate_id,
            "code_revision": self.code_revision,
            "environment_fingerprint_digest": self.environment_fingerprint_digest,
            "evaluation_refs": sorted(self.evaluation_refs),
            "feature_pipeline_digest": self.feature_pipeline_digest,
            "model_card_digest": self.model_card_digest,
            "model_state_digest": self.model_state_digest,
            "rng_context": self.rng_context.to_canonical_dict() if self.rng_context else None,
            "target_contract_digest": self.target_contract_digest,
            "training_input_boundary_digest": self.training_input_boundary_digest,
            "training_manifest_digest": self.training_manifest_digest,
        }
        serialized = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        object.__setattr__(self, "record_digest", digest)

    @classmethod
    def from_manifest(
        cls,
        manifest: ModelTrainingManifest,
        evaluation_refs: tuple[str, ...] = (),
        model_card_digest: str = "placeholder_card_digest",
    ) -> ModelRecord:
        return cls(
            candidate_id=manifest.candidate_id,
            model_state_digest=manifest.model_state_digest,
            training_input_boundary_digest=manifest.boundary_digest,
            feature_pipeline_digest=manifest.fitted_feature_pipeline_digest,
            target_contract_digest=manifest.target_contract_digest,
            rng_context=manifest.rng_context,
            environment_fingerprint_digest=manifest.environment_fingerprint.fingerprint_digest,
            training_manifest_digest=manifest.scientific_root_digest,
            evaluation_refs=evaluation_refs,
            model_card_digest=model_card_digest,
            code_revision=manifest.code_revision,
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "code_revision": self.code_revision,
            "environment_fingerprint_digest": self.environment_fingerprint_digest,
            "evaluation_refs": list(self.evaluation_refs),
            "feature_pipeline_digest": self.feature_pipeline_digest,
            "model_card_digest": self.model_card_digest,
            "model_state_digest": self.model_state_digest,
            "record_digest": self.record_digest,
            "rng_context": self.rng_context.to_canonical_dict() if self.rng_context else None,
            "target_contract_digest": self.target_contract_digest,
            "training_input_boundary_digest": self.training_input_boundary_digest,
            "training_manifest_digest": self.training_manifest_digest,
        }


class ResearchModelRegistry:
    """In-memory, append-only research registry for reproducible model records."""

    def __init__(self) -> None:
        self._records: dict[str, ModelRecord] = {}

    def register(self, record: ModelRecord) -> str:
        """Register an immutable ModelRecord with conflict detection and idempotency."""
        record_id = record.record_digest

        if record_id in self._records:
            existing = self._records[record_id]
            if existing != record:
                raise ValueError(
                    f"Conflict: Record digest '{record_id}' already registered "
                    f"with differing contents"
                )
            # Idempotent registration
            return record_id

        self._records[record_id] = record
        return record_id

    def get(self, record_digest: str) -> ModelRecord:
        """Retrieve a registered record by its immutable content digest."""
        if record_digest in BANNED_ALIASES or any(
            alias in record_digest.lower() for alias in BANNED_ALIASES
        ):
            raise ValueError(
                f"Lookup by mutable production alias '{record_digest}' is strictly forbidden "
                f"in ResearchModelRegistry"
            )
        if record_digest not in self._records:
            raise KeyError(f"Record with digest '{record_digest}' not found in registry")
        return self._records[record_digest]

    def contains(self, record_digest: str) -> bool:
        return record_digest in self._records

    def __len__(self) -> int:
        return len(self._records)
