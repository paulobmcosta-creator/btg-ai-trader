"""Finite canonical fact classification and explicit late annotations, without I/O."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from btg_ai_trader.observer.envelope import EventEnvelope
from btg_ai_trader.observer.identity import TradableInstrumentId
from btg_ai_trader.observer.values import require_text


def _fact(event: EventEnvelope) -> tuple[object, ...]:
    """Exclude receipt metadata; preserve intrinsic causal and source evidence."""
    return (
        event.event_type,
        event.source,
        event.instrument_id,
        event.times.event_time,
        event.times.effective_time,
        event.payload,
        event.envelope_version,
        event.schema_version,
        event.external_event_id,
        event.source_sequence,
        event.sequence_scope,
        event.correlation_id,
        event.causation_id,
    )


@dataclass(frozen=True, slots=True)
class DedupState:
    session_scope: str
    capacity: int
    canonical: tuple[EventEnvelope, ...] = ()

    def __post_init__(self) -> None:
        require_text(self.session_scope, "session_scope")
        if type(self.capacity) is not int or self.capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        if type(self.canonical) is not tuple:
            raise ValueError("canonical records must be an immutable tuple")
        if len(self.canonical) > self.capacity:
            raise ValueError("canonical records exceed capacity")
        if any(type(event) is not EventEnvelope for event in self.canonical):
            raise ValueError("canonical records must be validated EventEnvelope")
        identities = {event.event_id for event in self.canonical}
        if len(identities) != len(self.canonical):
            raise ValueError("canonical EventId must be unique within session_scope")


class DedupStatus(Enum):
    NEW = "NEW"
    DUPLICATE = "DUPLICATE"
    IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
    CAPACITY_EXHAUSTED = "CAPACITY_EXHAUSTED"


@dataclass(frozen=True, slots=True)
class DedupResult:
    status: DedupStatus
    incoming: EventEnvelope
    canonical: EventEnvelope | None
    state: DedupState


def classify_duplicate(state: DedupState, incoming: EventEnvelope) -> DedupResult:
    """Return evidence; a classification is not durable or operational admission."""
    if not isinstance(state, DedupState) or type(incoming) is not EventEnvelope:
        raise ValueError("classification requires DedupState and validated EventEnvelope")
    for canonical in state.canonical:
        if canonical.event_id == incoming.event_id:
            status = (
                DedupStatus.DUPLICATE
                if _fact(canonical) == _fact(incoming)
                else DedupStatus.IDENTITY_CONFLICT
            )
            return DedupResult(status, incoming, canonical, state)
    if len(state.canonical) == state.capacity:
        return DedupResult(DedupStatus.CAPACITY_EXHAUSTED, incoming, None, state)
    updated = DedupState(
        state.session_scope, state.capacity, (*state.canonical, incoming)
    )
    return DedupResult(DedupStatus.NEW, incoming, incoming, updated)


class LateStatus(Enum):
    LATE = "LATE"
    ON_OR_AFTER_FRONTIER = "ON_OR_AFTER_FRONTIER"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class LateAnnotation:
    status: LateStatus
    incoming: EventEnvelope
    frontier: EventEnvelope


def annotate_late(incoming: EventEnvelope, frontier: EventEnvelope) -> LateAnnotation:
    """Compare only explicit comparable evidence; never select or advance a frontier."""
    if type(incoming) is not EventEnvelope or type(frontier) is not EventEnvelope:
        raise ValueError("late annotation requires validated EventEnvelope records")
    event_time = incoming.times.event_time
    frontier_time = frontier.times.event_time
    comparable = (
        isinstance(incoming.instrument_id, TradableInstrumentId)
        and isinstance(frontier.instrument_id, TradableInstrumentId)
        and incoming.instrument_id == frontier.instrument_id
        and incoming.source == frontier.source
        and isinstance(event_time.value, datetime)
        and isinstance(frontier_time.value, datetime)
        and isinstance(event_time.basis, str)
        and isinstance(frontier_time.basis, str)
        and event_time.basis == frontier_time.basis
        and isinstance(event_time.resolution, timedelta)
        and isinstance(frontier_time.resolution, timedelta)
        and event_time.resolution == frontier_time.resolution
    )
    status = LateStatus.UNKNOWN
    if (
        comparable
        and isinstance(event_time.value, datetime)
        and isinstance(frontier_time.value, datetime)
    ):
        status = (
            LateStatus.LATE
            if event_time.value < frontier_time.value
            else LateStatus.ON_OR_AFTER_FRONTIER
        )
    return LateAnnotation(status, incoming, frontier)
