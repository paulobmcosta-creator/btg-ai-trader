"""Runtime evidence for NEG-CAP-01..10 on the integrated passive S1 Observer."""

import json
import os
import sys
import tomllib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from uuid import UUID

import pytest

from btg_ai_trader.observer.admission import IngressMetadata
from btg_ai_trader.observer.composition import (
    FixtureObserver,
    ObserverConfig,
    StepResult,
    StepStatus,
)
from btg_ai_trader.observer.health import HealthSample, SafetyPosture
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
from btg_ai_trader.observer.storage_records import EvidenceRecord, TechnicalJournalRecord
from btg_ai_trader.observer.values import MissingReason

NOW = datetime(2026, 9, 13, 12, tzinfo=UTC)
REF = ProviderInstrumentRef("fixture", "capture-a", "FixtureSymbol")
INSTRUMENT = TradableInstrumentId(str(UUID(int=31)))
FAMILY = InstrumentFamilyId(str(UUID(int=32)))
CODE = CodeRevision("a" * 40)
FORBIDDEN_SURFACE = {
    "order_send", "order_check", "order_calc_margin", "submit_order", "cancel_order",
    "modify_order", "trade", "execute", "auto_flatten", "enable_auto_trading",
}
CREDENTIAL_KEYS = (
    "MT5_LOGIN", "MT5_PASSWORD", "BROKER_PASSWORD", "TRADING_API_KEY", "TRADING_TOKEN",
)


def config(**changes: object) -> ObserverConfig:
    values: dict[str, object] = {
        "provider": "fixture",
        "capture_scope": "capture-a",
        "queue_capacity": 2,
        "dedup_capacity": 10,
        "max_payload_bytes": 65536,
        "clock_scope": "clock-a",
        "heartbeat_timeout_ns": 1000,
        "market_staleness_ns": 1000,
    }
    values.update(changes)
    return ObserverConfig.from_mapping(values)


def frame(*, event_id: int = 1, payload: bytes | None = None) -> RawFrame:
    if payload is None:
        body = {
            "envelope_version": 1,
            "schema_version": 1,
            "event_id": str(UUID(int=event_id)),
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
                "ask": {"decimal": "20"},
                "last": {"missing": "UNKNOWN"},
                "volume": {"decimal": "0"},
            },
            "external_event_id": None,
            "source_sequence": None,
            "sequence_scope": None,
            "correlation_id": None,
            "causation_id": None,
        }
        payload = json.dumps(body).encode()
    return RawFrame(payload, REF, RawChannel.TICK)


def capabilities() -> ProviderCapabilities:
    return ProviderCapabilities(
        REF.provider,
        REF.scope,
        CapabilitySupport.SUPPORTED,
        CapabilitySupport.SUPPORTED,
        CapabilitySupport.UNKNOWN,
        MissingReason.UNKNOWN,
        FidelityMode.UNKNOWN,
    )


def registry() -> InstrumentRegistry:
    return InstrumentRegistry([
        InstrumentMapping(
            REF,
            INSTRUMENT,
            FAMILY,
            NOW - timedelta(days=1),
            None,
            NOW - timedelta(days=1),
            "fixture-mapping",
        )
    ])


def store(tmp_path: Path) -> tuple[TechnicalEvidenceStore, Path, Path]:
    archive = tmp_path / "archive"
    journal = tmp_path / "journal"
    archive.mkdir()
    journal.mkdir()
    return (
        TechnicalEvidenceStore(
            archive_root=archive,
            journal_root=journal,
            max_record_bytes=1_000_000,
        ),
        archive,
        journal,
    )


def observer(
    tmp_path: Path,
    frames: list[RawFrame],
    *,
    cfg: ObserverConfig | None = None,
) -> tuple[FixtureObserver, Path, Path]:
    technical_store, archive, journal = store(tmp_path)
    source = FixtureMarketDataSource(capabilities(), frames)
    instance = FixtureObserver(
        cfg or config(),
        source,
        technical_store,
        registry(),
        run_id=RunId(str(UUID(int=33))),
        code_revision=CODE,
        started_at=NOW,
    )
    return instance, archive, journal


def advance(instance: FixtureObserver, *, sample_ns: int = 0) -> StepResult:
    return instance.advance(
        IngressMetadata(NOW, MissingReason.UNKNOWN, 0),
        valid_at=NOW,
        knowledge_cutoff=NOW,
        frontier=None,
        health_sample=HealthSample(
            "clock-a", sample_ns, MissingReason.UNKNOWN, MissingReason.UNKNOWN
        ),
    )


class CallbackTripwire:
    def __init__(self) -> None:
        self.calls = 0

    def order_send(self, *_args: object, **_kwargs: object) -> None:
        self.calls += 1
        raise AssertionError("financial callback must never execute")

    def describe_capabilities(self) -> ProviderCapabilities:
        self.calls += 1
        raise AssertionError("rejected dependency must not be invoked")


class DualUseFixture(FixtureMarketDataSource):
    def __init__(self, tripwire: CallbackTripwire) -> None:
        super().__init__(capabilities(), [frame()])
        self.tripwire = tripwire

    def order_send(self) -> None:
        self.tripwire.order_send()


class LedgerShaped:
    amount = 1


# NEG-CAP-01: real observation output remains a closed passive result.
def test_neg_cap_01_observation_has_no_operational_execution_authority(tmp_path: Path) -> None:
    instance, _, _ = observer(tmp_path, [frame()])
    assert instance.start().status is StepStatus.STARTED
    result = advance(instance)
    assert type(result) is StepResult
    assert result.status is StepStatus.ADMITTED
    assert not result.pending
    assert FORBIDDEN_SURFACE.isdisjoint(dir(instance))
    assert FORBIDDEN_SURFACE.isdisjoint(dir(result))


# NEG-CAP-02: executor-shaped dependencies and subclasses fail before callbacks.
@pytest.mark.parametrize("slot", ["source", "store", "registry"])
def test_neg_cap_02_executor_shaped_dependencies_are_rejected_before_invocation(
    tmp_path: Path, slot: str
) -> None:
    technical_store, _, _ = store(tmp_path)
    passive_source = FixtureMarketDataSource(capabilities(), [frame()])
    passive_registry = registry()
    tripwire = CallbackTripwire()
    values: dict[str, object] = {
        "source": passive_source,
        "store": technical_store,
        "registry": passive_registry,
    }
    values[slot] = tripwire
    with pytest.raises(TypeError, match="passive concrete dependencies"):
        FixtureObserver(
            config(),
            cast(Any, values["source"]),
            cast(Any, values["store"]),
            cast(Any, values["registry"]),
            run_id=RunId(str(UUID(int=34))),
            code_revision=CODE,
            started_at=NOW,
        )
    assert tripwire.calls == 0


def test_neg_cap_02_dual_use_provider_subclass_is_rejected_before_use(tmp_path: Path) -> None:
    technical_store, _, _ = store(tmp_path)
    tripwire = CallbackTripwire()
    source = DualUseFixture(tripwire)
    with pytest.raises(TypeError, match="passive concrete dependencies"):
        FixtureObserver(
            config(),
            cast(Any, source),
            technical_store,
            registry(),
            run_id=RunId(str(UUID(int=35))),
            code_revision=CODE,
            started_at=NOW,
        )
    assert tripwire.calls == 0


# NEG-CAP-03: full passive path writes technical evidence only; financial sentinel is untouched.
def test_neg_cap_03_observation_path_never_touches_financial_sentinel(tmp_path: Path) -> None:
    financial = tmp_path / "financial-sentinel"
    financial.mkdir()
    instance, archive, journal = observer(tmp_path, [frame()])
    assert instance.start().status is StepStatus.STARTED
    assert advance(instance).status is StepStatus.ADMITTED
    assert list(financial.iterdir()) == []
    assert list(archive.glob("*.json"))
    assert list(journal.glob("*.json"))


# NEG-CAP-04: strict config cannot add trading authority.
@pytest.mark.parametrize("key", ["order_send", "live_trading", "auto_trade", "executor"])
def test_neg_cap_04_execution_like_configuration_keys_fail_closed(key: str) -> None:
    values: dict[str, object] = {
        "provider": "fixture",
        "capture_scope": "capture-a",
        "queue_capacity": 2,
        "dedup_capacity": 10,
        "max_payload_bytes": 65536,
        "clock_scope": "clock-a",
        "heartbeat_timeout_ns": 1000,
        "market_staleness_ns": 1000,
        key: True,
    }
    with pytest.raises(ValueError, match="exactly the passive declared fields"):
        ObserverConfig.from_mapping(values)
    assert config().provider == "fixture"


# NEG-CAP-05: synthetic trading credentials are neither required nor persisted.
def test_neg_cap_05_trading_environment_markers_do_not_change_observer_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    markers: list[bytes] = []
    for index, key in enumerate(CREDENTIAL_KEYS):
        marker = f"synthetic-never-a-secret-{index}"
        monkeypatch.setenv(key, marker)
        markers.append(marker.encode())
    instance, archive, journal = observer(tmp_path, [frame()])
    instance.start()
    advance(instance)
    persisted = b"".join(path.read_bytes() for path in (*archive.glob("*"), *journal.glob("*")))
    assert all(marker not in persisted for marker in markers)
    assert all(os.environ[key].startswith("synthetic-never-a-secret-") for key in CREDENTIAL_KEYS)


# NEG-CAP-06: the admitted provider surface is fixture/read-only only.
def test_neg_cap_06_provider_surface_has_no_execution_methods(tmp_path: Path) -> None:
    source = FixtureMarketDataSource(capabilities(), [frame()])
    assert FORBIDDEN_SURFACE.isdisjoint(dir(source))
    assert set(name for name in dir(source) if not name.startswith("_")) == {
        "describe_capabilities", "read_next"
    }
    technical_store, _, _ = store(tmp_path)
    tripwire = CallbackTripwire()
    with pytest.raises(TypeError):
        FixtureObserver(
            config(),
            cast(Any, DualUseFixture(tripwire)),
            technical_store,
            registry(),
            run_id=RunId(str(UUID(int=36))),
            code_revision=CODE,
            started_at=NOW,
        )
    assert tripwire.calls == 0


# NEG-CAP-07: SAFE_HALT remains passive and does not auto-flatten/unlatch.
def test_neg_cap_07_safe_halt_is_passive_and_remains_latched(tmp_path: Path) -> None:
    instance, _, _ = observer(tmp_path, [frame(payload=b"not-json"), frame(event_id=2)])
    instance.start()
    first = advance(instance)
    assert first.status is StepStatus.QUARANTINED
    assert first.health is not None
    assert first.health.health.posture is SafetyPosture.SAFE_HALT
    second = instance.advance(
        IngressMetadata(NOW + timedelta(seconds=1), MissingReason.UNKNOWN, 1),
        valid_at=NOW + timedelta(seconds=1),
        knowledge_cutoff=NOW + timedelta(seconds=1),
        frontier=None,
        health_sample=HealthSample(
            "clock-a", 1, MissingReason.UNKNOWN, MissingReason.UNKNOWN
        ),
    )
    assert second.health is not None
    assert second.health.health.posture is SafetyPosture.SAFE_HALT
    assert FORBIDDEN_SURFACE.isdisjoint(dir(instance))


# NEG-CAP-08: packaging declares no CLI/UI/admin trading entrypoint.
def test_neg_cap_08_packaging_has_no_runtime_command_entrypoints() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["dependencies"] == []
    assert "scripts" not in project
    assert "gui-scripts" not in project
    assert "entry-points" not in project


# NEG-CAP-09: technical storage rejects ledger-shaped values before any I/O.
def test_neg_cap_09_technical_store_rejects_ledger_shaped_values_before_io(
    tmp_path: Path
) -> None:
    technical_store, archive, journal = store(tmp_path)
    ledger = LedgerShaped()
    with pytest.raises(ValueError, match="only EvidenceRecord"):
        technical_store.append_evidence(cast(EvidenceRecord, ledger))
    with pytest.raises(ValueError, match="only TechnicalJournalRecord"):
        technical_store.append_journal(cast(TechnicalJournalRecord, ledger))
    assert list(archive.iterdir()) == []
    assert list(journal.iterdir()) == []


# NEG-CAP-10: executing S1 does not load future financial/replay modules.
def test_neg_cap_10_runtime_graph_excludes_future_execution_modules(tmp_path: Path) -> None:
    instance, _, _ = observer(tmp_path, [frame()])
    instance.start()
    advance(instance)
    forbidden_prefixes = (
        "btg_ai_trader.execution",
        "btg_ai_trader.paper",
        "btg_ai_trader.risk",
        "btg_ai_trader.strategy",
        "btg_ai_trader.research.replay",
    )
    loaded = set(sys.modules)
    assert not any(name.startswith(forbidden_prefixes) for name in loaded)
    assert FORBIDDEN_SURFACE.isdisjoint(dir(instance))
