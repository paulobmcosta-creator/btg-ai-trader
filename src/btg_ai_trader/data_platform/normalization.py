"""Lossless market-data normalization per causal lane (S2-B)."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from btg_ai_trader.data_platform.quality import QualityFinding, evaluate_envelope_quality
from btg_ai_trader.observer.envelope import EventEnvelope
from btg_ai_trader.observer.identity import EventId
from btg_ai_trader.observer.values import require_text
from btg_ai_trader.replay import CausalLane


@dataclass(frozen=True, slots=True)
class NormalizedMarketBatch:
    """Lossless normalized market batch for a single causal lane."""

    lane: CausalLane
    events: tuple[EventEnvelope, ...]
    quality_findings: tuple[QualityFinding, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.lane, CausalLane):
            raise ValueError("lane must be a CausalLane instance")
        if type(self.events) is not tuple:
            raise ValueError("events must be a tuple of EventEnvelope")
        for e in self.events:
            if not isinstance(e, EventEnvelope):
                raise ValueError("events must contain EventEnvelope instances")
            if e.source.provider != self.lane.provider_id:
                raise ValueError("event provider does not match lane provider_id")
            if e.source.scope != self.lane.capture_scope:
                raise ValueError("event capture scope does not match lane capture_scope")
        if type(self.quality_findings) is not tuple:
            raise ValueError("quality_findings must be a tuple of QualityFinding")
        for f in self.quality_findings:
            if not isinstance(f, QualityFinding):
                raise ValueError("quality_findings must contain QualityFinding instances")

    @property
    def provider_id(self) -> str:
        return self.lane.provider_id

    @property
    def capture_scope(self) -> str:
        return self.lane.capture_scope

    @property
    def event_count(self) -> int:
        return len(self.events)

    def __len__(self) -> int:
        return len(self.events)

    def __getitem__(self, index: int) -> EventEnvelope:
        return self.events[index]

    def __iter__(self) -> Iterator[EventEnvelope]:
        return iter(self.events)

    @property
    def instruments(self) -> tuple[str, ...]:
        return tuple(sorted({e.source.symbol for e in self.events}))

    @property
    def blocks_replay(self) -> bool:
        return any(f.blocks_replay for f in self.quality_findings)

    @property
    def replay_blocking_findings(self) -> tuple[QualityFinding, ...]:
        return tuple(f for f in self.quality_findings if f.blocks_replay)

    def findings_for_event(self, event_id: EventId) -> tuple[QualityFinding, ...]:
        return tuple(f for f in self.quality_findings if f.event_id == event_id)

    @property
    def is_clean(self) -> bool:
        return len(self.quality_findings) == 0


def normalize_market_batch(
    events: Iterable[EventEnvelope],
    *,
    lane: CausalLane | None = None,
    provider_id: str | None = None,
    capture_scope: str | None = None,
) -> NormalizedMarketBatch:
    """Normalize market data losslessly within one explicit causal lane."""
    copied_events = tuple(events)
    for e in copied_events:
        if not isinstance(e, EventEnvelope):
            raise ValueError("all items must be EventEnvelope instances")

    if lane is not None:
        if not isinstance(lane, CausalLane):
            raise ValueError("lane must be a CausalLane instance")
        resolved_provider = lane.provider_id
        resolved_scope = lane.capture_scope
        if provider_id is not None and provider_id != resolved_provider:
            raise ValueError("conflicting provider_id and lane")
        if capture_scope is not None and capture_scope != resolved_scope:
            raise ValueError("conflicting capture_scope and lane")
    else:
        if provider_id is not None and capture_scope is not None:
            require_text(provider_id, "provider_id")
            require_text(capture_scope, "capture_scope")
            resolved_provider = provider_id
            resolved_scope = capture_scope
            lane = CausalLane(resolved_provider, resolved_scope)
        elif copied_events:
            first = copied_events[0]
            resolved_provider = first.source.provider
            resolved_scope = first.source.scope
            if provider_id is not None and provider_id != resolved_provider:
                raise ValueError("conflicting provider_id and first event")
            if capture_scope is not None and capture_scope != resolved_scope:
                raise ValueError("conflicting capture_scope and first event")
            lane = CausalLane(resolved_provider, resolved_scope)
        else:
            raise ValueError(
                "empty events requires explicit lane or (provider_id, capture_scope)"
            )

    for e in copied_events:
        if e.source.provider != resolved_provider:
            raise ValueError(
                "all normalized events must belong to one provider/capture scope: "
                "mixed provider rejected"
            )
        if e.source.scope != resolved_scope:
            raise ValueError(
                "all normalized events must belong to one provider/capture scope: "
                "mixed capture scope rejected"
            )

    all_findings: list[QualityFinding] = []
    for e in copied_events:
        findings = evaluate_envelope_quality(e)
        all_findings.extend(findings)

    return NormalizedMarketBatch(
        lane=lane,
        events=copied_events,
        quality_findings=tuple(all_findings),
    )
