"""Deterministic economic backtest execution engine (Sprint 3).

Orchestrates causal event replay, order simulation, fee/slippage application,
simulated position accounting, metrics calculation, and cryptographic provenance.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid5

from btg_ai_trader.backtesting.accounting import (
    BacktestEconomicState,
    EndOfWindowPolicy,
)
from btg_ai_trader.backtesting.assumptions import EconomicAssumptions
from btg_ai_trader.backtesting.domain import (
    ActionIdentity,
    BacktestAction,
    BacktestMarkEvidence,
    InstrumentEconomics,
    SimulatedFill,
)
from btg_ai_trader.backtesting.execution import BACKTEST_UUID_NAMESPACE, simulate_actions
from btg_ai_trader.backtesting.metrics import (
    DescriptiveBacktestMetrics,
    compute_descriptive_metrics,
)
from btg_ai_trader.backtesting.provenance import (
    BacktestInputBoundary,
    BacktestRunManifest,
    compute_actions_hash,
    compute_assumptions_hash,
    compute_instrument_economics_hash,
)
from btg_ai_trader.observer.envelope import EventEnvelope
from btg_ai_trader.observer.identity import RunId, TradableInstrumentId
from btg_ai_trader.observer.market import Tick
from btg_ai_trader.observer.provenance import CodeRevision, ConfigHash
from btg_ai_trader.replay.core import CausalMarketReplaySchedule


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


def validate_action_sequence(
    actions: Sequence[BacktestAction],
    instrument_id: TradableInstrumentId,
) -> None:
    """Validate action sequence for order, idempotency, causality, and instrument match."""
    seen_ids: set[ActionIdentity] = set()
    prev_cutoff: datetime | None = None
    prev_decision: datetime | None = None
    prev_ready: datetime | None = None

    for act in actions:
        if act.instrument_id != instrument_id:
            raise ValueError(
                f"Action instrument {act.instrument_id} does not match "
                f"engine instrument {instrument_id}"
            )
        if act.action_id in seen_ids:
            raise ValueError(f"duplicate action_id rejected: {act.action_id.value}")
        seen_ids.add(act.action_id)

        if prev_cutoff is not None and act.knowledge_cutoff < prev_cutoff:
            raise ValueError(
                "action sequence contradicts knowledge_cutoff causality: regression rejected"
            )
        if prev_decision is not None and act.decision_time < prev_decision:
            raise ValueError(
                "action sequence contradicts decision_time causality: regression rejected"
            )
        if prev_ready is not None and act.order_ready_time < prev_ready:
            raise ValueError(
                "action sequence contradicts order_ready_time causality: regression rejected"
            )

        prev_cutoff = act.knowledge_cutoff
        prev_decision = act.decision_time
        prev_ready = act.order_ready_time


class DeterministicEconomicBacktester:
    """Deterministic Economic Backtesting Kernel for Sprint 3.

    Enforces strict causal ordering, side-aware execution, deterministic adverse
    slippage, explicit fees, non-negative latency, and audit provenance.
    """

    def __init__(
        self,
        instrument_economics: InstrumentEconomics,
        assumptions: EconomicAssumptions,
        code_revision: CodeRevision | str,
        end_of_window_policy: EndOfWindowPolicy = EndOfWindowPolicy.KEEP_OPEN,
    ) -> None:
        if not isinstance(instrument_economics, InstrumentEconomics):
            raise ValueError("instrument_economics must be InstrumentEconomics")
        if not isinstance(assumptions, EconomicAssumptions):
            raise ValueError("assumptions must be EconomicAssumptions")
        if not isinstance(end_of_window_policy, EndOfWindowPolicy):
            raise ValueError("end_of_window_policy must be EndOfWindowPolicy enum")
        if code_revision is None:
            raise ValueError("code_revision must be explicitly provided")
        resolved_revision = (
            code_revision
            if isinstance(code_revision, CodeRevision)
            else CodeRevision(str(code_revision))
        )

        self.instrument_economics = instrument_economics
        self.assumptions = assumptions
        self.end_of_window_policy = end_of_window_policy
        self.code_revision = resolved_revision

    def run(
        self,
        actions: Sequence[BacktestAction],
        market_events_or_schedule: (
            CausalMarketReplaySchedule | Sequence[EventEnvelope] | None
        ) = None,
        *,
        replay_schedule: CausalMarketReplaySchedule | None = None,
        market_events: Sequence[EventEnvelope] | None = None,
        run_id: ActionIdentity | RunId | str | None = None,
        source_run_id: RunId | str | None = None,
        source_code_revision: CodeRevision | str | None = None,
        source_config_hash: ConfigHash | str | None = None,
        provider_id: str | None = None,
        capture_scope: str | None = None,
        session_id: str | None = None,
        created_at: datetime | None = None,
    ) -> BacktestResult:
        """Run deterministic backtest over the causal event stream."""
        # 1. Validate action sequence
        validate_action_sequence(actions, self.instrument_economics.instrument_id)

        # 2. Resolve replay schedule and events
        resolved_schedule = replay_schedule
        resolved_events_input = market_events
        if market_events_or_schedule is not None:
            if isinstance(market_events_or_schedule, CausalMarketReplaySchedule):
                resolved_schedule = market_events_or_schedule
            elif isinstance(market_events_or_schedule, Sequence):
                resolved_events_input = market_events_or_schedule
            else:
                raise ValueError(
                    "market_events_or_schedule must be CausalMarketReplaySchedule "
                    "or Sequence[EventEnvelope]"
                )

        schedule: CausalMarketReplaySchedule
        if resolved_schedule is not None:
            if not isinstance(resolved_schedule, CausalMarketReplaySchedule):
                raise ValueError("replay_schedule must be CausalMarketReplaySchedule")
            schedule = resolved_schedule
            events = tuple(schedule.events)
        elif resolved_events_input is not None:
            if source_run_id is None:
                raise ValueError("source_run_id must be provided when using raw market_events")
            if source_code_revision is None:
                raise ValueError(
                    "source_code_revision must be provided when using raw market_events"
                )
            if source_config_hash is None:
                raise ValueError("source_config_hash must be provided when using raw market_events")
            if provider_id is None:
                raise ValueError("provider_id must be provided when using raw market_events")
            if capture_scope is None:
                raise ValueError("capture_scope must be provided when using raw market_events")

            ev_tuple = tuple(resolved_events_input)
            resolved_s_run_id = (
                source_run_id if isinstance(source_run_id, RunId) else RunId(str(source_run_id))
            )
            resolved_s_code_rev = (
                source_code_revision
                if isinstance(source_code_revision, CodeRevision)
                else CodeRevision(str(source_code_revision))
            )
            resolved_s_cfg_hash = (
                source_config_hash
                if isinstance(source_config_hash, ConfigHash)
                else ConfigHash(str(source_config_hash))
            )

            schedule = CausalMarketReplaySchedule(
                events=ev_tuple,
                run_id=resolved_s_run_id,
                code_revision=resolved_s_code_rev,
                config_hash=resolved_s_cfg_hash,
                provider_id=provider_id,
                capture_scope=capture_scope,
            )
            events = tuple(schedule.events)
        else:
            raise ValueError("Either replay_schedule or market_events must be provided")

        # 3. Resolve Backtest RunId BEFORE execution and validate UUID
        resolved_run_id: ActionIdentity
        if run_id is not None:
            if isinstance(run_id, ActionIdentity):
                resolved_run_id = ActionIdentity(str(UUID(run_id.value)))
            elif isinstance(run_id, RunId):
                resolved_run_id = ActionIdentity(str(UUID(run_id.value)))
            elif isinstance(run_id, str):
                resolved_run_id = ActionIdentity(str(UUID(run_id)))
            else:
                raise ValueError(
                    f"run_id must be ActionIdentity, RunId, or UUID str, got {type(run_id)}"
                )
        elif session_id is not None:
            resolved_run_id = ActionIdentity(
                str(uuid5(BACKTEST_UUID_NAMESPACE, f"backtest.{session_id}"))
            )
        else:
            act_hash = compute_actions_hash(actions).value
            assump_hash = compute_assumptions_hash(
                self.assumptions,
                instrument_economics=self.instrument_economics,
                end_of_window_policy=self.end_of_window_policy,
            ).value
            econ_hash = compute_instrument_economics_hash(self.instrument_economics).value
            policy_str = self.end_of_window_policy.value
            code_rev = self.code_revision.value
            boundary_run_id = schedule.boundary.run_id.value
            seed_str = (
                f"backtest:{boundary_run_id}:{act_hash}:{assump_hash}:{econ_hash}:{policy_str}:{code_rev}"
            )
            resolved_run_id = ActionIdentity(str(uuid5(BACKTEST_UUID_NAMESPACE, seed_str)))

        # 4. Simulate standard action executions propagating resolved_run_id
        simulated_fills = list(
            simulate_actions(
                actions=actions,
                replay_events=events,
                assumptions=self.assumptions,
                instrument_economics=self.instrument_economics,
                run_id=resolved_run_id.value,
            )
        )

        # 5. Apply fills to simulated economic accounting
        state = BacktestEconomicState.initial(self.instrument_economics)
        state = state.apply_fills(simulated_fills)

        # 6. Handle EndOfWindowPolicy if position is still open
        pos = state.positions[0]
        if (
            not pos.is_flat
            and self.end_of_window_policy == EndOfWindowPolicy.CLOSE_AT_LAST_VALID_QUOTE
        ):
            raise NotImplementedError(
                "CLOSE_AT_LAST_VALID_QUOTE is deferred to future sprint (DD-98 deferred); "
                "baseline supports KEEP_OPEN"
            )

        # 7. Mark to market final open position (if any)
        mark_evidence = self._find_latest_mark_price(events)
        if not pos.is_flat:
            if mark_evidence is not None:
                state = state.compute_mark_to_market(
                    {self.instrument_economics.instrument_id: mark_evidence.mark_price},
                    mark_evidence=mark_evidence,
                )
            # If mark_evidence is None: fails closed,
            # keeping unrealized_pnl=None, total_net_pnl=None
        elif mark_evidence is not None:
            state = state.compute_mark_to_market(
                {self.instrument_economics.instrument_id: mark_evidence.mark_price},
                mark_evidence=mark_evidence,
            )
        else:
            state = state.compute_mark_to_market({})

        # 8. Compute descriptive metrics
        metrics = compute_descriptive_metrics(
            actions=actions,
            fills=simulated_fills,
            economic_state=state,
            instrument_economics=self.instrument_economics,
        )

        # 9. Build cryptographic run manifest
        input_boundary = BacktestInputBoundary.create(
            actions=actions,
            code_revision=self.code_revision,
            replay_schedule=schedule,
            events=events,
        )

        manifest_created_at = created_at
        if manifest_created_at is None:
            if events and isinstance(events[-1].times.knowledge_time, datetime):
                manifest_created_at = events[-1].times.knowledge_time
            else:
                manifest_created_at = datetime(2026, 9, 16, 0, 0, 0, tzinfo=UTC)

        manifest = BacktestRunManifest.create(
            run_id=resolved_run_id,
            input_boundary=input_boundary,
            assumptions=self.assumptions,
            instrument_id=self.instrument_economics.instrument_id,
            instrument_economics=self.instrument_economics,
            fills=simulated_fills,
            economic_state=state,
            metrics=metrics,
            end_of_window_policy=self.end_of_window_policy,
            created_at=manifest_created_at,
        )

        return BacktestResult(
            manifest=manifest,
            economic_state=state,
            metrics=metrics,
            fills=tuple(simulated_fills),
        )

    def _find_latest_mark_price(
        self,
        events: Sequence[EventEnvelope],
    ) -> BacktestMarkEvidence | None:
        """Find the latest mid or last trade price for mark-to-market evaluation."""
        for ev in reversed(events):
            if ev.instrument_id != self.instrument_economics.instrument_id:
                continue
            payload = ev.payload
            mark_price: Decimal | None = None
            method: str = ""
            if isinstance(payload, Tick):
                if isinstance(payload.bid, Decimal) and isinstance(payload.ask, Decimal):
                    mark_price = (payload.bid + payload.ask) / Decimal("2")
                    method = "MID_PRICE"
                elif isinstance(payload.last, Decimal):
                    mark_price = payload.last
                    method = "LAST_PRICE"
            elif hasattr(payload, "close") and isinstance(payload.close, Decimal):
                mark_price = payload.close
                method = "CANDLE_CLOSE"

            if mark_price is not None:
                raw_m = ev.times.event_time
                m_time: datetime | None = (
                    raw_m.value
                    if hasattr(raw_m, "value") and isinstance(raw_m.value, datetime)
                    else raw_m
                    if isinstance(raw_m, datetime)
                    else None
                )
                raw_k = ev.times.knowledge_time
                k_time: datetime | None = (
                    raw_k.value
                    if hasattr(raw_k, "value") and isinstance(raw_k.value, datetime)
                    else raw_k
                    if isinstance(raw_k, datetime)
                    else None
                )
                if m_time is not None and k_time is not None:
                    return BacktestMarkEvidence(
                        instrument_id=self.instrument_economics.instrument_id,
                        mark_price=mark_price,
                        mark_time=m_time,
                        knowledge_time=k_time,
                        source_event_id=ev.event_id,
                        valuation_method=method,
                    )
        return None
