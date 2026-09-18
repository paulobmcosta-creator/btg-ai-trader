"""Core domain abstractions, target contracts, and interfaces for the ML Engine."""

from __future__ import annotations

import hashlib
import json
import types
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal, localcontext
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from btg_ai_trader.statistical_baselines.domain import (
    PredictionInput,
    PredictionResult,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.metrics import NumericPolicy


class FeatureType(str, Enum):
    """Supported data types for individual features in a FeatureSchema."""

    NUMERIC = "NUMERIC"
    CATEGORICAL = "CATEGORICAL"
    BOOLEAN = "BOOLEAN"


class MissingnessPolicy(str, Enum):
    """Explicit policy for handling missing values in feature extraction."""

    REJECT = "REJECT"
    CONSTANT = "CONSTANT"
    INDICATOR = "INDICATOR"


class UnknownCategoryPolicy(str, Enum):
    """Explicit policy for handling unseen categories during inference."""

    REJECT = "REJECT"
    DECLARED_FALLBACK = "DECLARED_FALLBACK"


class ModelEvaluationDisposition(str, Enum):
    """Formal disposition of a model evaluation under Quantitative Protocol 0E-F."""

    FAVORABLE = "FAVORABLE"
    UNFAVORABLE = "UNFAVORABLE"
    INCONCLUSIVE = "INCONCLUSIVE"
    INVALID = "INVALID"
    CONDITIONAL = "CONDITIONAL"


class EvaluationScope(str, Enum):
    """Explicit evaluation scope partition under Quantitative Protocol 0E-F."""

    MODEL = "MODEL"
    STRATEGY = "STRATEGY"
    COMPOSITE_SYSTEM = "COMPOSITE_SYSTEM"


class MetricDirection(str, Enum):
    """Optimization direction for selection metrics."""

    MINIMIZE = "MINIMIZE"
    MAXIMIZE = "MAXIMIZE"


class TrainingFailureError(RuntimeError):
    """Raised when an estimator training procedure encounters a fatal failure."""


class InvalidCandidateError(ValueError):
    """Raised when an invalid candidate specification or hyperparameter is supplied."""


class ModelNotFittedError(ValueError):
    """Raised when an operation requiring fitted state is invoked on an unfitted candidate."""



def _deep_freeze(val: Any) -> Any:
    """Recursively freeze mapping and sequence structures into immutable types."""
    if isinstance(val, Mapping):
        return types.MappingProxyType({k: _deep_freeze(v) for k, v in val.items()})
    if isinstance(val, list | tuple):
        return tuple(_deep_freeze(x) for x in val)
    return val


def freeze_mapping(mapping: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return deeply immutable mapping proxy."""
    return types.MappingProxyType({k: _deep_freeze(v) for k, v in mapping.items()})


@dataclass(frozen=True, slots=True)
class TargetContract:
    """Explicit, immutable contract binding target semantics, horizon, and causal availability."""

    target_name: str
    target_semantics: TargetSemantics
    forecast_horizon_steps: int
    knowledge_delay_steps: int = 0
    description: str = ""
    contract_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.target_name or not isinstance(self.target_name, str):
            raise ValueError("target_name must be a non-empty string")
        if not isinstance(self.target_semantics, TargetSemantics):
            raise TypeError(
                f"target_semantics must be TargetSemantics, got {type(self.target_semantics)}"
            )
        if self.forecast_horizon_steps <= 0:
            raise ValueError(
                f"forecast_horizon_steps must be positive, got {self.forecast_horizon_steps}"
            )
        if self.knowledge_delay_steps < 0:
            raise ValueError(
                f"knowledge_delay_steps must be non-negative, got {self.knowledge_delay_steps}"
            )

        canonical_dict = self.to_canonical_dict()
        serialized = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        object.__setattr__(self, "contract_digest", digest)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "forecast_horizon_steps": self.forecast_horizon_steps,
            "knowledge_delay_steps": self.knowledge_delay_steps,
            "target_name": self.target_name,
            "target_semantics": self.target_semantics.value,
        }


@dataclass(frozen=True, slots=True)
class RNGContext:
    """Explicit pseudorandom number generator context for deterministic and stochastic models."""

    algorithm: str
    seed: int
    stream_semantics: str = "default"
    library_version: str = ""

    def __post_init__(self) -> None:
        if not self.algorithm or not isinstance(self.algorithm, str):
            raise ValueError("algorithm must be a non-empty string")
        if not isinstance(self.seed, int):
            raise TypeError(f"seed must be an integer, got {type(self.seed).__name__}")
        if self.seed < 0:
            raise ValueError(f"seed must be non-negative, got {self.seed}")
        if not self.stream_semantics:
            raise ValueError("stream_semantics must be a non-empty string")

    @property
    def context_digest(self) -> str:
        serialized = json.dumps(self.to_canonical_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def child_context(self, stream_qualifier: str) -> RNGContext:
        derived_seed = int(
            hashlib.sha256(f"{self.seed}:{stream_qualifier}".encode()).hexdigest()[:8], 16
        )
        return RNGContext(
            algorithm=self.algorithm,
            seed=derived_seed,
            stream_semantics=f"{self.stream_semantics}:{stream_qualifier}",
            library_version=self.library_version,
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "library_version": self.library_version,
            "seed": self.seed,
            "stream_semantics": self.stream_semantics,
        }


@dataclass(frozen=True, slots=True)
class MLCandidateSpec:
    """Immutable scientific candidate specification binding family, parameters, and policies."""

    family: str
    hyperparameters: Mapping[str, Any]
    target_contract: TargetContract
    feature_pipeline_spec_digest: str
    rng_context: RNGContext | None
    numeric_policy: NumericPolicy
    code_revision: str
    candidate_id: str = field(init=False)
    spec_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.family or not isinstance(self.family, str):
            raise ValueError("family must be a non-empty string")
        if not self.code_revision:
            raise ValueError("code_revision must be a non-empty string")
        if not self.feature_pipeline_spec_digest:
            raise ValueError("feature_pipeline_spec_digest must be non-empty")

        canonical_hyperparams = self._canonicalize_hyperparams(self.hyperparameters)
        object.__setattr__(self, "hyperparameters", freeze_mapping(canonical_hyperparams))

        canonical_dict = {
            "code_revision": self.code_revision,
            "family": self.family,
            "feature_pipeline_spec_digest": self.feature_pipeline_spec_digest,
            "hyperparameters": canonical_hyperparams,
            "numeric_policy": self.numeric_policy.to_canonical_dict(),
            "rng_context": self.rng_context.to_canonical_dict() if self.rng_context else None,
            "target_contract_digest": self.target_contract.contract_digest,
        }
        serialized = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        object.__setattr__(self, "spec_digest", digest)
        object.__setattr__(self, "candidate_id", f"ml:{self.family}:{digest[:12]}")

    @staticmethod
    def _canonicalize_hyperparams(params: Mapping[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k in sorted(params.keys()):
            v = params[k]
            if isinstance(v, Decimal):
                out[k] = str(v)
            elif isinstance(v, Mapping):
                out[k] = MLCandidateSpec._canonicalize_hyperparams(v)
            elif isinstance(v, list | tuple):
                out[k] = [str(x) if isinstance(x, Decimal) else x for x in v]
            else:
                out[k] = v
        return out

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "code_revision": self.code_revision,
            "family": self.family,
            "feature_pipeline_spec_digest": self.feature_pipeline_spec_digest,
            "hyperparameters": dict(self.hyperparameters),
            "numeric_policy": self.numeric_policy.to_canonical_dict(),
            "rng_context": self.rng_context.to_canonical_dict() if self.rng_context else None,
            "target_contract_digest": self.target_contract.contract_digest,
        }


@runtime_checkable
class PredictiveCandidate(Protocol):
    """Protocol implemented by all supported Machine Learning candidate families in Sprint 5."""

    @property
    def spec(self) -> MLCandidateSpec: ...

    @property
    def is_fitted(self) -> bool: ...

    @property
    def model_state_digest(self) -> str: ...

    def fit(self, X: Any, y: Any) -> None: ...

    def predict(
        self, inputs: Sequence[PredictionInput], fitted_pipeline: Any
    ) -> list[PredictionResult]: ...


def apply_numeric_policy(val: Decimal, policy: NumericPolicy) -> Decimal:
    """Normalize and round Decimal according to NumericPolicy context."""
    with localcontext(policy.get_context()):
        return +val
