"""Deterministic dedup and late evidence without storage, provider or clock effects."""

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast
from uuid import UUID

import pytest

from btg_ai_trader.observer.dedup import (
    DedupState,
    DedupStatus,
    LateStatus,
    annotate_late,
    classify_duplicate,
)
from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.identity import (
    CorrelationId,
    EventId,
    ProviderInstrumentRef,
    TradableInstrumentId,
)
from btg_ai_trader.observer.market import Candle, CandleFinality, Tick
from btg_ai_trader.observer.temporal import EventTime, ObservationTimes
from btg_ai_trader.observer.values import MissingReason

UNKNOWN = MissingReason.UNKNOWN
T0 = datetime(2026, 9, 13, tzinfo=UTC)


def event(index: int = 0) -> EventEnvelope:
    return EventEnvelope(
        EventId(str(UUID(int=index + 1))),
        EventType.TICK,
        ProviderInstrumentRef("fixture", "stream:a", "SYMBOL"),
        TradableInstrumentId(str(UUID(int=5000))),
        ObservationTimes(
            EventTime(T0, "fixture_timestamp", timedelta(seconds=1)), T0, T0, UNKNOWN
        ),
        Tick(Decimal("1"), Decimal("2"), UNKNOWN, Decimal("0")),
        ingestion_order=index,
    )


def with_time(original: EventEnvelope, timestamp: EventTime) -> EventEnvelope:
    return replace(original, times=replace(original.times, event_time=timestamp))


@pytest.mark.parametrize("bad", [0, -1, True, 1.0, None])
def test_capacity_is_strictly_positive_integer(bad: object) -> None:
    with pytest.raises(ValueError, match="capacity"):
        DedupState("session:a", cast(int, bad))


def test_new_and_duplicate_preserve_first_canonical_and_distinct_receipts() -> None:
    original = event()
    new = classify_duplicate(DedupState("session:a", 1), original)
    assert new.status is DedupStatus.NEW
    incoming = replace(
        original,
        ingestion_order=42,
        times=replace(
            original.times,
            ingestion_time=T0 + timedelta(seconds=2),
            knowledge_time=T0 + timedelta(seconds=3),
        ),
    )
    duplicate = classify_duplicate(new.state, incoming)
    assert duplicate.status is DedupStatus.DUPLICATE
    assert duplicate.incoming is incoming
    assert duplicate.canonical is original
    assert duplicate.state is new.state
    assert original.times.knowledge_time == T0
    assert original.ingestion_order == 0
    missing_knowledge = replace(incoming, times=replace(incoming.times, knowledge_time=UNKNOWN))
    assert classify_duplicate(new.state, missing_knowledge).status is DedupStatus.DUPLICATE


def test_changed_intrinsic_fact_is_conflict_and_never_replaces_original() -> None:
    original = event()
    state = classify_duplicate(DedupState("session:a", 1), original).state
    candle = Candle(
        T0, T0 + timedelta(minutes=1), CandleFinality.OPEN, UNKNOWN, UNKNOWN,
        Decimal("1"), Decimal("2"), Decimal("1"), Decimal("2"), UNKNOWN,
    )
    variants = [
        replace(original, payload=Tick(Decimal("1"), Decimal("3"), UNKNOWN, Decimal("0"))),
        replace(original, source=ProviderInstrumentRef("fixture", "stream:b", "SYMBOL")),
        replace(original, instrument_id=UNKNOWN),
        with_time(original, replace(original.times.event_time, value=T0 + timedelta(seconds=1))),
        replace(original, times=replace(original.times, effective_time=T0)),
        replace(original, external_event_id="source-event-2"),
        replace(original, source_sequence=1, sequence_scope="session-source"),
        replace(original, correlation_id=CorrelationId(str(UUID(int=17)))),
        replace(original, causation_id=EventId(str(UUID(int=18)))),
        replace(original, event_type=EventType.CANDLE, payload=candle),
    ]
    for incoming in variants:
        result = classify_duplicate(state, incoming)
        assert result.status is DedupStatus.IDENTITY_CONFLICT
        assert result.canonical is original
        assert result.incoming is incoming
        assert result.state is state
    assert state.canonical == (original,)


def test_distinct_ids_are_distinct_facts_and_session_state_is_explicit() -> None:
    original, other = event(), event(1)
    state = classify_duplicate(DedupState("session:a", 2), original).state
    distinct = classify_duplicate(state, other)
    assert distinct.status is DedupStatus.NEW
    assert distinct.state.canonical == (original, other)
    assert classify_duplicate(DedupState("session:b", 1), original).status is DedupStatus.NEW


def test_capacity_exhaustion_preserves_evidence_and_recognizes_known_ids() -> None:
    original, incoming = event(), event(1)
    state = classify_duplicate(DedupState("session:a", 1), original).state
    exhausted = classify_duplicate(state, incoming)
    assert exhausted.status is DedupStatus.CAPACITY_EXHAUSTED
    assert exhausted.incoming is incoming
    assert exhausted.canonical is None
    assert exhausted.state is state
    assert classify_duplicate(state, original).status is DedupStatus.DUPLICATE
    conflict = replace(original, external_event_id="conflicting")
    assert classify_duplicate(state, conflict).status is DedupStatus.IDENTITY_CONFLICT
    assert state.canonical[0] is original


@pytest.mark.parametrize("capacity", [1, 3, 19])
def test_long_sequence_never_evicts_canonical_records(capacity: int) -> None:
    state = DedupState("session:a", capacity)
    first: list[EventEnvelope] = []
    for index in range(300):
        incoming = event(index)
        before = state
        result = classify_duplicate(state, incoming)
        state = result.state
        if index < capacity:
            first.append(incoming)
            assert result.status is DedupStatus.NEW
        else:
            assert result.status is DedupStatus.CAPACITY_EXHAUSTED
            assert state is before
        assert state.canonical == tuple(first)
        assert len(state.canonical) <= capacity
        for canonical in first:
            duplicate = classify_duplicate(state, canonical)
            assert duplicate.status is DedupStatus.DUPLICATE
            assert duplicate.canonical is canonical


def test_invalid_table_and_non_envelope_input_fail_closed() -> None:
    original = event()
    with pytest.raises(ValueError, match="session_scope"):
        DedupState("", 1)
    with pytest.raises(ValueError, match="immutable tuple"):
        DedupState("session:a", 1, cast(tuple[EventEnvelope, ...], []))
    with pytest.raises(ValueError, match="exceed"):
        DedupState("session:a", 1, (original, event(1)))
    with pytest.raises(ValueError, match="unique"):
        DedupState("session:a", 2, (original, original))
    with pytest.raises(ValueError, match="validated EventEnvelope"):
        DedupState("session:a", 1, (cast(EventEnvelope, {}),))
    with pytest.raises(ValueError, match="classification requires"):
        classify_duplicate(cast(DedupState, None), original)
    with pytest.raises(ValueError, match="classification requires"):
        classify_duplicate(DedupState("session:a", 1), cast(EventEnvelope, {}))
    state = DedupState("session:a", 1)
    field_name = "canonical"
    with pytest.raises(FrozenInstanceError):
        setattr(state, field_name, (original,))


@pytest.mark.parametrize(
    ("seconds", "status"),
    [(-1, LateStatus.LATE), (0, LateStatus.ON_OR_AFTER_FRONTIER),
     (1, LateStatus.ON_OR_AFTER_FRONTIER)],
)
def test_known_comparable_frontier_annotates_without_changing_arrival(
    seconds: int, status: LateStatus
) -> None:
    frontier = event()
    incoming = with_time(
        event(1), replace(frontier.times.event_time, value=T0 + timedelta(seconds=seconds))
    )
    result = annotate_late(incoming, frontier)
    assert result.status is status
    assert result.incoming is incoming
    assert result.frontier is frontier
    assert incoming.ingestion_order == 1
    assert frontier.ingestion_order == 0


def test_missing_time_components_or_mismatched_time_contract_remain_unknown() -> None:
    original = event()
    timestamp = original.times.event_time
    variants = [
        replace(timestamp, value=UNKNOWN),
        replace(timestamp, basis=UNKNOWN),
        replace(timestamp, resolution=UNKNOWN),
        replace(timestamp, basis="different-source-basis"),
        replace(timestamp, resolution=timedelta(milliseconds=1)),
    ]
    for time in variants:
        changed = with_time(original, time)
        assert annotate_late(changed, original).status is LateStatus.UNKNOWN
        assert annotate_late(original, changed).status is LateStatus.UNKNOWN


def test_unresolved_or_mismatched_source_and_instrument_never_falsely_compare() -> None:
    original = event()
    variants = [
        replace(original, instrument_id=UNKNOWN),
        replace(original, instrument_id=TradableInstrumentId(str(UUID(int=5001)))),
        replace(original, source=ProviderInstrumentRef("other", "stream:a", "SYMBOL")),
        replace(original, source=ProviderInstrumentRef("fixture", "stream:b", "SYMBOL")),
        replace(original, source=ProviderInstrumentRef("fixture", "stream:a", "OTHER")),
    ]
    for changed in variants:
        assert annotate_late(changed, original).status is LateStatus.UNKNOWN
        assert annotate_late(original, changed).status is LateStatus.UNKNOWN
    unresolved = replace(original, instrument_id=UNKNOWN)
    assert annotate_late(unresolved, unresolved).status is LateStatus.UNKNOWN


def test_late_annotation_is_immutable_and_validates_both_input_types() -> None:
    original = event()
    result = annotate_late(original, original)
    field_name = "status"
    with pytest.raises(FrozenInstanceError):
        setattr(result, field_name, LateStatus.LATE)
    with pytest.raises(ValueError, match="validated EventEnvelope"):
        annotate_late(cast(EventEnvelope, None), original)
    with pytest.raises(ValueError, match="validated EventEnvelope"):
        annotate_late(original, cast(EventEnvelope, []))
