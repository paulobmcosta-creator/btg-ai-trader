"""Comprehensive Sprint 6 Scenario Engine core tests."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

import btg_ai_trader.scenario_engine.core as scenario_core
from btg_ai_trader.scenario_engine import (
    ComparisonOperator,
    LossDirection,
    MetricCondition,
    MetricDirection,
    ModelEvidenceSnapshot,
    ObservedSeries,
    ProtectedAdaptationRecord,
    QuantileConvention,
    RegimeAssignment,
    RegimeDefinition,
    RegimeDefinitionMode,
    RegimeObservation,
    RegimeUseMode,
    ResearchArtifactKind,
    ResearchArtifactRecord,
    ResearchAttemptRecord,
    RobustnessCharacterization,
    ScenarioDisposition,
    ScenarioDispositionPolicy,
    ScenarioGrid,
    ScenarioInputBoundary,
    ScenarioOutcome,
    ScenarioOutcomeSet,
    ScenarioResearchHistory,
    ScenarioRunManifest,
    ScenarioShock,
    ScenarioSpec,
    ShockTarget,
    SourceKind,
    TailMetricPolicy,
    ThresholdRule,
    build_scenario_outcome_set,
    characterize_robustness,
    classify_regime,
    compute_path_metrics,
    compute_tail_metrics,
    evaluate_disposition,
    fit_development_threshold_definition,
    summarize_metric_by_regime,
    summarize_observed_series,
    summarize_scenario_outcomes,
    verify_deterministic_equivalence,
    verify_experimental_parity,
)
from btg_ai_trader.statistical_baselines.boundaries import (
    EvaluationBoundary,
    TemporalFold,
    WalkForwardPlan,
)
from btg_ai_trader.statistical_baselines.comparison import (
    EvaluationHistory,
    ProtectedEvidenceUse,
)
from btg_ai_trader.statistical_baselines.domain import (
    CandidateIdentity,
    EvaluationRole,
    ParityViolationError,
    ProtectedEvidenceReuseError,
    StatisticalSample,
    TargetSemantics,
)
from btg_ai_trader.statistical_baselines.evaluation import (
    AggregateEvaluationResult,
    FoldEvaluationResult,
)
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY
from btg_ai_trader.statistical_baselines.provenance import StatisticalEvaluationInputBoundary
from btg_ai_trader.statistical_baselines.splits import EmbargoPolicy, PurgePolicy


def dt(second: int = 0) -> datetime:
    return datetime(2026, 9, 22, 12, 0, second, tzinfo=UTC)


def make_observation(
    obs_id: str = "o1",
    value: Decimal = Decimal("10"),
    *,
    event_time: datetime | None = None,
) -> RegimeObservation:
    return RegimeObservation(
        observation_id=obs_id,
        knowledge_time=dt(),
        variables={"vol": value},
        source_lineage_digest="a" * 64,
        event_time=event_time,
        variable_units={"vol": "unitless"},
    )


def make_definition(
    *,
    mode: RegimeDefinitionMode = RegimeDefinitionMode.PREDECLARED,
    development_boundary_id: str | None = None,
) -> RegimeDefinition:
    return RegimeDefinition(
        definition_id="regime-v1",
        mode=mode,
        rules=(
            ThresholdRule("vol", ComparisonOperator.LT, Decimal("10"), "LOW"),
            ThresholdRule("vol", ComparisonOperator.GE, Decimal("10"), "HIGH"),
        ),
        default_label="UNKNOWN",
        source_lineage_digest="a" * 64,
        development_boundary_id=development_boundary_id,
    )


def make_scenario(
    scenario_id: str = "s1",
    *,
    shocks: tuple[ScenarioShock, ...] | None = None,
    predeclared: bool = True,
    baseline_ref: str = "c" * 64,
    constraints: tuple[str, ...] = (),
) -> ScenarioSpec:
    return ScenarioSpec(
        scenario_id=scenario_id,
        baseline_evidence_ref=baseline_ref,
        shocks=shocks
        or (ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("1.5"), "multiplier"),),
        structural_constraints=constraints,
        predeclared=predeclared,
        research_history_ref="history-v1",
        code_revision="d" * 40,
    )


def make_policy(
    *,
    mode: RegimeDefinitionMode = RegimeDefinitionMode.PREDECLARED,
    development_boundary_id: str | None = None,
) -> ScenarioDispositionPolicy:
    return ScenarioDispositionPolicy(
        evaluation_scope="RESEARCH_SCENARIO",
        conditions=(
            MetricCondition("pnl", MetricDirection.MAXIMIZE, Decimal("0")),
            MetricCondition("dd", MetricDirection.MINIMIZE, Decimal("20")),
        ),
        invalidity_labels=("LEAKAGE", "BOUNDARY_MISMATCH"),
        definition_mode=mode,
        development_boundary_id=development_boundary_id,
    )


def test_jsonable_canonical_fallbacks() -> None:
    assert scenario_core._jsonable("plain") == "plain"
    assert scenario_core._jsonable([Decimal("1"), "x"]) == ["1", "x"]
    assert scenario_core._jsonable({"b": Decimal("2"), "a": Decimal("1")}) == {"a": "1", "b": "2"}
    assert scenario_core._jsonable(dt()) == dt().isoformat()
    assert scenario_core._jsonable(ComparisonOperator.GE) == "GE"


def test_private_model_snapshot_issuer_fails_closed() -> None:
    valid: dict[str, object] = {
        "candidate_id": "candidate-1",
        "evaluation_scope": "MODEL",
        "evaluation_role": EvaluationRole.VALIDATION_SELECTION,
        "protected_boundary_id": None,
        "dataset_digest": "a" * 64,
        "plan_digest": "b" * 64,
        "target_contract_digest": "c" * 64,
        "experimental_context_fingerprint": "d" * 64,
        "metrics": {"mae": Decimal("1")},
        "disposition": "INCONCLUSIVE",
        "source_manifest_ids": ("m" * 64,),
        "source_code_revision": "e" * 40,
        "numeric_policy": DEFAULT_NUMERIC_POLICY,
        "issuer_token": scenario_core._MODEL_SNAPSHOT_ISSUER_TOKEN,
    }
    issued = scenario_core._issue_model_evidence_snapshot(**valid)  # type: ignore[arg-type]
    assert issued.is_verified

    with pytest.raises(PermissionError, match="verified S5 adapter"):
        scenario_core._issue_model_evidence_snapshot(
            **(valid | {"issuer_token": object()})  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="MODEL evaluation scope"):
        scenario_core._issue_model_evidence_snapshot(
            **(valid | {"evaluation_scope": "STRATEGY"})  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="requires protected_boundary_id"):
        scenario_core._issue_model_evidence_snapshot(
            **(
                valid
                | {
                    "evaluation_role": EvaluationRole.PROTECTED_TEST,
                    "protected_boundary_id": None,
                }
            )  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="non-protected"):
        scenario_core._issue_model_evidence_snapshot(
            **(valid | {"protected_boundary_id": "pb"})  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="non-empty immutable identities"):
        scenario_core._issue_model_evidence_snapshot(
            **(valid | {"source_manifest_ids": ()})  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="non-empty immutable identities"):
        scenario_core._issue_model_evidence_snapshot(
            **(valid | {"source_manifest_ids": ("",)})  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="must be unique"):
        scenario_core._issue_model_evidence_snapshot(
            **(
                valid
                | {"source_manifest_ids": ("m" * 64, "m" * 64)}
            )  # type: ignore[arg-type]
        )


def test_input_boundary_and_model_snapshot_validation() -> None:
    series = ObservedSeries(
        "series", "trades", "trade", "BRL",
        (Decimal("1"), Decimal("2")), ("o1", "o2"), "source-root", "REJECT",
    )
    boundary = ScenarioInputBoundary.from_observed_series(
        series,
        evaluation_role=EvaluationRole.DEVELOPMENT,
        protected_boundary_id=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        source_code_revision="c" * 40,
        scenario_code_revision="d" * 40,
    )
    assert boundary.is_verified
    assert boundary.source_digest == series.series_digest
    protected = ScenarioInputBoundary.from_observed_series(
        series,
        evaluation_role=EvaluationRole.PROTECTED_TEST,
        protected_boundary_id="protected-1",
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        source_code_revision="c" * 40,
        scenario_code_revision="d" * 40,
    )
    assert protected.protected_boundary_id == "protected-1"
    with pytest.raises(ValueError, match="PROTECTED_TEST requires"):
        ScenarioInputBoundary.from_observed_series(
            series,
            evaluation_role=EvaluationRole.PROTECTED_TEST,
            protected_boundary_id=None,
            numeric_policy=DEFAULT_NUMERIC_POLICY,
            source_code_revision="c",
            scenario_code_revision="d",
        )
    with pytest.raises(ValueError, match="only valid for PROTECTED_TEST"):
        ScenarioInputBoundary.from_observed_series(
            series,
            evaluation_role=EvaluationRole.DEVELOPMENT,
            protected_boundary_id="bad",
            numeric_policy=DEFAULT_NUMERIC_POLICY,
            source_code_revision="c",
            scenario_code_revision="d",
        )
    with pytest.raises(ValueError, match="source_code_revision"):
        ScenarioInputBoundary.from_observed_series(
            series,
            evaluation_role=EvaluationRole.DEVELOPMENT,
            protected_boundary_id=None,
            numeric_policy=DEFAULT_NUMERIC_POLICY,
            source_code_revision="",
            scenario_code_revision="d",
        )
    unverified_snapshot = ModelEvidenceSnapshot(
        candidate_id="candidate-1",
        evaluation_scope="MODEL",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        protected_boundary_id=None,
        dataset_digest="a" * 64,
        plan_digest="b" * 64,
        target_contract_digest="c" * 64,
        experimental_context_fingerprint="d" * 64,
        metrics={"mae": Decimal("1.5")},
        disposition="INCONCLUSIVE",
        source_manifest_ids=("f" * 64,),
        source_code_revision="e" * 40,
        numeric_policy_digest="1" * 64,
        snapshot_digest="2" * 64,
    )
    assert not unverified_snapshot.is_verified
    with pytest.raises(ValueError, match="must be verified"):
        ScenarioInputBoundary.from_model_snapshot(
            unverified_snapshot,
            scenario_code_revision="f" * 40,
        )


def make_verified_statistical_source() -> tuple[
    StatisticalEvaluationInputBoundary,
    AggregateEvaluationResult,
]:
    t0 = dt()
    t1 = t0 + timedelta(minutes=1)
    t2 = t0 + timedelta(minutes=2)
    fold = TemporalFold(
        fold_id="f1",
        development_boundary=EvaluationBoundary(t0, t2, knowledge_cutoff=t0),
        training_boundary=EvaluationBoundary(t0, t1, knowledge_cutoff=t0),
        protected_evaluation_boundary=EvaluationBoundary(t1, t2, knowledge_cutoff=t1),
        knowledge_cutoff=t1,
        window_policy_name="EXPANDING",
    )
    plan = WalkForwardPlan(
        plan_id="plan",
        window_policy_name="EXPANDING",
        folds=(fold,),
        purge_policy=PurgePolicy(purge_overlapping=True, fail_closed_on_unknown=False),
        embargo_policy=EmbargoPolicy(duration=timedelta(0)),
    )
    sample = StatisticalSample(
        sample_id="sample",
        feature_knowledge_time=t0,
        target_knowledge_time=t0,
        target_value=Decimal("1"),
        target_semantics=TargetSemantics.CONTINUOUS,
        source_lineage="source",
    )
    revision = "revision"
    candidate = CandidateIdentity("Mean", {}, TargetSemantics.CONTINUOUS, revision)
    input_boundary = StatisticalEvaluationInputBoundary.create(
        [sample],
        plan,
        [candidate],
        revision,
        target_contract_id="target",
        metric_names=("mae",),
    )
    fold_result = FoldEvaluationResult(
        fold_id="f1",
        candidate_id=candidate.candidate_id,
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        metrics={"mae": Decimal("1")},
        sample_count=1,
        cold_start_count=0,
    )
    aggregate = AggregateEvaluationResult(
        candidate_id=candidate.candidate_id,
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        fold_results=(fold_result,),
        aggregate_metrics={"mean_mae": Decimal("1")},
        total_samples=1,
        total_cold_starts=0,
        numeric_policy=input_boundary.numeric_policy,
        target_contract_id="target",
        code_revision=revision,
        evaluation_context_fingerprint="context",
    )
    return input_boundary, aggregate


def test_statistical_evidence_boundary_is_verified_and_context_bound() -> None:
    input_boundary, aggregate = make_verified_statistical_source()
    boundary = ScenarioInputBoundary.from_statistical_evaluation(
        input_boundary, aggregate, protected_boundary_id=None, scenario_code_revision="s6"
    )
    assert boundary.is_verified
    assert boundary.source_kind is SourceKind.STATISTICAL_EVALUATION
    unverified = StatisticalEvaluationInputBoundary(
        sample_ids=input_boundary.sample_ids,
        dataset_digest=input_boundary.dataset_digest,
        source_lineage_digest=input_boundary.source_lineage_digest,
        target_semantics=input_boundary.target_semantics,
        target_contract_id=input_boundary.target_contract_id,
        candidate_identities=input_boundary.candidate_identities,
        search_family=input_boundary.search_family,
        plan_digest=input_boundary.plan_digest,
        fold_definitions=input_boundary.fold_definitions,
        purge_policy=input_boundary.purge_policy,
        embargo_policy=input_boundary.embargo_policy,
        metric_names=input_boundary.metric_names,
        calibration_config=input_boundary.calibration_config,
        aggregation_policy=input_boundary.aggregation_policy,
        numeric_policy=input_boundary.numeric_policy,
        code_revision=input_boundary.code_revision,
        logical_evaluation_digest=input_boundary.logical_evaluation_digest,
    )
    with pytest.raises(ValueError, match="must be verified"):
        ScenarioInputBoundary.from_statistical_evaluation(
            unverified, aggregate, protected_boundary_id=None, scenario_code_revision="s6"
        )
    with pytest.raises(ValueError, match="does not match verified"):
        ScenarioInputBoundary.from_statistical_evaluation(
            input_boundary,
            replace(aggregate, candidate_id="not-bound"),
            protected_boundary_id=None,
            scenario_code_revision="s6",
        )
    protected_record = ProtectedEvidenceUse(
        candidate_id=aggregate.candidate_id,
        protected_boundary_id="pb-real",
        evaluation_role=EvaluationRole.PROTECTED_TEST,
    )
    protected_result = replace(
        aggregate,
        evaluation_role=EvaluationRole.PROTECTED_TEST,
        fold_results=tuple(
            replace(fold, evaluation_role=EvaluationRole.PROTECTED_TEST)
            for fold in aggregate.fold_results
        ),
        protected_evidence_records=(protected_record,),
    )
    protected_boundary = ScenarioInputBoundary.from_statistical_evaluation(
        input_boundary,
        protected_result,
        protected_boundary_id="pb-real",
        scenario_code_revision="s6",
    )
    assert protected_boundary.protected_boundary_id == "pb-real"
    with pytest.raises(ValueError, match="does not match statistical protected"):
        ScenarioInputBoundary.from_statistical_evaluation(
            input_boundary, protected_result,
            protected_boundary_id="pb-wrong", scenario_code_revision="s6",
        )
    with pytest.raises(ValueError, match="canonical protected record"):
        ScenarioInputBoundary.from_statistical_evaluation(
            input_boundary,
            replace(protected_result, protected_evidence_records=()),
            protected_boundary_id="pb-real",
            scenario_code_revision="s6",
        )
    with pytest.raises(ValueError, match="cannot carry protected"):
        ScenarioInputBoundary.from_statistical_evaluation(
            input_boundary,
            replace(aggregate, protected_evidence_records=(protected_record,)),
            protected_boundary_id=None,
            scenario_code_revision="s6",
        )
    with pytest.raises(ValueError, match="does not match verified"):
        ScenarioInputBoundary.from_statistical_evaluation(
            input_boundary,
            replace(protected_result, fold_results=aggregate.fold_results),
            protected_boundary_id="pb-real",
            scenario_code_revision="s6",
        )


def test_regime_contracts_classification_and_development_fit() -> None:
    obs = make_observation(event_time=dt())
    assert obs.variables["vol"] == Decimal("10")
    assert obs.variable_units["vol"] == "unitless"
    with pytest.raises(ValueError, match="timezone-aware"):
        RegimeObservation(
            "x", datetime(2026, 1, 1), {"vol": Decimal(1)}, "a",
            variable_units={"vol": "unitless"},
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        RegimeObservation(
            "x", dt(), {"vol": Decimal(1)}, "a",
            datetime(2026, 1, 1), {"vol": "unitless"},
        )
    with pytest.raises(ValueError, match="later than knowledge_time"):
        RegimeObservation(
            "x", dt(), {"vol": Decimal(1)}, "a", dt(1), {"vol": "unitless"},
        )
    with pytest.raises(ValueError, match="exactly one unit"):
        RegimeObservation("x", dt(), {"vol": Decimal(1)}, "a")
    with pytest.raises(TypeError, match="threshold"):
        ThresholdRule("vol", ComparisonOperator.LT, 1, "LOW")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unit"):
        ThresholdRule("vol", ComparisonOperator.LT, Decimal(1), "LOW", "")
    for operator, value, expected in (
        (ComparisonOperator.LT, Decimal("9"), "YES"),
        (ComparisonOperator.LE, Decimal("10"), "YES"),
        (ComparisonOperator.GE, Decimal("10"), "YES"),
        (ComparisonOperator.GT, Decimal("11"), "YES"),
    ):
        definition = RegimeDefinition(
            definition_id=f"d-{operator.value}",
            mode=RegimeDefinitionMode.PREDECLARED,
            rules=(ThresholdRule("vol", operator, Decimal("10"), "YES"),),
            default_label="NO",
            source_lineage_digest="a" * 64,
        )
        assert classify_regime(
            definition,
            make_observation(value=value),
            use_mode=RegimeUseMode.CAUSAL_STRATIFICATION,
            as_of_time=dt(),
        ).label == expected
    assert classify_regime(
        RegimeDefinition(
            "d-default", RegimeDefinitionMode.PREDECLARED,
            (ThresholdRule("vol", ComparisonOperator.GT, Decimal("20"), "YES"),),
            "NO", "a" * 64,
        ),
        make_observation(value=Decimal("10")),
        use_mode=RegimeUseMode.CAUSAL_STRATIFICATION,
        as_of_time=dt(),
    ).label == "NO"
    missing = RegimeObservation("m", dt(), {}, "a" * 64)
    assert classify_regime(
        make_definition(), missing,
        use_mode=RegimeUseMode.CAUSAL_STRATIFICATION, as_of_time=dt(),
    ).label == "UNKNOWN"
    definition = make_definition()
    with pytest.raises(ValueError, match="verified upstream regime-use evidence"):
        classify_regime(
            definition, obs, use_mode=RegimeUseMode.STRATEGY_BOUND, as_of_time=dt()
        )
    retro = RegimeDefinition(
        "retro", RegimeDefinitionMode.RETROSPECTIVE_EXPLORATORY,
        (ThresholdRule("vol", ComparisonOperator.GE, Decimal("0"), "RETRO"),),
        "UNKNOWN", "a" * 64,
    )
    with pytest.raises(ValueError, match="exploratory-only"):
        classify_regime(
            retro, obs, use_mode=RegimeUseMode.CAUSAL_STRATIFICATION, as_of_time=dt()
        )
    assert classify_regime(
        retro, obs,
        use_mode=RegimeUseMode.RETROSPECTIVE_EXPLORATORY, as_of_time=dt(),
    ).label == "RETRO"
    with pytest.raises(ValueError, match="source lineage"):
        classify_regime(
            replace(make_definition(), source_lineage_digest="z" * 64),
            obs, use_mode=RegimeUseMode.CAUSAL_STRATIFICATION, as_of_time=dt(),
        )
    with pytest.raises(ValueError, match="known after as_of_time"):
        classify_regime(
            definition, replace(obs, knowledge_time=dt(1)),
            use_mode=RegimeUseMode.CAUSAL_STRATIFICATION, as_of_time=dt(),
        )
    with pytest.raises(ValueError, match="unit mismatch"):
        classify_regime(
            definition, replace(obs, variable_units={"vol": "percent"}),
            use_mode=RegimeUseMode.CAUSAL_STRATIFICATION, as_of_time=dt(),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        classify_regime(
            definition, obs, use_mode=RegimeUseMode.CAUSAL_STRATIFICATION,
            as_of_time=datetime(2026, 1, 1),
        )
    with pytest.raises(ValueError, match="rules cannot be empty"):
        RegimeDefinition("x", RegimeDefinitionMode.PREDECLARED, (), "U", "a")
    with pytest.raises(ValueError, match="requires development_boundary_id"):
        RegimeDefinition(
            "x", RegimeDefinitionMode.DEVELOPMENT_FIT,
            (ThresholdRule("vol", ComparisonOperator.GE, Decimal(1), "H"),),
            "U", "a" * 64,
        )
    with pytest.raises(ValueError, match="only valid for DEVELOPMENT_FIT"):
        RegimeDefinition(
            "x", RegimeDefinitionMode.PREDECLARED,
            (ThresholdRule("vol", ComparisonOperator.GE, Decimal(1), "H"),),
            "U", "a", development_boundary_id="bad",
        )
    odd = fit_development_threshold_definition(
        [make_observation("1", Decimal(1)), make_observation("2", Decimal(3)),
         make_observation("3", Decimal(2))],
        variable_name="vol", label_below="LOW", label_at_or_above="HIGH",
        definition_id="fit-odd", development_boundary_id="dev-1",
        source_lineage_digest="a" * 64, evaluation_role=EvaluationRole.DEVELOPMENT,
    )
    assert odd.rules[0].threshold == Decimal(2)
    even = fit_development_threshold_definition(
        [make_observation("1", Decimal(1)), make_observation("2", Decimal(3))],
        variable_name="vol", label_below="LOW", label_at_or_above="HIGH",
        definition_id="fit-even", development_boundary_id="dev-1",
        source_lineage_digest="a" * 64, evaluation_role=EvaluationRole.DEVELOPMENT,
    )
    assert even.rules[0].threshold == Decimal(2)
    with pytest.raises(ValueError, match="only on DEVELOPMENT"):
        fit_development_threshold_definition(
            [obs], variable_name="vol", label_below="L", label_at_or_above="H",
            definition_id="bad", development_boundary_id="dev",
            source_lineage_digest="a" * 64, evaluation_role=EvaluationRole.PROTECTED_TEST,
        )
    with pytest.raises(ValueError, match="cannot be empty"):
        fit_development_threshold_definition(
            [], variable_name="vol", label_below="L", label_at_or_above="H",
            definition_id="bad", development_boundary_id="dev",
            source_lineage_digest="a" * 64, evaluation_role=EvaluationRole.DEVELOPMENT,
        )
    with pytest.raises(ValueError, match="unique observation IDs"):
        fit_development_threshold_definition(
            [make_observation("dup", Decimal("1")), make_observation("dup", Decimal("2"))],
            variable_name="vol", label_below="L", label_at_or_above="H",
            definition_id="bad", development_boundary_id="dev",
            source_lineage_digest="a" * 64, evaluation_role=EvaluationRole.DEVELOPMENT,
        )
    with pytest.raises(ValueError, match="lineage"):
        fit_development_threshold_definition(
            [RegimeObservation(
                "x", dt(), {"vol": Decimal("1")}, "z" * 64,
                variable_units={"vol": "unitless"},
            )],
            variable_name="vol", label_below="L", label_at_or_above="H",
            definition_id="bad", development_boundary_id="dev",
            source_lineage_digest="a" * 64, evaluation_role=EvaluationRole.DEVELOPMENT,
        )
    with pytest.raises(ValueError, match="cannot silently drop"):
        fit_development_threshold_definition(
            [RegimeObservation("x", dt(), {}, "a" * 64)],
            variable_name="vol", label_below="L", label_at_or_above="H",
            definition_id="bad", development_boundary_id="dev",
            source_lineage_digest="a" * 64, evaluation_role=EvaluationRole.DEVELOPMENT,
        )
    with pytest.raises(ValueError, match="units"):
        fit_development_threshold_definition(
            [replace(obs, variable_units={"vol": "percent"})],
            variable_name="vol", label_below="L", label_at_or_above="H",
            definition_id="bad-unit", development_boundary_id="dev",
            source_lineage_digest="a" * 64, evaluation_role=EvaluationRole.DEVELOPMENT,
            variable_unit="unitless",
        )


def test_scenario_grid_outcome_contracts_and_summary() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("-1"), "multiplier")
    with pytest.raises(ValueError, match="unit"):
        ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("1"), "")
    with pytest.raises(ValueError, match="at least 1"):
        ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("0.5"), "multiplier")
    with pytest.raises(ValueError, match="must be positive"):
        ScenarioShock(ShockTarget.MAX_SPREAD, Decimal("0"), "price")
    with pytest.raises(ValueError, match="requires unit"):
        ScenarioShock(ShockTarget.SLIPPAGE_POINTS, Decimal("1"), "microseconds")

    with pytest.raises(ValueError, match="at least one shock"):
        ScenarioSpec("x", "a", (), (), True, "h", "c")
    duplicate = (
        ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("1"), "multiplier"),
        ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("2"), "multiplier"),
    )
    with pytest.raises(ValueError, match="duplicate shock"):
        make_scenario(shocks=duplicate, constraints=("same-axis",))
    multi = (
        ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("1"), "multiplier"),
        ScenarioShock(ShockTarget.SLIPPAGE_POINTS, Decimal("1"), "points"),
    )
    with pytest.raises(ValueError, match="structural consistency"):
        make_scenario(shocks=multi)
    multi_ok = make_scenario(shocks=multi, constraints=("joint adverse execution",))
    assert multi_ok.structural_constraints

    s1 = make_scenario("s1")
    s2 = make_scenario("s2")
    with pytest.raises(ValueError, match="must be predeclared"):
        ScenarioGrid("g", (s1,), False)
    with pytest.raises(ValueError, match="cannot be empty"):
        ScenarioGrid("g", (), True)
    with pytest.raises(ValueError, match="canonically ordered"):
        ScenarioGrid("g", (s2, s1), True)
    with pytest.raises(ValueError, match="unique"):
        ScenarioGrid("g", (s1, s1), True)
    with pytest.raises(ValueError, match="non-predeclared"):
        ScenarioGrid("g", (make_scenario("s1", predeclared=False),), True)

    grid = ScenarioGrid("g", (s1, s2), True)
    o1 = ScenarioOutcome("s1", {"pnl": Decimal("10"), "dd": Decimal("5")}, "m1")
    o2 = ScenarioOutcome("s2", {"pnl": Decimal("-2")}, "m2")
    with pytest.raises(ValueError, match="cannot be empty"):
        ScenarioOutcomeSet(grid.grid_digest, ())
    with pytest.raises(ValueError, match="exactly match"):
        build_scenario_outcome_set(grid, (o2, o1))
    outcome_set = build_scenario_outcome_set(grid, (o1, o2))
    summary = summarize_scenario_outcomes(outcome_set)
    assert summary["pnl"].minimum == Decimal("-2")
    assert summary["pnl"].maximum == Decimal("10")
    assert summary["pnl"].mean == Decimal("4")
    assert summary["pnl"].scenario_count == 2
    assert summary["pnl"].effective_count == 2
    assert summary["pnl"].missing_count == 0
    assert summary["dd"].mean == Decimal("5")
    assert summary["dd"].scenario_count == 2
    assert summary["dd"].effective_count == 1
    assert summary["dd"].missing_count == 1


def test_observed_distribution_tail_and_path_semantics() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        ObservedSeries("s", "p", "trade", "BRL", (), (), "a", "REJECT")
    with pytest.raises(ValueError, match="align one-to-one"):
        ObservedSeries("s", "p", "trade", "BRL", (Decimal(1),), (), "a", "REJECT")
    with pytest.raises(ValueError, match="unique"):
        ObservedSeries(
            "s", "p", "trade", "BRL", (Decimal(1), Decimal(2)), ("x", "x"), "a", "REJECT"
        )
    with pytest.raises(ValueError, match="timestamps must align"):
        ObservedSeries(
            "s", "p", "trade", "BRL", (Decimal(1),), ("x",), "a", "REJECT", (dt(), dt(1))
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        ObservedSeries(
            "s",
            "p",
            "trade",
            "BRL",
            (Decimal(1),),
            ("x",),
            "a",
            "REJECT",
            (datetime(2026, 1, 1),),
        )
    with pytest.raises(ValueError, match="monotonically"):
        ObservedSeries(
            "s",
            "p",
            "trade",
            "BRL",
            (Decimal(1), Decimal(2)),
            ("x", "y"),
            "a",
            "REJECT",
            (dt(1), dt()),
        )

    odd = ObservedSeries(
        "odd",
        "trades",
        "trade",
        "BRL",
        (Decimal("-1"), Decimal("2"), Decimal("3")),
        ("1", "2", "3"),
        "a",
        "REJECT",
    )
    odd_summary = summarize_observed_series(odd, loss_direction=LossDirection.LOWER_IS_LOSS)
    assert odd_summary.median == Decimal("2")
    assert odd_summary.empirical_probability_of_loss == Decimal(1) / Decimal(3)
    upper_loss_summary = summarize_observed_series(
        odd,
        loss_direction=LossDirection.HIGHER_IS_LOSS,
        loss_threshold=Decimal("2"),
    )
    assert upper_loss_summary.empirical_probability_of_loss == Decimal(1) / Decimal(3)

    even = ObservedSeries(
        "even",
        "trades",
        "trade",
        "BRL",
        (Decimal("1"), Decimal("3")),
        ("1", "2"),
        "a",
        "REJECT",
    )
    even_summary = summarize_observed_series(
        even,
        loss_direction=LossDirection.LOWER_IS_LOSS,
    )
    assert even_summary.median == Decimal("2")

    with pytest.raises(ValueError, match="predeclared"):
        TailMetricPolicy(
            Decimal("0.25"),
            LossDirection.LOWER_IS_LOSS,
            QuantileConvention.NEAREST_RANK,
            4,
            1,
            predeclared=False,
        )
    with pytest.raises(ValueError, match="tail_fraction"):
        TailMetricPolicy(
            Decimal(0),
            LossDirection.LOWER_IS_LOSS,
            QuantileConvention.NEAREST_RANK,
            1,
            1,
        )
    with pytest.raises(ValueError, match="tail_fraction"):
        TailMetricPolicy(
            Decimal("0.6"),
            LossDirection.LOWER_IS_LOSS,
            QuantileConvention.NEAREST_RANK,
            1,
            1,
        )
    with pytest.raises(ValueError, match="sample counts"):
        TailMetricPolicy(
            Decimal("0.5"),
            LossDirection.LOWER_IS_LOSS,
            QuantileConvention.NEAREST_RANK,
            0,
            1,
        )

    insufficient_policy = TailMetricPolicy(
        Decimal("0.25"),
        LossDirection.LOWER_IS_LOSS,
        QuantileConvention.NEAREST_RANK,
        10,
        2,
    )
    insufficient = compute_tail_metrics(odd, insufficient_policy)
    assert not insufficient.sufficient
    assert insufficient.value_at_risk is None

    lower_series = ObservedSeries(
        "tail",
        "trades",
        "trade",
        "BRL",
        (Decimal("-10"), Decimal("-5"), Decimal("1"), Decimal("2")),
        ("1", "2", "3", "4"),
        "a",
        "REJECT",
    )
    lower_policy = TailMetricPolicy(
        Decimal("0.5"),
        LossDirection.LOWER_IS_LOSS,
        QuantileConvention.NEAREST_RANK,
        4,
        2,
    )
    lower = compute_tail_metrics(lower_series, lower_policy)
    assert lower.sufficient
    with pytest.raises(ValueError, match="missing_policy"):
        compute_tail_metrics(replace(lower_series, missing_policy="KEEP"), lower_policy)
    assert lower.value_at_risk == Decimal("-5")
    assert lower.expected_shortfall == Decimal("-7.5")

    upper_policy = TailMetricPolicy(
        Decimal("0.5"),
        LossDirection.HIGHER_IS_LOSS,
        QuantileConvention.NEAREST_RANK,
        4,
        2,
    )
    upper = compute_tail_metrics(lower_series, upper_policy)
    assert upper.value_at_risk == Decimal("1")
    assert upper.expected_shortfall == Decimal("1.5")

    with pytest.raises(TypeError, match="ObservedSeries"):
        compute_tail_metrics("not-series", lower_policy)  # type: ignore[arg-type]

    no_time = ObservedSeries(
        "path",
        "equity",
        "point",
        "BRL",
        (Decimal("100"), Decimal("90"), Decimal("95"), Decimal("110")),
        ("1", "2", "3", "4"),
        "a",
        "REJECT",
    )
    path = compute_path_metrics(no_time)
    assert path.max_drawdown_amount == Decimal("10")
    assert path.max_drawdown_ratio is None
    assert path.max_underwater_seconds is None

    with pytest.raises(ValueError, match="positive"):
        compute_path_metrics(no_time, capital_denominator=Decimal(0))

    timed = ObservedSeries(
        "timed",
        "equity",
        "point",
        "BRL",
        (Decimal("100"), Decimal("90"), Decimal("95"), Decimal("110"), Decimal("105")),
        ("1", "2", "3", "4", "5"),
        "a",
        "REJECT",
        (dt(0), dt(1), dt(2), dt(3), dt(4)),
    )
    timed_path = compute_path_metrics(timed, capital_denominator=Decimal("100"))
    assert timed_path.max_drawdown_ratio == Decimal("0.1")
    assert timed_path.max_underwater_seconds == Decimal("3")

    unrecovered = ObservedSeries(
        "unrecovered",
        "equity",
        "point",
        "BRL",
        (Decimal("100"), Decimal("90"), Decimal("80")),
        ("1", "2", "3"),
        "a",
        "REJECT",
        (dt(0), dt(1), dt(2)),
    )
    assert compute_path_metrics(unrecovered).max_underwater_seconds == Decimal("2")


def test_disposition_robustness_history_and_manifest() -> None:
    with pytest.raises(ValueError, match="conditions cannot be empty"):
        ScenarioDispositionPolicy(
            "scope", (), (), RegimeDefinitionMode.PREDECLARED
        )
    with pytest.raises(ValueError, match="retrospectively"):
        ScenarioDispositionPolicy(
            "scope",
            (MetricCondition("x", MetricDirection.MAXIMIZE, Decimal(0)),),
            (),
            RegimeDefinitionMode.RETROSPECTIVE_EXPLORATORY,
        )
    with pytest.raises(ValueError, match="requires development_boundary_id"):
        ScenarioDispositionPolicy(
            "scope",
            (MetricCondition("x", MetricDirection.MAXIMIZE, Decimal(0)),),
            (),
            RegimeDefinitionMode.DEVELOPMENT_FIT,
        )
    with pytest.raises(ValueError, match="only valid for DEVELOPMENT_FIT"):
        ScenarioDispositionPolicy(
            "scope",
            (MetricCondition("x", MetricDirection.MAXIMIZE, Decimal(0)),),
            (),
            RegimeDefinitionMode.PREDECLARED,
            development_boundary_id="bad",
        )
    dev_policy = make_policy(
        mode=RegimeDefinitionMode.DEVELOPMENT_FIT,
        development_boundary_id="dev-1",
    )
    assert dev_policy.development_boundary_id == "dev-1"

    policy = make_policy()
    assert evaluate_disposition(
        policy, {"pnl": Decimal("5"), "dd": Decimal("10")}, invalidity_labels=("LEAKAGE",)
    ).disposition is ScenarioDisposition.INVALID

    missing = evaluate_disposition(policy, {"pnl": Decimal("5")})
    assert missing.disposition is ScenarioDisposition.INCONCLUSIVE
    assert missing.missing_required_metrics == ("dd",)

    favorable = evaluate_disposition(policy, {"pnl": Decimal("5"), "dd": Decimal("10")})
    assert favorable.disposition is ScenarioDisposition.FAVORABLE
    unfavorable = evaluate_disposition(policy, {"pnl": Decimal("-1"), "dd": Decimal("30")})
    assert unfavorable.disposition is ScenarioDisposition.UNFAVORABLE
    conditional = evaluate_disposition(policy, {"pnl": Decimal("5"), "dd": Decimal("30")})
    assert conditional.disposition is ScenarioDisposition.CONDITIONAL
    assert conditional.failed_metrics == ("dd",)

    optional_policy = ScenarioDispositionPolicy(
        "scope",
        (
            MetricCondition("pnl", MetricDirection.MAXIMIZE, Decimal("0")),
            MetricCondition("optional", MetricDirection.MAXIMIZE, Decimal("0"), required=False),
        ),
        (),
        RegimeDefinitionMode.PREDECLARED,
    )
    assert evaluate_disposition(
        optional_policy, {"pnl": Decimal("1")}
    ).disposition is ScenarioDisposition.FAVORABLE

    all_optional_policy = ScenarioDispositionPolicy(
        "scope",
        (MetricCondition("optional", MetricDirection.MAXIMIZE, Decimal("0"), required=False),),
        (),
        RegimeDefinitionMode.PREDECLARED,
    )
    assert evaluate_disposition(
        all_optional_policy, {}
    ).disposition is ScenarioDisposition.INCONCLUSIVE

    with pytest.raises(ValueError, match="cannot be empty"):
        characterize_robustness(policy, ())
    assert characterize_robustness(
        policy,
        (
            {"pnl": Decimal("1"), "dd": Decimal("1")},
            {"pnl": Decimal("2"), "dd": Decimal("2")},
        ),
    ) is RobustnessCharacterization.ROBUST_WITHIN_DECLARED_SCOPE
    assert characterize_robustness(
        policy,
        (
            {"pnl": Decimal("-1"), "dd": Decimal("30")},
            {"pnl": Decimal("-2"), "dd": Decimal("40")},
        ),
    ) is RobustnessCharacterization.FRAGILE
    assert characterize_robustness(
        policy,
        (
            {"pnl": Decimal("1"), "dd": Decimal("1")},
            {"pnl": Decimal("-1"), "dd": Decimal("30")},
        ),
    ) is RobustnessCharacterization.MIXED

    assert characterize_robustness(
        policy,
        (
            {"pnl": Decimal("1")},
            {"pnl": Decimal("2")},
        ),
    ) is RobustnessCharacterization.MIXED

    history = ScenarioResearchHistory()
    history.record_artifact(
        ResearchArtifactRecord("a" * 64, ResearchArtifactKind.REGIME_DEFINITION, True)
    )
    nonprotected = ResearchAttemptRecord(
        "a" * 64, EvaluationRole.DEVELOPMENT, None, "FAVORABLE"
    )
    history.record_attempt(nonprotected)
    history.check_admissibility(
        artifact_digest="b" * 64,
        evaluation_role=EvaluationRole.DEVELOPMENT,
        protected_boundary_id=None,
    )
    with pytest.raises(ValueError, match="requires protected_boundary_id"):
        ResearchAttemptRecord(
            "bad", EvaluationRole.PROTECTED_TEST, None, "INCONCLUSIVE"
        )
    with pytest.raises(ValueError, match="only valid for PROTECTED_TEST"):
        ResearchAttemptRecord(
            "bad", EvaluationRole.DEVELOPMENT, "pb", "INCONCLUSIVE"
        )
    with pytest.raises(ValueError, match="prior protected"):
        history.record_protected_adaptation(
            ProtectedAdaptationRecord("pb", "source", "derived")
        )
    with pytest.raises(ValueError, match="registered artifact"):
        history.record_attempt(
            ResearchAttemptRecord("missing", EvaluationRole.DEVELOPMENT, None, "INCONCLUSIVE")
        )

    history.record_artifact(
        ResearchArtifactRecord("source", ResearchArtifactKind.SCENARIO_SPEC, True)
    )
    predecl_history = ScenarioResearchHistory()
    predecl_spec = ScenarioSpec(
        scenario_id="predeclared",
        baseline_evidence_ref="b" * 64,
        shocks=(ScenarioShock(
            ShockTarget.FEE_MULTIPLIER, Decimal("1.5"), "multiplier"
        ),),
        structural_constraints=(),
        predeclared=True,
        research_history_ref=predecl_history.history_digest,
        code_revision="c" * 40,
    )
    predecl_history.record_scenario_spec(predecl_spec)
    predecl_grid = ScenarioGrid("predecl-grid", (predecl_spec,), True)
    predecl_history.record_scenario_grid(predecl_grid)
    assert predecl_history.history_digest
    with pytest.raises(ValueError, match="history digest"):
        ScenarioResearchHistory().record_scenario_spec(
            replace(predecl_spec, research_history_ref="wrong")
        )
    with pytest.raises(ValueError, match="registered first"):
        ScenarioResearchHistory().record_scenario_grid(predecl_grid)
    with pytest.raises(ValueError, match="requires predeclared"):
        ScenarioResearchHistory().record_scenario_spec(
            replace(predecl_spec, predeclared=False)
        )
    with pytest.raises(ValueError, match="previously registered"):
        history.record_artifact(
            ResearchArtifactRecord(
                "bad-child",
                ResearchArtifactKind.SCENARIO_SPEC,
                True,
                parent_digests=("missing",),
            )
        )
    history.record_artifact(
        ResearchArtifactRecord(
            "derived",
            ResearchArtifactKind.SCENARIO_SPEC,
            True,
            parent_digests=("source",),
            protected_informed=True,
        )
    )
    history.record_artifact(
        ResearchArtifactRecord(
            "descendant",
            ResearchArtifactKind.SCENARIO_GRID,
            True,
            parent_digests=("derived",),
            protected_informed=True,
        )
    )
    with pytest.raises(ValueError, match="already registered"):
        history.record_artifact(
            ResearchArtifactRecord(
                "derived",
                ResearchArtifactKind.SCENARIO_SPEC,
                True,
            )
        )

    protected = ResearchAttemptRecord(
        "source", EvaluationRole.PROTECTED_TEST, "pb", "UNFAVORABLE"
    )
    history.record_attempt(protected)
    history.record_protected_adaptation(
        ProtectedAdaptationRecord("pb", "source", "derived")
    )
    assert len(history.attempts) == 2
    assert len(history.adaptations) == 1

    history_unmarked = ScenarioResearchHistory()
    history_unmarked.record_artifact(
        ResearchArtifactRecord("source", ResearchArtifactKind.SCENARIO_SPEC, True)
    )
    history_unmarked.record_artifact(
        ResearchArtifactRecord(
            "derived",
            ResearchArtifactKind.SCENARIO_SPEC,
            True,
            parent_digests=("source",),
        )
    )
    history_unmarked.record_attempt(
        ResearchAttemptRecord(
            "source", EvaluationRole.PROTECTED_TEST, "pb", "UNFAVORABLE"
        )
    )
    history_missing_derived = ScenarioResearchHistory()
    history_missing_derived.record_artifact(
        ResearchArtifactRecord("source", ResearchArtifactKind.SCENARIO_SPEC, True)
    )
    history_missing_derived.record_attempt(
        ResearchAttemptRecord(
            "source", EvaluationRole.PROTECTED_TEST, "pb", "UNFAVORABLE"
        )
    )
    with pytest.raises(ValueError, match="derived artifact must be registered"):
        history_missing_derived.record_protected_adaptation(
            ProtectedAdaptationRecord("pb", "source", "not-registered")
        )
    with pytest.raises(ValueError, match="marked protected_informed"):
        history_unmarked.record_protected_adaptation(
            ProtectedAdaptationRecord("pb", "source", "derived")
        )

    with pytest.raises(ValueError, match="requires protected_boundary_id"):
        history.check_admissibility(
            artifact_digest="other",
            evaluation_role=EvaluationRole.PROTECTED_TEST,
            protected_boundary_id=None,
        )
    with pytest.raises(ProtectedEvidenceReuseError, match="protected-informed"):
        history.check_admissibility(
            artifact_digest="derived",
            evaluation_role=EvaluationRole.PROTECTED_TEST,
            protected_boundary_id="pb",
        )
    with pytest.raises(ProtectedEvidenceReuseError, match="protected-informed"):
        history.check_admissibility(
            artifact_digest="descendant",
            evaluation_role=EvaluationRole.PROTECTED_TEST,
            protected_boundary_id="pb",
        )
    history.check_admissibility(
        artifact_digest="fresh",
        evaluation_role=EvaluationRole.PROTECTED_TEST,
        protected_boundary_id="pb",
    )

    with pytest.raises(ValueError, match="artifact_digest"):
        ResearchAttemptRecord("", EvaluationRole.DEVELOPMENT, None, "F")
    with pytest.raises(ValueError, match="protected_boundary_id"):
        ProtectedAdaptationRecord("", "a", "b")

    manifest = ScenarioRunManifest(
        boundary_digest="a",
        regime_definition_digests=("b",),
        scenario_grid_digest="c",
        observed_series_digest="d",
        disposition_policy_digest="e",
        research_history_digest="h",
        result_digest="f",
        code_revision="1" * 40,
    )
    assert len(manifest.manifest_digest) == 64
    with pytest.raises(ValueError, match="boundary_digest"):
        ScenarioRunManifest("", (), None, None, None, "h", "f", "c")
    with pytest.raises(ValueError, match="research_history_digest"):
        ScenarioRunManifest("a", (), None, None, None, "", "f", "c")


def test_regime_conditioned_summary_parity_and_experimental_parity() -> None:
    definition = make_definition()
    assignments = (
        classify_regime(
            definition,
            make_observation("a", Decimal("5")),
            use_mode=RegimeUseMode.CAUSAL_STRATIFICATION,
        as_of_time=dt(),
        ),
        classify_regime(
            definition,
            make_observation("b", Decimal("15")),
            use_mode=RegimeUseMode.CAUSAL_STRATIFICATION,
        as_of_time=dt(),
        ),
        classify_regime(
            definition,
            make_observation("c", Decimal("20")),
            use_mode=RegimeUseMode.CAUSAL_STRATIFICATION,
        as_of_time=dt(),
        ),
    )
    summary = summarize_metric_by_regime(
        assignments,
        {"a": Decimal("-1"), "b": Decimal("2"), "c": Decimal("4")},
    )
    assert summary["LOW"].count == 1
    assert summary["HIGH"].mean == Decimal("3")

    with pytest.raises(ValueError, match="cannot be empty"):
        summarize_metric_by_regime((), {})
    with pytest.raises(ParityViolationError, match="exactly match"):
        summarize_metric_by_regime(assignments, {"a": Decimal("1")})
    duplicated = (assignments[0], assignments[0])
    with pytest.raises(ValueError, match="unique observation_id"):
        summarize_metric_by_regime(duplicated, {"a": Decimal("1")})
    mixed = (
        assignments[0],
        RegimeAssignment(
            observation_id="b",
            definition_digest="different",
            label="HIGH",
            use_mode=RegimeUseMode.CAUSAL_STRATIFICATION,
            knowledge_time=dt(),
        as_of_time=dt(),
        ),
    )
    with pytest.raises(ParityViolationError, match="cannot mix"):
        summarize_metric_by_regime(mixed, {"a": Decimal("1"), "b": Decimal("2")})

    mixed_mode = (
        assignments[0],
        RegimeAssignment(
            observation_id="b",
            definition_digest=definition.definition_digest,
            label="HIGH",
            use_mode=RegimeUseMode.STRATEGY_BOUND,
            knowledge_time=dt(),
        as_of_time=dt(),
        ),
    )
    with pytest.raises(ParityViolationError, match="cannot mix"):
        summarize_metric_by_regime(mixed_mode, {"a": Decimal("1"), "b": Decimal("2")})

    parity_series = ObservedSeries(
        "parity-series",
        "trades",
        "trade",
        "BRL",
        (Decimal("1"),),
        ("p1",),
        "source",
        "REJECT",
    )
    boundary = ScenarioInputBoundary.from_observed_series(
        parity_series,
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        protected_boundary_id=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        source_code_revision="c" * 40,
        scenario_code_revision="d" * 40,
    )
    same = ScenarioInputBoundary.from_observed_series(
        parity_series,
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        protected_boundary_id=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        source_code_revision="c" * 40,
        scenario_code_revision="f" * 40,
    )
    with pytest.raises(ParityViolationError, match="parity violation"):
        verify_experimental_parity((boundary, same))
    same_revision = ScenarioInputBoundary.from_observed_series(
        parity_series,
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        protected_boundary_id=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        source_code_revision="c" * 40,
        scenario_code_revision="d" * 40,
    )
    assert len(verify_experimental_parity((boundary, same_revision))) == 64
    with pytest.raises(ValueError, match="cannot be empty"):
        verify_experimental_parity(())
    unverified = ScenarioInputBoundary(
        source_kind=boundary.source_kind,
        source_artifact_id=boundary.source_artifact_id,
        source_digest=boundary.source_digest,
        source_lineage_digest=boundary.source_lineage_digest,
        evaluation_role=boundary.evaluation_role,
        protected_boundary_id=boundary.protected_boundary_id,
        role_provenance=boundary.role_provenance,
        numeric_policy_digest=boundary.numeric_policy_digest,
        source_code_revision=boundary.source_code_revision,
        scenario_code_revision=boundary.scenario_code_revision,
        ordered_input_digest=boundary.ordered_input_digest,
        boundary_digest=boundary.boundary_digest,
    )
    with pytest.raises(ValueError, match="verified"):
        verify_experimental_parity((unverified,))
    with pytest.raises(ValueError, match="verified"):
        verify_experimental_parity((boundary, unverified))
    different_series = ObservedSeries(
        "parity-series-different",
        "trades",
        "trade",
        "BRL",
        (Decimal("2"),),
        ("p1",),
        "source",
        "REJECT",
    )
    different = ScenarioInputBoundary.from_observed_series(
        different_series,
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        protected_boundary_id=None,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        source_code_revision="c" * 40,
        scenario_code_revision="d" * 40,
    )
    with pytest.raises(ParityViolationError, match="parity violation"):
        verify_experimental_parity((boundary, different))


def test_typed_research_history_upstream_evaluation_history_and_determinism() -> None:
    history = ScenarioResearchHistory()
    artifact = ResearchArtifactRecord(
        artifact_digest="artifact-1",
        kind=ResearchArtifactKind.REGIME_DEFINITION,
        predeclared=True,
    )
    history.record_artifact(artifact)
    assert history.artifacts == (artifact,)
    with pytest.raises(ValueError, match="already registered"):
        history.record_artifact(artifact)
    with pytest.raises(ValueError, match="parent_digests"):
        ResearchArtifactRecord(
            artifact_digest="x",
            kind=ResearchArtifactKind.SCENARIO_SPEC,
            predeclared=True,
            parent_digests=("",),
        )

    upstream = EvaluationHistory()
    upstream.record_evaluation(
        candidate_id="candidate",
        protected_boundary_id="pb",
        role=EvaluationRole.PROTECTED_TEST,
    )
    upstream.record_protected_evidence_consumption(
        protected_boundary_id="pb",
        source_candidate_id="candidate",
        derived_candidate_id="derived-candidate",
    )
    with pytest.raises(ValueError, match="candidate_id is required"):
        history.check_admissibility(
            artifact_digest="fresh",
            evaluation_role=EvaluationRole.PROTECTED_TEST,
            protected_boundary_id="pb",
            evaluation_history=upstream,
        )
    with pytest.raises(ProtectedEvidenceReuseError, match="Protected evidence reuse"):
        history.check_admissibility(
            artifact_digest="fresh",
            evaluation_role=EvaluationRole.PROTECTED_TEST,
            protected_boundary_id="pb",
            evaluation_history=upstream,
            candidate_id="derived-candidate",
        )

    first = ScenarioRunManifest(
        boundary_digest="a",
        regime_definition_digests=("b",),
        scenario_grid_digest="c",
        observed_series_digest="d",
        disposition_policy_digest="e",
        research_history_digest="h",
        result_digest="f",
        code_revision="1" * 40,
    )
    second = ScenarioRunManifest(
        boundary_digest="a",
        regime_definition_digests=("b",),
        scenario_grid_digest="c",
        observed_series_digest="d",
        disposition_policy_digest="e",
        research_history_digest="h",
        result_digest="f",
        code_revision="1" * 40,
    )
    assert verify_deterministic_equivalence(first, second) == first.manifest_digest
    third = ScenarioRunManifest(
        boundary_digest="a",
        regime_definition_digests=("b",),
        scenario_grid_digest="c",
        observed_series_digest="d",
        disposition_policy_digest="e",
        research_history_digest="h",
        result_digest="different",
        code_revision="1" * 40,
    )
    with pytest.raises(ValueError, match="equivalence violation"):
        verify_deterministic_equivalence(first, third)


def test_extreme_tail_is_preserved_and_synthetic_outcome_is_not_empirical() -> None:
    series = ObservedSeries(
        "extreme",
        "trades",
        "trade",
        "BRL",
        (Decimal("-100"), Decimal("-5"), Decimal("1"), Decimal("2")),
        ("1", "2", "3", "4"),
        "a",
        "REJECT",
    )
    policy = TailMetricPolicy(
        Decimal("0.5"),
        LossDirection.LOWER_IS_LOSS,
        QuantileConvention.NEAREST_RANK,
        4,
        2,
    )
    result = compute_tail_metrics(series, policy)
    assert result.expected_shortfall == Decimal("-52.5")

    outcome_set = ScenarioOutcomeSet(
        "grid",
        (ScenarioOutcome("s", {"pnl": Decimal("-100")}, "manifest"),),
    )
    with pytest.raises(TypeError, match="ObservedSeries"):
        compute_tail_metrics(outcome_set, policy)  # type: ignore[arg-type]
