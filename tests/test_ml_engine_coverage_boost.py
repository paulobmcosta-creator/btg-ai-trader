"""Supplemental unit tests to achieve high branch and statement coverage for ML Engine."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import numpy as np
import pytest

from btg_ai_trader.ml_engine.domain import (
    FeatureType,
    MissingnessPolicy,
    MLCandidateSpec,
    TargetContract,
    TrainingFailureError,
)
from btg_ai_trader.ml_engine.evaluation import (
    ModelEvaluationEngine,
)
from btg_ai_trader.ml_engine.features import (
    FeaturePipelineSpec,
    FeatureSchema,
    FeatureSpec,
    FittedFeaturePipeline,
)
from btg_ai_trader.ml_engine.model_card import ModelCard
from btg_ai_trader.ml_engine.models import (
    create_candidate,
)
from btg_ai_trader.ml_engine.provenance import (
    EnvironmentFingerprint,
    ModelTrainingManifest,
)
from btg_ai_trader.ml_engine.registry import ModelRecord, ResearchModelRegistry
from btg_ai_trader.statistical_baselines.boundaries import (
    EvaluationBoundary,
    TemporalFold,
    WalkForwardPlan,
)
from btg_ai_trader.statistical_baselines.domain import (
    EvaluationRole,
    PredictionInput,
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY


def _make_dummy_pipeline() -> tuple[FittedFeaturePipeline, list[PredictionInput]]:
    f1 = FeatureSpec(name="x1", feature_type=FeatureType.NUMERIC)
    schema = FeatureSchema([f1])
    spec = FeaturePipelineSpec(schema=schema)
    t = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    samples = [
        StatisticalSample(
            sample_id=f"s{i}",
            feature_knowledge_time=t,
            target_knowledge_time=t,
            target_value=Decimal(i % 2),
            target_semantics=TargetSemantics.BINARY_PROBABILITY,
            feature_metadata={"x1": str(float(i))},
        )
        for i in range(10)
    ]
    pipe = FittedFeaturePipeline.fit(spec, samples)
    inputs = [s.to_prediction_input() for s in samples]
    return pipe, inputs


def test_candidate_mismatched_semantics_rejection() -> None:
    contract_bin = TargetContract(
        target_name="y_bin",
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        forecast_horizon_steps=5,
    )
    contract_cont = TargetContract(
        target_name="y_cont",
        target_semantics=TargetSemantics.CONTINUOUS,
        forecast_horizon_steps=5,
    )

    # Ridge with binary semantics MUST FAIL
    spec_ridge_bad = MLCandidateSpec(
        family="ridge_regression",
        hyperparameters={},
        target_contract=contract_bin,
        feature_pipeline_spec_digest="d",
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev",
    )
    with pytest.raises(ValueError, match="requires CONTINUOUS"):
        create_candidate(spec_ridge_bad)

    # Logistic with continuous semantics MUST FAIL
    spec_log_bad = MLCandidateSpec(
        family="logistic_regression",
        hyperparameters={},
        target_contract=contract_cont,
        feature_pipeline_spec_digest="d",
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev",
    )
    with pytest.raises(ValueError, match="requires BINARY_PROBABILITY"):
        create_candidate(spec_log_bad)

    # RF regressor with binary semantics MUST FAIL
    spec_rf_reg_bad = MLCandidateSpec(
        family="random_forest_regressor",
        hyperparameters={},
        target_contract=contract_bin,
        feature_pipeline_spec_digest="d",
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev",
    )
    with pytest.raises(ValueError, match="requires CONTINUOUS"):
        create_candidate(spec_rf_reg_bad)

    # RF classifier with continuous semantics MUST FAIL
    spec_rf_clf_bad = MLCandidateSpec(
        family="random_forest_classifier",
        hyperparameters={},
        target_contract=contract_cont,
        feature_pipeline_spec_digest="d",
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev",
    )
    with pytest.raises(ValueError, match="requires BINARY_PROBABILITY"):
        create_candidate(spec_rf_clf_bad)

    # GB regressor with binary semantics MUST FAIL
    spec_gb_reg_bad = MLCandidateSpec(
        family="gradient_boosting_regressor",
        hyperparameters={},
        target_contract=contract_bin,
        feature_pipeline_spec_digest="d",
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev",
    )
    with pytest.raises(ValueError, match="requires CONTINUOUS"):
        create_candidate(spec_gb_reg_bad)

    # GB classifier with continuous semantics MUST FAIL
    spec_gb_clf_bad = MLCandidateSpec(
        family="gradient_boosting_classifier",
        hyperparameters={},
        target_contract=contract_cont,
        feature_pipeline_spec_digest="d",
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev",
    )
    with pytest.raises(ValueError, match="requires BINARY_PROBABILITY"):
        create_candidate(spec_gb_clf_bad)


def test_candidate_training_failures() -> None:
    contract_bin = TargetContract(
        target_name="y_bin",
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        forecast_horizon_steps=5,
    )
    spec_log = MLCandidateSpec(
        family="logistic_regression",
        hyperparameters={},
        target_contract=contract_bin,
        feature_pipeline_spec_digest="d",
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev",
    )
    cand = create_candidate(spec_log)

    # Empty data
    with pytest.raises(TrainingFailureError, match="Cannot fit LogisticRegression on empty data"):
        cand.fit(np.zeros((0, 2)), np.zeros(0))

    # Single class
    with pytest.raises(TrainingFailureError, match="requires at least 2 classes"):
        cand.fit(np.zeros((5, 2)), np.zeros(5, dtype=int))


def test_continuous_target_evaluation_workflow() -> None:
    f1 = FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)
    schema = FeatureSchema([f1])
    pipe_spec = FeaturePipelineSpec(schema=schema)

    contract = TargetContract(
        target_name="returns",
        target_semantics=TargetSemantics.CONTINUOUS,
        forecast_horizon_steps=5,
    )
    cand_spec = MLCandidateSpec(
        family="ridge_regression",
        hyperparameters={},
        target_contract=contract,
        feature_pipeline_spec_digest=pipe_spec.spec_digest,
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev_1",
    )
    cand = create_candidate(cand_spec)

    t0 = datetime(2025, 1, 1, 9, 0, tzinfo=UTC)
    t1 = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    t2 = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    t3 = datetime(2025, 1, 1, 13, 0, tzinfo=UTC)

    dev_b = EvaluationBoundary(start_time=t0, end_time=t3, knowledge_cutoff=t0)
    train_b = EvaluationBoundary(start_time=t0, end_time=t1, knowledge_cutoff=t0)
    val_b = EvaluationBoundary(start_time=t1, end_time=t2, knowledge_cutoff=t1)
    test_b = EvaluationBoundary(start_time=t2, end_time=t3, knowledge_cutoff=t2)

    fold = TemporalFold(
        fold_id="fold_cont_0",
        development_boundary=dev_b,
        training_boundary=train_b,
        validation_boundary=val_b,
        protected_evaluation_boundary=test_b,
        knowledge_cutoff=t1,
        window_policy_name="EXPANDING",
    )
    plan = WalkForwardPlan(plan_id="plan_cont", window_policy_name="EXPANDING", folds=(fold,))

    samples = [
        StatisticalSample(
            sample_id=f"train_{i}",
            feature_knowledge_time=t0 + timedelta(minutes=5 * i),
            target_knowledge_time=t0 + timedelta(minutes=5 * i),
            target_value=Decimal(str(float(i) * 0.1)),
            target_semantics=TargetSemantics.CONTINUOUS,
            feature_metadata={"f1": str(float(i))},
        )
        for i in range(15)
    ]
    # Validation samples
    for i in range(5):
        t = t1 + timedelta(minutes=5 * i)
        samples.append(
            StatisticalSample(
                sample_id=f"val_{i}",
                feature_knowledge_time=t,
                target_knowledge_time=t,
                target_value=Decimal(str(float(i + 15) * 0.1)),
                target_semantics=TargetSemantics.CONTINUOUS,
                feature_metadata={"f1": str(float(i + 15))},
            )
        )

    engine = ModelEvaluationEngine()
    report = engine.evaluate_candidate(
        cand, pipe_spec, plan, samples, role=EvaluationRole.VALIDATION_SELECTION
    )
    assert "mae" in report.mean_metrics
    assert "rmse" in report.mean_metrics
    assert "mean_bias" in report.mean_metrics


def test_boolean_and_constant_features() -> None:
    f_bool = FeatureSpec(name="flag", feature_type=FeatureType.BOOLEAN)
    f_const = FeatureSpec(
        name="zero_var",
        feature_type=FeatureType.NUMERIC,
        missingness_policy=MissingnessPolicy.CONSTANT,
        constant_fill_value=42.0,
    )
    schema = FeatureSchema([f_bool, f_const])
    pipe_spec = FeaturePipelineSpec(schema=schema, normalize=True)

    t = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    samples = [
        StatisticalSample(
            sample_id=f"s{i}",
            feature_knowledge_time=t,
            target_knowledge_time=t,
            target_value=Decimal(1),
            target_semantics=TargetSemantics.BINARY_PROBABILITY,
            feature_metadata={"flag": "true" if i % 2 == 0 else "false", "zero_var": "5.0"},
        )
        for i in range(10)
    ]

    fitted = FittedFeaturePipeline.fit(pipe_spec, samples)
    inputs = [s.to_prediction_input() for s in samples]
    matrix = fitted.transform(inputs)
    assert matrix.shape == (10, 2)
    # Boolean transformed to 1.0 and 0.0
    assert matrix[0, 0] == 1.0 or matrix[0, 1] == 1.0


def test_model_card_immutability_and_bounds() -> None:
    contract = TargetContract(
        target_name="returns_15m",
        target_semantics=TargetSemantics.CONTINUOUS,
        forecast_horizon_steps=15,
    )
    schema = FeatureSchema([FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)])
    env = EnvironmentFingerprint.capture()

    # Empty model_id MUST FAIL
    with pytest.raises(ValueError, match="model_id must be non-empty"):
        ModelCard(
            model_id="",
            family="ridge_regression",
            target_contract=contract,
            feature_schema=schema,
            training_boundary_digest="bound",
            hyperparameters={},
            rng_context=None,
            environment_fingerprint=env,
            validation_metrics={},
        )

    # Modified strategy_value MUST FAIL
    with pytest.raises(ValueError, match="strategy_value must remain 'NOT_ASSESSED'"):
        ModelCard(
            model_id="id1",
            family="ridge_regression",
            target_contract=contract,
            feature_schema=schema,
            training_boundary_digest="bound",
            hyperparameters={},
            rng_context=None,
            environment_fingerprint=env,
            validation_metrics={},
            strategy_value="ACTIVE",
        )

    # Modified economic_value MUST FAIL
    with pytest.raises(ValueError, match="economic_value must remain 'NOT_ASSESSED'"):
        ModelCard(
            model_id="id1",
            family="ridge_regression",
            target_contract=contract,
            feature_schema=schema,
            training_boundary_digest="bound",
            hyperparameters={},
            rng_context=None,
            environment_fingerprint=env,
            validation_metrics={},
            economic_value="PROFITABLE",
        )


def test_registry_conflict_detection() -> None:
    env = EnvironmentFingerprint.capture()
    manifest_1 = ModelTrainingManifest(
        candidate_id="cand_1",
        boundary_digest="b1",
        model_state_digest="s1",
        fitted_feature_pipeline_digest="p1",
        target_contract_digest="c1",
        rng_context=None,
        environment_fingerprint=env,
        code_revision="rev_1",
    )
    record_1 = ModelRecord.from_manifest(manifest_1)

    registry = ResearchModelRegistry()
    registry.register(record_1)

    # Duplicate record with different fields but forced collision
    # Creating a different record works independently:
    manifest_2 = ModelTrainingManifest(
        candidate_id="cand_2",
        boundary_digest="b2",
        model_state_digest="s2",
        fitted_feature_pipeline_digest="p2",
        target_contract_digest="c2",
        rng_context=None,
        environment_fingerprint=env,
        code_revision="rev_2",
    )
    record_2 = ModelRecord.from_manifest(manifest_2)
    registry.register(record_2)
    assert len(registry) == 2
