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
from datetime import UTC, datetime, timedelta
from decimal import Decimal

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
        purge_policy=PurgePolicy(purge_overlapping=True),
        embargo_policy=EmbargoPolicy(duration=timedelta(minutes=10)),
    )
    plan1 = WalkForwardPlanner.generate_plan(
        start_time=_dt(1),
        end_time=_dt(6),
        config=config,
        plan_id="plan_test",
    )
    purge2 = PurgePolicy(purge_overlapping=False)
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
        purge_policy=PurgePolicy(purge_overlapping=False),
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
        purge_policy=PurgePolicy(purge_overlapping=True, default_horizon=timedelta(hours=1)),
        embargo_policy=EmbargoPolicy(duration=timedelta(minutes=10)),
    )
    plan_p1 = WalkForwardPlanner.generate_plan(
        start_time=_dt(1),
        end_time=_dt(6),
        config=config1,
        plan_id="plan_test",
    )
    plan_p2 = plan_p1.with_policies(
        purge_policy=PurgePolicy(purge_overlapping=False),
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
        purge_policy=PurgePolicy(purge_overlapping=False),
        embargo_policy=EmbargoPolicy(duration=timedelta(0)),
    )
    plan = WalkForwardPlanner.generate_plan(
        start_time=_dt(1),
        end_time=_dt(5),
        config=config,
        plan_id="plan_test",
    )
    s1 = _sample(1, 1, target=100)
    input_b = StatisticalEvaluationInputBoundary(
        sample_ids=("s_1",),
        dataset_digest="ds_hash",
        source_lineage_digest="src_hash",
        target_semantics=TargetSemantics.CONTINUOUS,
        target_contract_id="contract_1",
        candidate_identities=(cand,),
        search_family=None,
        plan_digest="plan_hash",
        fold_definitions=(),
        purge_policy=PurgePolicy(purge_overlapping=False),
        embargo_policy=EmbargoPolicy(duration=timedelta(0)),
        metric_names=("mae",),
        calibration_config={},
        aggregation_policy=FoldAggregationPolicy.EQUAL_FOLD,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        code_revision="v1.0.0",
        logical_evaluation_digest="logical_digest_1",
    )
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
        input_boundary=input_b,
    )
    m2 = StatisticalEvaluationManifest.create(
        plan=plan,
        samples=[s1],
        candidate_identities=[cand],
        aggregate_results=[agg],
        comparison_results=[],
        code_revision="v1.0.0",
        execution_timestamp=_dt(20),
        input_boundary=input_b,
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
    with pytest.raises(
        ValueError, match=r"information_interval start .* cannot be after end"
    ):
        PredictionInput(
            sample_id="p1",
            feature_knowledge_time=_dt(1),
            target_semantics=TargetSemantics.CONTINUOUS,
            information_interval=(_dt(5), _dt(2)),
        )
    valid_pi = PredictionInput(
        sample_id="p_valid",
        feature_knowledge_time=_dt(1),
        target_semantics=TargetSemantics.CONTINUOUS,
        information_interval=(_dt(1), _dt(2)),
    )
    assert valid_pi.information_interval == (_dt(1), _dt(2))

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
        ConstantBaseline(constant_value="100", semantics=TargetSemantics.CONTINUOUS)  # type: ignore[arg-type]

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
        )

    with pytest.raises(TypeError, match="constant_probability must be Decimal"):
        ConstantBaseline(
            constant_probability="0.5", semantics=TargetSemantics.BINARY_PROBABILITY  # type: ignore[arg-type]
        )

    with pytest.raises(
        ValueError, match=r"constant_probability must be in \[0, 1\]"
    ):
        ConstantBaseline(
            constant_probability=Decimal("1.5"),
            semantics=TargetSemantics.BINARY_PROBABILITY,
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
        )

    # Valid binary baseline with probability
    bin_base = ConstantBaseline(
        constant_probability=Decimal("0.5"),
        semantics=TargetSemantics.BINARY_PROBABILITY,
    )
    assert bin_base.identity.parameters["constant_probability"] == "0.5"

    with pytest.raises(TypeError, match="constant_class must be str"):
        ConstantBaseline(constant_class=123, semantics=TargetSemantics.CATEGORICAL)  # type: ignore[arg-type]

    with pytest.raises(
        ValueError, match="Conflicting config: constant_value must be None for CATEGORICAL"
    ):
        ConstantBaseline(
            constant_class="UP",
            constant_value=Decimal("1"),
            semantics=TargetSemantics.CATEGORICAL,
        )

    with pytest.raises(TypeError, match="constant_probability must be Decimal"):
        ConstantBaseline(
            constant_class="UP",
            constant_probability="invalid",  # type: ignore[arg-type]
            semantics=TargetSemantics.CATEGORICAL,
        )

    with pytest.raises(
        ValueError, match=r"constant_probability must be in \[0, 1\]"
    ):
        ConstantBaseline(
            constant_class="UP",
            constant_probability=Decimal("1.5"),
            semantics=TargetSemantics.CATEGORICAL,
        )

    with pytest.raises(ValueError, match="Unsupported target semantics"):
        ConstantBaseline(
            constant_value=Decimal("1"),
            semantics="UNSUPPORTED",  # type: ignore[arg-type]
        )

    # Valid categorical with probability parameter
    cat_prob = ConstantBaseline(
        constant_class="UP",
        constant_probability=Decimal("0.8"),
        semantics=TargetSemantics.CATEGORICAL,
    )
    assert cat_prob.identity.parameters["constant_probability"] == "0.8"

    # Valid categorical without probability parameter
    cat_no_prob = ConstantBaseline(
        constant_class="DOWN",
        semantics=TargetSemantics.CATEGORICAL,
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

    # Hits lines 276, 278 when plan.purge_policy is None
    agg_none = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
        baseline_factory=lambda: ConstantBaseline(constant_value=Decimal("100")),
        plan=plan_with_nones,
        samples=samples,
        role=EvaluationRole.VALIDATION_SELECTION,
    )
    assert agg_none.total_samples > 0

    # Hits lines 280-283: plan policy override
    agg_override = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
        baseline_factory=lambda: ConstantBaseline(constant_value=Decimal("100")),
        plan=base_plan,
        samples=samples,
        role=EvaluationRole.VALIDATION_SELECTION,
        purge_policy=PurgePolicy(purge_overlapping=False),
    )
    assert agg_override.total_samples > 0

    # SAMPLE_WEIGHTED aggregation policy and zero best_val rel_deg
    agg_sw = StatisticalEvaluationEngine.evaluate_candidate_on_plan(
        baseline_factory=lambda: ConstantBaseline(constant_value=Decimal("100")),
        plan=base_plan,
        samples=samples,
        role=EvaluationRole.VALIDATION_SELECTION,
        aggregation_policy=FoldAggregationPolicy.SAMPLE_WEIGHTED,
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
        baseline_factory=lambda: MajorityClassBaseline(),
        plan=base_plan,
        samples=cat_samples,
        role=EvaluationRole.VALIDATION_SELECTION,
    )
    assert "mean_accuracy" in agg_cat.aggregate_metrics
    acc_diag = agg_cat.stability_diagnostics["accuracy"]
    assert acc_diag.best_fold_id != ""
    assert acc_diag.worst_fold_id != ""

