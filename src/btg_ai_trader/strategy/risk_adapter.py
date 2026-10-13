"""One-way Strategy-to-Risk adapter with consumer-side provenance replay.

The consumer must separately admit policy and causal evidence from a trusted
upstream boundary. Python object identity and SHA digests are not authentication.
"""

from __future__ import annotations

from btg_ai_trader.risk_engine import EconomicDirection as RiskEconomicDirection
from btg_ai_trader.risk_engine import RiskProposal
from btg_ai_trader.strategy.domain import (
    CandidateStrategy,
    DecisionOpportunity,
    EconomicDirection,
    TradeIntent,
)
from btg_ai_trader.strategy.engine import evaluate_strategy

_DIRECTION_MAP = {
    EconomicDirection.INCREASE_LONG: RiskEconomicDirection.INCREASE_LONG,
    EconomicDirection.INCREASE_SHORT: RiskEconomicDirection.INCREASE_SHORT,
    EconomicDirection.DECREASE_LONG: RiskEconomicDirection.DECREASE_LONG,
    EconomicDirection.DECREASE_SHORT: RiskEconomicDirection.DECREASE_SHORT,
}


def to_risk_proposal(
    intent: TradeIntent,
    *,
    admitted_candidate: CandidateStrategy | None = None,
    admitted_opportunity: DecisionOpportunity | None = None,
) -> RiskProposal:
    """Fail closed unless separately admitted inputs reproduce the exact intent.

    The consumer must source both inputs independently of the party supplying
    the intent. Caller-controlled duplicates are NOT independent admission.
    """
    if not isinstance(intent, TradeIntent) or not intent.is_engine_issued:
        raise ValueError("RiskProposal requires an engine-issued TradeIntent")
    if not isinstance(admitted_candidate, CandidateStrategy) or not isinstance(
        admitted_opportunity, DecisionOpportunity
    ):
        raise ValueError(
            "RiskProposal requires independently admitted candidate and opportunity"
        )
    replayed = evaluate_strategy(admitted_candidate, admitted_opportunity)
    expected = replayed.trade_intent
    if expected is None:
        raise ValueError("independent replay did not authorize PROPOSE_TRADE")
    if intent != expected:
        raise ValueError("TradeIntent independent provenance mismatch")

    # Never forward economic fields from the untrusted caller's object.
    objective = expected.objective
    return RiskProposal(
        proposal_id=f"risk-proposal:{expected.intent_digest[:24]}",
        instrument_id=expected.instrument_id,
        portfolio_id=expected.portfolio_id,
        direction=_DIRECTION_MAP[objective.direction],
        requested_quantity=objective.requested_quantity,
        quantity_unit=objective.quantity_unit,
        requested_exposure=objective.requested_exposure,
        exposure_unit=objective.exposure_unit,
        created_at=expected.created_at,
        source_digest=expected.intent_digest,
    )
