"""Passive fixture evidence for scoped registry and capability metadata contracts."""

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from typing import cast

import pytest

from btg_ai_trader.observer.identity import (
    InstrumentFamilyId,
    ProviderInstrumentRef,
    TradableInstrumentId,
)
from btg_ai_trader.observer.instruments import (
    InstrumentMapping,
    InstrumentRegistry,
    InstrumentResolution,
    ResolutionStatus,
)
from btg_ai_trader.observer.provider import (
    CapabilitySupport,
    FidelityMode,
    ProviderCapabilities,
    ProviderMetadata,
)
from btg_ai_trader.observer.values import MissingReason

T0 = datetime(2026, 1, 1, tzinfo=UTC)
T1 = T0 + timedelta(days=1)
T2 = T0 + timedelta(days=2)
REF = ProviderInstrumentRef("fixture-provider", "capture-a", "FIXTURE-SYMBOL")
ID_A = TradableInstrumentId("38f4a8d0-b7da-48a4-950d-0bf9c8220411")
ID_B = TradableInstrumentId("38f4a8d0-b7da-48a4-950d-0bf9c8220412")
FAMILY = InstrumentFamilyId("38f4a8d0-b7da-48a4-950d-0bf9c8220413")


def mapping() -> InstrumentMapping:
    return InstrumentMapping(REF, ID_A, FAMILY, T0, T1, T0, "fixture-evidence:one")


def capabilities() -> ProviderCapabilities:
    return ProviderCapabilities(
        provider=REF.provider,
        capture_scope=REF.scope,
        ticks=CapabilitySupport.SUPPORTED,
        candles=CapabilitySupport.UNKNOWN,
        source_sequence=CapabilitySupport.UNKNOWN,
        timestamp_resolution=MissingReason.UNKNOWN,
        fidelity=FidelityMode.UNKNOWN,
    )


def test_registry_uses_both_validity_and_knowledge_boundaries() -> None:
    late = replace(mapping(), known_at=T1)
    registry = InstrumentRegistry([late])
    hidden = registry.resolve(REF, valid_at=T0, knowledge_cutoff=T0)
    assert hidden.status is ResolutionStatus.NOT_FOUND
    assert hidden.instrument_id is None
    assert hidden.family_id is None
    assert hidden.matches == ()
    visible = registry.resolve(REF, valid_at=T0, knowledge_cutoff=T1)
    assert visible.status is ResolutionStatus.RESOLVED
    assert visible.instrument_id == ID_A
    assert visible.family_id == FAMILY
    assert visible.matches == (late,)


def test_validity_start_is_inclusive_and_end_exclusive() -> None:
    registry = InstrumentRegistry([mapping()])
    assert registry.resolve(REF, valid_at=T0, knowledge_cutoff=T2).instrument_id == ID_A
    assert (
        registry.resolve(REF, valid_at=T0 - timedelta(microseconds=1), knowledge_cutoff=T2).status
        is ResolutionStatus.NOT_FOUND
    )
    assert (
        registry.resolve(REF, valid_at=T1, knowledge_cutoff=T2).status
        is ResolutionStatus.NOT_FOUND
    )


def test_symbol_reuse_does_not_mutate_contract_identity() -> None:
    earlier = mapping()
    later = replace(earlier, instrument_id=ID_B, valid_from=T1, valid_until=None)
    registry = InstrumentRegistry([earlier, later])
    assert registry.resolve(REF, valid_at=T0, knowledge_cutoff=T0).instrument_id == ID_A
    assert registry.resolve(REF, valid_at=T1, knowledge_cutoff=T0).instrument_id == ID_B
    assert registry.resolve(REF, valid_at=T2, knowledge_cutoff=T0).instrument_id == ID_B
    assert earlier.instrument_id == ID_A


def test_provider_and_capture_scope_prevent_global_symbol_resolution() -> None:
    registry = InstrumentRegistry([mapping()])
    for other in (replace(REF, provider="other"), replace(REF, scope="capture-b")):
        assert (
            registry.resolve(other, valid_at=T0, knowledge_cutoff=T0).status
            is ResolutionStatus.NOT_FOUND
        )


def test_many_provider_references_may_resolve_to_one_instrument() -> None:
    other = replace(REF, provider="another-provider", symbol="OTHER-SYMBOL")
    registry = InstrumentRegistry([mapping(), replace(mapping(), reference=other)])
    for reference in (REF, other):
        assert registry.resolve(reference, valid_at=T0, knowledge_cutoff=T0).instrument_id == ID_A


def test_conflicts_fail_closed_instead_of_selecting_first_or_latest() -> None:
    first = mapping()
    conflict = replace(first, instrument_id=ID_B, known_at=T1, evidence_ref="fixture-evidence:two")
    registry = InstrumentRegistry([first, conflict])
    assert registry.resolve(REF, valid_at=T0, knowledge_cutoff=T0).instrument_id == ID_A
    result = registry.resolve(REF, valid_at=T0, knowledge_cutoff=T1)
    assert result.status is ResolutionStatus.AMBIGUOUS
    assert result.instrument_id is None
    assert result.family_id is None
    assert result.matches == (first, conflict)


def test_conflicting_family_is_not_silently_accepted() -> None:
    other_family = InstrumentFamilyId("38f4a8d0-b7da-48a4-950d-0bf9c8220414")
    registry = InstrumentRegistry([mapping(), replace(mapping(), family_id=other_family)])
    assert (
        registry.resolve(REF, valid_at=T0, knowledge_cutoff=T0).status
        is ResolutionStatus.AMBIGUOUS
    )


def test_agreeing_evidence_does_not_create_false_ambiguity() -> None:
    second = replace(mapping(), evidence_ref="fixture-evidence:two")
    registry = InstrumentRegistry([mapping(), second])
    result = registry.resolve(REF, valid_at=T0, knowledge_cutoff=T0)
    assert result.status is ResolutionStatus.RESOLVED
    assert result.matches == (mapping(), second)


def test_registry_and_resolution_copy_finite_inputs_and_remain_immutable() -> None:
    source = [mapping()]
    registry = InstrumentRegistry(source)
    result = InstrumentResolution(source)
    source.clear()
    assert registry.mappings == result.matches == (mapping(),)
    field_name = "mappings"
    with pytest.raises(FrozenInstanceError):
        setattr(registry, field_name, ())
    field_name = "instrument_id"
    with pytest.raises(FrozenInstanceError):
        setattr(registry.mappings[0], field_name, ID_B)


@pytest.mark.parametrize("bad", [T0, T0 - timedelta(microseconds=1)])
def test_invalid_validity_interval_is_rejected(bad: datetime) -> None:
    with pytest.raises(ValueError, match="positive duration"):
        replace(mapping(), valid_until=bad)


@pytest.mark.parametrize(
    "bad",
    [
        datetime(2026, 1, 1),
        datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=1))),
        None,
        MissingReason.UNKNOWN,
    ],
)
def test_unknown_or_ambiguous_times_never_enter_resolvable_catalog(bad: object) -> None:
    with pytest.raises(ValueError, match="UTC"):
        replace(mapping(), known_at=cast(datetime, bad))
    with pytest.raises(ValueError, match="UTC"):
        InstrumentRegistry([mapping()]).resolve(
            REF, valid_at=cast(datetime, bad), knowledge_cutoff=T0
        )
    with pytest.raises(ValueError, match="UTC"):
        InstrumentRegistry([mapping()]).resolve(
            REF, valid_at=T0, knowledge_cutoff=cast(datetime, bad)
        )


def test_invalid_identities_and_evidence_are_rejected() -> None:
    with pytest.raises(ValueError, match="reference"):
        replace(mapping(), reference=cast(ProviderInstrumentRef, "symbol"))
    with pytest.raises(ValueError, match="instrument_id"):
        replace(mapping(), instrument_id=cast(TradableInstrumentId, FAMILY))
    with pytest.raises(ValueError, match="family_id"):
        replace(mapping(), family_id=cast(InstrumentFamilyId, ID_A))
    with pytest.raises(ValueError, match="evidence_ref"):
        replace(mapping(), evidence_ref=" ")
    with pytest.raises(ValueError, match="reference"):
        InstrumentRegistry([]).resolve(
            cast(ProviderInstrumentRef, "symbol"), valid_at=T0, knowledge_cutoff=T0
        )
    for constructor in (InstrumentRegistry, InstrumentResolution):
        with pytest.raises(ValueError, match="InstrumentMapping"):
            constructor([cast(InstrumentMapping, "bad")])


def test_empty_registry_means_no_admissible_mapping_not_no_market() -> None:
    result = InstrumentRegistry([]).resolve(REF, valid_at=T0, knowledge_cutoff=T0)
    assert result.status is ResolutionStatus.NOT_FOUND


def test_unknown_capabilities_are_not_promoted_to_supported() -> None:
    descriptor = capabilities()
    assert descriptor.candles is CapabilitySupport.UNKNOWN
    assert descriptor.source_sequence is CapabilitySupport.UNKNOWN
    assert descriptor.fidelity is FidelityMode.UNKNOWN
    assert descriptor.timestamp_resolution is MissingReason.UNKNOWN
    assert descriptor.sequence_scope is None
    absent = replace(descriptor, ticks=CapabilitySupport.UNSUPPORTED)
    assert absent.ticks is CapabilitySupport.UNSUPPORTED


def test_source_sequence_support_and_fidelity_require_scope() -> None:
    descriptor = capabilities()
    with pytest.raises(ValueError, match="requires its scope"):
        replace(descriptor, source_sequence=CapabilitySupport.SUPPORTED)
    for support in (CapabilitySupport.UNKNOWN, CapabilitySupport.UNSUPPORTED):
        with pytest.raises(ValueError, match="fabricate scope"):
            replace(descriptor, source_sequence=support, sequence_scope="stream")
    with pytest.raises(ValueError, match="fidelity"):
        replace(descriptor, fidelity=FidelityMode.SOURCE_SEQUENCE_FAITHFUL)
    known = replace(
        descriptor,
        source_sequence=CapabilitySupport.SUPPORTED,
        sequence_scope="provider/connection/stream",
        fidelity=FidelityMode.SOURCE_SEQUENCE_FAITHFUL,
    )
    assert known.sequence_scope == "provider/connection/stream"


@pytest.mark.parametrize("bad", [timedelta(0), timedelta(seconds=-1), None, 1.0])
def test_resolution_must_be_explicit_positive_or_missing(bad: object) -> None:
    with pytest.raises(ValueError, match="timestamp_resolution"):
        replace(capabilities(), timestamp_resolution=cast(timedelta, bad))


def test_declarations_validate_types_and_preserve_resolution() -> None:
    for reason in MissingReason:
        assert replace(capabilities(), timestamp_resolution=reason).timestamp_resolution is reason
    known = replace(
        capabilities(),
        timestamp_resolution=timedelta(milliseconds=1),
        fidelity=FidelityMode.EVENT_TIME_ONLY,
    )
    assert known.timestamp_resolution == timedelta(milliseconds=1)
    with pytest.raises(ValueError, match="CapabilitySupport"):
        replace(known, ticks=cast(CapabilitySupport, True))
    with pytest.raises(ValueError, match="FidelityMode"):
        replace(known, fidelity=cast(FidelityMode, "UNKNOWN"))


def test_metadata_protocol_fixture_has_no_concrete_feed_or_execution() -> None:
    class StaticMetadataFixture:
        def describe_capabilities(self) -> ProviderCapabilities:
            return capabilities()

    fixture: ProviderMetadata = StaticMetadataFixture()
    assert fixture.describe_capabilities() == capabilities()
    assert not hasattr(fixture, "subscribe")
    assert not hasattr(fixture, "order_send")
