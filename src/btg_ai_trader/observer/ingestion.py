"""Bounded passive FIFO fixtures with explicit ownership and immutable evidence."""

from dataclasses import dataclass, replace
from enum import Enum

from btg_ai_trader.observer.envelope import EventEnvelope
from btg_ai_trader.observer.health import (
    HealthAssessment,
    HealthPolicy,
    HealthSample,
    RuntimePhase,
    SafetyPosture,
    evaluate_health,
)
from btg_ai_trader.observer.values import require_text


@dataclass(frozen=True, slots=True)
class QueueSnapshot:
    scope: str
    capacity: int
    depth: int
    accepted: int
    dequeued: int
    backpressure_count: int

    def __post_init__(self) -> None:
        require_text(self.scope, "scope")
        if type(self.capacity) is not int or self.capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        for name in ("depth", "accepted", "dequeued", "backpressure_count"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if self.depth > self.capacity:
            raise ValueError("depth cannot exceed capacity")
        if self.accepted - self.dequeued != self.depth:
            raise ValueError("queue counters must conserve accepted observations")

    @property
    def pressure_observed(self) -> bool:
        return self.depth == self.capacity or self.backpressure_count > 0


@dataclass(frozen=True, slots=True)
class ObservationQueue:
    snapshot: QueueSnapshot
    items: tuple[EventEnvelope, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.snapshot, QueueSnapshot):
            raise ValueError("snapshot must be QueueSnapshot")
        if type(self.items) is not tuple:
            raise ValueError("items must be an immutable tuple")
        if len(self.items) != self.snapshot.depth:
            raise ValueError("items must match snapshot depth")
        if any(type(item) is not EventEnvelope for item in self.items):
            raise ValueError("items must be validated EventEnvelope records")

    @classmethod
    def empty(cls, scope: str, capacity: int) -> "ObservationQueue":
        return cls(QueueSnapshot(scope, capacity, 0, 0, 0, 0))


class OfferStatus(Enum):
    ACCEPTED = "ACCEPTED"
    BACKPRESSURE = "BACKPRESSURE"


@dataclass(frozen=True, slots=True)
class OfferResult:
    status: OfferStatus
    item: EventEnvelope
    queue: ObservationQueue


@dataclass(frozen=True, slots=True)
class TakeResult:
    item: EventEnvelope | None
    queue: ObservationQueue


def offer(queue: ObservationQueue, item: EventEnvelope) -> OfferResult:
    """Caller must thread returned state forward and retain/retry rejected items."""
    if not isinstance(queue, ObservationQueue) or type(item) is not EventEnvelope:
        raise ValueError("offer requires ObservationQueue and validated EventEnvelope")
    before = queue.snapshot
    if before.depth == before.capacity:
        snapshot = replace(before, backpressure_count=before.backpressure_count + 1)
        return OfferResult(
            OfferStatus.BACKPRESSURE, item, ObservationQueue(snapshot, queue.items)
        )
    snapshot = replace(before, depth=before.depth + 1, accepted=before.accepted + 1)
    return OfferResult(
        OfferStatus.ACCEPTED, item, ObservationQueue(snapshot, (*queue.items, item))
    )


def take(queue: ObservationQueue) -> TakeResult:
    """Return the first accepted arrival; empty is explicit and has no side effect."""
    if not isinstance(queue, ObservationQueue):
        raise ValueError("take requires ObservationQueue")
    if not queue.items:
        return TakeResult(None, queue)
    before = queue.snapshot
    snapshot = replace(before, depth=before.depth - 1, dequeued=before.dequeued + 1)
    return TakeResult(queue.items[0], ObservationQueue(snapshot, queue.items[1:]))


@dataclass(frozen=True, slots=True)
class QueueHealthAssessment:
    queue: QueueSnapshot
    health: HealthAssessment

    def __post_init__(self) -> None:
        if not isinstance(self.queue, QueueSnapshot) or not isinstance(
            self.health, HealthAssessment
        ):
            raise ValueError("queue health requires validated snapshot and assessment")

    @property
    def backpressure_observed(self) -> bool:
        return self.queue.pressure_observed


@dataclass(frozen=True, slots=True)
class QueueHealthTransition:
    before: QueueHealthAssessment
    after: QueueHealthAssessment


@dataclass(frozen=True, slots=True)
class QueueHealthEvaluation:
    assessment: QueueHealthAssessment
    transition: QueueHealthTransition | None


def evaluate_queue_health(
    sample: HealthSample,
    *,
    queue: ObservationQueue,
    phase: RuntimePhase,
    requested_posture: SafetyPosture,
    policy: HealthPolicy,
    previous: QueueHealthAssessment | None = None,
) -> QueueHealthEvaluation:
    """Compose pressure with passive health; no clock, callback or unlatch authority."""
    if not isinstance(queue, ObservationQueue):
        raise ValueError("queue must be ObservationQueue")
    snapshot = queue.snapshot
    if previous is not None:
        if not isinstance(previous, QueueHealthAssessment):
            raise ValueError("previous must be QueueHealthAssessment")
        if (
            previous.queue.scope != snapshot.scope
            or previous.queue.capacity != snapshot.capacity
        ):
            raise ValueError("queue scope/capacity requires explicit continuity")
        for name in ("accepted", "dequeued", "backpressure_count"):
            if getattr(snapshot, name) < getattr(previous.queue, name):
                raise ValueError(f"queue {name} cannot move backward")
    posture = requested_posture
    if (
        phase is RuntimePhase.RUNNING
        and snapshot.pressure_observed
        and requested_posture is SafetyPosture.NORMAL
    ):
        posture = SafetyPosture.DEGRADED
    result = evaluate_health(
        sample,
        phase=phase,
        requested_posture=posture,
        policy=policy,
        previous=previous.health if previous else None,
    )
    current = QueueHealthAssessment(snapshot, result.assessment)
    transition = None
    if previous is not None and (
        result.transition is not None
        or previous.backpressure_observed != current.backpressure_observed
    ):
        transition = QueueHealthTransition(previous, current)
    return QueueHealthEvaluation(current, transition)
