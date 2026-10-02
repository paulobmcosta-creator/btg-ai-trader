"""Domain and provenance tests for Sprint 7 Risk Engine."""

# ruff: noqa: I001

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext

import pytest

from btg_ai_trader.observer.identity import TradableInstrumentId
from btg_ai_trader.risk_engine import (
    CircuitBreakerState,
    CircuitStatus,
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
    RiskEvaluationResult,
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
    initial_circuit_state,
    latch_circuit,
    unlatch_circuit,
)
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY


INSTRUMENT = TradableInstrumentId("11111111-1111-1111-1111-111111111111")
OTHER_INSTRUMENT = TradableInstrumentId("22222222-2222-2222-2222-222222222222")


def dt(seconds: int = 0) -> datetime:
    return datetime(2026, 9, 26, 12, 0, tzinfo=UTC) + timedelta(seconds=seconds)


T0 = dt(0)
T5 = dt(5)
T9 = dt(9)
T10 = dt(10)


def rules() -> tuple[RiskLimitRule, ...]:
    return (
        RiskLimitRule(
            "01-capacity",
            RiskMetric.PROJECTED_CAPACITY_USAGE,
            LimitOperator.LTE,
            Decimal("1000"),
            "BRL",
            True,
        ),
        RiskLimitRule(
            "02-daily",
            RiskMetric.DAILY_LOSS,
            LimitOperator.LTE,
            Decimal("100"),
            "BRL",
            True,
        ),
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
    rule_set: tuple[RiskLimitRule, ...] | None = None,
    portfolio_id: str = "portfolio-1",
    instrument_id: TradableInstrumentId | None = INSTRUMENT,
    effective_from: datetime = T0,
    effective_until: datetime | None = None,
    postures: tuple[SafetyPosture, ...] = (SafetyPosture.NORMAL,),
    ttl: int = 30,
    predeclared: bool = True,
) -> RiskPolicyBundle:
    return RiskPolicyBundle(
        policy_id="risk-policy",
        version="1",
        portfolio_id=portfolio_id,
        instrument_id=instrument_id,
        effective_from=effective_from,
        effective_until=effective_until,
        rules=rule_set or rules(),
        allowed_safety_postures=postures,
        authorization_ttl_seconds=ttl,
        daily_loss_semantics=daily_semantics(),
        drawdown_semantics=drawdown_semantics(),
        tail_semantics=tail_semantics(),
        numeric_policy=DEFAULT_NUMERIC_POLICY,
        predeclared=predeclared,
    )


def proposal(
    *,
    instrument_id: TradableInstrumentId = INSTRUMENT,
    portfolio_id: str = "portfolio-1",
    created_at: datetime = T5,
) -> RiskProposal:
    return RiskProposal(
        proposal_id="proposal-1",
        instrument_id=instrument_id,
        portfolio_id=portfolio_id,
        direction=EconomicDirection.INCREASE_LONG,
        requested_quantity=Decimal("10"),
        quantity_unit="shares",
        requested_exposure=Decimal("200"),
        exposure_unit="BRL",
        created_at=created_at,
        source_digest="proposal-source",
    )


def exposure(*, quality: EvidenceQuality = EvidenceQuality.VALID) -> ExposureState:
    return ExposureState(
        current_position_exposure=Decimal("300"),
        committed_potential_exposure=Decimal("100"),
        risk_capacity_reservation=Decimal("100"),
        worst_case_exposure=Decimal("400"),
        unit="BRL",
        source_digest="exposure-source",
        quality=quality,
    )


def daily_loss() -> DailyLossState:
    return DailyLossState(
        recognized_pnl=Decimal("-20"),
        currency="BRL",
        pnl_source_id="portfolio-pnl",
        include_unrealized=False,
        loss_sign_convention=PnlLossConvention.NEGATIVE_PNL_IS_LOSS,
        session_id="2026-09-26-B3",
        session_start=dt(0),
        session_end=dt(100),
        session_calendar_id="B3",
        timezone_name="America/Sao_Paulo",
        reset_semantics="SESSION_BOUNDARY",
        source_digest="pnl-source",
    )


def drawdown(*, denominator: Decimal | None = Decimal("1000")) -> DrawdownState:
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
    )


def tail() -> TailRiskEvidence:
    return TailRiskEvidence(
        source_kind=TailEvidenceSourceKind.EMPIRICAL_OBSERVED,
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
        sufficient=True,
        source_digest="tail-source",
    )


def state(
    risk_policy: RiskPolicyBundle,
    *,
    circuit: CircuitBreakerState | None = None,
    instrument_id: TradableInstrumentId = INSTRUMENT,
    portfolio_id: str = "portfolio-1",
    as_of_time: datetime = T10,
    knowledge_time: datetime = T9,
) -> RiskStateSnapshot:
    actual_circuit = circuit or initial_circuit_state(
        policy_digest=risk_policy.policy_digest,
        at_time=dt(0),
        evidence_digest="circuit-initial",
    )
    return RiskStateSnapshot(
        snapshot_id="state-1",
        portfolio_id=portfolio_id,
        instrument_id=instrument_id,
        as_of_time=as_of_time,
        knowledge_time=knowledge_time,
        exposure=exposure(),
        daily_loss=daily_loss(),
        drawdown=drawdown(),
        tail_risk=tail(),
        safety_posture=SafetyPosture.NORMAL,
        commitment_readiness=CommitmentReadiness.READY,
        circuit=actual_circuit,
        quality=EvidenceQuality.VALID,
        source_lineage_digest="risk-lineage",
    )


def boundary() -> RiskEvaluationBoundary:
    risk_policy = policy()
    return RiskEvaluationBoundary.build(
        proposal=proposal(),
        state=state(risk_policy),
        policy=risk_policy,
        as_of_time=dt(10),
        engine_revision="s7-test",
    )


def test_canonical_json_helpers_and_text_numeric_guards() -> None:
    payload = {
        "decimal": Decimal("1.25"),
        "datetime": dt(),
        "enum": RiskDecision.PERMIT,
        "instrument": INSTRUMENT,
        "mapping": {"z": Decimal("2"), "a": Decimal("1")},
        "sequence": (Decimal("3"), "x"),
        "plain": True,
    }
    converted = rc._jsonable(payload)
    assert isinstance(converted, dict)
    assert converted["decimal"] == "1.25"
    assert converted["instrument"] == INSTRUMENT.value
    assert converted["sequence"] == ["3", "x"]
    assert rc._digest({"x": Decimal("1")}) == rc._digest({"x": Decimal("1")})

    with pytest.raises(ValueError, match="nonempty text"):
        rc._require_text(" x ", "x")
    with pytest.raises(ValueError, match="timezone-aware"):
        rc._require_aware(datetime(2026, 9, 26), "when")
    with pytest.raises(ValueError, match="finite Decimal"):
        rc._require_decimal(Decimal("NaN"), "x")
    with pytest.raises(ValueError, match="non-negative"):
        rc._require_decimal(Decimal("-1"), "x", nonnegative=True)
    with pytest.raises(ValueError, match="positive"):
        rc._require_decimal(Decimal("0"), "x", positive=True)
    with pytest.raises(ValueError, match="metric_name"):
        rc._freeze_metrics({"": Decimal("1")})
    with pytest.raises(ValueError, match="finite Decimal"):
        rc._freeze_metrics({"x": Decimal("NaN")})

    with localcontext() as ambient:
        ambient.prec = 2
        ambient.Emin = 0
        ambient.Emax = 9
        assert rc._exact_subtract(Decimal("0.015"), Decimal("0.00")) == Decimal("0.015")


def test_proposal_exposure_daily_drawdown_and_tail_validation() -> None:
    item = proposal()
    assert len(item.proposal_digest) == 64

    with pytest.raises(ValueError, match="TradableInstrumentId"):
        dataclasses.replace(item, instrument_id="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="positive"):
        dataclasses.replace(item, requested_quantity=Decimal("0"))
    with pytest.raises(ValueError, match="positive"):
        dataclasses.replace(item, requested_exposure=Decimal("0"))

    exp = exposure()
    assert len(exp.exposure_digest) == 64
    with pytest.raises(ValueError, match="non-negative"):
        dataclasses.replace(exp, current_position_exposure=Decimal("-1"))
    with pytest.raises(ValueError, match="below current plus committed"):
        dataclasses.replace(exp, worst_case_exposure=Decimal("399"))

    loss = daily_loss()
    assert loss.loss_amount == Decimal("20")
    assert dataclasses.replace(loss, recognized_pnl=Decimal("10")).loss_amount == Decimal("0")
    with pytest.raises(ValueError, match="positive duration"):
        dataclasses.replace(loss, session_end=loss.session_start)
    assert len(daily_semantics().semantics_digest) == 64

    dd = drawdown()
    assert dd.amount == Decimal("100")
    assert dd.ratio == Decimal("0.1")
    third = DrawdownState(
        peak_value=Decimal("1"),
        current_value=Decimal("0"),
        unit="BRL",
        capital_denominator=Decimal("3"),
        denominator_convention=(
            DrawdownDenominatorConvention.EXPLICIT_POSITIVE_CAPITAL
        ),
        source_id="portfolio-equity",
        series_kind=DrawdownSeriesKind.EQUITY,
        peak_id="peak-third",
        current_id="current-third",
        source_digest="drawdown-third",
    )
    with localcontext() as ambient:
        ambient.prec = 2
        low_precision_ratio = third.ratio
    with localcontext() as ambient:
        ambient.prec = 50
        high_precision_ratio = third.ratio
    assert low_precision_ratio == high_precision_ratio
    assert drawdown(denominator=None).ratio is None
    with pytest.raises(ValueError, match="governed peak"):
        dataclasses.replace(dd, current_value=Decimal("1001"))
    with pytest.raises(ValueError, match="positive"):
        dataclasses.replace(dd, capital_denominator=Decimal("0"))
    with pytest.raises(ValueError, match="requires explicit denominator_convention"):
        dataclasses.replace(dd, denominator_convention=None)
    with pytest.raises(ValueError, match="requires an explicit capital_denominator"):
        dataclasses.replace(
            drawdown(denominator=None),
            denominator_convention=(
                DrawdownDenominatorConvention.EXPLICIT_POSITIVE_CAPITAL
            ),
        )
    assert len(drawdown_semantics().semantics_digest) == 64

    evidence = tail()
    assert len(evidence.tail_evidence_digest) == 64
    with pytest.raises(ValueError, match="must not exceed 0.5"):
        dataclasses.replace(evidence, tail_fraction=Decimal("0.6"))
    with pytest.raises(ValueError, match="counts must be positive"):
        dataclasses.replace(evidence, total_count=0)
    with pytest.raises(ValueError, match="cannot exceed"):
        dataclasses.replace(evidence, tail_count=101)
    with pytest.raises(ValueError, match="requires VaR and ES"):
        dataclasses.replace(evidence, value_at_risk=None)
    semantics = tail_semantics()
    assert len(semantics.semantics_digest) == 64
    with pytest.raises(ValueError, match="must not exceed 0.5"):
        dataclasses.replace(semantics, tail_fraction=Decimal("0.6"))


def test_circuit_breaker_is_latched_and_requires_human_unlatch() -> None:
    p = policy()
    initial = initial_circuit_state(
        policy_digest=p.policy_digest,
        at_time=dt(),
        evidence_digest="initial-evidence",
    )
    assert initial.status is CircuitStatus.NORMAL
    latched = latch_circuit(
        initial,
        reason="HARD_RISK_BREACH",
        evidence_digest="breach-evidence",
        at_time=dt(1),
    )
    assert latched.status is CircuitStatus.LATCHED
    assert latched.previous_state_digest == initial.circuit_digest

    with pytest.raises(ValueError, match="already latched"):
        latch_circuit(
            latched,
            reason="again",
            evidence_digest="again",
            at_time=dt(2),
        )
    with pytest.raises(ValueError, match="backward"):
        latch_circuit(
            initial,
            reason="bad-time",
            evidence_digest="e",
            at_time=dt(-1),
        )
    with pytest.raises(ValueError, match="only a latched"):
        unlatch_circuit(
            initial,
            human_confirmation_digest="human",
            recovery_digest="recovery",
            at_time=dt(2),
        )
    with pytest.raises(ValueError, match="human_confirmation_digest"):
        unlatch_circuit(
            latched,
            human_confirmation_digest="",
            recovery_digest="recovery",
            at_time=dt(2),
        )
    with pytest.raises(ValueError, match="recovery_digest"):
        unlatch_circuit(
            latched,
            human_confirmation_digest="human",
            recovery_digest="",
            at_time=dt(2),
        )
    with pytest.raises(ValueError, match="backward"):
        unlatch_circuit(
            latched,
            human_confirmation_digest="human",
            recovery_digest="recovery",
            at_time=dt(),
        )

    recovered = unlatch_circuit(
        latched,
        human_confirmation_digest="human",
        recovery_digest="recovery",
        at_time=dt(2),
    )
    assert recovered.status is CircuitStatus.NORMAL
    assert recovered.reason == "HUMAN_CONFIRMED_UNLATCH"
    assert recovered.previous_state_digest == latched.circuit_digest


def test_state_snapshot_validation_and_component_binding() -> None:
    p = policy()
    snapshot = state(p)
    assert len(snapshot.state_digest) == 64

    with pytest.raises(ValueError, match="TradableInstrumentId"):
        dataclasses.replace(snapshot, instrument_id="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="knowledge_time"):
        dataclasses.replace(snapshot, knowledge_time=dt(11))
    with pytest.raises(ValueError, match="daily-loss session"):
        dataclasses.replace(snapshot, as_of_time=dt(101))
    with pytest.raises(ValueError, match="circuit state"):
        dataclasses.replace(
            snapshot,
            circuit=initial_circuit_state(
                policy_digest=p.policy_digest,
                at_time=dt(11),
                evidence_digest="future",
            ),
        )


def test_policy_rule_validation_and_canonicalization() -> None:
    projected = RiskLimitRule(
        "01",
        RiskMetric.PROJECTED_WORST_CASE_EXPOSURE,
        LimitOperator.LTE,
        Decimal("1000"),
        "BRL",
        True,
    )
    assert projected.threshold == Decimal("1000")
    with pytest.raises(ValueError, match="positive"):
        dataclasses.replace(projected, threshold=Decimal("0"))

    valid = policy(rule_set=(projected,))
    assert len(valid.policy_digest) == 64
    assert policy(instrument_id=None).instrument_id is None
    assert policy(effective_until=dt(20)).effective_until == dt(20)

    with pytest.raises(ValueError, match="TradableInstrumentId or None"):
        dataclasses.replace(valid, instrument_id="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="positive duration"):
        dataclasses.replace(valid, effective_until=valid.effective_from)
    with pytest.raises(ValueError, match="predeclared"):
        dataclasses.replace(valid, predeclared=False)
    with pytest.raises(ValueError, match="at least one rule"):
        dataclasses.replace(valid, rules=())
    with pytest.raises(ValueError, match="canonically ordered"):
        dataclasses.replace(
            valid,
            rules=(
                RiskLimitRule(
                    "b",
                    RiskMetric.PROJECTED_CAPACITY_USAGE,
                    LimitOperator.LTE,
                    Decimal("1000"),
                    "BRL",
                    True,
                ),
                RiskLimitRule(
                    "a",
                    RiskMetric.DAILY_LOSS,
                    LimitOperator.LTE,
                    Decimal("10"),
                    "BRL",
                    True,
                ),
            ),
        )
    with pytest.raises(ValueError, match="must be unique"):
        dataclasses.replace(valid, rules=(projected, projected))
    with pytest.raises(ValueError, match="hard projected"):
        dataclasses.replace(
            valid,
            rules=(
                RiskLimitRule(
                    "01",
                    RiskMetric.DAILY_LOSS,
                    LimitOperator.LTE,
                    Decimal("10"),
                    "BRL",
                    True,
                ),
            ),
        )
    with pytest.raises(ValueError, match="cannot be empty"):
        dataclasses.replace(valid, allowed_safety_postures=())
    with pytest.raises(ValueError, match="canonically ordered"):
        dataclasses.replace(
            valid,
            allowed_safety_postures=(
                SafetyPosture.NORMAL,
                SafetyPosture.DEGRADED,
            ),
        )
    with pytest.raises(ValueError, match="must be unique"):
        dataclasses.replace(
            valid,
            allowed_safety_postures=(SafetyPosture.NORMAL, SafetyPosture.NORMAL),
        )
    with pytest.raises(ValueError, match="positive"):
        dataclasses.replace(valid, authorization_ttl_seconds=0)

    bare = dataclasses.replace(
        valid,
        daily_loss_semantics=None,
        drawdown_semantics=None,
        tail_semantics=None,
    )
    assert len(bare.policy_digest) == 64

    default_policy = policy()
    with pytest.raises(ValueError, match="DAILY_LOSS rule requires"):
        dataclasses.replace(default_policy, daily_loss_semantics=None)

    draw_rule = RiskLimitRule(
        "02-draw",
        RiskMetric.DRAWDOWN_AMOUNT,
        LimitOperator.LTE,
        Decimal("100"),
        "BRL",
        True,
    )
    with pytest.raises(ValueError, match="drawdown rule requires"):
        dataclasses.replace(
            valid,
            rules=(projected, draw_rule),
            drawdown_semantics=None,
        )

    ratio_rule = RiskLimitRule(
        "02-ratio",
        RiskMetric.DRAWDOWN_RATIO,
        LimitOperator.LTE,
        Decimal("0.2"),
        "ratio",
        True,
    )
    with pytest.raises(ValueError, match="explicit denominator convention"):
        dataclasses.replace(
            valid,
            rules=(projected, ratio_rule),
            drawdown_semantics=drawdown_semantics(None),
        )

    tail_rule = RiskLimitRule(
        "02-var",
        RiskMetric.VALUE_AT_RISK,
        LimitOperator.LTE,
        Decimal("100"),
        "BRL",
        True,
    )
    with pytest.raises(ValueError, match="VaR/ES rule requires"):
        dataclasses.replace(
            valid,
            rules=(projected, tail_rule),
            tail_semantics=None,
        )


def test_boundary_factory_fails_closed_and_marks_verified() -> None:
    p = policy()
    s = state(p)
    q = proposal()
    verified = RiskEvaluationBoundary.build(
        proposal=q,
        state=s,
        policy=p,
        as_of_time=dt(10),
        engine_revision="revision",
    )
    assert verified.is_verified
    assert len(verified.boundary_digest) == 64

    forged = RiskEvaluationBoundary(
        proposal=q,
        state=s,
        policy=p,
        as_of_time=dt(10),
        engine_revision="revision",
        boundary_digest="forged",
    )
    assert not forged.is_verified

    with pytest.raises(ValueError, match="instrument identities"):
        RiskEvaluationBoundary.build(
            proposal=proposal(instrument_id=OTHER_INSTRUMENT),
            state=s,
            policy=p,
            as_of_time=dt(10),
            engine_revision="r",
        )
    with pytest.raises(ValueError, match="portfolio identities"):
        RiskEvaluationBoundary.build(
            proposal=proposal(portfolio_id="other"),
            state=s,
            policy=p,
            as_of_time=dt(10),
            engine_revision="r",
        )
    with pytest.raises(ValueError, match="created after"):
        RiskEvaluationBoundary.build(
            proposal=proposal(created_at=dt(11)),
            state=s,
            policy=p,
            as_of_time=dt(10),
            engine_revision="r",
        )
    with pytest.raises(ValueError, match="from the future"):
        RiskEvaluationBoundary.build(
            proposal=q,
            state=state(p, as_of_time=dt(11), knowledge_time=dt(10)),
            policy=p,
            as_of_time=dt(10),
            engine_revision="r",
        )


def test_decision_authorization_and_result_structural_guards() -> None:
    b = boundary()
    decision = RiskDecisionRecord(
        decision=RiskDecision.PERMIT,
        boundary_digest=b.boundary_digest,
        proposal_digest=b.proposal.proposal_digest,
        state_digest=b.state.state_digest,
        policy_digest=b.policy.policy_digest,
        reasons=("PERMITTED",),
        metrics={"x": Decimal("1")},
        decided_at=b.as_of_time,
    )
    assert len(decision.decision_digest) == 64
    with pytest.raises(ValueError, match="at least one reason"):
        dataclasses.replace(decision, reasons=())
    with pytest.raises(ValueError, match="must be unique"):
        dataclasses.replace(decision, reasons=("x", "x"))

    authorization = RiskAuthorization(
        decision_digest=decision.decision_digest,
        proposal_digest=b.proposal.proposal_digest,
        state_digest=b.state.state_digest,
        policy_digest=b.policy.policy_digest,
        max_quantity=Decimal("1"),
        quantity_unit="shares",
        max_exposure=Decimal("10"),
        exposure_unit="BRL",
        valid_from=dt(10),
        valid_until=dt(11),
        engine_revision="r",
    )
    assert not authorization.is_engine_issued
    with pytest.raises(ValueError, match="positive duration"):
        dataclasses.replace(authorization, valid_until=authorization.valid_from)

    reject = dataclasses.replace(decision, decision=RiskDecision.REJECT, reasons=("REJECTED",))
    with pytest.raises(ValueError, match="REJECT cannot carry"):
        RiskEvaluationResult(reject, authorization)
    with pytest.raises(ValueError, match="PERMIT requires"):
        RiskEvaluationResult(decision, None)
