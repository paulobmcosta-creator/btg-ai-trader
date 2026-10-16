"""Operational Strategy contracts and deterministic policy engine for S8-B01 remediation."""

from btg_ai_trader.strategy.domain import (
    CandidateStrategy,
    ComparisonOperator,
    DecisionOpportunity,
    DecisionReason,
    EconomicDirection,
    EconomicObjective,
    StrategyDecision,
    StrategyDisposition,
    StrategyEvaluationResult,
    StrategyEvidenceQuality,
    StrategyRule,
    TradeIntent,
)
from btg_ai_trader.strategy.engine import evaluate_strategy, verify_deterministic_equivalence
from btg_ai_trader.strategy.risk_adapter import to_risk_proposal

__all__ = [
    "CandidateStrategy",
    "ComparisonOperator",
    "DecisionOpportunity",
    "DecisionReason",
    "EconomicDirection",
    "EconomicObjective",
    "StrategyDecision",
    "StrategyDisposition",
    "StrategyEvaluationResult",
    "StrategyEvidenceQuality",
    "StrategyRule",
    "TradeIntent",
    "evaluate_strategy",
    "to_risk_proposal",
    "verify_deterministic_equivalence",
]
