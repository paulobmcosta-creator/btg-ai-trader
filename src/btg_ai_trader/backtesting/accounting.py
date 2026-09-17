"""Simulated economic position accounting and P&L tracking (Sprint 3).

Note: This domain represents SIMULATED research backtest accounting only.
It NEVER mutates, instantiates, or accesses the canonical production FinancialLedger.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from btg_ai_trader.backtesting.domain import (
    BacktestMarkEvidence,
    ExecutionOutcome,
    InstrumentEconomics,
    Side,
    SimulatedFill,
)
from btg_ai_trader.observer.identity import TradableInstrumentId
from btg_ai_trader.observer.values import require_text


class EndOfWindowPolicy(str, Enum):
    """Policy for handling open positions when the backtest simulation window ends."""

    KEEP_OPEN = "KEEP_OPEN"
    CLOSE_AT_LAST_VALID_QUOTE = "CLOSE_AT_LAST_VALID_QUOTE"


@dataclass(frozen=True, slots=True)
class BacktestPositionState:
    """Isolated simulated position state for a single tradable instrument."""

    instrument_id: TradableInstrumentId
    quantity: Decimal = Decimal("0")
    weighted_cost_basis: Decimal = Decimal("0")
    currency: str = "BRL"
    money_per_price_unit: Decimal = Decimal("1.0")

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_id, TradableInstrumentId):
            raise ValueError("instrument_id must be TradableInstrumentId")
        if not isinstance(self.quantity, Decimal):
            raise ValueError("quantity must be Decimal")
        if not isinstance(self.weighted_cost_basis, Decimal) or self.weighted_cost_basis < Decimal(
            "0"
        ):
            raise ValueError("weighted_cost_basis must be nonnegative Decimal")
        require_text(self.currency, "currency")
        if not isinstance(
            self.money_per_price_unit, Decimal
        ) or self.money_per_price_unit <= Decimal("0"):
            raise ValueError("money_per_price_unit must be positive Decimal")

    @property
    def is_flat(self) -> bool:
        return self.quantity == Decimal("0")

    @property
    def is_long(self) -> bool:
        return self.quantity > Decimal("0")

    @property
    def is_short(self) -> bool:
        return self.quantity < Decimal("0")

    def apply_fill(
        self,
        fill: SimulatedFill,
    ) -> tuple[BacktestPositionState, Decimal, Decimal, Decimal]:
        """Apply a simulated fill using moving weighted average cost basis.

        Returns (new_state, gross_realized_pnl, fee, slippage_burden).
        """
        if fill.outcome != ExecutionOutcome.FILL:
            return (self, Decimal("0"), Decimal("0"), Decimal("0"))
        if fill.instrument_id != self.instrument_id:
            raise ValueError("fill instrument_id does not match position instrument_id")

        signed_fill_qty = fill.quantity if fill.side == Side.BUY else -fill.quantity
        fee = fill.explicit_fee
        slippage_burden = fill.slippage * fill.quantity * self.money_per_price_unit

        # Case 1: Currently FLAT
        if self.is_flat:
            new_state = BacktestPositionState(
                instrument_id=self.instrument_id,
                quantity=signed_fill_qty,
                weighted_cost_basis=fill.fill_price,
                currency=self.currency,
                money_per_price_unit=self.money_per_price_unit,
            )
            return (new_state, Decimal("0"), fee, slippage_burden)

        # Case 2: Increasing position in the same direction
        if (self.quantity > Decimal("0") and signed_fill_qty > Decimal("0")) or (
            self.quantity < Decimal("0") and signed_fill_qty < Decimal("0")
        ):
            new_quantity = self.quantity + signed_fill_qty
            total_cost = (abs(self.quantity) * self.weighted_cost_basis) + (
                abs(signed_fill_qty) * fill.fill_price
            )
            new_cost_basis = total_cost / abs(new_quantity)
            new_state = BacktestPositionState(
                instrument_id=self.instrument_id,
                quantity=new_quantity,
                weighted_cost_basis=new_cost_basis,
                currency=self.currency,
                money_per_price_unit=self.money_per_price_unit,
            )
            return (new_state, Decimal("0"), fee, slippage_burden)

        # Case 3: Reducing or reversing position (opposite signs)
        closing_qty = min(abs(self.quantity), abs(signed_fill_qty))
        if self.is_long:
            # Long position being sold
            gross_pnl = (
                (fill.fill_price - self.weighted_cost_basis)
                * closing_qty
                * self.money_per_price_unit
            )
        else:
            # Short position being covered
            gross_pnl = (
                (self.weighted_cost_basis - fill.fill_price)
                * closing_qty
                * self.money_per_price_unit
            )

        remainder_qty = self.quantity + signed_fill_qty
        if remainder_qty == Decimal("0"):
            new_cost_basis = Decimal("0")
        elif (remainder_qty > Decimal("0")) == self.is_long:
            # Partial close, cost basis unchanged
            new_cost_basis = self.weighted_cost_basis
        else:
            # Reversed position, remaining quantity adopts fill price
            new_cost_basis = fill.fill_price

        new_state = BacktestPositionState(
            instrument_id=self.instrument_id,
            quantity=remainder_qty,
            weighted_cost_basis=new_cost_basis,
            currency=self.currency,
            money_per_price_unit=self.money_per_price_unit,
        )
        return (new_state, gross_pnl, fee, slippage_burden)


@dataclass(frozen=True, slots=True)
class BacktestPnL:
    """Explicit P&L decomposition without double counting."""

    gross_realized_pnl: Decimal
    explicit_fees: Decimal
    net_realized_pnl: Decimal
    diagnostic_slippage_burden: Decimal
    diagnostic_spread_burden: Decimal = Decimal("0")
    unrealized_pnl: Decimal | None = None
    total_net_pnl: Decimal | None = None

    def __post_init__(self) -> None:
        required_fields = (
            "gross_realized_pnl",
            "explicit_fees",
            "net_realized_pnl",
            "diagnostic_slippage_burden",
            "diagnostic_spread_burden",
        )
        for f in required_fields:
            val = getattr(self, f)
            if not isinstance(val, Decimal):
                raise ValueError(f"{f} must be Decimal")
        if self.explicit_fees < Decimal("0"):
            raise ValueError("explicit_fees cannot be negative")
        if self.diagnostic_slippage_burden < Decimal("0"):
            raise ValueError("diagnostic_slippage_burden cannot be negative")
        if self.diagnostic_spread_burden < Decimal("0"):
            raise ValueError("diagnostic_spread_burden cannot be negative")
        if self.net_realized_pnl != (self.gross_realized_pnl - self.explicit_fees):
            raise ValueError("net_realized_pnl must equal gross_realized_pnl - explicit_fees")
        if self.unrealized_pnl is not None:
            if not isinstance(self.unrealized_pnl, Decimal):
                raise ValueError("unrealized_pnl must be Decimal or None")
            if self.total_net_pnl != (self.net_realized_pnl + self.unrealized_pnl):
                raise ValueError("total_net_pnl must equal net_realized_pnl + unrealized_pnl")
        else:
            if self.total_net_pnl is not None:
                raise ValueError("total_net_pnl requires known unrealized_pnl")


@dataclass(frozen=True, slots=True)
class BacktestEconomicState:
    """Comprehensive simulated economic state tracking positions, P&L, and equity curve."""

    positions: tuple[BacktestPositionState, ...]
    pnl: BacktestPnL
    realized_equity_curve: tuple[Decimal, ...]
    fills: tuple[SimulatedFill, ...]
    mark_evidence: BacktestMarkEvidence | None = None

    def __post_init__(self) -> None:
        if type(self.positions) is not tuple:
            raise ValueError("positions must be a tuple")
        if not isinstance(self.pnl, BacktestPnL):
            raise ValueError("pnl must be BacktestPnL")
        if type(self.realized_equity_curve) is not tuple:
            raise ValueError("realized_equity_curve must be a tuple")
        if type(self.fills) is not tuple:
            raise ValueError("fills must be a tuple")
        if self.mark_evidence is not None and not isinstance(
            self.mark_evidence, BacktestMarkEvidence
        ):
            raise ValueError("mark_evidence must be BacktestMarkEvidence or None")

    @classmethod
    def initial(cls, instrument_economics: InstrumentEconomics) -> BacktestEconomicState:
        """Create empty initial backtest state."""
        init_pos = BacktestPositionState(
            instrument_id=instrument_economics.instrument_id,
            quantity=Decimal("0"),
            weighted_cost_basis=Decimal("0"),
            currency=instrument_economics.currency,
            money_per_price_unit=instrument_economics.money_per_price_unit,
        )
        init_pnl = BacktestPnL(
            gross_realized_pnl=Decimal("0"),
            explicit_fees=Decimal("0"),
            net_realized_pnl=Decimal("0"),
            diagnostic_slippage_burden=Decimal("0"),
            diagnostic_spread_burden=Decimal("0"),
        )
        return cls(
            positions=(init_pos,),
            pnl=init_pnl,
            realized_equity_curve=(Decimal("0"),),
            fills=(),
            mark_evidence=None,
        )

    def apply_fills(
        self,
        fills: Sequence[SimulatedFill],
    ) -> BacktestEconomicState:
        """Deterministically apply a sequence of simulated fills to the state."""
        curr_positions = {p.instrument_id: p for p in self.positions}
        cum_gross = self.pnl.gross_realized_pnl
        cum_fees = self.pnl.explicit_fees
        cum_slippage = self.pnl.diagnostic_slippage_burden
        cum_spread = self.pnl.diagnostic_spread_burden
        equity_curve = list(self.realized_equity_curve)
        all_fills = list(self.fills)

        for fill in fills:
            all_fills.append(fill)
            if fill.outcome != ExecutionOutcome.FILL:
                continue

            if fill.instrument_id not in curr_positions:
                raise ValueError(
                    f"Fill instrument_id {fill.instrument_id} not tracked by BacktestEconomicState"
                )
            pos = curr_positions[fill.instrument_id]
            new_pos, gross_pnl, fee, slippage_burden = pos.apply_fill(fill)
            curr_positions[fill.instrument_id] = new_pos

            cum_gross += gross_pnl
            cum_fees += fee
            cum_slippage += slippage_burden
            cum_spread += fill.diagnostic_spread_burden
            net_cum = cum_gross - cum_fees
            equity_curve.append(net_cum)

        updated_pnl = BacktestPnL(
            gross_realized_pnl=cum_gross,
            explicit_fees=cum_fees,
            net_realized_pnl=cum_gross - cum_fees,
            diagnostic_slippage_burden=cum_slippage,
            diagnostic_spread_burden=cum_spread,
        )

        return BacktestEconomicState(
            positions=tuple(curr_positions.values()),
            pnl=updated_pnl,
            realized_equity_curve=tuple(equity_curve),
            fills=tuple(all_fills),
            mark_evidence=self.mark_evidence,
        )

    def compute_mark_to_market(
        self,
        mark_prices: dict[TradableInstrumentId, Decimal],
        mark_evidence: BacktestMarkEvidence | None = None,
    ) -> BacktestEconomicState:
        """Compute unrealized P&L and total net P&L given explicit mark prices.

        If an open position lacks a valid mark price, unrealized P&L cannot be computed.
        """
        unrealized_sum = Decimal("0")
        has_open = any(not p.is_flat for p in self.positions)

        if has_open and mark_evidence is None:
            # Missing mark evidence for open positions: fails closed
            return self

        if not has_open:
            new_pnl = BacktestPnL(
                gross_realized_pnl=self.pnl.gross_realized_pnl,
                explicit_fees=self.pnl.explicit_fees,
                net_realized_pnl=self.pnl.net_realized_pnl,
                diagnostic_slippage_burden=self.pnl.diagnostic_slippage_burden,
                diagnostic_spread_burden=self.pnl.diagnostic_spread_burden,
                unrealized_pnl=Decimal("0"),
                total_net_pnl=self.pnl.net_realized_pnl,
            )
            return BacktestEconomicState(
                positions=self.positions,
                pnl=new_pnl,
                realized_equity_curve=self.realized_equity_curve,
                fills=self.fills,
                mark_evidence=mark_evidence,
            )

        for pos in self.positions:
            if pos.is_flat:
                continue
            if pos.instrument_id not in mark_prices:
                # Missing mark price: fails closed, preserving None
                return self
            mark_price = mark_prices[pos.instrument_id]
            if not isinstance(mark_price, Decimal) or mark_price <= Decimal("0"):
                return self

            if pos.is_long:
                unrealized = (
                    (mark_price - pos.weighted_cost_basis) * pos.quantity * pos.money_per_price_unit
                )
            else:
                unrealized = (
                    (pos.weighted_cost_basis - mark_price)
                    * abs(pos.quantity)
                    * pos.money_per_price_unit
                )
            unrealized_sum += unrealized

        new_pnl = BacktestPnL(
            gross_realized_pnl=self.pnl.gross_realized_pnl,
            explicit_fees=self.pnl.explicit_fees,
            net_realized_pnl=self.pnl.net_realized_pnl,
            diagnostic_slippage_burden=self.pnl.diagnostic_slippage_burden,
            diagnostic_spread_burden=self.pnl.diagnostic_spread_burden,
            unrealized_pnl=unrealized_sum,
            total_net_pnl=self.pnl.net_realized_pnl + unrealized_sum,
        )

        return BacktestEconomicState(
            positions=self.positions,
            pnl=new_pnl,
            realized_equity_curve=self.realized_equity_curve,
            fills=self.fills,
            mark_evidence=mark_evidence,
        )
