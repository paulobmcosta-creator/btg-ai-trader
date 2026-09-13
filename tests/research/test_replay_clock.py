"""Fixture-only engineering evidence, not financial or historical validation."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone

import pytest

from btg_ai_trader.research.replay_clock import (
    FixtureScheduleEntry,
    ReplayClock,
    ReplayCursor,
    ReplaySchedule,
)

START = datetime(2026, 1, 1, tzinfo=UTC)


def entry(
    name: str = "fixture:a",
    seconds: int = 1,
    position: int = 1,
    scope: str = "fixture-session:one",
) -> FixtureScheduleEntry:
    return FixtureScheduleEntry(name, START + timedelta(seconds=seconds), scope, position)


def test_clock_is_monotonic_and_equal_instant_is_allowed() -> None:
    clock = ReplayClock(START)
    clock.advance_to(START)
    clock.advance_to(START + timedelta(seconds=2))
    with pytest.raises(ValueError, match="backward"):
        clock.advance_to(START)
    assert clock.now == START + timedelta(seconds=2)


def test_clock_uses_utc_without_inventing_time() -> None:
    offset = timezone(timedelta(hours=-3))
    instant = datetime(2025, 12, 31, 21, tzinfo=offset)
    assert ReplayClock(instant).now == START
    item = FixtureScheduleEntry("fixture:a", instant, "scope", 0)
    assert item.knowledge_time.tzinfo is UTC
    assert item.knowledge_time == START


def test_naive_times_are_rejected_at_every_temporal_boundary() -> None:
    naive = datetime(2026, 1, 1)
    with pytest.raises(ValueError, match="timezone-aware"):
        ReplayClock(naive)
    with pytest.raises(ValueError, match="timezone-aware"):
        FixtureScheduleEntry("fixture:a", naive, "scope", 1)
    clock = ReplayClock(START)
    with pytest.raises(ValueError, match="timezone-aware"):
        clock.advance_to(naive)
    cursor = ReplayCursor(ReplaySchedule([entry()]), START)
    with pytest.raises(ValueError, match="timezone-aware"):
        cursor.advance_to(naive)
    assert clock.now == cursor.now == START
    assert cursor.advance_to(START + timedelta(seconds=1)) == (entry(),)


def test_unknown_time_is_not_imputed() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ReplayClock(None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        FixtureScheduleEntry("fixture:a", None, "scope", 0)  # type: ignore[arg-type]


@pytest.mark.parametrize("field_value", ["", " ", "\n"])
def test_empty_identity_and_scope_are_rejected(field_value: str) -> None:
    with pytest.raises(ValueError, match="fixture_ref"):
        FixtureScheduleEntry(field_value, START, "scope", 0)
    with pytest.raises(ValueError, match="order_scope"):
        FixtureScheduleEntry("fixture:a", START, field_value, 0)


@pytest.mark.parametrize("position", [-1, True, False])
def test_position_is_an_actual_nonnegative_integer(position: int) -> None:
    with pytest.raises(ValueError, match="non-negative integer"):
        entry(position=position)


def test_input_boundary_is_copied_and_records_are_immutable() -> None:
    source = [entry()]
    schedule = ReplaySchedule(source)
    source.append(entry("fixture:b", 2, 2))
    assert schedule.entries == (entry(),)
    with pytest.raises(FrozenInstanceError):
        schedule.entries[0].knowledge_time = START  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        schedule.entries = ()  # type: ignore[misc]
    assert schedule.entries == (entry(),)


def test_duplicate_reference_does_not_become_another_input() -> None:
    with pytest.raises(ValueError, match="unique"):
        ReplaySchedule([entry(), entry(seconds=2, position=2)])


def test_independent_scopes_are_not_fabricated_into_global_order() -> None:
    with pytest.raises(ValueError, match="merge policy"):
        ReplaySchedule([entry(), entry("fixture:b", 2, 2, "other-scope")])


@pytest.mark.parametrize("second_position", [0, 1])
def test_nonincreasing_position_is_rejected(second_position: int) -> None:
    with pytest.raises(ValueError, match="strictly increase"):
        ReplaySchedule([entry(), entry("fixture:b", 2, second_position)])


def test_conflicting_time_is_rejected_instead_of_resorted() -> None:
    with pytest.raises(ValueError, match="conflicts"):
        ReplaySchedule([entry(seconds=2), entry("fixture:b", 1, 2)])


def test_future_inputs_are_withheld_and_exact_cutoff_is_inclusive() -> None:
    first = entry()
    second = entry("fixture:b", 2, 2)
    cursor = ReplayCursor(ReplaySchedule([first, second]), START)
    assert cursor.advance_to(START + timedelta(microseconds=999999)) == ()
    assert not cursor.exhausted
    assert cursor.advance_to(first.knowledge_time) == (first,)
    assert cursor.now == first.knowledge_time
    assert cursor.advance_to(first.knowledge_time) == ()
    assert not cursor.exhausted
    assert cursor.advance_to(second.knowledge_time) == (second,)
    assert cursor.exhausted
    assert cursor.advance_to(START + timedelta(seconds=10)) == ()
    assert cursor.now == START + timedelta(seconds=10)


def test_equal_times_follow_supplied_scoped_positions() -> None:
    first = entry("fixture:z", 1, 3)
    second = entry("fixture:a", 1, 7)
    cursor = ReplayCursor(ReplaySchedule([first, second]), START)
    assert cursor.advance_to(first.knowledge_time) == (first, second)


def test_backward_cutoff_does_not_consume_pending_items() -> None:
    first = entry()
    second = entry("fixture:b", 2, 2)
    cursor = ReplayCursor(ReplaySchedule([first, second]), START)
    assert cursor.advance_to(first.knowledge_time) == (first,)
    with pytest.raises(ValueError, match="backward"):
        cursor.advance_to(START)
    assert cursor.now == first.knowledge_time
    assert cursor.advance_to(second.knowledge_time) == (second,)


def test_initial_clock_cannot_silently_skip_history() -> None:
    with pytest.raises(ValueError, match="skip"):
        ReplayCursor(ReplaySchedule([entry()]), START + timedelta(seconds=2))


def test_empty_schedule_advances_without_inventing_inputs() -> None:
    cursor = ReplayCursor(ReplaySchedule([]), START)
    assert cursor.exhausted
    assert cursor.advance_to(START + timedelta(seconds=5)) == ()
    assert cursor.now == START + timedelta(seconds=5)


def test_same_input_and_cutoffs_produce_exactly_equal_trace() -> None:
    schedule = ReplaySchedule([entry(), entry("fixture:b", 3, 8), entry("fixture:c", 3, 9)])
    left = ReplayCursor(schedule, START)
    right = ReplayCursor(schedule, START)
    for seconds in (0, 1, 1, 2, 3, 7):
        cutoff = START + timedelta(seconds=seconds)
        assert left.advance_to(cutoff) == right.advance_to(cutoff)
        assert left.now == right.now
        assert left.exhausted == right.exhausted


def test_schedule_rejects_non_entry_values() -> None:
    with pytest.raises(ValueError, match="FixtureScheduleEntry"):
        ReplaySchedule(["not-an-entry"])  # type: ignore[list-item]
