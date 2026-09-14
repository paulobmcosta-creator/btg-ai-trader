"""Point-in-time causal discovery tests for RQM-040 / AC-01."""

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from typing import cast
from uuid import UUID

import pytest

from btg_ai_trader.observer.discovery import InstrumentDiscovery, discover_instruments
from btg_ai_trader.observer.identity import (
    InstrumentFamilyId,
    ProviderInstrumentRef,
    TradableInstrumentId,
)
from btg_ai_trader.observer.instruments import InstrumentMapping, InstrumentRegistry

T0 = datetime(2026, 1, 1, tzinfo=UTC)
T1 = T0 + timedelta(days=1)
T2 = T0 + timedelta(days=2)
FAMILY = InstrumentFamilyId(str(UUID(int=91)))
OTHER_FAMILY = InstrumentFamilyId(str(UUID(int=92)))
FIRST = TradableInstrumentId(str(UUID(int=93)))
SECOND = TradableInstrumentId(str(UUID(int=94)))
REF_A = ProviderInstrumentRef("fixture-provider", "capture-a", "FUT-A")
REF_B = ProviderInstrumentRef("fixture-provider", "capture-a", "FUT-B")


def _mapping(
    reference: ProviderInstrumentRef,
    instrument_id: TradableInstrumentId,
    *,
    family_id: InstrumentFamilyId = FAMILY,
    valid_from: datetime = T0,
    valid_until: datetime | None = None,
    known_at: datetime = T0,
    evidence_ref: str = "fixture-discovery",
) -> InstrumentMapping:
    return InstrumentMapping(
        reference,
        instrument_id,
        family_id,
        valid_from,
        valid_until,
        known_at,
        evidence_ref,
    )


def _discover(registry: InstrumentRegistry, *, valid_at: datetime = T0, cutoff: datetime = T0) -> InstrumentDiscovery:
    return discover_instruments(
        registry,
        FAMILY,
        provider="fixture-provider",
        capture_scope="capture-a",
        valid_at=valid_at,
        knowledge_cutoff=cutoff,
    )


def test_discovery_respects_validity_and_historical_knowledge_cutoff() -> None:
    visible = _mapping(REF_A, FIRST)
    future_known = _mapping(REF_B, SECOND, known_at=T1)
    registry = InstrumentRegistry((visible, future_known))

    assert _discover(registry, cutoff=T0).matches == (visible,)
    assert _discover(registry, cutoff=T1).matches == (visible, future_known)

    expired = replace(visible, valid_until=T1)
    registry = InstrumentRegistry((expired, future_known))
    assert _discover(registry, valid_at=T1, cutoff=T1).matches == (future_known,)


def test_discovery_filters_family_provider_and_capture_scope_without_global_symbol_logic() -> None:
    included = _mapping(REF_A, FIRST)
    other_family = _mapping(REF_B, SECOND, family_id=OTHER_FAMILY)
    other_provider = _mapping(
        replace(REF_A, provider="other-provider"),
        TradableInstrumentId(str(UUID(int=95))),
    )
    other_scope = _mapping(
        replace(REF_A, scope="capture-b"),
        TradableInstrumentId(str(UUID(int=96))),
    )
    registry = InstrumentRegistry((included, other_family, other_provider, other_scope))

    assert _discover(registry).matches == (included,)


def test_overlapping_admissible_contracts_are_all_returned_without_ranking_or_selection() -> None:
    first = _mapping(REF_A, FIRST)
    second = _mapping(REF_B, SECOND)
    discovery = _discover(InstrumentRegistry((first, second)))

    assert discovery.matches == (first, second)
    assert not hasattr(discovery, "selected")
    assert not hasattr(discovery, "front_contract")
    assert not hasattr(discovery, "rank")


def test_discovered_reference_can_be_resolved_separately_at_same_point_in_time() -> None:
    first = _mapping(REF_A, FIRST)
    registry = InstrumentRegistry((first,))
    discovery = _discover(registry)

    assert discovery.matches == (first,)
    resolution = registry.resolve(REF_A, valid_at=T0, knowledge_cutoff=T0)
    assert resolution.instrument_id == FIRST
    assert resolution.family_id == FAMILY


def test_discovery_copies_finite_input_and_remains_immutable() -> None:
    source = [_mapping(REF_A, FIRST)]
    discovery = InstrumentDiscovery(source)
    source.clear()
    assert len(discovery.matches) == 1
    field_name = "matches"
    with pytest.raises(FrozenInstanceError):
        setattr(discovery, field_name, ())
    with pytest.raises(ValueError, match="InstrumentMapping"):
        InstrumentDiscovery([cast(InstrumentMapping, "bad")])


def test_discovery_requires_typed_family_nonempty_labels_and_unambiguous_utc_boundaries() -> None:
    registry = InstrumentRegistry((_mapping(REF_A, FIRST),))
    with pytest.raises(ValueError, match="InstrumentFamilyId"):
        discover_instruments(
            registry,
            cast(InstrumentFamilyId, FIRST),
            provider="fixture-provider",
            capture_scope="capture-a",
            valid_at=T0,
            knowledge_cutoff=T0,
        )
    for provider, scope in (("", "capture-a"), ("fixture-provider", " ")):
        with pytest.raises(ValueError):
            discover_instruments(
                registry,
                FAMILY,
                provider=provider,
                capture_scope=scope,
                valid_at=T0,
                knowledge_cutoff=T0,
            )
    for bad in (
        datetime(2026, 1, 1),
        datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=1))),
    ):
        with pytest.raises(ValueError, match="UTC"):
            discover_instruments(
                registry,
                FAMILY,
                provider="fixture-provider",
                capture_scope="capture-a",
                valid_at=bad,
                knowledge_cutoff=T0,
            )
        with pytest.raises(ValueError, match="UTC"):
            discover_instruments(
                registry,
                FAMILY,
                provider="fixture-provider",
                capture_scope="capture-a",
                valid_at=T0,
                knowledge_cutoff=bad,
            )


def test_discovery_has_no_network_subscription_or_execution_surface() -> None:
    discovery = _discover(InstrumentRegistry((_mapping(REF_A, FIRST),)))
    forbidden = {
        "subscribe",
        "connect",
        "authenticate",
        "order_send",
        "trade",
        "execute",
    }
    assert forbidden.isdisjoint(dir(discovery))
