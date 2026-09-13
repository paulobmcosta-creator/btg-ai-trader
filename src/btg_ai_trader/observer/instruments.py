"""Passive scoped point-in-time instrument mapping; no selection or trading authority."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from btg_ai_trader.observer.identity import (
    InstrumentFamilyId,
    ProviderInstrumentRef,
    TradableInstrumentId,
)
from btg_ai_trader.observer.temporal import require_utc
from btg_ai_trader.observer.values import require_text


@dataclass(frozen=True, slots=True)
class InstrumentMapping:
    reference: ProviderInstrumentRef
    instrument_id: TradableInstrumentId
    family_id: InstrumentFamilyId
    valid_from: datetime
    valid_until: datetime | None
    known_at: datetime
    evidence_ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.reference, ProviderInstrumentRef):
            raise ValueError("reference must be ProviderInstrumentRef")
        if not isinstance(self.instrument_id, TradableInstrumentId):
            raise ValueError("instrument_id must be TradableInstrumentId")
        if not isinstance(self.family_id, InstrumentFamilyId):
            raise ValueError("family_id must be InstrumentFamilyId")
        require_utc(self.valid_from, "valid_from")
        require_utc(self.known_at, "known_at")
        if self.valid_until is not None:
            require_utc(self.valid_until, "valid_until")
            if self.valid_until <= self.valid_from:
                raise ValueError("validity must have positive duration")
        require_text(self.evidence_ref, "evidence_ref")


class ResolutionStatus(Enum):
    NOT_FOUND = "NOT_FOUND"
    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True, slots=True, init=False)
class InstrumentResolution:
    """Admissible evidence and derived disposition; ambiguity exposes no chosen ID."""

    matches: tuple[InstrumentMapping, ...]

    def __init__(self, matches: Iterable[InstrumentMapping]) -> None:
        copied = tuple(matches)
        if any(not isinstance(item, InstrumentMapping) for item in copied):
            raise ValueError("resolution evidence must contain InstrumentMapping records")
        object.__setattr__(self, "matches", copied)

    @property
    def status(self) -> ResolutionStatus:
        if not self.matches:
            return ResolutionStatus.NOT_FOUND
        identities = {(item.instrument_id, item.family_id) for item in self.matches}
        if len(identities) == 1:
            return ResolutionStatus.RESOLVED
        return ResolutionStatus.AMBIGUOUS

    @property
    def instrument_id(self) -> TradableInstrumentId | None:
        if self.status is ResolutionStatus.RESOLVED:
            return self.matches[0].instrument_id
        return None

    @property
    def family_id(self) -> InstrumentFamilyId | None:
        if self.status is ResolutionStatus.RESOLVED:
            return self.matches[0].family_id
        return None


@dataclass(frozen=True, slots=True, init=False)
class InstrumentRegistry:
    """Immutable finite snapshot; no clock reads, global symbols or latest-wins policy."""

    mappings: tuple[InstrumentMapping, ...]

    def __init__(self, mappings: Iterable[InstrumentMapping]) -> None:
        copied = tuple(mappings)
        if any(not isinstance(item, InstrumentMapping) for item in copied):
            raise ValueError("registry requires InstrumentMapping records")
        object.__setattr__(self, "mappings", copied)

    def resolve(
        self,
        reference: ProviderInstrumentRef,
        *,
        valid_at: datetime,
        knowledge_cutoff: datetime,
    ) -> InstrumentResolution:
        if not isinstance(reference, ProviderInstrumentRef):
            raise ValueError("reference must be ProviderInstrumentRef")
        require_utc(valid_at, "valid_at")
        require_utc(knowledge_cutoff, "knowledge_cutoff")
        matches = tuple(
            item
            for item in self.mappings
            if item.known_at <= knowledge_cutoff
            and item.reference == reference
            and item.valid_from <= valid_at
            and (item.valid_until is None or valid_at < item.valid_until)
        )
        return InstrumentResolution(matches)
