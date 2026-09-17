"""Anti-leakage and anti-lookahead verification test suite for Sprint 3.

Verifies that execution outcomes and realized metrics are strictly causal,
preventing future events or post-execution perturbations from influencing earlier actions.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from btg_ai_trader.backtesting.assumptions import (
    EconomicAssumptions,
    ExecutionPolicy,
    FeeSchedule,
    FixedPointsSlippageModel,
    LatencyModel,
    SpreadModel,
    ZeroSlippageModel,
)
from btg_ai_trader.backtesting.domain import (
    ActionIdentity,
    BacktestAction,
    ExecutionOutcome,
    InstrumentEconomics,
    OrderStyle,
    Side,
)
from btg_ai_trader.backtesting.engine import DeterministicEconomicBacktester
from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.identity import (
    EventId,
    ProviderInstrumentRef,
    TradableInstrumentId,
)
from btg_ai_trader.observer.market import Tick
from btg_ai_trader.observer.provenance import CodeRevision
from btg_ai_trader.observer.temporal import EventTime, ObservationTimes

DUMMY_REV = CodeRevision("a" * 40)


def make_uuid(num: int = 1) -> str:
    return str(UUID(int=num))


def make_tick_event(
    seq: int,
    ts: datetime,
    iid: TradableInstrumentId,
    bid: Decimal,
    ask: Decimal,
) -> EventEnvelope:
    payload = Tick(
        bid=bid,
        ask=ask,
        last=bid,
        volume=Decimal("10"),
    )
    event_time = EventTime(ts, "fixture-clock", timedelta(microseconds=1))
    return EventEnvelope(
        event_id=EventId(make_uuid(100 + seq)),
        event_type=EventType.TICK,
        source=ProviderInstrumentRef("xp", "market", "WINV26"),
        instrument_id=iid,
        times=ObservationTimes(
            event_time=event_time,
            ingestion_time=ts,
            knowledge_time=ts,
        ),
        payload=payload,
    )


def make_action(
    action_num: int,
    ts: datetime,
    iid: TradableInstrumentId,
    side: Side,
    qty: Decimal = Decimal("10"),
) -> BacktestAction:
    return BacktestAction(
        action_id=ActionIdentity(make_uuid(action_num)),
        instrument_id=iid,
        side=side,
        quantity=qty,
        order_style=OrderStyle.MARKET,
        knowledge_cutoff=ts,
        decision_time=ts,
        order_ready_time=ts,
    )


def test_future_event_insertion_invariance() -> None:
    """Inserting future market events must NOT alter execution of earlier actions."""
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        assumptions_id="leakage_assump",
        spread_model=SpreadModel(),
        slippage_model=FixedPointsSlippageModel(adverse_points=Decimal("0.5")),
        fee_schedule=FeeSchedule(schedule_id="fee"),
        latency_model=LatencyModel(decision_latency_us=100, transit_latency_us=100),
        execution_policy=ExecutionPolicy(),
    )
    engine = DeterministicEconomicBacktester(econ, assumptions, code_revision=DUMMY_REV)

    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t_future = datetime(2026, 9, 16, 10, 5, 0, tzinfo=UTC)

    action = make_action(1, t0, iid, Side.BUY, Decimal("10"))
    # Event 1 at t0 + 500us (after simulated arrival at t0 + 200us)
    e1 = make_tick_event(
        1, t0 + timedelta(microseconds=500), iid, bid=Decimal("99.5"), ask=Decimal("100.0")
    )

    # Baseline: single action and single eligible event
    res_base = engine.run([action], [e1])
    assert len(res_base.fills) == 1
    f_base = res_base.fills[0]
    assert f_base.outcome == ExecutionOutcome.FILL
    assert f_base.fill_price == Decimal("100.5")  # Ask 100.0 + 0.5 adverse slippage

    # Sequence with future events inserted (e.g. wild price swing 5 minutes later)
    e_future1 = make_tick_event(2, t_future, iid, bid=Decimal("50.0"), ask=Decimal("51.0"))
    e_future2 = make_tick_event(
        3, t_future + timedelta(seconds=1), iid, bid=Decimal("200.0"), ask=Decimal("201.0")
    )

    res_with_future = engine.run([action], [e1, e_future1, e_future2])
    assert len(res_with_future.fills) == 1
    f_with_future = res_with_future.fills[0]

    # Exactly identical execution parameters
    assert f_with_future.fill_price == f_base.fill_price
    assert f_with_future.slippage == f_base.slippage
    assert f_with_future.explicit_fee == f_base.explicit_fee
    assert f_with_future.timing == f_base.timing
    assert f_with_future.outcome == f_base.outcome


def test_future_event_perturbation_invariance() -> None:
    """Modifying future market events cannot retroactively alter earlier fills."""
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        assumptions_id="leakage_assump",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule(schedule_id="fee"),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )
    engine = DeterministicEconomicBacktester(econ, assumptions, code_revision=DUMMY_REV)

    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)

    action1 = make_action(1, t0, iid, Side.BUY, Decimal("10"))
    e1 = make_tick_event(1, t0, iid, bid=Decimal("99.5"), ask=Decimal("100.0"))

    # Future event variant A
    e2_a = make_tick_event(2, t1, iid, bid=Decimal("105.0"), ask=Decimal("106.0"))
    res_a = engine.run([action1], [e1, e2_a])

    # Future event variant B (drastically different quote)
    e2_b = make_tick_event(2, t1, iid, bid=Decimal("150.0"), ask=Decimal("151.0"))
    res_b = engine.run([action1], [e1, e2_b])

    # Past fill for action1 is completely invariant
    assert res_a.fills[0].fill_price == res_b.fills[0].fill_price == Decimal("100.0")
    assert res_a.fills[0].timing == res_b.fills[0].timing
    assert res_a.fills[0].outcome == res_b.fills[0].outcome


def test_pre_arrival_event_cannot_be_consumed() -> None:
    """An action cannot execute against a quote observed prior to its arrival time."""
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        assumptions_id="leakage_assump",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule(schedule_id="fee"),
        latency_model=LatencyModel(decision_latency_us=500, transit_latency_us=500),
        execution_policy=ExecutionPolicy(),
    )
    engine = DeterministicEconomicBacktester(econ, assumptions, code_revision=DUMMY_REV)

    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    # Order ready at t0 -> simulated arrival at t0 + 1000us
    action = make_action(1, t0, iid, Side.BUY, Decimal("10"))

    # Event 1 at t0 + 200us (too early, prior to arrival at t0 + 1000us) with tempting low ask
    e_too_early = make_tick_event(
        1, t0 + timedelta(microseconds=200), iid, bid=Decimal("79.0"), ask=Decimal("80.0")
    )
    # Event 2 at t0 + 1200us (eligible after arrival) with higher ask
    e_eligible = make_tick_event(
        2, t0 + timedelta(microseconds=1200), iid, bid=Decimal("99.0"), ask=Decimal("100.0")
    )

    res = engine.run([action], [e_too_early, e_eligible])
    assert len(res.fills) == 1
    # Must NOT consume the pre-arrival event at 80.0
    assert res.fills[0].fill_price == Decimal("100.0")
    assert res.fills[0].raw_price == Decimal("100.0")
    assert res.fills[0].timing.fill_opportunity_time == e_eligible.times.knowledge_time
