"""Tests for causal deterministic feature pipelines."""

from datetime import UTC, datetime
from decimal import Decimal

import numpy as np
import pytest

from btg_ai_trader.ml_engine.domain import (
    FeatureType,
    MissingnessPolicy,
    UnknownCategoryPolicy,
)
from btg_ai_trader.ml_engine.features import (
    FeaturePipelineSpec,
    FeatureSchema,
    FeatureSpec,
    FittedFeaturePipeline,
)
from btg_ai_trader.statistical_baselines.domain import (
    PredictionInput,
    StatisticalSample,
    TargetSemantics,
)


def _sample(sample_id: str, metadata: dict[str, str]) -> StatisticalSample:
    timestamp = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    return StatisticalSample(
        sample_id=sample_id,
        feature_knowledge_time=timestamp,
        target_knowledge_time=timestamp,
        target_value=Decimal(1),
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        feature_metadata=metadata,
    )


def test_feature_spec_and_schema_validation() -> None:
    FeatureSpec(
        "x",
        FeatureType.NUMERIC,
        MissingnessPolicy.INDICATOR,
        constant_fill_value=0.0,
    )
    with pytest.raises(ValueError, match="Feature name"):
        FeatureSpec("", FeatureType.NUMERIC)
    with pytest.raises(TypeError, match="FeatureType"):
        FeatureSpec("x", "NUMERIC")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="MissingnessPolicy"):
        FeatureSpec("x", FeatureType.NUMERIC, "REJECT")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="UnknownCategoryPolicy"):
        FeatureSpec(
            "x",
            FeatureType.NUMERIC,
            unknown_category_policy="REJECT",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="constant_fill_value"):
        FeatureSpec("x", FeatureType.NUMERIC, MissingnessPolicy.INDICATOR)
    with pytest.raises(ValueError, match="only valid for categorical"):
        FeatureSpec(
            "x",
            FeatureType.NUMERIC,
            unknown_category_policy=UnknownCategoryPolicy.DECLARED_FALLBACK,
            fallback_category="OTHER",
        )
    with pytest.raises(ValueError, match="fallback_category"):
        FeatureSpec(
            "x",
            FeatureType.CATEGORICAL,
            unknown_category_policy=UnknownCategoryPolicy.DECLARED_FALLBACK,
        )
    with pytest.raises(ValueError, match="at least one"):
        FeatureSchema(())
    with pytest.raises(ValueError, match="Duplicate"):
        FeatureSchema(
            (
                FeatureSpec("x", FeatureType.NUMERIC),
                FeatureSpec("x", FeatureType.NUMERIC),
            )
        )


def test_numeric_indicator_normalization_and_empty_transform() -> None:
    spec = FeaturePipelineSpec(
        FeatureSchema(
            (
                FeatureSpec(
                    "x",
                    FeatureType.NUMERIC,
                    MissingnessPolicy.INDICATOR,
                    constant_fill_value=0.0,
                ),
            )
        ),
        normalize=True,
    )
    samples = [_sample("a", {"x": "1"}), _sample("b", {}), _sample("c", {"x": "3"})]
    fitted = FittedFeaturePipeline.fit(spec, samples)
    matrix = fitted.transform([sample.to_prediction_input() for sample in samples])
    assert matrix.shape == (3, 2)
    assert matrix[1, 1] == 1.0
    assert fitted.transform([]).shape == (0, 2)
    assert len(fitted.pipeline_digest) == 64


def test_categorical_fallback_and_reject() -> None:
    fallback_feature = FeatureSpec(
        "session",
        FeatureType.CATEGORICAL,
        unknown_category_policy=UnknownCategoryPolicy.DECLARED_FALLBACK,
        fallback_category="OTHER",
    )
    fitted = FittedFeaturePipeline.fit(
        FeaturePipelineSpec(FeatureSchema((fallback_feature,))),
        [_sample("a", {"session": "OTHER"}), _sample("b", {"session": "MORNING"})],
    )
    unknown = _sample("c", {"session": "EVENING"}).to_prediction_input()
    assert fitted.transform([unknown])[0, 0] == float(
        fitted.learned_vocabularies["session"]["OTHER"]
    )

    reject_feature = FeatureSpec("regime", FeatureType.CATEGORICAL)
    rejecting = FittedFeaturePipeline.fit(
        FeaturePipelineSpec(FeatureSchema((reject_feature,))),
        [_sample("a", {"regime": "BULL"})],
    )
    with pytest.raises(ValueError, match="Unknown category"):
        rejecting.transform([_sample("b", {"regime": "BEAR"}).to_prediction_input()])

    with pytest.raises(ValueError, match="fit-domain vocabulary"):
        FittedFeaturePipeline.fit(
            FeaturePipelineSpec(FeatureSchema((fallback_feature,))),
            [_sample("x", {"session": "MORNING"})],
        )


def test_boolean_literals_and_missing_rejection() -> None:
    feature = FeatureSpec("flag", FeatureType.BOOLEAN)
    fitted = FittedFeaturePipeline.fit(
        FeaturePipelineSpec(FeatureSchema((feature,))),
        [_sample("a", {"flag": "true"}), _sample("b", {"flag": "0"})],
    )
    matrix = fitted.transform(
        [_sample("x", {"flag": "yes"}).to_prediction_input(), _sample("y", {"flag": "no"}).to_prediction_input()]
    )
    assert np.array_equal(matrix[:, 0], np.asarray([1.0, 0.0]))
    with pytest.raises(ValueError, match="Invalid boolean literal"):
        fitted.transform([_sample("z", {"flag": "perhaps"}).to_prediction_input()])

    numeric = FeatureSpec("x", FeatureType.NUMERIC)
    with pytest.raises(ValueError, match="missing"):
        FittedFeaturePipeline.fit(
            FeaturePipelineSpec(FeatureSchema((numeric,))),
            [_sample("m", {})],
        )


def test_nonfinite_invalid_numeric_and_wrong_input() -> None:
    feature = FeatureSpec("x", FeatureType.NUMERIC)
    spec = FeaturePipelineSpec(FeatureSchema((feature,)))
    for value in ("nan", "inf", "-inf", "abc"):
        with pytest.raises(ValueError):
            FittedFeaturePipeline.fit(spec, [_sample(value, {"x": value})])
    with pytest.raises(TypeError, match="Expected StatisticalSample"):
        FittedFeaturePipeline.fit(spec, [object()])  # type: ignore[list-item]

    input_item = PredictionInput(
        sample_id="pred",
        feature_knowledge_time=datetime(2025, 1, 1, 10, 0, tzinfo=UTC),
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        feature_metadata={"x": "4.0"},
    )
    fitted = FittedFeaturePipeline.fit(spec, [input_item])
    assert fitted.transform([input_item])[0, 0] == 4.0
