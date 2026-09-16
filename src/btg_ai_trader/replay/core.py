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
from btg_ai_trader.observer.identity import EventId
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
class ReplayEmission:
    """One immutable market observation released by the causal replay cursor."""

    ordinal: int
    envelope: EventEnvelope
    knowledge_time: datetime
    source_delta_us: int
    virtual_delay_us: Fraction

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

    @property
    def event_id(self) -> EventId:
        return self.envelope.event_id

    @property
    def symbol(self) -> str:
        return self.envelope.source.symbol


@dataclass(frozen=True, slots=True, init=False)
class CausalMarketReplaySchedule:
    """Finite immutable replay lane for one provider/capture scope."""

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
        lane: CausalLane | None = None,
        provider_id: str | None = None,
        provider: str | None = None,
        capture_scope: str | None = None,
        scope: str | None = None,
        speed: ReplaySpeed | None = None,
        rate: ReplaySpeed | None = None,
    ) -> None:
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
            if resolved_provider_cand is None:
                raise ValueError("provider_id or provider must be supplied")
            require_text(resolved_provider_cand, "provider_id")
            resolved_provider = resolved_provider_cand

            if capture_scope is not None and scope is not None and capture_scope != scope:
                raise ValueError("conflicting capture_scope and scope")
            resolved_scope_cand = capture_scope if capture_scope is not None else scope
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

        copied = tuple(events)
        seen_event_ids: set[EventId] = set()
        knowledge_times: list[datetime] = []
        previous_knowledge: datetime | None = None

        for envelope in copied:
            if not isinstance(envelope, EventEnvelope):
                raise ValueError("replay schedule accepts only EventEnvelope values")
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
                )
            )
            last_knowledge = knowledge
            index += 1

        self._index = index
        self._last_emitted_knowledge = last_knowledge
        self._current_cutoff = knowledge_cutoff
        return tuple(emissions)
