"""Domain models and primitives for deterministic economic backtesting (Sprint 3)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from btg_ai_trader.observer.identity import EventId, TradableInstrumentId
from btg_ai_trader.observer.temporal import require_utc
from btg_ai_trader.observer.values import require_text


@dataclass(frozen=True, slots=True)
class ActionIdentity:
    """Immutable UUID identity for a research backtest action or simulated fill."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise ValueError("identity must be canonical UUID text")
        try:
            parsed = UUID(self.value)
        except ValueError as error:
            raise ValueError("identity must be canonical UUID text") from error
        if str(parsed) != self.value:
            raise ValueError("identity must be lowercase hyphenated UUID text")


class Side(str, Enum):
    """Order and execution economic direction."""

    BUY = "BUY"
    SELL = "SELL"


class OrderStyle(str, Enum):
    """Order execution style. The baseline kernel only supports MARKET."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class ExecutionOutcome(str, Enum):
    """Categorical outcome of simulating an order against market evidence."""

    FILL = "FILL"
    NO_FILL = "NO_FILL"
    INDETERMINATE = "INDETERMINATE"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class InstrumentEconomics:
    """Explicit economic parameters for financial instruments in backtesting."""

    instrument_id: TradableInstrumentId
    currency: str
    money_per_price_unit: Decimal
    tick_size: Decimal
    quantity_step: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_id, TradableInstrumentId):
            raise ValueError("instrument_id must be TradableInstrumentId")
        require_text(self.currency, "currency")
        if not isinstance(self.money_per_price_unit, Decimal):
            raise ValueError("money_per_price_unit must be Decimal")
        if self.money_per_price_unit <= Decimal("0"):
            raise ValueError("money_per_price_unit must be positive")
        if not isinstance(self.tick_size, Decimal):
            raise ValueError("tick_size must be Decimal")
        if self.tick_size <= Decimal("0"):
            raise ValueError("tick_size must be positive")
        if not isinstance(self.quantity_step, Decimal):
            raise ValueError("quantity_step must be Decimal")
        if self.quantity_step <= Decimal("0"):
            raise ValueError("quantity_step must be positive")


@dataclass(frozen=True, slots=True)
class ExecutionTiming:
    """Explicit causal temporal timeline for an execution opportunity."""

    knowledge_cutoff: datetime
    decision_time: datetime
    order_ready_time: datetime
    simulated_market_arrival_time: datetime
    fill_opportunity_time: datetime

    def __post_init__(self) -> None:
        require_utc(self.knowledge_cutoff, "knowledge_cutoff")
        require_utc(self.decision_time, "decision_time")
        require_utc(self.order_ready_time, "order_ready_time")
        require_utc(self.simulated_market_arrival_time, "simulated_market_arrival_time")
        require_utc(self.fill_opportunity_time, "fill_opportunity_time")

        if self.decision_time < self.knowledge_cutoff:
            raise ValueError("decision_time cannot precede knowledge_cutoff")
        if self.order_ready_time < self.decision_time:
            raise ValueError("order_ready_time cannot precede decision_time")
        if self.simulated_market_arrival_time < self.order_ready_time:
            raise ValueError("simulated_market_arrival_time cannot precede order_ready_time")
        if self.fill_opportunity_time < self.simulated_market_arrival_time:
            raise ValueError("fill_opportunity_time cannot precede simulated_market_arrival_time")


@dataclass(frozen=True, slots=True)
class BacktestAction:
    """Immutable research action instructing backtest kernel to evaluate execution.

    This is strictly a research simulation instruction and IS NOT a StrategyDecision,
    TradeIntent, RiskDecision, RiskAuthorization, OrderIntent, or ExecutionOrder.
    """

    action_id: ActionIdentity
    instrument_id: TradableInstrumentId
    side: Side
    quantity: Decimal
    order_style: OrderStyle
    knowledge_cutoff: datetime
    decision_time: datetime
    order_ready_time: datetime
    notes: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.action_id, ActionIdentity):
            raise ValueError("action_id must be ActionIdentity")
        if not isinstance(self.instrument_id, TradableInstrumentId):
            raise ValueError("instrument_id must be TradableInstrumentId")
        if not isinstance(self.side, Side):
            raise ValueError("side must be Side enum")
        if not isinstance(self.quantity, Decimal):
            raise ValueError("quantity must be Decimal")
        if self.quantity <= Decimal("0"):
            raise ValueError("quantity must be strictly positive")
        if not isinstance(self.order_style, OrderStyle):
            raise ValueError("order_style must be OrderStyle enum")
        if self.order_style != OrderStyle.MARKET:
            raise ValueError(
                f"order_style {self.order_style} is not supported by the baseline kernel; "
                "only MARKET is supported"
            )
        require_utc(self.knowledge_cutoff, "knowledge_cutoff")
        require_utc(self.decision_time, "decision_time")
        require_utc(self.order_ready_time, "order_ready_time")

        if self.decision_time < self.knowledge_cutoff:
            raise ValueError("decision_time cannot precede knowledge_cutoff")
        if self.order_ready_time < self.decision_time:
            raise ValueError("order_ready_time cannot precede decision_time")


@dataclass(frozen=True, slots=True)
class SimulatedFill:
    """Simulated execution result for a research backtest action."""

    fill_id: ActionIdentity
    action_id: ActionIdentity
    instrument_id: TradableInstrumentId
    side: Side
    quantity: Decimal
    raw_price: Decimal
    fill_price: Decimal
    slippage: Decimal
    explicit_fee: Decimal
    timing: ExecutionTiming
    outcome: ExecutionOutcome
    source_event_id: EventId | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.fill_id, ActionIdentity):
            raise ValueError("fill_id must be ActionIdentity")
        if not isinstance(self.action_id, ActionIdentity):
            raise ValueError("action_id must be ActionIdentity")
        if not isinstance(self.instrument_id, TradableInstrumentId):
            raise ValueError("instrument_id must be TradableInstrumentId")
        if not isinstance(self.side, Side):
            raise ValueError("side must be Side enum")
        if not isinstance(self.quantity, Decimal):
            raise ValueError("quantity must be Decimal")
        if self.quantity < Decimal("0"):
            raise ValueError("quantity cannot be negative")
        if not isinstance(self.raw_price, Decimal):
            raise ValueError("raw_price must be Decimal")
        if not isinstance(self.fill_price, Decimal):
            raise ValueError("fill_price must be Decimal")
        if not isinstance(self.slippage, Decimal):
            raise ValueError("slippage must be Decimal")
        if self.slippage < Decimal("0"):
            raise ValueError("slippage cannot be negative")
        if not isinstance(self.explicit_fee, Decimal):
            raise ValueError("explicit_fee must be Decimal")
        if self.explicit_fee < Decimal("0"):
            raise ValueError("explicit_fee cannot be negative")
        if not isinstance(self.timing, ExecutionTiming):
            raise ValueError("timing must be ExecutionTiming")
        if not isinstance(self.outcome, ExecutionOutcome):
            raise ValueError("outcome must be ExecutionOutcome enum")
        if self.source_event_id is not None and not isinstance(self.source_event_id, EventId):
            raise ValueError("source_event_id must be EventId or None")
