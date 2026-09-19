"""Targeted branch coverage for safe failure paths in the Sprint 5 ML package."""

# ruff: noqa: I001 -- explicit grouping retained for audit readability.

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

import numpy as np
import pytest
import sklearn

from btg_ai_trader.ml_engine.domain import (
    FeatureType,
    MissingnessPolicy,
    MLCandidateSpec,
    RNGContext,
)
from btg_ai_trader.ml_engine.features import (
    FeaturePipelineSpec,
    FeatureSchema,
    FeatureSpec,
    FittedFeaturePipeline,
)
from btg_ai_trader.ml_engine.models import (
    BasePredictiveCandidate,
    GradientBoostingClassifierCandidate,
    GradientBoostingRegressorCandidate,
    LogisticRegressionCandidate,
    RandomForestClassifierCandidate,
    RandomForestRegressorCandidate,
    RidgeRegressionCandidate,
    _convert_prediction_to_decimal,
    create_candidate,
)
from btg_ai_trader.ml_engine.provenance import (
    EnvironmentFingerprint,
    ModelTrainingInputBoundary,
    ModelTrainingManifest,
)
from btg_ai_trader.ml_engine.registry import ModelRecord, ResearchModelRegistry
from btg_ai_trader.ml_engine.selection import SearchAttemptRecord
from btg_ai_trader.ml_engine.training import ModelTrainer
from btg_ai_trader.statistical_baselines.domain import EvaluationRole, TargetSemantics
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY
from tests.ml_engine_helpers import (
    make_binary_samples,
    make_candidate_spec,
    make_model_card,
    make_pipeline,
)


class _BoomEstimator:
    def fit(self, X: object, y: object) -> None:
        raise RuntimeError("boom")


def test_feature_constant_categorical_boolean_indicator_paths() -> None:
    schema = FeatureSchema(
        (
            FeatureSpec(
                "cat",
                FeatureType.CATEGORICAL,
                MissingnessPolicy.INDICATOR,
                constant_fill_value="OTHER",
            ),
            FeatureSpec(
                "flag",
                FeatureType.BOOLEAN,
                MissingnessPolicy.INDICATOR,
                constant_fill_value=False,
            ),
            FeatureSpec(
                "num",
                FeatureType.NUMERIC,
                MissingnessPolicy.CONSTANT,
                constant_fill_value=2.0,
            ),
        )
    )
    pipeline = FeaturePipelineSpec(schema)
    samples = make_binary_samples()[:2]
    remapped = [
        dataclasses.replace(
            sample,
            feature_metadata={"cat": "", "flag": "", "num": ""},
        )
        for sample in samples
    ]
    fitted = FittedFeaturePipeline.fit(pipeline, remapped)
    matrix = fitted.transform([sample.to_prediction_input() for sample in remapped])
    assert matrix.shape == (2, 5)
    assert np.all(matrix[:, 1] == 1.0)
    assert np.all(matrix[:, 3] == 1.0)


def test_direct_candidate_constructor_family_and_semantics_guards() -> None:
    pipeline = make_pipeline()
    binary = make_candidate_spec(
        "logistic_regression", pipeline, TargetSemantics.BINARY_PROBABILITY
    )
    continuous = make_candidate_spec(
        "ridge_regression", pipeline, TargetSemantics.CONTINUOUS
    )
    wrong_binary_family = MLCandidateSpec(
        family="random_forest_classifier",
        hyperparameters={},
        target_contract=binary.target_contract,
        feature_pipeline_spec_digest=pipeline.spec_digest,
        rng_context=RNGContext(
            "sklearn_random_state", 1, library_version=sklearn.__version__
        ),
        numeric_policy=binary.numeric_policy,
        code_revision=binary.code_revision,
    )
    wrong_cont_family = MLCandidateSpec(
        family="random_forest_regressor",
        hyperparameters={},
        target_contract=continuous.target_contract,
        feature_pipeline_spec_digest=pipeline.spec_digest,
        rng_context=RNGContext(
            "sklearn_random_state", 1, library_version=sklearn.__version__
        ),
        numeric_policy=continuous.numeric_policy,
        code_revision=continuous.code_revision,
    )
    constructors = (
        (LogisticRegressionCandidate, wrong_binary_family),
        (RandomForestClassifierCandidate, binary),
        (GradientBoostingClassifierCandidate, binary),
        (RidgeRegressionCandidate, wrong_cont_family),
        (RandomForestRegressorCandidate, continuous),
        (GradientBoostingRegressorCandidate, continuous),
    )
    for constructor, spec in constructors:
        with pytest.raises(ValueError, match="Spec family"):
            constructor(spec)

    bad_base = MLCandidateSpec(
        family="not-supported",
        hyperparameters={},
        target_contract=binary.target_contract,
        feature_pipeline_spec_digest=pipeline.spec_digest,
        rng_context=None,
        numeric_policy=binary.numeric_policy,
        code_revision=binary.code_revision,
    )
    with pytest.raises(ValueError, match="Unsupported family"):
        BasePredictiveCandidate(bad_base)


@pytest.mark.parametrize(
    ("family", "semantics"),
    [
        ("logistic_regression", TargetSemantics.BINARY_PROBABILITY),
        ("random_forest_classifier", TargetSemantics.BINARY_PROBABILITY),
        ("gradient_boosting_classifier", TargetSemantics.BINARY_PROBABILITY),
        ("ridge_regression", TargetSemantics.CONTINUOUS),
        ("random_forest_regressor", TargetSemantics.CONTINUOUS),
        ("gradient_boosting_regressor", TargetSemantics.CONTINUOUS),
    ],
)
def test_each_fit_wraps_estimator_failure(
    family: str, semantics: TargetSemantics
) -> None:
    pipeline = make_pipeline(two_features=False)
    params: dict[str, object] = (
        {"n_estimators": 2}
        if "forest" in family or "boosting" in family
        else {}
    )
    spec = make_candidate_spec(family, pipeline, semantics, hyperparameters=params)
    candidate = create_candidate(spec)
    cast(Any, candidate)._estimator = _BoomEstimator()
    with pytest.raises(Exception, match="fit failed"):
        candidate.fit(np.ones((2, 1)), np.asarray([0, 1]))


@pytest.mark.parametrize(
    ("family", "semantics"),
    [
        ("random_forest_classifier", TargetSemantics.BINARY_PROBABILITY),
        ("gradient_boosting_classifier", TargetSemantics.BINARY_PROBABILITY),
    ],
)
def test_stochastic_classifiers_reject_single_class(
    family: str, semantics: TargetSemantics
) -> None:
    spec = make_candidate_spec(
        family,
        make_pipeline(two_features=False),
        semantics,
        hyperparameters={"n_estimators": 2},
    )
    with pytest.raises(Exception, match="2 classes"):
        create_candidate(spec).fit(np.ones((2, 1)), np.ones(2, dtype=int))


@pytest.mark.parametrize(
    ("family", "semantics"),
    [
        ("ridge_regression", TargetSemantics.CONTINUOUS),
        ("random_forest_regressor", TargetSemantics.CONTINUOUS),
        ("gradient_boosting_regressor", TargetSemantics.CONTINUOUS),
        ("random_forest_classifier", TargetSemantics.BINARY_PROBABILITY),
        ("gradient_boosting_classifier", TargetSemantics.BINARY_PROBABILITY),
    ],
)
def test_each_family_empty_fit_is_rejected(
    family: str, semantics: TargetSemantics
) -> None:
    spec = make_candidate_spec(
        family,
        make_pipeline(two_features=False),
        semantics,
        hyperparameters={"n_estimators": 2} if "forest" in family or "boosting" in family else {},
    )
    with pytest.raises(Exception, match="empty"):
        create_candidate(spec).fit(np.empty((0, 1)), np.empty((0,)))


def test_nonfinite_prediction_conversion_rejected() -> None:
    with pytest.raises(ValueError, match="Non-finite"):
        _convert_prediction_to_decimal(float("inf"), DEFAULT_NUMERIC_POLICY)


def test_boundary_required_fields_target_mismatch_and_manifest_mismatches() -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression", pipeline, TargetSemantics.BINARY_PROBABILITY
    )
    env = EnvironmentFingerprint.capture()
    samples = make_binary_samples()[:8]
    cutoff = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    boundary = ModelTrainingInputBoundary.create_and_verify(
        samples=samples,
        target_contract=spec.target_contract,
        feature_pipeline_spec_digest=pipeline.spec_digest,
        candidate_spec=spec,
        knowledge_cutoff=cutoff,
        environment=env,
        code_revision=spec.code_revision,
    )

    with pytest.raises(ValueError, match="dataset_digest"):
        ModelTrainingInputBoundary(
            ordered_sample_ids=("x",),
            dataset_digest="",
            source_lineage_digest="x",
            target_contract_digest="x",
            feature_pipeline_spec_digest="x",
            knowledge_cutoff=cutoff,
            candidate_spec_digest="x",
            numeric_policy=DEFAULT_NUMERIC_POLICY,
            environment_fingerprint_digest="x",
            code_revision="x",
        )

    result = ModelTrainer().fit(
        candidate_spec=spec,
        pipeline_spec=pipeline,
        samples=samples,
        knowledge_cutoff=cutoff,
        code_revision=spec.code_revision,
    )
    manifest = result.manifest
    card = make_model_card(result, pipeline)
    assert manifest.is_verified
    with pytest.raises(ValueError, match="verified"):
        ModelRecord.from_manifest(
            dataclasses.replace(manifest),
            model_card=card,
        )

    other_env = dataclasses.replace(env, platform_machine=env.platform_machine + "-other")
    with pytest.raises(ValueError, match="environment"):
        ModelTrainingManifest.create(
            boundary=boundary,
            candidate_spec=spec,
            fitted_feature_pipeline_digest="fit",
            model_state_digest="state",
            environment_fingerprint=other_env,
            code_revision=spec.code_revision,
        )


def test_registry_conflict_branch_is_fail_closed() -> None:
    pipeline = make_pipeline()
    spec = make_candidate_spec(
        "logistic_regression", pipeline, TargetSemantics.BINARY_PROBABILITY
    )
    result = ModelTrainer().fit(
        candidate_spec=spec,
        pipeline_spec=pipeline,
        samples=make_binary_samples()[:8],
        knowledge_cutoff=datetime(2025, 1, 1, 11, 0, tzinfo=UTC),
        code_revision=spec.code_revision,
    )
    first_card = make_model_card(result, pipeline)
    second_card = dataclasses.replace(
        first_card,
        validation_metrics={"fixture_metric": Decimal("1")},
    )
    first = ModelRecord.from_manifest(
        result.manifest, model_card=first_card
    )
    second = ModelRecord.from_manifest(
        result.manifest, model_card=second_card
    )
    object.__setattr__(second, "record_digest", first.record_digest)
    registry = ResearchModelRegistry()
    registry.register(first)
    with pytest.raises(ValueError, match="conflicts"):
        registry.register(second)


def test_search_attempt_success_requires_context_and_freezes_metrics() -> None:
    spec = make_candidate_spec(
        "logistic_regression",
        make_pipeline(),
        TargetSemantics.BINARY_PROBABILITY,
    )
    with pytest.raises(ValueError, match="evaluation_context"):
        SearchAttemptRecord(
            candidate_spec=spec,
            fit_status="SUCCESS",
            evaluation_role=EvaluationRole.VALIDATION_SELECTION,
            evaluation_context_fingerprint="",
            validation_metrics={"x": Decimal("1")},
        )
    record = SearchAttemptRecord(
        candidate_spec=spec,
        fit_status="FAILED",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        evaluation_context_fingerprint="",
    )
    assert record.validation_metrics == {}
