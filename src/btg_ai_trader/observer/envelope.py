"""Canonical v1 observation envelope, with no implicit context or schema fallback."""

from dataclasses import dataclass
from enum import Enum

from btg_ai_trader.observer.identity import (
    CorrelationId,
    EventId,
    ProviderInstrumentRef,
    TradableInstrumentId,
)
from btg_ai_trader.observer.market import Candle, Tick
from btg_ai_trader.observer.temporal import ObservationTimes
from btg_ai_trader.observer.values import MissingReason, require_text


class EventType(Enum):
    TICK = "TICK"
    CANDLE = "CANDLE"


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    event_id: EventId
    event_type: EventType
    source: ProviderInstrumentRef
    instrument_id: TradableInstrumentId | MissingReason
    times: ObservationTimes
    payload: Tick | Candle
    envelope_version: int = 1
    schema_version: int = 1
    external_event_id: str | None = None
    source_sequence: int | None = None
    sequence_scope: str | None = None
    ingestion_order: int | None = None
    correlation_id: CorrelationId | None = None
    causation_id: EventId | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, EventId):
            raise ValueError("event_id must be EventId")
        if not isinstance(self.source, ProviderInstrumentRef):
            raise ValueError("source must be a scoped ProviderInstrumentRef")
        if not isinstance(self.instrument_id, (TradableInstrumentId, MissingReason)):
            raise ValueError("instrument_id must be concrete or explicitly unresolved")
        if not isinstance(self.times, ObservationTimes):
            raise ValueError("times must be ObservationTimes")
        for field in ("envelope_version", "schema_version"):
            version = getattr(self, field)
            if type(version) is not int or version != 1:
                raise ValueError(f"unsupported {field}; only version 1 is declared")
        if not (
            (self.event_type is EventType.TICK and isinstance(self.payload, Tick))
            or (self.event_type is EventType.CANDLE and isinstance(self.payload, Candle))
        ):
            raise ValueError("event_type must match the declared immutable payload")
        if self.external_event_id is not None:
            require_text(self.external_event_id, "external_event_id")
        if (self.source_sequence is None) != (self.sequence_scope is None):
            raise ValueError("source_sequence and sequence_scope must be supplied together")
        if self.sequence_scope is not None:
            require_text(self.sequence_scope, "sequence_scope")
        for field in ("source_sequence", "ingestion_order"):
            value = getattr(self, field)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{field} must be a nonnegative integer or absent")
        if self.correlation_id is not None and not isinstance(self.correlation_id, CorrelationId):
            raise ValueError("correlation_id must be CorrelationId or absent")
        if self.causation_id is not None and not isinstance(self.causation_id, EventId):
            raise ValueError("causation_id must be EventId or absent")
