"""Causal, deterministic feature schema, specifications, and pipeline for ML models."""

from __future__ import annotations

import hashlib
import json
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

__all__ = [
    "FeaturePipelineSpec",
    "FeatureSchema",
    "FeatureSpec",
    "FeatureType",
    "FittedFeaturePipeline",
    "MissingnessPolicy",
    "UnknownCategoryPolicy",
]


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    """Specification of an individual feature extracted from PredictionInput metadata."""

    name: str
    feature_type: FeatureType
    missingness_policy: MissingnessPolicy = MissingnessPolicy.REJECT
    constant_fill_value: float | str | None = None
    unknown_category_policy: UnknownCategoryPolicy = UnknownCategoryPolicy.REJECT
    fallback_category: str | None = None

    def __post_init__(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Feature name must be a non-empty string")
        if not isinstance(self.feature_type, FeatureType):
            raise TypeError(f"feature_type must be FeatureType, got {type(self.feature_type)}")
        if not isinstance(self.missingness_policy, MissingnessPolicy):
            raise TypeError(
                f"missingness_policy must be MissingnessPolicy, got {type(self.missingness_policy)}"
            )
        if not isinstance(self.unknown_category_policy, UnknownCategoryPolicy):
            raise TypeError(
                f"unknown_category_policy must be UnknownCategoryPolicy, "
                f"got {type(self.unknown_category_policy)}"
            )

        if self.missingness_policy is MissingnessPolicy.CONSTANT:
            if self.constant_fill_value is None:
                raise ValueError(
                    f"Feature {self.name}: constant_fill_value required when policy is CONSTANT"
                )
        if self.unknown_category_policy is UnknownCategoryPolicy.DECLARED_FALLBACK:
            if self.fallback_category is None:
                raise ValueError(
                    f"Feature {self.name}: fallback_category required when "
                    f"policy is DECLARED_FALLBACK"
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
    """Immutable schema defining the complete set of features in strictly deterministic order."""

    features: Sequence[FeatureSpec] = field(default_factory=tuple)
    schema_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.features:
            raise ValueError("FeatureSchema must contain at least one feature")
        # Enforce deterministic ordering by sorting features by name
        sorted_features = tuple(sorted(self.features, key=lambda f: f.name))
        names = [f.name for f in sorted_features]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate feature names found in FeatureSchema")
        object.__setattr__(self, "features", sorted_features)

        canonical_list = [f.to_canonical_dict() for f in sorted_features]
        serialized = json.dumps(canonical_list, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        object.__setattr__(self, "schema_digest", digest)

    def __len__(self) -> int:
        return len(self.features)


@dataclass(frozen=True, slots=True)
class FeaturePipelineSpec:
    """Specification of the feature pipeline including schema and preprocessing steps."""

    schema: FeatureSchema
    normalize: bool = False
    spec_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if len(self.schema) == 0:
            raise ValueError("FeaturePipelineSpec cannot have an empty FeatureSchema")

        canonical_dict = {
            "normalize": self.normalize,
            "schema_digest": self.schema.schema_digest,
        }
        serialized = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        object.__setattr__(self, "spec_digest", digest)


@dataclass(frozen=True, slots=True)
class FittedFeaturePipeline:
    """Stateful feature transformer fitted strictly on training domain samples."""

    spec: FeaturePipelineSpec
    learned_means: Mapping[str, float]
    learned_scales: Mapping[str, float]
    learned_vocabularies: Mapping[str, Mapping[str, int]]
    output_feature_names: tuple[str, ...]
    pipeline_digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "learned_means", freeze_mapping(self.learned_means))
        object.__setattr__(self, "learned_scales", freeze_mapping(self.learned_scales))
        object.__setattr__(self, "learned_vocabularies", freeze_mapping(self.learned_vocabularies))

        canonical_dict = {
            "learned_means": dict(self.learned_means),
            "learned_scales": dict(self.learned_scales),
            "learned_vocabularies": {k: dict(v) for k, v in self.learned_vocabularies.items()},
            "output_feature_names": list(self.output_feature_names),
            "spec_digest": self.spec.spec_digest,
        }
        serialized = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        object.__setattr__(self, "pipeline_digest", digest)

    @classmethod
    def fit(
        cls,
        spec: FeaturePipelineSpec,
        inputs: Sequence[StatisticalSample | PredictionInput],
    ) -> FittedFeaturePipeline:
        """Fit feature pipeline on training inputs ONLY."""
        if not inputs:
            raise ValueError("Cannot fit FeaturePipeline on empty inputs")

        pred_inputs: list[PredictionInput] = []
        for inp in inputs:
            if isinstance(inp, StatisticalSample):
                pred_inputs.append(inp.to_prediction_input())
            elif isinstance(inp, PredictionInput):
                pred_inputs.append(inp)
            else:
                raise TypeError(f"Expected StatisticalSample or PredictionInput, got {type(inp)}")

        learned_means: dict[str, float] = {}
        learned_scales: dict[str, float] = {}
        learned_vocabularies: dict[str, dict[str, int]] = {}
        output_feature_names: list[str] = []

        for f_spec in spec.schema.features:
            if f_spec.feature_type is FeatureType.NUMERIC:
                values: list[float] = []
                for p_inp in pred_inputs:
                    raw_val = p_inp.feature_metadata.get(f_spec.name)
                    if raw_val is None or raw_val == "":
                        if f_spec.missingness_policy is MissingnessPolicy.REJECT:
                            raise ValueError(
                                f"Feature '{f_spec.name}' missing for sample "
                                f"'{p_inp.sample_id}' during fit"
                            )
                        elif f_spec.missingness_policy in (
                            MissingnessPolicy.CONSTANT,
                            MissingnessPolicy.INDICATOR,
                        ):
                            val = float(f_spec.constant_fill_value)  # type: ignore[arg-type]
                            values.append(val)
                    else:
                        try:
                            values.append(float(raw_val))
                        except (ValueError, TypeError) as e:
                            raise ValueError(
                                f"Invalid numeric value '{raw_val}' for feature "
                                f"'{f_spec.name}': {e}"
                            ) from e

                arr = np.array(values, dtype=np.float64)
                mean = float(np.mean(arr))
                std = float(np.std(arr))
                if std < 1e-12:
                    std = 1.0  # Avoid zero division on constant training features

                learned_means[f_spec.name] = mean
                learned_scales[f_spec.name] = std
                output_feature_names.append(f_spec.name)
                if f_spec.missingness_policy is MissingnessPolicy.INDICATOR:
                    output_feature_names.append(f"{f_spec.name}__missing")

            elif f_spec.feature_type is FeatureType.CATEGORICAL:
                categories: set[str] = set()
                for p_inp in pred_inputs:
                    raw_val = p_inp.feature_metadata.get(f_spec.name)
                    if raw_val is None or raw_val == "":
                        if f_spec.missingness_policy is MissingnessPolicy.REJECT:
                            raise ValueError(
                                f"Feature '{f_spec.name}' missing for sample "
                                f"'{p_inp.sample_id}' during fit"
                            )
                        elif f_spec.missingness_policy in (
                            MissingnessPolicy.CONSTANT,
                            MissingnessPolicy.INDICATOR,
                        ):
                            categories.add(str(f_spec.constant_fill_value))
                    else:
                        categories.add(raw_val)

                # Deterministic integer encoding by sorting vocabulary
                sorted_cats = sorted(categories)
                vocab = {cat: idx for idx, cat in enumerate(sorted_cats)}
                learned_vocabularies[f_spec.name] = vocab
                output_feature_names.append(f_spec.name)
                if f_spec.missingness_policy is MissingnessPolicy.INDICATOR:
                    output_feature_names.append(f"{f_spec.name}__missing")

            elif f_spec.feature_type is FeatureType.BOOLEAN:
                output_feature_names.append(f_spec.name)
                if f_spec.missingness_policy is MissingnessPolicy.INDICATOR:
                    output_feature_names.append(f"{f_spec.name}__missing")

        return cls(
            spec=spec,
            learned_means=learned_means,
            learned_scales=learned_scales,
            learned_vocabularies=learned_vocabularies,
            output_feature_names=tuple(output_feature_names),
        )

    def transform(self, inputs: Sequence[PredictionInput]) -> np.ndarray:
        """Transform causal inputs into 2D float64 matrix with shape (n_samples, n_features)."""
        if not inputs:
            return np.empty((0, len(self.output_feature_names)), dtype=np.float64)

        n_samples = len(inputs)
        matrix = np.zeros((n_samples, len(self.output_feature_names)), dtype=np.float64)

        for row_idx, p_inp in enumerate(inputs):
            col_idx = 0
            for f_spec in self.spec.schema.features:
                raw_val = p_inp.feature_metadata.get(f_spec.name)
                is_missing = raw_val is None or raw_val == ""

                if is_missing:
                    if f_spec.missingness_policy is MissingnessPolicy.REJECT:
                        raise ValueError(
                            f"Missing value for feature '{f_spec.name}' in "
                            f"sample '{p_inp.sample_id}'"
                        )
                    elif f_spec.missingness_policy is MissingnessPolicy.CONSTANT:
                        raw_val = str(f_spec.constant_fill_value)
                    elif f_spec.missingness_policy is MissingnessPolicy.INDICATOR:
                        raw_val = str(f_spec.constant_fill_value)

                if f_spec.feature_type is FeatureType.NUMERIC:
                    num_val = float(raw_val)  # type: ignore[arg-type]
                    if self.spec.normalize:
                        mean = self.learned_means[f_spec.name]
                        scale = self.learned_scales[f_spec.name]
                        num_val = (num_val - mean) / scale
                    matrix[row_idx, col_idx] = num_val
                    col_idx += 1

                    if f_spec.missingness_policy is MissingnessPolicy.INDICATOR:
                        matrix[row_idx, col_idx] = 1.0 if is_missing else 0.0
                        col_idx += 1

                elif f_spec.feature_type is FeatureType.CATEGORICAL:
                    vocab = self.learned_vocabularies[f_spec.name]
                    if raw_val not in vocab:
                        if f_spec.unknown_category_policy is UnknownCategoryPolicy.REJECT:
                            raise ValueError(
                                f"Unknown category '{raw_val}' for feature '{f_spec.name}' "
                                f"in sample '{p_inp.sample_id}'"
                            )
                        elif (
                            f_spec.unknown_category_policy
                            is UnknownCategoryPolicy.DECLARED_FALLBACK
                        ):
                            fallback = str(f_spec.fallback_category)
                            if fallback not in vocab:
                                raise ValueError(
                                    f"Declared fallback category '{fallback}' was not "
                                    f"in training vocabulary"
                                )
                            cat_val = float(vocab[fallback])
                    else:
                        cat_val = float(vocab[raw_val])  # type: ignore[index]

                    matrix[row_idx, col_idx] = cat_val
                    col_idx += 1

                    if f_spec.missingness_policy is MissingnessPolicy.INDICATOR:
                        matrix[row_idx, col_idx] = 1.0 if is_missing else 0.0
                        col_idx += 1

                elif f_spec.feature_type is FeatureType.BOOLEAN:
                    if isinstance(raw_val, str):
                        b_val = 1.0 if raw_val.lower() in ("true", "1", "t", "yes") else 0.0
                    else:
                        b_val = 1.0 if bool(raw_val) else 0.0

                    matrix[row_idx, col_idx] = b_val
                    col_idx += 1

                    if f_spec.missingness_policy is MissingnessPolicy.INDICATOR:
                        matrix[row_idx, col_idx] = 1.0 if is_missing else 0.0
                        col_idx += 1

        return matrix
