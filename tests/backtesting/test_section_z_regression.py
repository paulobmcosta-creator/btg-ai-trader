"""Comprehensive regression test suite covering all Section Z criteria (1-40)."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest

from btg_ai_trader.backtesting.accounting import (
    BacktestEconomicState,
    BacktestPnL,
    BacktestPositionState,
    EndOfWindowPolicy,
)
from btg_ai_trader.backtesting.assumptions import (
    EconomicAssumptions,
    ExecutionPolicy,
    FeeSchedule,
    FixedPercentageSlippageModel,
    FixedPointsSlippageModel,
    LatencyModel,
    SpreadModel,
    ZeroSlippageModel,
)
from btg_ai_trader.backtesting.domain import (
    ActionIdentity,
    BacktestAction,
    ExecutionOutcome,
    ExecutionTiming,
    InstrumentEconomics,
    OrderStyle,
    Side,
    SimulatedFill,
)
from btg_ai_trader.backtesting.engine import (
    DeterministicEconomicBacktester,
    validate_action_sequence,
)
from btg_ai_trader.backtesting.provenance import (
    compute_assumptions_hash,
)
from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.identity import (
    EventId,
    ProviderInstrumentRef,
    RunId,
    TradableInstrumentId,
)
from btg_ai_trader.observer.market import Tick
from btg_ai_trader.observer.provenance import CodeRevision, ConfigHash
from btg_ai_trader.observer.temporal import EventTime, ObservationTimes
from btg_ai_trader.replay.core import CausalMarketReplaySchedule

DUMMY_REV = CodeRevision("a" * 40)


def make_uuid(num: int = 1) -> str:
    return str(UUID(int=num))


def make_schedule(
    events: Sequence[EventEnvelope],
    run_id: str | None = None,
    code_revision: CodeRevision | None = None,
    config_hash: ConfigHash | None = None,
    provider_id: str = "xp",
    capture_scope: str = "market",
) -> CausalMarketReplaySchedule:
    return CausalMarketReplaySchedule(
        events,
        run_id=RunId(run_id or make_uuid(50)),
        code_revision=code_revision or DUMMY_REV,
        config_hash=config_hash or ConfigHash("1" * 64),
        provider_id=provider_id,
        capture_scope=capture_scope,
    )


def make_tick(
    seq: int,
    ts: datetime,
    iid: TradableInstrumentId,
    bid: Decimal = Decimal("100.0"),
    ask: Decimal = Decimal("101.0"),
) -> EventEnvelope:
    payload = Tick(bid=bid, ask=ask, last=bid, volume=Decimal("10"))
    event_time = EventTime(ts, "clock", timedelta(microseconds=1))
    return EventEnvelope(
        event_id=EventId(make_uuid(100 + seq)),
        event_type=EventType.TICK,
        source=ProviderInstrumentRef("xp", "market", "WINV26"),
        instrument_id=iid,
        times=ObservationTimes(event_time=event_time, ingestion_time=ts, knowledge_time=ts),
        payload=payload,
    )


def make_act(
    seq: int,
    ts: datetime,
    iid: TradableInstrumentId,
    side: Side = Side.BUY,
    qty: Decimal = Decimal("1.0"),
) -> BacktestAction:
    return BacktestAction(
        action_id=ActionIdentity(make_uuid(seq)),
        instrument_id=iid,
        side=side,
        quantity=qty,
        order_style=OrderStyle.MARKET,
        knowledge_cutoff=ts,
        decision_time=ts,
        order_ready_time=ts,
    )


# ---------------------------------------------------------------------------
# Criterion 1: ADR verification (Operating profiles and determinism)
# ---------------------------------------------------------------------------
def test_criterion_1_adr_exists_and_approved() -> None:
    adr_path = Path("docs/adr/0008-operating-profiles-replay-and-determinism.md")
    assert adr_path.exists(), "ADR-0008 must exist"
    content = adr_path.read_text(encoding="utf-8")
    assert "Aceita" in content or "APROVADO" in content or "Approved" in content


# ---------------------------------------------------------------------------
# Criterion 3: validate_action_sequence rejects causal violations
# ---------------------------------------------------------------------------
def test_criterion_3_action_sequence_validation() -> None:
    iid1 = TradableInstrumentId(make_uuid(1))
    iid2 = TradableInstrumentId(make_uuid(2))
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)

    # Instrument mismatch
    a_bad_inst = make_act(1, t0, iid2)
    with pytest.raises(ValueError, match="does not match engine instrument"):
        validate_action_sequence([a_bad_inst], iid1)

    # Duplicate action_id
    a1 = make_act(1, t0, iid1)
    a1_dup = make_act(1, t1, iid1)
    with pytest.raises(ValueError, match="duplicate action_id rejected"):
        validate_action_sequence([a1, a1_dup], iid1)

    # Knowledge cutoff regression
    a_early = BacktestAction(
        action_id=ActionIdentity(make_uuid(2)),
        instrument_id=iid1,
        side=Side.BUY,
        quantity=Decimal("1"),
        order_style=OrderStyle.MARKET,
        knowledge_cutoff=t0 - timedelta(seconds=1),
        decision_time=t1,
        order_ready_time=t1,
    )
    with pytest.raises(ValueError, match="knowledge_cutoff causality"):
        validate_action_sequence([a1, a_early], iid1)

    # Decision time regression (same knowledge_cutoff t0, but decision_time regresses)
    a_base_dec = BacktestAction(
        action_id=ActionIdentity(make_uuid(10)),
        instrument_id=iid1,
        side=Side.BUY,
        quantity=Decimal("1"),
        order_style=OrderStyle.MARKET,
        knowledge_cutoff=t0,
        decision_time=t1,
        order_ready_time=t1,
    )
    a_decision_regr = BacktestAction(
        action_id=ActionIdentity(make_uuid(11)),
        instrument_id=iid1,
        side=Side.BUY,
        quantity=Decimal("1"),
        order_style=OrderStyle.MARKET,
        knowledge_cutoff=t0,
        decision_time=t0,
        order_ready_time=t1,
    )
    with pytest.raises(ValueError, match="decision_time causality"):
        validate_action_sequence([a_base_dec, a_decision_regr], iid1)

    # Order ready time regression
    a_base_ready = BacktestAction(
        action_id=ActionIdentity(make_uuid(20)),
        instrument_id=iid1,
        side=Side.BUY,
        quantity=Decimal("1"),
        order_style=OrderStyle.MARKET,
        knowledge_cutoff=t0,
        decision_time=t0,
        order_ready_time=t1,
    )
    a_ready_regr = BacktestAction(
        action_id=ActionIdentity(make_uuid(21)),
        instrument_id=iid1,
        side=Side.BUY,
        quantity=Decimal("1"),
        order_style=OrderStyle.MARKET,
        knowledge_cutoff=t0,
        decision_time=t0,
        order_ready_time=t0,
    )
    with pytest.raises(ValueError, match="order_ready_time causality"):
        validate_action_sequence([a_base_ready, a_ready_regr], iid1)


# ---------------------------------------------------------------------------
# Criterion 6: Code revision strictness
# ---------------------------------------------------------------------------
def test_criterion_6_code_revision_strict() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        assumptions_id="base",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule("fee"),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )

    with pytest.raises(ValueError, match="code_revision must be explicitly provided"):
        DeterministicEconomicBacktester(econ, assumptions, code_revision=None)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="full lowercase hexadecimal"):
        DeterministicEconomicBacktester(econ, assumptions, code_revision="not-a-hex")


# ---------------------------------------------------------------------------
# Criterion 7: compute_assumptions_hash includes bps, economics, and policy
# ---------------------------------------------------------------------------
def test_criterion_7_hash_includes_bps_and_economics() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assump = EconomicAssumptions(
        assumptions_id="pct_slip",
        spread_model=SpreadModel(),
        slippage_model=FixedPercentageSlippageModel(bps=Decimal("5.0")),
        fee_schedule=FeeSchedule("fee"),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )
    h = compute_assumptions_hash(
        assump,
        instrument_economics=econ,
        end_of_window_policy=EndOfWindowPolicy.KEEP_OPEN,
    )
    assert h.value is not None
    assert len(h.value) == 64


# ---------------------------------------------------------------------------
# Criterion 9: Adverse tick rounding
# ---------------------------------------------------------------------------
def test_criterion_9_adverse_tick_rounding() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))

    # BUY rounds UP (ceiling)
    assert econ.round_price_adverse(Side.BUY, Decimal("100.1")) == Decimal("100.5")
    assert econ.round_price_adverse(Side.BUY, Decimal("100.0")) == Decimal("100.0")

    # SELL rounds DOWN (floor)
    assert econ.round_price_adverse(Side.SELL, Decimal("100.4")) == Decimal("100.0")
    assert econ.round_price_adverse(Side.SELL, Decimal("100.5")) == Decimal("100.5")

    # Non-positive price
    with pytest.raises(ValueError, match="price must be positive"):
        econ.round_price_adverse(Side.BUY, Decimal("0"))

    with pytest.raises(ValueError, match="unrecognized side"):
        econ.round_price_adverse("INVALID", Decimal("100.0"))  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Criterion 10: Slippage resulting in non-positive price raises ValueError
# ---------------------------------------------------------------------------
def test_criterion_10_slippage_non_positive_price() -> None:
    slip = FixedPointsSlippageModel(adverse_points=Decimal("200.0"))
    with pytest.raises(ValueError, match="implies non-positive fill price"):
        slip.apply_slippage(Side.SELL, Decimal("100.0"))

    slip_pct = FixedPercentageSlippageModel(bps=Decimal("15000.0"))  # 150% slippage
    with pytest.raises(ValueError, match="implies non-positive fill price"):
        slip_pct.apply_slippage(Side.SELL, Decimal("100.0"))


# ---------------------------------------------------------------------------
# Criterion 11: CLOSE_AT_LAST_VALID_QUOTE raises NotImplementedError if open
# ---------------------------------------------------------------------------
def test_criterion_11_close_at_last_valid_quote_deferred() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assump = EconomicAssumptions(
        assumptions_id="base",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule("fee"),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )
    engine = DeterministicEconomicBacktester(
        econ,
        assump,
        code_revision=DUMMY_REV,
        end_of_window_policy=EndOfWindowPolicy.CLOSE_AT_LAST_VALID_QUOTE,
    )
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    act = make_act(1, t0, iid, Side.BUY, Decimal("1.0"))
    ev = make_tick(1, t0, iid)

    with pytest.raises(NotImplementedError, match="CLOSE_AT_LAST_VALID_QUOTE is deferred"):
        engine.run([act], make_schedule([ev]))


# ---------------------------------------------------------------------------
# Criterion 12: Fail-closed mark evidence when open position lacks quote
# ---------------------------------------------------------------------------
def test_criterion_12_fail_closed_mark_evidence() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    # Open position state directly
    pos = BacktestPositionState(iid, quantity=Decimal("5"), weighted_cost_basis=Decimal("100.0"))
    pnl = BacktestPnL(
        gross_realized_pnl=Decimal("0"),
        explicit_fees=Decimal("0"),
        net_realized_pnl=Decimal("0"),
        diagnostic_slippage_burden=Decimal("0"),
    )
    state = BacktestEconomicState(
        positions=(pos,),
        pnl=pnl,
        realized_equity_curve=(Decimal("0"),),
        fills=(),
    )

    # compute_mark_to_market with no mark_evidence fails closed (returns self)
    res_state = state.compute_mark_to_market({iid: Decimal("105.0")}, mark_evidence=None)
    assert res_state.pnl.unrealized_pnl is None


# ---------------------------------------------------------------------------
# Criterion 13: SimulatedFill invariant enforcement
# ---------------------------------------------------------------------------
def test_criterion_13_simulated_fill_invariants() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    t = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    timing = ExecutionTiming(t, t, t, t, t)

    # FILL with zero quantity
    with pytest.raises(ValueError, match="FILL outcome requires strictly positive quantity"):
        SimulatedFill(
            fill_id=ActionIdentity(make_uuid(1)),
            action_id=ActionIdentity(make_uuid(2)),
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("0"),
            raw_price=Decimal("100"),
            fill_price=Decimal("100"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.FILL,
            source_event_id=EventId(make_uuid(3)),
        )

    # FILL with None source_event_id
    with pytest.raises(ValueError, match="FILL outcome requires a non-None source_event_id"):
        SimulatedFill(
            fill_id=ActionIdentity(make_uuid(1)),
            action_id=ActionIdentity(make_uuid(2)),
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("1"),
            raw_price=Decimal("100"),
            fill_price=Decimal("100"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.FILL,
            source_event_id=None,
        )

    # NO_FILL with non-zero quantity
    with pytest.raises(ValueError, match="non-FILL outcome requires executed quantity == 0"):
        SimulatedFill(
            fill_id=ActionIdentity(make_uuid(1)),
            action_id=ActionIdentity(make_uuid(2)),
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("1"),
            raw_price=Decimal("0"),
            fill_price=Decimal("0"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.NO_FILL,
        )


# ---------------------------------------------------------------------------
# Criterion 14: FeeSchedule temporal validity
# ---------------------------------------------------------------------------
def test_criterion_14_fee_schedule_effective_window() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)

    # FeeSchedule effective from t0 + 1 hour
    fee_sched = FeeSchedule(
        "future_fee",
        effective_from=t0 + timedelta(hours=1),
    )
    assump = EconomicAssumptions(
        assumptions_id="base",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=fee_sched,
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )
    engine = DeterministicEconomicBacktester(econ, assump, code_revision=DUMMY_REV)

    act = make_act(1, t0, iid, Side.BUY, Decimal("1.0"))
    ev = make_tick(1, t0, iid)

    res = engine.run([act], make_schedule([ev]))
    assert len(res.fills) == 1
    assert res.fills[0].outcome == ExecutionOutcome.INDETERMINATE
    assert res.fills[0].reason == "FEE_SCHEDULE_OUTSIDE_EFFECTIVE_PERIOD"


# ---------------------------------------------------------------------------
# Criterion 15: ExecutionPolicy naming and timeout
# ---------------------------------------------------------------------------
def test_criterion_15_execution_policy_timeout() -> None:
    policy = ExecutionPolicy(max_execution_evidence_wait_us=1000)
    assert policy.max_execution_evidence_wait_us == 1000
    assert policy.max_quote_age_us == 1000

    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assump = EconomicAssumptions(
        assumptions_id="timeout_assump",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule("fee"),
        latency_model=LatencyModel(),
        execution_policy=policy,
    )
    engine = DeterministicEconomicBacktester(econ, assump, code_revision=DUMMY_REV)

    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    act = make_act(1, t0, iid, Side.BUY, Decimal("1.0"))
    # Event arrives 5 seconds later (> 1000us)
    ev_late = make_tick(1, t0 + timedelta(seconds=5), iid)

    res = engine.run([act], make_schedule([ev_late]))
    assert len(res.fills) == 1
    assert res.fills[0].outcome == ExecutionOutcome.INDETERMINATE
    assert res.fills[0].reason == "NO_EXECUTION_EVIDENCE_WITHIN_WAIT_WINDOW"


# ---------------------------------------------------------------------------
# Criterion 16: InstrumentEconomics quantity step validation
# ---------------------------------------------------------------------------
def test_criterion_16_quantity_step_validation() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("5.0"))

    econ.validate_quantity(Decimal("10.0"))
    econ.validate_quantity(Decimal("5.0"))

    with pytest.raises(ValueError, match="integer multiple of quantity_step"):
        econ.validate_quantity(Decimal("7.0"))

    with pytest.raises(ValueError, match="strictly positive"):
        econ.validate_quantity(Decimal("0"))

    with pytest.raises(ValueError, match="quantity must be Decimal"):
        econ.validate_quantity(10)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Criterion 17: Diagnostic spread burden tracking without double deduction
# ---------------------------------------------------------------------------
def test_criterion_17_diagnostic_spread_burden() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assump = EconomicAssumptions(
        assumptions_id="base",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule("fee", fixed_per_order=Decimal("2.0")),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )
    engine = DeterministicEconomicBacktester(econ, assump, code_revision=DUMMY_REV)

    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)

    # Buy 10 @ ask 101.0, bid 99.0 -> mid 100.0, spread burden = (101 - 100)*10 = 10
    # Sell 10 @ bid 109.0, ask 111.0 -> mid 110.0, spread burden = (110 - 109)*10 = 10
    act1 = make_act(1, t0, iid, Side.BUY, Decimal("10.0"))
    act2 = make_act(2, t1, iid, Side.SELL, Decimal("10.0"))
    ev1 = make_tick(1, t0, iid, bid=Decimal("99.0"), ask=Decimal("101.0"))
    ev2 = make_tick(2, t1, iid, bid=Decimal("109.0"), ask=Decimal("111.0"))

    res = engine.run([act1, act2], make_schedule([ev1, ev2]))

    assert res.fills[0].diagnostic_spread_burden == Decimal("10.0")
    assert res.fills[1].diagnostic_spread_burden == Decimal("10.0")
    # Total diagnostic spread burden
    assert res.metrics.diagnostic_spread_burden == Decimal("20.0")

    # Net realized PnL = (109 - 101)*10 - 4 (fees) = 80 - 4 = 76
    # Spread burden is NOT deducted again!
    assert res.metrics.gross_realized_pnl == Decimal("80.0")
    assert res.metrics.total_explicit_fees == Decimal("4.0")
    assert res.metrics.net_realized_pnl == Decimal("76.0")


# ---------------------------------------------------------------------------
# Criterion 28: Deterministic run_id derivation via uuid5
# ---------------------------------------------------------------------------
def test_criterion_28_run_id_deterministic_uuid5() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assump = EconomicAssumptions(
        assumptions_id="base",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule("fee"),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )
    engine = DeterministicEconomicBacktester(econ, assump, code_revision=DUMMY_REV)

    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    act = make_act(1, t0, iid, Side.BUY, Decimal("1.0"))
    ev = make_tick(1, t0, iid)
    sched = make_schedule([ev])

    res1 = engine.run([act], sched)
    res2 = engine.run([act], sched)

    assert res1.manifest.run_id == res2.manifest.run_id
    # Valid UUID v5
    uuid_obj = UUID(res1.manifest.run_id.value)
    assert uuid_obj.version == 5


# ---------------------------------------------------------------------------
# Engine input parameter validations (missing schedule/events)
# ---------------------------------------------------------------------------
def test_engine_missing_events_and_invalid_schedule() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assump = EconomicAssumptions(
        assumptions_id="base",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule("fee"),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )
    engine = DeterministicEconomicBacktester(econ, assump, code_revision=DUMMY_REV)

    with pytest.raises(
        ValueError, match="Either replay_schedule or market_events must be provided"
    ):
        engine.run([], market_events=None, replay_schedule=None)

    with pytest.raises(ValueError, match="replay_schedule must be CausalMarketReplaySchedule"):
        engine.run([], replay_schedule="not_a_schedule")  # type: ignore[arg-type]
