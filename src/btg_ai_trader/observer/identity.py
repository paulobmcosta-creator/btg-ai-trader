"""Immutable typed identities, independent of provider symbol text (DD-01)."""

from dataclasses import dataclass
from uuid import UUID

from btg_ai_trader.observer.values import require_text


@dataclass(frozen=True, slots=True)
class _UuidId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise ValueError("identity must be canonical UUID text")
        try:
            parsed = UUID(self.value)
        except ValueError as error:
            raise ValueError("identity must be canonical UUID text") from error
        if str(parsed) != self.value:
            raise ValueError("identity must be lowercase hyphenated UUID text")


@dataclass(frozen=True, slots=True)
class EventId(_UuidId):
    """Identity of a fact; independent of capture or processing runs."""


@dataclass(frozen=True, slots=True)
class CorrelationId(_UuidId):
    """Identity of explicit correlation evidence, separate from event identity."""


@dataclass(frozen=True, slots=True)
class InstrumentFamilyId(_UuidId):
    """Economic family identity; not the identity of a concrete contract."""


@dataclass(frozen=True, slots=True)
class TradableInstrumentId(_UuidId):
    """Immutable internal identity of a concrete instrument."""


@dataclass(frozen=True, slots=True)
class ProviderInstrumentRef:
    """External symbol within its provider and declared reference scope."""

    provider: str
    scope: str
    symbol: str

    def __post_init__(self) -> None:
        require_text(self.provider, "provider")
        require_text(self.scope, "scope")
        require_text(self.symbol, "symbol")


@dataclass(frozen=True, slots=True)
class RunId(_UuidId):
    """A concrete execution identity; restart requires a new value."""


@dataclass(frozen=True, slots=True)
class ArtifactId(_UuidId):
    """Identity of an artifact, separate from its producing or processing run."""


@dataclass(frozen=True, slots=True)
class ReceiptId(_UuidId):
    """Identity of a processing observation, never the identity of its input."""


@dataclass(frozen=True, slots=True)
class LineageRecordId(_UuidId):
    """Identity of a derivation record, separate from processing receipts."""
