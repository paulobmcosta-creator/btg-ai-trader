"""Speculative Sprint 2 market-data replay with causal knowledge cutoffs.

This module is deliberately pure: no wall clock, sleeping, provider I/O, strategy,
execution or financial simulation. It replays immutable Observer EventEnvelope values
according to explicit knowledge-time evidence and caller-supplied order.
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


def _positive_int(value: int, field: str) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field} must be a positive integer")


def _delta_microseconds(delta: timedelta) -> int:
    if delta < timedelta(0):
        raise ValueError("replay delta must not be negative")
    return (
        (delta.days * _SECONDS_PER_DAY + delta.seconds) * _MICROSECONDS_PER_SECOND
        + delta.microseconds
    )


@dataclass(frozen=True, slots=True)
class ReplayRate:
    """Exact rational playback rate; 2/1 means two times source knowledge speed."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        _positive_int(self.numerator, "rate numerator")
        _positive_int(self.denominator, "rate denominator")

    def virtual_delay_us(self, source_delta_us: int) -> Fraction:
        if type(source_delta_us) is not int or source_delta_us < 0:
            raise ValueError("source_delta_us must be a nonnegative integer")
        return Fraction(source_delta_us * self.denominator, self.numerator)


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


@dataclass(frozen=True, slots=True, init=False)
class CausalMarketReplaySchedule:
    """Finite immutable replay lane for one provider/capture scope."""

    provider: str
    capture_scope: str
    rate: ReplayRate
    events: tuple[EventEnvelope, ...]
    _knowledge: tuple[datetime, ...] = field(repr=False)

    def __init__(
        self,
        events: Iterable[EventEnvelope],
        *,
        provider: str,
        capture_scope: str,
        rate: ReplayRate,
    ) -> None:
        require_text(provider, "provider")
        require_text(capture_scope, "capture_scope")
        if not isinstance(rate, ReplayRate):
            raise ValueError("rate must be ReplayRate")

        copied = tuple(events)
        seen_event_ids: set[EventId] = set()
        knowledge_times: list[datetime] = []
        previous_knowledge: datetime | None = None

        for envelope in copied:
            if not isinstance(envelope, EventEnvelope):
                raise ValueError("replay schedule accepts only EventEnvelope values")
            if envelope.source.provider != provider or envelope.source.scope != capture_scope:
                raise ValueError("all replay events must belong to one provider/capture scope")
            if envelope.event_id in seen_event_ids:
                raise ValueError("replay schedule must not repeat EventId")
            seen_event_ids.add(envelope.event_id)

            knowledge = envelope.times.knowledge_time
            if not isinstance(knowledge, datetime):
                raise ValueError("formal replay requires known knowledge_time")
            require_utc(knowledge, "knowledge_time")
            if previous_knowledge is not None and knowledge < previous_knowledge:
                raise ValueError("supplied replay order contradicts knowledge-time causality")
            knowledge_times.append(knowledge)
            previous_knowledge = knowledge

        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "capture_scope", capture_scope)
        object.__setattr__(self, "rate", rate)
        object.__setattr__(self, "events", copied)
        object.__setattr__(self, "_knowledge", tuple(knowledge_times))

    def cursor(self) -> "CausalMarketReplayCursor":
        return CausalMarketReplayCursor(self)


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
    def current_cutoff(self) -> datetime | None:
        return self._current_cutoff

    @property
    def emitted_count(self) -> int:
        return self._index

    @property
    def complete(self) -> bool:
        return self._index == len(self._schedule.events)

    def advance_to(self, knowledge_cutoff: datetime) -> tuple[ReplayEmission, ...]:
        require_utc(knowledge_cutoff, "knowledge_cutoff")
        if self._current_cutoff is not None and knowledge_cutoff < self._current_cutoff:
            raise ValueError("replay cutoff must be monotonic")

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
                    virtual_delay_us=self._schedule.rate.virtual_delay_us(source_delta_us),
                )
            )
            last_knowledge = knowledge
            index += 1

        self._index = index
        self._last_emitted_knowledge = last_knowledge
        self._current_cutoff = knowledge_cutoff
        return tuple(emissions)
