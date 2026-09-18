"""Verified training boundaries, manifests, and sanitized environment provenance."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import platform
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

import joblib
import numpy as np
import scipy
import sklearn
import threadpoolctl

from btg_ai_trader.ml_engine.domain import MLCandidateSpec, RNGContext, TargetContract
from btg_ai_trader.statistical_baselines.domain import (
    CausalLeakageError,
    StatisticalSample,
    _freeze_mapping,
)
from btg_ai_trader.statistical_baselines.metrics import (
    DEFAULT_NUMERIC_POLICY,
    NumericPolicy,
)
from btg_ai_trader.statistical_baselines.provenance import (
    StatisticalEvaluationInputBoundary,
)


_BOUNDARY_VERIFICATION_TOKEN = object()
_MANIFEST_VERIFICATION_TOKEN = object()


@dataclasses.dataclass(frozen=True, slots=True)
class EnvironmentFingerprint:
    """Sanitized environment identity for same-environment reproducibility claims."""

    python_version: str
    python_implementation: str
    sklearn_version: str
    numpy_version: str
    scipy_version: str
    joblib_version: str
    threadpoolctl_version: str
    platform_system: str
    platform_machine: str
    byteorder: str
    threadpool_signature: tuple[str, ...]
    fingerprint_digest: str = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        payload = self.to_canonical_dict(include_digest=False)
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        object.__setattr__(
            self,
            "fingerprint_digest",
            hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        )

    @classmethod
    def current(cls) -> EnvironmentFingerprint:
        signature: list[str] = []
        for info in threadpoolctl.threadpool_info():
            allowed = {
                "architecture": info.get("architecture"),
                "internal_api": info.get("internal_api"),
                "num_threads": info.get("num_threads"),
                "prefix": info.get("prefix"),
                "threading_layer": info.get("threading_layer"),
                "user_api": info.get("user_api"),
                "version": info.get("version"),
            }
            signature.append(
                json.dumps(allowed, sort_keys=True, separators=(",", ":"))
            )
        return cls(
            python_version=sys.version.split()[0],
            python_implementation=platform.python_implementation(),
            sklearn_version=sklearn.__version__,
            numpy_version=np.__version__,
            scipy_version=scipy.__version__,
            joblib_version=joblib.__version__,
            threadpoolctl_version=threadpoolctl.__version__,
            platform_system=platform.system(),
            platform_machine=platform.machine(),
            byteorder=sys.byteorder,
            threadpool_signature=tuple(sorted(signature)),
        )

    @classmethod
    def capture(cls) -> EnvironmentFingerprint:
        return cls.current()

    @property
    def scikit_learn_version(self) -> str:
        return self.sklearn_version

    def to_canonical_dict(self, include_digest: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "byteorder": self.byteorder,
            "joblib_version": self.joblib_version,
            "numpy_version": self.numpy_version,
            "platform_machine": self.platform_machine,
            "platform_system": self.platform_system,
            "python_implementation": self.python_implementation,
            "python_version": self.python_version,
            "scipy_version": self.scipy_version,
            "sklearn_version": self.sklearn_version,
            "threadpool_signature": list(self.threadpool_signature),
            "threadpoolctl_version": self.threadpoolctl_version,
        }
        if include_digest:
            payload["fingerprint_digest"] = self.fingerprint_digest
        return payload


@dataclasses.dataclass(frozen=True, slots=True)
class ModelTrainingInputBoundary:
    """Deeply bound training input identity with non-transferable verification state."""

    ordered_sample_ids: tuple[str, ...]
    dataset_digest: str
    source_lineage_digest: str
    target_contract_digest: str
    feature_pipeline_spec_digest: str
    knowledge_cutoff: datetime
    candidate_spec_digest: str
    numeric_policy: NumericPolicy
    environment_fingerprint_digest: str
    code_revision: str
    boundary_digest: str = dataclasses.field(init=False)
    _verification_token: object = dataclasses.field(
        default=None, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if (
            self.knowledge_cutoff.tzinfo is None
            or self.knowledge_cutoff.tzinfo.utcoffset(self.knowledge_cutoff) is None
        ):
            raise ValueError("knowledge_cutoff must be timezone-aware")
        required = {
            "dataset_digest": self.dataset_digest,
            "source_lineage_digest": self.source_lineage_digest,
            "target_contract_digest": self.target_contract_digest,
            "feature_pipeline_spec_digest": self.feature_pipeline_spec_digest,
            "candidate_spec_digest": self.candidate_spec_digest,
            "environment_fingerprint_digest": self.environment_fingerprint_digest,
            "code_revision": self.code_revision,
        }
        for name, value in required.items():
            if not value:
                raise ValueError(f"{name} must be non-empty")
        payload = {
            "candidate_spec_digest": self.candidate_spec_digest,
            "code_revision": self.code_revision,
            "dataset_digest": self.dataset_digest,
            "environment_fingerprint_digest": self.environment_fingerprint_digest,
            "feature_pipeline_spec_digest": self.feature_pipeline_spec_digest,
            "knowledge_cutoff": self.knowledge_cutoff.isoformat(),
            "numeric_policy": self.numeric_policy.to_canonical_dict(),
            "ordered_sample_ids": list(self.ordered_sample_ids),
            "source_lineage_digest": self.source_lineage_digest,
            "target_contract_digest": self.target_contract_digest,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        object.__setattr__(
            self,
            "boundary_digest",
            hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        )

    @property
    def is_verified(self) -> bool:
        return self._verification_token is _BOUNDARY_VERIFICATION_TOKEN

    @classmethod
    def create_and_verify(
        cls,
        samples: Sequence[StatisticalSample],
        target_contract: TargetContract,
        feature_pipeline_spec_digest: str,
        candidate_spec: MLCandidateSpec,
        knowledge_cutoff: datetime,
        environment: EnvironmentFingerprint,
        code_revision: str,
    ) -> ModelTrainingInputBoundary:
        valid_samples = StatisticalEvaluationInputBoundary.validate_dataset(samples)
        if candidate_spec.target_contract.contract_digest != target_contract.contract_digest:
            raise ValueError("candidate target contract does not match training target contract")
        if candidate_spec.feature_pipeline_spec_digest != feature_pipeline_spec_digest:
            raise ValueError(
                "candidate feature_pipeline_spec_digest does not match the fitted pipeline spec"
            )
        if candidate_spec.code_revision != code_revision:
            raise ValueError("candidate code_revision does not match training code_revision")
        for sample in valid_samples:
            if sample.target_knowledge_time > knowledge_cutoff:
                raise CausalLeakageError(
                    f"Future label leakage detected: sample '{sample.sample_id}' "
                    f"target knowledge time {sample.target_knowledge_time} exceeds "
                    f"training cutoff {knowledge_cutoff}"
                )
            if sample.target_semantics is not target_contract.target_semantics:
                raise ValueError(
                    f"Sample '{sample.sample_id}' target semantics do not match TargetContract"
                )
        boundary = cls(
            ordered_sample_ids=tuple(sample.sample_id for sample in valid_samples),
            dataset_digest=StatisticalEvaluationInputBoundary.compute_dataset_digest(
                valid_samples
            ),
            source_lineage_digest=(
                StatisticalEvaluationInputBoundary.compute_source_lineage_digest(
                    valid_samples
                )
            ),
            target_contract_digest=target_contract.contract_digest,
            feature_pipeline_spec_digest=feature_pipeline_spec_digest,
            knowledge_cutoff=knowledge_cutoff,
            candidate_spec_digest=candidate_spec.spec_digest,
            numeric_policy=candidate_spec.numeric_policy,
            environment_fingerprint_digest=environment.fingerprint_digest,
            code_revision=code_revision,
        )
        object.__setattr__(
            boundary, "_verification_token", _BOUNDARY_VERIFICATION_TOKEN
        )
        return boundary


@dataclasses.dataclass(frozen=True, slots=True)
class ModelTrainingManifest:
    """Verified scientific root for a completed model fit."""

    boundary_digest: str
    candidate_id: str
    fitted_feature_pipeline_digest: str
    model_state_digest: str
    target_contract_digest: str
    rng_context: RNGContext | None
    environment_fingerprint: EnvironmentFingerprint
    code_revision: str
    numeric_policy: NumericPolicy = DEFAULT_NUMERIC_POLICY
    audit_metadata: Mapping[str, str] = dataclasses.field(default_factory=dict)
    scientific_root_digest: str = dataclasses.field(init=False)
    _verification_token: object = dataclasses.field(
        default=None, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        for name in (
            "boundary_digest",
            "candidate_id",
            "fitted_feature_pipeline_digest",
            "model_state_digest",
            "target_contract_digest",
            "code_revision",
        ):
            if not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        object.__setattr__(
            self, "audit_metadata", _freeze_mapping(dict(self.audit_metadata))
        )
        payload = {
            "boundary_digest": self.boundary_digest,
            "candidate_id": self.candidate_id,
            "code_revision": self.code_revision,
            "environment_fingerprint_digest": (
                self.environment_fingerprint.fingerprint_digest
            ),
            "fitted_feature_pipeline_digest": self.fitted_feature_pipeline_digest,
            "model_state_digest": self.model_state_digest,
            "numeric_policy": self.numeric_policy.to_canonical_dict(),
            "rng_context": (
                self.rng_context.to_canonical_dict() if self.rng_context else None
            ),
            "target_contract_digest": self.target_contract_digest,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        object.__setattr__(
            self,
            "scientific_root_digest",
            hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        )

    @property
    def is_verified(self) -> bool:
        return self._verification_token is _MANIFEST_VERIFICATION_TOKEN

    @classmethod
    def create(
        cls,
        *,
        boundary: ModelTrainingInputBoundary,
        candidate_spec: MLCandidateSpec,
        fitted_feature_pipeline_digest: str,
        model_state_digest: str,
        environment_fingerprint: EnvironmentFingerprint,
        code_revision: str,
        audit_metadata: Mapping[str, str] | None = None,
    ) -> ModelTrainingManifest:
        if not boundary.is_verified:
            raise ValueError("ModelTrainingManifest requires a verified training boundary")
        if boundary.candidate_spec_digest != candidate_spec.spec_digest:
            raise ValueError("boundary candidate identity does not match candidate_spec")
        if boundary.target_contract_digest != candidate_spec.target_contract.contract_digest:
            raise ValueError("boundary target contract does not match candidate_spec")
        if boundary.feature_pipeline_spec_digest != candidate_spec.feature_pipeline_spec_digest:
            raise ValueError("boundary feature pipeline spec does not match candidate_spec")
        if boundary.environment_fingerprint_digest != environment_fingerprint.fingerprint_digest:
            raise ValueError("boundary environment does not match manifest environment")
        if boundary.code_revision != code_revision or candidate_spec.code_revision != code_revision:
            raise ValueError("code revision mismatch across boundary/candidate/manifest")
        manifest = cls(
            boundary_digest=boundary.boundary_digest,
            candidate_id=candidate_spec.candidate_id,
            fitted_feature_pipeline_digest=fitted_feature_pipeline_digest,
            model_state_digest=model_state_digest,
            target_contract_digest=candidate_spec.target_contract.contract_digest,
            rng_context=candidate_spec.rng_context,
            environment_fingerprint=environment_fingerprint,
            code_revision=code_revision,
            numeric_policy=candidate_spec.numeric_policy,
            audit_metadata=dict(audit_metadata or {}),
        )
        object.__setattr__(
            manifest, "_verification_token", _MANIFEST_VERIFICATION_TOKEN
        )
        return manifest

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
