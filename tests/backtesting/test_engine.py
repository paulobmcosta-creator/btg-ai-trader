"""Unit tests for the Deterministic Economic Backtesting Engine."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest

from btg_ai_trader.backtesting.accounting import (
    BacktestEconomicState,
    EndOfWindowPolicy,
)
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
    InstrumentEconomics,
    OrderStyle,
    Side,
)
from btg_ai_trader.backtesting.engine import (
    BacktestResult,
    DeterministicEconomicBacktester,
)
from btg_ai_trader.backtesting.metrics import DescriptiveBacktestMetrics
from btg_ai_trader.backtesting.provenance import BacktestInputBoundary, BacktestRunManifest
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


def make_tick_event(
    seq: int,
    ts: datetime,
    iid: TradableInstrumentId,
    bid: Decimal = Decimal("100.0"),
    ask: Decimal = Decimal("100.5"),
    last: Decimal = Decimal("100.2"),
) -> EventEnvelope:
    payload = Tick(
        bid=bid,
        ask=ask,
        last=last,
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


def make_candle_event(
    seq: int,
    ts: datetime,
    iid: TradableInstrumentId,
    close: Decimal = Decimal("105.0"),
) -> EventEnvelope:
    high = max(Decimal("106.0"), close + Decimal("1.0"))
    low = min(Decimal("99.0"), close - Decimal("1.0"))
    candle = Candle(
        interval_start=ts - timedelta(minutes=1),
        interval_end=ts,
        finality=CandleFinality.FINAL,
        finalized_at=ts,
        available_at=ts,
        open=Decimal("100.0"),
        high=high,
        low=low,
        close=close,
        volume=Decimal("100"),
    )
    event_time = EventTime(ts, "fixture-clock", timedelta(microseconds=1))
    return EventEnvelope(
        event_id=EventId(make_uuid(200 + seq)),
        event_type=EventType.CANDLE,
        source=ProviderInstrumentRef("xp", "market", "WINV26"),
        instrument_id=iid,
        times=ObservationTimes(
            event_time=event_time,
            ingestion_time=ts,
            knowledge_time=ts,
        ),
        payload=candle,
    )


def make_action(
    action_num: int,
    ts: datetime,
    iid: TradableInstrumentId,
    side: Side = Side.BUY,
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


def test_engine_initialization_and_result_validation() -> None:
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

    with pytest.raises(ValueError, match="instrument_economics must be InstrumentEconomics"):
        DeterministicEconomicBacktester("bad", assumptions)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="assumptions must be EconomicAssumptions"):
        DeterministicEconomicBacktester(econ, "bad")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="end_of_window_policy must be EndOfWindowPolicy enum"):
        DeterministicEconomicBacktester(econ, assumptions, "bad")  # type: ignore[arg-type]

    # Result validation
    boundary = BacktestInputBoundary.create([], [])
    manifest = BacktestRunManifest.create(
        run_id=ActionIdentity(make_uuid(10)),
        input_boundary=boundary,
        assumptions=assumptions,
        instrument_id=iid,
        metrics=DescriptiveBacktestMetrics(
            gross_realized_pnl=Decimal("0"),
            net_realized_pnl=Decimal("0"),
            total_explicit_fees=Decimal("0"),
            diagnostic_slippage_burden=Decimal("0"),
            turnover=Decimal("0"),
            total_actions=0,
            fill_count=0,
            no_fill_count=0,
            indeterminate_count=0,
            rejected_count=0,
            fill_rate=Decimal("0"),
            closed_trade_count=0,
            winning_trade_count=0,
            losing_trade_count=0,
            breakeven_trade_count=0,
            hit_rate=Decimal("0"),
            average_win=Decimal("0"),
            average_loss=Decimal("0"),
            profit_factor=Decimal("0"),
            expectancy=Decimal("0"),
            max_drawdown_amount=Decimal("0"),
            max_drawdown_ratio=Decimal("0"),
        ),
    )
    state = BacktestEconomicState.initial(econ)
    metrics = manifest.metrics

    with pytest.raises(ValueError, match="manifest must be BacktestRunManifest"):
        BacktestResult("bad", state, metrics, ())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="economic_state must be BacktestEconomicState"):
        BacktestResult(manifest, "bad", metrics, ())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="metrics must be DescriptiveBacktestMetrics"):
        BacktestResult(manifest, state, "bad", ())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="fills must be a tuple"):
        BacktestResult(manifest, state, metrics, [])  # type: ignore[arg-type]


def test_engine_empty_run_and_mismatched_instrument() -> None:
    iid1 = TradableInstrumentId(make_uuid(1))
    iid2 = TradableInstrumentId(make_uuid(2))
    econ = InstrumentEconomics(iid1, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        assumptions_id="base",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule("fee"),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )
    engine = DeterministicEconomicBacktester(econ, assumptions)

    # Empty run
    res = engine.run(actions=[], market_events=[], session_id="test-session")
    assert res.metrics.total_actions == 0
    assert len(res.fills) == 0
    assert res.manifest.verify_integrity()

    # Mismatched instrument action
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    bad_action = make_action(1, t0, iid2)
    with pytest.raises(ValueError, match="does not match engine instrument"):
        engine.run(actions=[bad_action], market_events=[])


def test_engine_full_lifecycle_and_session_determinism() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("2.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        assumptions_id="base",
        spread_model=SpreadModel(),
        slippage_model=FixedPointsSlippageModel(adverse_points=Decimal("0.5")),
        fee_schedule=FeeSchedule(schedule_id="fee", fixed_per_order=Decimal("5.0")),
        latency_model=LatencyModel(decision_latency_us=100, transit_latency_us=200),
        execution_policy=ExecutionPolicy(),
    )
    engine = DeterministicEconomicBacktester(econ, assumptions)

    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)

    # Action 1: Buy 10 @ t0 -> arrives at t0 + 300us
    # Action 2: Sell 10 @ t1 -> arrives at t1 + 300us
    a1 = make_action(1, t0, iid, Side.BUY, Decimal("10"))
    a2 = make_action(2, t1, iid, Side.SELL, Decimal("10"))

    # Event 1 at t0 + 500us: Ask = 100.0 -> BUY filled at 100.0 + 0.5 (slip) = 100.5
    # Event 2 at t1 + 500us: Bid = 110.0 -> SELL filled at 110.0 - 0.5 (slip) = 109.5
    e1 = make_tick_event(
        1, t0 + timedelta(microseconds=500), iid, bid=Decimal("99.5"), ask=Decimal("100.0")
    )
    e2 = make_tick_event(
        2, t1 + timedelta(microseconds=500), iid, bid=Decimal("110.0"), ask=Decimal("110.5")
    )

    res1 = engine.run([a1, a2], [e1, e2], session_id="fixed-seed-1")
    res2 = engine.run([a1, a2], [e1, e2], session_id="fixed-seed-1")

    # Byte-for-byte identical manifest and hash
    assert res1.manifest.manifest_hash == res2.manifest.manifest_hash
    assert res1.manifest.run_id == res2.manifest.run_id
    assert res1.manifest.to_json() == res2.manifest.to_json()

    # Economic validation:
    # BUY: 10 units @ 100.5, fee = 5
    # SELL: 10 units @ 109.5, fee = 5
    # Gross realized = (109.5 - 100.5) * 10 * 2 = 9.0 * 20 = 180.0
    # Fees = 10.0
    # Net realized = 170.0
    assert res1.metrics.gross_realized_pnl == Decimal("180.0")
    assert res1.metrics.total_explicit_fees == Decimal("10.0")
    assert res1.metrics.net_realized_pnl == Decimal("170.0")
    assert res1.economic_state.positions[0].is_flat


def test_engine_end_of_window_policy_close_long_and_short() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        assumptions_id="base",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule(schedule_id="fee"),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )

    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)

    # 1. Long position left open, policy = CLOSE_AT_LAST_VALID_QUOTE
    engine_close = DeterministicEconomicBacktester(
        econ,
        assumptions,
        end_of_window_policy=EndOfWindowPolicy.CLOSE_AT_LAST_VALID_QUOTE,
    )
    a_buy = make_action(1, t0, iid, Side.BUY, Decimal("10"))
    e1 = make_tick_event(1, t0, iid, bid=Decimal("100.0"), ask=Decimal("101.0"))
    e2 = make_tick_event(2, t1, iid, bid=Decimal("105.0"), ask=Decimal("106.0"))

    res_long = engine_close.run([a_buy], [e1, e2])
    assert len(res_long.fills) == 2  # Original buy + synthetic close
    assert res_long.fills[1].side == Side.SELL
    assert res_long.fills[1].quantity == Decimal("10")
    assert res_long.fills[1].fill_price == Decimal("105.0")  # Closing long takes bid (105.0)
    assert res_long.economic_state.positions[0].is_flat
    assert res_long.metrics.gross_realized_pnl == Decimal("40.0")  # (105 - 101)*10

    # 2. Short position left open, policy = CLOSE_AT_LAST_VALID_QUOTE
    a_sell = make_action(2, t0, iid, Side.SELL, Decimal("10"))
    res_short = engine_close.run([a_sell], [e1, e2])
    assert len(res_short.fills) == 2
    assert res_short.fills[1].side == Side.BUY
    assert res_short.fills[1].fill_price == Decimal("106.0")  # Closing short takes ask (106.0)
    assert res_short.economic_state.positions[0].is_flat

    # 3. Policy = KEEP_OPEN -> position stays open, marked to market
    engine_keep = DeterministicEconomicBacktester(
        econ,
        assumptions,
        end_of_window_policy=EndOfWindowPolicy.KEEP_OPEN,
    )
    res_keep = engine_keep.run([a_buy], [e1, e2])
    assert len(res_keep.fills) == 1
    assert res_keep.economic_state.positions[0].is_long
    # Marked to market using mid price of e2: (105 + 106)/2 = 105.5
    # Unrealized = (105.5 - 101)*10 = 45.0
    assert res_keep.economic_state.pnl.unrealized_pnl == Decimal("45.0")


def test_engine_mark_prices_variations() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        assumptions_id="base",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule(schedule_id="fee"),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )
    engine = DeterministicEconomicBacktester(econ, assumptions)

    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)
    a_buy = make_action(1, t0, iid, Side.BUY, Decimal("5"))

    # Candle event gives close price for mark to market
    e_candle = make_candle_event(1, t1, iid, close=Decimal("110.0"))
    e_tick_entry = make_tick_event(1, t0, iid, bid=Decimal("99.5"), ask=Decimal("100.0"))
    res_candle = engine.run([a_buy], [e_tick_entry, e_candle])
    assert res_candle.economic_state.pnl.unrealized_pnl == Decimal("50.0")  # (110 - 100)*5

    # Tick event with only last price
    payload_last_only = Tick(
        bid=MissingReason.NOT_PROVIDED,
        ask=MissingReason.NOT_PROVIDED,
        last=Decimal("112.0"),
        volume=Decimal("10"),
    )
    event_time = EventTime(t1, "fixture-clock", timedelta(microseconds=1))
    e_last = EventEnvelope(
        event_id=EventId(make_uuid(99)),
        event_type=EventType.TICK,
        source=ProviderInstrumentRef("xp", "market", "WINV26"),
        instrument_id=iid,
        times=ObservationTimes(event_time=event_time, ingestion_time=t1, knowledge_time=t1),
        payload=payload_last_only,
    )
    res_last = engine.run([a_buy], [e_tick_entry, e_last])
    assert res_last.economic_state.pnl.unrealized_pnl == Decimal("60.0")  # (112 - 100)*5


def test_engine_edge_cases_coverage() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        assumptions_id="base",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule(schedule_id="fee"),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )
    engine = DeterministicEconomicBacktester(
        econ,
        assumptions,
        end_of_window_policy=EndOfWindowPolicy.CLOSE_AT_LAST_VALID_QUOTE,
    )

    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t_custom = datetime(2026, 9, 16, 12, 0, 0, tzinfo=UTC)
    a_buy = make_action(1, t0, iid, Side.BUY, Decimal("5"))

    # Explicit created_at
    res_custom = engine.run([], [], created_at=t_custom)
    assert res_custom.manifest.created_at == t_custom

    # Event with missing bid & missing ask (only volume)
    payload_empty = Tick(
        bid=MissingReason.NOT_PROVIDED,
        ask=MissingReason.NOT_PROVIDED,
        last=MissingReason.NOT_PROVIDED,
        volume=Decimal("10"),
    )
    event_time = EventTime(t0, "fixture-clock", timedelta(microseconds=1))
    e_empty = EventEnvelope(
        event_id=EventId(make_uuid(99)),
        event_type=EventType.TICK,
        source=ProviderInstrumentRef("xp", "market", "WINV26"),
        instrument_id=iid,
        times=ObservationTimes(event_time=event_time, ingestion_time=t0, knowledge_time=t0),
        payload=payload_empty,
    )

    # Candle with missing close
    candle_missing_close = Candle(
        interval_start=t0 - timedelta(minutes=1),
        interval_end=t0,
        finality=CandleFinality.FINAL,
        finalized_at=t0,
        available_at=t0,
        open=Decimal("100.0"),
        high=Decimal("105.0"),
        low=Decimal("95.0"),
        close=MissingReason.NOT_PROVIDED,
        volume=Decimal("100"),
    )
    e_candle_missing = EventEnvelope(
        event_id=EventId(make_uuid(98)),
        event_type=EventType.CANDLE,
        source=ProviderInstrumentRef("xp", "market", "WINV26"),
        instrument_id=iid,
        times=ObservationTimes(event_time=event_time, ingestion_time=t0, knowledge_time=t0),
        payload=candle_missing_close,
    )

    # Policy CLOSE_AT_LAST_VALID_QUOTE when position is open but events has NO valid quote to close
    # We can test _find_last_quote_price directly:
    assert engine._find_last_quote_price([e_empty], is_closing_long=True) is None
    assert engine._find_last_quote_price([e_empty], is_closing_long=False) is None
    assert engine._find_latest_mark_price([e_empty, e_candle_missing]) is None

    # Candle fill with no tick quotes available: fills on candle, but cannot close via quotes
    assumptions_candle = EconomicAssumptions(
        assumptions_id="candle_assump",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule(schedule_id="fee"),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(allow_candle_fills=True),
    )
    engine_candle = DeterministicEconomicBacktester(
        econ,
        assumptions_candle,
        end_of_window_policy=EndOfWindowPolicy.CLOSE_AT_LAST_VALID_QUOTE,
    )
    e_candle_valid = make_candle_event(1, t0, iid, close=Decimal("100.0"))
    res_candle_open = engine_candle.run([a_buy], [e_candle_valid])
    assert len(res_candle_open.fills) == 1
    assert res_candle_open.economic_state.positions[0].is_long
