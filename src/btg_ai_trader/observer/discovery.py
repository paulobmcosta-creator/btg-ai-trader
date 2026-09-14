"""Passive point-in-time discovery over evidenced instrument-registry snapshots."""

from dataclasses import dataclass
from datetime import datetime

from btg_ai_trader.observer.identity import InstrumentFamilyId
from btg_ai_trader.observer.instruments import InstrumentMapping, InstrumentRegistry
from btg_ai_trader.observer.temporal import require_utc
from btg_ai_trader.observer.values import require_text


@dataclass(frozen=True, slots=True)
class InstrumentDiscovery:
    """All admissible mappings; this evidence never ranks or selects a contract."""

    matches: tuple[InstrumentMapping, ...]

    def __post_init__(self) -> None:
        if type(self.matches) is not tuple or any(
            not isinstance(item, InstrumentMapping) for item in self.matches
        ):
            raise ValueError("discovery evidence must be an immutable tuple of InstrumentMapping")


def discover_instruments(
    registry: InstrumentRegistry,
    family_id: InstrumentFamilyId,
    *,
    provider: str,
    capture_scope: str,
    valid_at: datetime,
    knowledge_cutoff: datetime,
) -> InstrumentDiscovery:
    """Return mappings admissible at both validity and historical-knowledge boundaries."""
    if not isinstance(registry, InstrumentRegistry):
        raise ValueError("discovery requires InstrumentRegistry")
    if not isinstance(family_id, InstrumentFamilyId):
        raise ValueError("discovery requires InstrumentFamilyId")
    require_text(provider, "provider")
    require_text(capture_scope, "capture_scope")
    require_utc(valid_at, "valid_at")
    require_utc(knowledge_cutoff, "knowledge_cutoff")
    matches = tuple(
        item
        for item in registry.mappings
        if item.family_id == family_id
        and item.reference.provider == provider
        and item.reference.scope == capture_scope
        and item.known_at <= knowledge_cutoff
        and item.valid_from <= valid_at
        and (item.valid_until is None or valid_at < item.valid_until)
    )
    return InstrumentDiscovery(matches)
