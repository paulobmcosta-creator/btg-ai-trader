"""Descriptive economic metrics computation for backtesting (Sprint 3).

Note: These metrics are strictly DESCRIPTIVE statistics of realized simulation history.
Inferential, statistical, and promotional claims (Sharpe, Sortino, Calmar, VaR,
Expected Shortfall, p-values, hypothesis tests) are explicitly excluded and deferred.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from btg_ai_trader.backtesting.accounting import BacktestEconomicState
from btg_ai_trader.backtesting.domain import (
    BacktestAction,
    ExecutionOutcome,
    InstrumentEconomics,
    Side,
    SimulatedFill,
)


@dataclass(frozen=True, slots=True, init=False)
class DescriptiveBacktestMetrics:
    """Deterministic descriptive economic summary of a completed backtest run."""

    gross_realized_pnl: Decimal
    net_realized_pnl: Decimal
    total_explicit_fees: Decimal
    diagnostic_slippage_burden: Decimal
    diagnostic_spread_burden: Decimal
    turnover: Decimal
    total_actions: int
    fill_count: int
    no_fill_count: int
    indeterminate_count: int
    rejected_count: int
    fill_rate: Decimal
    closed_trade_count: int
    winning_trade_count: int
    losing_trade_count: int
    breakeven_trade_count: int
    hit_rate: Decimal
    average_win: Decimal
    average_loss: Decimal
    gross_profit_factor: Decimal
    gross_expectancy: Decimal
    max_drawdown_amount: Decimal
    max_drawdown_ratio: Decimal | None

    def __init__(
        self,
        gross_realized_pnl: Decimal,
        net_realized_pnl: Decimal,
        total_explicit_fees: Decimal,
        diagnostic_slippage_burden: Decimal,
        turnover: Decimal,
        total_actions: int,
        fill_count: int,
        no_fill_count: int,
        indeterminate_count: int,
        rejected_count: int,
        fill_rate: Decimal,
        closed_trade_count: int,
        winning_trade_count: int,
        losing_trade_count: int,
        breakeven_trade_count: int,
        hit_rate: Decimal,
        average_win: Decimal,
        average_loss: Decimal,
        gross_profit_factor: Decimal | None = None,
        gross_expectancy: Decimal | None = None,
        max_drawdown_amount: Decimal = Decimal("0"),
        max_drawdown_ratio: Decimal | None = None,
        profit_factor: Decimal | None = None,
        expectancy: Decimal | None = None,
        diagnostic_spread_burden: Decimal = Decimal("0"),
    ) -> None:
        resolved_pf = gross_profit_factor if gross_profit_factor is not None else (
            profit_factor if profit_factor is not None else Decimal("0")
        )
        resolved_exp = gross_expectancy if gross_expectancy is not None else (
            expectancy if expectancy is not None else Decimal("0")
        )

        object.__setattr__(self, "gross_realized_pnl", gross_realized_pnl)
        object.__setattr__(self, "net_realized_pnl", net_realized_pnl)
        object.__setattr__(self, "total_explicit_fees", total_explicit_fees)
        object.__setattr__(self, "diagnostic_slippage_burden", diagnostic_slippage_burden)
        object.__setattr__(self, "diagnostic_spread_burden", diagnostic_spread_burden)
        object.__setattr__(self, "turnover", turnover)
        object.__setattr__(self, "total_actions", total_actions)
        object.__setattr__(self, "fill_count", fill_count)
        object.__setattr__(self, "no_fill_count", no_fill_count)
        object.__setattr__(self, "indeterminate_count", indeterminate_count)
        object.__setattr__(self, "rejected_count", rejected_count)
        object.__setattr__(self, "fill_rate", fill_rate)
        object.__setattr__(self, "closed_trade_count", closed_trade_count)
        object.__setattr__(self, "winning_trade_count", winning_trade_count)
        object.__setattr__(self, "losing_trade_count", losing_trade_count)
        object.__setattr__(self, "breakeven_trade_count", breakeven_trade_count)
        object.__setattr__(self, "hit_rate", hit_rate)
        object.__setattr__(self, "average_win", average_win)
        object.__setattr__(self, "average_loss", average_loss)
        object.__setattr__(self, "gross_profit_factor", resolved_pf)
        object.__setattr__(self, "gross_expectancy", resolved_exp)
        object.__setattr__(self, "max_drawdown_amount", max_drawdown_amount)
        object.__setattr__(self, "max_drawdown_ratio", max_drawdown_ratio)

    @property
    def profit_factor(self) -> Decimal:
        return self.gross_profit_factor

    @property
    def expectancy(self) -> Decimal:
        return self.gross_expectancy


def compute_descriptive_metrics(
    actions: Sequence[BacktestAction],
    fills: Sequence[SimulatedFill],
    economic_state: BacktestEconomicState,
    instrument_economics: InstrumentEconomics,
) -> DescriptiveBacktestMetrics:
    """Compute deterministic descriptive economic metrics from backtest artifacts."""
    total_actions = len(actions)
    fill_count = sum(1 for f in fills if f.outcome == ExecutionOutcome.FILL)
    no_fill_count = sum(1 for f in fills if f.outcome == ExecutionOutcome.NO_FILL)
    indeterminate_count = sum(1 for f in fills if f.outcome == ExecutionOutcome.INDETERMINATE)
    rejected_count = sum(1 for f in fills if f.outcome == ExecutionOutcome.REJECTED)

    # Action-level fill rate bounded in [0, 1]
    raw_fill_rate = (
        Decimal(fill_count) / Decimal(total_actions) if total_actions > 0 else Decimal("0")
    )
    fill_rate = min(Decimal("1"), raw_fill_rate)

    turnover = sum(
        (
            f.fill_price * f.quantity * instrument_economics.money_per_price_unit
            for f in fills
            if f.outcome == ExecutionOutcome.FILL
        ),
        start=Decimal("0"),
    )

    # Reconstruct closed trades from fills to evaluate trade-level stats
    closed_pnls: list[Decimal] = []
    curr_qty = Decimal("0")
    curr_basis = Decimal("0")

    for f in fills:
        if f.outcome != ExecutionOutcome.FILL:
            continue
        signed_qty = f.quantity if f.side == Side.BUY else -f.quantity

        if curr_qty == Decimal("0"):
            curr_qty = signed_qty
            curr_basis = f.fill_price
        elif (curr_qty > 0 and signed_qty > 0) or (curr_qty < 0 and signed_qty < 0):
            total_qty = abs(curr_qty) + abs(signed_qty)
            curr_basis = (
                (abs(curr_qty) * curr_basis) + (abs(signed_qty) * f.fill_price)
            ) / total_qty
            curr_qty += signed_qty
        else:
            closing_qty = min(abs(curr_qty), abs(signed_qty))
            mult = instrument_economics.money_per_price_unit
            if curr_qty > 0:
                trade_pnl = (f.fill_price - curr_basis) * closing_qty * mult
            else:
                trade_pnl = (curr_basis - f.fill_price) * closing_qty * mult
            closed_pnls.append(trade_pnl)

            rem = curr_qty + signed_qty
            if rem == Decimal("0"):
                curr_basis = Decimal("0")
            elif (rem > 0) == (curr_qty > 0):
                pass
            else:
                curr_basis = f.fill_price
            curr_qty = rem

    closed_trade_count = len(closed_pnls)
    winning_trades = [p for p in closed_pnls if p > Decimal("0")]
    losing_trades = [p for p in closed_pnls if p < Decimal("0")]
    breakeven_trades = [p for p in closed_pnls if p == Decimal("0")]

    winning_trade_count = len(winning_trades)
    losing_trade_count = len(losing_trades)
    breakeven_trade_count = len(breakeven_trades)

    hit_rate = (
        Decimal(winning_trade_count) / Decimal(closed_trade_count)
        if closed_trade_count > 0
        else Decimal("0")
    )

    gross_wins = sum(winning_trades, start=Decimal("0"))
    gross_losses = sum((abs(p) for p in losing_trades), start=Decimal("0"))

    average_win = (
        gross_wins / Decimal(winning_trade_count) if winning_trade_count > 0 else Decimal("0")
    )
    average_loss = (
        gross_losses / Decimal(losing_trade_count) if losing_trade_count > 0 else Decimal("0")
    )

    if gross_losses > Decimal("0"):
        gross_profit_factor = gross_wins / gross_losses
    elif gross_wins > Decimal("0"):
        gross_profit_factor = Decimal("Infinity")
    else:
        gross_profit_factor = Decimal("0")

    # Mathematical trade expectancy handles breakevens without bias
    gross_expectancy = (
        sum(closed_pnls, start=Decimal("0")) / Decimal(closed_trade_count)
        if closed_trade_count > 0
        else Decimal("0")
    )

    # Realized drawdown amount from equity curve; ratio is None without explicit capital denominator
    curve = economic_state.realized_equity_curve
    max_peak = Decimal("0")
    max_dd_amount = Decimal("0")

    for val in curve:
        if val > max_peak:
            max_peak = val
        dd = max_peak - val
        if dd > max_dd_amount:
            max_dd_amount = dd

    max_dd_ratio: Decimal | None = None

    return DescriptiveBacktestMetrics(
        gross_realized_pnl=economic_state.pnl.gross_realized_pnl,
        net_realized_pnl=economic_state.pnl.net_realized_pnl,
        total_explicit_fees=economic_state.pnl.explicit_fees,
        diagnostic_slippage_burden=economic_state.pnl.diagnostic_slippage_burden,
        diagnostic_spread_burden=economic_state.pnl.diagnostic_spread_burden,
        turnover=turnover,
        total_actions=total_actions,
        fill_count=fill_count,
        no_fill_count=no_fill_count,
        indeterminate_count=indeterminate_count,
        rejected_count=rejected_count,
        fill_rate=fill_rate,
        closed_trade_count=closed_trade_count,
        winning_trade_count=winning_trade_count,
        losing_trade_count=losing_trade_count,
        breakeven_trade_count=breakeven_trade_count,
        hit_rate=hit_rate,
        average_win=average_win,
        average_loss=average_loss,
        gross_profit_factor=gross_profit_factor,
        gross_expectancy=gross_expectancy,
        max_drawdown_amount=max_dd_amount,
        max_drawdown_ratio=max_dd_ratio,
    )
