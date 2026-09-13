"""SPECULATIVE fixture-only replay clock; never part of the S1 Observer."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime


def _utc(value: datetime) -> datetime:
    """Reject missing/naive availability instead of fabricating temporal evidence."""
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("a known timezone-aware instant is required")
    return value.astimezone(UTC)


def _nonempty(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


class ReplayClock:
    """A controllable clock with no system-time or I/O dependency."""

    __slots__ = ("_now",)

    def __init__(self, initial_time: datetime) -> None:
        self._now = _utc(initial_time)

    @property
    def now(self) -> datetime:
        return self._now

    def advance_to(self, instant: datetime) -> None:
        resolved = _utc(instant)
        if resolved < self._now:
            raise ValueError("replay time cannot move backward")
        self._now = resolved


@dataclass(frozen=True, slots=True)
class FixtureScheduleEntry:
    """Opaque fixture reference, proven availability and explicitly scoped order."""

    fixture_ref: str
    knowledge_time: datetime
    order_scope: str
    position: int

    def __post_init__(self) -> None:
        _nonempty(self.fixture_ref, "fixture_ref")
        _nonempty(self.order_scope, "order_scope")
        if type(self.position) is not int or self.position < 0:
            raise ValueError("position must be a non-negative integer")
        object.__setattr__(self, "knowledge_time", _utc(self.knowledge_time))


@dataclass(frozen=True, slots=True, init=False)
class ReplaySchedule:
    """A finite single-scope fixture boundary; supplied order is never synthesized."""

    entries: tuple[FixtureScheduleEntry, ...]

    def __init__(self, entries: Iterable[FixtureScheduleEntry]) -> None:
        frozen_entries = tuple(entries)
        seen: set[str] = set()
        previous: FixtureScheduleEntry | None = None
        for entry in frozen_entries:
            if not isinstance(entry, FixtureScheduleEntry):
                raise ValueError("schedule requires FixtureScheduleEntry values")
            if entry.fixture_ref in seen:
                raise ValueError("fixture references must be unique within this boundary")
            seen.add(entry.fixture_ref)
            if previous is not None:
                if entry.order_scope != previous.order_scope:
                    raise ValueError("independent ordering scopes require an explicit merge policy")
                if entry.position <= previous.position:
                    raise ValueError("positions must strictly increase within their scope")
                if entry.knowledge_time < previous.knowledge_time:
                    raise ValueError("supplied ordering conflicts with knowledge availability")
            previous = entry
        object.__setattr__(self, "entries", frozen_entries)


class ReplayCursor:
    """Release known fixtures causally with inclusive, monotonic knowledge cutoffs."""

    __slots__ = ("_clock", "_next_index", "_schedule")

    def __init__(self, schedule: ReplaySchedule, initial_time: datetime) -> None:
        clock = ReplayClock(initial_time)
        if schedule.entries and schedule.entries[0].knowledge_time < clock.now:
            raise ValueError("initial time cannot skip unprocessed fixture history")
        self._schedule = schedule
        self._clock = clock
        self._next_index = 0

    @property
    def now(self) -> datetime:
        return self._clock.now

    @property
    def exhausted(self) -> bool:
        return self._next_index == len(self._schedule.entries)

    def advance_to(self, knowledge_cutoff: datetime) -> tuple[FixtureScheduleEntry, ...]:
        cutoff = _utc(knowledge_cutoff)
        if cutoff < self.now:
            raise ValueError("knowledge cutoff cannot move backward")
        end = self._next_index
        entries = self._schedule.entries
        while end < len(entries) and entries[end].knowledge_time <= cutoff:
            end += 1
        released = entries[self._next_index : end]
        for entry in released:
            self._clock.advance_to(entry.knowledge_time)
        self._clock.advance_to(cutoff)
        self._next_index = end
        return released
