"""Deterministic operational Strategy policy evaluation."""

from __future__ import annotations

from btg_ai_trader.strategy.domain import (
    CandidateStrategy,
    DecisionOpportunity,
    StrategyDecision,
    StrategyDisposition,
    StrategyEvaluationResult,
    TradeIntent,
)


def evaluate_strategy(
    candidate: CandidateStrategy,
    opportunity: DecisionOpportunity,
) -> StrategyEvaluationResult:
    """Evaluate one immutable opportunity under one immutable candidate policy."""

    decision = StrategyDecision._issue(candidate=candidate, opportunity=opportunity)
    if decision.disposition is StrategyDisposition.NO_TRADE:
        return StrategyEvaluationResult(decision=decision, trade_intent=None)

    intent = TradeIntent._build(
        decision=decision,
        candidate=candidate,
        opportunity=opportunity,
    )
    return StrategyEvaluationResult(decision=decision, trade_intent=intent)


def verify_deterministic_equivalence(
    candidate: CandidateStrategy,
    opportunity: DecisionOpportunity,
) -> bool:
    """Re-evaluate identical immutable inputs and compare canonical digests."""

    first = evaluate_strategy(candidate, opportunity)
    second = evaluate_strategy(candidate, opportunity)
    return first.result_digest == second.result_digest
