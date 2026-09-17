"""Deterministic economic backtest execution engine (Sprint 3).

Orchestrates causal event replay, order simulation, fee/slippage application,
simulated position accounting, metrics calculation, and cryptographic provenance.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import NAMESPACE_DNS, uuid4, uuid5

from btg_ai_trader.backtesting.accounting import (
    BacktestEconomicState,
    EndOfWindowPolicy,
)
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
from btg_ai_trader.backtesting.execution import simulate_actions
from btg_ai_trader.backtesting.metrics import (
    DescriptiveBacktestMetrics,
    compute_descriptive_metrics,
)
from btg_ai_trader.backtesting.provenance import (
    BacktestInputBoundary,
    BacktestRunManifest,
)
from btg_ai_trader.observer.envelope import EventEnvelope
from btg_ai_trader.observer.market import Tick


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """Immutable result bundle from a completed deterministic backtest run."""

    manifest: BacktestRunManifest
    economic_state: BacktestEconomicState
    metrics: DescriptiveBacktestMetrics
    fills: tuple[SimulatedFill, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.manifest, BacktestRunManifest):
            raise ValueError("manifest must be BacktestRunManifest")
        if not isinstance(self.economic_state, BacktestEconomicState):
            raise ValueError("economic_state must be BacktestEconomicState")
        if not isinstance(self.metrics, DescriptiveBacktestMetrics):
            raise ValueError("metrics must be DescriptiveBacktestMetrics")
        if type(self.fills) is not tuple:
            raise ValueError("fills must be a tuple")


class DeterministicEconomicBacktester:
    """Deterministic Economic Backtesting Kernel for Sprint 3.

    Enforces strict causal ordering, side-aware execution, deterministic adverse
    slippage, explicit fees, non-negative latency, and audit provenance.
    """

    def __init__(
        self,
        instrument_economics: InstrumentEconomics,
        assumptions: EconomicAssumptions,
        end_of_window_policy: EndOfWindowPolicy = EndOfWindowPolicy.KEEP_OPEN,
        code_revision: str = "ba6c0c41988fc9fefbdff13b0daedf96301dd74c",
    ) -> None:
        if not isinstance(instrument_economics, InstrumentEconomics):
            raise ValueError("instrument_economics must be InstrumentEconomics")
        if not isinstance(assumptions, EconomicAssumptions):
            raise ValueError("assumptions must be EconomicAssumptions")
        if not isinstance(end_of_window_policy, EndOfWindowPolicy):
            raise ValueError("end_of_window_policy must be EndOfWindowPolicy enum")

        self.instrument_economics = instrument_economics
        self.assumptions = assumptions
        self.end_of_window_policy = end_of_window_policy
        self.code_revision = code_revision

    def run(
        self,
        actions: Sequence[BacktestAction],
        market_events: Sequence[EventEnvelope],
        session_id: str | None = None,
        created_at: datetime | None = None,
    ) -> BacktestResult:
        """Run deterministic backtest over the causal event stream."""
        # 1. Validate action instrument IDs
        for act in actions:
            if act.instrument_id != self.instrument_economics.instrument_id:
                raise ValueError(
                    f"Action instrument {act.instrument_id} does not match "
                    f"engine instrument {self.instrument_economics.instrument_id}"
                )

        # 2. Simulate standard action executions
        simulated_fills = list(
            simulate_actions(
                actions=actions,
                replay_events=market_events,
                assumptions=self.assumptions,
                instrument_economics=self.instrument_economics,
            )
        )

        # 3. Apply fills to simulated economic accounting
        state = BacktestEconomicState.initial(self.instrument_economics)
        state = state.apply_fills(simulated_fills)

        # 4. Handle EndOfWindowPolicy if position is still open
        pos = state.positions[0]
        if (
            not pos.is_flat
            and self.end_of_window_policy == EndOfWindowPolicy.CLOSE_AT_LAST_VALID_QUOTE
        ):
            last_quote_price = self._find_last_quote_price(market_events, pos.is_long)
            if last_quote_price is not None:
                close_fill = self._create_close_fill(pos, last_quote_price, market_events)
                simulated_fills.append(close_fill)
                state = state.apply_fills((close_fill,))

        # 5. Mark to market final open position (if any)
        latest_mid_or_last = self._find_latest_mark_price(market_events)
        if latest_mid_or_last is not None:
            state = state.compute_mark_to_market(
                {self.instrument_economics.instrument_id: latest_mid_or_last}
            )

        # 6. Compute descriptive metrics
        metrics = compute_descriptive_metrics(
            actions=actions,
            fills=simulated_fills,
            economic_state=state,
            instrument_economics=self.instrument_economics,
        )

        # 7. Build cryptographic run manifest
        if session_id:
            run_uuid = str(uuid5(NAMESPACE_DNS, f"backtest.{session_id}"))
        else:
            run_uuid = str(uuid4())
        run_id = ActionIdentity(run_uuid)

        input_boundary = BacktestInputBoundary.create(
            events=market_events,
            actions=actions,
            code_revision_str=self.code_revision,
        )

        manifest_created_at = created_at
        if manifest_created_at is None:
            if market_events and isinstance(market_events[-1].times.knowledge_time, datetime):
                manifest_created_at = market_events[-1].times.knowledge_time
            else:
                manifest_created_at = datetime(2026, 9, 16, 0, 0, 0, tzinfo=UTC)

        manifest = BacktestRunManifest.create(
            run_id=run_id,
            input_boundary=input_boundary,
            assumptions=self.assumptions,
            instrument_id=self.instrument_economics.instrument_id,
            metrics=metrics,
            created_at=manifest_created_at,
        )

        return BacktestResult(
            manifest=manifest,
            economic_state=state,
            metrics=metrics,
            fills=tuple(simulated_fills),
        )

    def _find_last_quote_price(
        self,
        events: Sequence[EventEnvelope],
        is_closing_long: bool,
    ) -> Decimal | None:
        """Find the price of the last valid quote for closing an open position."""
        for ev in reversed(events):
            payload = ev.payload
            if isinstance(payload, Tick):
                if is_closing_long and isinstance(payload.bid, Decimal):
                    return payload.bid
                if not is_closing_long and isinstance(payload.ask, Decimal):
                    return payload.ask
        return None

    def _find_latest_mark_price(
        self,
        events: Sequence[EventEnvelope],
    ) -> Decimal | None:
        """Find the latest mid or last trade price for mark-to-market evaluation."""
        for ev in reversed(events):
            payload = ev.payload
            if isinstance(payload, Tick):
                if isinstance(payload.bid, Decimal) and isinstance(payload.ask, Decimal):
                    return (payload.bid + payload.ask) / Decimal("2")
                if isinstance(payload.last, Decimal):
                    return payload.last
            else:
                # Candle
                if isinstance(payload.close, Decimal):
                    return payload.close
        return None

    def _create_close_fill(
        self,
        pos: Any,
        raw_price: Decimal,
        events: Sequence[EventEnvelope],
    ) -> SimulatedFill:
        """Construct synthetic close-out fill with full economic friction."""
        side = Side.SELL if pos.is_long else Side.BUY
        qty = abs(pos.quantity)

        # Apply slippage
        fill_price, slip_points = self.assumptions.slippage_model.apply_slippage(
            side=side,
            raw_price=raw_price,
        )

        # Apply fee
        fee = self.assumptions.fee_schedule.compute_fee(
            quantity=qty,
            fill_price=fill_price,
            money_per_price_unit=self.instrument_economics.money_per_price_unit,
        )

        last_ts = (
            events[-1].times.knowledge_time
            if events and isinstance(events[-1].times.knowledge_time, datetime)
            else datetime(2026, 9, 16, 0, 0, 0, tzinfo=UTC)
        )
        timing = ExecutionTiming(
            knowledge_cutoff=last_ts,
            decision_time=last_ts,
            order_ready_time=last_ts,
            simulated_market_arrival_time=last_ts,
            fill_opportunity_time=last_ts,
        )

        return SimulatedFill(
            fill_id=ActionIdentity(str(uuid4())),
            action_id=ActionIdentity(str(uuid4())),
            instrument_id=self.instrument_economics.instrument_id,
            side=side,
            quantity=qty,
            raw_price=raw_price,
            fill_price=fill_price,
            slippage=slip_points,
            explicit_fee=fee,
            timing=timing,
            outcome=ExecutionOutcome.FILL,
        )
