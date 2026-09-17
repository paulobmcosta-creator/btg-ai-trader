"""Unit tests for simulated accounting and P&L tracking."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from btg_ai_trader.backtesting.accounting import (
    BacktestEconomicState,
    BacktestPnL,
    BacktestPositionState,
    EndOfWindowPolicy,
)
from btg_ai_trader.backtesting.domain import (
    ActionIdentity,
    ExecutionOutcome,
    ExecutionTiming,
    InstrumentEconomics,
    Side,
    SimulatedFill,
)
from btg_ai_trader.observer.identity import TradableInstrumentId


def make_uuid(num: int = 1) -> str:
    return str(UUID(int=num))


def make_fill(
    instrument_id: TradableInstrumentId,
    side: Side,
    qty: Decimal,
    fill_price: Decimal,
    raw_price: Decimal | None = None,
    slippage: Decimal = Decimal("0"),
    fee: Decimal = Decimal("0"),
    outcome: ExecutionOutcome = ExecutionOutcome.FILL,
) -> SimulatedFill:
    t = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    timing = ExecutionTiming(t, t, t, t, t)
    return SimulatedFill(
        fill_id=ActionIdentity(make_uuid(100)),
        action_id=ActionIdentity(make_uuid(200)),
        instrument_id=instrument_id,
        side=side,
        quantity=qty,
        raw_price=raw_price if raw_price is not None else fill_price,
        fill_price=fill_price,
        slippage=slippage,
        explicit_fee=fee,
        timing=timing,
        outcome=outcome,
    )


def test_position_state_validation() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    pos = BacktestPositionState(
        instrument_id=iid,
        quantity=Decimal("10"),
        weighted_cost_basis=Decimal("100.0"),
        currency="BRL",
        money_per_price_unit=Decimal("1.0"),
    )
    assert pos.is_long
    assert not pos.is_short
    assert not pos.is_flat

    flat_pos = BacktestPositionState(instrument_id=iid)
    assert flat_pos.is_flat
    assert not flat_pos.is_long
    assert not flat_pos.is_short

    short_pos = BacktestPositionState(instrument_id=iid, quantity=Decimal("-5"))
    assert short_pos.is_short
    assert not short_pos.is_long
    assert not short_pos.is_flat

    with pytest.raises(ValueError, match="TradableInstrumentId"):
        BacktestPositionState(instrument_id="bad")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="quantity must be Decimal"):
        BacktestPositionState(instrument_id=iid, quantity=10)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="weighted_cost_basis must be nonnegative Decimal"):
        BacktestPositionState(instrument_id=iid, weighted_cost_basis=Decimal("-1"))

    with pytest.raises(ValueError, match="currency"):
        BacktestPositionState(instrument_id=iid, currency="")

    with pytest.raises(ValueError, match="money_per_price_unit must be positive Decimal"):
        BacktestPositionState(instrument_id=iid, money_per_price_unit=Decimal("0"))


def test_position_transitions_long_and_closed() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    pos = BacktestPositionState(instrument_id=iid, money_per_price_unit=Decimal("2.0"))

    # 1. Buy 10 @ 100
    fill1 = make_fill(iid, Side.BUY, Decimal("10"), Decimal("100.0"), fee=Decimal("5.0"))
    pos, gross_pnl, fee, slip = pos.apply_fill(fill1)
    assert pos.quantity == Decimal("10")
    assert pos.weighted_cost_basis == Decimal("100.0")
    assert gross_pnl == Decimal("0")
    assert fee == Decimal("5.0")

    # 2. Buy 10 more @ 110 -> weighted cost basis = (10*100 + 10*110)/20 = 105
    fill2 = make_fill(iid, Side.BUY, Decimal("10"), Decimal("110.0"))
    pos, gross_pnl, fee, slip = pos.apply_fill(fill2)
    assert pos.quantity == Decimal("20")
    assert pos.weighted_cost_basis == Decimal("105.0")
    assert gross_pnl == Decimal("0")

    # 3. Sell 5 @ 120 (partial close) -> cost basis stays 105, realized P&L = (120 - 105)*5*2 = 150
    fill3 = make_fill(iid, Side.SELL, Decimal("5"), Decimal("120.0"))
    pos, gross_pnl, fee, slip = pos.apply_fill(fill3)
    assert pos.quantity == Decimal("15")
    assert pos.weighted_cost_basis == Decimal("105.0")
    assert gross_pnl == Decimal("150.0")

    # 4. Sell 15 @ 105 (full close to flat) -> cost basis becomes 0, realized P&L = 0
    fill4 = make_fill(iid, Side.SELL, Decimal("15"), Decimal("105.0"))
    pos, gross_pnl, fee, slip = pos.apply_fill(fill4)
    assert pos.is_flat
    assert pos.weighted_cost_basis == Decimal("0")
    assert gross_pnl == Decimal("0")


def test_position_reversal_flip() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    pos = BacktestPositionState(instrument_id=iid, money_per_price_unit=Decimal("1.0"))

    # Buy 10 @ 100
    pos, _, _, _ = pos.apply_fill(make_fill(iid, Side.BUY, Decimal("10"), Decimal("100.0")))
    assert pos.quantity == Decimal("10")

    # Sell 15 @ 110 (flips from +10 to -5)
    # Closed part = 10 units with P&L = (110 - 100)*10 = 100
    # Remaining part = -5 units with new cost basis = 110
    pos, gross_pnl, fee, slip = pos.apply_fill(
        make_fill(iid, Side.SELL, Decimal("15"), Decimal("110.0"))
    )
    assert pos.quantity == Decimal("-5")
    assert pos.weighted_cost_basis == Decimal("110.0")
    assert gross_pnl == Decimal("100.0")

    # Buy 10 @ 105 (covers -5, flips to +5)
    # Closed part = 5 units with short P&L = (110 - 105)*5 = 25
    # Remaining part = +5 units with new cost basis = 105
    pos, gross_pnl, fee, slip = pos.apply_fill(
        make_fill(iid, Side.BUY, Decimal("10"), Decimal("105.0"))
    )
    assert pos.quantity == Decimal("5")
    assert pos.weighted_cost_basis == Decimal("105.0")
    assert gross_pnl == Decimal("25.0")

    # Partial cover short test
    pos_short = BacktestPositionState(
        instrument_id=iid,
        quantity=Decimal("-10"),
        weighted_cost_basis=Decimal("100.0"),
    )
    pos_short, pnl_cover, _, _ = pos_short.apply_fill(
        make_fill(iid, Side.BUY, Decimal("4"), Decimal("90.0"))
    )
    assert pos_short.quantity == Decimal("-6")
    assert pos_short.weighted_cost_basis == Decimal("100.0")
    assert pnl_cover == Decimal("40.0")  # (100 - 90)*4


def test_position_apply_fill_edge_cases() -> None:
    iid1 = TradableInstrumentId(make_uuid(1))
    iid2 = TradableInstrumentId(make_uuid(2))
    pos = BacktestPositionState(instrument_id=iid1)

    # Ignored non-fill
    no_fill = make_fill(
        iid1, Side.BUY, Decimal("5"), Decimal("100"), outcome=ExecutionOutcome.NO_FILL
    )
    pos2, gross, fee, slip = pos.apply_fill(no_fill)
    assert pos2 == pos
    assert gross == Decimal("0")

    # Instrument mismatch
    fill_diff = make_fill(iid2, Side.BUY, Decimal("5"), Decimal("100"))
    with pytest.raises(ValueError, match="instrument_id does not match"):
        pos.apply_fill(fill_diff)


def test_pnl_invariants_and_no_double_counting() -> None:
    # Valid PnL
    pnl = BacktestPnL(
        gross_realized_pnl=Decimal("100.0"),
        explicit_fees=Decimal("10.0"),
        net_realized_pnl=Decimal("90.0"),
        diagnostic_slippage_burden=Decimal("5.0"),
    )
    assert pnl.net_realized_pnl == Decimal("90.0")

    # Invariant: net must equal gross - fees
    match_gross = "net_realized_pnl must equal gross_realized_pnl - explicit_fees"
    with pytest.raises(ValueError, match=match_gross):
        BacktestPnL(
            gross_realized_pnl=Decimal("100.0"),
            explicit_fees=Decimal("10.0"),
            net_realized_pnl=Decimal("85.0"),  # wrong!
            diagnostic_slippage_burden=Decimal("5.0"),
        )

    # Invariant: total_net must equal net + unrealized
    match_net = r"total_net_pnl must equal net_realized_pnl \+ unrealized_pnl"
    with pytest.raises(ValueError, match=match_net):
        BacktestPnL(
            gross_realized_pnl=Decimal("100.0"),
            explicit_fees=Decimal("10.0"),
            net_realized_pnl=Decimal("90.0"),
            diagnostic_slippage_burden=Decimal("5.0"),
            unrealized_pnl=Decimal("20.0"),
            total_net_pnl=Decimal("100.0"),  # should be 110
        )

    with pytest.raises(ValueError, match="total_net_pnl requires known unrealized_pnl"):
        BacktestPnL(
            gross_realized_pnl=Decimal("100.0"),
            explicit_fees=Decimal("10.0"),
            net_realized_pnl=Decimal("90.0"),
            diagnostic_slippage_burden=Decimal("5.0"),
            unrealized_pnl=None,
            total_net_pnl=Decimal("90.0"),
        )

    # Negative fees rejected
    with pytest.raises(ValueError, match="explicit_fees cannot be negative"):
        BacktestPnL(
            gross_realized_pnl=Decimal("100.0"),
            explicit_fees=Decimal("-10.0"),
            net_realized_pnl=Decimal("110.0"),
            diagnostic_slippage_burden=Decimal("5.0"),
        )

    # Negative slippage burden rejected
    with pytest.raises(ValueError, match="diagnostic_slippage_burden cannot be negative"):
        BacktestPnL(
            gross_realized_pnl=Decimal("100.0"),
            explicit_fees=Decimal("10.0"),
            net_realized_pnl=Decimal("90.0"),
            diagnostic_slippage_burden=Decimal("-5.0"),
        )

    # Non-decimal values rejected
    with pytest.raises(ValueError, match="must be Decimal"):
        BacktestPnL(
            gross_realized_pnl=100.0,  # type: ignore[arg-type]
            explicit_fees=Decimal("10.0"),
            net_realized_pnl=Decimal("90.0"),
            diagnostic_slippage_burden=Decimal("5.0"),
        )


def test_economic_state_lifecycle_and_mark_to_market() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    state = BacktestEconomicState.initial(econ)

    assert state.pnl.gross_realized_pnl == Decimal("0")
    assert state.pnl.net_realized_pnl == Decimal("0")
    assert state.positions[0].is_flat

    # Apply BUY fill
    fill_buy = make_fill(iid, Side.BUY, Decimal("10"), Decimal("100.0"), fee=Decimal("2.0"))
    state = state.apply_fills((fill_buy,))
    assert state.positions[0].quantity == Decimal("10")
    assert state.pnl.explicit_fees == Decimal("2.0")
    assert state.pnl.net_realized_pnl == Decimal("-2.0")

    # Mark to market with quote 110 -> unrealized = (110 - 100)*10 = 100, total_net = -2 + 100 = 98
    marked = state.compute_mark_to_market({iid: Decimal("110.0")})
    assert marked.pnl.unrealized_pnl == Decimal("100.0")
    assert marked.pnl.total_net_pnl == Decimal("98.0")

    # Mark to market with missing quote -> fails closed, preserving None
    unmarked = state.compute_mark_to_market({})
    assert unmarked.pnl.unrealized_pnl is None

    # Mark to market with invalid price -> fails closed, preserving None
    invalid_marked = state.compute_mark_to_market({iid: Decimal("-10.0")})
    assert invalid_marked.pnl.unrealized_pnl is None

    # Apply SELL fill closing position
    fill_sell = make_fill(iid, Side.SELL, Decimal("10"), Decimal("110.0"), fee=Decimal("2.0"))
    state = state.apply_fills((fill_sell,))
    assert state.positions[0].is_flat
    assert state.pnl.gross_realized_pnl == Decimal("100.0")
    assert state.pnl.explicit_fees == Decimal("4.0")
    assert state.pnl.net_realized_pnl == Decimal("96.0")

    # When flat, mark to market has 0 unrealized
    flat_marked = state.compute_mark_to_market({iid: Decimal("150.0")})
    assert flat_marked.pnl.unrealized_pnl == Decimal("0")
    assert flat_marked.pnl.total_net_pnl == Decimal("96.0")


def test_economic_state_validation_types() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    pos = BacktestPositionState(instrument_id=iid)
    pnl = BacktestPnL(
        gross_realized_pnl=Decimal("0"),
        explicit_fees=Decimal("0"),
        net_realized_pnl=Decimal("0"),
        diagnostic_slippage_burden=Decimal("0"),
    )

    with pytest.raises(ValueError, match="positions must be a tuple"):
        BacktestEconomicState(
            positions=[pos],  # type: ignore[arg-type]
            pnl=pnl,
            realized_equity_curve=(),
            fills=(),
        )

    with pytest.raises(ValueError, match="pnl must be BacktestPnL"):
        BacktestEconomicState(
            positions=(pos,),
            pnl="not_pnl",  # type: ignore[arg-type]
            realized_equity_curve=(),
            fills=(),
        )

    with pytest.raises(ValueError, match="realized_equity_curve must be a tuple"):
        BacktestEconomicState(
            positions=(pos,),
            pnl=pnl,
            realized_equity_curve=[],  # type: ignore[arg-type]
            fills=(),
        )

    with pytest.raises(ValueError, match="fills must be a tuple"):
        BacktestEconomicState(
            positions=(pos,),
            pnl=pnl,
            realized_equity_curve=(),
            fills=[],  # type: ignore[arg-type]
        )


def test_pnl_unrealized_invalid_type() -> None:
    with pytest.raises(ValueError, match="unrealized_pnl must be Decimal or None"):
        BacktestPnL(
            gross_realized_pnl=Decimal("0"),
            explicit_fees=Decimal("0"),
            net_realized_pnl=Decimal("0"),
            diagnostic_slippage_burden=Decimal("0"),
            unrealized_pnl="100",  # type: ignore[arg-type]
        )


def test_economic_state_apply_fills_edge_cases() -> None:
    iid1 = TradableInstrumentId(make_uuid(1))
    iid_untracked = TradableInstrumentId(make_uuid(99))
    econ = InstrumentEconomics(iid1, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    state = BacktestEconomicState.initial(econ)

    # Untracked instrument fill
    bad_fill = make_fill(iid_untracked, Side.BUY, Decimal("10"), Decimal("100.0"))
    with pytest.raises(ValueError, match="not tracked by BacktestEconomicState"):
        state.apply_fills((bad_fill,))

    # Non-fill fill outcome handled safely
    rejected_fill = make_fill(
        iid1,
        Side.BUY,
        Decimal("10"),
        Decimal("100.0"),
        outcome=ExecutionOutcome.REJECTED,
    )
    state_after = state.apply_fills((rejected_fill,))
    assert len(state_after.fills) == 1
    assert state_after.positions[0].is_flat
    assert state_after.pnl.gross_realized_pnl == Decimal("0")


def test_economic_state_mark_to_market_short_and_invalid_type() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("2.0"), Decimal("0.5"), Decimal("1.0"))
    state = BacktestEconomicState.initial(econ)

    # Go short 5 @ 100
    fill_short = make_fill(iid, Side.SELL, Decimal("5"), Decimal("100.0"), fee=Decimal("1.0"))
    state = state.apply_fills((fill_short,))
    assert state.positions[0].is_short

    # Mark price = 90 (profit of 10 per unit * 5 units * 2 money_per_unit = 100)
    marked = state.compute_mark_to_market({iid: Decimal("90.0")})
    assert marked.pnl.unrealized_pnl == Decimal("100.0")
    assert marked.pnl.total_net_pnl == Decimal("99.0")  # net_realized (-1) + 100

    # Non-decimal mark price in dict -> fails closed
    non_decimal = state.compute_mark_to_market({iid: "90.0"})  # type: ignore[dict-item]
    assert non_decimal.pnl.unrealized_pnl is None


def test_end_of_window_policy_enum() -> None:
    assert EndOfWindowPolicy.KEEP_OPEN.value == "KEEP_OPEN"
    assert EndOfWindowPolicy.CLOSE_AT_LAST_VALID_QUOTE.value == "CLOSE_AT_LAST_VALID_QUOTE"

