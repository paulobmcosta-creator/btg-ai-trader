"""Unit tests for backtesting domain models."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

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
from btg_ai_trader.observer.identity import EventId, TradableInstrumentId


def make_uuid() -> str:
    return str(uuid4())


def test_action_identity_valid() -> None:
    val = make_uuid()
    ident = ActionIdentity(val)
    assert ident.value == val


def test_action_identity_invalid_types() -> None:
    with pytest.raises(ValueError, match="canonical UUID text"):
        ActionIdentity(123)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="canonical UUID text"):
        ActionIdentity("not-a-uuid")

    val = make_uuid().upper()
    with pytest.raises(ValueError, match="lowercase hyphenated UUID text"):
        ActionIdentity(val)


def test_instrument_economics_valid() -> None:
    inst_id = TradableInstrumentId(make_uuid())
    econ = InstrumentEconomics(
        instrument_id=inst_id,
        currency="BRL",
        money_per_price_unit=Decimal("1.0"),
        tick_size=Decimal("0.5"),
        quantity_step=Decimal("1.0"),
    )
    assert econ.currency == "BRL"
    assert econ.money_per_price_unit == Decimal("1.0")


def test_instrument_economics_invalid() -> None:
    inst_id = TradableInstrumentId(make_uuid())
    with pytest.raises(ValueError, match="TradableInstrumentId"):
        InstrumentEconomics(
            instrument_id="bad",  # type: ignore[arg-type]
            currency="BRL",
            money_per_price_unit=Decimal("1.0"),
            tick_size=Decimal("0.5"),
            quantity_step=Decimal("1.0"),
        )

    with pytest.raises(ValueError, match="money_per_price_unit must be Decimal"):
        InstrumentEconomics(
            instrument_id=inst_id,
            currency="BRL",
            money_per_price_unit=1.0,  # type: ignore[arg-type]
            tick_size=Decimal("0.5"),
            quantity_step=Decimal("1.0"),
        )

    with pytest.raises(ValueError, match="money_per_price_unit must be positive"):
        InstrumentEconomics(
            instrument_id=inst_id,
            currency="BRL",
            money_per_price_unit=Decimal("0.0"),
            tick_size=Decimal("0.5"),
            quantity_step=Decimal("1.0"),
        )

    with pytest.raises(ValueError, match="tick_size must be Decimal"):
        InstrumentEconomics(
            instrument_id=inst_id,
            currency="BRL",
            money_per_price_unit=Decimal("1.0"),
            tick_size=0.5,  # type: ignore[arg-type]
            quantity_step=Decimal("1.0"),
        )

    with pytest.raises(ValueError, match="tick_size must be positive"):
        InstrumentEconomics(
            instrument_id=inst_id,
            currency="BRL",
            money_per_price_unit=Decimal("1.0"),
            tick_size=Decimal("-0.5"),
            quantity_step=Decimal("1.0"),
        )

    with pytest.raises(ValueError, match="quantity_step must be Decimal"):
        InstrumentEconomics(
            instrument_id=inst_id,
            currency="BRL",
            money_per_price_unit=Decimal("1.0"),
            tick_size=Decimal("0.5"),
            quantity_step=1.0,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="quantity_step must be positive"):
        InstrumentEconomics(
            instrument_id=inst_id,
            currency="BRL",
            money_per_price_unit=Decimal("1.0"),
            tick_size=Decimal("0.5"),
            quantity_step=Decimal("0"),
        )


def test_execution_timing_valid() -> None:
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)
    t2 = datetime(2026, 9, 16, 10, 0, 2, tzinfo=UTC)
    t3 = datetime(2026, 9, 16, 10, 0, 3, tzinfo=UTC)
    t4 = datetime(2026, 9, 16, 10, 0, 4, tzinfo=UTC)

    timing = ExecutionTiming(
        knowledge_cutoff=t0,
        decision_time=t1,
        order_ready_time=t2,
        simulated_market_arrival_time=t3,
        fill_opportunity_time=t4,
    )
    assert timing.knowledge_cutoff == t0
    assert timing.fill_opportunity_time == t4


def test_execution_timing_regressions() -> None:
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)

    with pytest.raises(ValueError, match="decision_time cannot precede knowledge_cutoff"):
        ExecutionTiming(
            knowledge_cutoff=t1,
            decision_time=t0,
            order_ready_time=t1,
            simulated_market_arrival_time=t1,
            fill_opportunity_time=t1,
        )

    with pytest.raises(ValueError, match="order_ready_time cannot precede decision_time"):
        ExecutionTiming(
            knowledge_cutoff=t0,
            decision_time=t1,
            order_ready_time=t0,
            simulated_market_arrival_time=t1,
            fill_opportunity_time=t1,
        )

    with pytest.raises(
        ValueError, match="simulated_market_arrival_time cannot precede order_ready_time"
    ):
        ExecutionTiming(
            knowledge_cutoff=t0,
            decision_time=t0,
            order_ready_time=t1,
            simulated_market_arrival_time=t0,
            fill_opportunity_time=t1,
        )

    with pytest.raises(
        ValueError,
        match="fill_opportunity_time cannot precede simulated_market_arrival_time",
    ):
        ExecutionTiming(
            knowledge_cutoff=t0,
            decision_time=t0,
            order_ready_time=t0,
            simulated_market_arrival_time=t1,
            fill_opportunity_time=t0,
        )


def test_backtest_action_valid() -> None:
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)
    t2 = datetime(2026, 9, 16, 10, 0, 2, tzinfo=UTC)

    action = BacktestAction(
        action_id=ActionIdentity(make_uuid()),
        instrument_id=TradableInstrumentId(make_uuid()),
        side=Side.BUY,
        quantity=Decimal("5"),
        order_style=OrderStyle.MARKET,
        knowledge_cutoff=t0,
        decision_time=t1,
        order_ready_time=t2,
    )
    assert action.side == Side.BUY
    assert action.quantity == Decimal("5")


def test_backtest_action_invalid_inputs() -> None:
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)
    t2 = datetime(2026, 9, 16, 10, 0, 2, tzinfo=UTC)
    aid = ActionIdentity(make_uuid())
    iid = TradableInstrumentId(make_uuid())

    with pytest.raises(ValueError, match="action_id must be ActionIdentity"):
        BacktestAction(
            action_id="bad",  # type: ignore[arg-type]
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("1"),
            order_style=OrderStyle.MARKET,
            knowledge_cutoff=t0,
            decision_time=t1,
            order_ready_time=t2,
        )

    with pytest.raises(ValueError, match="instrument_id must be TradableInstrumentId"):
        BacktestAction(
            action_id=aid,
            instrument_id="bad",  # type: ignore[arg-type]
            side=Side.BUY,
            quantity=Decimal("1"),
            order_style=OrderStyle.MARKET,
            knowledge_cutoff=t0,
            decision_time=t1,
            order_ready_time=t2,
        )

    with pytest.raises(ValueError, match="side must be Side enum"):
        BacktestAction(
            action_id=aid,
            instrument_id=iid,
            side="BUY",  # type: ignore[arg-type]
            quantity=Decimal("1"),
            order_style=OrderStyle.MARKET,
            knowledge_cutoff=t0,
            decision_time=t1,
            order_ready_time=t2,
        )

    with pytest.raises(ValueError, match="quantity must be Decimal"):
        BacktestAction(
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=1,  # type: ignore[arg-type]
            order_style=OrderStyle.MARKET,
            knowledge_cutoff=t0,
            decision_time=t1,
            order_ready_time=t2,
        )

    with pytest.raises(ValueError, match="quantity must be strictly positive"):
        BacktestAction(
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("0"),
            order_style=OrderStyle.MARKET,
            knowledge_cutoff=t0,
            decision_time=t1,
            order_ready_time=t2,
        )

    with pytest.raises(ValueError, match="order_style must be OrderStyle enum"):
        BacktestAction(
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("1"),
            order_style="MARKET",  # type: ignore[arg-type]
            knowledge_cutoff=t0,
            decision_time=t1,
            order_ready_time=t2,
        )

    with pytest.raises(ValueError, match="only MARKET is supported"):
        BacktestAction(
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("1"),
            order_style=OrderStyle.LIMIT,
            knowledge_cutoff=t0,
            decision_time=t1,
            order_ready_time=t2,
        )

    with pytest.raises(ValueError, match="decision_time cannot precede knowledge_cutoff"):
        BacktestAction(
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("1"),
            order_style=OrderStyle.MARKET,
            knowledge_cutoff=t1,
            decision_time=t0,
            order_ready_time=t2,
        )

    with pytest.raises(ValueError, match="order_ready_time cannot precede decision_time"):
        BacktestAction(
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("1"),
            order_style=OrderStyle.MARKET,
            knowledge_cutoff=t0,
            decision_time=t2,
            order_ready_time=t1,
        )


def test_simulated_fill_valid() -> None:
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    timing = ExecutionTiming(t0, t0, t0, t0, t0)
    aid = ActionIdentity(make_uuid())
    fid = ActionIdentity(make_uuid())
    iid = TradableInstrumentId(make_uuid())
    eid = EventId(make_uuid())

    fill = SimulatedFill(
        fill_id=fid,
        action_id=aid,
        instrument_id=iid,
        side=Side.BUY,
        quantity=Decimal("10"),
        raw_price=Decimal("100.00"),
        fill_price=Decimal("100.05"),
        slippage=Decimal("0.05"),
        explicit_fee=Decimal("1.25"),
        timing=timing,
        outcome=ExecutionOutcome.FILL,
        source_event_id=eid,
    )
    assert fill.outcome == ExecutionOutcome.FILL
    assert fill.slippage == Decimal("0.05")
    assert fill.explicit_fee == Decimal("1.25")


def test_simulated_fill_invalid_inputs() -> None:
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    timing = ExecutionTiming(t0, t0, t0, t0, t0)
    aid = ActionIdentity(make_uuid())
    fid = ActionIdentity(make_uuid())
    iid = TradableInstrumentId(make_uuid())

    with pytest.raises(ValueError, match="fill_id must be ActionIdentity"):
        SimulatedFill(
            fill_id="bad",  # type: ignore[arg-type]
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("10"),
            raw_price=Decimal("100.00"),
            fill_price=Decimal("100.00"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.FILL,
        )

    with pytest.raises(ValueError, match="action_id must be ActionIdentity"):
        SimulatedFill(
            fill_id=fid,
            action_id="bad",  # type: ignore[arg-type]
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("10"),
            raw_price=Decimal("100.00"),
            fill_price=Decimal("100.00"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.FILL,
        )

    with pytest.raises(ValueError, match="instrument_id must be TradableInstrumentId"):
        SimulatedFill(
            fill_id=fid,
            action_id=aid,
            instrument_id="bad",  # type: ignore[arg-type]
            side=Side.BUY,
            quantity=Decimal("10"),
            raw_price=Decimal("100.00"),
            fill_price=Decimal("100.00"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.FILL,
        )

    with pytest.raises(ValueError, match="side must be Side enum"):
        SimulatedFill(
            fill_id=fid,
            action_id=aid,
            instrument_id=iid,
            side="BUY",  # type: ignore[arg-type]
            quantity=Decimal("10"),
            raw_price=Decimal("100.00"),
            fill_price=Decimal("100.00"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.FILL,
        )

    with pytest.raises(ValueError, match="quantity must be Decimal"):
        SimulatedFill(
            fill_id=fid,
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=10,  # type: ignore[arg-type]
            raw_price=Decimal("100.00"),
            fill_price=Decimal("100.00"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.FILL,
        )

    with pytest.raises(ValueError, match="quantity cannot be negative"):
        SimulatedFill(
            fill_id=fid,
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("-1"),
            raw_price=Decimal("100.00"),
            fill_price=Decimal("100.00"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.FILL,
        )

    with pytest.raises(ValueError, match="raw_price must be Decimal"):
        SimulatedFill(
            fill_id=fid,
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("10"),
            raw_price=100.0,  # type: ignore[arg-type]
            fill_price=Decimal("100.00"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.FILL,
        )

    with pytest.raises(ValueError, match="fill_price must be Decimal"):
        SimulatedFill(
            fill_id=fid,
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("10"),
            raw_price=Decimal("100.00"),
            fill_price=100.0,  # type: ignore[arg-type]
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.FILL,
        )

    with pytest.raises(ValueError, match="slippage must be Decimal"):
        SimulatedFill(
            fill_id=fid,
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("10"),
            raw_price=Decimal("100.00"),
            fill_price=Decimal("100.00"),
            slippage=0.0,  # type: ignore[arg-type]
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.FILL,
        )

    with pytest.raises(ValueError, match="slippage cannot be negative"):
        SimulatedFill(
            fill_id=fid,
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("10"),
            raw_price=Decimal("100.00"),
            fill_price=Decimal("100.00"),
            slippage=Decimal("-1"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.FILL,
        )

    with pytest.raises(ValueError, match="explicit_fee must be Decimal"):
        SimulatedFill(
            fill_id=fid,
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("10"),
            raw_price=Decimal("100.00"),
            fill_price=Decimal("100.00"),
            slippage=Decimal("0"),
            explicit_fee=1.0,  # type: ignore[arg-type]
            timing=timing,
            outcome=ExecutionOutcome.FILL,
        )

    with pytest.raises(ValueError, match="explicit_fee cannot be negative"):
        SimulatedFill(
            fill_id=fid,
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("10"),
            raw_price=Decimal("100.00"),
            fill_price=Decimal("100.00"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("-1"),
            timing=timing,
            outcome=ExecutionOutcome.FILL,
        )

    with pytest.raises(ValueError, match="timing must be ExecutionTiming"):
        SimulatedFill(
            fill_id=fid,
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("10"),
            raw_price=Decimal("100.00"),
            fill_price=Decimal("100.00"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing="timing",  # type: ignore[arg-type]
            outcome=ExecutionOutcome.FILL,
        )

    with pytest.raises(ValueError, match="outcome must be ExecutionOutcome enum"):
        SimulatedFill(
            fill_id=fid,
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("10"),
            raw_price=Decimal("100.00"),
            fill_price=Decimal("100.00"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome="FILL",  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="source_event_id must be EventId or None"):
        SimulatedFill(
            fill_id=fid,
            action_id=aid,
            instrument_id=iid,
            side=Side.BUY,
            quantity=Decimal("10"),
            raw_price=Decimal("100.00"),
            fill_price=Decimal("100.00"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.FILL,
            source_event_id="bad",  # type: ignore[arg-type]
        )
