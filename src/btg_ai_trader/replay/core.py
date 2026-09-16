"""Pure, deterministic causal market-data replay core for Sprint 2.

This module is strictly read-only and deterministic: no wall clock, sleeping,
network/provider I/O, strategy, risk, execution or financial simulation.
It replays immutable EventEnvelope values according to explicit knowledge-time
evidence and caller-supplied order.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from fractions import Fraction

from btg_ai_trader.observer.envelope import EventEnvelope
from btg_ai_trader.observer.identity import EventId, RunId
from btg_ai_trader.observer.provenance import (
    CodeRevision,
    ConfigHash,
    ContentHash,
    InputIdentity,
    RunManifest,
)
from btg_ai_trader.observer.temporal import require_utc
from btg_ai_trader.observer.values import require_text

_MICROSECONDS_PER_SECOND = 1_000_000
_SECONDS_PER_DAY = 86_400


def _positive_int(value: int, field_name: str) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")


def _delta_microseconds(delta: timedelta) -> int:
    if delta < timedelta(0):
        raise ValueError("replay delta must not be negative")
    return (
        (delta.days * _SECONDS_PER_DAY + delta.seconds) * _MICROSECONDS_PER_SECOND
        + delta.microseconds
    )


@dataclass(frozen=True, slots=True)
class CausalLane:
    """Explicit causal lane identifying one provider and capture scope."""

    provider_id: str
    capture_scope: str

    def __post_init__(self) -> None:
        require_text(self.provider_id, "provider_id")
        require_text(self.capture_scope, "capture_scope")


@dataclass(frozen=True, slots=True)
class ReplaySpeed:
    """Exact rational replay speed; 2/1 means 2x source knowledge speed."""

    numerator: int
    denominator: int = 1

    def __post_init__(self) -> None:
        _positive_int(self.numerator, "speed numerator")
        _positive_int(self.denominator, "speed denominator")

    def virtual_delay_us(self, source_delta_us: int) -> Fraction:
        if type(source_delta_us) is not int or source_delta_us < 0:
            raise ValueError("source_delta_us must be a nonnegative integer")
        return Fraction(source_delta_us * self.denominator, self.numerator)

    def as_fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)

    @classmethod
    def from_fraction(cls, fraction: Fraction) -> "ReplaySpeed":
        if not isinstance(fraction, Fraction):
            raise ValueError("fraction must be a Fraction instance")
        if fraction <= 0:
            raise ValueError("speed fraction must be positive")
        return cls(fraction.numerator, fraction.denominator)

    @classmethod
    def from_ratio(cls, numerator: int, denominator: int = 1) -> "ReplaySpeed":
        return cls(numerator, denominator)

    @classmethod
    def one(cls) -> "ReplaySpeed":
        return cls(1, 1)


ReplayRate = ReplaySpeed


@dataclass(frozen=True, slots=True)
class ReplayEmissionLineage:
    """Lineage linking an emitted event to its replay run and source lane."""

    run_id: RunId
    event_id: EventId
    ordinal: int
    provider_id: str
    capture_scope: str

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, RunId):
            raise ValueError("run_id must be RunId")
        if not isinstance(self.event_id, EventId):
            raise ValueError("event_id must be EventId")
        if type(self.ordinal) is not int or self.ordinal < 0:
            raise ValueError("ordinal must be a nonnegative integer")
        require_text(self.provider_id, "provider_id")
        require_text(self.capture_scope, "capture_scope")


@dataclass(frozen=True, slots=True)
class ReplayEmission:
    """One immutable market observation released by the causal replay cursor."""

    ordinal: int
    envelope: EventEnvelope
    knowledge_time: datetime
    source_delta_us: int
    virtual_delay_us: Fraction
    run_id: RunId

    def __post_init__(self) -> None:
        if type(self.ordinal) is not int or self.ordinal < 0:
            raise ValueError("ordinal must be a nonnegative integer")
        if not isinstance(self.envelope, EventEnvelope):
            raise ValueError("emission requires EventEnvelope")
        require_utc(self.knowledge_time, "knowledge_time")
        if type(self.source_delta_us) is not int or self.source_delta_us < 0:
            raise ValueError("source_delta_us must be nonnegative")
        if not isinstance(self.virtual_delay_us, Fraction) or self.virtual_delay_us < 0:
            raise ValueError("virtual_delay_us must be a nonnegative exact Fraction")
        if not isinstance(self.run_id, RunId):
            raise ValueError("run_id must be RunId")

    @property
    def event_id(self) -> EventId:
        return self.envelope.event_id

    @property
    def symbol(self) -> str:
        return self.envelope.source.symbol

    @property
    def lineage(self) -> ReplayEmissionLineage:
        return ReplayEmissionLineage(
            run_id=self.run_id,
            event_id=self.envelope.event_id,
            ordinal=self.ordinal,
            provider_id=self.envelope.source.provider,
            capture_scope=self.envelope.source.scope,
        )


@dataclass(frozen=True, slots=True)
class ReplayInputBoundary:
    """Immutable replay input boundary binding lane, inputs, provenance, semantics (DD-15)."""

    run_id: RunId
    code_revision: CodeRevision
    config_hash: ConfigHash
    provider_id: str
    capture_scope: str
    event_ids: tuple[EventId, ...]
    content_hashes: tuple[ContentHash | None, ...] = ()
    temporal_semantics: str = "knowledge_time_v1"

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, RunId):
            raise ValueError("run_id must be RunId")
        if not isinstance(self.code_revision, CodeRevision):
            raise ValueError("code_revision must be CodeRevision")
        if not isinstance(self.config_hash, ConfigHash):
            raise ValueError("config_hash must be ConfigHash")
        require_text(self.provider_id, "provider_id")
        require_text(self.capture_scope, "capture_scope")
        if type(self.event_ids) is not tuple:
            raise ValueError("event_ids must be a tuple of EventId")
        seen: set[EventId] = set()
        for item in self.event_ids:
            if not isinstance(item, EventId):
                raise ValueError("event_ids must contain EventId instances")
            if item in seen:
                raise ValueError("duplicate EventId in boundary event_ids")
            seen.add(item)
        if type(self.content_hashes) is not tuple:
            raise ValueError("content_hashes must be a tuple")
        if self.content_hashes:
            if len(self.content_hashes) != len(self.event_ids):
                raise ValueError("content_hashes count must match event_ids count")
            for h in self.content_hashes:
                if h is not None and not isinstance(h, ContentHash):
                    raise ValueError("content_hashes entries must be ContentHash or None")
        require_text(self.temporal_semantics, "temporal_semantics")

    @property
    def lane(self) -> CausalLane:
        return CausalLane(self.provider_id, self.capture_scope)

    @property
    def input_identities(self) -> tuple[InputIdentity, ...]:
        if not self.content_hashes:
            return ()
        return tuple(
            InputIdentity(eid, h)
            for eid, h in zip(self.event_ids, self.content_hashes, strict=True)
            if h is not None
        )

    @classmethod
    def from_events(
        cls,
        events: Iterable[EventEnvelope],
        *,
        run_id: RunId,
        code_revision: CodeRevision,
        config_hash: ConfigHash,
        provider_id: str,
        capture_scope: str,
        content_hashes: Iterable[ContentHash | None] | None = None,
        temporal_semantics: str = "knowledge_time_v1",
    ) -> "ReplayInputBoundary":
        event_tuple = tuple(events)
        for e in event_tuple:
            if not isinstance(e, EventEnvelope):
                raise ValueError("events must contain EventEnvelope instances")
        e_ids = tuple(e.event_id for e in event_tuple)
        hashes_tuple = tuple(content_hashes) if content_hashes is not None else ()
        return cls(
            run_id=run_id,
            code_revision=code_revision,
            config_hash=config_hash,
            provider_id=provider_id,
            capture_scope=capture_scope,
            event_ids=e_ids,
            content_hashes=hashes_tuple,
            temporal_semantics=temporal_semantics,
        )

    @classmethod
    def from_manifest(
        cls,
        manifest: RunManifest,
        *,
        provider_id: str,
        capture_scope: str,
        event_ids: Iterable[EventId],
        temporal_semantics: str = "knowledge_time_v1",
    ) -> "ReplayInputBoundary":
        if not isinstance(manifest, RunManifest):
            raise ValueError("manifest must be RunManifest")
        eid_tuple = tuple(event_ids)
        manifest_map = {inp.artifact_id: inp.content_hash for inp in manifest.inputs}
        hashes = tuple(manifest_map.get(eid) for eid in eid_tuple)
        return cls(
            run_id=manifest.run_id,
            code_revision=manifest.code_revision,
            config_hash=manifest.config_hash,
            provider_id=provider_id,
            capture_scope=capture_scope,
            event_ids=eid_tuple,
            content_hashes=hashes,
            temporal_semantics=temporal_semantics,
        )


RunInputBoundary = ReplayInputBoundary


@dataclass(frozen=True, slots=True, init=False)
class CausalMarketReplaySchedule:
    """Finite immutable replay lane for one provider/capture scope."""

    boundary: ReplayInputBoundary
    run_id: RunId
    code_revision: CodeRevision
    config_hash: ConfigHash
    temporal_semantics: str
    lane: CausalLane
    provider_id: str
    provider: str
    capture_scope: str
    speed: ReplaySpeed
    rate: ReplaySpeed
    events: tuple[EventEnvelope, ...]
    _knowledge: tuple[datetime, ...] = field(repr=False)

    def __init__(
        self,
        events: Iterable[EventEnvelope],
        *,
        boundary: ReplayInputBoundary | None = None,
        run_id: RunId | None = None,
        code_revision: CodeRevision | None = None,
        config_hash: ConfigHash | None = None,
        lane: CausalLane | None = None,
        provider_id: str | None = None,
        provider: str | None = None,
        capture_scope: str | None = None,
        scope: str | None = None,
        speed: ReplaySpeed | None = None,
        rate: ReplaySpeed | None = None,
        content_hashes: Iterable[ContentHash | None] | None = None,
        temporal_semantics: str = "knowledge_time_v1",
    ) -> None:
        copied = tuple(events)
        for envelope in copied:
            if not isinstance(envelope, EventEnvelope):
                raise ValueError("replay schedule accepts only EventEnvelope values")

        if boundary is not None and not isinstance(boundary, ReplayInputBoundary):
            raise ValueError("boundary must be a ReplayInputBoundary instance")

        if lane is not None:
            if not isinstance(lane, CausalLane):
                raise ValueError("lane must be a CausalLane instance")
            resolved_provider = lane.provider_id
            resolved_scope = lane.capture_scope
            if provider_id is not None and provider_id != resolved_provider:
                raise ValueError("conflicting provider_id and lane")
            if provider is not None and provider != resolved_provider:
                raise ValueError("conflicting provider and lane")
            if capture_scope is not None and capture_scope != resolved_scope:
                raise ValueError("conflicting capture_scope and lane")
            if scope is not None and scope != resolved_scope:
                raise ValueError("conflicting scope and lane")
        else:
            if provider_id is not None and provider is not None and provider_id != provider:
                raise ValueError("conflicting provider_id and provider")
            resolved_provider_cand = provider_id if provider_id is not None else provider
            if boundary is not None and resolved_provider_cand is None:
                resolved_provider_cand = boundary.provider_id
            if resolved_provider_cand is None:
                raise ValueError("provider_id or provider must be supplied")
            require_text(resolved_provider_cand, "provider_id")
            resolved_provider = resolved_provider_cand

            if capture_scope is not None and scope is not None and capture_scope != scope:
                raise ValueError("conflicting capture_scope and scope")
            resolved_scope_cand = capture_scope if capture_scope is not None else scope
            if boundary is not None and resolved_scope_cand is None:
                resolved_scope_cand = boundary.capture_scope
            if resolved_scope_cand is None:
                raise ValueError("capture_scope or scope must be supplied")
            require_text(resolved_scope_cand, "capture_scope")
            resolved_scope = resolved_scope_cand

            lane = CausalLane(provider_id=resolved_provider, capture_scope=resolved_scope)

        if speed is not None and rate is not None and speed != rate:
            raise ValueError("conflicting speed and rate")
        resolved_speed = speed if speed is not None else (
            rate if rate is not None else ReplaySpeed(1, 1)
        )
        if not isinstance(resolved_speed, ReplaySpeed):
            raise ValueError("speed must be ReplaySpeed")

        seen_event_ids: set[EventId] = set()
        knowledge_times: list[datetime] = []
        previous_knowledge: datetime | None = None

        for envelope in copied:
            if envelope.source.provider != resolved_provider:
                raise ValueError(
                    "all replay events must belong to one provider/capture scope: "
                    "mixed provider rejected"
                )
            if envelope.source.scope != resolved_scope:
                raise ValueError(
                    "all replay events must belong to one provider/capture scope: "
                    "mixed capture scope rejected"
                )
            if envelope.event_id in seen_event_ids:
                raise ValueError(
                    "replay schedule must not repeat EventId: duplicate EventId rejected"
                )
            seen_event_ids.add(envelope.event_id)

            knowledge = envelope.times.knowledge_time
            if not isinstance(knowledge, datetime):
                raise ValueError("formal replay requires known, timezone-aware knowledge_time")
            require_utc(knowledge, "knowledge_time")
            if previous_knowledge is not None and knowledge < previous_knowledge:
                raise ValueError(
                    "supplied replay order contradicts knowledge-time causality: "
                    "knowledge-time regression rejected"
                )
            knowledge_times.append(knowledge)
            previous_knowledge = knowledge

        event_ids_sequence = tuple(e.event_id for e in copied)

        if boundary is not None:
            if boundary.provider_id != resolved_provider:
                raise ValueError("boundary provider_id does not match schedule provider")
            if boundary.capture_scope != resolved_scope:
                raise ValueError("boundary capture_scope does not match schedule capture_scope")
            if boundary.event_ids != event_ids_sequence:
                raise ValueError("boundary event_ids do not match supplied events sequence")
            if temporal_semantics is not None and temporal_semantics != boundary.temporal_semantics:
                raise ValueError("temporal_semantics does not match boundary")
            resolved_boundary = boundary
        else:
            if run_id is None or code_revision is None or config_hash is None:
                raise ValueError(
                    "replay schedule requires boundary or explicit "
                    "(run_id, code_revision, config_hash)"
                )
            resolved_boundary = ReplayInputBoundary.from_events(
                copied,
                run_id=run_id,
                code_revision=code_revision,
                config_hash=config_hash,
                provider_id=resolved_provider,
                capture_scope=resolved_scope,
                content_hashes=content_hashes,
                temporal_semantics=temporal_semantics,
            )

        object.__setattr__(self, "boundary", resolved_boundary)
        object.__setattr__(self, "run_id", resolved_boundary.run_id)
        object.__setattr__(self, "code_revision", resolved_boundary.code_revision)
        object.__setattr__(self, "config_hash", resolved_boundary.config_hash)
        object.__setattr__(self, "temporal_semantics", resolved_boundary.temporal_semantics)
        object.__setattr__(self, "lane", lane)
        object.__setattr__(self, "provider_id", resolved_provider)
        object.__setattr__(self, "provider", resolved_provider)
        object.__setattr__(self, "capture_scope", resolved_scope)
        object.__setattr__(self, "speed", resolved_speed)
        object.__setattr__(self, "rate", resolved_speed)
        object.__setattr__(self, "events", copied)
        object.__setattr__(self, "_knowledge", tuple(knowledge_times))

    def cursor(self) -> "CausalMarketReplayCursor":
        return CausalMarketReplayCursor(self)

    def __len__(self) -> int:
        return len(self.events)

    def __getitem__(self, index: int) -> EventEnvelope:
        return self.events[index]

    @property
    def instruments(self) -> tuple[str, ...]:
        return tuple(sorted({e.source.symbol for e in self.events}))

    @property
    def start_knowledge_time(self) -> datetime | None:
        return self._knowledge[0] if self._knowledge else None

    @property
    def end_knowledge_time(self) -> datetime | None:
        return self._knowledge[-1] if self._knowledge else None


class CausalMarketReplayCursor:
    """Monotonic inclusive knowledge-cutoff cursor over one immutable schedule."""

    __slots__ = ("_current_cutoff", "_index", "_last_emitted_knowledge", "_schedule")

    def __init__(self, schedule: CausalMarketReplaySchedule) -> None:
        if not isinstance(schedule, CausalMarketReplaySchedule):
            raise ValueError("cursor requires CausalMarketReplaySchedule")
        self._schedule = schedule
        self._index = 0
        self._current_cutoff: datetime | None = None
        self._last_emitted_knowledge: datetime | None = None

    @property
    def schedule(self) -> CausalMarketReplaySchedule:
        return self._schedule

    @property
    def current_cutoff(self) -> datetime | None:
        return self._current_cutoff

    @property
    def emitted_count(self) -> int:
        return self._index

    @property
    def remaining_count(self) -> int:
        return len(self._schedule.events) - self._index

    @property
    def complete(self) -> bool:
        return self._index == len(self._schedule.events)

    def advance_to(self, knowledge_cutoff: datetime) -> tuple[ReplayEmission, ...]:
        require_utc(knowledge_cutoff, "knowledge_cutoff")
        if self._current_cutoff is not None and knowledge_cutoff < self._current_cutoff:
            raise ValueError("replay cutoff must be monotonic: backward cutoff rejected")

        emissions: list[ReplayEmission] = []
        events = self._schedule.events
        knowledge_times = self._schedule._knowledge
        index = self._index
        last_knowledge = self._last_emitted_knowledge

        while index < len(events) and knowledge_times[index] <= knowledge_cutoff:
            knowledge = knowledge_times[index]
            source_delta_us = (
                0
                if last_knowledge is None
                else _delta_microseconds(knowledge - last_knowledge)
            )
            emissions.append(
                ReplayEmission(
                    ordinal=index,
                    envelope=events[index],
                    knowledge_time=knowledge,
                    source_delta_us=source_delta_us,
                    virtual_delay_us=self._schedule.speed.virtual_delay_us(source_delta_us),
                    run_id=self._schedule.run_id,
                )
            )
            last_knowledge = knowledge
            index += 1

        self._index = index
        self._last_emitted_knowledge = last_knowledge
        self._current_cutoff = knowledge_cutoff
        return tuple(emissions)
