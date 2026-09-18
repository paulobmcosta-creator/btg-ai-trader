"""Tests for deterministic feature schema, pipelines, and train-time fitting."""

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
    StatisticalSample,
    TargetSemantics,
)


def _make_sample(
    sample_id: str,
    feature_meta: dict[str, str],
    target_val: Decimal = Decimal(1),
) -> StatisticalSample:
    t = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    return StatisticalSample(
        sample_id=sample_id,
        feature_knowledge_time=t,
        target_knowledge_time=t,
        target_value=target_val,
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        feature_metadata=feature_meta,
    )


def test_feature_spec_validation() -> None:
    f_num = FeatureSpec(
        name="volatility_20",
        feature_type=FeatureType.NUMERIC,
        missingness_policy=MissingnessPolicy.CONSTANT,
        constant_fill_value=0.0,
    )
    assert f_num.name == "volatility_20"
    assert f_num.feature_type is FeatureType.NUMERIC

    with pytest.raises(ValueError, match="Feature name must be a non-empty string"):
        FeatureSpec(name="", feature_type=FeatureType.NUMERIC)

    with pytest.raises(TypeError, match="feature_type must be FeatureType"):
        FeatureSpec(name="f", feature_type="NUMERIC")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="missingness_policy must be MissingnessPolicy"):
        FeatureSpec(
            name="f",
            feature_type=FeatureType.NUMERIC,
            missingness_policy="CONSTANT",  # type: ignore[arg-type]
        )

    with pytest.raises(TypeError, match="unknown_category_policy must be UnknownCategoryPolicy"):
        FeatureSpec(
            name="f",
            feature_type=FeatureType.CATEGORICAL,
            unknown_category_policy="REJECT",  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="constant_fill_value required when policy is CONSTANT"):
        FeatureSpec(
            name="f",
            feature_type=FeatureType.NUMERIC,
            missingness_policy=MissingnessPolicy.CONSTANT,
            constant_fill_value=None,
        )

    with pytest.raises(ValueError, match="fallback_category required"):
        FeatureSpec(
            name="f",
            feature_type=FeatureType.CATEGORICAL,
            unknown_category_policy=UnknownCategoryPolicy.DECLARED_FALLBACK,
            fallback_category=None,
        )


def test_feature_schema_duplicate_error() -> None:
    f1 = FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)
    f2 = FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)
    with pytest.raises(ValueError, match="Duplicate feature name"):
        FeatureSchema([f1, f2])

    with pytest.raises(ValueError, match="FeatureSchema must contain at least one feature"):
        FeatureSchema(())


def test_feature_pipeline_fit_and_transform_numeric() -> None:
    f1 = FeatureSpec(name="spread", feature_type=FeatureType.NUMERIC)
    f2 = FeatureSpec(name="volume", feature_type=FeatureType.NUMERIC)
    schema = FeatureSchema([f1, f2])
    spec = FeaturePipelineSpec(schema=schema, normalize=True)

    samples = [
        _make_sample("s1", {"spread": "1.0", "volume": "100.0"}),
        _make_sample("s2", {"spread": "2.0", "volume": "200.0"}),
        _make_sample("s3", {"spread": "3.0", "volume": "300.0"}),
    ]

    fitted = FittedFeaturePipeline.fit(spec, samples)
    assert fitted.output_feature_names == ("spread", "volume")
    assert pytest.approx(fitted.learned_means["spread"]) == 2.0
    assert pytest.approx(fitted.learned_means["volume"]) == 200.0

    inputs = [s.to_prediction_input() for s in samples]
    matrix = fitted.transform(inputs)

    assert matrix.shape == (3, 2)
    # Mean of normalized column should be ~0
    assert pytest.approx(np.mean(matrix[:, 0]), abs=1e-7) == 0.0
    assert pytest.approx(np.mean(matrix[:, 1]), abs=1e-7) == 0.0


def test_feature_pipeline_missingness_indicator() -> None:
    f1 = FeatureSpec(
        name="depth",
        feature_type=FeatureType.NUMERIC,
        missingness_policy=MissingnessPolicy.INDICATOR,
        constant_fill_value=0.0,
    )
    schema = FeatureSchema([f1])
    spec = FeaturePipelineSpec(schema=schema, normalize=False)

    samples = [
        _make_sample("s1", {"depth": "10.0"}),
        _make_sample("s2", {"depth": ""}),
        _make_sample("s3", {}),
    ]

    fitted = FittedFeaturePipeline.fit(spec, samples)
    assert fitted.output_feature_names == ("depth", "depth__missing")

    matrix = fitted.transform([s.to_prediction_input() for s in samples])
    assert matrix.shape == (3, 2)
    # Sample 1: present
    assert matrix[0, 0] == 10.0
    assert matrix[0, 1] == 0.0
    # Sample 2: missing
    assert matrix[1, 0] == 0.0
    assert matrix[1, 1] == 1.0
    # Sample 3: missing
    assert matrix[2, 0] == 0.0
    assert matrix[2, 1] == 1.0


def test_feature_pipeline_missingness_reject() -> None:
    f1 = FeatureSpec(
        name="depth",
        feature_type=FeatureType.NUMERIC,
        missingness_policy=MissingnessPolicy.REJECT,
    )
    schema = FeatureSchema([f1])
    spec = FeaturePipelineSpec(schema=schema)

    samples_bad = [_make_sample("s1", {})]
    with pytest.raises(ValueError, match="missing for sample 's1' during fit"):
        FittedFeaturePipeline.fit(spec, samples_bad)


def test_feature_pipeline_categorical_vocab_and_fallback() -> None:
    f_cat = FeatureSpec(
        name="session",
        feature_type=FeatureType.CATEGORICAL,
        unknown_category_policy=UnknownCategoryPolicy.DECLARED_FALLBACK,
        fallback_category="OTHER",
    )
    schema = FeatureSchema([f_cat])
    spec = FeaturePipelineSpec(schema=schema)

    samples_train = [
        _make_sample("s1", {"session": "MORNING"}),
        _make_sample("s2", {"session": "AFTERNOON"}),
        _make_sample("s3", {"session": "OTHER"}),
    ]

    fitted = FittedFeaturePipeline.fit(spec, samples_train)
    vocab = fitted.learned_vocabularies["session"]
    assert "MORNING" in vocab
    assert "AFTERNOON" in vocab
    assert "OTHER" in vocab

    # Test unknown category maps to fallback
    s_unknown = _make_sample("s4", {"session": "EVENING"})
    matrix = fitted.transform([s_unknown.to_prediction_input()])
    assert matrix[0, 0] == float(vocab["OTHER"])


def test_feature_pipeline_categorical_reject_unknown() -> None:
    f_cat = FeatureSpec(
        name="regime",
        feature_type=FeatureType.CATEGORICAL,
        unknown_category_policy=UnknownCategoryPolicy.REJECT,
    )
    schema = FeatureSchema([f_cat])
    spec = FeaturePipelineSpec(schema=schema)

    samples_train = [_make_sample("s1", {"regime": "BULL"})]
    fitted = FittedFeaturePipeline.fit(spec, samples_train)

    s_unknown = _make_sample("s2", {"regime": "BEAR"})
    with pytest.raises(ValueError, match="Unknown category 'BEAR'"):
        fitted.transform([s_unknown.to_prediction_input()])
