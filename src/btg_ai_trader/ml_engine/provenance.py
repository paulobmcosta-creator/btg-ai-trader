"""Scientific provenance, cryptographic training input boundaries, and environment fingerprints."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import joblib
import numpy as np
import scipy
import sklearn
import threadpoolctl

from btg_ai_trader.ml_engine.domain import (
    MLCandidateSpec,
    RNGContext,
    TargetContract,
)
from btg_ai_trader.statistical_baselines.domain import CausalLeakageError, StatisticalSample
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY, NumericPolicy


@dataclass(frozen=True, slots=True)
class EnvironmentFingerprint:
    """Factual, secure snapshot of runtime Python and scientific library versions."""

    python_version: str
    sklearn_version: str
    numpy_version: str
    scipy_version: str
    joblib_version: str
    threadpoolctl_version: str
    platform_system: str
    fingerprint_digest: str = field(init=False)

    def __post_init__(self) -> None:
        canonical_dict = {
            "joblib_version": self.joblib_version,
            "numpy_version": self.numpy_version,
            "platform_system": self.platform_system,
            "python_version": self.python_version,
            "scipy_version": self.scipy_version,
            "sklearn_version": self.sklearn_version,
            "threadpoolctl_version": self.threadpoolctl_version,
        }
        serialized = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        object.__setattr__(self, "fingerprint_digest", digest)

    @classmethod
    def current(cls) -> EnvironmentFingerprint:
        """Capture the live runtime environment without leaking private usernames or paths."""
        return cls(
            python_version=sys.version.split()[0],
            sklearn_version=sklearn.__version__,
            numpy_version=np.__version__,
            scipy_version=scipy.__version__,
            joblib_version=joblib.__version__,
            threadpoolctl_version=threadpoolctl.__version__,
            platform_system=platform.system(),
        )

    @classmethod
    def capture(cls) -> EnvironmentFingerprint:
        """Alias for current() to capture live runtime environment."""
        return cls.current()

    @property
    def scikit_learn_version(self) -> str:
        return self.sklearn_version

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "fingerprint_digest": self.fingerprint_digest,
            "joblib_version": self.joblib_version,
            "numpy_version": self.numpy_version,
            "platform_system": self.platform_system,
            "python_version": self.python_version,
            "scipy_version": self.scipy_version,
            "sklearn_version": self.sklearn_version,
            "threadpoolctl_version": self.threadpoolctl_version,
        }


@dataclass(frozen=True, slots=True)
class ModelTrainingInputBoundary:
    """Cryptographic boundary capturing all causal inputs, contracts, and policies entering fit."""

    ordered_sample_ids: tuple[str, ...]
    dataset_digest: str
    source_lineage_digest: str
    target_contract_digest: str
    feature_schema_digest: str
    knowledge_cutoff: datetime
    candidate_spec_digest: str
    numeric_policy: NumericPolicy
    environment_fingerprint_digest: str
    code_revision: str
    boundary_digest: str = field(init=False)
    is_verified: bool = False

    def __post_init__(self) -> None:
        if (
            self.knowledge_cutoff.tzinfo is None
            or self.knowledge_cutoff.tzinfo.utcoffset(self.knowledge_cutoff) is None
        ):
            raise ValueError(
                f"knowledge_cutoff must be timezone-aware, got {self.knowledge_cutoff!r}"
            )
        if not self.dataset_digest:
            raise ValueError("dataset_digest must be non-empty")
        if not self.candidate_spec_digest:
            raise ValueError("candidate_spec_digest must be non-empty")
        if not self.code_revision:
            raise ValueError("code_revision must be non-empty")

        canonical_dict = {
            "candidate_spec_digest": self.candidate_spec_digest,
            "code_revision": self.code_revision,
            "dataset_digest": self.dataset_digest,
            "environment_fingerprint_digest": self.environment_fingerprint_digest,
            "feature_schema_digest": self.feature_schema_digest,
            "knowledge_cutoff": self.knowledge_cutoff.isoformat(),
            "numeric_policy": self.numeric_policy.to_canonical_dict(),
            "ordered_sample_ids": list(self.ordered_sample_ids),
            "source_lineage_digest": self.source_lineage_digest,
            "target_contract_digest": self.target_contract_digest,
        }
        serialized = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        object.__setattr__(self, "boundary_digest", digest)

    @classmethod
    def create_and_verify(
        cls,
        samples: Sequence[StatisticalSample],
        target_contract: TargetContract,
        feature_schema_digest: str,
        candidate_spec: MLCandidateSpec,
        knowledge_cutoff: datetime,
        environment: EnvironmentFingerprint | None = None,
        code_revision: str = "",
    ) -> ModelTrainingInputBoundary:
        """Create and cryptographically verify a ModelTrainingInputBoundary."""
        if not samples:
            raise ValueError("Cannot construct training input boundary with zero samples")

        env = environment if environment is not None else EnvironmentFingerprint.current()
        ordered_sample_ids: list[str] = []
        hasher_dataset = hashlib.sha256()
        hasher_lineage = hashlib.sha256()

        for s in samples:
            if s.target_knowledge_time > knowledge_cutoff:
                raise CausalLeakageError(
                    f"Future label leakage detected: sample '{s.sample_id}' "
                    f"target knowledge time {s.target_knowledge_time} "
                    f"exceeds training cutoff {knowledge_cutoff}"
                )
            ordered_sample_ids.append(s.sample_id)
            hasher_dataset.update(s.sample_id.encode("utf-8"))
            hasher_dataset.update(str(s.target_value).encode("utf-8"))
            hasher_lineage.update(s.source_lineage.encode("utf-8"))

        boundary = cls(
            ordered_sample_ids=tuple(ordered_sample_ids),
            dataset_digest=hasher_dataset.hexdigest(),
            source_lineage_digest=hasher_lineage.hexdigest(),
            target_contract_digest=target_contract.contract_digest,
            feature_schema_digest=feature_schema_digest,
            knowledge_cutoff=knowledge_cutoff,
            candidate_spec_digest=candidate_spec.spec_digest,
            numeric_policy=candidate_spec.numeric_policy,
            environment_fingerprint_digest=env.fingerprint_digest,
            code_revision=code_revision,
            is_verified=True,
        )
        return boundary


@dataclass(frozen=True, slots=True)
class ModelTrainingManifest:
    """Immutable manifest capturing the scientific root of a completed model fit."""

    boundary_digest: str
    candidate_id: str
    fitted_feature_pipeline_digest: str
    model_state_digest: str
    target_contract_digest: str
    rng_context: RNGContext | None
    environment_fingerprint: EnvironmentFingerprint
    code_revision: str
    numeric_policy: NumericPolicy = DEFAULT_NUMERIC_POLICY
    scientific_root_digest: str = field(init=False)
    audit_metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        canonical_scientific_root = {
            "boundary_digest": self.boundary_digest,
            "candidate_id": self.candidate_id,
            "code_revision": self.code_revision,
            "environment_fingerprint_digest": self.environment_fingerprint.fingerprint_digest,
            "fitted_feature_pipeline_digest": self.fitted_feature_pipeline_digest,
            "model_state_digest": self.model_state_digest,
            "numeric_policy": self.numeric_policy.to_canonical_dict(),
            "rng_context": self.rng_context.to_canonical_dict() if self.rng_context else None,
            "target_contract_digest": self.target_contract_digest,
        }
        serialized = json.dumps(canonical_scientific_root, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        object.__setattr__(self, "scientific_root_digest", digest)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "audit_metadata": dict(self.audit_metadata),
            "boundary_digest": self.boundary_digest,
            "candidate_id": self.candidate_id,
            "code_revision": self.code_revision,
            "environment_fingerprint": self.environment_fingerprint.to_canonical_dict(),
            "fitted_feature_pipeline_digest": self.fitted_feature_pipeline_digest,
            "model_state_digest": self.model_state_digest,
            "numeric_policy": self.numeric_policy.to_canonical_dict(),
            "rng_context": self.rng_context.to_canonical_dict() if self.rng_context else None,
            "scientific_root_digest": self.scientific_root_digest,
            "target_contract_digest": self.target_contract_digest,
        }
