"""Regression fixtures for metadata continuity, not state recovery."""

from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from btg_ai_trader.runtime_experimental.continuity import (
    Continuity,
    Integrity,
    JournalSegment,
    Reason,
    RecoveryBoundary,
    assess_continuity,
)


def boundary(
    target: int = 5, integrity: Integrity = Integrity.VERIFIED
) -> RecoveryBoundary:
    return RecoveryBoundary("journal-A", 1, target, integrity)


def segment(start: int, end: int) -> JournalSegment:
    return JournalSegment("journal-A", start, end, Integrity.VERIFIED)


def test_exact_adjacency_preserves_input_and_boundary() -> None:
    inputs = [segment(1, 3), segment(3, 5)]
    cut = boundary()
    result = assess_continuity(cut, inputs)
    inputs.clear()
    assert result.status is Continuity.METADATA_CONTIGUOUS
    assert result.boundary is cut
    assert result.segments == (segment(1, 3), segment(3, 5))
    assert result.reasons == ()
    with pytest.raises(FrozenInstanceError):
        result.status = Continuity.INSUFFICIENT  # type: ignore[misc]


@pytest.mark.parametrize(
    ("items", "reason"),
    [
        ([], Reason.MISSING_TAIL),
        ([segment(1, 3)], Reason.MISSING_TAIL),
        ([segment(2, 5)], Reason.GAP),
        ([segment(1, 3), segment(2, 5)], Reason.OVERLAP),
        ([segment(1, 6)], Reason.BEYOND_TARGET),
        ([segment(3, 5), segment(1, 3)], Reason.GAP),
        (
            [JournalSegment("journal-B", 1, 5, Integrity.VERIFIED)],
            Reason.WRONG_SCOPE,
        ),
    ],
)
def test_incoherent_boundary_is_insufficient(
    items: list[JournalSegment], reason: Reason
) -> None:
    result = assess_continuity(boundary(), items)
    assert result.status is Continuity.INSUFFICIENT
    assert reason in result.reasons
    assert result.segments == tuple(items)


@pytest.mark.parametrize("integrity", [Integrity.UNKNOWN, Integrity.CORRUPT])
def test_integrity_assertions_never_default_to_verified(integrity: Integrity) -> None:
    snap = assess_continuity(boundary(integrity=integrity), [segment(1, 5)])
    journal = assess_continuity(
        boundary(), [JournalSegment("journal-A", 1, 5, integrity)]
    )
    assert snap.reasons == (Reason.SNAPSHOT_UNVERIFIED,)
    assert journal.reasons == (Reason.SEGMENT_UNVERIFIED,)
    assert snap.status is journal.status is Continuity.INSUFFICIENT


def test_empty_required_range_and_extraneous_segment() -> None:
    cut = boundary(target=1)
    assert assess_continuity(cut, []).status is Continuity.METADATA_CONTIGUOUS
    assert assess_continuity(cut, [segment(1, 2)]).status is Continuity.INSUFFICIENT
    assert assess_continuity(
        boundary(target=1, integrity=Integrity.UNKNOWN), []
    ).status is Continuity.INSUFFICIENT


@pytest.mark.parametrize("invalid", [-1, True, 1.0, None, "1"])
def test_positions_are_strict(invalid: Any) -> None:
    with pytest.raises(ValueError):
        RecoveryBoundary("journal-A", invalid, 5, Integrity.VERIFIED)
    with pytest.raises(ValueError):
        JournalSegment("journal-A", 1, invalid, Integrity.VERIFIED)


@pytest.mark.parametrize("scope", ["", " ", None, 1])
def test_scope_is_explicit(scope: Any) -> None:
    with pytest.raises(ValueError):
        RecoveryBoundary(scope, 1, 5, Integrity.VERIFIED)
    with pytest.raises(ValueError):
        JournalSegment(scope, 1, 5, Integrity.VERIFIED)


def test_reversed_boundaries_and_untyped_integrity_fail() -> None:
    with pytest.raises(ValueError):
        boundary(target=0)
    with pytest.raises(ValueError):
        segment(2, 2)
    with pytest.raises(ValueError):
        segment(2, 1)
    invalid: Any = "VERIFIED"
    with pytest.raises(TypeError):
        RecoveryBoundary("journal-A", 1, 5, invalid)
    with pytest.raises(TypeError):
        JournalSegment("journal-A", 1, 5, invalid)
    with pytest.raises(TypeError):
        assess_continuity(invalid, [])
    with pytest.raises(TypeError):
        assess_continuity(boundary(), [invalid])


def test_repeated_reasons_are_stable_and_not_silently_sorted() -> None:
    inputs = [segment(2, 3), segment(4, 5)]
    result = assess_continuity(boundary(), inputs)
    assert result.reasons == (Reason.GAP,)
    assert result.segments == tuple(inputs)
    assert assess_continuity(boundary(), inputs) == result
