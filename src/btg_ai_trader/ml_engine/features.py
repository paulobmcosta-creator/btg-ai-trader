"""Causal deterministic feature schemas and train-only fitted transformations."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from btg_ai_trader.ml_engine.domain import (
    FeatureType,
    MissingnessPolicy,
    UnknownCategoryPolicy,
    freeze_mapping,
)
from btg_ai_trader.statistical_baselines.domain import PredictionInput, StatisticalSample


def _finite_float(value: object, feature_name: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid numeric value {value!r} for feature '{feature_name}'"
        ) from exc
    if not math.isfinite(parsed):
        raise ValueError(
            f"Non-finite numeric value {value!r} for feature '{feature_name}' is forbidden"
        )
    return parsed


def _parse_boolean(value: object, feature_name: str) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    token = str(value).strip().lower()
    if token in {"true", "1", "t", "yes"}:
        return 1.0
    if token in {"false", "0", "f", "no"}:
        return 0.0
    raise ValueError(
        f"Invalid boolean literal {value!r} for feature '{feature_name}'"
    )


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    """One explicitly governed feature."""

    name: str
    feature_type: FeatureType
    missingness_policy: MissingnessPolicy = MissingnessPolicy.REJECT
    constant_fill_value: float | str | bool | None = None
    unknown_category_policy: UnknownCategoryPolicy = UnknownCategoryPolicy.REJECT
    fallback_category: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Feature name must be a non-empty string")
        if not isinstance(self.feature_type, FeatureType):
            raise TypeError(f"feature_type must be FeatureType, got {type(self.feature_type)}")
        if not isinstance(self.missingness_policy, MissingnessPolicy):
            raise TypeError(
                f"missingness_policy must be MissingnessPolicy, got {type(self.missingness_policy)}"
            )
        if not isinstance(self.unknown_category_policy, UnknownCategoryPolicy):
            raise TypeError(
                "unknown_category_policy must be UnknownCategoryPolicy, "
                f"got {type(self.unknown_category_policy)}"
            )
        if self.missingness_policy in (
            MissingnessPolicy.CONSTANT,
            MissingnessPolicy.INDICATOR,
        ) and self.constant_fill_value is None:
            raise ValueError(
                f"Feature {self.name}: constant_fill_value required when policy is "
                f"{self.missingness_policy.value}"
            )
        if self.unknown_category_policy is UnknownCategoryPolicy.DECLARED_FALLBACK:
            if self.feature_type is not FeatureType.CATEGORICAL:
                raise ValueError("DECLARED_FALLBACK is only valid for categorical features")
            if not self.fallback_category:
                raise ValueError(
                    f"Feature {self.name}: fallback_category required when policy is "
                    "DECLARED_FALLBACK"
                )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "constant_fill_value": self.constant_fill_value,
            "fallback_category": self.fallback_category,
            "feature_type": self.feature_type.value,
            "missingness_policy": self.missingness_policy.value,
            "name": self.name,
            "unknown_category_policy": self.unknown_category_policy.value,
        }


@dataclass(frozen=True, slots=True)
class FeatureSchema:
    """Immutable deterministically ordered feature schema."""

    features: Sequence[FeatureSpec] = field(default_factory=tuple)
    schema_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.features:
            raise ValueError("FeatureSchema must contain at least one feature")
        ordered = tuple(sorted(self.features, key=lambda feature: feature.name))
        names = [feature.name for feature in ordered]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate feature names found in FeatureSchema")
        object.__setattr__(self, "features", ordered)
        payload = [feature.to_canonical_dict() for feature in ordered]
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        object.__setattr__(
            self, "schema_digest", hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        )

    def __len__(self) -> int:
        return len(self.features)


@dataclass(frozen=True, slots=True)
class FeaturePipelineSpec:
    """Declarative feature-pipeline specification."""

    schema: FeatureSchema
    normalize: bool = False
    spec_digest: str = field(init=False)

    def __post_init__(self) -> None:
        payload = {
            "normalize": self.normalize,
            "schema_digest": self.schema.schema_digest,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        object.__setattr__(
            self, "spec_digest", hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        )


@dataclass(frozen=True, slots=True)
class FittedFeaturePipeline:
    """Feature transformer whose learned state comes only from the fit domain."""

    spec: FeaturePipelineSpec
    learned_means: Mapping[str, float]
    learned_scales: Mapping[str, float]
    learned_vocabularies: Mapping[str, Mapping[str, int]]
    output_feature_names: tuple[str, ...]
    pipeline_digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "learned_means", freeze_mapping(self.learned_means))
        object.__setattr__(self, "learned_scales", freeze_mapping(self.learned_scales))
        object.__setattr__(
            self, "learned_vocabularies", freeze_mapping(self.learned_vocabularies)
        )
        payload = {
            "learned_means": {
                key: format(value, ".17g")
                for key, value in sorted(self.learned_means.items())
            },
            "learned_scales": {
                key: format(value, ".17g")
                for key, value in sorted(self.learned_scales.items())
            },
            "learned_vocabularies": {
                key: dict(sorted(value.items()))
                for key, value in sorted(self.learned_vocabularies.items())
            },
            "output_feature_names": list(self.output_feature_names),
            "spec_digest": self.spec.spec_digest,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        object.__setattr__(
            self, "pipeline_digest", hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        )

    @staticmethod
    def _prediction_inputs(
        inputs: Sequence[StatisticalSample | PredictionInput],
    ) -> tuple[PredictionInput, ...]:
        converted: list[PredictionInput] = []
        for item in inputs:
            if isinstance(item, StatisticalSample):
                converted.append(item.to_prediction_input())
            elif isinstance(item, PredictionInput):
                converted.append(item)
            else:
                raise TypeError(
                    "Expected StatisticalSample or PredictionInput, "
                    f"got {type(item).__name__}"
                )
        return tuple(converted)

    @classmethod
    def fit(
        cls,
        spec: FeaturePipelineSpec,
        inputs: Sequence[StatisticalSample | PredictionInput],
    ) -> FittedFeaturePipeline:
        if not inputs:
            raise ValueError("Cannot fit FeaturePipeline on empty inputs")
        pred_inputs = cls._prediction_inputs(inputs)

        means: dict[str, float] = {}
        scales: dict[str, float] = {}
        vocabularies: dict[str, dict[str, int]] = {}
        output_names: list[str] = []

        for feature in spec.schema.features:
            if feature.feature_type is FeatureType.NUMERIC:
                values: list[float] = []
                for item in pred_inputs:
                    raw = item.feature_metadata.get(feature.name)
                    missing = raw is None or raw == ""
                    if missing:
                        if feature.missingness_policy is MissingnessPolicy.REJECT:
                            raise ValueError(
                                f"Feature '{feature.name}' missing for sample "
                                f"'{item.sample_id}' during fit"
                            )
                        raw = feature.constant_fill_value
                    values.append(_finite_float(raw, feature.name))
                array = np.asarray(values, dtype=np.float64)
                mean = float(np.mean(array))
                scale = float(np.std(array))
                if scale < 1e-12:
                    scale = 1.0
                means[feature.name] = mean
                scales[feature.name] = scale
                output_names.append(feature.name)
            elif feature.feature_type is FeatureType.CATEGORICAL:
                categories: set[str] = set()
                for item in pred_inputs:
                    raw = item.feature_metadata.get(feature.name)
                    missing = raw is None or raw == ""
                    if missing:
                        if feature.missingness_policy is MissingnessPolicy.REJECT:
                            raise ValueError(
                                f"Feature '{feature.name}' missing for sample "
                                f"'{item.sample_id}' during fit"
                            )
                        raw = feature.constant_fill_value
                    categories.add(str(raw))
                ordered = sorted(categories)
                vocabularies[feature.name] = {
                    value: index for index, value in enumerate(ordered)
                }
                if (
                    feature.unknown_category_policy
                    is UnknownCategoryPolicy.DECLARED_FALLBACK
                    and str(feature.fallback_category) not in vocabularies[feature.name]
                ):
                    raise ValueError(
                        f"Declared fallback category '{feature.fallback_category}' was not "
                        "present in the fit-domain vocabulary"
                    )
                output_names.append(feature.name)
            else:
                for item in pred_inputs:
                    raw = item.feature_metadata.get(feature.name)
                    missing = raw is None or raw == ""
                    if missing:
                        if feature.missingness_policy is MissingnessPolicy.REJECT:
                            raise ValueError(
                                f"Feature '{feature.name}' missing for sample "
                                f"'{item.sample_id}' during fit"
                            )
                        raw = feature.constant_fill_value
                    _parse_boolean(raw, feature.name)
                output_names.append(feature.name)

            if feature.missingness_policy is MissingnessPolicy.INDICATOR:
                output_names.append(f"{feature.name}__missing")

        return cls(
            spec=spec,
            learned_means=means,
            learned_scales=scales,
            learned_vocabularies=vocabularies,
            output_feature_names=tuple(output_names),
        )

    def transform(self, inputs: Sequence[PredictionInput]) -> np.ndarray:
        if not inputs:
            return np.empty((0, len(self.output_feature_names)), dtype=np.float64)

        matrix = np.zeros(
            (len(inputs), len(self.output_feature_names)), dtype=np.float64
        )
        for row_index, item in enumerate(inputs):
            column_index = 0
            for feature in self.spec.schema.features:
                raw: object = item.feature_metadata.get(feature.name)
                missing = raw is None or raw == ""
                if missing:
                    if feature.missingness_policy is MissingnessPolicy.REJECT:
                        raise ValueError(
                            f"Missing value for feature '{feature.name}' in sample "
                            f"'{item.sample_id}'"
                        )
                    raw = feature.constant_fill_value

                if feature.feature_type is FeatureType.NUMERIC:
                    value = _finite_float(raw, feature.name)
                    if self.spec.normalize:
                        value = (
                            value - self.learned_means[feature.name]
                        ) / self.learned_scales[feature.name]
                    matrix[row_index, column_index] = value
                elif feature.feature_type is FeatureType.CATEGORICAL:
                    token = str(raw)
                    vocabulary = self.learned_vocabularies[feature.name]
                    if token not in vocabulary:
                        if (
                            feature.unknown_category_policy
                            is UnknownCategoryPolicy.REJECT
                        ):
                            raise ValueError(
                                f"Unknown category '{token}' for feature '{feature.name}' "
                                f"in sample '{item.sample_id}'"
                            )
                        token = str(feature.fallback_category)
                    matrix[row_index, column_index] = float(vocabulary[token])
                else:
                    matrix[row_index, column_index] = _parse_boolean(
                        raw, feature.name
                    )
                column_index += 1

                if feature.missingness_policy is MissingnessPolicy.INDICATOR:
                    matrix[row_index, column_index] = 1.0 if missing else 0.0
                    column_index += 1

        return matrix
