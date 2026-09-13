"""Bounded transport fixture proofs; no provider, wall clock or persistent delivery."""

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast
from uuid import UUID

import pytest

from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.health import (
    HealthPolicy,
    HealthSample,
    ReadinessStatus,
    RuntimePhase,
    SafetyPosture,
)
from btg_ai_trader.observer.identity import EventId, ProviderInstrumentRef
from btg_ai_trader.observer.ingestion import (
    ObservationQueue,
    OfferStatus,
    QueueHealthAssessment,
    QueueSnapshot,
    evaluate_queue_health,
    offer,
    take,
)
from btg_ai_trader.observer.market import Tick
from btg_ai_trader.observer.temporal import ObservationTimes
from btg_ai_trader.observer.values import MissingReason

UNKNOWN = MissingReason.UNKNOWN
POLICY = HealthPolicy("fixture:v1", 10, 20)
SAMPLE = HealthSample("clock:a", 100, 100, 100)


def event(index: int) -> EventEnvelope:
    instant = datetime(2026, 9, 13, tzinfo=UTC)
    return EventEnvelope(
        EventId(str(UUID(int=index + 1))),
        EventType.TICK,
        ProviderInstrumentRef("fixture", "stream:a", "SYMBOL"),
        UNKNOWN,
        ObservationTimes(UNKNOWN, instant, instant, UNKNOWN),
        Tick(Decimal("1"), Decimal("2"), UNKNOWN, Decimal("0")),
        ingestion_order=index,
    )


def health(
    queue: ObservationQueue,
    *,
    previous: QueueHealthAssessment | None = None,
    posture: SafetyPosture = SafetyPosture.NORMAL,
    phase: RuntimePhase = RuntimePhase.RUNNING,
    sample: HealthSample = SAMPLE,
) -> QueueHealthAssessment:
    return evaluate_queue_health(
        sample,
        queue=queue,
        phase=phase,
        requested_posture=posture,
        policy=POLICY,
        previous=previous,
    ).assessment


@pytest.mark.parametrize("bad", [0, -1, True, 1.0, None])
def test_capacity_is_an_explicit_positive_integer(bad: object) -> None:
    with pytest.raises(ValueError, match="capacity"):
        ObservationQueue.empty("queue:a", cast(int, bad))


def test_saturation_preserves_items_and_returns_rejected_identity_for_retry() -> None:
    empty = ObservationQueue.empty("queue:a", 1)
    first, second = event(0), event(1)
    accepted = offer(empty, first)
    rejected = offer(accepted.queue, second)
    assert accepted.status is OfferStatus.ACCEPTED
    assert rejected.status is OfferStatus.BACKPRESSURE
    assert rejected.item is second
    assert rejected.queue.items == (first,)
    assert rejected.queue.items[0] is first
    assert rejected.queue.snapshot.backpressure_count == 1
    assert accepted.queue.snapshot.backpressure_count == 0
    assert empty.items == ()
    drained = take(rejected.queue)
    assert drained.item is first
    retried = offer(drained.queue, rejected.item)
    assert retried.status is OfferStatus.ACCEPTED
    assert take(retried.queue).item is second
    assert retried.queue.snapshot.accepted == 2
    assert retried.queue.snapshot.dequeued == 1


def test_empty_take_and_immutable_result_are_explicit() -> None:
    queue = ObservationQueue.empty("queue:a", 2)
    result = take(queue)
    assert result.item is None
    assert result.queue is queue
    with pytest.raises(FrozenInstanceError):
        setattr(result, "item", event(0))
    with pytest.raises(FrozenInstanceError):
        setattr(queue.snapshot, "capacity", 100)


@pytest.mark.parametrize("capacity", [1, 2, 7, 31])
def test_long_deterministic_sequences_conserve_fifo_and_bounded_storage(capacity: int) -> None:
    queue = ObservationQueue.empty("queue:a", capacity)
    expected: list[EventEnvelope] = []
    offers = accepted = rejected = dequeued = 0
    for index in range(1200):
        if index % 5 in (0, 1, 2):
            item = event(index)
            offers += 1
            result = offer(queue, item)
            queue = result.queue
            if len(expected) < capacity:
                assert result.status is OfferStatus.ACCEPTED
                expected.append(item)
                accepted += 1
            else:
                assert result.status is OfferStatus.BACKPRESSURE
                assert result.item is item
                rejected += 1
        else:
            taken = take(queue)
            queue = taken.queue
            if expected:
                assert taken.item is expected.pop(0)
                dequeued += 1
            else:
                assert taken.item is None
        assert queue.items == tuple(expected)
        assert 0 <= queue.snapshot.depth <= capacity
        assert queue.snapshot.accepted == accepted
        assert queue.snapshot.dequeued == dequeued
        assert queue.snapshot.backpressure_count == rejected
        assert accepted + rejected == offers
        assert accepted - dequeued == len(expected)


def test_transport_preserves_duplicates_and_supplied_arrival_order_without_claiming_dedup() -> None:
    queue = ObservationQueue.empty("queue:a", 3)
    older, newer = event(0), event(1)
    for item in (newer, older, newer):
        queue = offer(queue, item).queue
    assert queue.items == (newer, older, newer)
    assert queue.items[0] is queue.items[2]
    assert older.ingestion_order == 0
    assert newer.correlation_id is None
    assert newer.payload.last is UNKNOWN


@pytest.mark.parametrize("bad", [-1, True, 1.0])
def test_snapshot_counters_reject_invalid_values(bad: object) -> None:
    snapshot = ObservationQueue.empty("queue:a", 2).snapshot
    with pytest.raises(ValueError, match="nonnegative integer"):
        replace(snapshot, depth=cast(int, bad))
    with pytest.raises(ValueError, match="nonnegative integer"):
        replace(snapshot, accepted=cast(int, bad))
    with pytest.raises(ValueError, match="nonnegative integer"):
        replace(snapshot, dequeued=cast(int, bad))
    with pytest.raises(ValueError, match="nonnegative integer"):
        replace(snapshot, backpressure_count=cast(int, bad))


def test_queue_invariants_and_typed_payload_boundary_fail_closed() -> None:
    snapshot = QueueSnapshot("queue:a", 2, 0, 0, 0, 0)
    with pytest.raises(ValueError, match="conserve"):
        replace(snapshot, accepted=1)
    with pytest.raises(ValueError, match="exceed"):
        replace(snapshot, depth=3)
    with pytest.raises(ValueError, match="immutable tuple"):
        ObservationQueue(snapshot, cast(tuple[EventEnvelope, ...], []))
    with pytest.raises(ValueError, match="match snapshot depth"):
        ObservationQueue(snapshot, (event(0),))
    with pytest.raises(ValueError, match="validated EventEnvelope"):
        ObservationQueue(QueueSnapshot("queue:a", 1, 1, 1, 0, 0), (cast(EventEnvelope, {}),))
    with pytest.raises(ValueError, match="snapshot"):
        ObservationQueue(cast(QueueSnapshot, None))
    queue = ObservationQueue.empty("queue:a", 1)
    with pytest.raises(ValueError, match="validated EventEnvelope"):
        offer(queue, cast(EventEnvelope, {"payload": []}))
    with pytest.raises(ValueError, match="ObservationQueue"):
        offer(cast(ObservationQueue, None), event(0))
    with pytest.raises(ValueError, match="ObservationQueue"):
        take(cast(ObservationQueue, None))


def test_live_health_plus_full_queue_is_blocked_and_draining_does_not_unlatch() -> None:
    queue = ObservationQueue.empty("queue:a", 1)
    initial = health(queue)
    assert initial.health.readiness is ReadinessStatus.READY
    full = offer(queue, event(0)).queue
    result = evaluate_queue_health(
        SAMPLE, queue=full, phase=RuntimePhase.RUNNING,
        requested_posture=SafetyPosture.NORMAL, policy=POLICY, previous=initial,
    )
    pressured = result.assessment
    assert result.transition is not None
    assert result.transition.before is initial
    assert result.transition.after is pressured
    assert pressured.backpressure_observed
    assert pressured.health.heartbeat_alive
    assert pressured.health.readiness is ReadinessStatus.NOT_READY
    drained = health(take(full).queue, previous=pressured)
    assert not drained.backpressure_observed
    assert drained.health.posture is SafetyPosture.DEGRADED
    assert drained.health.readiness is ReadinessStatus.NOT_READY


@pytest.mark.parametrize("posture", [SafetyPosture.SAFE_HALT, SafetyPosture.EMERGENCY_STOP])
def test_pressure_never_weakens_a_stronger_containment(posture: SafetyPosture) -> None:
    full = offer(ObservationQueue.empty("queue:a", 1), event(0)).queue
    assert health(full, posture=posture).health.posture is posture


def test_rejection_evidence_survives_drain_and_unknown_samples_remain_unknown() -> None:
    full = offer(ObservationQueue.empty("queue:a", 1), event(0)).queue
    rejected = offer(full, event(1)).queue
    drained = take(rejected).queue
    sample = HealthSample("clock:a", 100, UNKNOWN, UNKNOWN)
    result = health(drained, sample=sample)
    assert result.backpressure_observed
    assert result.queue.depth == 0
    assert result.queue.backpressure_count == 1
    assert result.health.heartbeat_age_ns is UNKNOWN
    assert result.health.market_age_ns is UNKNOWN
    assert result.health.readiness is ReadinessStatus.NOT_READY


def test_predecessor_queue_scope_capacity_and_counters_require_continuity() -> None:
    empty = ObservationQueue.empty("queue:a", 1)
    full = offer(empty, event(0)).queue
    previous = health(offer(full, event(1)).queue)
    with pytest.raises(ValueError, match="accepted.*backward"):
        health(empty, previous=previous)
    with pytest.raises(ValueError, match="backpressure_count.*backward"):
        health(full, previous=previous)
    drained = health(take(full).queue)
    with pytest.raises(ValueError, match="dequeued.*backward"):
        health(full, previous=drained)
    for queue in (ObservationQueue.empty("queue:b", 1), ObservationQueue.empty("queue:a", 2)):
        with pytest.raises(ValueError, match="scope/capacity"):
            health(queue, previous=previous)


def test_composition_validates_inputs_and_retains_health_temporal_contract() -> None:
    queue = ObservationQueue.empty("queue:a", 2)
    previous = health(queue)
    with pytest.raises(ValueError, match="previous"):
        health(queue, previous=cast(QueueHealthAssessment, "bad"))
    with pytest.raises(ValueError, match="queue"):
        health(cast(ObservationQueue, None))
    with pytest.raises(ValueError, match="validated snapshot"):
        QueueHealthAssessment(cast(QueueSnapshot, None), previous.health)
    with pytest.raises(ValueError, match="backward"):
        health(queue, previous=previous, sample=HealthSample("clock:a", 101, 99, 101))
    with pytest.raises(ValueError, match="distinct enum"):
        health(queue, phase=cast(RuntimePhase, "RUNNING"))


def test_stable_composition_does_not_fabricate_transition_or_startup_fault() -> None:
    full = offer(ObservationQueue.empty("queue:a", 1), event(0)).queue
    previous = health(full, phase=RuntimePhase.STARTING)
    assert previous.health.posture is SafetyPosture.NORMAL
    assert previous.health.readiness is ReadinessStatus.NOT_READY
    result = evaluate_queue_health(
        SAMPLE, queue=full, phase=RuntimePhase.STARTING,
        requested_posture=SafetyPosture.NORMAL, policy=POLICY, previous=previous,
    )
    assert result.transition is None
    assert result.assessment == previous
