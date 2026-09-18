"""Core domain abstractions and immutable identities for the Sprint 5 research ML engine."""

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
    """Supported feature data types."""

    NUMERIC = "NUMERIC"
    CATEGORICAL = "CATEGORICAL"
    BOOLEAN = "BOOLEAN"


class MissingnessPolicy(str, Enum):
    """Explicit feature missingness policies."""

    REJECT = "REJECT"
    CONSTANT = "CONSTANT"
    INDICATOR = "INDICATOR"


class UnknownCategoryPolicy(str, Enum):
    """Explicit policy for categorical values unseen during fitting."""

    REJECT = "REJECT"
    DECLARED_FALLBACK = "DECLARED_FALLBACK"


class ModelEvaluationDisposition(str, Enum):
    """Protocol 0E-F model-evaluation disposition."""

    FAVORABLE = "FAVORABLE"
    UNFAVORABLE = "UNFAVORABLE"
    INCONCLUSIVE = "INCONCLUSIVE"
    INVALID = "INVALID"
    CONDITIONAL = "CONDITIONAL"


class EvaluationScope(str, Enum):
    """Evaluation-scope partition from Protocol 0E-F."""

    MODEL = "MODEL"
    STRATEGY = "STRATEGY"
    COMPOSITE_SYSTEM = "COMPOSITE_SYSTEM"


class MetricDirection(str, Enum):
    """Optimization direction for a predeclared validation metric."""

    MINIMIZE = "MINIMIZE"
    MAXIMIZE = "MAXIMIZE"


class TrainingFailureError(RuntimeError):
    """Raised when model fitting fails safely."""


class InvalidCandidateError(ValueError):
    """Raised when a candidate specification is invalid."""


class ModelNotFittedError(ValueError):
    """Raised when fitted state is required but absent."""


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return types.MappingProxyType({str(k): _deep_freeze(v) for k, v in value.items()})
    if isinstance(value, list | tuple):
        return tuple(_deep_freeze(v) for v in value)
    return value


def freeze_mapping(mapping: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return a recursively immutable mapping."""

    return types.MappingProxyType({str(k): _deep_freeze(v) for k, v in mapping.items()})


@dataclass(frozen=True, slots=True)
class TargetContract:
    """Explicit immutable target semantics and causal availability contract."""

    target_name: str
    target_semantics: TargetSemantics
    forecast_horizon_steps: int
    knowledge_delay_steps: int = 0
    description: str = ""
    contract_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.target_name, str) or not self.target_name:
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
        payload = json.dumps(
            self.to_canonical_dict(), sort_keys=True, separators=(",", ":")
        )
        object.__setattr__(
            self, "contract_digest", hashlib.sha256(payload.encode("utf-8")).hexdigest()
        )

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
    """Factual scikit-learn integer random_state provenance.

    The engine does not claim that a NumPy BitGenerator is directly supplied to estimators.
    Supported stochastic S5 estimators consume the integer seed through scikit-learn's
    random_state contract.
    """

    algorithm: str
    seed: int
    stream_semantics: str = "candidate"
    library_version: str = ""

    def __post_init__(self) -> None:
        if self.algorithm != "sklearn_random_state":
            raise ValueError(
                "algorithm must be 'sklearn_random_state'; S5 estimators consume "
                "scikit-learn integer random_state semantics"
            )
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise TypeError(f"seed must be an integer, got {type(self.seed).__name__}")
        if self.seed < 0:
            raise ValueError(f"seed must be non-negative, got {self.seed}")
        if not self.stream_semantics:
            raise ValueError("stream_semantics must be a non-empty string")

    @property
    def context_digest(self) -> str:
        serialized = json.dumps(
            self.to_canonical_dict(), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def child_context(self, stream_qualifier: str) -> RNGContext:
        if not stream_qualifier:
            raise ValueError("stream_qualifier must be non-empty")
        material = f"{self.context_digest}:{stream_qualifier}"
        derived_seed = int(hashlib.sha256(material.encode("utf-8")).hexdigest()[:8], 16)
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
    """Immutable scientific identity for one ML candidate specification."""

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
        if not isinstance(self.family, str) or not self.family:
            raise ValueError("family must be a non-empty string")
        if not self.code_revision:
            raise ValueError("code_revision must be a non-empty string")
        if not self.feature_pipeline_spec_digest:
            raise ValueError("feature_pipeline_spec_digest must be non-empty")
        canonical_hyperparams = self._canonicalize_hyperparams(self.hyperparameters)
        object.__setattr__(self, "hyperparameters", freeze_mapping(canonical_hyperparams))
        payload = {
            "code_revision": self.code_revision,
            "family": self.family,
            "feature_pipeline_spec_digest": self.feature_pipeline_spec_digest,
            "hyperparameters": canonical_hyperparams,
            "numeric_policy": self.numeric_policy.to_canonical_dict(),
            "rng_context": self.rng_context.to_canonical_dict() if self.rng_context else None,
            "target_contract_digest": self.target_contract.contract_digest,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        object.__setattr__(self, "spec_digest", digest)
        object.__setattr__(self, "candidate_id", f"ml:{self.family}:{digest[:12]}")

    @staticmethod
    def _canonicalize_hyperparams(params: Mapping[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key in sorted(params):
            value = params[key]
            if isinstance(value, Decimal):
                out[key] = str(value)
            elif isinstance(value, Mapping):
                out[key] = MLCandidateSpec._canonicalize_hyperparams(value)
            elif isinstance(value, list | tuple):
                out[key] = [str(v) if isinstance(v, Decimal) else v for v in value]
            else:
                out[key] = value
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
    """Common interface for S5 predictive candidates."""

    @property
    def spec(self) -> MLCandidateSpec: ...

    @property
    def is_fitted(self) -> bool: ...

    @property
    def model_state_digest(self) -> str: ...

    def fit(self, X: Any, y: Any) -> None: ...

    def predict(
        self,
        inputs: Sequence[PredictionInput],
        fitted_pipeline: Any,
    ) -> list[PredictionResult]: ...


def apply_numeric_policy(value: Decimal, policy: NumericPolicy) -> Decimal:
    """Apply the explicit Decimal context without consulting global Decimal state."""

    with localcontext(policy.get_context()):
        return +value
