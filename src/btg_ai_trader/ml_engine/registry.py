"""Immutable content-addressed research model registry."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from btg_ai_trader.ml_engine.domain import RNGContext
from btg_ai_trader.ml_engine.provenance import ModelTrainingManifest

BANNED_ALIASES = {
    "active",
    "challenger",
    "champion",
    "current",
    "default",
    "latest",
    "production",
    "staging",
}


@dataclass(frozen=True, slots=True)
class ModelRecord:
    """Scientific registry record; never a deployment pointer."""

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
        required = {
            "candidate_id": self.candidate_id,
            "model_state_digest": self.model_state_digest,
            "training_input_boundary_digest": self.training_input_boundary_digest,
            "feature_pipeline_digest": self.feature_pipeline_digest,
            "target_contract_digest": self.target_contract_digest,
            "environment_fingerprint_digest": self.environment_fingerprint_digest,
            "training_manifest_digest": self.training_manifest_digest,
            "model_card_digest": self.model_card_digest,
            "code_revision": self.code_revision,
        }
        for name, value in required.items():
            if not value:
                raise ValueError(f"{name} must be non-empty")
        if self.model_card_digest.startswith("placeholder"):
            raise ValueError("placeholder model-card digests are forbidden")
        object.__setattr__(self, "evaluation_refs", tuple(self.evaluation_refs))
        payload = {
            "candidate_id": self.candidate_id,
            "code_revision": self.code_revision,
            "environment_fingerprint_digest": self.environment_fingerprint_digest,
            "evaluation_refs": list(self.evaluation_refs),
            "feature_pipeline_digest": self.feature_pipeline_digest,
            "model_card_digest": self.model_card_digest,
            "model_state_digest": self.model_state_digest,
            "rng_context": self.rng_context.to_canonical_dict() if self.rng_context else None,
            "target_contract_digest": self.target_contract_digest,
            "training_input_boundary_digest": self.training_input_boundary_digest,
            "training_manifest_digest": self.training_manifest_digest,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        object.__setattr__(
            self, "record_digest", hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        )

    @classmethod
    def from_manifest(
        cls,
        manifest: ModelTrainingManifest,
        *,
        model_card_digest: str,
        evaluation_refs: tuple[str, ...] = (),
    ) -> ModelRecord:
        if not manifest.is_verified:
            raise ValueError("ModelRecord requires a verified ModelTrainingManifest")
        return cls(
            candidate_id=manifest.candidate_id,
            model_state_digest=manifest.model_state_digest,
            training_input_boundary_digest=manifest.boundary_digest,
            feature_pipeline_digest=manifest.fitted_feature_pipeline_digest,
            target_contract_digest=manifest.target_contract_digest,
            rng_context=manifest.rng_context,
            environment_fingerprint_digest=(
                manifest.environment_fingerprint.fingerprint_digest
            ),
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
    """In-memory append-only catalog of immutable research records."""

    def __init__(self) -> None:
        self._records: dict[str, ModelRecord] = {}

    def register(self, record: ModelRecord) -> str:
        record_id = record.record_digest
        existing = self._records.get(record_id)
        if existing is not None:
            if existing != record:
                raise ValueError(
                    f"Record digest '{record_id}' conflicts with existing contents"
                )
            return record_id
        self._records[record_id] = record
        return record_id

    def get(self, record_digest: str) -> ModelRecord:
        if record_digest.lower() in BANNED_ALIASES:
            raise ValueError(
                f"Lookup by mutable production alias '{record_digest}' is strictly "
                "forbidden in ResearchModelRegistry"
            )
        try:
            return self._records[record_digest]
        except KeyError as exc:
            raise KeyError(
                f"Record with digest '{record_digest}' not found in registry"
            ) from exc

    def contains(self, record_digest: str) -> bool:
        return record_digest in self._records

    def __len__(self) -> int:
        return len(self._records)
