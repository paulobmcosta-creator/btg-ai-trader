"""Comprehensive Sprint 6 Scenario Engine core tests."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from btg_ai_trader.scenario_engine import (
    ComparisonOperator,
    LossDirection,
    MetricCondition,
    MetricDirection,
    ModelEvidenceSnapshot,
    ObservedSeries,
    ProtectedAdaptationRecord,
    QuantileConvention,
    RegimeDefinition,
    RegimeDefinitionMode,
    RegimeObservation,
    RegimeUseMode,
    ResearchAttemptRecord,
    RobustnessCharacterization,
    RoleProvenance,
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
    summarize_observed_series,
    summarize_scenario_outcomes,
)
from btg_ai_trader.statistical_baselines.domain import (
    EvaluationRole,
    ProtectedEvidenceReuseError,
)
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY


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
        source_lineage_digest="b" * 64,
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


def test_input_boundary_and_model_snapshot_validation() -> None:
    boundary = ScenarioInputBoundary.create(
        source_kind=SourceKind.BACKTEST,
        source_artifact_id="run-1",
        source_digest="a" * 64,
        source_lineage_digest="b" * 64,
        evaluation_role=EvaluationRole.DEVELOPMENT,
        protected_boundary_id=None,
        role_provenance=RoleProvenance.EXPERIMENT_ASSIGNED,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        source_code_revision="c" * 40,
        scenario_code_revision="d" * 40,
        ordered_input_digest="e" * 64,
    )
    assert boundary.is_verified
    assert len(boundary.boundary_digest) == 64
    assert boundary.numeric_policy_digest

    protected = ScenarioInputBoundary.create(
        source_kind=SourceKind.STATISTICAL_EVALUATION,
        source_artifact_id="eval-1",
        source_digest="f" * 64,
        source_lineage_digest="1" * 64,
        evaluation_role=EvaluationRole.PROTECTED_TEST,
        protected_boundary_id="protected-1",
        role_provenance=RoleProvenance.INHERITED,
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        source_code_revision="2" * 40,
        scenario_code_revision="3" * 40,
        ordered_input_digest="4" * 64,
    )
    assert protected.protected_boundary_id == "protected-1"

    with pytest.raises(ValueError, match="source_artifact_id"):
        ScenarioInputBoundary.create(
            source_kind=SourceKind.BACKTEST,
            source_artifact_id="",
            source_digest="a",
            source_lineage_digest="b",
            evaluation_role=EvaluationRole.DEVELOPMENT,
            protected_boundary_id=None,
            role_provenance=RoleProvenance.EXPERIMENT_ASSIGNED,
            numeric_policy=DEFAULT_NUMERIC_POLICY,
            source_code_revision="c",
            scenario_code_revision="d",
            ordered_input_digest="e",
        )

    with pytest.raises(ValueError, match="PROTECTED_TEST requires"):
        ScenarioInputBoundary.create(
            source_kind=SourceKind.BACKTEST,
            source_artifact_id="x",
            source_digest="a",
            source_lineage_digest="b",
            evaluation_role=EvaluationRole.PROTECTED_TEST,
            protected_boundary_id=None,
            role_provenance=RoleProvenance.EXPERIMENT_ASSIGNED,
            numeric_policy=DEFAULT_NUMERIC_POLICY,
            source_code_revision="c",
            scenario_code_revision="d",
            ordered_input_digest="e",
        )

    with pytest.raises(ValueError, match="only valid for PROTECTED_TEST"):
        ScenarioInputBoundary.create(
            source_kind=SourceKind.BACKTEST,
            source_artifact_id="x",
            source_digest="a",
            source_lineage_digest="b",
            evaluation_role=EvaluationRole.DEVELOPMENT,
            protected_boundary_id="bad",
            role_provenance=RoleProvenance.EXPERIMENT_ASSIGNED,
            numeric_policy=DEFAULT_NUMERIC_POLICY,
            source_code_revision="c",
            scenario_code_revision="d",
            ordered_input_digest="e",
        )

    snapshot = ModelEvidenceSnapshot.create(
        candidate_id="candidate-1",
        evaluation_role=EvaluationRole.VALIDATION_SELECTION,
        dataset_digest="a" * 64,
        plan_digest="b" * 64,
        target_contract_digest="c" * 64,
        experimental_context_fingerprint="d" * 64,
        metrics={"mae": Decimal("1.5")},
        disposition="FAVORABLE",
        source_manifest_ids=("manifest-1",),
        source_code_revision="e" * 40,
    )
    assert snapshot.is_verified
    assert snapshot.evaluation_scope == "MODEL"
    assert snapshot.metrics["mae"] == Decimal("1.5")

    with pytest.raises(ValueError, match="candidate_id"):
        ModelEvidenceSnapshot.create(
            candidate_id="",
            evaluation_role=EvaluationRole.DEVELOPMENT,
            dataset_digest="a",
            plan_digest="b",
            target_contract_digest="c",
            experimental_context_fingerprint="d",
            metrics={},
            disposition="FAVORABLE",
            source_manifest_ids=("m",),
            source_code_revision="e",
        )
    with pytest.raises(ValueError, match="source_manifest_ids"):
        ModelEvidenceSnapshot.create(
            candidate_id="c",
            evaluation_role=EvaluationRole.DEVELOPMENT,
            dataset_digest="a",
            plan_digest="b",
            target_contract_digest="c",
            experimental_context_fingerprint="d",
            metrics={},
            disposition="FAVORABLE",
            source_manifest_ids=(),
            source_code_revision="e",
        )


def test_regime_contracts_classification_and_development_fit() -> None:
    obs = make_observation(event_time=dt())
    assert obs.variables["vol"] == Decimal("10")

    with pytest.raises(ValueError, match="timezone-aware"):
        RegimeObservation("x", datetime(2026, 1, 1), {"vol": Decimal(1)}, "a")
    with pytest.raises(ValueError, match="timezone-aware"):
        RegimeObservation("x", dt(), {"vol": Decimal(1)}, "a", datetime(2026, 1, 1))
    with pytest.raises(TypeError, match="threshold"):
        ThresholdRule("vol", ComparisonOperator.LT, 1, "LOW")  # type: ignore[arg-type]

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
            source_lineage_digest="a",
        )
        assert classify_regime(
            definition,
            make_observation(value=value),
            use_mode=RegimeUseMode.CAUSAL_STRATIFICATION,
        ).label == expected

    assert classify_regime(
        RegimeDefinition(
            "d-default",
            RegimeDefinitionMode.PREDECLARED,
            (ThresholdRule("vol", ComparisonOperator.GT, Decimal("20"), "YES"),),
            "NO",
            "a",
        ),
        make_observation(value=Decimal("10")),
        use_mode=RegimeUseMode.CAUSAL_STRATIFICATION,
    ).label == "NO"

    missing = RegimeObservation("m", dt(), {}, "a")
    assert classify_regime(
        make_definition(), missing, use_mode=RegimeUseMode.CAUSAL_STRATIFICATION
    ).label == "UNKNOWN"

    definition = make_definition()
    with pytest.raises(ValueError, match="STRATEGY_BOUND"):
        classify_regime(definition, obs, use_mode=RegimeUseMode.STRATEGY_BOUND)
    bound = classify_regime(
        definition,
        obs,
        use_mode=RegimeUseMode.STRATEGY_BOUND,
        strategy_regime_definition_digest=definition.definition_digest,
    )
    assert bound.label == "HIGH"
    assert bound.knowledge_time == dt()

    retro = RegimeDefinition(
        "retro",
        RegimeDefinitionMode.RETROSPECTIVE_EXPLORATORY,
        (ThresholdRule("vol", ComparisonOperator.GE, Decimal("0"), "RETRO"),),
        "UNKNOWN",
        "a",
    )
    with pytest.raises(ValueError, match="exploratory-only"):
        classify_regime(retro, obs, use_mode=RegimeUseMode.CAUSAL_STRATIFICATION)
    assert classify_regime(
        retro, obs, use_mode=RegimeUseMode.RETROSPECTIVE_EXPLORATORY
    ).label == "RETRO"

    with pytest.raises(ValueError, match="rules cannot be empty"):
        RegimeDefinition("x", RegimeDefinitionMode.PREDECLARED, (), "U", "a")
    with pytest.raises(ValueError, match="requires development_boundary_id"):
        RegimeDefinition(
            "x",
            RegimeDefinitionMode.DEVELOPMENT_FIT,
            (ThresholdRule("vol", ComparisonOperator.GE, Decimal(1), "H"),),
            "U",
            "a",
        )
    with pytest.raises(ValueError, match="only valid for DEVELOPMENT_FIT"):
        RegimeDefinition(
            "x",
            RegimeDefinitionMode.PREDECLARED,
            (ThresholdRule("vol", ComparisonOperator.GE, Decimal(1), "H"),),
            "U",
            "a",
            development_boundary_id="bad",
        )

    odd = fit_development_threshold_definition(
        [make_observation("1", Decimal(1)), make_observation("2", Decimal(3)), make_observation("3", Decimal(2))],
        variable_name="vol",
        label_below="LOW",
        label_at_or_above="HIGH",
        definition_id="fit-odd",
        development_boundary_id="dev-1",
        source_lineage_digest="a",
        evaluation_role=EvaluationRole.DEVELOPMENT,
    )
    assert odd.rules[0].threshold == Decimal(2)

    even = fit_development_threshold_definition(
        [make_observation("1", Decimal(1)), make_observation("2", Decimal(3))],
        variable_name="vol",
        label_below="LOW",
        label_at_or_above="HIGH",
        definition_id="fit-even",
        development_boundary_id="dev-1",
        source_lineage_digest="a",
        evaluation_role=EvaluationRole.DEVELOPMENT,
    )
    assert even.rules[0].threshold == Decimal(2)

    with pytest.raises(ValueError, match="only on DEVELOPMENT"):
        fit_development_threshold_definition(
            [obs],
            variable_name="vol",
            label_below="L",
            label_at_or_above="H",
            definition_id="bad",
            development_boundary_id="dev",
            source_lineage_digest="a",
            evaluation_role=EvaluationRole.PROTECTED_TEST,
        )
    with pytest.raises(ValueError, match="cannot be empty"):
        fit_development_threshold_definition(
            [],
            variable_name="vol",
            label_below="L",
            label_at_or_above="H",
            definition_id="bad",
            development_boundary_id="dev",
            source_lineage_digest="a",
            evaluation_role=EvaluationRole.DEVELOPMENT,
        )
    with pytest.raises(ValueError, match="cannot silently drop"):
        fit_development_threshold_definition(
            [RegimeObservation("x", dt(), {}, "a")],
            variable_name="vol",
            label_below="L",
            label_at_or_above="H",
            definition_id="bad",
            development_boundary_id="dev",
            source_lineage_digest="a",
            evaluation_role=EvaluationRole.DEVELOPMENT,
        )


def test_scenario_grid_outcome_contracts_and_summary() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("-1"), "multiplier")
    with pytest.raises(ValueError, match="unit"):
        ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("1"), "")

    with pytest.raises(ValueError, match="at least one shock"):
        ScenarioSpec("x", "a", (), (), True, "h", "c")
    duplicate = (
        ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("1"), "x"),
        ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("2"), "x"),
    )
    with pytest.raises(ValueError, match="duplicate shock"):
        make_scenario(shocks=duplicate, constraints=("same-axis",))
    multi = (
        ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("1"), "x"),
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
    assert summary["dd"].mean == Decimal("5")


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
    odd_summary = summarize_observed_series(odd)
    assert odd_summary.median == Decimal("2")
    assert odd_summary.empirical_probability_of_loss == Decimal(1) / Decimal(3)

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
    assert summarize_observed_series(even).median == Decimal("2")

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

    history = ScenarioResearchHistory()
    nonprotected = ResearchAttemptRecord(
        "a" * 64, EvaluationRole.DEVELOPMENT, None, "FAVORABLE"
    )
    history.record_attempt(nonprotected)
    history.check_admissibility(
        artifact_digest="b" * 64,
        evaluation_role=EvaluationRole.DEVELOPMENT,
        protected_boundary_id=None,
    )
    with pytest.raises(ValueError, match="prior protected"):
        history.record_protected_adaptation(
            ProtectedAdaptationRecord("pb", "source", "derived")
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
        result_digest="f",
        code_revision="1" * 40,
    )
    assert len(manifest.manifest_digest) == 64
    with pytest.raises(ValueError, match="boundary_digest"):
        ScenarioRunManifest("", (), None, None, None, "f", "c")
