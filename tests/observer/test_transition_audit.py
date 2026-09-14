"""Integrated audit evidence for operational health transitions in Sprint 1."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from btg_ai_trader.observer.admission import IngressMetadata
from btg_ai_trader.observer.composition import FixtureObserver, ObserverConfig, StepStatus
from btg_ai_trader.observer.health import HealthSample
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
from btg_ai_trader.observer.storage_records import (
    EvidenceRecord,
    TechnicalEventKind,
    TechnicalJournalRecord,
    decode_record,
)
from btg_ai_trader.observer.values import MissingReason

NOW = datetime(2026, 9, 13, 12, tzinfo=UTC)
REF = ProviderInstrumentRef("fixture", "audit-scope", "FixtureSymbol")
INSTRUMENT = TradableInstrumentId(str(UUID(int=81)))


def _frame(number: int) -> RawFrame:
    payload = {
        "envelope_version": 1,
        "schema_version": 1,
        "event_id": str(UUID(int=number)),
        "event_type": "TICK",
        "source": {"provider": REF.provider, "scope": REF.scope, "symbol": REF.symbol},
        "instrument_id": {"uuid": INSTRUMENT.value},
        "event_time": {
            "value": {"utc": "2026-09-13T12:00:00.000000Z"},
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


def _observer(tmp_path: Path) -> tuple[FixtureObserver, Path, Path]:
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
            CapabilitySupport.UNSUPPORTED,
            timedelta(microseconds=1),
            FidelityMode.OBSERVATION_FAITHFUL,
        ),
        [_frame(82), _frame(83)],
    )
    registry = InstrumentRegistry([
        InstrumentMapping(
            REF,
            INSTRUMENT,
            InstrumentFamilyId(str(UUID(int=84))),
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
        "capture_scope": "audit-scope",
        "queue_capacity": 2,
        "dedup_capacity": 10,
        "max_payload_bytes": 65536,
        "clock_scope": "audit-clock",
        "heartbeat_timeout_ns": 100,
        "market_staleness_ns": 100,
    })
    observer = FixtureObserver(
        config,
        source,
        store,
        registry,
        run_id=RunId(str(UUID(int=85))),
        code_revision=CodeRevision("a" * 40),
        started_at=NOW,
    )
    return observer, archive, journal


def _advance(observer: FixtureObserver, *, index: int, sample: HealthSample) -> StepStatus:
    stamp = NOW + timedelta(seconds=index)
    result = observer.advance(
        IngressMetadata(stamp, MissingReason.UNKNOWN, index),
        valid_at=stamp,
        knowledge_cutoff=stamp,
        frontier=None,
        health_sample=sample,
    )
    assert result.health is not None
    return result.status


def _decoded(root: Path) -> list[EvidenceRecord | TechnicalJournalRecord]:
    return [decode_record(path.read_bytes()) for path in root.glob("*.json")]


def test_health_transition_is_observable_and_persisted_with_journal_reference(
    tmp_path: Path,
) -> None:
    observer, archive, journal = _observer(tmp_path)
    assert observer.start().status is StepStatus.STARTED

    fresh = HealthSample("audit-clock", 10, 10, 10)
    assert _advance(observer, index=0, sample=fresh) is StepStatus.ADMITTED
    observer.take()

    stale = HealthSample("audit-clock", 250, 100, 100)
    assert _advance(observer, index=1, sample=stale) is StepStatus.ADMITTED

    evidence = [item for item in _decoded(archive) if isinstance(item, EvidenceRecord)]
    decoded_decisions = [
        (item, json.loads(item.raw))
        for item in evidence
        if b"fixture-observation-decision-plan" in item.raw
    ]
    assert len(decoded_decisions) == 2
    transitions = [
        (item, body)
        for item, body in decoded_decisions
        if body["health_previous_observation"] is not None
    ]
    assert len(transitions) == 1
    transition_record, body = transitions[0]

    previous = body["health_previous_observation"]["health"]
    current = body["health_before_queue_commit"]["health"]
    assert previous["readiness"]["value"] == "READY"
    assert previous["posture"]["value"] == "NORMAL"
    assert current["readiness"]["value"] == "NOT_READY"
    assert current["posture"]["value"] == "DEGRADED"
    assert "HEARTBEAT_TIMEOUT" in {item["value"] for item in current["reasons"]}
    assert "MARKET_DATA_STALE" in {item["value"] for item in current["reasons"]}

    journals = [
        item for item in _decoded(journal) if isinstance(item, TechnicalJournalRecord)
    ]
    linked = [
        item
        for item in journals
        if item.kind is TechnicalEventKind.OBSERVATION_RECORDED
        and item.evidence_ref == transition_record.record_id
    ]
    assert len(linked) == 1
    assert linked[0].run_id == observer.manifest.run_id
