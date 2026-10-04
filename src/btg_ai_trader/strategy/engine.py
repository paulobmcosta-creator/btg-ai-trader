"""Deterministic operational Strategy policy evaluation."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from btg_ai_trader.strategy.domain import (
    CandidateStrategy,
    ComparisonOperator,
    DecisionOpportunity,
    DecisionReason,
    StrategyDecision,
    StrategyDisposition,
    StrategyEvaluationResult,
    StrategyEvidenceQuality,
    StrategyRule,
    TradeIntent,
)


def _matches(value: Decimal, operator: ComparisonOperator, threshold: Decimal) -> bool:
    if operator is ComparisonOperator.LT:
        return value < threshold
    if operator is ComparisonOperator.LE:
        return value <= threshold
    if operator is ComparisonOperator.GE:
        return value >= threshold
    return value > threshold


def _no_trade(
    candidate: CandidateStrategy,
    opportunity: DecisionOpportunity,
    reason: DecisionReason,
) -> StrategyEvaluationResult:
    decision = StrategyDecision._build(
        candidate=candidate,
        opportunity=opportunity,
        disposition=StrategyDisposition.NO_TRADE,
        reason_codes=(reason,),
        matched_rule_id=None,
    )
    return StrategyEvaluationResult(decision=decision, trade_intent=None)


def evaluate_strategy(
    candidate: CandidateStrategy,
    opportunity: DecisionOpportunity,
) -> StrategyEvaluationResult:
    """Evaluate one immutable opportunity under one immutable candidate policy."""

    if opportunity.instrument_id != candidate.instrument_id:
        return _no_trade(candidate, opportunity, DecisionReason.CANDIDATE_INSTRUMENT_MISMATCH)
    if opportunity.portfolio_id != candidate.portfolio_id:
        return _no_trade(candidate, opportunity, DecisionReason.CANDIDATE_PORTFOLIO_MISMATCH)
    if opportunity.input_spec_digest != candidate.input_spec_digest:
        return _no_trade(candidate, opportunity, DecisionReason.INPUT_SPEC_MISMATCH)
    if opportunity.evidence_quality is not StrategyEvidenceQuality.VALID:
        return _no_trade(candidate, opportunity, DecisionReason.EVIDENCE_NOT_VALID)
    max_age = timedelta(seconds=candidate.max_evidence_age_seconds)
    if opportunity.decision_time - opportunity.knowledge_time > max_age:
        return _no_trade(candidate, opportunity, DecisionReason.EVIDENCE_TOO_OLD)
    if any(name not in opportunity.signals for name in candidate.required_signals):
        return _no_trade(candidate, opportunity, DecisionReason.MISSING_REQUIRED_SIGNAL)

    matched_rule: StrategyRule | None = None
    for rule in candidate.rules:
        if _matches(opportunity.signals[rule.signal_name], rule.operator, rule.threshold):
            matched_rule = rule
            break
    if matched_rule is None:
        return _no_trade(candidate, opportunity, DecisionReason.NO_RULE_MATCHED)

    decision = StrategyDecision._build(
        candidate=candidate,
        opportunity=opportunity,
        disposition=StrategyDisposition.PROPOSE_TRADE,
        reason_codes=(DecisionReason.RULE_MATCHED,),
        matched_rule_id=matched_rule.rule_id,
    )
    intent = TradeIntent._build(
        decision=decision,
        candidate=candidate,
        opportunity=opportunity,
        objective=matched_rule.objective,
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
