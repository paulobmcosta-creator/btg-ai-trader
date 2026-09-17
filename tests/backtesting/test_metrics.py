"""Unit tests for descriptive economic metrics computation."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from btg_ai_trader.backtesting.accounting import (
    BacktestEconomicState,
    BacktestPnL,
    BacktestPositionState,
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
from btg_ai_trader.backtesting.metrics import compute_descriptive_metrics
from btg_ai_trader.observer.identity import EventId, TradableInstrumentId


def make_uuid(num: int = 1) -> str:
    return str(UUID(int=num))


def make_action(iid: TradableInstrumentId, side: Side, qty: Decimal) -> BacktestAction:
    t = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    return BacktestAction(
        action_id=ActionIdentity(make_uuid(10)),
        instrument_id=iid,
        side=side,
        quantity=qty,
        order_style=OrderStyle.MARKET,
        knowledge_cutoff=t,
        decision_time=t,
        order_ready_time=t,
    )


def make_fill(
    iid: TradableInstrumentId,
    side: Side,
    qty: Decimal,
    price: Decimal,
    outcome: ExecutionOutcome = ExecutionOutcome.FILL,
    fee: Decimal = Decimal("0"),
    slippage: Decimal = Decimal("0"),
    source_event_id: EventId | None = None,
) -> SimulatedFill:
    t = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    timing = ExecutionTiming(t, t, t, t, t)
    if outcome != ExecutionOutcome.FILL:
        resolved_qty = Decimal("0")
        resolved_raw = Decimal("0")
        resolved_fill = Decimal("0")
        resolved_slip = Decimal("0")
        resolved_fee = Decimal("0")
        ev_id = None
    else:
        resolved_qty = qty
        resolved_raw = price
        resolved_fill = price
        resolved_slip = slippage
        resolved_fee = fee
        ev_id = source_event_id if source_event_id is not None else EventId(make_uuid(999))

    return SimulatedFill(
        fill_id=ActionIdentity(make_uuid(100)),
        action_id=ActionIdentity(make_uuid(200)),
        instrument_id=iid,
        side=side,
        quantity=resolved_qty,
        raw_price=resolved_raw,
        fill_price=resolved_fill,
        slippage=resolved_slip,
        explicit_fee=resolved_fee,
        timing=timing,
        outcome=outcome,
        source_event_id=ev_id,
    )


def test_compute_descriptive_metrics_empty() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    state = BacktestEconomicState.initial(econ)

    metrics = compute_descriptive_metrics(
        actions=(),
        fills=(),
        economic_state=state,
        instrument_economics=econ,
    )

    assert metrics.total_actions == 0
    assert metrics.fill_count == 0
    assert metrics.fill_rate == Decimal("0")
    assert metrics.turnover == Decimal("0")
    assert metrics.closed_trade_count == 0
    assert metrics.winning_trade_count == 0
    assert metrics.losing_trade_count == 0
    assert metrics.breakeven_trade_count == 0
    assert metrics.hit_rate == Decimal("0")
    assert metrics.average_win == Decimal("0")
    assert metrics.average_loss == Decimal("0")
    assert metrics.profit_factor == Decimal("0")
    assert metrics.expectancy == Decimal("0")
    assert metrics.max_drawdown_amount == Decimal("0")
    assert metrics.max_drawdown_ratio is None


def test_compute_descriptive_metrics_full_trade_lifecycle() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))

    # Actions: 6 actions
    actions = [
        make_action(iid, Side.BUY, Decimal("10")),
        make_action(iid, Side.SELL, Decimal("5")),
        make_action(iid, Side.SELL, Decimal("5")),
        make_action(iid, Side.BUY, Decimal("5")),
        make_action(iid, Side.SELL, Decimal("5")),
        make_action(iid, Side.BUY, Decimal("5")),
    ]

    # Fills:
    # 1. BUY 10 @ 100
    # 2. SELL 5 @ 120 -> gain 100 (win)
    # 3. SELL 5 @ 80 -> loss 100 (loss)
    # 4. BUY 5 @ 100
    # 5. SELL 5 @ 100 -> gain 0 (breakeven)
    # 6. Rejected fill
    f1 = make_fill(iid, Side.BUY, Decimal("10"), Decimal("100.0"))
    f2 = make_fill(iid, Side.SELL, Decimal("5"), Decimal("120.0"))
    f3 = make_fill(iid, Side.SELL, Decimal("5"), Decimal("80.0"))
    f4 = make_fill(iid, Side.BUY, Decimal("5"), Decimal("100.0"))
    f5 = make_fill(iid, Side.SELL, Decimal("5"), Decimal("100.0"))
    f6 = make_fill(iid, Side.BUY, Decimal("5"), Decimal("100.0"), outcome=ExecutionOutcome.REJECTED)
    f7 = make_fill(iid, Side.BUY, Decimal("1"), Decimal("100.0"), outcome=ExecutionOutcome.NO_FILL)
    f8 = make_fill(
        iid, Side.BUY, Decimal("1"), Decimal("100.0"), outcome=ExecutionOutcome.INDETERMINATE
    )

    state = BacktestEconomicState.initial(econ)
    state = state.apply_fills((f1, f2, f3, f4, f5, f6, f7, f8))

    metrics = compute_descriptive_metrics(
        actions=actions,
        fills=(f1, f2, f3, f4, f5, f6, f7, f8),
        economic_state=state,
        instrument_economics=econ,
    )

    assert metrics.total_actions == 6
    assert metrics.fill_count == 5
    assert metrics.no_fill_count == 1
    assert metrics.indeterminate_count == 1
    assert metrics.rejected_count == 1
    assert metrics.fill_rate == Decimal("5") / Decimal("6")
    # Turnover = 10*100 + 5*120 + 5*80 + 5*100 + 5*100 = 1000 + 600 + 400 + 500 + 500 = 3000
    assert metrics.turnover == Decimal("3000.0")

    assert metrics.closed_trade_count == 3
    assert metrics.winning_trade_count == 1
    assert metrics.losing_trade_count == 1
    assert metrics.breakeven_trade_count == 1
    assert metrics.hit_rate == Decimal("1") / Decimal("3")
    assert metrics.average_win == Decimal("100.0")
    assert metrics.average_loss == Decimal("100.0")
    assert metrics.profit_factor == Decimal("1.0")


def test_metrics_profit_factor_infinity_and_drawdown_ratio() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))

    # Only winning trades
    f1 = make_fill(iid, Side.BUY, Decimal("10"), Decimal("100.0"))
    f2 = make_fill(iid, Side.SELL, Decimal("10"), Decimal("150.0"))

    state = BacktestEconomicState.initial(econ)
    state = state.apply_fills((f1, f2))

    metrics = compute_descriptive_metrics(
        actions=[
            make_action(iid, Side.BUY, Decimal("10")),
            make_action(iid, Side.SELL, Decimal("10")),
        ],
        fills=(f1, f2),
        economic_state=state,
        instrument_economics=econ,
    )

    assert metrics.winning_trade_count == 1
    assert metrics.losing_trade_count == 0
    assert metrics.profit_factor == Decimal("Infinity")


def test_metrics_short_accumulation_and_cover() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("2.0"), Decimal("0.5"), Decimal("1.0"))

    # 1. Short 5 @ 100
    # 2. Short 5 more @ 110 -> basis = 105, qty = -10
    # 3. Buy 15 @ 95 -> covers 10 (gain = (105 - 95)*10*2 = 200), goes long 5 @ 95
    f1 = make_fill(iid, Side.SELL, Decimal("5"), Decimal("100.0"))
    f2 = make_fill(iid, Side.SELL, Decimal("5"), Decimal("110.0"))
    f3 = make_fill(iid, Side.BUY, Decimal("15"), Decimal("95.0"))

    state = BacktestEconomicState.initial(econ)
    state = state.apply_fills((f1, f2, f3))

    metrics = compute_descriptive_metrics(
        actions=[],
        fills=(f1, f2, f3),
        economic_state=state,
        instrument_economics=econ,
    )

    assert metrics.closed_trade_count == 1
    assert metrics.winning_trade_count == 1
    assert metrics.average_win == Decimal("200.0")


def test_metrics_negative_equity_curve_drawdown() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))

    # Simulated state where equity curve is always non-positive (peak stays 0)
    pos = BacktestPositionState(instrument_id=iid)
    pnl = BacktestPnL(
        gross_realized_pnl=Decimal("-100"),
        explicit_fees=Decimal("0"),
        net_realized_pnl=Decimal("-100"),
        diagnostic_slippage_burden=Decimal("0"),
    )
    # Peak is 0, drops to -50, then -100
    state = BacktestEconomicState(
        positions=(pos,),
        pnl=pnl,
        realized_equity_curve=(Decimal("-50"), Decimal("-100")),
        fills=(),
    )

    metrics = compute_descriptive_metrics(
        actions=[],
        fills=(),
        economic_state=state,
        instrument_economics=econ,
    )

    assert metrics.max_drawdown_amount == Decimal("100")
    # Peak is 0, so max_dd_ratio is not calculated and is None (no positive denominator)
    assert metrics.max_drawdown_ratio is None
