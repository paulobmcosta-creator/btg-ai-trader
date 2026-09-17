"""Deterministic economic backtesting package for BTG AI Trader (Sprint 3)."""

from btg_ai_trader.backtesting.accounting import (
    BacktestEconomicState,
    BacktestPnL,
    BacktestPositionState,
    EndOfWindowPolicy,
)
from btg_ai_trader.backtesting.assumptions import (
    EconomicAssumptions,
    ExecutionPolicy,
    FeeSchedule,
    FixedBpsSlippageModel,
    FixedPercentageSlippageModel,
    FixedPointsSlippageModel,
    LatencyModel,
    SlippageModel,
    SpreadModel,
    ZeroSlippageModel,
)
from btg_ai_trader.backtesting.domain import (
    ActionIdentity,
    BacktestAction,
    BacktestMarkEvidence,
    ExecutionOutcome,
    ExecutionTiming,
    InstrumentEconomics,
    OrderStyle,
    Side,
    SimulatedFill,
)
from btg_ai_trader.backtesting.engine import (
    BacktestResult,
    DeterministicEconomicBacktester,
)
from btg_ai_trader.backtesting.execution import (
    simulate_action_execution,
    simulate_actions,
)
from btg_ai_trader.backtesting.metrics import (
    DescriptiveBacktestMetrics,
    compute_descriptive_metrics,
)
from btg_ai_trader.backtesting.provenance import (
    BacktestInputBoundary,
    BacktestRunManifest,
    compute_actions_hash,
    compute_assumptions_hash,
    compute_dataset_hash,
    compute_economic_state_hash,
    compute_fills_hash,
    compute_instrument_economics_hash,
    compute_metrics_hash,
)
from btg_ai_trader.backtesting.sensitivity import (
    MonotonicityViolationError,
    SensitivityDataPoint,
    run_fee_sensitivity_sweep,
    run_latency_sensitivity_sweep,
    run_slippage_sensitivity_sweep,
    verify_pnl_monotonicity,
)

__all__ = [
    "ActionIdentity",
    "BacktestAction",
    "BacktestEconomicState",
    "BacktestInputBoundary",
    "BacktestMarkEvidence",
    "BacktestPnL",
    "BacktestPositionState",
    "BacktestResult",
    "BacktestRunManifest",
    "DescriptiveBacktestMetrics",
    "DeterministicEconomicBacktester",
    "EconomicAssumptions",
    "EndOfWindowPolicy",
    "ExecutionOutcome",
    "ExecutionPolicy",
    "ExecutionTiming",
    "FeeSchedule",
    "FixedBpsSlippageModel",
    "FixedPercentageSlippageModel",
    "FixedPointsSlippageModel",
    "InstrumentEconomics",
    "LatencyModel",
    "MonotonicityViolationError",
    "OrderStyle",
    "SensitivityDataPoint",
    "Side",
    "SimulatedFill",
    "SlippageModel",
    "SpreadModel",
    "ZeroSlippageModel",
    "compute_actions_hash",
    "compute_assumptions_hash",
    "compute_dataset_hash",
    "compute_descriptive_metrics",
    "compute_economic_state_hash",
    "compute_fills_hash",
    "compute_instrument_economics_hash",
    "compute_metrics_hash",
    "run_fee_sensitivity_sweep",
    "run_latency_sensitivity_sweep",
    "run_slippage_sensitivity_sweep",
    "simulate_action_execution",
    "simulate_actions",
    "verify_pnl_monotonicity",
]
