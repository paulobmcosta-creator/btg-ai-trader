"""Domain models and primitives for deterministic economic backtesting (Sprint 3)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
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

    def validate_quantity(self, quantity: Decimal) -> None:
        """Validate that quantity is positive and strictly aligns with quantity_step."""
        if not isinstance(quantity, Decimal):
            raise ValueError("quantity must be Decimal")
        if quantity <= Decimal("0"):
            raise ValueError("quantity must be strictly positive")
        if (quantity % self.quantity_step) != Decimal("0"):
            raise ValueError(
                f"quantity {quantity} is not an integer multiple "
                f"of quantity_step {self.quantity_step}"
            )

    def round_price_adverse(self, side: Side, price: Decimal) -> Decimal:
        """Deterministically round price to nearest valid tick adversively.

        BUY orders round UP (ROUND_CEILING), higher price paid.
        SELL orders round DOWN (ROUND_FLOOR), lower price received.
        Never rounds favorably to the trading strategy.
        """
        if not isinstance(price, Decimal) or price <= Decimal("0"):
            raise ValueError("price must be positive Decimal")
        if side == Side.BUY:
            ticks = (price / self.tick_size).quantize(Decimal("1"), rounding=ROUND_CEILING)
            return ticks * self.tick_size
        if side == Side.SELL:
            ticks = (price / self.tick_size).quantize(Decimal("1"), rounding=ROUND_FLOOR)
            return ticks * self.tick_size
        raise ValueError(f"unrecognized side: {side}")


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
class BacktestMarkEvidence:
    """Explicit mark-to-market evidence artifact for an open position at window boundary."""

    instrument_id: TradableInstrumentId
    mark_price: Decimal
    mark_time: datetime
    knowledge_time: datetime
    source_event_id: EventId
    valuation_method: str = "MID"

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_id, TradableInstrumentId):
            raise ValueError("instrument_id must be TradableInstrumentId")
        if not isinstance(self.mark_price, Decimal):
            raise ValueError("mark_price must be Decimal")
        if self.mark_price <= Decimal("0"):
            raise ValueError("mark_price must be positive")
        require_utc(self.mark_time, "mark_time")
        require_utc(self.knowledge_time, "knowledge_time")
        if not isinstance(self.source_event_id, EventId):
            raise ValueError("source_event_id must be EventId")
        require_text(self.valuation_method, "valuation_method")


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
    diagnostic_spread_burden: Decimal = Decimal("0")
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
        if not isinstance(self.diagnostic_spread_burden, Decimal):
            raise ValueError("diagnostic_spread_burden must be Decimal")
        if self.diagnostic_spread_burden < Decimal("0"):
            raise ValueError("diagnostic_spread_burden cannot be negative")
        if not isinstance(self.timing, ExecutionTiming):
            raise ValueError("timing must be ExecutionTiming")
        if not isinstance(self.outcome, ExecutionOutcome):
            raise ValueError("outcome must be ExecutionOutcome enum")
        if self.source_event_id is not None and not isinstance(self.source_event_id, EventId):
            raise ValueError("source_event_id must be EventId or None")

        if self.outcome == ExecutionOutcome.FILL:
            if self.quantity <= Decimal("0"):
                raise ValueError("FILL outcome requires strictly positive quantity")
            if self.raw_price <= Decimal("0"):
                raise ValueError("FILL outcome requires strictly positive raw_price")
            if self.fill_price <= Decimal("0"):
                raise ValueError("FILL outcome requires strictly positive fill_price")
            if self.source_event_id is None:
                raise ValueError("FILL outcome requires a non-None source_event_id")
            if self.slippage != abs(self.fill_price - self.raw_price):
                diff = abs(self.fill_price - self.raw_price)
                raise ValueError(
                    f"FILL outcome requires slippage == abs(fill_price - raw_price): "
                    f"slippage={self.slippage}, abs(fill_price - raw_price)={diff}"
                )
        else:
            if self.quantity != Decimal("0"):
                raise ValueError("non-FILL outcome requires executed quantity == 0")
            if self.fill_price != Decimal("0"):
                raise ValueError("non-FILL outcome requires fill_price == 0")
            if self.raw_price != Decimal("0"):
                raise ValueError("non-FILL outcome requires raw_price == 0")
            if self.slippage != Decimal("0"):
                raise ValueError("non-FILL outcome requires slippage == 0")
            if self.explicit_fee != Decimal("0"):
                raise ValueError("non-FILL outcome requires explicit_fee == 0")
            if self.diagnostic_spread_burden != Decimal("0"):
                raise ValueError("non-FILL outcome requires diagnostic_spread_burden == 0")
