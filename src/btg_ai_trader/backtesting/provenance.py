"""Audit manifest and provenance tracking for deterministic backtesting (Sprint 3).

Captures full cryptographic lineage of backtest inputs, assumptions, and outputs.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from btg_ai_trader.backtesting.accounting import (
    BacktestEconomicState,
    EndOfWindowPolicy,
)
from btg_ai_trader.backtesting.assumptions import EconomicAssumptions
from btg_ai_trader.backtesting.domain import (
    ActionIdentity,
    BacktestAction,
    InstrumentEconomics,
    SimulatedFill,
)
from btg_ai_trader.backtesting.metrics import DescriptiveBacktestMetrics
from btg_ai_trader.observer.envelope import EventEnvelope
from btg_ai_trader.observer.identity import EventId, RunId, TradableInstrumentId
from btg_ai_trader.observer.market import Tick
from btg_ai_trader.observer.provenance import CodeRevision, ConfigHash, ContentHash
from btg_ai_trader.observer.temporal import require_utc
from btg_ai_trader.observer.values import require_text
from btg_ai_trader.replay.core import CausalMarketReplaySchedule, ReplayInputBoundary


def sha256_canonical_json(payload: Any) -> ContentHash:
    """Compute SHA-256 ContentHash over canonical JSON representation."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )
    return ContentHash(hashlib.sha256(encoded).hexdigest())


def compute_dataset_hash(events: Sequence[EventEnvelope]) -> ContentHash:
    """Compute deterministic SHA-256 digest over the input market event sequence."""
    records = []
    for ev in events:
        kt_iso = (
            ev.times.knowledge_time.isoformat()
            if isinstance(ev.times.knowledge_time, datetime)
            else str(ev.times.knowledge_time)
        )
        et_iso = (
            ev.times.event_time.isoformat()
            if isinstance(ev.times.event_time, datetime)
            else str(ev.times.event_time)
        )
        payload_data: dict[str, Any] = {"type": ev.payload.__class__.__name__}
        if isinstance(ev.payload, Tick):
            payload_data["bid"] = str(ev.payload.bid)
            payload_data["ask"] = str(ev.payload.ask)
            payload_data["last"] = str(ev.payload.last)
            payload_data["volume"] = str(ev.payload.volume)
        else:
            payload_data["open"] = str(ev.payload.open)
            payload_data["high"] = str(ev.payload.high)
            payload_data["low"] = str(ev.payload.low)
            payload_data["close"] = str(ev.payload.close)
            payload_data["volume"] = str(ev.payload.volume)

        records.append(
            {
                "event_id": ev.event_id.value,
                "source": f"{ev.source.provider}:{ev.source.symbol}",
                "knowledge_time": kt_iso,
                "event_time": et_iso,
                "payload": payload_data,
            }
        )
    return sha256_canonical_json(records)


def compute_actions_hash(actions: Sequence[BacktestAction]) -> ContentHash:
    """Compute deterministic SHA-256 digest over the input backtest action sequence."""
    records = []
    for act in actions:
        records.append(
            {
                "action_id": act.action_id.value,
                "instrument_id": act.instrument_id.value,
                "side": act.side.value,
                "quantity": str(act.quantity),
                "order_style": act.order_style.value,
                "knowledge_cutoff": act.knowledge_cutoff.isoformat(),
                "decision_time": act.decision_time.isoformat(),
                "order_ready_time": act.order_ready_time.isoformat(),
            }
        )
    return sha256_canonical_json(records)


def compute_assumptions_hash(
    assumptions: EconomicAssumptions,
    instrument_economics: InstrumentEconomics | None = None,
    end_of_window_policy: EndOfWindowPolicy | None = None,
) -> ContentHash:
    """Compute deterministic SHA-256 digest over the complete economic assumptions."""
    data: dict[str, Any] = {
        "assumptions_id": assumptions.assumptions_id,
        "spread_model": {
            "require_positive_spread": assumptions.spread_model.require_positive_spread,
            "max_spread": (
                str(assumptions.spread_model.max_spread)
                if assumptions.spread_model.max_spread is not None
                else None
            ),
        },
        "slippage_model": {
            "type": assumptions.slippage_model.__class__.__name__,
            "points": str(getattr(assumptions.slippage_model, "adverse_points", "0")),
            "bps": str(getattr(assumptions.slippage_model, "bps", "0")),
        },
        "fee_schedule": {
            "schedule_id": assumptions.fee_schedule.schedule_id,
            "fixed_per_order": str(assumptions.fee_schedule.fixed_per_order),
            "per_unit": str(assumptions.fee_schedule.per_unit),
            "bps_rate": str(assumptions.fee_schedule.bps_rate),
            "currency": assumptions.fee_schedule.currency,
            "effective_from": (
                assumptions.fee_schedule.effective_from.isoformat()
                if assumptions.fee_schedule.effective_from is not None
                else None
            ),
            "effective_until": (
                assumptions.fee_schedule.effective_until.isoformat()
                if assumptions.fee_schedule.effective_until is not None
                else None
            ),
        },
        "latency_model": {
            "decision_latency_us": assumptions.latency_model.decision_latency_us,
            "transit_latency_us": assumptions.latency_model.transit_latency_us,
        },
        "execution_policy": {
            "small_lot_max_quantity": str(assumptions.execution_policy.small_lot_max_quantity),
            "allow_candle_fills": assumptions.execution_policy.allow_candle_fills,
            "max_execution_evidence_wait_us": (
                assumptions.execution_policy.max_execution_evidence_wait_us
            ),
        },
    }
    if instrument_economics is not None:
        data["instrument_economics"] = {
            "instrument_id": instrument_economics.instrument_id.value,
            "currency": instrument_economics.currency,
            "money_per_price_unit": str(instrument_economics.money_per_price_unit),
            "tick_size": str(instrument_economics.tick_size),
            "quantity_step": str(instrument_economics.quantity_step),
        }
    if end_of_window_policy is not None:
        data["end_of_window_policy"] = end_of_window_policy.value

    return sha256_canonical_json(data)


def compute_instrument_economics_hash(econ: InstrumentEconomics) -> ContentHash:
    """Compute deterministic SHA-256 digest over the InstrumentEconomics configuration."""
    data = {
        "instrument_id": econ.instrument_id.value,
        "currency": econ.currency,
        "money_per_price_unit": str(econ.money_per_price_unit),
        "tick_size": str(econ.tick_size),
        "quantity_step": str(econ.quantity_step),
    }
    return sha256_canonical_json(data)


def compute_fills_hash(fills: Sequence[SimulatedFill]) -> ContentHash:
    """Compute deterministic SHA-256 digest over simulated fill executions."""
    records = []
    for f in fills:
        records.append(
            {
                "fill_id": f.fill_id.value,
                "action_id": f.action_id.value,
                "instrument_id": f.instrument_id.value,
                "side": f.side.value,
                "quantity": str(f.quantity),
                "raw_price": str(f.raw_price),
                "fill_price": str(f.fill_price),
                "slippage": str(f.slippage),
                "explicit_fee": str(f.explicit_fee),
                "outcome": f.outcome.value,
                "source_event_id": f.source_event_id.value if f.source_event_id else None,
                "diagnostic_spread_burden": str(f.diagnostic_spread_burden),
                "fill_opportunity_time": (
                    f.timing.fill_opportunity_time.isoformat()
                    if f.timing.fill_opportunity_time
                    else None
                ),
            }
        )
    return sha256_canonical_json(records)


def compute_economic_state_hash(state: BacktestEconomicState) -> ContentHash:
    """Compute deterministic SHA-256 digest over the final BacktestEconomicState."""
    positions_data = []
    for p in state.positions:
        positions_data.append(
            {
                "instrument_id": p.instrument_id.value,
                "quantity": str(p.quantity),
                "weighted_cost_basis": str(p.weighted_cost_basis),
                "is_flat": p.is_flat,
                "is_long": p.is_long,
                "is_short": p.is_short,
            }
        )
    mark_data = None
    if state.mark_evidence is not None:
        mark_data = {
            "instrument_id": state.mark_evidence.instrument_id.value,
            "mark_price": str(state.mark_evidence.mark_price),
            "mark_time": state.mark_evidence.mark_time.isoformat(),
            "knowledge_time": state.mark_evidence.knowledge_time.isoformat(),
            "source_event_id": state.mark_evidence.source_event_id.value,
            "valuation_method": state.mark_evidence.valuation_method,
        }
    data = {
        "gross_realized_pnl": str(state.pnl.gross_realized_pnl),
        "explicit_fees": str(state.pnl.explicit_fees),
        "net_realized_pnl": str(state.pnl.net_realized_pnl),
        "unrealized_pnl": (
            str(state.pnl.unrealized_pnl) if state.pnl.unrealized_pnl is not None else None
        ),
        "total_net_pnl": (
            str(state.pnl.total_net_pnl) if state.pnl.total_net_pnl is not None else None
        ),
        "diagnostic_slippage_burden": str(state.pnl.diagnostic_slippage_burden),
        "diagnostic_spread_burden": str(state.pnl.diagnostic_spread_burden),
        "positions": positions_data,
        "mark_evidence": mark_data,
    }
    return sha256_canonical_json(data)


def compute_metrics_hash(metrics: DescriptiveBacktestMetrics) -> ContentHash:
    """Compute deterministic SHA-256 digest over descriptive backtest metrics."""
    data = {
        "gross_realized_pnl": str(metrics.gross_realized_pnl),
        "net_realized_pnl": str(metrics.net_realized_pnl),
        "total_explicit_fees": str(metrics.total_explicit_fees),
        "diagnostic_slippage_burden": str(metrics.diagnostic_slippage_burden),
        "diagnostic_spread_burden": str(metrics.diagnostic_spread_burden),
        "turnover": str(metrics.turnover),
        "total_actions": metrics.total_actions,
        "fill_count": metrics.fill_count,
        "no_fill_count": metrics.no_fill_count,
        "indeterminate_count": metrics.indeterminate_count,
        "rejected_count": metrics.rejected_count,
        "fill_rate": str(metrics.fill_rate),
        "closed_trade_count": metrics.closed_trade_count,
        "winning_trade_count": metrics.winning_trade_count,
        "losing_trade_count": metrics.losing_trade_count,
        "breakeven_trade_count": metrics.breakeven_trade_count,
        "hit_rate": str(metrics.hit_rate),
        "average_win": str(metrics.average_win),
        "average_loss": str(metrics.average_loss),
        "gross_profit_factor": str(metrics.gross_profit_factor),
        "gross_expectancy": str(metrics.gross_expectancy),
        "max_drawdown_amount": str(metrics.max_drawdown_amount),
        "max_drawdown_ratio": (
            str(metrics.max_drawdown_ratio) if metrics.max_drawdown_ratio is not None else None
        ),
    }
    return sha256_canonical_json(data)


def _replay_boundary_to_dict(rb: ReplayInputBoundary) -> dict[str, Any]:
    return {
        "run_id": rb.run_id.value,
        "code_revision": rb.code_revision.value,
        "config_hash": rb.config_hash.value,
        "provider_id": rb.provider_id,
        "capture_scope": rb.capture_scope,
        "event_ids": [eid.value for eid in rb.event_ids],
        "content_hashes": [h.value if h is not None else None for h in rb.content_hashes],
        "temporal_semantics": rb.temporal_semantics,
    }


def _replay_boundary_from_dict(d: dict[str, Any]) -> ReplayInputBoundary:
    return ReplayInputBoundary(
        run_id=RunId(d["run_id"]),
        code_revision=CodeRevision(d["code_revision"]),
        config_hash=ConfigHash(d["config_hash"]),
        provider_id=d["provider_id"],
        capture_scope=d["capture_scope"],
        event_ids=tuple(EventId(eid) for eid in d["event_ids"]),
        content_hashes=tuple(
            ContentHash(h) if h is not None else None for h in d.get("content_hashes", ())
        ),
        temporal_semantics=d.get("temporal_semantics", "knowledge_time_v1"),
    )


@dataclass(frozen=True, slots=True)
class BacktestInputBoundary:
    """Cryptographic provenance of the input data and environment for a backtest run."""

    replay_boundary: ReplayInputBoundary
    actions_hash: ContentHash
    code_revision: CodeRevision
    environment_signature: str
    derived_input_digest: ContentHash | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.replay_boundary, ReplayInputBoundary):
            raise ValueError("replay_boundary must be ReplayInputBoundary")
        if not isinstance(self.actions_hash, ContentHash):
            raise ValueError("actions_hash must be ContentHash")
        if not isinstance(self.code_revision, CodeRevision):
            raise ValueError("code_revision must be CodeRevision")
        require_text(self.environment_signature, "environment_signature")
        if self.derived_input_digest is not None and not isinstance(
            self.derived_input_digest, ContentHash
        ):
            raise ValueError("derived_input_digest must be ContentHash or None")

    @property
    def dataset_hash(self) -> ContentHash:
        """Derived dataset hash for compatibility."""
        if self.derived_input_digest is not None:
            return self.derived_input_digest
        return sha256_canonical_json([eid.value for eid in self.replay_boundary.event_ids])

    @classmethod
    def create(
        cls,
        first_arg: Sequence[EventEnvelope] | Sequence[BacktestAction] | None = None,
        second_arg: (
            Sequence[BacktestAction] | Sequence[EventEnvelope] | CodeRevision | str | None
        ) = None,
        code_revision: CodeRevision | str | None = None,
        *,
        events: Sequence[EventEnvelope] | None = None,
        actions: Sequence[BacktestAction] | None = None,
        replay_schedule: CausalMarketReplaySchedule | None = None,
        replay_boundary: ReplayInputBoundary | None = None,
        run_id: RunId | str | None = None,
        config_hash: ConfigHash | str | None = None,
        provider_id: str | None = None,
        capture_scope: str | None = None,
    ) -> BacktestInputBoundary:
        resolved_events: Sequence[EventEnvelope] | None = events
        resolved_actions: Sequence[BacktestAction] | None = actions
        resolved_code_raw: CodeRevision | str | None = code_revision

        if first_arg is not None:
            if (
                isinstance(first_arg, Sequence)
                and len(first_arg) > 0
                and isinstance(first_arg[0], EventEnvelope)
            ):
                resolved_events = cast(Sequence[EventEnvelope], first_arg)
                if isinstance(second_arg, Sequence):
                    resolved_actions = cast(Sequence[BacktestAction], second_arg)
                elif second_arg is not None and resolved_code_raw is None:
                    resolved_code_raw = second_arg
            elif (
                isinstance(first_arg, Sequence)
                and len(first_arg) > 0
                and isinstance(first_arg[0], BacktestAction)
            ):
                resolved_actions = cast(Sequence[BacktestAction], first_arg)
                if isinstance(second_arg, CodeRevision | str):
                    resolved_code_raw = second_arg
                elif isinstance(second_arg, Sequence):
                    resolved_events = cast(Sequence[EventEnvelope], second_arg)
            elif isinstance(first_arg, Sequence) and len(first_arg) == 0:
                if isinstance(second_arg, Sequence):
                    resolved_events = cast(Sequence[EventEnvelope], first_arg)
                    resolved_actions = cast(Sequence[BacktestAction], second_arg)
                else:
                    resolved_actions = cast(Sequence[BacktestAction], first_arg)
                    if isinstance(second_arg, CodeRevision | str):
                        resolved_code_raw = second_arg

        if resolved_code_raw is None:
            raise ValueError("code_revision must be explicitly provided")

        resolved_revision = (
            resolved_code_raw
            if isinstance(resolved_code_raw, CodeRevision)
            else CodeRevision(str(resolved_code_raw))
        )
        act_seq = resolved_actions if resolved_actions is not None else ()
        resolved_actions_hash = compute_actions_hash(act_seq)
        env_sig = f"python={platform.python_version()};os={sys.platform}"

        resolved_derived_digest: ContentHash | None = None
        if resolved_events is not None:
            resolved_derived_digest = compute_dataset_hash(resolved_events)

        target_boundary: ReplayInputBoundary | None = None
        if replay_schedule is not None:
            if not isinstance(replay_schedule, CausalMarketReplaySchedule):
                raise ValueError("replay_schedule must be CausalMarketReplaySchedule")
            target_boundary = replay_schedule.boundary
        elif replay_boundary is not None:
            if not isinstance(replay_boundary, ReplayInputBoundary):
                raise ValueError("replay_boundary must be ReplayInputBoundary")
            target_boundary = replay_boundary

        if target_boundary is not None:
            if resolved_events is not None:
                ev_tuple = tuple(resolved_events)
                ev_ids = tuple(ev.event_id for ev in ev_tuple)
                if ev_ids != target_boundary.event_ids:
                    raise ValueError(
                        f"Event IDs in events ({len(ev_ids)}) do not match "
                        f"replay boundary event_ids ({len(target_boundary.event_ids)})"
                    )
                for ev in ev_tuple:
                    if ev.source.provider != target_boundary.provider_id:
                        raise ValueError(
                            f"Event provider {ev.source.provider} does not match "
                            f"replay boundary provider {target_boundary.provider_id}"
                        )
                    if ev.source.scope != target_boundary.capture_scope:
                        raise ValueError(
                            f"Event capture scope {ev.source.scope} does not match "
                            f"replay boundary capture scope {target_boundary.capture_scope}"
                        )
            return cls(
                replay_boundary=target_boundary,
                actions_hash=resolved_actions_hash,
                code_revision=resolved_revision,
                environment_signature=env_sig,
                derived_input_digest=resolved_derived_digest,
            )

        # Neither replay_schedule nor replay_boundary provided:
        # All provenance fields are strictly required without synthetic fallbacks
        if resolved_events is None:
            raise ValueError(
                "BacktestInputBoundary requires replay_schedule, replay_boundary, "
                "or explicit events with full source provenance"
            )
        if run_id is None:
            raise ValueError(
                "run_id must be explicitly provided when building boundary from raw events"
            )
        if config_hash is None:
            raise ValueError(
                "config_hash must be explicitly provided when building boundary from raw events"
            )
        if provider_id is None:
            raise ValueError(
                "provider_id must be explicitly provided when building boundary from raw events"
            )
        if capture_scope is None:
            raise ValueError(
                "capture_scope must be explicitly provided when building boundary from raw events"
            )

        ev_list = tuple(resolved_events)
        resolved_run_id = run_id if isinstance(run_id, RunId) else RunId(str(run_id))
        resolved_cfg_hash = (
            config_hash if isinstance(config_hash, ConfigHash) else ConfigHash(str(config_hash))
        )

        rb = ReplayInputBoundary.from_events(
            ev_list,
            run_id=resolved_run_id,
            code_revision=resolved_revision,
            config_hash=resolved_cfg_hash,
            provider_id=provider_id,
            capture_scope=capture_scope,
        )

        return cls(
            replay_boundary=rb,
            actions_hash=resolved_actions_hash,
            code_revision=resolved_revision,
            environment_signature=env_sig,
            derived_input_digest=resolved_derived_digest,
        )

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "replay_boundary": _replay_boundary_to_dict(self.replay_boundary),
            "actions_hash": self.actions_hash.value,
            "code_revision": self.code_revision.value,
            "environment_signature": self.environment_signature,
            "dataset_hash": self.dataset_hash.value,
        }
        if self.derived_input_digest is not None:
            d["derived_input_digest"] = self.derived_input_digest.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BacktestInputBoundary:
        rb = _replay_boundary_from_dict(data["replay_boundary"])
        actions_hash = ContentHash(data["actions_hash"])
        code_revision = CodeRevision(data["code_revision"])
        env_sig = data["environment_signature"]
        derived_digest = (
            ContentHash(data["derived_input_digest"])
            if data.get("derived_input_digest")
            else (ContentHash(data["dataset_hash"]) if data.get("dataset_hash") else None)
        )
        return cls(
            replay_boundary=rb,
            actions_hash=actions_hash,
            code_revision=code_revision,
            environment_signature=env_sig,
            derived_input_digest=derived_digest,
        )


@dataclass(frozen=True, slots=True)
class BacktestRunManifest:
    """Immutable audit manifest certifying deterministic execution of a backtest run."""

    run_id: ActionIdentity
    created_at: datetime
    input_boundary: BacktestInputBoundary
    assumptions_hash: ContentHash
    instrument_id: TradableInstrumentId
    instrument_economics_hash: ContentHash
    fills_hash: ContentHash
    economic_state_hash: ContentHash
    metrics_hash: ContentHash
    metrics: DescriptiveBacktestMetrics
    manifest_hash: ContentHash

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, ActionIdentity):
            raise ValueError("run_id must be ActionIdentity")
        require_utc(self.created_at, "created_at")
        if not isinstance(self.input_boundary, BacktestInputBoundary):
            raise ValueError("input_boundary must be BacktestInputBoundary")
        if not isinstance(self.assumptions_hash, ContentHash):
            raise ValueError("assumptions_hash must be ContentHash")
        if not isinstance(self.instrument_id, TradableInstrumentId):
            raise ValueError("instrument_id must be TradableInstrumentId")
        if not isinstance(self.instrument_economics_hash, ContentHash):
            raise ValueError("instrument_economics_hash must be ContentHash")
        if not isinstance(self.fills_hash, ContentHash):
            raise ValueError("fills_hash must be ContentHash")
        if not isinstance(self.economic_state_hash, ContentHash):
            raise ValueError("economic_state_hash must be ContentHash")
        if not isinstance(self.metrics_hash, ContentHash):
            raise ValueError("metrics_hash must be ContentHash")
        if not isinstance(self.metrics, DescriptiveBacktestMetrics):
            raise ValueError("metrics must be DescriptiveBacktestMetrics")
        if not isinstance(self.manifest_hash, ContentHash):
            raise ValueError("manifest_hash must be ContentHash")

    def _canonical_payload(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id.value,
            "created_at": self.created_at.isoformat(),
            "input_boundary": self.input_boundary.to_dict(),
            "assumptions_hash": self.assumptions_hash.value,
            "instrument_id": self.instrument_id.value,
            "instrument_economics_hash": self.instrument_economics_hash.value,
            "fills_hash": self.fills_hash.value,
            "economic_state_hash": self.economic_state_hash.value,
            "metrics_hash": self.metrics_hash.value,
            "metrics": {
                "gross_realized_pnl": str(self.metrics.gross_realized_pnl),
                "net_realized_pnl": str(self.metrics.net_realized_pnl),
                "total_explicit_fees": str(self.metrics.total_explicit_fees),
                "diagnostic_slippage_burden": str(self.metrics.diagnostic_slippage_burden),
                "diagnostic_spread_burden": str(self.metrics.diagnostic_spread_burden),
                "turnover": str(self.metrics.turnover),
                "total_actions": self.metrics.total_actions,
                "fill_count": self.metrics.fill_count,
                "no_fill_count": self.metrics.no_fill_count,
                "indeterminate_count": self.metrics.indeterminate_count,
                "rejected_count": self.metrics.rejected_count,
                "fill_rate": str(self.metrics.fill_rate),
                "closed_trade_count": self.metrics.closed_trade_count,
                "winning_trade_count": self.metrics.winning_trade_count,
                "losing_trade_count": self.metrics.losing_trade_count,
                "breakeven_trade_count": self.metrics.breakeven_trade_count,
                "hit_rate": str(self.metrics.hit_rate),
                "average_win": str(self.metrics.average_win),
                "average_loss": str(self.metrics.average_loss),
                "profit_factor": str(self.metrics.profit_factor),
                "expectancy": str(self.metrics.expectancy),
                "max_drawdown_amount": str(self.metrics.max_drawdown_amount),
                "max_drawdown_ratio": (
                    str(self.metrics.max_drawdown_ratio)
                    if self.metrics.max_drawdown_ratio is not None
                    else None
                ),
            },
        }

    def verify_integrity(self) -> bool:
        """Verify that manifest_hash matches the cryptographic hash of the content payload."""
        expected = sha256_canonical_json(self._canonical_payload())
        return self.manifest_hash == expected

    def to_dict(self) -> dict[str, Any]:
        payload = self._canonical_payload()
        payload["manifest_hash"] = self.manifest_hash.value
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)

    @classmethod
    def create(
        cls,
        run_id: ActionIdentity,
        input_boundary: BacktestInputBoundary,
        assumptions: EconomicAssumptions,
        instrument_id: TradableInstrumentId,
        instrument_economics: InstrumentEconomics,
        fills: Sequence[SimulatedFill],
        economic_state: BacktestEconomicState,
        metrics: DescriptiveBacktestMetrics,
        *,
        end_of_window_policy: EndOfWindowPolicy | None = None,
        created_at: datetime | None = None,
    ) -> BacktestRunManifest:
        if not isinstance(instrument_economics, InstrumentEconomics):
            raise ValueError("instrument_economics must be InstrumentEconomics")
        if not isinstance(economic_state, BacktestEconomicState):
            raise ValueError("economic_state must be BacktestEconomicState")
        if not isinstance(metrics, DescriptiveBacktestMetrics):
            raise ValueError("metrics must be DescriptiveBacktestMetrics")
        if type(fills) is not tuple and not isinstance(fills, Sequence):
            raise ValueError("fills must be a sequence of SimulatedFill")

        ts = created_at or datetime(2026, 9, 16, 0, 0, 0, tzinfo=UTC)
        assump_hash = compute_assumptions_hash(
            assumptions,
            instrument_economics=instrument_economics,
            end_of_window_policy=end_of_window_policy,
        )

        resolved_econ_hash = compute_instrument_economics_hash(instrument_economics)
        resolved_fills_hash = compute_fills_hash(fills)
        resolved_state_hash = compute_economic_state_hash(economic_state)
        resolved_metrics_hash = compute_metrics_hash(metrics)

        unhashed = cls(
            run_id=run_id,
            created_at=ts,
            input_boundary=input_boundary,
            assumptions_hash=assump_hash,
            instrument_id=instrument_id,
            instrument_economics_hash=resolved_econ_hash,
            fills_hash=resolved_fills_hash,
            economic_state_hash=resolved_state_hash,
            metrics_hash=resolved_metrics_hash,
            metrics=metrics,
            manifest_hash=ContentHash("0" * 64),
        )
        calculated_hash = sha256_canonical_json(unhashed._canonical_payload())
        return cls(
            run_id=run_id,
            created_at=ts,
            input_boundary=input_boundary,
            assumptions_hash=assump_hash,
            instrument_id=instrument_id,
            instrument_economics_hash=resolved_econ_hash,
            fills_hash=resolved_fills_hash,
            economic_state_hash=resolved_state_hash,
            metrics_hash=resolved_metrics_hash,
            metrics=metrics,
            manifest_hash=calculated_hash,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BacktestRunManifest:
        for h_field in (
            "instrument_economics_hash",
            "fills_hash",
            "economic_state_hash",
            "metrics_hash",
        ):
            if h_field not in data:
                raise ValueError(f"Incomplete manifest payload: missing '{h_field}'")
            val = data[h_field]
            if not isinstance(val, str) or len(val) != 64:
                raise ValueError(f"Invalid hash in manifest payload: '{h_field}'")
            if val == "0" * 64:
                raise ValueError(
                    f"Fabricated sentinel '0'*64 hash rejected for '{h_field}' "
                    "in BacktestRunManifest"
                )

        metrics_dict = data["metrics"]
        metrics = DescriptiveBacktestMetrics(
            gross_realized_pnl=Decimal(metrics_dict["gross_realized_pnl"]),
            net_realized_pnl=Decimal(metrics_dict["net_realized_pnl"]),
            total_explicit_fees=Decimal(metrics_dict["total_explicit_fees"]),
            diagnostic_slippage_burden=Decimal(metrics_dict["diagnostic_slippage_burden"]),
            turnover=Decimal(metrics_dict["turnover"]),
            total_actions=int(metrics_dict["total_actions"]),
            fill_count=int(metrics_dict["fill_count"]),
            no_fill_count=int(metrics_dict["no_fill_count"]),
            indeterminate_count=int(metrics_dict["indeterminate_count"]),
            rejected_count=int(metrics_dict["rejected_count"]),
            fill_rate=Decimal(metrics_dict["fill_rate"]),
            closed_trade_count=int(metrics_dict["closed_trade_count"]),
            winning_trade_count=int(metrics_dict["winning_trade_count"]),
            losing_trade_count=int(metrics_dict["losing_trade_count"]),
            breakeven_trade_count=int(metrics_dict["breakeven_trade_count"]),
            hit_rate=Decimal(metrics_dict["hit_rate"]),
            average_win=Decimal(metrics_dict["average_win"]),
            average_loss=Decimal(metrics_dict["average_loss"]),
            profit_factor=Decimal(metrics_dict["profit_factor"]),
            expectancy=Decimal(metrics_dict["expectancy"]),
            max_drawdown_amount=Decimal(metrics_dict["max_drawdown_amount"]),
            max_drawdown_ratio=(
                Decimal(metrics_dict["max_drawdown_ratio"])
                if metrics_dict.get("max_drawdown_ratio") is not None
                else None
            ),
            diagnostic_spread_burden=(
                Decimal(metrics_dict["diagnostic_spread_burden"])
                if metrics_dict.get("diagnostic_spread_burden") is not None
                else Decimal("0")
            ),
        )
        manifest = cls(
            run_id=ActionIdentity(data["run_id"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            input_boundary=BacktestInputBoundary.from_dict(data["input_boundary"]),
            assumptions_hash=ContentHash(data["assumptions_hash"]),
            instrument_id=TradableInstrumentId(data["instrument_id"]),
            instrument_economics_hash=ContentHash(data["instrument_economics_hash"]),
            fills_hash=ContentHash(data["fills_hash"]),
            economic_state_hash=ContentHash(data["economic_state_hash"]),
            metrics_hash=ContentHash(data["metrics_hash"]),
            metrics=metrics,
            manifest_hash=ContentHash(data["manifest_hash"]),
        )
        if not manifest.verify_integrity():
            raise ValueError("Manifest integrity verification failed: hash mismatch")
        return manifest

    @classmethod
    def from_json(cls, json_str: str) -> BacktestRunManifest:
        return cls.from_dict(json.loads(json_str))
