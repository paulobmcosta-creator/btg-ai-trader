"""Explicit passive latency composition for the Sprint 1 Observer boundary."""

from dataclasses import dataclass
from datetime import datetime

from btg_ai_trader.observer.admission import IngressMetadata
from btg_ai_trader.observer.composition import FixtureObserver, StepResult
from btg_ai_trader.observer.envelope import EventEnvelope
from btg_ai_trader.observer.health import (
    HealthSample,
    TransitLatencyEvidence,
    measure_transit_latency,
)
from btg_ai_trader.observer.values import MissingReason


@dataclass(frozen=True, slots=True)
class LatencyObservedStep:
    """One Observer step paired with explicit same-scope transit-latency evidence."""

    step: StepResult
    latency: TransitLatencyEvidence

    def __post_init__(self) -> None:
        if not isinstance(self.step, StepResult):
            raise ValueError("step must be a validated StepResult")
        if not isinstance(self.latency, TransitLatencyEvidence):
            raise ValueError("latency must be validated monotonic transit evidence")


def advance_with_latency(
    observer: FixtureObserver,
    ingress: IngressMetadata,
    *,
    ingress_ns: int,
    valid_at: datetime | MissingReason,
    knowledge_cutoff: datetime,
    frontier: EventEnvelope | None,
    health_sample: HealthSample,
) -> LatencyObservedStep:
    """Advance the passive Observer and emit latency from caller-supplied monotonic readings."""
    if type(observer) is not FixtureObserver:
        raise TypeError("latency boundary requires the exact passive FixtureObserver")
    if type(health_sample) is not HealthSample:
        raise TypeError("latency boundary requires an explicit HealthSample")
    if health_sample.clock_scope != observer.config.clock_scope:
        raise ValueError("latency clock scope differs from Observer configuration")
    latency = measure_transit_latency(
        health_sample.clock_scope,
        ingress_ns,
        health_sample.now_ns,
    )
    step = observer.advance(
        ingress,
        valid_at=valid_at,
        knowledge_cutoff=knowledge_cutoff,
        frontier=frontier,
        health_sample=health_sample,
    )
    return LatencyObservedStep(step, latency)
