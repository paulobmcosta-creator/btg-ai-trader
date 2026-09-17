"""Deterministic market execution simulation matching research actions to replay events."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from btg_ai_trader.backtesting.assumptions import EconomicAssumptions
from btg_ai_trader.backtesting.domain import (
    ActionIdentity,
    BacktestAction,
    ExecutionOutcome,
    ExecutionTiming,
    InstrumentEconomics,
    SimulatedFill,
)
from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.market import Candle, Tick


def simulate_action_execution(
    action: BacktestAction,
    replay_events: Sequence[EventEnvelope],
    assumptions: EconomicAssumptions,
    instrument_economics: InstrumentEconomics,
) -> SimulatedFill:
    """Simulate execution of a single BacktestAction against replay events deterministically."""
    if not isinstance(action, BacktestAction):
        raise ValueError("action must be BacktestAction")
    if not isinstance(assumptions, EconomicAssumptions):
        raise ValueError("assumptions must be EconomicAssumptions")
    if not isinstance(instrument_economics, InstrumentEconomics):
        raise ValueError("instrument_economics must be InstrumentEconomics")

    zero_timing = ExecutionTiming(
        knowledge_cutoff=action.knowledge_cutoff,
        decision_time=action.decision_time,
        order_ready_time=action.order_ready_time,
        simulated_market_arrival_time=action.order_ready_time,
        fill_opportunity_time=action.order_ready_time,
    )

    # 1. Capacity check under small-lot assumption
    if action.quantity > assumptions.execution_policy.small_lot_max_quantity:
        return SimulatedFill(
            fill_id=ActionIdentity(str(uuid4())),
            action_id=action.action_id,
            instrument_id=action.instrument_id,
            side=action.side,
            quantity=action.quantity,
            raw_price=Decimal("0"),
            fill_price=Decimal("0"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=zero_timing,
            outcome=ExecutionOutcome.REJECTED,
            reason="EXCEEDS_SMALL_LOT_CAPACITY",
        )

    # 2. Virtual latency computation
    simulated_ready, simulated_arrival = assumptions.latency_model.apply_latency(
        action.decision_time, action.order_ready_time
    )

    # 3. Causal scan for first eligible market event
    candidate_event: EventEnvelope | None = None
    candidate_kt: datetime | None = None

    for event in replay_events:
        if event.instrument_id != action.instrument_id:
            continue
        if not isinstance(event.times.knowledge_time, datetime):
            continue
        kt = event.times.knowledge_time
        if kt >= simulated_arrival and kt >= action.knowledge_cutoff:
            candidate_event = event
            candidate_kt = kt
            break

    if candidate_event is None or candidate_kt is None:
        return SimulatedFill(
            fill_id=ActionIdentity(str(uuid4())),
            action_id=action.action_id,
            instrument_id=action.instrument_id,
            side=action.side,
            quantity=action.quantity,
            raw_price=Decimal("0"),
            fill_price=Decimal("0"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=ExecutionTiming(
                knowledge_cutoff=action.knowledge_cutoff,
                decision_time=action.decision_time,
                order_ready_time=simulated_ready,
                simulated_market_arrival_time=simulated_arrival,
                fill_opportunity_time=simulated_arrival,
            ),
            outcome=ExecutionOutcome.NO_FILL,
            reason="NO_MARKET_EVENT_AFTER_ARRIVAL",
        )

    timing = ExecutionTiming(
        knowledge_cutoff=action.knowledge_cutoff,
        decision_time=action.decision_time,
        order_ready_time=simulated_ready,
        simulated_market_arrival_time=simulated_arrival,
        fill_opportunity_time=candidate_kt,
    )

    # 4. Check quote staleness
    if assumptions.execution_policy.max_quote_age_us is not None:
        delta_us = int((candidate_kt - simulated_arrival).total_seconds() * 1_000_000)
        if delta_us > assumptions.execution_policy.max_quote_age_us:
            return SimulatedFill(
                fill_id=ActionIdentity(str(uuid4())),
                action_id=action.action_id,
                instrument_id=action.instrument_id,
                side=action.side,
                quantity=action.quantity,
                raw_price=Decimal("0"),
                fill_price=Decimal("0"),
                slippage=Decimal("0"),
                explicit_fee=Decimal("0"),
                timing=timing,
                outcome=ExecutionOutcome.INDETERMINATE,
                source_event_id=candidate_event.event_id,
                reason="STALE_QUOTE_EXCEEDS_MAX_AGE",
            )

    # 5. Process according to event type
    if candidate_event.event_type is EventType.TICK and isinstance(candidate_event.payload, Tick):
        bid_val = candidate_event.payload.bid
        ask_val = candidate_event.payload.ask
        if not isinstance(bid_val, Decimal) or not isinstance(ask_val, Decimal):
            return SimulatedFill(
                fill_id=ActionIdentity(str(uuid4())),
                action_id=action.action_id,
                instrument_id=action.instrument_id,
                side=action.side,
                quantity=action.quantity,
                raw_price=Decimal("0"),
                fill_price=Decimal("0"),
                slippage=Decimal("0"),
                explicit_fee=Decimal("0"),
                timing=timing,
                outcome=ExecutionOutcome.INDETERMINATE,
                source_event_id=candidate_event.event_id,
                reason="MISSING_BID_ASK_DATA",
            )

        raw_price, spread_reason = assumptions.spread_model.resolve_executable_price(
            action.side, bid_val, ask_val
        )
        if raw_price is None:
            return SimulatedFill(
                fill_id=ActionIdentity(str(uuid4())),
                action_id=action.action_id,
                instrument_id=action.instrument_id,
                side=action.side,
                quantity=action.quantity,
                raw_price=Decimal("0"),
                fill_price=Decimal("0"),
                slippage=Decimal("0"),
                explicit_fee=Decimal("0"),
                timing=timing,
                outcome=ExecutionOutcome.INDETERMINATE,
                source_event_id=candidate_event.event_id,
                reason=f"SPREAD_REJECTED_{spread_reason}",
            )

        fill_price, slippage = assumptions.slippage_model.apply_slippage(action.side, raw_price)
        fee = assumptions.fee_schedule.compute_fee(
            action.quantity, fill_price, instrument_economics.money_per_price_unit
        )

        return SimulatedFill(
            fill_id=ActionIdentity(str(uuid4())),
            action_id=action.action_id,
            instrument_id=action.instrument_id,
            side=action.side,
            quantity=action.quantity,
            raw_price=raw_price,
            fill_price=fill_price,
            slippage=slippage,
            explicit_fee=fee,
            timing=timing,
            outcome=ExecutionOutcome.FILL,
            source_event_id=candidate_event.event_id,
            reason="FILLED_AT_MARKET",
        )

    if candidate_event.event_type is EventType.CANDLE and isinstance(
        candidate_event.payload, Candle
    ):
        if not assumptions.execution_policy.allow_candle_fills:
            return SimulatedFill(
                fill_id=ActionIdentity(str(uuid4())),
                action_id=action.action_id,
                instrument_id=action.instrument_id,
                side=action.side,
                quantity=action.quantity,
                raw_price=Decimal("0"),
                fill_price=Decimal("0"),
                slippage=Decimal("0"),
                explicit_fee=Decimal("0"),
                timing=timing,
                outcome=ExecutionOutcome.INDETERMINATE,
                source_event_id=candidate_event.event_id,
                reason="CANDLE_INTRABAR_TRAJECTORY_AMBIGUOUS_DEFERRED",
            )

        if not isinstance(candidate_event.payload.open, Decimal):
            return SimulatedFill(
                fill_id=ActionIdentity(str(uuid4())),
                action_id=action.action_id,
                instrument_id=action.instrument_id,
                side=action.side,
                quantity=action.quantity,
                raw_price=Decimal("0"),
                fill_price=Decimal("0"),
                slippage=Decimal("0"),
                explicit_fee=Decimal("0"),
                timing=timing,
                outcome=ExecutionOutcome.INDETERMINATE,
                source_event_id=candidate_event.event_id,
                reason="MISSING_CANDLE_OPEN_PRICE",
            )

        raw_price = candidate_event.payload.open
        fill_price, slippage = assumptions.slippage_model.apply_slippage(action.side, raw_price)
        fee = assumptions.fee_schedule.compute_fee(
            action.quantity, fill_price, instrument_economics.money_per_price_unit
        )

        return SimulatedFill(
            fill_id=ActionIdentity(str(uuid4())),
            action_id=action.action_id,
            instrument_id=action.instrument_id,
            side=action.side,
            quantity=action.quantity,
            raw_price=raw_price,
            fill_price=fill_price,
            slippage=slippage,
            explicit_fee=fee,
            timing=timing,
            outcome=ExecutionOutcome.FILL,
            source_event_id=candidate_event.event_id,
            reason="FILLED_AT_CANDLE_OPEN",
        )

    # Unknown or unsupported payload
    return SimulatedFill(
        fill_id=ActionIdentity(str(uuid4())),
        action_id=action.action_id,
        instrument_id=action.instrument_id,
        side=action.side,
        quantity=action.quantity,
        raw_price=Decimal("0"),
        fill_price=Decimal("0"),
        slippage=Decimal("0"),
        explicit_fee=Decimal("0"),
        timing=timing,
        outcome=ExecutionOutcome.INDETERMINATE,
        source_event_id=candidate_event.event_id,
        reason="UNSUPPORTED_EVENT_PAYLOAD",
    )


def simulate_actions(
    actions: Sequence[BacktestAction],
    replay_events: Sequence[EventEnvelope],
    assumptions: EconomicAssumptions,
    instrument_economics: InstrumentEconomics,
) -> tuple[SimulatedFill, ...]:
    """Simulate a sequence of BacktestAction instances deterministically in order."""
    return tuple(
        simulate_action_execution(action, replay_events, assumptions, instrument_economics)
        for action in actions
    )
