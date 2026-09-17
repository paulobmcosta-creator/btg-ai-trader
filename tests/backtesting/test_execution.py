"""Unit tests for deterministic execution simulation."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest

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
from btg_ai_trader.backtesting.execution import (
    simulate_action_execution,
    simulate_actions,
)
from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.identity import (
    EventId,
    ProviderInstrumentRef,
    TradableInstrumentId,
)
from btg_ai_trader.observer.market import Candle, CandleFinality, Tick
from btg_ai_trader.observer.temporal import EventTime, ObservationTimes
from btg_ai_trader.observer.values import MissingReason


def make_uuid(num: int = 1) -> str:
    return str(UUID(int=num))


def make_event(
    num: int,
    kt: datetime | MissingReason,
    instrument_id: TradableInstrumentId,
    payload: Tick | Candle,
    event_type: EventType = EventType.TICK,
) -> EventEnvelope:
    t = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    event_time = EventTime(t, "fixture-clock", timedelta(microseconds=1))
    return EventEnvelope(
        event_id=EventId(make_uuid(num)),
        event_type=event_type,
        source=ProviderInstrumentRef("xp", "market", "WINV26"),
        instrument_id=instrument_id,
        times=ObservationTimes(
            event_time=event_time,
            ingestion_time=t,
            knowledge_time=kt,
        ),
        payload=payload,
    )


def test_simulate_action_validation() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        "test_a",
        SpreadModel(),
        ZeroSlippageModel(),
        FeeSchedule("fee"),
        LatencyModel(),
        ExecutionPolicy(),
    )
    t = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    action = BacktestAction(
        ActionIdentity(make_uuid(2)),
        iid,
        Side.BUY,
        Decimal("1"),
        OrderStyle.MARKET,
        t,
        t,
        t,
    )

    with pytest.raises(ValueError, match="action must be BacktestAction"):
        simulate_action_execution("bad", (), assumptions, econ)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="assumptions must be EconomicAssumptions"):
        simulate_action_execution(action, (), "bad", econ)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="instrument_economics must be InstrumentEconomics"):
        simulate_action_execution(action, (), assumptions, "bad")  # type: ignore[arg-type]


def test_capacity_rejection() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    policy = ExecutionPolicy(small_lot_max_quantity=Decimal("5"))
    assumptions = EconomicAssumptions(
        "test_a",
        SpreadModel(),
        ZeroSlippageModel(),
        FeeSchedule("fee"),
        LatencyModel(),
        policy,
    )
    t = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    action = BacktestAction(
        ActionIdentity(make_uuid(2)),
        iid,
        Side.BUY,
        Decimal("10"),  # exceeds 5
        OrderStyle.MARKET,
        t,
        t,
        t,
    )

    fill = simulate_action_execution(action, (), assumptions, econ)
    assert fill.outcome == ExecutionOutcome.REJECTED
    assert fill.reason == "EXCEEDS_SMALL_LOT_CAPACITY"


def test_no_fill_when_no_eligible_events() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        "test_a",
        SpreadModel(),
        ZeroSlippageModel(),
        FeeSchedule("fee"),
        LatencyModel(transit_latency_us=5000),
        ExecutionPolicy(),
    )
    t_action = datetime(2026, 9, 16, 10, 0, 0, 10000, tzinfo=UTC)
    action = BacktestAction(
        ActionIdentity(make_uuid(2)),
        iid,
        Side.BUY,
        Decimal("1"),
        OrderStyle.MARKET,
        t_action,
        t_action,
        t_action,
    )

    # Event 1 is before arrival
    t_early = datetime(2026, 9, 16, 10, 0, 0, 12000, tzinfo=UTC)  # arrival is 15000us
    ev1 = make_event(
        10,
        t_early,
        iid,
        Tick(Decimal("100.0"), Decimal("100.5"), Decimal("100.2"), Decimal("1")),
    )

    fill = simulate_action_execution(action, (ev1,), assumptions, econ)
    assert fill.outcome == ExecutionOutcome.NO_FILL
    assert fill.reason == "NO_MARKET_EVENT_AFTER_ARRIVAL"


def test_stale_quote_rejection() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    policy = ExecutionPolicy(max_quote_age_us=1000)
    assumptions = EconomicAssumptions(
        "test_a",
        SpreadModel(),
        ZeroSlippageModel(),
        FeeSchedule("fee"),
        LatencyModel(),
        policy,
    )
    t_action = datetime(2026, 9, 16, 10, 0, 0, 0, tzinfo=UTC)
    action = BacktestAction(
        ActionIdentity(make_uuid(2)),
        iid,
        Side.BUY,
        Decimal("1"),
        OrderStyle.MARKET,
        t_action,
        t_action,
        t_action,
    )

    # Event is 5000us later, exceeds max_quote_age_us=1000
    t_late = datetime(2026, 9, 16, 10, 0, 0, 5000, tzinfo=UTC)
    ev = make_event(
        10,
        t_late,
        iid,
        Tick(Decimal("100.0"), Decimal("100.5"), Decimal("100.2"), Decimal("1")),
    )

    fill = simulate_action_execution(action, (ev,), assumptions, econ)
    assert fill.outcome == ExecutionOutcome.INDETERMINATE
    assert fill.reason == "NO_EXECUTION_EVIDENCE_WITHIN_WAIT_WINDOW"

    # Fresh quote under max_quote_age_us (delta = 500us < 1000us)
    t_fresh = datetime(2026, 9, 16, 10, 0, 0, 500, tzinfo=UTC)
    ev_fresh = make_event(
        11,
        t_fresh,
        iid,
        Tick(Decimal("100.0"), Decimal("100.5"), Decimal("100.2"), Decimal("1")),
    )
    fill_fresh = simulate_action_execution(action, (ev_fresh,), assumptions, econ)
    assert fill_fresh.outcome == ExecutionOutcome.FILL


def test_missing_quote_or_spread_rejection() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        "test_a",
        SpreadModel(require_positive_spread=True),
        ZeroSlippageModel(),
        FeeSchedule("fee"),
        LatencyModel(),
        ExecutionPolicy(),
    )
    t = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    action = BacktestAction(
        ActionIdentity(make_uuid(2)),
        iid,
        Side.BUY,
        Decimal("1"),
        OrderStyle.MARKET,
        t,
        t,
        t,
    )

    # 1. Missing bid
    ev_missing = make_event(
        10,
        t,
        iid,
        Tick(MissingReason.NOT_PROVIDED, Decimal("100.5"), Decimal("100.2"), Decimal("1")),
    )
    fill1 = simulate_action_execution(action, (ev_missing,), assumptions, econ)
    assert fill1.outcome == ExecutionOutcome.INDETERMINATE
    assert fill1.reason == "MISSING_BID_ASK_DATA"

    # 2. Zero spread (ask == bid) with require_positive_spread=True
    ev_zero_spread = make_event(
        11,
        t,
        iid,
        Tick(Decimal("100.0"), Decimal("100.0"), Decimal("100.0"), Decimal("1")),
    )
    fill2 = simulate_action_execution(action, (ev_zero_spread,), assumptions, econ)
    assert fill2.outcome == ExecutionOutcome.INDETERMINATE
    assert "SPREAD_REJECTED_NON_POSITIVE_SPREAD" in fill2.reason


def test_successful_market_tick_fill() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("2.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        "test_a",
        SpreadModel(),
        FixedPointsSlippageModel(adverse_points=Decimal("0.5")),
        FeeSchedule("fee", fixed_per_order=Decimal("1.0"), per_unit=Decimal("0.5")),
        LatencyModel(decision_latency_us=1000, transit_latency_us=2000),
        ExecutionPolicy(),
    )
    t0 = datetime(2026, 9, 16, 10, 0, 0, 0, tzinfo=UTC)
    action_buy = BacktestAction(
        ActionIdentity(make_uuid(2)),
        iid,
        Side.BUY,
        Decimal("2"),
        OrderStyle.MARKET,
        t0,
        t0,
        t0,
    )
    action_sell = BacktestAction(
        ActionIdentity(make_uuid(3)),
        iid,
        Side.SELL,
        Decimal("2"),
        OrderStyle.MARKET,
        t0,
        t0,
        t0,
    )

    # Replay event at 3000us
    t_ev = datetime(2026, 9, 16, 10, 0, 0, 3000, tzinfo=UTC)
    ev = make_event(
        10,
        t_ev,
        iid,
        Tick(Decimal("100.0"), Decimal("101.0"), Decimal("100.5"), Decimal("1")),
    )

    # BUY consumes Ask (101.0) + slippage (0.5) = 101.5
    # Fee: fixed 1.0 + unit 0.5*2 = 2.0
    fill_buy = simulate_action_execution(action_buy, (ev,), assumptions, econ)
    assert fill_buy.outcome == ExecutionOutcome.FILL
    assert fill_buy.raw_price == Decimal("101.0")
    assert fill_buy.fill_price == Decimal("101.5")
    assert fill_buy.slippage == Decimal("0.5")
    assert fill_buy.explicit_fee == Decimal("2.0")
    assert fill_buy.source_event_id == ev.event_id
    assert fill_buy.reason == "FILLED_AT_MARKET"

    # SELL consumes Bid (100.0) - slippage (0.5) = 99.5
    fill_sell = simulate_action_execution(action_sell, (ev,), assumptions, econ)
    assert fill_sell.outcome == ExecutionOutcome.FILL
    assert fill_sell.raw_price == Decimal("100.0")
    assert fill_sell.fill_price == Decimal("99.5")
    assert fill_sell.slippage == Decimal("0.5")


def test_candle_execution_handling() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 1, 0, tzinfo=UTC)

    action = BacktestAction(
        ActionIdentity(make_uuid(2)),
        iid,
        Side.BUY,
        Decimal("1"),
        OrderStyle.MARKET,
        t0,
        t0,
        t0,
    )

    candle = Candle(
        interval_start=t0,
        interval_end=t1,
        finality=CandleFinality.FINAL,
        finalized_at=t1,
        available_at=t1,
        open=Decimal("100.0"),
        high=Decimal("105.0"),
        low=Decimal("99.0"),
        close=Decimal("103.0"),
        volume=Decimal("100"),
    )
    ev_candle = make_event(20, t1, iid, candle, event_type=EventType.CANDLE)

    # 1. Default policy (allow_candle_fills=False) -> INDETERMINATE
    assumptions_default = EconomicAssumptions(
        "test_a",
        SpreadModel(),
        ZeroSlippageModel(),
        FeeSchedule("fee"),
        LatencyModel(),
        ExecutionPolicy(allow_candle_fills=False),
    )
    fill1 = simulate_action_execution(action, (ev_candle,), assumptions_default, econ)
    assert fill1.outcome == ExecutionOutcome.INDETERMINATE
    assert fill1.reason == "CANDLE_EXECUTION_PATH_UNSUPPORTED"

    # 2. Even when allow_candle_fills=True -> precise execution is deferred, returns INDETERMINATE
    assumptions_allowed = EconomicAssumptions(
        "test_a",
        SpreadModel(),
        ZeroSlippageModel(),
        FeeSchedule("fee"),
        LatencyModel(),
        ExecutionPolicy(allow_candle_fills=True),
    )
    fill2 = simulate_action_execution(action, (ev_candle,), assumptions_allowed, econ)
    assert fill2.outcome == ExecutionOutcome.INDETERMINATE
    assert fill2.reason == "CANDLE_EXECUTION_PATH_UNSUPPORTED"

    # 3. Missing candle open also results in INDETERMINATE
    candle_no_open = Candle(
        interval_start=t0,
        interval_end=t1,
        finality=CandleFinality.FINAL,
        finalized_at=t1,
        available_at=t1,
        open=MissingReason.NOT_PROVIDED,
        high=Decimal("105.0"),
        low=Decimal("99.0"),
        close=Decimal("103.0"),
        volume=Decimal("100"),
    )
    ev_no_open = make_event(21, t1, iid, candle_no_open, event_type=EventType.CANDLE)
    fill3 = simulate_action_execution(action, (ev_no_open,), assumptions_allowed, econ)
    assert fill3.outcome == ExecutionOutcome.INDETERMINATE
    assert fill3.reason == "CANDLE_EXECUTION_PATH_UNSUPPORTED"


def test_simulate_actions_batch() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        "test_a",
        SpreadModel(),
        ZeroSlippageModel(),
        FeeSchedule("fee"),
        LatencyModel(),
        ExecutionPolicy(),
    )
    t = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    a1 = BacktestAction(
        ActionIdentity(make_uuid(2)),
        iid,
        Side.BUY,
        Decimal("1"),
        OrderStyle.MARKET,
        t,
        t,
        t,
    )
    a2 = BacktestAction(
        ActionIdentity(make_uuid(3)),
        iid,
        Side.SELL,
        Decimal("1"),
        OrderStyle.MARKET,
        t,
        t,
        t,
    )

    ev = make_event(
        10,
        t,
        iid,
        Tick(Decimal("100.0"), Decimal("100.5"), Decimal("100.2"), Decimal("1")),
    )

    results = simulate_actions((a1, a2), (ev,), assumptions, econ)
    assert len(results) == 2
    assert results[0].side == Side.BUY
    assert results[0].outcome == ExecutionOutcome.FILL
    assert results[1].side == Side.SELL
    assert results[1].outcome == ExecutionOutcome.FILL


def test_unsupported_event_payload_and_skipping() -> None:
    iid1 = TradableInstrumentId(make_uuid(1))
    iid2 = TradableInstrumentId(make_uuid(2))
    econ = InstrumentEconomics(iid1, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        "test_a",
        SpreadModel(),
        ZeroSlippageModel(),
        FeeSchedule("fee"),
        LatencyModel(),
        ExecutionPolicy(),
    )
    t = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    action = BacktestAction(
        ActionIdentity(make_uuid(3)),
        iid1,
        Side.BUY,
        Decimal("1"),
        OrderStyle.MARKET,
        t,
        t,
        t,
    )

    # Event for different instrument (should be skipped)
    ev_other = make_event(
        10,
        t,
        iid2,
        Tick(Decimal("100.0"), Decimal("100.5"), Decimal("100.2"), Decimal("1")),
    )
    # Event with missing knowledge_time (should be skipped)
    ev_no_kt = make_event(
        11,
        MissingReason.UNKNOWN,
        iid1,
        Tick(Decimal("100.0"), Decimal("100.5"), Decimal("100.2"), Decimal("1")),
    )

    fill = simulate_action_execution(action, (ev_other, ev_no_kt), assumptions, econ)
    assert fill.outcome == ExecutionOutcome.NO_FILL


def test_unsupported_payload_type() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        "test_a",
        SpreadModel(),
        ZeroSlippageModel(),
        FeeSchedule("fee"),
        LatencyModel(),
        ExecutionPolicy(),
    )
    t = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    action = BacktestAction(
        ActionIdentity(make_uuid(2)),
        iid,
        Side.BUY,
        Decimal("1"),
        OrderStyle.MARKET,
        t,
        t,
        t,
    )

    class DummyEvent:
        def __init__(self) -> None:
            self.instrument_id = iid
            self.times = ObservationTimes(
                event_time=EventTime(t, "c", timedelta(microseconds=1)),
                ingestion_time=t,
                knowledge_time=t,
            )
            self.event_type = "UNSUPPORTED"
            self.payload = "raw"
            self.event_id = EventId(make_uuid(99))

    ev = DummyEvent()

    fill = simulate_action_execution(action, (ev,), assumptions, econ)  # type: ignore[arg-type]
    assert fill.outcome == ExecutionOutcome.INDETERMINATE
    assert fill.reason == "UNSUPPORTED_EVENT_PAYLOAD"
