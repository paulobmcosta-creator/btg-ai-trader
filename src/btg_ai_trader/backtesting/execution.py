"""Deterministic market execution simulation matching research actions to replay events."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid5

from btg_ai_trader.backtesting.assumptions import EconomicAssumptions
from btg_ai_trader.backtesting.domain import (
    ActionIdentity,
    BacktestAction,
    ExecutionOutcome,
    ExecutionTiming,
    InstrumentEconomics,
    Side,
    SimulatedFill,
)
from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.market import Candle, Tick

BACKTEST_UUID_NAMESPACE = UUID("a3b4c5d6-e7f8-4901-b234-56789abcdef0")


def derive_fill_id(
    run_id: str,
    action_id: str,
    ordinal: int,
    source_event_id: str | None,
    outcome: str,
) -> ActionIdentity:
    """Derive deterministic collision-safe ActionIdentity from execution lineage."""
    ev_str = source_event_id or "none"
    name = f"{run_id}:{action_id}:{ordinal}:{ev_str}:{outcome}"
    return ActionIdentity(str(uuid5(BACKTEST_UUID_NAMESPACE, name)))


def simulate_action_execution(
    action: BacktestAction,
    replay_events: Sequence[EventEnvelope],
    assumptions: EconomicAssumptions,
    instrument_economics: InstrumentEconomics,
    *,
    run_id: str = "default-run",
    ordinal: int = 0,
) -> SimulatedFill:
    """Simulate execution of a single BacktestAction against replay events deterministically."""
    if not isinstance(action, BacktestAction):
        raise ValueError("action must be BacktestAction")
    if not isinstance(assumptions, EconomicAssumptions):
        raise ValueError("assumptions must be EconomicAssumptions")
    if not isinstance(instrument_economics, InstrumentEconomics):
        raise ValueError("instrument_economics must be InstrumentEconomics")

    if action.instrument_id != instrument_economics.instrument_id:
        raise ValueError(
            f"action instrument_id {action.instrument_id} does not match "
            f"instrument_economics {instrument_economics.instrument_id}"
        )

    instrument_economics.validate_quantity(action.quantity)

    if assumptions.fee_schedule.currency != instrument_economics.currency:
        raise ValueError(
            f"fee schedule currency {assumptions.fee_schedule.currency} does not match "
            f"instrument currency {instrument_economics.currency}"
        )

    zero_timing = ExecutionTiming(
        knowledge_cutoff=action.knowledge_cutoff,
        decision_time=action.decision_time,
        order_ready_time=action.order_ready_time,
        simulated_market_arrival_time=action.order_ready_time,
        fill_opportunity_time=action.order_ready_time,
    )

    # 1. Capacity check under small-lot assumption
    if action.quantity > assumptions.execution_policy.small_lot_max_quantity:
        fill_id = derive_fill_id(
            run_id, action.action_id.value, ordinal, None, ExecutionOutcome.REJECTED.value
        )
        return SimulatedFill(
            fill_id=fill_id,
            action_id=action.action_id,
            instrument_id=action.instrument_id,
            side=action.side,
            quantity=Decimal("0"),
            raw_price=Decimal("0"),
            fill_price=Decimal("0"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=zero_timing,
            outcome=ExecutionOutcome.REJECTED,
            diagnostic_spread_burden=Decimal("0"),
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
        fill_id = derive_fill_id(
            run_id, action.action_id.value, ordinal, None, ExecutionOutcome.NO_FILL.value
        )
        return SimulatedFill(
            fill_id=fill_id,
            action_id=action.action_id,
            instrument_id=action.instrument_id,
            side=action.side,
            quantity=Decimal("0"),
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
            diagnostic_spread_burden=Decimal("0"),
            reason="NO_MARKET_EVENT_AFTER_ARRIVAL",
        )

    timing = ExecutionTiming(
        knowledge_cutoff=action.knowledge_cutoff,
        decision_time=action.decision_time,
        order_ready_time=simulated_ready,
        simulated_market_arrival_time=simulated_arrival,
        fill_opportunity_time=candidate_kt,
    )

    # 4. Check quote wait window
    wait_limit_us = assumptions.execution_policy.max_execution_evidence_wait_us
    if wait_limit_us is not None:
        delta_us = int((candidate_kt - simulated_arrival).total_seconds() * 1_000_000)
        if delta_us > wait_limit_us:
            fill_id = derive_fill_id(
                run_id,
                action.action_id.value,
                ordinal,
                candidate_event.event_id.value,
                ExecutionOutcome.INDETERMINATE.value,
            )
            return SimulatedFill(
                fill_id=fill_id,
                action_id=action.action_id,
                instrument_id=action.instrument_id,
                side=action.side,
                quantity=Decimal("0"),
                raw_price=Decimal("0"),
                fill_price=Decimal("0"),
                slippage=Decimal("0"),
                explicit_fee=Decimal("0"),
                timing=timing,
                outcome=ExecutionOutcome.INDETERMINATE,
                diagnostic_spread_burden=Decimal("0"),
                source_event_id=candidate_event.event_id,
                reason="NO_EXECUTION_EVIDENCE_WITHIN_WAIT_WINDOW",
            )

    # 5. Check fee schedule validity period
    if not assumptions.fee_schedule.is_effective_at(candidate_kt):
        fill_id = derive_fill_id(
            run_id,
            action.action_id.value,
            ordinal,
            candidate_event.event_id.value,
            ExecutionOutcome.INDETERMINATE.value,
        )
        return SimulatedFill(
            fill_id=fill_id,
            action_id=action.action_id,
            instrument_id=action.instrument_id,
            side=action.side,
            quantity=Decimal("0"),
            raw_price=Decimal("0"),
            fill_price=Decimal("0"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.INDETERMINATE,
            diagnostic_spread_burden=Decimal("0"),
            source_event_id=candidate_event.event_id,
            reason="FEE_SCHEDULE_OUTSIDE_EFFECTIVE_PERIOD",
        )

    # 6. Process according to event type
    if candidate_event.event_type is EventType.TICK and isinstance(candidate_event.payload, Tick):
        bid_val = candidate_event.payload.bid
        ask_val = candidate_event.payload.ask
        if (
            not isinstance(bid_val, Decimal)
            or not isinstance(ask_val, Decimal)
            or bid_val <= Decimal("0")
            or ask_val <= Decimal("0")
        ):
            fill_id = derive_fill_id(
                run_id,
                action.action_id.value,
                ordinal,
                candidate_event.event_id.value,
                ExecutionOutcome.INDETERMINATE.value,
            )
            return SimulatedFill(
                fill_id=fill_id,
                action_id=action.action_id,
                instrument_id=action.instrument_id,
                side=action.side,
                quantity=Decimal("0"),
                raw_price=Decimal("0"),
                fill_price=Decimal("0"),
                slippage=Decimal("0"),
                explicit_fee=Decimal("0"),
                timing=timing,
                outcome=ExecutionOutcome.INDETERMINATE,
                diagnostic_spread_burden=Decimal("0"),
                source_event_id=candidate_event.event_id,
                reason="MISSING_BID_ASK_DATA",
            )

        raw_price, spread_reason = assumptions.spread_model.resolve_executable_price(
            action.side, bid_val, ask_val
        )
        if raw_price is None:
            fill_id = derive_fill_id(
                run_id,
                action.action_id.value,
                ordinal,
                candidate_event.event_id.value,
                ExecutionOutcome.INDETERMINATE.value,
            )
            return SimulatedFill(
                fill_id=fill_id,
                action_id=action.action_id,
                instrument_id=action.instrument_id,
                side=action.side,
                quantity=Decimal("0"),
                raw_price=Decimal("0"),
                fill_price=Decimal("0"),
                slippage=Decimal("0"),
                explicit_fee=Decimal("0"),
                timing=timing,
                outcome=ExecutionOutcome.INDETERMINATE,
                diagnostic_spread_burden=Decimal("0"),
                source_event_id=candidate_event.event_id,
                reason=f"SPREAD_REJECTED_{spread_reason}",
            )

        mid_price = (ask_val + bid_val) / Decimal("2")
        if action.side == Side.BUY:
            diagnostic_spread_burden = (
                (ask_val - mid_price) * action.quantity * instrument_economics.money_per_price_unit
            )
        else:
            diagnostic_spread_burden = (
                (mid_price - bid_val) * action.quantity * instrument_economics.money_per_price_unit
            )

        tentative_fill_price, _ = assumptions.slippage_model.apply_slippage(action.side, raw_price)
        fill_price = instrument_economics.round_price_adverse(action.side, tentative_fill_price)
        actual_slippage = abs(fill_price - raw_price)

        fee = assumptions.fee_schedule.compute_fee(
            action.quantity, fill_price, instrument_economics.money_per_price_unit
        )

        fill_id = derive_fill_id(
            run_id,
            action.action_id.value,
            ordinal,
            candidate_event.event_id.value,
            ExecutionOutcome.FILL.value,
        )
        return SimulatedFill(
            fill_id=fill_id,
            action_id=action.action_id,
            instrument_id=action.instrument_id,
            side=action.side,
            quantity=action.quantity,
            raw_price=raw_price,
            fill_price=fill_price,
            slippage=actual_slippage,
            explicit_fee=fee,
            timing=timing,
            outcome=ExecutionOutcome.FILL,
            diagnostic_spread_burden=diagnostic_spread_burden,
            source_event_id=candidate_event.event_id,
            reason="FILLED_AT_MARKET",
        )

    if candidate_event.event_type is EventType.CANDLE and isinstance(
        candidate_event.payload, Candle
    ):
        # Precise candle execution is deferred in Sprint 3 baseline
        fill_id = derive_fill_id(
            run_id,
            action.action_id.value,
            ordinal,
            candidate_event.event_id.value,
            ExecutionOutcome.INDETERMINATE.value,
        )
        return SimulatedFill(
            fill_id=fill_id,
            action_id=action.action_id,
            instrument_id=action.instrument_id,
            side=action.side,
            quantity=Decimal("0"),
            raw_price=Decimal("0"),
            fill_price=Decimal("0"),
            slippage=Decimal("0"),
            explicit_fee=Decimal("0"),
            timing=timing,
            outcome=ExecutionOutcome.INDETERMINATE,
            diagnostic_spread_burden=Decimal("0"),
            source_event_id=candidate_event.event_id,
            reason="CANDLE_EXECUTION_PATH_UNSUPPORTED",
        )

    # Unknown or unsupported payload
    fill_id = derive_fill_id(
        run_id,
        action.action_id.value,
        ordinal,
        candidate_event.event_id.value,
        ExecutionOutcome.INDETERMINATE.value,
    )
    return SimulatedFill(
        fill_id=fill_id,
        action_id=action.action_id,
        instrument_id=action.instrument_id,
        side=action.side,
        quantity=Decimal("0"),
        raw_price=Decimal("0"),
        fill_price=Decimal("0"),
        slippage=Decimal("0"),
        explicit_fee=Decimal("0"),
        timing=timing,
        outcome=ExecutionOutcome.INDETERMINATE,
        diagnostic_spread_burden=Decimal("0"),
        source_event_id=candidate_event.event_id,
        reason="UNSUPPORTED_EVENT_PAYLOAD",
    )


def simulate_actions(
    actions: Sequence[BacktestAction],
    replay_events: Sequence[EventEnvelope],
    assumptions: EconomicAssumptions,
    instrument_economics: InstrumentEconomics,
    *,
    run_id: str = "default-run",
) -> tuple[SimulatedFill, ...]:
    """Simulate a sequence of BacktestAction instances deterministically in order."""
    return tuple(
        simulate_action_execution(
            action,
            replay_events,
            assumptions,
            instrument_economics,
            run_id=run_id,
            ordinal=idx,
        )
        for idx, action in enumerate(actions)
    )
