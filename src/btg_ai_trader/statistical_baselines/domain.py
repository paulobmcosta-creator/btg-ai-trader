"""Domain models and core temporal sample abstractions for statistical baselines."""

from __future__ import annotations

import hashlib
import json
import types
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any


class TargetSemantics(str, Enum):
    """Classification of target values for baseline estimation and evaluation."""

    CONTINUOUS = "CONTINUOUS"
    BINARY_PROBABILITY = "BINARY_PROBABILITY"
    CATEGORICAL = "CATEGORICAL"


class EvaluationRole(str, Enum):
    """Epistemological role of data partitions in accordance with Protocol 0E-C."""

    DEVELOPMENT = "DEVELOPMENT"
    TRAINING_FIT = "TRAINING_FIT"
    VALIDATION_SELECTION = "VALIDATION_SELECTION"
    PROTECTED_TEST = "PROTECTED_TEST"


class CausalLeakageError(ValueError):
    """Raised when look-ahead or causal ordering violation is detected."""


class ParityViolationError(ValueError):
    """Raised when candidate evaluation contexts differ in model comparison."""


class ProtectedEvidenceReuseError(ValueError):
    """Raised when protected test evidence is reused after candidate adaptation."""


def _validate_timezone_aware(dt: datetime, field_name: str) -> None:
    """Ensure datetime is timezone-aware to prevent local/system time ambiguity."""
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime, got naive {dt!r}")


def _deep_freeze_value(val: Any) -> Any:
    """Recursively freeze mapping and sequence structures into immutable proxies."""
    if isinstance(val, Mapping):
        return types.MappingProxyType({k: _deep_freeze_value(v) for k, v in val.items()})
    if isinstance(val, list | tuple):
        return tuple(_deep_freeze_value(x) for x in val)
    return val


def _freeze_mapping(mapping: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return deeply immutable mapping proxy."""
    return types.MappingProxyType({k: _deep_freeze_value(v) for k, v in mapping.items()})


@dataclass(frozen=True, slots=True)
class PredictionInput:
    """Causally safe prediction input surface strictly omitting target fields."""

    sample_id: str
    feature_knowledge_time: datetime
    target_semantics: TargetSemantics
    reference_value: Decimal | None = None
    information_interval: tuple[datetime, datetime] | None = None
    source_lineage: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.sample_id or not isinstance(self.sample_id, str):
            raise ValueError("sample_id must be a non-empty string")

        _validate_timezone_aware(self.feature_knowledge_time, "feature_knowledge_time")

        if self.information_interval is not None:
            start, end = self.information_interval
            _validate_timezone_aware(start, "information_interval.start")
            _validate_timezone_aware(end, "information_interval.end")
            if start > end:
                raise ValueError(
                    f"information_interval start ({start}) cannot be after end ({end})"
                )

        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class StatisticalSample:
    """Explicit temporal sample contract enforcing feature and label availability."""

    sample_id: str
    feature_knowledge_time: datetime
    target_knowledge_time: datetime
    target_value: Decimal | int | str
    target_semantics: TargetSemantics
    reference_value: Decimal | None = None
    information_interval: tuple[datetime, datetime] | None = None
    source_lineage: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.sample_id or not isinstance(self.sample_id, str):
            raise ValueError("sample_id must be a non-empty string")

        _validate_timezone_aware(self.feature_knowledge_time, "feature_knowledge_time")
        _validate_timezone_aware(self.target_knowledge_time, "target_knowledge_time")

        if self.feature_knowledge_time > self.target_knowledge_time:
            raise CausalLeakageError(
                f"feature_knowledge_time ({self.feature_knowledge_time}) cannot be later than "
                f"target_knowledge_time ({self.target_knowledge_time})"
            )

        if self.information_interval is not None:
            start, end = self.information_interval
            _validate_timezone_aware(start, "information_interval.start")
            _validate_timezone_aware(end, "information_interval.end")
            if start > end:
                raise ValueError(
                    f"information_interval start ({start}) cannot be after end ({end})"
                )

        # Validate and canonicalize target value consistency with target semantics
        if self.target_semantics is TargetSemantics.CONTINUOUS:
            if not isinstance(self.target_value, Decimal):
                val_type = type(self.target_value).__name__
                raise TypeError(
                    f"target_value for CONTINUOUS semantics must be Decimal, got {val_type}"
                )
        elif self.target_semantics is TargetSemantics.BINARY_PROBABILITY:
            if isinstance(self.target_value, bool):
                raise TypeError(
                    "target_value for BINARY_PROBABILITY must be int or Decimal, got bool"
                )
            if isinstance(self.target_value, Decimal):
                if self.target_value not in (Decimal(0), Decimal(1)):
                    raise ValueError(
                        f"target_value for BINARY_PROBABILITY must be 0 or 1, "
                        f"got {self.target_value}"
                    )
            elif isinstance(self.target_value, int):
                if self.target_value not in (0, 1):
                    raise ValueError(
                        f"target_value for BINARY_PROBABILITY must be 0 or 1, "
                        f"got {self.target_value}"
                    )
                # Canonicalize int to Decimal internally
                object.__setattr__(self, "target_value", Decimal(self.target_value))
            else:
                val_type = type(self.target_value).__name__
                raise TypeError(
                    f"target_value for BINARY_PROBABILITY must be int or Decimal, got {val_type}"
                )
        elif self.target_semantics is TargetSemantics.CATEGORICAL:
            if not isinstance(self.target_value, str):
                val_type = type(self.target_value).__name__
                raise TypeError(
                    f"target_value for CATEGORICAL semantics must be str, got {val_type}"
                )
        else:
            raise ValueError(f"Unsupported target_semantics: {self.target_semantics}")

        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def is_causally_admissible_for_fit(self, knowledge_cutoff: datetime) -> bool:
        """Check whether the sample's target was causally available at knowledge_cutoff."""
        _validate_timezone_aware(knowledge_cutoff, "knowledge_cutoff")
        return self.target_knowledge_time <= knowledge_cutoff

    def to_prediction_input(self) -> PredictionInput:
        """Convert sample into a causally safe prediction input surface without target fields."""
        return PredictionInput(
            sample_id=self.sample_id,
            feature_knowledge_time=self.feature_knowledge_time,
            target_semantics=self.target_semantics,
            reference_value=self.reference_value,
            information_interval=self.information_interval,
            source_lineage=self.source_lineage,
            metadata=self.metadata,
        )


@dataclass(frozen=True, slots=True)
class PredictionResult:
    """Result of a baseline prediction for a given sample."""

    sample_id: str
    prediction_time: datetime
    predicted_value: Decimal | None = None
    predicted_probability: Decimal | None = None
    predicted_class: str | None = None
    is_cold_start: bool = False
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_timezone_aware(self.prediction_time, "prediction_time")
        if self.predicted_probability is not None:
            if not (Decimal(0) <= self.predicted_probability <= Decimal(1)):
                raise ValueError(
                    f"predicted_probability must be in [0, 1], got {self.predicted_probability}"
                )
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class CandidateIdentity:
    """Version-specific and deterministic candidate identity derived from configuration."""

    baseline_type: str
    parameters: Mapping[str, Any]
    target_semantics: TargetSemantics
    code_revision: str
    identity_hash: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.baseline_type:
            raise ValueError("baseline_type must be a non-empty string")
        if not self.code_revision:
            raise ValueError("code_revision must be a non-empty string")

        canonical_params = self._canonicalize_params(self.parameters)
        canonical_dict = {
            "baseline_type": self.baseline_type,
            "code_revision": self.code_revision,
            "parameters": canonical_params,
            "target_semantics": self.target_semantics.value,
        }
        serialized = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        object.__setattr__(self, "identity_hash", digest)
        # Deeply freeze parameters so external mutation does not affect state
        object.__setattr__(self, "parameters", _freeze_mapping(canonical_params))

    @property
    def candidate_id(self) -> str:
        """Deterministic candidate identifier derived from baseline_type and identity_hash."""
        return f"{self.baseline_type}:{self.identity_hash[:12]}"

    @staticmethod
    def _canonicalize_params(params: Mapping[str, Any]) -> dict[str, Any]:
        """Convert parameter mapping into deterministic serializable structure."""
        out: dict[str, Any] = {}
        for k in sorted(params.keys()):
            v = params[k]
            if isinstance(v, Decimal):
                out[k] = str(v)
            elif isinstance(v, int | float | str | bool) or v is None:
                out[k] = v
            elif isinstance(v, Mapping):
                out[k] = CandidateIdentity._canonicalize_params(v)
            elif isinstance(v, list | tuple):
                out[k] = [str(x) if isinstance(x, Decimal) else x for x in v]
            else:
                out[k] = str(v)
        return out
