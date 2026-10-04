"""One-way Strategy-to-Risk adapter with no execution authority."""

from __future__ import annotations

from btg_ai_trader.risk_engine import EconomicDirection as RiskEconomicDirection
from btg_ai_trader.risk_engine import RiskProposal
from btg_ai_trader.strategy.domain import EconomicDirection, TradeIntent

_DIRECTION_MAP = {
    EconomicDirection.INCREASE_LONG: RiskEconomicDirection.INCREASE_LONG,
    EconomicDirection.INCREASE_SHORT: RiskEconomicDirection.INCREASE_SHORT,
    EconomicDirection.DECREASE_LONG: RiskEconomicDirection.DECREASE_LONG,
    EconomicDirection.DECREASE_SHORT: RiskEconomicDirection.DECREASE_SHORT,
}


def to_risk_proposal(intent: TradeIntent) -> RiskProposal:
    """Convert an engine-issued TradeIntent into the exact proposal seen by S7 Risk."""

    if not isinstance(intent, TradeIntent) or not intent.is_engine_issued:
        raise ValueError("RiskProposal requires an engine-issued TradeIntent")
    objective = intent.objective
    return RiskProposal(
        proposal_id=f"risk-proposal:{intent.intent_digest[:24]}",
        instrument_id=intent.instrument_id,
        portfolio_id=intent.portfolio_id,
        direction=_DIRECTION_MAP[objective.direction],
        requested_quantity=objective.requested_quantity,
        quantity_unit=objective.quantity_unit,
        requested_exposure=objective.requested_exposure,
        exposure_unit=objective.exposure_unit,
        created_at=intent.created_at,
        source_digest=intent.intent_digest,
    )
