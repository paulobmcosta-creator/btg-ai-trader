"""Evaluation and authorization tests for Sprint 7 Risk Engine."""

# ruff: noqa: I001

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from btg_ai_trader.observer.identity import TradableInstrumentId
from btg_ai_trader.risk_engine import (
    AuthorizationInvalidity,
    CommitmentReadiness,
    DailyLossPolicySemantics,
    DailyLossState,
    DrawdownDenominatorConvention,
    DrawdownPolicySemantics,
    DrawdownSeriesKind,
    DrawdownState,
    EconomicDirection,
    EvidenceQuality,
    ExposureState,
    LimitOperator,
    PnlLossConvention,
    RiskAuthorization,
    RiskDecision,
    RiskDecisionRecord,
    RiskEvaluationBoundary,
    RiskLimitRule,
    RiskMetric,
    RiskPolicyBundle,
    RiskProposal,
    RiskStateSnapshot,
    SafetyPosture,
    TailEvidenceSourceKind,
    TailLossDirection,
    TailQuantileConvention,
    TailRiskEvidence,
    TailRiskPolicySemantics,
    core as rc,
    evaluate_risk,
    initial_circuit_state,
    latch_circuit,
    validate_authorization,
    verify_deterministic_equivalence,
)
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY


INSTRUMENT = TradableInstrumentId("11111111-1111-1111-1111-111111111111")
OTHER_INSTRUMENT = TradableInstrumentId("22222222-2222-2222-2222-222222222222")


def dt(seconds: int = 0) -> datetime:
    return datetime(2026, 9, 26, 12, 0, tzinfo=UTC) + timedelta(seconds=seconds)


T0 = dt(0)
T5 = dt(5)
T10 = dt(10)


def rule(
    rule_id: str,
    metric: RiskMetric,
    threshold: str,
    unit: str,
    *,
    operator: LimitOperator = LimitOperator.LTE,
    hard: bool = True,
) -> RiskLimitRule:
    return RiskLimitRule(
        rule_id=rule_id,
        metric=metric,
        operator=operator,
        threshold=Decimal(threshold),
        unit=unit,
        hard=hard,
    )


def daily_semantics() -> DailyLossPolicySemantics:
    return DailyLossPolicySemantics(
        currency="BRL",
        pnl_source_id="portfolio-pnl",
        include_unrealized=False,
        loss_sign_convention=PnlLossConvention.NEGATIVE_PNL_IS_LOSS,
        session_calendar_id="B3",
        timezone_name="America/Sao_Paulo",
        reset_semantics="SESSION_BOUNDARY",
    )


def drawdown_semantics(
    denominator_convention: DrawdownDenominatorConvention | None = (
        DrawdownDenominatorConvention.EXPLICIT_POSITIVE_CAPITAL
    ),
) -> DrawdownPolicySemantics:
    return DrawdownPolicySemantics(
        source_id="portfolio-equity",
        series_kind=DrawdownSeriesKind.EQUITY,
        denominator_convention=denominator_convention,
    )


def tail_semantics() -> TailRiskPolicySemantics:
    return TailRiskPolicySemantics(
        tail_fraction=Decimal("0.05"),
        loss_direction=TailLossDirection.LOWER_IS_LOSS,
        quantile_convention=TailQuantileConvention.NEAREST_RANK,
        missing_policy="REJECT",
        source_policy_digest="tail-policy",
    )


def policy(
    *,
    extra_rules: tuple[RiskLimitRule, ...] = (),
    capacity_threshold: str = "1000",
    portfolio_id: str = "portfolio-1",
    instrument_id: TradableInstrumentId | None = INSTRUMENT,
    effective_from: datetime = T0,
    effective_until: datetime | None = None,
    postures: tuple[SafetyPosture, ...] = (SafetyPosture.NORMAL,),
    ttl: int = 30,
) -> RiskPolicyBundle:
    all_rules = (
        rule(
            "01-capacity",
            RiskMetric.PROJECTED_CAPACITY_USAGE,
            capacity_threshold,
            "BRL",
        ),
        *extra_rules,
    )
    return RiskPolicyBundle(
        policy_id="risk-policy",
        version="1",
        portfolio_id=portfolio_id,
        instrument_id=instrument_id,
        effective_from=effective_from,
        effective_until=effective_until,
        rules=tuple(sorted(all_rules, key=lambda item: item.rule_id)),
        allowed_safety_postures=postures,
        authorization_ttl_seconds=ttl,
        daily_loss_semantics=daily_semantics(),
        drawdown_semantics=drawdown_semantics(),
        tail_semantics=tail_semantics(),
        numeric_policy=DEFAULT_NUMERIC_POLICY,
    )


def proposal(
    *,
    exposure: str = "200",
    exposure_unit: str = "BRL",
    quantity: str = "10",
    portfolio_id: str = "portfolio-1",
    instrument_id: TradableInstrumentId = INSTRUMENT,
    created_at: datetime = T5,
    source_digest: str = "proposal-source",
) -> RiskProposal:
    return RiskProposal(
        proposal_id="proposal-1",
        instrument_id=instrument_id,
        portfolio_id=portfolio_id,
        direction=EconomicDirection.INCREASE_LONG,
        requested_quantity=Decimal(quantity),
        quantity_unit="shares",
        requested_exposure=Decimal(exposure),
        exposure_unit=exposure_unit,
        created_at=created_at,
        source_digest=source_digest,
    )


def make_exposure(
    *,
    quality: EvidenceQuality = EvidenceQuality.VALID,
    unit: str = "BRL",
) -> ExposureState:
    return ExposureState(
        current_position_exposure=Decimal("300"),
        committed_potential_exposure=Decimal("100"),
        risk_capacity_reservation=Decimal("100"),
        worst_case_exposure=Decimal("400"),
        unit=unit,
        source_digest="exposure-source",
        quality=quality,
    )


def make_daily(
    *,
    quality: EvidenceQuality = EvidenceQuality.VALID,
    pnl: str = "-20",
) -> DailyLossState:
    return DailyLossState(
        recognized_pnl=Decimal(pnl),
        currency="BRL",
        pnl_source_id="portfolio-pnl",
        include_unrealized=False,
        loss_sign_convention=PnlLossConvention.NEGATIVE_PNL_IS_LOSS,
        session_id="session",
        session_start=dt(0),
        session_end=dt(100),
        session_calendar_id="B3",
        timezone_name="America/Sao_Paulo",
        reset_semantics="SESSION_BOUNDARY",
        source_digest="daily-source",
        quality=quality,
    )


def make_drawdown(
    *,
    quality: EvidenceQuality = EvidenceQuality.VALID,
    denominator: Decimal | None = Decimal("1000"),
) -> DrawdownState:
    convention = (
        DrawdownDenominatorConvention.EXPLICIT_POSITIVE_CAPITAL
        if denominator is not None
        else None
    )
    return DrawdownState(
        peak_value=Decimal("1000"),
        current_value=Decimal("900"),
        unit="BRL",
        capital_denominator=denominator,
        denominator_convention=convention,
        source_id="portfolio-equity",
        series_kind=DrawdownSeriesKind.EQUITY,
        peak_id="peak-1",
        current_id="current-1",
        source_digest="drawdown-source",
        quality=quality,
    )


def make_tail(
    *,
    quality: EvidenceQuality = EvidenceQuality.VALID,
    kind: TailEvidenceSourceKind = TailEvidenceSourceKind.EMPIRICAL_OBSERVED,
    sufficient: bool = True,
) -> TailRiskEvidence:
    return TailRiskEvidence(
        source_kind=kind,
        value_at_risk=Decimal("50"),
        expected_shortfall=Decimal("60"),
        unit="BRL",
        tail_fraction=Decimal("0.05"),
        loss_direction=TailLossDirection.LOWER_IS_LOSS,
        quantile_convention=TailQuantileConvention.NEAREST_RANK,
        missing_policy="REJECT",
        source_policy_digest="tail-policy",
        total_count=100,
        tail_count=5,
        sufficient=sufficient,
        source_digest="tail-source",
        quality=quality,
    )


def state(
    risk_policy: RiskPolicyBundle,
    *,
    quality: EvidenceQuality = EvidenceQuality.VALID,
    exposure_quality: EvidenceQuality = EvidenceQuality.VALID,
    exposure_unit: str = "BRL",
    readiness: CommitmentReadiness = CommitmentReadiness.READY,
    posture: SafetyPosture = SafetyPosture.NORMAL,
    circuit_policy_digest: str | None = None,
    latched: bool = False,
    include_daily: bool = True,
    daily_quality: EvidenceQuality = EvidenceQuality.VALID,
    pnl: str = "-20",
    include_drawdown: bool = True,
    drawdown_quality: EvidenceQuality = EvidenceQuality.VALID,
    denominator: Decimal | None = Decimal("1000"),
    include_tail: bool = True,
    tail_quality: EvidenceQuality = EvidenceQuality.VALID,
    tail_kind: TailEvidenceSourceKind = TailEvidenceSourceKind.EMPIRICAL_OBSERVED,
    tail_sufficient: bool = True,
    source_lineage_digest: str = "risk-lineage",
) -> RiskStateSnapshot:
    circuit = initial_circuit_state(
        policy_digest=circuit_policy_digest or risk_policy.policy_digest,
        at_time=dt(0),
        evidence_digest="initial",
    )
    if latched:
        circuit = latch_circuit(
            circuit,
            reason="HARD_RISK_BREACH",
            evidence_digest="breach",
            at_time=dt(1),
        )
    return RiskStateSnapshot(
        snapshot_id="state-1",
        portfolio_id="portfolio-1",
        instrument_id=INSTRUMENT,
        as_of_time=dt(10),
        knowledge_time=dt(9),
        exposure=make_exposure(quality=exposure_quality, unit=exposure_unit),
        daily_loss=make_daily(quality=daily_quality, pnl=pnl) if include_daily else None,
        drawdown=(
            make_drawdown(quality=drawdown_quality, denominator=denominator)
            if include_drawdown
            else None
        ),
        tail_risk=(
            make_tail(
                quality=tail_quality,
                kind=tail_kind,
                sufficient=tail_sufficient,
            )
            if include_tail
            else None
        ),
        safety_posture=posture,
        commitment_readiness=readiness,
        circuit=circuit,
        quality=quality,
        source_lineage_digest=source_lineage_digest,
    )


def boundary(
    *,
    risk_policy: RiskPolicyBundle | None = None,
    risk_state: RiskStateSnapshot | None = None,
    risk_proposal: RiskProposal | None = None,
    as_of_time: datetime = T10,
) -> RiskEvaluationBoundary:
    actual_policy = risk_policy or policy()
    actual_state = risk_state or state(actual_policy)
    actual_proposal = risk_proposal or proposal()
    return RiskEvaluationBoundary.build(
        proposal=actual_proposal,
        state=actual_state,
        policy=actual_policy,
        as_of_time=as_of_time,
        engine_revision="s7-test",
    )


def preserve_issuer(auth: RiskAuthorization) -> RiskAuthorization:
    object.__setattr__(auth, "_issuer_token", rc._ENGINE_AUTHORIZATION_TOKEN)
    return auth


def test_happy_path_permits_and_issues_bounded_authorization() -> None:
    rules = (
        rule("02-current", RiskMetric.CURRENT_POSITION_EXPOSURE, "500", "BRL"),
        rule("03-committed", RiskMetric.COMMITTED_POTENTIAL_EXPOSURE, "200", "BRL"),
        rule("04-reserved", RiskMetric.RISK_CAPACITY_RESERVATION, "200", "BRL"),
        rule("05-worst", RiskMetric.WORST_CASE_EXPOSURE, "500", "BRL"),
        rule("06-request", RiskMetric.REQUESTED_EXPOSURE, "250", "BRL"),
        rule("07-daily", RiskMetric.DAILY_LOSS, "100", "BRL"),
        rule("08-dd-amount", RiskMetric.DRAWDOWN_AMOUNT, "150", "BRL"),
        rule("09-dd-ratio", RiskMetric.DRAWDOWN_RATIO, "0.2", "ratio"),
        rule("10-var", RiskMetric.VALUE_AT_RISK, "80", "BRL"),
        rule("11-es", RiskMetric.EXPECTED_SHORTFALL, "90", "BRL"),
    )
    p = policy(extra_rules=rules)
    b = boundary(risk_policy=p)
    first = evaluate_risk(b)
    second = evaluate_risk(b)

    assert first.decision.decision is RiskDecision.PERMIT
    assert first.authorization is not None
    assert first.authorization.is_engine_issued
    assert first.authorization.max_exposure == Decimal("200")
    assert first.authorization.max_quantity == Decimal("10")
    assert first.authorization.quantity_unit == "shares"
    assert first.authorization.exposure_unit == "BRL"
    assert set(first.decision.metrics) == {
        RiskMetric.PROJECTED_CAPACITY_USAGE.value,
        *(item.metric.value for item in rules),
    }
    assert verify_deterministic_equivalence(first, second) == first.result_digest
    assert validate_authorization(
        first.authorization,
        decision=first.decision,
        proposal=b.proposal,
        state=b.state,
        policy=b.policy,
        as_of_time=dt(11),
    ).valid

    changed = dataclasses.replace(
        second,
        decision=dataclasses.replace(second.decision, reasons=("CHANGED",)),
    )
    with pytest.raises(ValueError, match="not deterministically equivalent"):
        verify_deterministic_equivalence(first, changed)


def test_projected_limits_cap_authorization_without_becoming_strategy_sizing() -> None:
    p = policy(capacity_threshold="550")
    result = evaluate_risk(boundary(risk_policy=p))
    assert result.decision.decision is RiskDecision.PERMIT
    assert result.authorization is not None
    assert result.authorization.max_exposure == Decimal("50")
    assert result.authorization.max_quantity == Decimal("2.5")
    assert "AUTHORIZATION_CAPPED:01-capacity" in result.decision.reasons

    worst_policy = RiskPolicyBundle(
        policy_id="worst-case",
        version="1",
        portfolio_id="portfolio-1",
        instrument_id=INSTRUMENT,
        effective_from=dt(0),
        effective_until=None,
        rules=(
            rule(
                "01-worst",
                RiskMetric.PROJECTED_WORST_CASE_EXPOSURE,
                "500",
                "BRL",
            ),
        ),
        allowed_safety_postures=(SafetyPosture.NORMAL,),
        authorization_ttl_seconds=30,
    )
    worst_result = evaluate_risk(boundary(risk_policy=worst_policy))
    assert worst_result.authorization is not None
    assert worst_result.authorization.max_exposure == Decimal("100")

    no_capacity = evaluate_risk(boundary(risk_policy=policy(capacity_threshold="500")))
    assert no_capacity.decision.decision is RiskDecision.REJECT
    assert no_capacity.authorization is None
    assert "HARD_LIMIT_BREACH:01-capacity" in no_capacity.decision.reasons

    with pytest.raises(ValueError, match="not a projected"):
        rc._projected_base(boundary(), RiskMetric.DAILY_LOSS)


@pytest.mark.parametrize(
    ("risk_policy", "risk_state", "expected"),
    [
        (policy(effective_from=dt(11)), None, "POLICY_NOT_EFFECTIVE"),
        (policy(portfolio_id="other"), None, "POLICY_PORTFOLIO_SCOPE_MISMATCH"),
        (
            policy(instrument_id=OTHER_INSTRUMENT),
            None,
            "POLICY_INSTRUMENT_SCOPE_MISMATCH",
        ),
        (
            policy(),
            "STATE_UNKNOWN",
            "STATE_QUALITY_UNKNOWN",
        ),
        (
            policy(),
            "EXPOSURE_STALE",
            "EXPOSURE_QUALITY_STALE",
        ),
        (
            policy(),
            "READINESS_BLOCKED",
            "COMMITMENT_READINESS_BLOCKED",
        ),
        (
            policy(),
            "READINESS_UNKNOWN",
            "COMMITMENT_READINESS_UNKNOWN",
        ),
        (
            policy(),
            "SAFE_HALT",
            "SAFETY_POSTURE_SAFE_HALT",
        ),
        (
            policy(),
            "CIRCUIT_MISMATCH",
            "CIRCUIT_POLICY_MISMATCH",
        ),
        (
            policy(),
            "CIRCUIT_LATCHED",
            "CIRCUIT_LATCHED",
        ),
    ],
)
def test_fail_closed_preconditions(
    risk_policy: RiskPolicyBundle,
    risk_state: RiskStateSnapshot | str | None,
    expected: str,
) -> None:
    if risk_state is None:
        actual_state = state(risk_policy)
    elif risk_state == "STATE_UNKNOWN":
        actual_state = state(risk_policy, quality=EvidenceQuality.UNKNOWN)
    elif risk_state == "EXPOSURE_STALE":
        actual_state = state(risk_policy, exposure_quality=EvidenceQuality.STALE)
    elif risk_state == "READINESS_BLOCKED":
        actual_state = state(risk_policy, readiness=CommitmentReadiness.BLOCKED)
    elif risk_state == "READINESS_UNKNOWN":
        actual_state = state(risk_policy, readiness=CommitmentReadiness.UNKNOWN)
    elif risk_state == "SAFE_HALT":
        actual_state = state(risk_policy, posture=SafetyPosture.SAFE_HALT)
    elif risk_state == "CIRCUIT_MISMATCH":
        actual_state = state(risk_policy, circuit_policy_digest="other-policy")
    elif risk_state == "CIRCUIT_LATCHED":
        actual_state = state(risk_policy, latched=True)
    else:
        raise AssertionError(risk_state)

    result = evaluate_risk(boundary(risk_policy=risk_policy, risk_state=actual_state))
    assert result.decision.decision is RiskDecision.REJECT
    assert result.authorization is None
    assert expected in result.decision.reasons


def test_degraded_posture_can_be_explicitly_allowed() -> None:
    p = policy(postures=(SafetyPosture.DEGRADED, SafetyPosture.NORMAL))
    result = evaluate_risk(
        boundary(risk_policy=p, risk_state=state(p, posture=SafetyPosture.DEGRADED))
    )
    assert result.decision.decision is RiskDecision.PERMIT


@pytest.mark.parametrize(
    ("metric", "state_kwargs", "expected"),
    [
        (RiskMetric.DAILY_LOSS, {"include_daily": False}, "DAILY_LOSS_MISSING"),
        (
            RiskMetric.DAILY_LOSS,
            {"daily_quality": EvidenceQuality.STALE},
            "DAILY_LOSS_QUALITY",
        ),
        (RiskMetric.DRAWDOWN_AMOUNT, {"include_drawdown": False}, "DRAWDOWN_MISSING"),
        (
            RiskMetric.DRAWDOWN_AMOUNT,
            {"drawdown_quality": EvidenceQuality.INCOMPLETE},
            "DRAWDOWN_QUALITY",
        ),
        (
            RiskMetric.DRAWDOWN_RATIO,
            {"denominator": None},
            "DRAWDOWN_DENOMINATOR_MISSING",
        ),
        (RiskMetric.VALUE_AT_RISK, {"include_tail": False}, "TAIL_EVIDENCE_MISSING"),
        (
            RiskMetric.VALUE_AT_RISK,
            {"tail_quality": EvidenceQuality.UNKNOWN},
            "TAIL_EVIDENCE_QUALITY",
        ),
        (
            RiskMetric.VALUE_AT_RISK,
            {"tail_kind": TailEvidenceSourceKind.SYNTHETIC_SCENARIO},
            "SYNTHETIC_TAIL_EVIDENCE_FORBIDDEN",
        ),
        (
            RiskMetric.EXPECTED_SHORTFALL,
            {"tail_sufficient": False},
            "TAIL_EVIDENCE_INSUFFICIENT",
        ),
    ],
)
def test_required_metric_evidence_fails_closed(
    metric: RiskMetric,
    state_kwargs: dict[str, object],
    expected: str,
) -> None:
    unit = "ratio" if metric is RiskMetric.DRAWDOWN_RATIO else "BRL"
    extra = rule("02-required", metric, "1000", unit)
    p = policy(extra_rules=(extra,))
    actual_state = state(p, **state_kwargs)  # type: ignore[arg-type]
    result = evaluate_risk(boundary(risk_policy=p, risk_state=actual_state))
    assert result.decision.decision is RiskDecision.REJECT
    assert f"{expected}:02-required" in result.decision.reasons


def test_policy_semantics_are_bound_to_runtime_evidence() -> None:
    bare = dataclasses.replace(
        policy(),
        daily_loss_semantics=None,
        drawdown_semantics=None,
        tail_semantics=None,
    )
    bare_boundary = boundary(risk_policy=bare, risk_state=state(bare))
    assert rc._metric_value(
        bare_boundary,
        RiskMetric.DAILY_LOSS,
    )[2] == "DAILY_LOSS_POLICY_MISSING"
    assert rc._metric_value(
        bare_boundary,
        RiskMetric.DRAWDOWN_AMOUNT,
    )[2] == "DRAWDOWN_POLICY_MISSING"
    assert rc._metric_value(
        bare_boundary,
        RiskMetric.VALUE_AT_RISK,
    )[2] == "TAIL_POLICY_MISSING"

    daily_rule = rule("02-daily", RiskMetric.DAILY_LOSS, "100", "BRL")
    daily_policy = policy(extra_rules=(daily_rule,))
    daily_state = dataclasses.replace(
        state(daily_policy),
        daily_loss=dataclasses.replace(
            make_daily(),
            pnl_source_id="other-source",
        ),
    )
    daily_result = evaluate_risk(
        boundary(risk_policy=daily_policy, risk_state=daily_state)
    )
    assert daily_result.decision.decision is RiskDecision.REJECT
    assert "DAILY_LOSS_POLICY_MISMATCH:02-daily" in daily_result.decision.reasons

    draw_rule = rule("02-draw", RiskMetric.DRAWDOWN_AMOUNT, "200", "BRL")
    draw_policy = policy(extra_rules=(draw_rule,))
    draw_state = dataclasses.replace(
        state(draw_policy),
        drawdown=dataclasses.replace(
            make_drawdown(),
            source_id="other-equity-source",
        ),
    )
    draw_result = evaluate_risk(
        boundary(risk_policy=draw_policy, risk_state=draw_state)
    )
    assert draw_result.decision.decision is RiskDecision.REJECT
    assert "DRAWDOWN_POLICY_MISMATCH:02-draw" in draw_result.decision.reasons

    ratio_policy = policy(
        extra_rules=(
            rule("02-ratio", RiskMetric.DRAWDOWN_RATIO, "0.2", "ratio"),
        )
    )
    ratio_state = dataclasses.replace(
        state(ratio_policy),
        drawdown=dataclasses.replace(
            make_drawdown(),
            denominator_convention=None,
            capital_denominator=None,
        ),
    )
    ratio_result = evaluate_risk(
        boundary(risk_policy=ratio_policy, risk_state=ratio_state)
    )
    assert "DRAWDOWN_DENOMINATOR_MISSING:02-ratio" in ratio_result.decision.reasons

    tail_rule = rule("02-var", RiskMetric.VALUE_AT_RISK, "100", "BRL")
    tail_policy = policy(extra_rules=(tail_rule,))
    tail_state = dataclasses.replace(
        state(tail_policy),
        tail_risk=dataclasses.replace(
            make_tail(),
            source_policy_digest="other-tail-policy",
        ),
    )
    tail_result = evaluate_risk(
        boundary(risk_policy=tail_policy, risk_state=tail_state)
    )
    assert tail_result.decision.decision is RiskDecision.REJECT
    assert "TAIL_POLICY_MISMATCH:02-var" in tail_result.decision.reasons


def test_advisory_missing_and_breach_do_not_override_permit() -> None:
    advisory_missing = rule(
        "02-daily",
        RiskMetric.DAILY_LOSS,
        "10",
        "BRL",
        hard=False,
    )
    advisory_breach = rule(
        "03-current",
        RiskMetric.CURRENT_POSITION_EXPOSURE,
        "100",
        "BRL",
        hard=False,
    )
    p = policy(extra_rules=(advisory_missing, advisory_breach))
    result = evaluate_risk(
        boundary(
            risk_policy=p,
            risk_state=state(p, include_daily=False),
        )
    )
    assert result.decision.decision is RiskDecision.PERMIT
    assert "ADVISORY_DAILY_LOSS_MISSING:02-daily" in result.decision.reasons
    assert "ADVISORY_LIMIT_BREACH:03-current" in result.decision.reasons


def test_unit_mismatch_is_hard_or_advisory_according_to_policy() -> None:
    hard = policy(
        extra_rules=(
            rule("02-hard", RiskMetric.REQUESTED_EXPOSURE, "500", "USD", hard=True),
        )
    )
    hard_result = evaluate_risk(boundary(risk_policy=hard))
    assert hard_result.decision.decision is RiskDecision.REJECT
    assert "UNIT_MISMATCH:02-hard" in hard_result.decision.reasons

    advisory = policy(
        extra_rules=(
            rule(
                "02-advisory",
                RiskMetric.REQUESTED_EXPOSURE,
                "500",
                "USD",
                hard=False,
            ),
        )
    )
    advisory_result = evaluate_risk(boundary(risk_policy=advisory))
    assert advisory_result.decision.decision is RiskDecision.PERMIT
    assert "ADVISORY_UNIT_MISMATCH:02-advisory" in advisory_result.decision.reasons

    projected_mismatch = policy()
    mismatch_result = evaluate_risk(
        boundary(
            risk_policy=projected_mismatch,
            risk_proposal=proposal(exposure_unit="USD"),
        )
    )
    assert mismatch_result.decision.decision is RiskDecision.REJECT
    assert "EXPOSURE_UNIT_MISMATCH:01-capacity" in mismatch_result.decision.reasons


def test_gte_rule_and_hard_limit_non_compensation() -> None:
    passing = policy(
        extra_rules=(
            rule(
                "02-floor",
                RiskMetric.CURRENT_POSITION_EXPOSURE,
                "200",
                "BRL",
                operator=LimitOperator.GTE,
            ),
        )
    )
    assert evaluate_risk(boundary(risk_policy=passing)).decision.decision is RiskDecision.PERMIT

    failing = policy(
        extra_rules=(
            rule(
                "02-floor",
                RiskMetric.CURRENT_POSITION_EXPOSURE,
                "500",
                "BRL",
                operator=LimitOperator.GTE,
            ),
            rule(
                "03-advisory-good",
                RiskMetric.DAILY_LOSS,
                "1000",
                "BRL",
                hard=False,
            ),
        )
    )
    rejected = evaluate_risk(boundary(risk_policy=failing))
    assert rejected.decision.decision is RiskDecision.REJECT
    assert "HARD_LIMIT_BREACH:02-floor" in rejected.decision.reasons


def test_unverified_boundary_is_rejected() -> None:
    b = boundary()
    forged = RiskEvaluationBoundary(
        proposal=b.proposal,
        state=b.state,
        policy=b.policy,
        as_of_time=b.as_of_time,
        engine_revision=b.engine_revision,
        boundary_digest=b.boundary_digest,
    )
    with pytest.raises(ValueError, match="must be created by build"):
        evaluate_risk(forged)


def test_metric_dispatch_invalid_enum_fails_explicitly() -> None:
    with pytest.raises(AssertionError, match="unsupported risk metric"):
        rc._metric_value(boundary(), "NOT_A_METRIC")  # type: ignore[arg-type]


def test_internal_metric_dispatch_covers_remaining_guard_paths() -> None:
    p = policy()
    stale_exposure_state = state(p, exposure_quality=EvidenceQuality.STALE)
    stale_boundary = boundary(risk_policy=p, risk_state=stale_exposure_state)
    value, unit, missing = rc._metric_value(stale_boundary, RiskMetric.DAILY_LOSS)
    assert (value, unit, missing) == (Decimal("20"), "BRL", None)

    mismatch_boundary = boundary(
        risk_policy=p,
        risk_proposal=proposal(exposure_unit="USD"),
    )
    value, unit, missing = rc._metric_value(
        mismatch_boundary,
        RiskMetric.PROJECTED_WORST_CASE_EXPOSURE,
    )
    assert (value, unit, missing) == (None, "BRL", "EXPOSURE_UNIT_MISMATCH")

    denominator_mismatch_policy = dataclasses.replace(
        p,
        drawdown_semantics=drawdown_semantics(None),
    )
    denominator_mismatch_boundary = boundary(risk_policy=denominator_mismatch_policy)
    value, unit, missing = rc._metric_value(
        denominator_mismatch_boundary,
        RiskMetric.DRAWDOWN_AMOUNT,
    )
    assert (value, unit, missing) == (None, "BRL", "DRAWDOWN_POLICY_MISMATCH")
    value, unit, missing = rc._metric_value(
        denominator_mismatch_boundary,
        RiskMetric.DRAWDOWN_RATIO,
    )
    assert (value, unit, missing) == (None, "ratio", "DRAWDOWN_POLICY_MISMATCH")

    reasons = ["ALREADY_PRESENT"]
    rc._append_unique(reasons, "ALREADY_PRESENT")
    assert reasons == ["ALREADY_PRESENT"]


def test_authorization_validity_is_truncated_by_policy_expiry() -> None:
    p = policy(effective_until=dt(15), ttl=30)
    result = evaluate_risk(boundary(risk_policy=p))
    assert result.authorization is not None
    assert result.authorization.valid_until == dt(15)


def test_authorization_validation_detects_all_invalidity_classes() -> None:
    p = policy(effective_until=dt(20), ttl=10)
    b = boundary(risk_policy=p)
    result = evaluate_risk(b)
    assert result.authorization is not None
    auth = result.authorization

    valid = validate_authorization(
        auth,
        decision=result.decision,
        proposal=b.proposal,
        state=b.state,
        policy=b.policy,
        as_of_time=dt(11),
    )
    assert valid.valid
    assert valid.reasons == ()

    unissued = dataclasses.replace(auth)
    assert not unissued.is_engine_issued
    assert AuthorizationInvalidity.NOT_ENGINE_ISSUED in validate_authorization(
        unissued,
        decision=result.decision,
        proposal=b.proposal,
        state=b.state,
        policy=b.policy,
        as_of_time=dt(11),
    ).reasons

    reject_decision = RiskDecisionRecord(
        decision=RiskDecision.REJECT,
        boundary_digest=result.decision.boundary_digest,
        proposal_digest=result.decision.proposal_digest,
        state_digest=result.decision.state_digest,
        policy_digest=result.decision.policy_digest,
        reasons=("REJECTED",),
        metrics={},
        decided_at=result.decision.decided_at,
    )
    changed_proposal = dataclasses.replace(b.proposal, source_digest="other-proposal")
    changed_state = dataclasses.replace(b.state, source_lineage_digest="other-state")
    changed_policy = dataclasses.replace(b.policy, version="2")

    oversized = preserve_issuer(
        dataclasses.replace(
            auth,
            max_quantity=Decimal("11"),
            max_exposure=Decimal("201"),
        )
    )
    decision_mismatch_auth = preserve_issuer(
        dataclasses.replace(auth, decision_digest="other-decision")
    )
    proposal_mismatch_auth = preserve_issuer(
        dataclasses.replace(auth, proposal_digest="other-proposal")
    )
    state_mismatch_auth = preserve_issuer(dataclasses.replace(auth, state_digest="other-state"))
    policy_mismatch_auth = preserve_issuer(
        dataclasses.replace(auth, policy_digest="other-policy")
    )

    assert AuthorizationInvalidity.DECISION_NOT_PERMIT in validate_authorization(
        auth,
        decision=reject_decision,
        proposal=b.proposal,
        state=b.state,
        policy=b.policy,
        as_of_time=dt(11),
    ).reasons
    assert AuthorizationInvalidity.DECISION_MISMATCH in validate_authorization(
        decision_mismatch_auth,
        decision=result.decision,
        proposal=b.proposal,
        state=b.state,
        policy=b.policy,
        as_of_time=dt(11),
    ).reasons
    assert AuthorizationInvalidity.PROPOSAL_MISMATCH in validate_authorization(
        proposal_mismatch_auth,
        decision=result.decision,
        proposal=b.proposal,
        state=b.state,
        policy=b.policy,
        as_of_time=dt(11),
    ).reasons
    assert AuthorizationInvalidity.PROPOSAL_MISMATCH in validate_authorization(
        auth,
        decision=result.decision,
        proposal=changed_proposal,
        state=b.state,
        policy=b.policy,
        as_of_time=dt(11),
    ).reasons
    assert AuthorizationInvalidity.STATE_MISMATCH in validate_authorization(
        state_mismatch_auth,
        decision=result.decision,
        proposal=b.proposal,
        state=b.state,
        policy=b.policy,
        as_of_time=dt(11),
    ).reasons
    assert AuthorizationInvalidity.STATE_MISMATCH in validate_authorization(
        auth,
        decision=result.decision,
        proposal=b.proposal,
        state=changed_state,
        policy=b.policy,
        as_of_time=dt(11),
    ).reasons
    assert AuthorizationInvalidity.POLICY_MISMATCH in validate_authorization(
        policy_mismatch_auth,
        decision=result.decision,
        proposal=b.proposal,
        state=b.state,
        policy=b.policy,
        as_of_time=dt(11),
    ).reasons
    assert AuthorizationInvalidity.POLICY_MISMATCH in validate_authorization(
        auth,
        decision=result.decision,
        proposal=b.proposal,
        state=b.state,
        policy=changed_policy,
        as_of_time=dt(11),
    ).reasons
    assert AuthorizationInvalidity.NOT_YET_VALID in validate_authorization(
        auth,
        decision=result.decision,
        proposal=b.proposal,
        state=b.state,
        policy=b.policy,
        as_of_time=dt(9),
    ).reasons
    assert AuthorizationInvalidity.EXPIRED in validate_authorization(
        auth,
        decision=result.decision,
        proposal=b.proposal,
        state=b.state,
        policy=b.policy,
        as_of_time=dt(20),
    ).reasons
    assert AuthorizationInvalidity.ENVELOPE_EXCEEDS_PROPOSAL in validate_authorization(
        oversized,
        decision=result.decision,
        proposal=b.proposal,
        state=b.state,
        policy=b.policy,
        as_of_time=dt(11),
    ).reasons
    assert AuthorizationInvalidity.POLICY_NOT_EFFECTIVE in validate_authorization(
        auth,
        decision=result.decision,
        proposal=b.proposal,
        state=b.state,
        policy=b.policy,
        as_of_time=dt(20),
    ).reasons
