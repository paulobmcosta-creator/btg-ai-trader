"""Integrated passive fixtures on controlled temporary CI storage."""

import json
import os
import subprocess
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

from btg_ai_trader.observer.admission import IngressMetadata
from btg_ai_trader.observer.composition import (
    FixtureObserver,
    FrontierAvailability,
    ObserverConfig,
    StepStatus,
)
from btg_ai_trader.observer.dedup import LateStatus
from btg_ai_trader.observer.envelope import EventType
from btg_ai_trader.observer.health import HealthSample, ReadinessStatus, SafetyPosture
from btg_ai_trader.observer.identity import (
    ArtifactId,
    InstrumentFamilyId,
    ProviderInstrumentRef,
    RunId,
    TradableInstrumentId,
)
from btg_ai_trader.observer.instruments import InstrumentMapping, InstrumentRegistry
from btg_ai_trader.observer.market import Candle, CandleFinality
from btg_ai_trader.observer.provenance import CodeRevision, InputIdentity
from btg_ai_trader.observer.provider import (
    CapabilitySupport,
    FidelityMode,
    ProviderCapabilities,
)
from btg_ai_trader.observer.raw_source import FixtureMarketDataSource, RawChannel, RawFrame
from btg_ai_trader.observer.storage import TechnicalEvidenceStore
from btg_ai_trader.observer.storage_records import EvidenceRecord, content_hash, decode_record
from btg_ai_trader.observer.values import MissingReason

NOW = datetime(2026, 9, 13, 12, tzinfo=UTC)
REF = ProviderInstrumentRef("fixture", "capture-a", "FixtureSymbol")
INSTRUMENT = TradableInstrumentId(str(UUID(int=11)))


def config(**changes: object) -> ObserverConfig:
    values: dict[str, object] = {
        "provider": "fixture", "capture_scope": "capture-a", "queue_capacity": 2,
        "dedup_capacity": 10, "max_payload_bytes": 65536, "clock_scope": "clock-a",
        "heartbeat_timeout_ns": 1000, "market_staleness_ns": 1000,
    }
    values.update(changes)
    return ObserverConfig.from_mapping(values)


def frame(number: int = 1, bid: str = "10") -> RawFrame:
    data = {
        "envelope_version": 1, "schema_version": 1,
        "event_id": str(UUID(int=number)), "event_type": "TICK",
        "source": {"provider": REF.provider, "scope": REF.scope, "symbol": REF.symbol},
        "instrument_id": {"uuid": INSTRUMENT.value},
        "event_time": {
            "value": {"utc": "2026-09-13T12:00:00.000000Z"},
            "basis": {"text": "source"}, "resolution_us": 1,
        },
        "effective_time": {"missing": "UNKNOWN"},
        "payload": {
            "bid": {"decimal": bid}, "ask": {"decimal": "20"},
            "last": {"missing": "UNKNOWN"}, "volume": {"decimal": "0"},
        },
        "external_event_id": None, "source_sequence": None, "sequence_scope": None,
        "correlation_id": None, "causation_id": None,
    }
    return RawFrame(json.dumps(data).encode(), REF, RawChannel.TICK)


def make(
    tmp_path: Path, frames: list[RawFrame], *, cfg: ObserverConfig | None = None,
    registry: InstrumentRegistry | None = None,
) -> tuple[FixtureObserver, FixtureMarketDataSource, Path, Path]:
    archive, journal = tmp_path / "archive", tmp_path / "journal"
    archive.mkdir()
    journal.mkdir()
    descriptor = ProviderCapabilities(
        REF.provider, REF.scope, CapabilitySupport.SUPPORTED, CapabilitySupport.SUPPORTED,
        CapabilitySupport.UNKNOWN, MissingReason.UNKNOWN, FidelityMode.UNKNOWN,
    )
    source = FixtureMarketDataSource(descriptor, frames)
    store = TechnicalEvidenceStore(
        archive_root=archive, journal_root=journal, max_record_bytes=1000000
    )
    if registry is None:
        registry = InstrumentRegistry([InstrumentMapping(
            REF, INSTRUMENT, InstrumentFamilyId(str(UUID(int=12))),
            NOW - timedelta(days=1), None, NOW - timedelta(days=1), "fixture-mapping",
        )])
    # Test harness only: runtime never shells out or inspects the user's checkout.
    actual_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    declared = (
        (InputIdentity(ArtifactId(str(UUID(int=20))), content_hash(frames[0].payload)),)
        if frames else ()
    )
    observer = FixtureObserver(
        cfg or config(), source, store, registry,
        run_id=RunId(str(UUID(int=21))), code_revision=CodeRevision(actual_sha),
        started_at=NOW, inputs=declared,
    )
    return observer, source, archive, journal


def advance(observer: FixtureObserver, index: int = 0, **changes: Any) -> Any:
    stamp = NOW + timedelta(seconds=index)
    arguments: dict[str, Any] = {
        "valid_at": stamp, "knowledge_cutoff": stamp, "frontier": None,
        "health_sample": HealthSample("clock-a", index, MissingReason.UNKNOWN,
                                      MissingReason.UNKNOWN),
    }
    arguments.update(changes)
    return observer.advance(IngressMetadata(stamp, MissingReason.UNKNOWN, index), **arguments)


def records(root: Path) -> list[EvidenceRecord]:
    output = [decode_record(path.read_bytes()) for path in root.glob("*.json")]
    return [item for item in output if isinstance(item, EvidenceRecord)]


def test_manifest_configuration_actual_code_pin_and_read_after_start(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raw = frame()
    observer, _, archive, journal = make(tmp_path, [raw])
    with pytest.raises(ValueError, match="start"):
        advance(observer)
    assert not list(archive.iterdir())
    assert observer.start().status is StepStatus.STARTED
    manifest = records(archive)[0]
    body = json.loads(manifest.raw)
    assert manifest == observer.manifest_record
    assert body["manifest"]["code_revision"]["value"] == observer.manifest.code_revision.value
    assert body["manifest"]["inputs"][0]["content_hash"]["value"] == content_hash(raw.payload).value
    assert (
        content_hash(observer.config.canonical_bytes()).value == observer.manifest.config_hash.value
    )
    assert body["effective_config"]["queue_capacity"] == 2
    assert len(list(journal.glob("*.json"))) == 1
    result = advance(observer)
    assert result.status is StepStatus.ADMITTED and not result.pending
    assert result.raw is raw and observer.queue.items[0] is result.decision.admission.envelope
    assert result.health.health.readiness is ReadinessStatus.NOT_READY
    assert result.health.health.posture is SafetyPosture.DEGRADED
    persisted = records(archive)
    assert any(record.raw == raw.payload for record in persisted)
    assert len(persisted) == 3
    decision = next(item for item in persisted if b"fixture-observation-decision-plan" in item.raw)
    encoded = json.loads(decision.raw)
    assert encoded["health_before_queue_commit"]["health"]["readiness"]["value"] == "NOT_READY"
    assert encoded["health_before_queue_commit"]["health"]["sample"]["clock_scope"] == "clock-a"
    assert encoded["health_after_planned_queue_commit"]["queue"]["depth"] == 1
    assert encoded["registry"]["matches"][0]["family_id"]["value"] == str(UUID(int=12))
    assert encoded["processing_completion_time"] == {"missing": "UNKNOWN"}
    assert encoded["derived_availability"] == {"missing": "UNKNOWN"}
    assert result.decision_receipt.record_id == decision.record_id
    with capsys.disabled():
        print("OBSERVER_CODE_SHA=" + observer.manifest.code_revision.value)
        print("OBSERVER_CONFIG_SHA256=" + observer.manifest.config_hash.value)
        print("OBSERVER_MANIFEST_SHA256=" + manifest.input_identity.content_hash.value)
        print("OBSERVER_FRAME_DISPOSITION=" + result.status.value)


def test_corrupt_quarantine_is_logically_separate_then_valid_feed_continues(tmp_path: Path) -> None:
    corrupt = replace(frame(), payload=b"\xff\x00corrupt")
    good = frame(2)
    observer, _, archive, _ = make(tmp_path, [corrupt, good])
    observer.start()
    rejected = advance(observer)
    assert rejected.status is StepStatus.QUARANTINED and rejected.raw is corrupt
    assert observer.queue.items == ()
    stored = records(archive)
    assert any(item.raw == corrupt.payload for item in stored)
    decision = json.loads(next(
        item.raw for item in stored if b"fixture-observation-decision-plan" in item.raw
    ))
    assert decision["rejection"] == {"reason": "UTF8", "field": "$"}
    assert decision["envelope"] is None
    accepted = advance(observer, 1)
    assert accepted.status is StepStatus.ADMITTED and accepted.raw is good
    assert len(observer.queue.items) == 1
    assert accepted.health.health.posture is SafetyPosture.SAFE_HALT
    assert advance(observer, 2).status is StepStatus.EXHAUSTED
    assert advance(observer, 3).health.health.readiness is ReadinessStatus.NOT_READY


def test_backpressure_drain_retry_does_not_commit_dedup_or_lose_frame(tmp_path: Path) -> None:
    first, second = frame(), frame(2)
    observer, _, _, _ = make(tmp_path, [first, second], cfg=config(queue_capacity=1))
    observer.start()
    assert advance(observer).status is StepStatus.ADMITTED
    blocked = advance(observer, 1)
    assert blocked.status is StepStatus.BACKPRESSURE and observer.pending_raw is second
    with pytest.raises(ValueError, match="pending"):
        advance(observer, 2)
    assert observer.retry_pending().status is StepStatus.BACKPRESSURE
    assert observer.queue.snapshot.backpressure_count == 1
    first_taken = observer.take().item
    assert first_taken is not None and first_taken.event_id.value == str(UUID(int=1))
    accepted = observer.retry_pending()
    assert accepted.status is StepStatus.ADMITTED and accepted.raw is second
    assert len(observer.queue.items) == 1
    second_taken = observer.take().item
    assert second_taken is not None and second_taken.event_id.value == str(UUID(int=2))
    assert observer.pending_raw is None


def test_duplicate_conflict_and_late_unknown_keep_both_evidences(tmp_path: Path) -> None:
    original, duplicate, conflict = frame(), frame(), frame(1, bid="11")
    observer, _, archive, _ = make(tmp_path, [original, duplicate, conflict])
    observer.start()
    first = advance(observer)
    frontier = first.decision.admission.envelope
    unknown = replace(frontier, instrument_id=MissingReason.UNKNOWN)
    second = advance(observer, 1, frontier=unknown)
    assert second.status is StepStatus.DUPLICATE
    assert second.decision.dedup.canonical is frontier
    assert second.decision.dedup.incoming is not frontier
    assert second.decision.late.status is LateStatus.UNKNOWN
    third = advance(observer, 2, frontier=frontier)
    assert third.status is StepStatus.IDENTITY_CONFLICT
    assert len(observer.queue.items) == 1
    assert len(records(archive)) == 7


@pytest.mark.parametrize("missing_time", [False, True])
def test_unresolved_registry_or_unknown_valid_time_never_enters_queue(
    tmp_path: Path, missing_time: bool
) -> None:
    registry = None if missing_time else InstrumentRegistry([])
    observer, _, _, _ = make(tmp_path, [frame()], registry=registry)
    observer.start()
    result = advance(observer, valid_at=MissingReason.UNKNOWN if missing_time else NOW)
    assert result.status is StepStatus.REGISTRY_UNRESOLVED
    assert observer.queue.items == ()
    assert result.health.health.readiness is ReadinessStatus.NOT_READY
    assert result.decision.admission.envelope.instrument_id == INSTRUMENT


def test_dedup_capacity_keeps_pending_without_eviction(tmp_path: Path) -> None:
    observer, _, _, _ = make(tmp_path, [frame(), frame(2)], cfg=config(dedup_capacity=1))
    observer.start()
    advance(observer)
    blocked = advance(observer, 1)
    assert blocked.status is StepStatus.DEDUP_FULL and blocked.pending
    assert observer.retry_pending().status is StepStatus.DEDUP_FULL
    with pytest.raises(ValueError):
        observer.take()
    assert len(observer.queue.items) == 1


@pytest.mark.parametrize("fail_at", [1, 2, 3])
def test_raw_decision_journal_failure_retries_same_pending_and_applies_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fail_at: int
) -> None:
    raw = frame()
    observer, _, archive, journal = make(tmp_path, [raw, frame(2)])
    observer.start()
    original_link = os.link
    calls = 0

    def fail_link(*args: Any, **kwargs: Any) -> None:
        nonlocal calls
        calls += 1
        if calls == fail_at:
            raise OSError("fixture write failure")
        original_link(*args, **kwargs)

    monkeypatch.setattr(os, "link", fail_link)
    result = advance(observer)
    assert result.status is StepStatus.STORAGE_BLOCKED and observer.pending_raw is raw
    assert observer.queue.items == ()
    assert observer.health is not None
    assert observer.health.health.posture is SafetyPosture.SAFE_HALT
    with pytest.raises(ValueError):
        advance(observer, 1)
    with pytest.raises(ValueError):
        observer.take()
    monkeypatch.setattr(os, "link", original_link)
    complete = observer.retry_pending()
    assert complete.status is StepStatus.ADMITTED and complete.raw is raw
    assert len(observer.queue.items) == 1
    assert len(records(archive)) == 3
    assert len(list(journal.glob("*.json"))) == 2
    assert observer.health is not None
    assert observer.health.health.posture is SafetyPosture.SAFE_HALT
    assert advance(observer, 1).raw.payload == frame(2).payload


def test_published_uncertain_raw_is_resolved_without_new_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observer, _, archive, _ = make(tmp_path, [frame()])
    observer.start()
    original_link = os.link

    def link_then_fail(*args: Any, **kwargs: Any) -> None:
        original_link(*args, **kwargs)
        raise OSError("simulated result uncertainty")

    monkeypatch.setattr(os, "link", link_then_fail)
    assert advance(observer).status is StepStatus.STORAGE_BLOCKED
    published = {path.name for path in archive.glob("*.json")}
    assert len(published) == 2
    monkeypatch.setattr(os, "link", original_link)
    result = observer.retry_pending()
    assert result.status is StepStatus.ADMITTED
    assert published <= {path.name for path in archive.glob("*.json")}
    assert len(records(archive)) == 3


def test_start_failure_blocks_first_read_and_invalid_context_does_not_consume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = frame()
    observer, source, _, _ = make(tmp_path, [raw])
    original_link = os.link

    def failure(*args: Any, **kwargs: Any) -> None:
        raise OSError("manifest failure")

    monkeypatch.setattr(os, "link", failure)
    assert observer.start().status is StepStatus.STORAGE_BLOCKED
    with pytest.raises(ValueError):
        advance(observer)
    monkeypatch.setattr(os, "link", original_link)
    assert observer.retry_pending().status is StepStatus.STARTED
    with pytest.raises(ValueError):
        advance(observer, knowledge_cutoff=NOW + timedelta(seconds=1))
    with pytest.raises(ValueError):
        advance(observer, health_sample=HealthSample("other", 0, 0, 0))
    assert observer.pending_raw is None
    assert source.read_next() is raw


@pytest.mark.parametrize("field", ["executor", "credentials", "trading_enabled", "unknown"])
def test_config_unknown_fields_are_rejected(field: str) -> None:
    with pytest.raises(ValueError, match="exactly"):
        config(**{field: "forbidden"})
    with pytest.raises(ValueError):
        config(queue_capacity=True)


def test_dependency_ducktypes_rejected_before_method_invocation() -> None:
    class Bomb:
        def __getattr__(self, name: str) -> object:
            raise AssertionError("dependency was invoked")

    bomb: Any = Bomb()
    with pytest.raises(TypeError, match="exact"):
        FixtureObserver(
            config(), bomb, bomb, bomb, run_id=RunId(str(UUID(int=1))),
            code_revision=CodeRevision("a" * 40), started_at=NOW,
        )


def test_candle_ancestral_availability_sidecars_and_readonly_config(tmp_path: Path) -> None:
    tick = frame()
    data = json.loads(tick.payload)
    data["event_type"] = "CANDLE"
    data["payload"] = {
        "interval_start": {"utc": "2026-09-13T11:59:00.000000Z"},
        "interval_end": {"utc": "2026-09-13T12:00:00.000000Z"},
        "finality": "UNKNOWN", "finalized_at": {"missing": "UNKNOWN"},
        "available_at": {"missing": "UNKNOWN"},
        "open": {"decimal": "10"}, "high": {"decimal": "12"},
        "low": {"decimal": "9"}, "close": {"decimal": "11"},
        "volume": {"missing": "NOT_PROVIDED"},
    }
    candle = RawFrame(json.dumps(data).encode(), REF, RawChannel.CANDLE)
    observer, _, archive, _ = make(tmp_path, [candle])
    observer.start()
    with pytest.raises(AttributeError):
        observer.config = config(queue_capacity=99)  # type: ignore[misc]
    result = advance(observer)
    assert result.status is StepStatus.ADMITTED and result.raw is candle
    decision = json.loads(next(
        item.raw for item in records(archive) if b"fixture-observation-decision-plan" in item.raw
    ))
    assert decision["envelope"]["payload"]["available_at"]["value"] == "UNKNOWN"
    assert decision["envelope"]["times"]["knowledge_time"]["value"] == "UNKNOWN"
    assert decision["derived_availability"] == {"missing": "UNKNOWN"}


@pytest.mark.parametrize("axis", ["ingestion", "knowledge"])
def test_frontier_known_in_future_rejected_before_read(tmp_path: Path, axis: str) -> None:
    observer, _, _, _ = make(tmp_path, [frame(), frame(2)])
    observer.start()
    first = advance(observer)
    original = first.decision.admission.envelope
    future = NOW + timedelta(seconds=2)
    if axis == "ingestion":
        times = replace(original.times, ingestion_time=future, knowledge_time=MissingReason.UNKNOWN)
    else:
        times = replace(original.times, knowledge_time=future)
    frontier = replace(original, times=times)
    with pytest.raises(ValueError, match="frontier availability"):
        advance(observer, 1, frontier=frontier)
    assert observer.pending_raw is None
    result = advance(observer, 1, frontier=original)
    assert result.raw.payload == frame(2).payload
    assert result.decision.frontier_availability is FrontierAvailability.UNKNOWN
    assert result.decision.late.status is LateStatus.UNKNOWN


def test_known_frontier_has_explicit_availability_sidecar(tmp_path: Path) -> None:
    observer, _, archive, _ = make(tmp_path, [frame(), frame(2)])
    observer.start()
    first = advance(observer)
    original = first.decision.admission.envelope
    frontier = replace(original, times=replace(original.times, knowledge_time=NOW))
    result = advance(observer, 1, frontier=frontier)
    assert result.decision.frontier_availability is FrontierAvailability.KNOWN_AT_CUTOFF
    assert result.decision.late.status is LateStatus.ON_OR_AFTER_FRONTIER
    decision = json.loads(next(
        item.raw for item in records(archive)
        if b'"frontier_availability":"KNOWN_AT_CUTOFF"' in item.raw
    ))
    assert decision["derived_availability"] == {"missing": "UNKNOWN"}
    assert decision["late"]["frontier"]["times"]["knowledge_time"]["utc"].startswith("2026-09-13")


def test_frontier_candle_availability_does_not_derive_from_event_time(tmp_path: Path) -> None:
    observer, _, _, _ = make(tmp_path, [frame(), frame(2)])
    observer.start()
    first = advance(observer).decision.admission.envelope
    missing = MissingReason.UNKNOWN
    candle = Candle(
        NOW - timedelta(minutes=1), NOW, CandleFinality.FINAL, NOW,
        NOW + timedelta(seconds=2), missing, missing, missing, missing, missing,
    )
    frontier = replace(
        first, event_type=EventType.CANDLE, payload=candle,
        times=replace(first.times, knowledge_time=NOW),
    )
    with pytest.raises(ValueError, match="frontier availability"):
        advance(observer, 1, frontier=frontier)
    unknown = replace(frontier, payload=replace(candle, available_at=missing))
    result = advance(observer, 1, frontier=unknown)
    assert result.decision.frontier_availability is FrontierAvailability.UNKNOWN
    assert result.decision.late.status is LateStatus.UNKNOWN
