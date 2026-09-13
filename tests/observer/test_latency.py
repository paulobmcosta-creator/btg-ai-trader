"""Monotonic transit-latency evidence for the passive S1 Observer boundary."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from btg_ai_trader.observer.admission import IngressMetadata
from btg_ai_trader.observer.composition import FixtureObserver, ObserverConfig, StepStatus
from btg_ai_trader.observer.health import (
    HealthSample,
    TransitLatencyEvidence,
    measure_transit_latency,
)
from btg_ai_trader.observer.identity import (
    InstrumentFamilyId,
    ProviderInstrumentRef,
    RunId,
    TradableInstrumentId,
)
from btg_ai_trader.observer.instruments import InstrumentMapping, InstrumentRegistry
from btg_ai_trader.observer.provenance import CodeRevision
from btg_ai_trader.observer.provider import (
    CapabilitySupport,
    FidelityMode,
    ProviderCapabilities,
)
from btg_ai_trader.observer.raw_source import FixtureMarketDataSource, RawChannel, RawFrame
from btg_ai_trader.observer.storage import TechnicalEvidenceStore
from btg_ai_trader.observer.values import MissingReason

NOW = datetime(2026, 9, 13, 12, tzinfo=UTC)
REF = ProviderInstrumentRef("fixture", "capture-a", "FixtureSymbol")
INSTRUMENT = TradableInstrumentId(str(UUID(int=71)))


def _frame() -> RawFrame:
    payload = {
        "envelope_version": 1,
        "schema_version": 1,
        "event_id": str(UUID(int=72)),
        "event_type": "TICK",
        "source": {"provider": REF.provider, "scope": REF.scope, "symbol": REF.symbol},
        "instrument_id": {"uuid": INSTRUMENT.value},
        "event_time": {
            "value": {"utc": "2026-09-13T11:59:59.000000Z"},
            "basis": {"text": "source"},
            "resolution_us": 1,
        },
        "effective_time": {"missing": "UNKNOWN"},
        "payload": {
            "bid": {"decimal": "10"},
            "ask": {"decimal": "11"},
            "last": {"missing": "UNKNOWN"},
            "volume": {"decimal": "0"},
        },
        "external_event_id": None,
        "source_sequence": None,
        "sequence_scope": None,
        "correlation_id": None,
        "causation_id": None,
    }
    return RawFrame(json.dumps(payload).encode(), REF, RawChannel.TICK)


def _observer(tmp_path: Path) -> FixtureObserver:
    archive = tmp_path / "archive"
    journal = tmp_path / "journal"
    archive.mkdir()
    journal.mkdir()
    source = FixtureMarketDataSource(
        ProviderCapabilities(
            REF.provider,
            REF.scope,
            CapabilitySupport.SUPPORTED,
            CapabilitySupport.SUPPORTED,
            CapabilitySupport.UNKNOWN,
            MissingReason.UNKNOWN,
            FidelityMode.UNKNOWN,
        ),
        [_frame()],
    )
    registry = InstrumentRegistry([
        InstrumentMapping(
            REF,
            INSTRUMENT,
            InstrumentFamilyId(str(UUID(int=73))),
            NOW - timedelta(days=1),
            None,
            NOW - timedelta(days=1),
            "fixture-mapping",
        )
    ])
    store = TechnicalEvidenceStore(
        archive_root=archive,
        journal_root=journal,
        max_record_bytes=1_000_000,
    )
    config = ObserverConfig.from_mapping({
        "provider": "fixture",
        "capture_scope": "capture-a",
        "queue_capacity": 2,
        "dedup_capacity": 10,
        "max_payload_bytes": 65536,
        "clock_scope": "clock-a",
        "heartbeat_timeout_ns": 1000,
        "market_staleness_ns": 1000,
    })
    return FixtureObserver(
        config,
        source,
        store,
        registry,
        run_id=RunId(str(UUID(int=74))),
        code_revision=CodeRevision("a" * 40),
        started_at=NOW,
    )


def test_measure_transit_latency_is_explicit_same_scope_evidence() -> None:
    evidence = measure_transit_latency("clock-a", ingress_ns=125, available_ns=180)
    assert evidence == TransitLatencyEvidence("clock-a", 125, 180, 55)


def test_transit_latency_rejects_backward_or_inconsistent_monotonic_evidence() -> None:
    with pytest.raises(ValueError, match="cannot move backward"):
        measure_transit_latency("clock-a", ingress_ns=181, available_ns=180)
    with pytest.raises(ValueError, match="must equal"):
        TransitLatencyEvidence("clock-a", 125, 180, 54)


def test_latency_measurement_pairs_with_real_fixture_observer_boundary(tmp_path: Path) -> None:
    observer = _observer(tmp_path)
    assert observer.start().status is StepStatus.STARTED

    # Adapter/owner readings are explicit values from one monotonic clock scope. The event's
    # wall-clock timestamp is deliberately unrelated and is never used to derive this metric.
    ingress_ns = 1_000
    sample = HealthSample("clock-a", 1_075, 1_050, 1_060)
    latency = measure_transit_latency(sample.clock_scope, ingress_ns, sample.now_ns)

    result = observer.advance(
        IngressMetadata(NOW, MissingReason.UNKNOWN, 0),
        valid_at=NOW,
        knowledge_cutoff=NOW,
        frontier=None,
        health_sample=sample,
    )

    assert result.status is StepStatus.ADMITTED
    assert latency.clock_scope == observer.config.clock_scope
    assert latency.latency_ns == 75
    assert result.health is not None
    assert result.health.health.sample == sample
