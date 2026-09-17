"""Deterministic sensitivity analysis and monotonicity verification (Sprint 3).

Evaluates simulation behavior under adverse friction sweeps (slippage, fees, latency).
Under stated assumptions, fees and adverse slippage verify monotonic net P&L degradation.
Latency is evaluated for deterministic and comparable sensitivity ONLY; universal latency
monotonicity is not claimed.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from btg_ai_trader.backtesting.assumptions import (
    EconomicAssumptions,
    FeeSchedule,
    FixedPointsSlippageModel,
    LatencyModel,
    SlippageModel,
    ZeroSlippageModel,
)
from btg_ai_trader.backtesting.domain import BacktestAction, InstrumentEconomics
from btg_ai_trader.backtesting.engine import DeterministicEconomicBacktester
from btg_ai_trader.observer.provenance import CodeRevision
from btg_ai_trader.replay.core import CausalMarketReplaySchedule


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

    first_param = sweep_results[0].parameter_name
    for i in range(1, len(sweep_results)):
        prev = sweep_results[i - 1]
        curr = sweep_results[i]

        if curr.parameter_name != first_param:
            raise ValueError(
                f"Mixed parameters in sensitivity sweep: {curr.parameter_name} vs {first_param}"
            )
        if curr.friction_value < prev.friction_value:
            raise ValueError(
                f"Sensitivity sweep results must be sorted by friction_value ascending: "
                f"{curr.friction_value} < {prev.friction_value}"
            )
        if curr.net_realized_pnl > prev.net_realized_pnl:
            raise MonotonicityViolationError(
                f"Monotonicity violation on {curr.parameter_name}: "
                f"friction {curr.friction_value} produced net P&L {curr.net_realized_pnl}, "
                f"which is greater than friction {prev.friction_value} "
                f"net P&L {prev.net_realized_pnl}"
            )


def run_fee_sensitivity_sweep(
    actions: Sequence[BacktestAction],
    replay_schedule: CausalMarketReplaySchedule,
    instrument_economics: InstrumentEconomics,
    base_assumptions: EconomicAssumptions,
    fee_multipliers: Sequence[Decimal],
    code_revision: CodeRevision | str,
) -> list[SensitivityDataPoint]:
    """Sweep explicit fee multipliers and verify net P&L monotonicity."""
    if not isinstance(replay_schedule, CausalMarketReplaySchedule):
        raise ValueError("replay_schedule must be CausalMarketReplaySchedule")
    if code_revision is None:
        raise ValueError("code_revision must be explicitly provided")

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
            effective_from=base_fee.effective_from,
            effective_until=base_fee.effective_until,
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
            code_revision=code_revision,
        )
        res = tester.run(actions=actions, replay_schedule=replay_schedule)
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
    replay_schedule: CausalMarketReplaySchedule,
    instrument_economics: InstrumentEconomics,
    base_assumptions: EconomicAssumptions,
    slippage_points_list: Sequence[Decimal],
    code_revision: CodeRevision | str,
) -> list[SensitivityDataPoint]:
    """Sweep fixed adverse slippage points and verify net P&L monotonicity."""
    if not isinstance(replay_schedule, CausalMarketReplaySchedule):
        raise ValueError("replay_schedule must be CausalMarketReplaySchedule")
    if code_revision is None:
        raise ValueError("code_revision must be explicitly provided")

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
            code_revision=code_revision,
        )
        res = tester.run(actions=actions, replay_schedule=replay_schedule)
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


def run_latency_sensitivity_sweep(
    actions: Sequence[BacktestAction],
    replay_schedule: CausalMarketReplaySchedule,
    instrument_economics: InstrumentEconomics,
    base_assumptions: EconomicAssumptions,
    transit_latencies_us: Sequence[int],
    code_revision: CodeRevision | str,
) -> list[SensitivityDataPoint]:
    """Sweep virtual transit latency in microseconds and collect sensitivity data."""
    if not isinstance(replay_schedule, CausalMarketReplaySchedule):
        raise ValueError("replay_schedule must be CausalMarketReplaySchedule")
    if code_revision is None:
        raise ValueError("code_revision must be explicitly provided")

    results: list[SensitivityDataPoint] = []

    for lat_us in sorted(transit_latencies_us):
        if lat_us < 0:
            raise ValueError("latency cannot be negative")

        swept_latency = LatencyModel(
            decision_latency_us=base_assumptions.latency_model.decision_latency_us,
            transit_latency_us=lat_us,
        )
        swept_assumptions = EconomicAssumptions(
            assumptions_id=f"{base_assumptions.assumptions_id}-lat-{lat_us}",
            spread_model=base_assumptions.spread_model,
            slippage_model=base_assumptions.slippage_model,
            fee_schedule=base_assumptions.fee_schedule,
            latency_model=swept_latency,
            execution_policy=base_assumptions.execution_policy,
        )

        tester = DeterministicEconomicBacktester(
            instrument_economics=instrument_economics,
            assumptions=swept_assumptions,
            code_revision=code_revision,
        )
        res = tester.run(actions=actions, replay_schedule=replay_schedule)
        point = SensitivityDataPoint(
            parameter_name="transit_latency_us",
            friction_value=Decimal(lat_us),
            gross_realized_pnl=res.metrics.gross_realized_pnl,
            net_realized_pnl=res.metrics.net_realized_pnl,
            total_explicit_fees=res.metrics.total_explicit_fees,
            diagnostic_slippage_burden=res.metrics.diagnostic_slippage_burden,
        )
        results.append(point)

    return results
