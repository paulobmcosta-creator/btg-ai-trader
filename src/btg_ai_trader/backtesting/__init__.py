"""Deterministic economic backtesting package for BTG AI Trader (Sprint 3)."""

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

__all__ = [
    "ActionIdentity",
    "BacktestAction",
    "EconomicAssumptions",
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
    "simulate_action_execution",
    "simulate_actions",
]
