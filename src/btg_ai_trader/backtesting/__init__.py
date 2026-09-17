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
    FixedPointsSlippageModel,
    LatencyModel,
    SlippageModel,
    SpreadModel,
    ZeroSlippageModel,
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
from btg_ai_trader.backtesting.execution import (
    simulate_action_execution,
    simulate_actions,
)
from btg_ai_trader.backtesting.metrics import (
    DescriptiveBacktestMetrics,
    compute_descriptive_metrics,
)

__all__ = [
    "ActionIdentity",
    "BacktestAction",
    "BacktestEconomicState",
    "BacktestPnL",
    "BacktestPositionState",
    "DescriptiveBacktestMetrics",
    "EconomicAssumptions",
    "EndOfWindowPolicy",
    "ExecutionOutcome",
    "ExecutionPolicy",
    "ExecutionTiming",
    "FeeSchedule",
    "FixedBpsSlippageModel",
    "FixedPointsSlippageModel",
    "InstrumentEconomics",
    "LatencyModel",
    "OrderStyle",
    "Side",
    "SimulatedFill",
    "SlippageModel",
    "SpreadModel",
    "ZeroSlippageModel",
    "compute_descriptive_metrics",
    "simulate_action_execution",
    "simulate_actions",
]
