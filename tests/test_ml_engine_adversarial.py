"""Adversarial test suite for Sprint 5 ML Engine.

Tests:
1. Causal data leakage and lookahead bias rejection.
2. Protected evaluation boundary reuse rejection.
3. Best-seed selection cherry-picking prohibition.
4. 20-run and 100-run bitwise deterministic repeatability across all 6 model families.
5. ModelCard rejection of financial / strategy scope claims.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import numpy as np
import pytest

from btg_ai_trader.ml_engine.domain import (
    EvaluationScope,
    MLCandidateSpec,
    RNGContext,
    TargetContract,
    UnknownCategoryPolicy,
)
from btg_ai_trader.ml_engine.evaluation import (
    ModelEvaluationEngine,
)
from btg_ai_trader.ml_engine.features import (
    FeaturePipelineSpec,
    FeatureSchema,
    FeatureSpec,
    FeatureType,
    FittedFeaturePipeline,
)
from btg_ai_trader.ml_engine.model_card import ModelCard
from btg_ai_trader.ml_engine.models import create_candidate
from btg_ai_trader.ml_engine.provenance import EnvironmentFingerprint
from btg_ai_trader.ml_engine.selection import (
    ModelSearchSpace,
    ModelSelectionPolicy,
)
from btg_ai_trader.ml_engine.training import ModelTrainer
from btg_ai_trader.statistical_baselines.boundaries import (
    EvaluationBoundary,
    TemporalFold,
    WalkForwardPlan,
)
from btg_ai_trader.statistical_baselines.domain import (
    CausalLeakageError,
    EvaluationRole,
    ProtectedEvidenceReuseError,
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY


def _make_dummy_samples(count: int, cutoff: datetime) -> list[StatisticalSample]:
    samples = []
    base_t = cutoff - timedelta(hours=2)
    for i in range(count):
        t = base_t + timedelta(minutes=5 * i)
        samples.append(
            StatisticalSample(
                sample_id=f"s_{i}",
                feature_knowledge_time=t,
                target_knowledge_time=t,
                target_value=Decimal(i % 2),
                target_semantics=TargetSemantics.BINARY_PROBABILITY,
                feature_metadata={"f1": str(float(i)), "f2": str(float(i * 3))},
            )
        )
    return samples


def test_adversarial_causal_data_leakage_rejection() -> None:
    f1 = FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)
    schema = FeatureSchema([f1])
    pipe_spec = FeaturePipelineSpec(schema=schema)
    contract = TargetContract(
        target_name="up",
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        forecast_horizon_steps=5,
    )
    spec = MLCandidateSpec(
        family="logistic_regression",
        hyperparameters={},
        target_contract=contract,
        feature_pipeline_spec_digest=pipe_spec.spec_digest,
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev_1",
    )

    t_cutoff = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    t_leak = t_cutoff + timedelta(seconds=1)

    leaked_sample = StatisticalSample(
        sample_id="leaked_future",
        feature_knowledge_time=t_cutoff,
        target_knowledge_time=t_leak,
        target_value=Decimal(1),
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        feature_metadata={"f1": "1.0"},
    )

    trainer = ModelTrainer()
    with pytest.raises(CausalLeakageError, match="Future label leakage detected"):
        trainer.fit(
            candidate_spec=spec,
            pipeline_spec=pipe_spec,
            samples=[leaked_sample],
            knowledge_cutoff=t_cutoff,
            code_revision="rev_1",
        )


def test_adversarial_protected_test_reuse_rejection() -> None:
    f1 = FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)
    schema = FeatureSchema([f1])
    pipe_spec = FeaturePipelineSpec(schema=schema)
    contract = TargetContract(
        target_name="up",
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        forecast_horizon_steps=5,
    )
    spec = MLCandidateSpec(
        family="logistic_regression",
        hyperparameters={},
        target_contract=contract,
        feature_pipeline_spec_digest=pipe_spec.spec_digest,
        rng_context=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev_1",
    )
    cand = create_candidate(spec)

    t0 = datetime(2025, 1, 1, 9, 0, tzinfo=UTC)
    t1 = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    t2 = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)

    dev_boundary = EvaluationBoundary(start_time=t0, end_time=t2, knowledge_cutoff=t0)
    train_boundary = EvaluationBoundary(start_time=t0, end_time=t1, knowledge_cutoff=t0)
    test_boundary = EvaluationBoundary(start_time=t1, end_time=t2, knowledge_cutoff=t1)

    fold = TemporalFold(
        fold_id="fold_adv_0",
        development_boundary=dev_boundary,
        training_boundary=train_boundary,
        protected_evaluation_boundary=test_boundary,
        knowledge_cutoff=t1,
        window_policy_name="EXPANDING",
    )
    plan = WalkForwardPlan(plan_id="plan_adv", window_policy_name="EXPANDING", folds=(fold,))

    samples = _make_dummy_samples(10, t1)
    # Add test samples
    for i in range(4):
        t = t1 + timedelta(minutes=10 * i)
        samples.append(
            StatisticalSample(
                sample_id=f"test_{i}",
                feature_knowledge_time=t,
                target_knowledge_time=t,
                target_value=Decimal(i % 2),
                target_semantics=TargetSemantics.BINARY_PROBABILITY,
                feature_metadata={"f1": str(float(i))},
            )
        )

    engine = ModelEvaluationEngine()
    # First protected evaluation consumes the boundary
    engine.evaluate_candidate(cand, pipe_spec, plan, samples, role=EvaluationRole.PROTECTED_TEST)

    # Second protected evaluation MUST be rejected
    with pytest.raises(ProtectedEvidenceReuseError):
        engine.evaluate_candidate(
            cand, pipe_spec, plan, samples, role=EvaluationRole.PROTECTED_TEST
        )


def test_adversarial_best_seed_cherry_picking_rejection() -> None:
    contract = TargetContract(
        target_name="up",
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        forecast_horizon_steps=5,
    )
    spec_seed_1 = MLCandidateSpec(
        family="random_forest_classifier",
        hyperparameters={"n_estimators": 10},
        target_contract=contract,
        feature_pipeline_spec_digest="d",
        rng_context=RNGContext(algorithm="numpy_pcg64", seed=1),
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev_1",
    )
    spec_seed_2 = MLCandidateSpec(
        family="random_forest_classifier",
        hyperparameters={"n_estimators": 10},
        target_contract=contract,
        feature_pipeline_spec_digest="d",
        rng_context=RNGContext(algorithm="numpy_pcg64", seed=2),
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="rev_1",
    )

    space = ModelSearchSpace((spec_seed_1, spec_seed_2))
    with pytest.raises(ValueError, match="Seed cherry-picking is strictly prohibited"):
        ModelSelectionPolicy.assert_no_best_seed_selection(space)


def test_adversarial_20_runs_bitwise_repeatability() -> None:
    """Verify that all 6 candidate families produce bitwise repeatable digests across 20 runs."""
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

    X = np.array([[float(i), float(i * 2)] for i in range(20)], dtype=np.float64)
    y_bin = np.array([i % 2 for i in range(20)], dtype=np.int64)
    y_cont = np.array([float(i) * 1.5 for i in range(20)], dtype=np.float64)

    families = [
        ("logistic_regression", contract_bin, y_bin, {}),
        ("ridge_regression", contract_cont, y_cont, {}),
        ("random_forest_classifier", contract_bin, y_bin, {"n_estimators": 5}),
        ("random_forest_regressor", contract_cont, y_cont, {"n_estimators": 5}),
        ("gradient_boosting_classifier", contract_bin, y_bin, {"n_estimators": 5}),
        ("gradient_boosting_regressor", contract_cont, y_cont, {"n_estimators": 5}),
    ]

    for fam, contract, y_arr, extra_params in families:
        spec = MLCandidateSpec(
            family=fam,
            hyperparameters=extra_params,
            target_contract=contract,
            feature_pipeline_spec_digest="pipe_d",
            rng_context=RNGContext(algorithm="numpy_pcg64", seed=123),
            numeric_policy=DEFAULT_NUMERIC_POLICY,
            code_revision="rev_1",
        )

        initial_digest = None
        for run_idx in range(20):
            cand = create_candidate(spec)
            cand.fit(X, y_arr)
            digest = cand.model_state_digest
            if run_idx == 0:
                initial_digest = digest
            else:
                assert digest == initial_digest, (
                    f"Run {run_idx} produced differing digest for {fam}: "
                    f"{digest} != {initial_digest}"
                )


def test_adversarial_100_runs_feature_pipeline_determinism() -> None:
    f1 = FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)
    f2 = FeatureSpec(
        name="cat",
        feature_type=FeatureType.CATEGORICAL,
        unknown_category_policy=UnknownCategoryPolicy.DECLARED_FALLBACK,
        fallback_category="UNK",
    )
    schema = FeatureSchema([f1, f2])
    spec = FeaturePipelineSpec(schema=schema, normalize=True)

    samples = [
        StatisticalSample(
            sample_id=f"s_{i}",
            feature_knowledge_time=datetime(2025, 1, 1, 10, 0, tzinfo=UTC),
            target_knowledge_time=datetime(2025, 1, 1, 10, 0, tzinfo=UTC),
            target_value=Decimal(1),
            target_semantics=TargetSemantics.BINARY_PROBABILITY,
            feature_metadata={"f1": str(float(i * 10)), "cat": "CAT_A" if i % 2 == 0 else "UNK"},
        )
        for i in range(20)
    ]

    initial_digest = None
    inputs = [s.to_prediction_input() for s in samples]

    for run_idx in range(100):
        fitted = FittedFeaturePipeline.fit(spec, samples)
        matrix = fitted.transform(inputs)
        matrix_bytes = matrix.tobytes()

        if run_idx == 0:
            initial_digest = fitted.pipeline_digest
            initial_bytes = matrix_bytes
        else:
            assert fitted.pipeline_digest == initial_digest
            assert matrix_bytes == initial_bytes


def test_adversarial_model_card_strategy_scope_rejection() -> None:
    contract = TargetContract(
        target_name="returns",
        target_semantics=TargetSemantics.CONTINUOUS,
        forecast_horizon_steps=5,
    )
    schema = FeatureSchema([FeatureSpec(name="f1", feature_type=FeatureType.NUMERIC)])
    env = EnvironmentFingerprint.capture()

    with pytest.raises(ValueError, match="evaluation_scope must be EvaluationScope.MODEL"):
        ModelCard(
            model_id="ml:ridge:1",
            family="ridge_regression",
            target_contract=contract,
            feature_schema=schema,
            training_boundary_digest="bound_1",
            hyperparameters={},
            rng_context=None,
            environment_fingerprint=env,
            validation_metrics={"mae": Decimal("0.01")},
            evaluation_scope=EvaluationScope.STRATEGY,
        )
