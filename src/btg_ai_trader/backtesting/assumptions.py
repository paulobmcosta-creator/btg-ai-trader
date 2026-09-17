"""Deterministic execution assumptions for economic backtesting (Sprint 3)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Protocol

from btg_ai_trader.backtesting.domain import Side
from btg_ai_trader.observer.temporal import require_utc
from btg_ai_trader.observer.values import require_text


@dataclass(frozen=True, slots=True)
class SpreadModel:
    """Side-aware executable pricing and spread validation model."""

    require_positive_spread: bool = True
    max_spread: Decimal | None = None

    def __post_init__(self) -> None:
        if not self.require_positive_spread:
            raise ValueError(
                "require_positive_spread=False is forbidden in Sprint 3 baseline: "
                "crossed or non-positive quotes are indeterminate"
            )
        if self.max_spread is not None:
            if not isinstance(self.max_spread, Decimal):
                raise ValueError("max_spread must be Decimal or None")
            if self.max_spread <= Decimal("0"):
                raise ValueError("max_spread must be positive")

    def resolve_executable_price(
        self,
        side: Side,
        bid: Decimal | None,
        ask: Decimal | None,
    ) -> tuple[Decimal | None, str]:
        """Resolve executable price consuming Ask for BUY and Bid for SELL.

        Mid-price is explicitly forbidden as an aggressive execution price.
        """
        if bid is None or ask is None:
            return (None, "MISSING_QUOTE")
        if not isinstance(bid, Decimal) or not isinstance(ask, Decimal):
            raise ValueError("bid and ask must be Decimal")
        if bid <= Decimal("0") or ask <= Decimal("0"):
            return (None, "NON_POSITIVE_PRICE")

        spread = ask - bid
        if spread <= Decimal("0"):
            return (None, "NON_POSITIVE_SPREAD")
        if self.max_spread is not None and spread > self.max_spread:
            return (None, "SPREAD_EXCEEDS_MAX")

        if side == Side.BUY:
            return (ask, "ASK_CONSUMED")
        if side == Side.SELL:
            return (bid, "BID_CONSUMED")
        raise ValueError(f"unrecognized side: {side}")


class SlippageModel(Protocol):
    """Protocol for deterministic adverse slippage computation."""

    def apply_slippage(self, side: Side, raw_price: Decimal) -> tuple[Decimal, Decimal]:
        """Return (fill_price, slippage_amount).

        Invariants:
        - BUY: fill_price >= raw_price (slippage >= 0)
        - SELL: fill_price <= raw_price (slippage >= 0)
        Favorable slippage is strictly prohibited.
        """
        ...


@dataclass(frozen=True, slots=True)
class ZeroSlippageModel:
    """Explicit zero slippage model.

    Zero slippage is only valid when explicitly configured.
    """

    def apply_slippage(self, side: Side, raw_price: Decimal) -> tuple[Decimal, Decimal]:
        if not isinstance(raw_price, Decimal) or raw_price <= Decimal("0"):
            raise ValueError("raw_price must be positive Decimal")
        return (raw_price, Decimal("0"))


@dataclass(frozen=True, slots=True)
class FixedPointsSlippageModel:
    """Adverse slippage by a fixed absolute price point/tick amount."""

    adverse_points: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.adverse_points, Decimal):
            raise ValueError("adverse_points must be Decimal")
        if self.adverse_points < Decimal("0"):
            raise ValueError("adverse_points cannot be negative")

    def apply_slippage(self, side: Side, raw_price: Decimal) -> tuple[Decimal, Decimal]:
        if not isinstance(raw_price, Decimal) or raw_price <= Decimal("0"):
            raise ValueError("raw_price must be positive Decimal")

        if side == Side.BUY:
            fill_price = raw_price + self.adverse_points
            return (fill_price, self.adverse_points)
        if side == Side.SELL:
            fill_price = raw_price - self.adverse_points
            if fill_price <= Decimal("0"):
                raise ValueError(
                    f"adverse slippage points {self.adverse_points} "
                    f"implies non-positive fill price: {fill_price}"
                )
            return (fill_price, self.adverse_points)
        raise ValueError(f"unrecognized side: {side}")


@dataclass(frozen=True, slots=True)
class FixedBpsSlippageModel:
    """Adverse slippage by basis points (1 bp = 0.0001)."""

    bps: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.bps, Decimal):
            raise ValueError("bps must be Decimal")
        if self.bps < Decimal("0"):
            raise ValueError("bps cannot be negative")

    def apply_slippage(self, side: Side, raw_price: Decimal) -> tuple[Decimal, Decimal]:
        if not isinstance(raw_price, Decimal) or raw_price <= Decimal("0"):
            raise ValueError("raw_price must be positive Decimal")

        slippage_amt = (raw_price * self.bps) / Decimal("10000")
        if side == Side.BUY:
            fill_price = raw_price + slippage_amt
            return (fill_price, slippage_amt)
        if side == Side.SELL:
            fill_price = raw_price - slippage_amt
            if fill_price <= Decimal("0"):
                raise ValueError(
                    f"adverse slippage bps {self.bps} implies non-positive fill price: {fill_price}"
                )
            return (fill_price, slippage_amt)
        raise ValueError(f"unrecognized side: {side}")


FixedPercentageSlippageModel = FixedBpsSlippageModel


@dataclass(frozen=True, slots=True)
class FeeSchedule:
    """Explicit configurable fee schedule.

    Does not claim historical B3 accuracy without explicitly verified evidence.
    """

    schedule_id: str
    fixed_per_order: Decimal = Decimal("0")
    per_unit: Decimal = Decimal("0")
    bps_rate: Decimal = Decimal("0")
    currency: str = "BRL"
    effective_from: datetime | None = None
    effective_until: datetime | None = None

    def __post_init__(self) -> None:
        require_text(self.schedule_id, "schedule_id")
        require_text(self.currency, "currency")
        if not isinstance(self.fixed_per_order, Decimal) or self.fixed_per_order < Decimal("0"):
            raise ValueError("fixed_per_order must be nonnegative Decimal")
        if not isinstance(self.per_unit, Decimal) or self.per_unit < Decimal("0"):
            raise ValueError("per_unit must be nonnegative Decimal")
        if not isinstance(self.bps_rate, Decimal) or self.bps_rate < Decimal("0"):
            raise ValueError("bps_rate must be nonnegative Decimal")
        if self.effective_from is not None:
            require_utc(self.effective_from, "effective_from")
        if self.effective_until is not None:
            require_utc(self.effective_until, "effective_until")
        if (
            self.effective_from is not None
            and self.effective_until is not None
            and self.effective_until < self.effective_from
        ):
            raise ValueError("effective_until cannot precede effective_from")

    def is_effective_at(self, t: datetime) -> bool:
        """Check whether timestamp falls within configured effective period."""
        require_utc(t, "t")
        if self.effective_from is not None and t < self.effective_from:
            return False
        if self.effective_until is not None and t > self.effective_until:
            return False
        return True

    def compute_fee(
        self,
        quantity: Decimal,
        fill_price: Decimal,
        money_per_price_unit: Decimal,
    ) -> Decimal:
        if (
            quantity <= Decimal("0")
            or fill_price <= Decimal("0")
            or money_per_price_unit <= Decimal("0")
        ):
            raise ValueError("quantity, fill_price, and money_per_price_unit must be positive")

        notional = quantity * fill_price * money_per_price_unit
        fixed_cost = self.fixed_per_order
        unit_cost = self.per_unit * quantity
        bps_cost = (notional * self.bps_rate) / Decimal("10000")
        return fixed_cost + unit_cost + bps_cost


@dataclass(frozen=True, slots=True)
class LatencyModel:
    """Deterministic latency model expressed in virtual microseconds."""

    decision_latency_us: int = 0
    transit_latency_us: int = 0

    def __post_init__(self) -> None:
        if type(self.decision_latency_us) is not int or self.decision_latency_us < 0:
            raise ValueError("decision_latency_us must be nonnegative integer")
        if type(self.transit_latency_us) is not int or self.transit_latency_us < 0:
            raise ValueError("transit_latency_us must be nonnegative integer")

    def apply_latency(
        self,
        decision_time: datetime,
        order_ready_time: datetime,
    ) -> tuple[datetime, datetime]:
        """Compute simulated order_ready_time and market_arrival_time."""
        require_utc(decision_time, "decision_time")
        require_utc(order_ready_time, "order_ready_time")
        if order_ready_time < decision_time:
            raise ValueError("order_ready_time cannot precede decision_time")

        simulated_ready = max(
            order_ready_time,
            decision_time + timedelta(microseconds=self.decision_latency_us),
        )
        simulated_arrival = simulated_ready + timedelta(microseconds=self.transit_latency_us)
        return (simulated_ready, simulated_arrival)


@dataclass(frozen=True, slots=True, init=False)
class ExecutionPolicy:
    """Execution constraints and fail-closed policies for market simulation."""

    small_lot_max_quantity: Decimal
    allow_candle_fills: bool
    max_execution_evidence_wait_us: int | None

    def __init__(
        self,
        small_lot_max_quantity: Decimal = Decimal("100"),
        allow_candle_fills: bool = False,
        max_execution_evidence_wait_us: int | None = None,
        max_quote_age_us: int | None = None,
    ) -> None:
        resolved_wait = (
            max_execution_evidence_wait_us
            if max_execution_evidence_wait_us is not None
            else max_quote_age_us
        )
        if not isinstance(small_lot_max_quantity, Decimal):
            raise ValueError("small_lot_max_quantity must be Decimal")
        if small_lot_max_quantity <= Decimal("0"):
            raise ValueError("small_lot_max_quantity must be positive")
        if resolved_wait is not None:
            if type(resolved_wait) is not int or resolved_wait <= 0:
                raise ValueError("max_execution_evidence_wait_us must be positive integer or None")

        object.__setattr__(self, "small_lot_max_quantity", small_lot_max_quantity)
        object.__setattr__(self, "allow_candle_fills", allow_candle_fills)
        object.__setattr__(self, "max_execution_evidence_wait_us", resolved_wait)

    @property
    def max_quote_age_us(self) -> int | None:
        return self.max_execution_evidence_wait_us


@dataclass(frozen=True, slots=True)
class EconomicAssumptions:
    """Bundle of all economic simulation assumptions."""

    assumptions_id: str
    spread_model: SpreadModel
    slippage_model: SlippageModel
    fee_schedule: FeeSchedule
    latency_model: LatencyModel
    execution_policy: ExecutionPolicy

    def __post_init__(self) -> None:
        require_text(self.assumptions_id, "assumptions_id")
        if not isinstance(self.spread_model, SpreadModel):
            raise ValueError("spread_model must be SpreadModel")
        if not isinstance(
            self.slippage_model,
            ZeroSlippageModel | FixedPointsSlippageModel | FixedBpsSlippageModel,
        ):
            raise ValueError(
                "slippage_model must be ZeroSlippageModel, FixedPointsSlippageModel, "
                "or FixedBpsSlippageModel"
            )
        if not isinstance(self.fee_schedule, FeeSchedule):
            raise ValueError("fee_schedule must be FeeSchedule")
        if not isinstance(self.latency_model, LatencyModel):
            raise ValueError("latency_model must be LatencyModel")
        if not isinstance(self.execution_policy, ExecutionPolicy):
            raise ValueError("execution_policy must be ExecutionPolicy")
