"""Tests covering Sprint 4 audit remediation enhancements across all modules.

Validates:
- PurgePolicy fail-closed behavior on unknown horizon.
- EmbargoPolicy explicit duration requirements.
- WalkForwardPlan.with_policies immutability and binding.
- Deep immutability of StatisticalSample, CandidateIdentity, PredictionResult, PredictionInput.
- sample.to_prediction_input() omitting target value and target availability time.
- Canonicalization of binary targets to Decimal(0) and Decimal(1).
- StatisticalSample information_interval invariant validation.
- ConstantBaseline output configuration validation against TargetSemantics.
- MajorityClassBaseline restriction to CATEGORICAL targets with predicted_probability=None.
- NumericPolicy context wrapping and compute_continuous_metrics with custom policy.
- FoldAggregationPolicy (EQUAL_FOLD, SAMPLE_WEIGHTED) and FoldStabilityDiagnostics.
- StatisticalEvaluationEngine role enforcement (rejecting DEVELOPMENT and TRAINING_FIT
  on evaluate_candidate_on_plan).
- Comparator parity checking (fingerprint, fold IDs, role, aggregation policy, numeric policy)
  and ParityViolationError.
- EvaluationHistory and ProtectedEvidenceUse preventing protected evidence reuse
  (ProtectedEvidenceReuseError).
- StatisticalEvaluationInputBoundary immutability, dataset hashing without silent sort,
  and plan digest closure.
- Manifest hashing omitting wall-clock from scientific hash while preserving audit metadata.
"""

from __future__ import annotations

import decimal
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast

import pytest

from btg_ai_trader.statistical_baselines.baselines import (
    ConstantBaseline,
    MajorityClassBaseline,
)
from btg_ai_trader.statistical_baselines.boundaries import (
    WalkForwardPlan,
)
from btg_ai_trader.statistical_baselines.comparison import (
    Comparator,
    EvaluationHistory,
    SearchFamily,
)
from btg_ai_trader.statistical_baselines.domain import (
    CandidateIdentity,
    EvaluationRole,
    ParityViolationError,
    PredictionInput,
    ProtectedEvidenceReuseError,
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.evaluation import (
    FoldAggregationPolicy,
    FoldEvaluationResult,
    FoldStabilityDiagnostics,
    StatisticalEvaluationEngine,
)
from btg_ai_trader.statistical_baselines.metrics import (
    DEFAULT_NUMERIC_POLICY,
    NumericPolicy,
    compute_continuous_metrics,
)
from btg_ai_trader.statistical_baselines.provenance import (
    StatisticalEvaluationInputBoundary,
    StatisticalEvaluationManifest,
)
from btg_ai_trader.statistical_baselines.splits import (
    EmbargoPolicy,
    PurgePolicy,
    SplitPlanConfig,
    WalkForwardPlanner,
    WindowPolicy,
)


def _dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 1, 1, hour, minute, tzinfo=UTC)


def _sample(
    idx: int,
    hour: int,
    target: Decimal | int | str = Decimal("100"),
    target_hour: int | None = None,
    info_start_hour: int | None = None,
    info_end_hour: int | None = None,
) -> StatisticalSample:
    feat_time = _dt(hour)
    avail_time = _dt(target_hour if target_hour is not None else hour + 1)
    info_interval = (
        (_dt(info_start_hour), _dt(info_end_hour))
        if info_start_hour is not None and info_end_hour is not None
        else None
    )
    return StatisticalSample(
        sample_id=f"s_{idx}",
        feature_knowledge_time=feat_time,
        target_knowledge_time=avail_time,
        target_semantics=TargetSemantics.CONTINUOUS,
        target_value=Decimal(str(target)),
        information_interval=info_interval,
        source_lineage="test_lineage",
        metadata={"price": str(hour * 10)},
    )


# 1. PurgePolicy fail-closed tests
def test_purge_policy_fail_closed_on_unknown() -> None:
    policy_fail_closed = PurgePolicy(
        purge_overlapping=True,
        default_horizon=None,
        fail_closed_on_unknown=True,
    )
    # Target available at hour 11, eval starts at hour 12
    # target <= eval_start, but information_interval is None and default_horizon is None:
    s_unknown = _sample(1, 10, target_hour=11, info_start_hour=None, info_end_hour=None)
    eval_start = _dt(12)

    # With unknown horizon and fail_closed_on_unknown=True, should return True (purge)
    assert policy_fail_closed.should_purge(s_unknown, eval_start) is True

    policy_allow_unknown = PurgePolicy(
        purge_overlapping=True,
        default_horizon=None,
        fail_closed_on_unknown=False,
    )
    # With unknown horizon and fail_closed_on_unknown=False, should return False (keep)
    assert policy_allow_unknown.should_purge(s_unknown, eval_start) is False

    policy_no_purge = PurgePolicy(
        purge_overlapping=False,
        default_horizon=None,
        fail_closed_on_unknown=True,
    )
    assert policy_no_purge.should_purge(s_unknown, eval_start) is False


def test_purge_policy_default_horizon_fallback() -> None:
    policy = PurgePolicy(
        purge_overlapping=True,
        default_horizon=timedelta(hours=2),
        fail_closed_on_unknown=True,
    )
    # Target at 11, default horizon gives feature_time(10) + 2h = 12h
    s = _sample(1, 10, target_hour=11)
    eval_start_overlap = _dt(11, 30)
    assert policy.should_purge(s, eval_start_overlap) is True

    eval_start_no_overlap = _dt(13)
    assert policy.should_purge(s, eval_start_no_overlap) is False


# 2. EmbargoPolicy explicit duration
def test_embargo_policy_duration() -> None:
    embargo = EmbargoPolicy(duration=timedelta(minutes=15))
    assert embargo.duration == timedelta(minutes=15)

    with pytest.raises(ValueError, match="duration cannot be negative"):
        EmbargoPolicy(duration=timedelta(seconds=-1))


# 3. WalkForwardPlan.with_policies
def test_walk_forward_plan_with_policies() -> None:
    config = SplitPlanConfig(
        window_policy=WindowPolicy.EXPANDING,
        train_duration=timedelta(hours=2),
        test_duration=timedelta(hours=1),
        step_duration=timedelta(hours=1),
        purge_policy=PurgePolicy(purge_overlapping=True, fail_closed_on_unknown=False),
        embargo_policy=EmbargoPolicy(duration=timedelta(minutes=10)),
    )
    plan1 = WalkForwardPlanner.generate_plan(
        start_time=_dt(1),
        end_time=_dt(6),
        config=config,
        plan_id="plan_test",
    )
    purge2 = PurgePolicy(purge_overlapping=False, fail_closed_on_unknown=False)
    embargo2 = EmbargoPolicy(duration=timedelta(minutes=30))

    plan2 = plan1.with_policies(purge_policy=purge2, embargo_policy=embargo2)
    assert plan2.purge_policy == purge2
    assert plan2.embargo_policy == embargo2
    assert plan2.plan_id != plan1.plan_id
    assert plan1.purge_policy == config.purge_policy


# 4. StatisticalSample immutability and PredictionInput
def test_sample_deep_immutability_and_prediction_input() -> None:
    sample = StatisticalSample(
        sample_id="s_imm",
        feature_knowledge_time=_dt(1),
        target_knowledge_time=_dt(2),
        target_semantics=TargetSemantics.CONTINUOUS,
        target_value=Decimal("10"),
        metadata={"a": "1", "b": "2"},
    )

    with pytest.raises((TypeError, AttributeError)):
        sample.metadata["a"] = "99"  # type: ignore[index]

    pred_in = sample.to_prediction_input()
    assert isinstance(pred_in, PredictionInput)
    assert pred_in.sample_id == "s_imm"
    assert pred_in.feature_knowledge_time == _dt(1)
    assert not hasattr(pred_in, "target_value")
    assert not hasattr(pred_in, "target_knowledge_time")

    with pytest.raises((TypeError, AttributeError)):
        pred_in.metadata["a"] = "99"  # type: ignore[index]


def test_binary_target_canonicalization() -> None:
    s0 = StatisticalSample(
        sample_id="s_b0",
        feature_knowledge_time=_dt(1),
        target_knowledge_time=_dt(2),
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        target_value=0,
    )
    assert s0.target_value == Decimal("0")
    assert isinstance(s0.target_value, Decimal)

    s1 = StatisticalSample(
        sample_id="s_b1",
        feature_knowledge_time=_dt(1),
        target_knowledge_time=_dt(2),
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        target_value=1,
    )
    assert s1.target_value == Decimal("1")
    assert isinstance(s1.target_value, Decimal)

    with pytest.raises(ValueError, match=r"target_value.*must be 0 or 1"):
        StatisticalSample(
            sample_id="s_b2",
            feature_knowledge_time=_dt(1),
            target_knowledge_time=_dt(2),
            target_semantics=TargetSemantics.BINARY_PROBABILITY,
            target_value=2,
        )


def test_sample_information_interval_invariants() -> None:
    with pytest.raises(ValueError, match="start.*cannot be after.*end"):
        StatisticalSample(
            sample_id="s_inv1",
            feature_knowledge_time=_dt(1),
            target_knowledge_time=_dt(3),
            target_semantics=TargetSemantics.CONTINUOUS,
            target_value=Decimal("1"),
            information_interval=(_dt(2), _dt(1)),
        )


# 5. ConstantBaseline output configuration validation
def test_constant_baseline_configuration_validation() -> None:
    # BINARY_PROBABILITY with conflicting constant_value
    with pytest.raises(ValueError, match="Conflicting config"):
        ConstantBaseline(
            code_revision="v1.0.0",
            semantics=TargetSemantics.BINARY_PROBABILITY,
            constant_probability=Decimal("0.8"),
            constant_value=Decimal("0.5"),
        )

    # BINARY_PROBABILITY without constant_probability
    with pytest.raises(ValueError, match="constant_probability is required"):
        ConstantBaseline(
            code_revision="v1.0.0",
            semantics=TargetSemantics.BINARY_PROBABILITY,
        )

    # CATEGORICAL requires constant_class
    with pytest.raises(ValueError, match="constant_class is required"):
        ConstantBaseline(
            code_revision="v1.0.0",
            semantics=TargetSemantics.CATEGORICAL,
        )

    # CONTINUOUS requires constant_value
    with pytest.raises(ValueError, match="constant_value is required"):
        ConstantBaseline(
            code_revision="v1.0.0",
            semantics=TargetSemantics.CONTINUOUS,
        )


# 6. MajorityClassBaseline semantics restriction
def test_majority_class_baseline_semantics_restriction() -> None:
    with pytest.raises(ValueError, match="only supports CATEGORICAL"):
        MajorityClassBaseline(
            code_revision="v1.0.0",
            target_semantics=TargetSemantics.CONTINUOUS,
        )

    with pytest.raises(ValueError, match="only supports CATEGORICAL"):
        MajorityClassBaseline(
            code_revision="v1.0.0",
            target_semantics=TargetSemantics.BINARY_PROBABILITY,
        )

    base = MajorityClassBaseline(
        code_revision="v1.0.0",
        target_semantics=TargetSemantics.CATEGORICAL,
    )
    s = StatisticalSample(
        sample_id="s_cat",
        feature_knowledge_time=_dt(1),
        target_knowledge_time=_dt(2),
        target_semantics=TargetSemantics.CATEGORICAL,
        target_value="BUY",
    )
    base.fit([s], knowledge_cutoff=_dt(3))
    pred = base.predict(s.to_prediction_input())
    assert pred.predicted_class == "BUY"
    assert pred.predicted_probability is None


# 7. NumericPolicy and compute_continuous_metrics
def test_numeric_policy_and_continuous_metrics() -> None:
    custom_policy = NumericPolicy(precision=4, rounding_mode=decimal.ROUND_HALF_UP)
    y_true = [Decimal("1.23456"), Decimal("2.34567")]
    y_pred = [Decimal("1.23000"), Decimal("2.34000")]

    metrics = compute_continuous_metrics(y_true, y_pred, policy=custom_policy)
    assert "mae" in metrics
    assert "mse" in metrics
    assert "rmse" in metrics
    assert "mean_bias" in metrics
    assert isinstance(metrics["mae"], Decimal)


# 8. FoldAggregationPolicy and FoldStabilityDiagnostics
def test_fold_stability_diagnostics_and_aggregation_policy() -> None:
    diag = FoldStabilityDiagnostics(
        metric_name="mae",
        min_value=Decimal("0.1"),
        max_value=Decimal("0.3"),
        median_value=Decimal("0.2"),
        dispersion=Decimal("0.05"),
        range_value=Decimal("0.2"),
        worst_fold_id="fold_1",
        best_fold_id="fold_0",
        sign_consistency=True,
        relative_degradation=Decimal("0.15"),
        has_stability_evidence=True,
    )
    assert diag.worst_fold_id == "fold_1"
    assert diag.has_stability_evidence is True
    d = diag.to_canonical_dict()
    assert d["worst_fold_id"] == "fold_1"


# 9. StatisticalEvaluationEngine role enforcement
def test_evaluation_engine_role_enforcement() -> None:
    baseline = ConstantBaseline(
        code_revision="v1.0.0",
        constant_value=Decimal("100"),
        semantics=TargetSemantics.CONTINUOUS,
    )
    s_train = _sample(1, 1, target=100)
    s_eval = _sample(2, 4, target=100)

    config = SplitPlanConfig(
        window_policy=WindowPolicy.EXPANDING,
        train_duration=timedelta(hours=2),
        test_duration=timedelta(hours=1),
        step_duration=timedelta(hours=1),
        purge_policy=PurgePolicy(purge_overlapping=False, fail_closed_on_unknown=False),
        embargo_policy=EmbargoPolicy(duration=timedelta(0)),
    )
    plan = WalkForwardPlanner.generate_plan(
        start_time=_dt(1),
        end_time=_dt(5),
        config=config,
        plan_id="plan_test",
    )

    with pytest.raises(
        ValueError,
        match="evaluate_candidate_on_plan only accepts VALIDATION_SELECTION or PROTECTED_TEST",
    ):
        StatisticalEvaluationEngine.evaluate_candidate_on_plan(
            baseline_factory=lambda: baseline,
            plan=plan,
            samples=[s_train, s_eval],
            role=EvaluationRole.TRAINING_FIT,
        )


# 10. Comparator strict parity checking
def test_comparator_strict_parity_enforcement() -> None:
    fold_res_a = FoldEvaluationResult(
        fold_id="fold_0",
        candidate_id="cand_a",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        sample_count=10,
        cold_start_count=0,
        metrics={"mae": Decimal("1.5")},
        metric_effective_counts={"mae": 10},
    )
    fold_res_b = FoldEvaluationResult(
        fold_id="fold_0",
        candidate_id="cand_b",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        sample_count=10,
        cold_start_count=0,
        metrics={"mae": Decimal("1.2")},
        metric_effective_counts={"mae": 10},
    )

    from btg_ai_trader.statistical_baselines.evaluation import AggregateEvaluationResult

    res_a = AggregateEvaluationResult(
        candidate_id="cand_a",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        fold_results=(fold_res_a,),
        aggregate_metrics={"mae": Decimal("1.5")},
        total_samples=10,
        total_cold_starts=0,
        evaluation_context_fingerprint="fingerprint_1",
    )
    # Different fingerprint
    res_b_mismatched_fp = AggregateEvaluationResult(
        candidate_id="cand_b",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        fold_results=(fold_res_b,),
        aggregate_metrics={"mae": Decimal("1.2")},
        total_samples=10,
        total_cold_starts=0,
        evaluation_context_fingerprint="fingerprint_2",
    )

    with pytest.raises(ParityViolationError, match="Evaluation context parity mismatch"):
        Comparator.compare_candidates([res_a, res_b_mismatched_fp], metric_name="mae")

    # Mismatched roles
    res_b_mismatched_role = AggregateEvaluationResult(
        candidate_id="cand_b",
        evaluation_role=EvaluationRole.PROTECTED_TEST,
        fold_results=(fold_res_b,),
        aggregate_metrics={"mae": Decimal("1.2")},
        total_samples=10,
        total_cold_starts=0,
        evaluation_context_fingerprint="fingerprint_1",
    )
    with pytest.raises(ParityViolationError, match="Mixed evaluation roles"):
        Comparator.compare_candidates([res_a, res_b_mismatched_role], metric_name="mae")


# 11. EvaluationHistory and ProtectedEvidenceReuseError
def test_evaluation_history_protected_evidence_reuse() -> None:
    history = EvaluationHistory()
    cand = CandidateIdentity(
        baseline_type="ConstantBaseline",
        parameters={"constant_value": Decimal("100")},
        target_semantics=TargetSemantics.CONTINUOUS,
        code_revision="v1.0.0",
    )
    cand_adapted = CandidateIdentity(
        baseline_type="ConstantBaseline",
        parameters={"constant_value": Decimal("105")},
        target_semantics=TargetSemantics.CONTINUOUS,
        code_revision="v1.0.0",
    )

    history.record_evaluation(
        candidate_id=cand.candidate_id,
        protected_boundary_id="digest_oos_1",
        role=EvaluationRole.PROTECTED_TEST,
        informed_adaptation=True,
    )

    with pytest.raises(ProtectedEvidenceReuseError, match="Protected evidence reuse violation"):
        history.check_admissibility(
            candidate_id=cand_adapted.candidate_id,
            protected_boundary_id="digest_oos_1",
            role=EvaluationRole.PROTECTED_TEST,
            parent_candidate_ids=(cand.candidate_id,),
        )


# 12. Dataset hashing and plan digest closure
def test_dataset_hashing_order_sensitivity() -> None:
    s1 = _sample(1, 1)
    s2 = _sample(2, 2)

    digest1 = StatisticalEvaluationInputBoundary.compute_dataset_digest([s1, s2])
    digest2 = StatisticalEvaluationInputBoundary.compute_dataset_digest([s1, s2])
    assert digest1 == digest2

    with pytest.raises(ValueError, match="out of chronological order"):
        StatisticalEvaluationInputBoundary.validate_dataset([s2, s1])


def test_plan_digest_policy_sensitivity() -> None:
    config1 = SplitPlanConfig(
        window_policy=WindowPolicy.EXPANDING,
        train_duration=timedelta(hours=2),
        test_duration=timedelta(hours=1),
        step_duration=timedelta(hours=1),
        purge_policy=PurgePolicy(purge_overlapping=True, default_horizon=timedelta(hours=1), fail_closed_on_unknown=False),
        embargo_policy=EmbargoPolicy(duration=timedelta(minutes=10)),
    )
    plan_p1 = WalkForwardPlanner.generate_plan(
        start_time=_dt(1),
        end_time=_dt(6),
        config=config1,
        plan_id="plan_test",
    )
    plan_p2 = plan_p1.with_policies(
        purge_policy=PurgePolicy(purge_overlapping=False, fail_closed_on_unknown=False),
        embargo_policy=EmbargoPolicy(duration=timedelta(minutes=20)),
    )

    digest_p1 = StatisticalEvaluationManifest.compute_plan_digest(plan_p1)
    digest_p2 = StatisticalEvaluationManifest.compute_plan_digest(plan_p2)
    assert digest_p1 != digest_p2


# 13. Manifest deterministic payload hash excludes wall-clock
def test_manifest_scientific_hash_excludes_wall_clock() -> None:
    cand = CandidateIdentity(
        baseline_type="ConstantBaseline",
        parameters={"constant_value": Decimal("100")},
        target_semantics=TargetSemantics.CONTINUOUS,
        code_revision="v1.0.0",
    )
    config = SplitPlanConfig(
        window_policy=WindowPolicy.EXPANDING,
        train_duration=timedelta(hours=2),
        test_duration=timedelta(hours=1),
        step_duration=timedelta(hours=1),
        purge_policy=PurgePolicy(purge_overlapping=False, fail_closed_on_unknown=False),
        embargo_policy=EmbargoPolicy(duration=timedelta(0)),
    )
    plan = WalkForwardPlanner.generate_plan(
        start_time=_dt(1),
        end_time=_dt(5),
        config=config,
        plan_id="plan_test",
    )
    s1 = _sample(1, 1, target=100)
    from btg_ai_trader.statistical_baselines.evaluation import AggregateEvaluationResult

    agg = AggregateEvaluationResult(
        candidate_id=cand.candidate_id,
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        fold_results=(),
        aggregate_metrics={"mae": Decimal("1.0")},
        total_samples=100,
        total_cold_starts=0,
    )

    m1 = StatisticalEvaluationManifest.create(
        plan=plan,
        samples=[s1],
        candidate_identities=[cand],
        aggregate_results=[agg],
        comparison_results=[],
        code_revision="v1.0.0",
        execution_timestamp=_dt(10),
    )
    m2 = StatisticalEvaluationManifest.create(
        plan=plan,
        samples=[s1],
        candidate_identities=[cand],
        aggregate_results=[agg],
        comparison_results=[],
        code_revision="v1.0.0",
        execution_timestamp=_dt(20),
    )

    assert m1.manifest_digest == m2.manifest_digest
    assert m1.observed_execution_timestamp != m2.observed_execution_timestamp


def test_numeric_policy_validation() -> None:
    with pytest.raises(ValueError, match="precision must be positive"):
        NumericPolicy(precision=0)
    with pytest.raises(ValueError, match="Invalid rounding_mode"):
        NumericPolicy(rounding_mode="INVALID")


def test_evaluation_provenance_record_validation() -> None:
    from btg_ai_trader.statistical_baselines.provenance import EvaluationProvenanceRecord

    with pytest.raises(
        ValueError,
        match="observed_execution_timestamp or execution_timestamp must be provided",
    ):
        EvaluationProvenanceRecord(
            plan_id="p1",
            plan_digest="pd",
            dataset_digest="dd",
            candidate_identities=(),
            code_revision="v1",
            manifest_digest="md",
            observed_execution_timestamp=None,
            execution_timestamp=None,
        )


def test_domain_prediction_input_and_sample_validation() -> None:
    with pytest.raises(ValueError, match="sample_id must be a non-empty string"):
        PredictionInput(
            sample_id="",
            feature_knowledge_time=_dt(1),
            target_semantics=TargetSemantics.CONTINUOUS,
        )
    valid_pi = PredictionInput(
        sample_id="p_valid",
        feature_knowledge_time=_dt(1),
        target_semantics=TargetSemantics.CONTINUOUS,
        feature_metadata={"known_feature": "1"},
    )
    assert valid_pi.metadata["known_feature"] == "1"

    shielded_sample = StatisticalSample(
        sample_id="p_shielded",
        feature_knowledge_time=_dt(1),
        target_knowledge_time=_dt(2),
        target_semantics=TargetSemantics.CONTINUOUS,
        target_value=Decimal("1"),
        feature_metadata={"known_feature": "1"},
        audit_metadata={"future_label": "999", "target_debug": "999"},
        source_lineage="audit-only-source",
    )
    shielded_input = shielded_sample.to_prediction_input()
    assert shielded_input.feature_metadata["known_feature"] == "1"
    assert not hasattr(shielded_input, "audit_metadata")
    assert not hasattr(shielded_input, "source_lineage")
    assert not hasattr(shielded_input, "information_interval")
    assert not hasattr(shielded_input, "reference_value")

    with pytest.raises(
        TypeError,
        match="target_value for BINARY_PROBABILITY must be int or Decimal, got bool",
    ):
        StatisticalSample(
            sample_id="s_bool",
            feature_knowledge_time=_dt(1),
            target_semantics=TargetSemantics.BINARY_PROBABILITY,
            target_value=True,
            target_knowledge_time=_dt(2),
        )


def test_baselines_configuration_validation() -> None:
    with pytest.raises(
        ValueError, match="code_revision must be a non-empty string explicitly provided"
    ):
        ConstantBaseline(constant_value=Decimal("1"), code_revision="")

    with pytest.raises(TypeError, match="constant_value must be Decimal"):
        ConstantBaseline(
            constant_value=cast(Any, "100"),
            semantics=TargetSemantics.CONTINUOUS,
            code_revision="v1.0.0",
        )

    with pytest.raises(
        ValueError,
        match=(
            "Conflicting config: constant_probability and constant_class "
            "must be None for CONTINUOUS"
        ),
    ):
        ConstantBaseline(
            constant_value=Decimal("100"),
            constant_class="UP",
            semantics=TargetSemantics.CONTINUOUS,
            code_revision="v1.0.0",
        )

    with pytest.raises(TypeError, match="constant_probability must be Decimal"):
        ConstantBaseline(
            constant_probability=cast(Any, "0.5"),
            semantics=TargetSemantics.BINARY_PROBABILITY,
            code_revision="v1.0.0",
        )

    with pytest.raises(
        ValueError, match=r"constant_probability must be in \[0, 1\]"
    ):
        ConstantBaseline(
            constant_probability=Decimal("1.5"),
            semantics=TargetSemantics.BINARY_PROBABILITY,
            code_revision="v1.0.0",
        )

    with pytest.raises(
        ValueError,
        match=(
            "Conflicting config: constant_value and constant_class "
            "must be None for BINARY_PROBABILITY"
        ),
    ):
        ConstantBaseline(
            constant_probability=Decimal("0.5"),
            constant_class="UP",
            semantics=TargetSemantics.BINARY_PROBABILITY,
            code_revision="v1.0.0",
        )

    # Valid binary baseline with probability
    bin_base = ConstantBaseline(
        constant_probability=Decimal("0.5"),
        semantics=TargetSemantics.BINARY_PROBABILITY,
        code_revision="v1.0.0",
    )
    assert bin_base.identity.parameters["constant_probability"] == "0.5"

    with pytest.raises(TypeError, match="constant_class must be str"):
        ConstantBaseline(
            constant_class=cast(Any, 123),
            semantics=TargetSemantics.CATEGORICAL,
            code_revision="v1.0.0",
        )

    with pytest.raises(
        ValueError, match="Conflicting config: constant_value must be None for CATEGORICAL"
    ):
        ConstantBaseline(
            constant_class="UP",
            constant_value=Decimal("1"),
            semantics=TargetSemantics.CATEGORICAL,
            code_revision="v1.0.0",
        )

    with pytest.raises(TypeError, match="constant_probability must be Decimal"):
        ConstantBaseline(
            constant_class="UP",
            constant_probability="invalid",  # type: ignore[arg-type]
            semantics=TargetSemantics.CATEGORICAL,
            code_revision="v1.0.0",
        )

    with pytest.raises(
        ValueError, match=r"constant_probability must be in \[0, 1\]"
    ):
        ConstantBaseline(
            constant_class="UP",
            constant_probability=Decimal("1.5"),
            semantics=TargetSemantics.CATEGORICAL,
            code_revision="v1.0.0",
        )

    with pytest.raises(ValueError, match="Unsupported target semantics"):
        ConstantBaseline(
            constant_value=Decimal("1"),
            semantics="UNSUPPORTED",  # type: ignore[arg-type]
            code_revision="v1.0.0",
        )

    # Valid categorical with probability parameter
    cat_prob = ConstantBaseline(
        constant_class="UP",
        constant_probability=Decimal("0.8"),
        semantics=TargetSemantics.CATEGORICAL,
        code_revision="v1.0.0",
    )
    assert cat_prob.identity.parameters["constant_probability"] == "0.8"

    # Valid categorical without probability parameter
    cat_no_prob = ConstantBaseline(
        constant_class="DOWN",
        semantics=TargetSemantics.CATEGORICAL,
        code_revision="v1.0.0",
    )
    assert cat_no_prob.identity.parameters["constant_class"] == "DOWN"


def test_comparison_search_family_and_evaluation_history() -> None:
    cand = CandidateIdentity("const", {"val": "1"}, TargetSemantics.CONTINUOUS, "v1")
    fam = SearchFamily(
        family_name="fam1",
        target_semantics=TargetSemantics.CONTINUOUS,
        candidates=(cand,),
        candidate_ids_considered=("c1",),
        configurations_considered=({"p": "1"},),
        baseline_ids=("const",),
    )
    d = fam.to_canonical_dict()
    assert d["family_name"] == "fam1"
    assert d["candidate_ids_considered"] == ["c1"]
    assert d["baseline_ids"] == ["const"]

    history = EvaluationHistory()
    assert history.records == ()
    # Non-protected role returns early
    history.check_admissibility(
        candidate_id="c1",
        protected_boundary_id="b1",
        role=EvaluationRole.VALIDATION_SELECTION,
    )

    history.record_evaluation(
        candidate_id="c1",
        protected_boundary_id="b1",
        role=EvaluationRole.PROTECTED_TEST,
        informed_adaptation=True,
    )

    with pytest.raises(
        ProtectedEvidenceReuseError, match="candidate c1 was already evaluated"
    ):
        history.check_admissibility("c1", "b1", EvaluationRole.PROTECTED_TEST)

    with pytest.raises(ProtectedEvidenceReuseError, match="adapted from parent c1"):
        history.check_admissibility(
            "c2",
            "b1",
            EvaluationRole.PROTECTED_TEST,
            parent_candidate_ids=("c1",),
        )

    # Parent candidate not in parent_candidate_ids: should pass check
    history.check_admissibility(
        "c2",
        "b1",
        EvaluationRole.PROTECTED_TEST,
        parent_candidate_ids=("unrelated_parent",),
    )

    # Other boundary should pass without error
    history.check_admissibility("c1", "b2", EvaluationRole.PROTECTED_TEST)


def test_comparison_parity_violations() -> None:
    from btg_ai_trader.statistical_baselines.evaluation import AggregateEvaluationResult

    res1 = AggregateEvaluationResult(
        candidate_id="c1",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        fold_results=(),
        aggregate_metrics={"mae": Decimal("1")},
        total_samples=10,
        total_cold_starts=0,
        aggregation_policy=FoldAggregationPolicy.EQUAL_FOLD,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
    )
    res2 = AggregateEvaluationResult(
        candidate_id="c2",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        fold_results=(),
        aggregate_metrics={"mae": Decimal("2")},
        total_samples=10,
        total_cold_starts=0,
        aggregation_policy=FoldAggregationPolicy.SAMPLE_WEIGHTED,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
    )
    with pytest.raises(ParityViolationError, match="aggregation policies differ"):
        Comparator.compare_candidates([res1, res2], "mae")

    custom_np = NumericPolicy(precision=34)
    res3 = AggregateEvaluationResult(
        candidate_id="c3",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        fold_results=(),
        aggregate_metrics={"mae": Decimal("2")},
        total_samples=10,
        total_cold_starts=0,
        aggregation_policy=FoldAggregationPolicy.EQUAL_FOLD,
        numeric_policy=custom_np,
    )
    with pytest.raises(ParityViolationError, match="numeric policies differ"):
        Comparator.compare_candidates([res1, res3], "mae")


def test_evaluation_policy_overrides_and_sample_weighted_and_stability() -> None:

    base_plan = WalkForwardPlanner.generate_plan(
        start_time=_dt(0),
        end_time=_dt(15),
        config=SplitPlanConfig(
            window_policy=WindowPolicy.EXPANDING,
            train_duration=timedelta(hours=3),
            test_duration=timedelta(hours=2),
            step_duration=timedelta(hours=2),
            validation_duration=timedelta(hours=2),
            purge_policy=PurgePolicy(purge_overlapping=True, fail_closed_on_unknown=False),
            embargo_policy=EmbargoPolicy(duration=timedelta(0)),
        ),
        plan_id="plan_base",
    )
    val_b = base_plan.folds[0].validation_boundary
    assert val_b is not None

    plan_with_nones = WalkForwardPlan(
        plan_id="plan_none",
        window_policy_name="EXPANDING",
        folds=base_plan.folds,
        purge_policy=None,
        embargo_policy=None,
    )
    samples = [
        _sample(1, 1, target=100),
        _sample(2, 2, target=100),
        _sample(3, 4, target=100),
        _sample(4, 6, target=100),
    ]

    # Plan without purge_policy fails closed
    with pytest.raises(ValueError, match="purge_policy"):
        StatisticalEvaluationEngine.evaluate_candidate_on_plan(
            baseline_factory=lambda: ConstantBaseline(
                constant_value=Decimal("100"), code_revision="v1.0.0"
            ),
            plan=plan_with_nones,
            samples=samples,
            role=EvaluationRole.VALIDATION_SELECTION,
            code_revision="v1.0.0",
        )

    # Plan without embargo_policy fails closed
    plan_no_embargo = WalkForwardPlan(
        plan_id="plan_no_emb",
        window_policy_name="EXPANDING",
        folds=base_plan.folds,
        purge_policy=PurgePolicy(purge_overlapping=True, fail_closed_on_unknown=False),
        embargo_policy=None,
    )
    with pytest.raises(ValueError, match="embargo_policy"):
        StatisticalEvaluationEngine.evaluate_candidate_on_plan(
            baseline_factory=lambda: ConstantBaseline(
                constant_value=Decimal("100"), code_revision="v1.0.0"
            ),
            plan=plan_no_embargo,
            samples=samples,
            role=EvaluationRole.VALIDATION_SELECTION,
            code_revision="v1.0.0",
        )

    # SAMPLE_WEIGHTED aggregation policy and zero best_val rel_deg
    agg_sw = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
        baseline_factory=lambda: ConstantBaseline(
            constant_value=Decimal("100"), code_revision="v1.0.0"
        ),
        plan=base_plan,
        samples=samples,
        role=EvaluationRole.VALIDATION_SELECTION,
        aggregation_policy=FoldAggregationPolicy.SAMPLE_WEIGHTED,
        code_revision="v1.0.0",
    )
    assert agg_sw.aggregation_policy is FoldAggregationPolicy.SAMPLE_WEIGHTED
    assert "weighted_mean_mae" in agg_sw.aggregate_metrics
    assert agg_sw.stability_diagnostics["mae"].min_value == Decimal("0")

    # Accuracy higher_is_better diagnostics
    cat_samples = [
        StatisticalSample(
            sample_id=f"s_cat_{i}",
            feature_knowledge_time=_dt(i),
            target_semantics=TargetSemantics.CATEGORICAL,
            target_value="UP" if i % 2 == 0 else "DOWN",
            target_knowledge_time=_dt(i + 1),
        )
        for i in range(1, 14)
    ]
    agg_cat = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
        baseline_factory=lambda: MajorityClassBaseline(code_revision="v1.0.0"),
        plan=base_plan,
        samples=cat_samples,
        role=EvaluationRole.VALIDATION_SELECTION,
        code_revision="v1.0.0",
    )
    assert "mean_accuracy" in agg_cat.aggregate_metrics
    acc_diag = agg_cat.stability_diagnostics["accuracy"]
    assert acc_diag.best_fold_id != ""
    assert acc_diag.worst_fold_id != ""


def test_split_plan_config_mandatory_policies_rejection() -> None:
    """SplitPlanConfig requires both purge_policy and embargo_policy explicitly."""
    with pytest.raises(ValueError, match="purge_policy is required"):
        SplitPlanConfig(
            window_policy=WindowPolicy.EXPANDING,
            train_duration=timedelta(hours=3),
            test_duration=timedelta(hours=1),
            step_duration=timedelta(hours=1),
            purge_policy=None,  # type: ignore[arg-type]
            embargo_policy=EmbargoPolicy(duration=timedelta(0)),
        )

    with pytest.raises(ValueError, match="embargo_policy is required"):
        SplitPlanConfig(
            window_policy=WindowPolicy.EXPANDING,
            train_duration=timedelta(hours=3),
            test_duration=timedelta(hours=1),
            step_duration=timedelta(hours=1),
            purge_policy=PurgePolicy(purge_overlapping=True, fail_closed_on_unknown=False),
            embargo_policy=None,  # type: ignore[arg-type]
        )


def test_partition_samples_purge_overlapping_branch() -> None:
    """Samples whose information interval overlaps with eval_start are purged from training."""
    plan = WalkForwardPlanner.generate_plan(
        start_time=_dt(0),
        end_time=_dt(10),
        config=SplitPlanConfig(
            window_policy=WindowPolicy.EXPANDING,
            train_duration=timedelta(hours=4),
            test_duration=timedelta(hours=2),
            step_duration=timedelta(hours=2),
            purge_policy=PurgePolicy(purge_overlapping=True, default_horizon=timedelta(hours=2), fail_closed_on_unknown=False),
            embargo_policy=EmbargoPolicy(duration=timedelta(0)),
        ),
        plan_id="plan_purge_test",
    )
    fold = plan.folds[0]
    overlapping_sample = StatisticalSample(
        sample_id="s_overlap",
        feature_knowledge_time=_dt(3),
        target_semantics=TargetSemantics.CONTINUOUS,
        target_value=Decimal("100"),
        target_knowledge_time=_dt(4),
    )
    normal_sample = StatisticalSample(
        sample_id="s_normal",
        feature_knowledge_time=_dt(1),
        target_semantics=TargetSemantics.CONTINUOUS,
        target_value=Decimal("100"),
        target_knowledge_time=_dt(2),
    )
    train, _val, _ev = WalkForwardPlanner.partition_samples(
        [normal_sample, overlapping_sample],
        fold,
        plan.purge_policy,
        plan.embargo_policy,
    )
    assert normal_sample in train
    assert overlapping_sample not in train


def test_calibration_report_to_canonical_dict() -> None:
    """CalibrationReport.to_canonical_dict produces exact expected structure."""
    from btg_ai_trader.statistical_baselines.calibration import CalibrationBin, CalibrationReport

    bin1 = CalibrationBin(
        bin_index=0,
        bin_lower=Decimal("0.0"),
        bin_upper=Decimal("0.5"),
        sample_count=2,
        mean_predicted_probability=Decimal("0.25"),
        observed_frequency=Decimal("0.5"),
    )
    bin2 = CalibrationBin(
        bin_index=1,
        bin_lower=Decimal("0.5"),
        bin_upper=Decimal("1.0"),
        sample_count=0,
        mean_predicted_probability=None,
        observed_frequency=None,
    )
    report = CalibrationReport(
        bins=(bin1, bin2),
        num_bins=2,
        expected_calibration_error=Decimal("0.1"),
        maximum_calibration_error=Decimal("0.2"),
    )
    canonical = report.to_canonical_dict()
    assert canonical["num_bins"] == 2
    assert canonical["expected_calibration_error"] == "0.1"
    assert canonical["maximum_calibration_error"] == "0.2"
    assert canonical["bins"][0]["mean_predicted_probability"] == "0.25"
    assert canonical["bins"][0]["observed_frequency"] == "0.5"
    assert canonical["bins"][1]["mean_predicted_probability"] is None
    assert canonical["bins"][1]["observed_frequency"] is None


def test_domain_information_interval_leakage_causal_error() -> None:
    """information_interval end later than target_knowledge_time raises CausalLeakageError."""
    from btg_ai_trader.statistical_baselines.domain import CausalLeakageError

    with pytest.raises(CausalLeakageError, match="information_interval end"):
        StatisticalSample(
            sample_id="s_leak",
            feature_knowledge_time=_dt(1),
            target_semantics=TargetSemantics.CONTINUOUS,
            target_value=Decimal("100"),
            target_knowledge_time=_dt(2),
            information_interval=(_dt(1), _dt(3)),
        )


def test_evaluation_protected_test_history_integration() -> None:
    """Protected evaluation requires history and blocks reuse after later evidence consumption."""
    plan = WalkForwardPlanner.generate_plan(
        start_time=_dt(0),
        end_time=_dt(10),
        config=SplitPlanConfig(
            window_policy=WindowPolicy.EXPANDING,
            train_duration=timedelta(hours=3),
            test_duration=timedelta(hours=2),
            step_duration=timedelta(hours=2),
            purge_policy=PurgePolicy(purge_overlapping=True, fail_closed_on_unknown=False),
            embargo_policy=EmbargoPolicy(duration=timedelta(0)),
        ),
        plan_id="plan_prot",
    )
    samples = [
        _sample(1, 1, target=100),
        _sample(2, 2, target=100),
        _sample(3, 4, target=100),
        _sample(4, 6, target=100),
    ]

    with pytest.raises(ValueError, match="requires EvaluationHistory"):
        StatisticalEvaluationEngine.evaluate_candidate_on_plan(
            baseline_factory=lambda: ConstantBaseline(
                constant_value=Decimal("100"), code_revision="v1.0.0"
            ),
            plan=plan,
            samples=samples,
            role=EvaluationRole.PROTECTED_TEST,
            code_revision="v1.0.0",
        )

    history = EvaluationHistory()
    res1 = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
        baseline_factory=lambda: ConstantBaseline(
            constant_value=Decimal("100"), code_revision="v1.0.0"
        ),
        plan=plan,
        samples=samples,
        role=EvaluationRole.PROTECTED_TEST,
        evaluation_history=history,
        code_revision="v1.0.0",
    )
    assert res1.evaluation_role is EvaluationRole.PROTECTED_TEST
    assert len(res1.protected_evidence_records) == 1
    cand1_id = res1.candidate_id

    adapted = ConstantBaseline(constant_value=Decimal("105"), code_revision="v1.0.0")
    history.record_protected_evidence_consumption(
        protected_boundary_id="plan_prot:protected",
        source_candidate_id=cand1_id,
        derived_candidate_id=adapted.identity.candidate_id,
    )

    with pytest.raises(ProtectedEvidenceReuseError, match="derived using evidence"):
        StatisticalEvaluationEngine.evaluate_candidate_on_plan(
            baseline_factory=lambda: ConstantBaseline(
                constant_value=Decimal("105"), code_revision="v1.0.0"
            ),
            plan=plan,
            samples=samples,
            role=EvaluationRole.PROTECTED_TEST,
            evaluation_history=history,
            code_revision="v1.0.0",
            parent_candidate_ids=(cand1_id,),
        )

    res_q = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
        baseline_factory=lambda: ConstantBaseline(
            constant_value=Decimal("105"), code_revision="v1.0.0"
        ),
        plan=plan,
        samples=samples,
        role=EvaluationRole.PROTECTED_TEST,
        evaluation_history=history,
        protected_boundary_id="independent_q",
        code_revision="v1.0.0",
        parent_candidate_ids=(cand1_id,),
    )
    assert res_q.evaluation_role is EvaluationRole.PROTECTED_TEST


def test_provenance_input_boundary_fake_digest_rejected() -> None:
    """StatisticalEvaluationInputBoundary rejects fake or tampered logical_evaluation_digest."""
    import dataclasses

    samples = [_sample(1, 1, target=100), _sample(2, 2, target=100)]
    plan = WalkForwardPlanner.generate_plan(
        start_time=_dt(0),
        end_time=_dt(10),
        config=SplitPlanConfig(
            window_policy=WindowPolicy.EXPANDING,
            train_duration=timedelta(hours=3),
            test_duration=timedelta(hours=2),
            step_duration=timedelta(hours=2),
            purge_policy=PurgePolicy(purge_overlapping=True, fail_closed_on_unknown=False),
            embargo_policy=EmbargoPolicy(duration=timedelta(0)),
        ),
        plan_id="plan_fake",
    )
    cand_id = CandidateIdentity(
        baseline_type="model",
        parameters={},
        target_semantics=TargetSemantics.CONTINUOUS,
        code_revision="v1.0.0",
    )
    bnd = StatisticalEvaluationInputBoundary.create(
        samples=samples,
        plan=plan,
        candidate_identities=(cand_id,),
        code_revision="v1.0.0",
        target_contract_id="contract_1",
    )
    with pytest.raises(ValueError, match="logical_evaluation_digest mismatch"):
        dataclasses.replace(bnd, logical_evaluation_digest="tampered_fake_digest_value")


def test_provenance_create_input_boundary_missing_plan_policies() -> None:
    """StatisticalEvaluationInputBoundary.create and compute_plan_digest require bound policies."""
    base_plan = WalkForwardPlanner.generate_plan(
        start_time=_dt(0),
        end_time=_dt(10),
        config=SplitPlanConfig(
            window_policy=WindowPolicy.EXPANDING,
            train_duration=timedelta(hours=3),
            test_duration=timedelta(hours=2),
            step_duration=timedelta(hours=2),
            purge_policy=PurgePolicy(purge_overlapping=True, fail_closed_on_unknown=False),
            embargo_policy=EmbargoPolicy(duration=timedelta(0)),
        ),
        plan_id="plan_no_pol",
    )
    plan_no_purge = WalkForwardPlan(
        plan_id="no_purge",
        window_policy_name="EXPANDING",
        folds=base_plan.folds,
        purge_policy=None,
        embargo_policy=base_plan.embargo_policy,
    )
    plan_no_embargo = WalkForwardPlan(
        plan_id="no_embargo",
        window_policy_name="EXPANDING",
        folds=base_plan.folds,
        purge_policy=base_plan.purge_policy,
        embargo_policy=None,
    )
    samples = [_sample(1, 1, target=100)]
    cands = (
        CandidateIdentity(
            baseline_type="model",
            parameters={},
            target_semantics=TargetSemantics.CONTINUOUS,
            code_revision="v1.0.0",
        ),
    )

    with pytest.raises(ValueError, match="must have purge_policy bound"):
        StatisticalEvaluationInputBoundary.create(
            samples=samples,
            plan=plan_no_purge,
            candidate_identities=cands,
            code_revision="v1.0.0",
            target_contract_id="c",
        )
    with pytest.raises(ValueError, match="must have embargo_policy bound"):
        StatisticalEvaluationInputBoundary.create(
            samples=samples,
            plan=plan_no_embargo,
            candidate_identities=cands,
            code_revision="v1.0.0",
            target_contract_id="c",
        )
    with pytest.raises(ValueError, match="must have purge_policy bound"):
        StatisticalEvaluationManifest.compute_plan_digest(plan_no_purge)
    with pytest.raises(ValueError, match="must have embargo_policy bound"):
        StatisticalEvaluationManifest.compute_plan_digest(plan_no_embargo)


def test_manifest_create_reconciliation_rejections_and_cal_config() -> None:
    """StatisticalEvaluationManifest.create reconciles input_boundary fields against results."""
    from btg_ai_trader.statistical_baselines.calibration import CalibrationBin, CalibrationReport

    samples = [_sample(1, 1, target=100), _sample(2, 2, target=100), _sample(3, 4, target=100)]
    plan = WalkForwardPlanner.generate_plan(
        start_time=_dt(0),
        end_time=_dt(10),
        config=SplitPlanConfig(
            window_policy=WindowPolicy.EXPANDING,
            train_duration=timedelta(hours=3),
            test_duration=timedelta(hours=2),
            step_duration=timedelta(hours=2),
            validation_duration=timedelta(hours=2),
            purge_policy=PurgePolicy(purge_overlapping=True, fail_closed_on_unknown=False),
            embargo_policy=EmbargoPolicy(duration=timedelta(0)),
        ),
        plan_id="plan_manifest_test",
    )
    res = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
        baseline_factory=lambda: ConstantBaseline(
            constant_value=Decimal("100"), code_revision="v1.0.0"
        ),
        plan=plan,
        samples=samples,
        role=EvaluationRole.VALIDATION_SELECTION,
        code_revision="v1.0.0",
    )
    b1 = ConstantBaseline(constant_value=Decimal("100"), code_revision="v1.0.0")
    cand_identity = b1.identity

    evaluated_metric_names = tuple(
        sorted({name for fold in res.fold_results for name in fold.metrics})
    )
    bnd_valid = StatisticalEvaluationInputBoundary.create(
        samples=samples,
        plan=plan,
        candidate_identities=(cand_identity,),
        code_revision="v1.0.0",
        target_contract_id=res.target_contract_id,
        metric_names=evaluated_metric_names,
        aggregation_policy=res.aggregation_policy,
        numeric_policy=res.numeric_policy,
    )

    diff_samples = [_sample(1, 1, target=200)]
    bnd_diff_ds = StatisticalEvaluationInputBoundary.create(
        samples=diff_samples,
        plan=plan,
        candidate_identities=bnd_valid.candidate_identities,
        code_revision="v1.0.0",
        target_contract_id=res.target_contract_id,
    )
    with pytest.raises(ValueError, match="dataset_digest.*does not match"):
        StatisticalEvaluationManifest.create(
            plan=plan,
            samples=samples,
            candidate_identities=bnd_valid.candidate_identities,
            aggregate_results=[res],
            comparison_results=[],
            code_revision="v1.0.0",
            execution_timestamp=_dt(10),
            input_boundary=bnd_diff_ds,
        )

    plan2 = WalkForwardPlanner.generate_plan(
        start_time=_dt(0),
        end_time=_dt(10),
        config=SplitPlanConfig(
            window_policy=WindowPolicy.ROLLING,
            train_duration=timedelta(hours=3),
            test_duration=timedelta(hours=2),
            step_duration=timedelta(hours=2),
            validation_duration=timedelta(hours=2),
            purge_policy=PurgePolicy(purge_overlapping=True, fail_closed_on_unknown=False),
            embargo_policy=EmbargoPolicy(duration=timedelta(0)),
        ),
        plan_id="plan_manifest_diff",
    )
    bnd_diff_plan = StatisticalEvaluationInputBoundary.create(
        samples=samples,
        plan=plan2,
        candidate_identities=bnd_valid.candidate_identities,
        code_revision="v1.0.0",
        target_contract_id=res.target_contract_id,
    )
    with pytest.raises(ValueError, match="plan_digest.*does not match"):
        StatisticalEvaluationManifest.create(
            plan=plan,
            samples=samples,
            candidate_identities=bnd_valid.candidate_identities,
            aggregate_results=[res],
            comparison_results=[],
            code_revision="v1.0.0",
            execution_timestamp=_dt(10),
            input_boundary=bnd_diff_plan,
        )

    bnd_diff_rev = StatisticalEvaluationInputBoundary.create(
        samples=samples,
        plan=plan,
        candidate_identities=bnd_valid.candidate_identities,
        code_revision="v2.0.0",
        target_contract_id=res.target_contract_id,
    )
    with pytest.raises(ValueError, match="code_revision.*does not match"):
        StatisticalEvaluationManifest.create(
            plan=plan,
            samples=samples,
            candidate_identities=bnd_valid.candidate_identities,
            aggregate_results=[res],
            comparison_results=[],
            code_revision="v1.0.0",
            execution_timestamp=_dt(10),
            input_boundary=bnd_diff_rev,
        )

    other_cand = CandidateIdentity(
        baseline_type="Other",
        parameters={},
        target_semantics=TargetSemantics.CONTINUOUS,
        code_revision="v1.0.0",
    )
    bnd_diff_cands = StatisticalEvaluationInputBoundary.create(
        samples=samples,
        plan=plan,
        candidate_identities=(other_cand,),
        code_revision="v1.0.0",
        target_contract_id=res.target_contract_id,
    )
    with pytest.raises(ValueError, match="candidate_identities.*does not match"):
        StatisticalEvaluationManifest.create(
            plan=plan,
            samples=samples,
            candidate_identities=bnd_valid.candidate_identities,
            aggregate_results=[res],
            comparison_results=[],
            code_revision="v1.0.0",
            execution_timestamp=_dt(10),
            input_boundary=bnd_diff_cands,
        )

    bnd_diff_agg = StatisticalEvaluationInputBoundary.create(
        samples=samples,
        plan=plan,
        candidate_identities=bnd_valid.candidate_identities,
        code_revision="v1.0.0",
        target_contract_id=res.target_contract_id,
        aggregation_policy=FoldAggregationPolicy.SAMPLE_WEIGHTED,
    )
    with pytest.raises(ValueError, match="aggregation_policy.*does not match"):
        StatisticalEvaluationManifest.create(
            plan=plan,
            samples=samples,
            candidate_identities=bnd_valid.candidate_identities,
            aggregate_results=[res],
            comparison_results=[],
            code_revision="v1.0.0",
            execution_timestamp=_dt(10),
            input_boundary=bnd_diff_agg,
        )

    from btg_ai_trader.statistical_baselines.evaluation import AggregateEvaluationResult

    cal_rep = CalibrationReport(
        bins=(CalibrationBin(0, Decimal("0"), Decimal("1"), 1, Decimal("0.5"), Decimal("0")),),
        num_bins=1,
        expected_calibration_error=Decimal("0.5"),
        maximum_calibration_error=Decimal("0.5"),
    )
    fold_with_cal = FoldEvaluationResult(
        fold_id="f0",
        candidate_id="cand_cal",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        metrics={"ece": Decimal("0.5")},
        sample_count=1,
        cold_start_count=0,
        calibration_report=cal_rep,
    )
    cand_cal_id = CandidateIdentity(
        baseline_type="cand_cal",
        parameters={},
        target_semantics=TargetSemantics.BINARY_PROBABILITY,
        code_revision="v1.0.0",
    )
    res_with_cal = AggregateEvaluationResult(
        candidate_id="cand_cal",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        fold_results=(fold_with_cal,),
        aggregate_metrics={"mean_ece": Decimal("0.5")},
        total_samples=1,
        total_cold_starts=0,
        aggregation_policy=FoldAggregationPolicy.EQUAL_FOLD,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        target_contract_id="contract_cal",
        code_revision="v1.0.0",
    )
    manifest = StatisticalEvaluationManifest.create(
        plan=plan,
        samples=samples,
        candidate_identities=(cand_cal_id,),
        aggregate_results=[res_with_cal],
        comparison_results=[],
        code_revision="v1.0.0",
        execution_timestamp=_dt(10),
        input_boundary=None,
    )
    assert manifest.input_boundary is not None
    assert manifest.input_boundary.calibration_config == {"bins": 1}

    # Happy path: input_boundary provided and matches
    m_valid = StatisticalEvaluationManifest.create(
        plan=plan,
        samples=samples,
        candidate_identities=bnd_valid.candidate_identities,
        aggregate_results=[res],
        comparison_results=[],
        code_revision="v1.0.0",
        execution_timestamp=_dt(10),
        input_boundary=bnd_valid,
    )
    assert m_valid.input_boundary == bnd_valid

    # A boundary that records evaluated metrics cannot be paired with no evaluation results.
    with pytest.raises(ValueError, match="logical_evaluation_digest"):
        StatisticalEvaluationManifest.create(
            plan=plan,
            samples=samples,
            candidate_identities=bnd_valid.candidate_identities,
            aggregate_results=[],
            comparison_results=[],
            code_revision="v1.0.0",
            execution_timestamp=_dt(10),
            input_boundary=bnd_valid,
        )


def test_baseline_code_revision_required_and_differentiating() -> None:
    """All baselines require code_revision and different revisions produce different identities."""
    from btg_ai_trader.statistical_baselines.baselines import (
        ConstantBaseline,
        HistoricalMeanBaseline,
        HistoricalMedianBaseline,
        HistoricalPriorProbabilityBaseline,
        LastKnownClassBaseline,
        MajorityClassBaseline,
        PersistenceBaseline,
    )

    def _make_c1(**kw: Any) -> Any:
        return ConstantBaseline(constant_value=Decimal("1"), **kw)

    def _make_c2(**kw: Any) -> Any:
        return PersistenceBaseline(**kw)

    def _make_c3(**kw: Any) -> Any:
        return HistoricalMeanBaseline(**kw)

    def _make_c4(**kw: Any) -> Any:
        return HistoricalMedianBaseline(**kw)

    def _make_c5(**kw: Any) -> Any:
        return HistoricalPriorProbabilityBaseline(**kw)

    def _make_c6(**kw: Any) -> Any:
        return MajorityClassBaseline(**kw)

    def _make_c7(**kw: Any) -> Any:
        return LastKnownClassBaseline(**kw)

    baseline_factories: list[Callable[..., Any]] = [
        _make_c1,
        _make_c2,
        _make_c3,
        _make_c4,
        _make_c5,
        _make_c6,
        _make_c7,
    ]

    for factory in baseline_factories:
        with pytest.raises(TypeError):
            factory()

        b1 = factory(code_revision="v1.0.0")
        b2 = factory(code_revision="v1.0.1")
        assert b1.identity.code_revision == "v1.0.0"
        assert b2.identity.code_revision == "v1.0.1"
        assert b1.identity.candidate_id != b2.identity.candidate_id


def test_decimal_metamorphic_robustness() -> None:
    """Changing global Decimal context has zero effect under explicit NumericPolicy."""
    from btg_ai_trader.statistical_baselines.baselines import HistoricalMeanBaseline

    samples = [
        _sample(1, 1, target=Decimal("100.12345678901234567890")),
        _sample(2, 2, target=Decimal("102.98765432109876543210")),
        _sample(3, 4, target=Decimal("105.55555555555555555555")),
        _sample(4, 6, target=Decimal("101.22222222222222222222")),
    ]
    plan = WalkForwardPlanner.generate_plan(
        start_time=_dt(0),
        end_time=_dt(10),
        config=SplitPlanConfig(
            window_policy=WindowPolicy.EXPANDING,
            train_duration=timedelta(hours=3),
            test_duration=timedelta(hours=2),
            step_duration=timedelta(hours=2),
            validation_duration=timedelta(hours=2),
            purge_policy=PurgePolicy(purge_overlapping=True, fail_closed_on_unknown=False),
            embargo_policy=EmbargoPolicy(duration=timedelta(0)),
        ),
        plan_id="plan_metamorphic",
    )

    b_mean = HistoricalMeanBaseline(code_revision="v1.0.0")

    with decimal.localcontext() as ctx:
        ctx.prec = 5
        res_prec5 = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
            baseline_factory=lambda: HistoricalMeanBaseline(code_revision="v1.0.0"),
            plan=plan,
            samples=samples,
            role=EvaluationRole.VALIDATION_SELECTION,
            code_revision="v1.0.0",
        )
        manifest_prec5 = StatisticalEvaluationManifest.create(
            plan=plan,
            samples=samples,
            candidate_identities=(b_mean.identity,),
            aggregate_results=[res_prec5],
            comparison_results=[],
            code_revision="v1.0.0",
            execution_timestamp=_dt(10),
        )

    with decimal.localcontext() as ctx:
        ctx.prec = 60
        res_prec60 = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
            baseline_factory=lambda: HistoricalMeanBaseline(code_revision="v1.0.0"),
            plan=plan,
            samples=samples,
            role=EvaluationRole.VALIDATION_SELECTION,
            code_revision="v1.0.0",
        )
        manifest_prec60 = StatisticalEvaluationManifest.create(
            plan=plan,
            samples=samples,
            candidate_identities=(b_mean.identity,),
            aggregate_results=[res_prec60],
            comparison_results=[],
            code_revision="v1.0.0",
            execution_timestamp=_dt(10),
        )

    assert res_prec5.aggregate_metrics == res_prec60.aggregate_metrics
    assert (
        res_prec5.stability_diagnostics["mae"].min_value
        == res_prec60.stability_diagnostics["mae"].min_value
    )
    assert manifest_prec5.manifest_digest == manifest_prec60.manifest_digest

    pol_custom = NumericPolicy(precision=12)
    b_custom = HistoricalMeanBaseline(code_revision="v1.0.0", numeric_policy=pol_custom)
    assert b_custom.identity.candidate_id != b_mean.identity.candidate_id



def test_comparator_rejection_reasons_comprehensive() -> None:
    """Comparator rejects all variations violating evaluation context parity."""
    from btg_ai_trader.statistical_baselines.evaluation import (
        AggregateEvaluationResult,
        FoldEvaluationResult,
    )

    base_res = AggregateEvaluationResult(
        candidate_id="c1",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        fold_results=(),
        aggregate_metrics={"mae": Decimal("1")},
        total_samples=10,
        total_cold_starts=0,
        aggregation_policy=FoldAggregationPolicy.EQUAL_FOLD,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        evaluation_context_fingerprint="fp_1",
        target_contract_id="contract_s4",
        code_revision="v1.0.0",
    )

    res_diff_fp = AggregateEvaluationResult(
        candidate_id="c2",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        fold_results=(),
        aggregate_metrics={"mae": Decimal("2")},
        total_samples=10,
        total_cold_starts=0,
        aggregation_policy=FoldAggregationPolicy.EQUAL_FOLD,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        evaluation_context_fingerprint="fp_2",
        target_contract_id="contract_s4",
        code_revision="v1.0.0",
    )
    with pytest.raises(ParityViolationError, match="NOT_COMPARABLE"):
        Comparator.compare_candidates([base_res, res_diff_fp], "mae")

    fold1 = FoldEvaluationResult(
        fold_id="f0",
        candidate_id="c1",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        metrics={"mae": Decimal("1")},
        sample_count=5,
        cold_start_count=0,
    )
    fold2 = FoldEvaluationResult(
        fold_id="f1",
        candidate_id="c2",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        metrics={"mae": Decimal("1")},
        sample_count=5,
        cold_start_count=0,
    )
    res_folds1 = AggregateEvaluationResult(
        candidate_id="c1",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        fold_results=(fold1,),
        aggregate_metrics={"mae": Decimal("1")},
        total_samples=5,
        total_cold_starts=0,
        aggregation_policy=FoldAggregationPolicy.EQUAL_FOLD,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        evaluation_context_fingerprint="fp_1",
    )
    res_folds2 = AggregateEvaluationResult(
        candidate_id="c2",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        fold_results=(fold2,),
        aggregate_metrics={"mae": Decimal("2")},
        total_samples=5,
        total_cold_starts=0,
        aggregation_policy=FoldAggregationPolicy.EQUAL_FOLD,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        evaluation_context_fingerprint="fp_1",
    )
    with pytest.raises(ParityViolationError, match="Experimental parity violation: candidate"):
        Comparator.compare_candidates([res_folds1, res_folds2], "mae")
