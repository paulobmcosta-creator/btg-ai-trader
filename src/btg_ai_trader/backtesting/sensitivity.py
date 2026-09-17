"""Deterministic sensitivity analysis and monotonicity verification (Sprint 3).

Evaluates simulation behavior under adverse friction sweeps (slippage, fees, latency)
and verifies that economic performance degrades monotonically as friction increases.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from btg_ai_trader.backtesting.assumptions import (
    EconomicAssumptions,
    FeeSchedule,
    FixedPointsSlippageModel,
    SlippageModel,
    ZeroSlippageModel,
)
from btg_ai_trader.backtesting.domain import BacktestAction, InstrumentEconomics
from btg_ai_trader.backtesting.engine import DeterministicEconomicBacktester
from btg_ai_trader.observer.envelope import EventEnvelope


class MonotonicityViolationError(Exception):
    """Raised when an increase in execution friction yields an increase in net P&L."""


@dataclass(frozen=True, slots=True)
class SensitivityDataPoint:
    """Single evaluated step in a friction sensitivity sweep."""

    parameter_name: str
    friction_value: Decimal
    gross_realized_pnl: Decimal
    net_realized_pnl: Decimal
    total_explicit_fees: Decimal
    diagnostic_slippage_burden: Decimal


def verify_pnl_monotonicity(sweep_results: Sequence[SensitivityDataPoint]) -> None:
    """Verify that net_realized_pnl is monotonically non-increasing as friction increases."""
    if len(sweep_results) < 2:
        return

    for i in range(1, len(sweep_results)):
        prev = sweep_results[i - 1]
        curr = sweep_results[i]
        if curr.net_realized_pnl > prev.net_realized_pnl:
            raise MonotonicityViolationError(
                f"Monotonicity violation on {curr.parameter_name}: "
                f"friction {curr.friction_value} produced net P&L {curr.net_realized_pnl}, "
                f"which is greater than friction {prev.friction_value} "
                f"net P&L {prev.net_realized_pnl}"
            )


def run_fee_sensitivity_sweep(
    actions: Sequence[BacktestAction],
    market_events: Sequence[EventEnvelope],
    instrument_economics: InstrumentEconomics,
    base_assumptions: EconomicAssumptions,
    fee_multipliers: Sequence[Decimal],
) -> list[SensitivityDataPoint]:
    """Sweep explicit fee multipliers and verify net P&L monotonicity."""
    results: list[SensitivityDataPoint] = []

    base_fee = base_assumptions.fee_schedule
    for mult in sorted(fee_multipliers):
        if mult < Decimal("0"):
            raise ValueError("fee multiplier cannot be negative")

        scaled_schedule = FeeSchedule(
            schedule_id=f"{base_fee.schedule_id}-mult-{mult}",
            fixed_per_order=base_fee.fixed_per_order * mult,
            per_unit=base_fee.per_unit * mult,
            bps_rate=base_fee.bps_rate * mult,
            currency=base_fee.currency,
        )
        swept_assumptions = EconomicAssumptions(
            assumptions_id=f"{base_assumptions.assumptions_id}-fee-{mult}",
            spread_model=base_assumptions.spread_model,
            slippage_model=base_assumptions.slippage_model,
            fee_schedule=scaled_schedule,
            latency_model=base_assumptions.latency_model,
            execution_policy=base_assumptions.execution_policy,
        )

        tester = DeterministicEconomicBacktester(
            instrument_economics=instrument_economics,
            assumptions=swept_assumptions,
        )
        res = tester.run(actions=actions, market_events=market_events)
        point = SensitivityDataPoint(
            parameter_name="fee_multiplier",
            friction_value=mult,
            gross_realized_pnl=res.metrics.gross_realized_pnl,
            net_realized_pnl=res.metrics.net_realized_pnl,
            total_explicit_fees=res.metrics.total_explicit_fees,
            diagnostic_slippage_burden=res.metrics.diagnostic_slippage_burden,
        )
        results.append(point)

    verify_pnl_monotonicity(results)
    return results


def run_slippage_sensitivity_sweep(
    actions: Sequence[BacktestAction],
    market_events: Sequence[EventEnvelope],
    instrument_economics: InstrumentEconomics,
    base_assumptions: EconomicAssumptions,
    slippage_points_list: Sequence[Decimal],
) -> list[SensitivityDataPoint]:
    """Sweep fixed adverse slippage points and verify net P&L monotonicity."""
    results: list[SensitivityDataPoint] = []

    for pts in sorted(slippage_points_list):
        if pts < Decimal("0"):
            raise ValueError("slippage points cannot be negative")

        slip_model: SlippageModel
        if pts == Decimal("0"):
            slip_model = ZeroSlippageModel()
        else:
            slip_model = FixedPointsSlippageModel(adverse_points=pts)

        swept_assumptions = EconomicAssumptions(
            assumptions_id=f"{base_assumptions.assumptions_id}-slip-{pts}",
            spread_model=base_assumptions.spread_model,
            slippage_model=slip_model,
            fee_schedule=base_assumptions.fee_schedule,
            latency_model=base_assumptions.latency_model,
            execution_policy=base_assumptions.execution_policy,
        )

        tester = DeterministicEconomicBacktester(
            instrument_economics=instrument_economics,
            assumptions=swept_assumptions,
        )
        res = tester.run(actions=actions, market_events=market_events)
        point = SensitivityDataPoint(
            parameter_name="slippage_points",
            friction_value=pts,
            gross_realized_pnl=res.metrics.gross_realized_pnl,
            net_realized_pnl=res.metrics.net_realized_pnl,
            total_explicit_fees=res.metrics.total_explicit_fees,
            diagnostic_slippage_burden=res.metrics.diagnostic_slippage_burden,
        )
        results.append(point)

    verify_pnl_monotonicity(results)
    return results
