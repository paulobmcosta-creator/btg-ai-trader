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
from typing import Any

from btg_ai_trader.backtesting.assumptions import EconomicAssumptions
from btg_ai_trader.backtesting.domain import ActionIdentity, BacktestAction
from btg_ai_trader.backtesting.metrics import DescriptiveBacktestMetrics
from btg_ai_trader.observer.envelope import EventEnvelope
from btg_ai_trader.observer.identity import TradableInstrumentId
from btg_ai_trader.observer.market import Tick
from btg_ai_trader.observer.provenance import CodeRevision, ContentHash
from btg_ai_trader.observer.temporal import require_utc
from btg_ai_trader.observer.values import require_text


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


def compute_assumptions_hash(assumptions: EconomicAssumptions) -> ContentHash:
    """Compute deterministic SHA-256 digest over the economic assumptions."""
    data = {
        "assumptions_id": assumptions.assumptions_id,
        "spread_model": {
            "max_spread": str(assumptions.spread_model.max_spread)
            if assumptions.spread_model.max_spread is not None
            else None,
        },
        "slippage_model": {
            "type": assumptions.slippage_model.__class__.__name__,
            "points": str(getattr(assumptions.slippage_model, "adverse_points", "0")),
            "bps": str(getattr(assumptions.slippage_model, "adverse_bps", "0")),
        },
        "fee_schedule": {
            "schedule_id": assumptions.fee_schedule.schedule_id,
            "fixed_per_order": str(assumptions.fee_schedule.fixed_per_order),
            "per_unit": str(assumptions.fee_schedule.per_unit),
            "bps_rate": str(assumptions.fee_schedule.bps_rate),
            "currency": assumptions.fee_schedule.currency,
        },
        "latency_model": {
            "decision_latency_us": assumptions.latency_model.decision_latency_us,
            "transit_latency_us": assumptions.latency_model.transit_latency_us,
        },
        "execution_policy": {
            "small_lot_max_quantity": str(assumptions.execution_policy.small_lot_max_quantity),
            "allow_candle_fills": assumptions.execution_policy.allow_candle_fills,
            "max_quote_age_us": assumptions.execution_policy.max_quote_age_us,
        },
    }
    return sha256_canonical_json(data)


@dataclass(frozen=True, slots=True)
class BacktestInputBoundary:
    """Cryptographic provenance of the input data and environment for a backtest run."""

    dataset_hash: ContentHash
    actions_hash: ContentHash
    code_revision: CodeRevision
    environment_signature: str

    def __post_init__(self) -> None:
        if not isinstance(self.dataset_hash, ContentHash):
            raise ValueError("dataset_hash must be ContentHash")
        if not isinstance(self.actions_hash, ContentHash):
            raise ValueError("actions_hash must be ContentHash")
        if not isinstance(self.code_revision, CodeRevision):
            raise ValueError("code_revision must be CodeRevision")
        require_text(self.environment_signature, "environment_signature")

    @classmethod
    def create(
        cls,
        events: Sequence[EventEnvelope],
        actions: Sequence[BacktestAction],
        code_revision_str: str = "ba6c0c41988fc9fefbdff13b0daedf96301dd74c",
    ) -> BacktestInputBoundary:
        env_sig = f"python={platform.python_version()};os={sys.platform}"
        return cls(
            dataset_hash=compute_dataset_hash(events),
            actions_hash=compute_actions_hash(actions),
            code_revision=CodeRevision(code_revision_str),
            environment_signature=env_sig,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "dataset_hash": self.dataset_hash.value,
            "actions_hash": self.actions_hash.value,
            "code_revision": self.code_revision.value,
            "environment_signature": self.environment_signature,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BacktestInputBoundary:
        return cls(
            dataset_hash=ContentHash(data["dataset_hash"]),
            actions_hash=ContentHash(data["actions_hash"]),
            code_revision=CodeRevision(data["code_revision"]),
            environment_signature=data["environment_signature"],
        )


@dataclass(frozen=True, slots=True)
class BacktestRunManifest:
    """Immutable audit manifest certifying deterministic execution of a backtest run."""

    run_id: ActionIdentity
    created_at: datetime
    input_boundary: BacktestInputBoundary
    assumptions_hash: ContentHash
    instrument_id: TradableInstrumentId
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
            "metrics": {
                "gross_realized_pnl": str(self.metrics.gross_realized_pnl),
                "net_realized_pnl": str(self.metrics.net_realized_pnl),
                "total_explicit_fees": str(self.metrics.total_explicit_fees),
                "diagnostic_slippage_burden": str(self.metrics.diagnostic_slippage_burden),
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
                "max_drawdown_ratio": str(self.metrics.max_drawdown_ratio),
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
        metrics: DescriptiveBacktestMetrics,
        created_at: datetime | None = None,
    ) -> BacktestRunManifest:
        ts = created_at or datetime(2026, 9, 16, 0, 0, 0, tzinfo=UTC)
        assump_hash = compute_assumptions_hash(assumptions)
        unhashed = cls(
            run_id=run_id,
            created_at=ts,
            input_boundary=input_boundary,
            assumptions_hash=assump_hash,
            instrument_id=instrument_id,
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
            metrics=metrics,
            manifest_hash=calculated_hash,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BacktestRunManifest:
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
            max_drawdown_ratio=Decimal(metrics_dict["max_drawdown_ratio"]),
        )
        return cls(
            run_id=ActionIdentity(data["run_id"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            input_boundary=BacktestInputBoundary.from_dict(data["input_boundary"]),
            assumptions_hash=ContentHash(data["assumptions_hash"]),
            instrument_id=TradableInstrumentId(data["instrument_id"]),
            metrics=metrics,
            manifest_hash=ContentHash(data["manifest_hash"]),
        )

    @classmethod
    def from_json(cls, json_str: str) -> BacktestRunManifest:
        return cls.from_dict(json.loads(json_str))
