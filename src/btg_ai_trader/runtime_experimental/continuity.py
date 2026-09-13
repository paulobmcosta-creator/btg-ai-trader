"""Experimental scoped journal metadata checks; never operational readiness."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum


class Integrity(Enum):
    VERIFIED = "VERIFIED"
    UNKNOWN = "UNKNOWN"
    CORRUPT = "CORRUPT"


class Continuity(Enum):
    METADATA_CONTIGUOUS = "METADATA_CONTIGUOUS"
    INSUFFICIENT = "INSUFFICIENT"


class Reason(Enum):
    SNAPSHOT_UNVERIFIED = "SNAPSHOT_UNVERIFIED"
    SEGMENT_UNVERIFIED = "SEGMENT_UNVERIFIED"
    WRONG_SCOPE = "WRONG_SCOPE"
    GAP = "GAP"
    OVERLAP = "OVERLAP"
    BEYOND_TARGET = "BEYOND_TARGET"
    MISSING_TAIL = "MISSING_TAIL"


def _position(value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValueError("journal position must be a nonnegative integer")


def _scope(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("explicit nonempty journal scope required")


@dataclass(frozen=True, slots=True)
class JournalSegment:
    scope: str
    start: int
    end: int
    integrity: Integrity

    def __post_init__(self) -> None:
        _scope(self.scope)
        _position(self.start)
        _position(self.end)
        if self.end <= self.start:
            raise ValueError("segment must be nonempty and forward")
        if not isinstance(self.integrity, Integrity):
            raise TypeError("explicit segment integrity required")


@dataclass(frozen=True, slots=True)
class RecoveryBoundary:
    scope: str
    snapshot_next: int
    target_next: int
    snapshot_integrity: Integrity

    def __post_init__(self) -> None:
        _scope(self.scope)
        _position(self.snapshot_next)
        _position(self.target_next)
        if self.target_next < self.snapshot_next:
            raise ValueError("target cannot precede snapshot boundary")
        if not isinstance(self.snapshot_integrity, Integrity):
            raise TypeError("explicit snapshot integrity required")


@dataclass(frozen=True, slots=True)
class ContinuityAssessment:
    boundary: RecoveryBoundary
    segments: tuple[JournalSegment, ...]
    status: Continuity
    reasons: tuple[Reason, ...]


def assess_continuity(
    boundary: RecoveryBoundary, segments: Iterable[JournalSegment]
) -> ContinuityAssessment:
    """Assess caller-supplied metadata; do not prove bytes or reconstruct state."""
    if not isinstance(boundary, RecoveryBoundary):
        raise TypeError("recovery boundary required")
    supplied = tuple(segments)
    if any(not isinstance(item, JournalSegment) for item in supplied):
        raise TypeError("journal segments required")
    reasons: list[Reason] = []

    def note(reason: Reason) -> None:
        if reason not in reasons:
            reasons.append(reason)

    if boundary.snapshot_integrity is not Integrity.VERIFIED:
        note(Reason.SNAPSHOT_UNVERIFIED)
    next_position = boundary.snapshot_next
    for segment in supplied:
        if segment.scope != boundary.scope:
            note(Reason.WRONG_SCOPE)
        if segment.integrity is not Integrity.VERIFIED:
            note(Reason.SEGMENT_UNVERIFIED)
        if segment.start > next_position:
            note(Reason.GAP)
        elif segment.start < next_position:
            note(Reason.OVERLAP)
        if segment.end > boundary.target_next:
            note(Reason.BEYOND_TARGET)
        next_position = segment.end
    if next_position < boundary.target_next:
        note(Reason.MISSING_TAIL)
    status = Continuity.INSUFFICIENT if reasons else Continuity.METADATA_CONTIGUOUS
    return ContinuityAssessment(boundary, supplied, status, tuple(reasons))
