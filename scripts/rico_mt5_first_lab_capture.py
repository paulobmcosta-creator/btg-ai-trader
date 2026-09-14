"""Controlled local evidence harness for the Rico/MT5 read-only Sprint 1 bridge.

The harness never connects to MetaTrader, a broker account or an order surface. It only
consumes append-only files emitted by the reviewed custom indicator, preserves bounded
raw prefixes, and records local provenance, health and monotonic ingestion evidence.
"""

import argparse
import hashlib
import json
import re
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from btg_ai_trader.observer.health import (
    HealthAssessment,
    HealthPolicy,
    HealthSample,
    ReadinessStatus,
    RuntimePhase,
    SafetyPosture,
    evaluate_health,
    measure_transit_latency,
)
from btg_ai_trader.observer.identity import EventId
from btg_ai_trader.observer.provenance import (
    CaptureContext,
    CodeRevision,
    ConfigHash,
    InputIdentity,
    ProvenanceLabel,
    start_run,
)
from btg_ai_trader.observer.raw_source import RawChannel, RawFrame
from btg_ai_trader.observer.rico_mt5_bridge import (
    RICO_MT5_PROVIDER,
    RicoMt5BridgeReader,
    RicoMt5BridgeSettings,
)
from btg_ai_trader.observer.rico_mt5_discovery import (
    RicoMt5DiscoveryReader,
    RicoMt5DiscoverySettings,
)
from btg_ai_trader.observer.storage import TechnicalEvidenceStore
from btg_ai_trader.observer.storage_records import (
    EvidenceRecord,
    PersistenceRecordId,
    TechnicalEventKind,
    TechnicalJournalRecord,
    content_hash,
)
from btg_ai_trader.observer.values import MissingReason, require_text

WIN_CONTRACT = re.compile(r"^WIN[A-Z][0-9]{2}$")
PROVIDER_LABEL = ProvenanceLabel(RICO_MT5_PROVIDER)
MIN_CAPTURE_SECONDS = 60.0
MAX_CAPTURE_SECONDS = 300.0
MAX_DISCOVERY_SECONDS = 30.0
MAX_CHANNEL_BYTES = 24_000_000
MAX_METADATA_BYTES = 24_000_000
STORE_MAX_RECORD_BYTES = 64_000_000
MAX_DRAIN_PER_CHANNEL = 4096
MIN_TICK_FRAMES = 2
MIN_CANDLE_FRAMES = 1


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _positive_int(value: object, field: str) -> int:
    if type(value) is not int or value <= 0:
        raise RuntimeError(f"{field} must be a positive integer")
    return value


def _bounded_append(target: bytearray, payload: bytes, *, limit: int, label: str) -> None:
    if len(target) + len(payload) > limit:
        raise RuntimeError(f"{label} exceeded the controlled evidence byte bound")
    target.extend(payload)


def _validate_transport_path(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("transport path must be pathlib.Path")
    absolute = path.absolute()
    parent = absolute.parent
    if any(part.is_symlink() for part in (parent, *parent.parents)):
        raise ValueError("transport parent and ancestors must not be symlinks")
    controlled_parent = parent.resolve(strict=True)
    if not controlled_parent.is_dir():
        raise ValueError("transport parent must be an existing directory")
    candidate = controlled_parent / absolute.name
    if candidate.exists():
        if candidate.is_symlink() or not candidate.is_file():
            raise ValueError("transport path must be absent or a regular file")
        if candidate.stat().st_size != 0:
            raise ValueError("transport file must be absent or empty at session start")
    return candidate


def _validated_transport_paths(
    discovery_file: Path, tick_file: Path, candle_file: Path
) -> tuple[Path, Path, Path]:
    paths = tuple(
        _validate_transport_path(path) for path in (discovery_file, tick_file, candle_file)
    )
    if len(set(paths)) != 3:
        raise ValueError("discovery, tick and candle transport paths must be distinct")
    if len({path.parent for path in paths}) != 1:
        raise ValueError("all transport files must use one explicit session directory")
    return paths


def _read_exact_prefix(path: Path, byte_count: int) -> bytes:
    if type(byte_count) is not int or byte_count < 0:
        raise ValueError("byte_count must be a non-negative integer")
    with path.open("rb") as source:
        data = source.read(byte_count)
    if len(data) != byte_count:
        raise RuntimeError("transport prefix changed before evidence preservation")
    return data


def _new_store(output_root: Path) -> tuple[TechnicalEvidenceStore, Path]:
    if not isinstance(output_root, Path):
        raise TypeError("output_root must be pathlib.Path")
    absolute = output_root.absolute()
    if any(part.is_symlink() for part in (absolute, *absolute.parents)):
        raise ValueError("output root and ancestors must not be symlinks")
    root = absolute.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("output root must be an existing directory")
    session_root = root / ("rico-mt5-s1-first-lab-" + str(uuid4()))
    session_root.mkdir()
    archive = session_root / "archive"
    journal = session_root / "journal"
    archive.mkdir()
    journal.mkdir()
    return (
        TechnicalEvidenceStore(
            archive_root=archive,
            journal_root=journal,
            max_record_bytes=STORE_MAX_RECORD_BYTES,
        ),
        session_root,
    )


class SessionEvidence:
    """Bounded append-only technical evidence for one local Rico qualification run."""

    def __init__(
        self,
        store: TechnicalEvidenceStore,
        *,
        code_revision: CodeRevision,
        config: dict[str, object],
        started_at: datetime,
    ) -> None:
        config_bytes = _canonical_json(config)
        config_hash = ConfigHash(hashlib.sha256(config_bytes).hexdigest())
        manifest = start_run(
            started_at=started_at,
            code_revision=code_revision,
            config_hash=config_hash,
            inputs=(),
        )
        self._store = store
        self._context = CaptureContext.from_manifest(manifest, PROVIDER_LABEL)
        self._run_id = manifest.run_id.value
        plan = _canonical_json(
            {
                "schema": 1,
                "run_id": self._run_id,
                "started_at": started_at.isoformat(timespec="microseconds"),
                "code_revision": code_revision.value,
                "config_hash": config_hash.value,
                "config": config,
            }
        )
        self.record(plan, "rico-session-plan", started_at, TechnicalEventKind.STARTED)

    @property
    def run_id(self) -> str:
        return self._run_id

    def record(
        self,
        raw: bytes,
        detail: str,
        observed_at: datetime,
        kind: TechnicalEventKind = TechnicalEventKind.OBSERVATION_RECORDED,
    ) -> PersistenceRecordId:
        evidence_id = PersistenceRecordId(str(uuid4()))
        identity = InputIdentity(EventId(str(uuid4())), content_hash(raw))
        self._store.append_evidence(
            EvidenceRecord(
                evidence_id,
                identity,
                observed_at,
                raw,
                self._context,
            )
        )
        self._store.append_journal(
            TechnicalJournalRecord(
                PersistenceRecordId(str(uuid4())),
                self._context.run_id,
                observed_at,
                kind,
                ProvenanceLabel(detail),
                evidence_id,
            )
        )
        return evidence_id

    def stop(self, observed_at: datetime) -> None:
        self._store.append_journal(
            TechnicalJournalRecord(
                PersistenceRecordId(str(uuid4())),
                self._context.run_id,
                observed_at,
                TechnicalEventKind.STOPPED,
                ProvenanceLabel("rico-first-lab-stopped"),
            )
        )


def _config(
    *,
    instrument: str,
    capture_scope: str,
    clock_scope: str,
    discovery_timeout_seconds: float,
    capture_seconds: float,
    poll_interval_ms: int,
    heartbeat_timeout_ms: int,
    market_staleness_ms: int,
) -> dict[str, object]:
    return {
        "provider": RICO_MT5_PROVIDER,
        "instrument_family": "WIN",
        "instrument": instrument,
        "capture_scope": capture_scope,
        "clock_scope": clock_scope,
        "discovery_timeout_seconds": discovery_timeout_seconds,
        "capture_seconds": capture_seconds,
        "poll_interval_ms": poll_interval_ms,
        "heartbeat_timeout_ms": heartbeat_timeout_ms,
        "market_staleness_ms": market_staleness_ms,
        "transport": "append-only-file-common",
        "auto_rollover": False,
        "auto_contract_selection": False,
        "economic_authority": "none",
    }


def _parse_market_object(frame: RawFrame, instrument: str) -> dict[str, object]:
    try:
        value = json.loads(frame.payload.decode("ascii"))
    except ValueError as exc:
        raise RuntimeError("market bridge record is not canonical ASCII JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError("market bridge record must be a JSON object")
    if value.get("schema") != 1:
        raise RuntimeError("market bridge schema mismatch")
    if value.get("provider") != RICO_MT5_PROVIDER or value.get("symbol") != instrument:
        raise RuntimeError("market bridge provider/symbol differs from qualified session")
    return value


def _validate_tick(frame: RawFrame, instrument: str, expected_sequence: int) -> int:
    if frame.channel is not RawChannel.TICK:
        raise RuntimeError("tick reader emitted the wrong channel")
    value = _parse_market_object(frame, instrument)
    sequence = _positive_int(value.get("bridge_sequence"), "tick bridge_sequence")
    _positive_int(value.get("time_msc"), "tick time_msc")
    if sequence != expected_sequence:
        raise RuntimeError("tick bridge sequence is not contiguous from one")
    return sequence


def _validate_candle(frame: RawFrame, instrument: str, expected_sequence: int) -> int:
    if frame.channel is not RawChannel.CANDLE:
        raise RuntimeError("candle reader emitted the wrong channel")
    value = _parse_market_object(frame, instrument)
    sequence = _positive_int(value.get("bridge_sequence"), "candle bridge_sequence")
    interval_start = _positive_int(value.get("interval_start"), "candle interval_start")
    interval_end = _positive_int(value.get("interval_end"), "candle interval_end")
    _positive_int(value.get("timeframe_seconds"), "candle timeframe_seconds")
    if interval_end <= interval_start:
        raise RuntimeError("candle interval must have positive duration")
    if value.get("finality") != "FINAL":
        raise RuntimeError("qualification accepts only explicitly finalized candles")
    if sequence != expected_sequence:
        raise RuntimeError("candle bridge sequence is not contiguous from one")
    return sequence


def _monotonic_field(value: int | MissingReason) -> object:
    if isinstance(value, MissingReason):
        return {"missing": value.value}
    return value


def _health_line(assessment: HealthAssessment) -> bytes:
    return _canonical_json(
        {
            "schema": 1,
            "clock_scope": assessment.sample.clock_scope,
            "now_ns": assessment.sample.now_ns,
            "heartbeat_ns": _monotonic_field(assessment.sample.heartbeat_ns),
            "market_data_ns": _monotonic_field(assessment.sample.market_data_ns),
            "heartbeat_age_ns": _monotonic_field(assessment.heartbeat_age_ns),
            "market_age_ns": _monotonic_field(assessment.market_age_ns),
            "readiness": assessment.readiness.value,
            "posture": assessment.posture.value,
            "reasons": [reason.value for reason in assessment.reasons],
        }
    )


def _latency_line(
    *,
    frame: RawFrame,
    sequence: int,
    ingress_ns: int,
    available_ns: int,
    clock_scope: str,
) -> bytes:
    latency = measure_transit_latency(clock_scope, ingress_ns, available_ns)
    return _canonical_json(
        {
            "schema": 1,
            "channel": frame.channel.value,
            "sequence": sequence,
            "payload_sha256": content_hash(frame.payload).value,
            "clock_scope": latency.clock_scope,
            "ingress_ns": latency.ingress_ns,
            "available_ns": latency.available_ns,
            "ingress_to_validated_availability_ns": latency.latency_ns,
        }
    )


def _persist_buffers(
    evidence: SessionEvidence,
    *,
    tick_bytes: bytearray,
    candle_bytes: bytearray,
    latency_bytes: bytearray,
    health_bytes: bytearray,
    observed_at: datetime,
) -> None:
    if tick_bytes:
        evidence.record(bytes(tick_bytes), "rico-tick-prefix", observed_at)
    if candle_bytes:
        evidence.record(bytes(candle_bytes), "rico-candle-prefix", observed_at)
    if latency_bytes:
        evidence.record(bytes(latency_bytes), "rico-local-latency", observed_at)
    if health_bytes:
        evidence.record(bytes(health_bytes), "rico-health-samples", observed_at)


def run_first_lab(
    *,
    instrument: str,
    capture_scope: str,
    code_revision: str,
    discovery_file: Path,
    tick_file: Path,
    candle_file: Path,
    output_root: Path,
    clock_scope: str,
    discovery_timeout_seconds: float,
    capture_seconds: float,
    poll_interval_ms: int,
    heartbeat_timeout_ms: int,
    market_staleness_ms: int,
    monotonic_ns: Callable[[], int] = time.monotonic_ns,
    sleep: Callable[[float], None] = time.sleep,
    wall_now: Callable[[], datetime] = _utc_now,
) -> Path:
    """Observe one bounded local bridge session and persist non-financial evidence."""
    if WIN_CONTRACT.fullmatch(instrument) is None:
        raise ValueError("instrument must be an explicit concrete WIN contract")
    require_text(capture_scope, "capture_scope")
    require_text(clock_scope, "clock_scope")
    if discovery_timeout_seconds <= 0 or discovery_timeout_seconds > MAX_DISCOVERY_SECONDS:
        raise ValueError("discovery_timeout_seconds must be in (0, 30]")
    if capture_seconds < MIN_CAPTURE_SECONDS or capture_seconds > MAX_CAPTURE_SECONDS:
        raise ValueError("capture_seconds must be in [60, 300]")
    if type(poll_interval_ms) is not int or not 10 <= poll_interval_ms <= 1000:
        raise ValueError("poll_interval_ms must be an integer in [10, 1000]")
    if type(heartbeat_timeout_ms) is not int or heartbeat_timeout_ms <= poll_interval_ms:
        raise ValueError("heartbeat_timeout_ms must exceed poll_interval_ms")
    if type(market_staleness_ms) is not int or market_staleness_ms <= poll_interval_ms:
        raise ValueError("market_staleness_ms must exceed poll_interval_ms")

    revision = CodeRevision(code_revision)
    discovery_path, tick_path, candle_path = _validated_transport_paths(
        discovery_file, tick_file, candle_file
    )
    store, session_root = _new_store(output_root)
    started_at = wall_now()
    evidence = SessionEvidence(
        store,
        code_revision=revision,
        config=_config(
            instrument=instrument,
            capture_scope=capture_scope,
            clock_scope=clock_scope,
            discovery_timeout_seconds=discovery_timeout_seconds,
            capture_seconds=capture_seconds,
            poll_interval_ms=poll_interval_ms,
            heartbeat_timeout_ms=heartbeat_timeout_ms,
            market_staleness_ms=market_staleness_ms,
        ),
        started_at=started_at,
    )

    discovery = RicoMt5DiscoveryReader(RicoMt5DiscoverySettings(discovery_path))
    ticks = RicoMt5BridgeReader(
        RicoMt5BridgeSettings(capture_scope, instrument, tick_path, RawChannel.TICK)
    )
    candles = RicoMt5BridgeReader(
        RicoMt5BridgeSettings(capture_scope, instrument, candle_path, RawChannel.CANDLE)
    )
    policy = HealthPolicy(
        "rico-mt5-first-lab",
        heartbeat_timeout_ms * 1_000_000,
        market_staleness_ms * 1_000_000,
    )

    tick_bytes = bytearray()
    candle_bytes = bytearray()
    latency_bytes = bytearray()
    health_bytes = bytearray()
    tick_count = 0
    candle_count = 0
    last_tick_sequence = 0
    last_candle_sequence = 0
    last_market_ns: int | None = None
    previous_health: HealthAssessment | None = None
    health_failed = False
    buffers_persisted = False
    session_succeeded = False

    start_ns = monotonic_ns()
    discovery_deadline_ns = start_ns + int(discovery_timeout_seconds * 1_000_000_000)
    capture_deadline_ns: int | None = None
    last_loop_ns = start_ns

    try:
        while True:
            now_ns = monotonic_ns()
            if capture_deadline_ns is None:
                if now_ns > discovery_deadline_ns:
                    raise RuntimeError("complete Rico/MT5 discovery snapshot did not arrive in time")
                before = discovery.offset
                snapshot = discovery.poll_snapshot()
                if snapshot is not None:
                    after = discovery.offset
                    raw_snapshot = _read_exact_prefix(discovery_path, after)[before:after]
                    evidence.record(raw_snapshot, "rico-discovery-snapshot", wall_now())
                    if snapshot.prefix != "WIN" or not snapshot.enumeration_complete:
                        raise RuntimeError("Rico/MT5 discovery snapshot is incomplete or wrong-prefix")
                    candidates = tuple(item.symbol for item in snapshot.symbols)
                    if instrument not in candidates:
                        raise RuntimeError("explicit WIN instrument is absent from discovery evidence")
                    confirmation = _canonical_json(
                        {
                            "schema": 1,
                            "instrument_family": "WIN",
                            "provider": RICO_MT5_PROVIDER,
                            "capture_scope": capture_scope,
                            "instrument": instrument,
                            "confirmation": "complete-discovery-exact-match",
                            "candidate_count": len(candidates),
                            "snapshot_id": snapshot.snapshot_id,
                        }
                    )
                    evidence.record(confirmation, "rico-instrument-confirmed", wall_now())
                    capture_deadline_ns = monotonic_ns() + int(capture_seconds * 1_000_000_000)
                else:
                    last_loop_ns = now_ns
                    sleep(poll_interval_ms / 1000)
                    continue

            hit_drain_limit = False
            for reader, channel in ((ticks, RawChannel.TICK), (candles, RawChannel.CANDLE)):
                for _ in range(MAX_DRAIN_PER_CHANNEL):
                    frame = reader.poll_next()
                    if frame is None:
                        break
                    ingress_ns = monotonic_ns()
                    if channel is RawChannel.TICK:
                        _bounded_append(
                            tick_bytes,
                            frame.payload,
                            limit=MAX_CHANNEL_BYTES,
                            label="tick prefix",
                        )
                        sequence = _validate_tick(frame, instrument, last_tick_sequence + 1)
                        last_tick_sequence = sequence
                        tick_count += 1
                        last_market_ns = ingress_ns
                    else:
                        _bounded_append(
                            candle_bytes,
                            frame.payload,
                            limit=MAX_CHANNEL_BYTES,
                            label="candle prefix",
                        )
                        sequence = _validate_candle(frame, instrument, last_candle_sequence + 1)
                        last_candle_sequence = sequence
                        candle_count += 1
                    available_ns = monotonic_ns()
                    _bounded_append(
                        latency_bytes,
                        _latency_line(
                            frame=frame,
                            sequence=sequence,
                            ingress_ns=ingress_ns,
                            available_ns=available_ns,
                            clock_scope=clock_scope,
                        ),
                        limit=MAX_METADATA_BYTES,
                        label="latency evidence",
                    )
                else:
                    hit_drain_limit = True

            sample_now_ns = monotonic_ns()
            if last_market_ns is not None:
                sample = HealthSample(
                    clock_scope,
                    sample_now_ns,
                    last_loop_ns,
                    last_market_ns,
                )
                evaluation = evaluate_health(
                    sample,
                    phase=RuntimePhase.RUNNING,
                    requested_posture=SafetyPosture.NORMAL,
                    policy=policy,
                    previous=previous_health,
                )
                previous_health = evaluation.assessment
                _bounded_append(
                    health_bytes,
                    _health_line(evaluation.assessment),
                    limit=MAX_METADATA_BYTES,
                    label="health evidence",
                )
                if evaluation.assessment.readiness is not ReadinessStatus.READY:
                    health_failed = True
            last_loop_ns = sample_now_ns

            if capture_deadline_ns is not None and sample_now_ns >= capture_deadline_ns:
                break
            if not hit_drain_limit:
                sleep(poll_interval_ms / 1000)

        if tick_count < MIN_TICK_FRAMES:
            raise RuntimeError("qualification capture requires at least two realtime tick frames")
        if candle_count < MIN_CANDLE_FRAMES:
            raise RuntimeError("qualification capture requires at least one finalized candle frame")
        if health_failed or previous_health is None:
            raise RuntimeError("qualification capture did not preserve a continuously ready health path")

        finished_at = wall_now()
        _persist_buffers(
            evidence,
            tick_bytes=tick_bytes,
            candle_bytes=candle_bytes,
            latency_bytes=latency_bytes,
            health_bytes=health_bytes,
            observed_at=finished_at,
        )
        buffers_persisted = True
        summary = _canonical_json(
            {
                "schema": 1,
                "provider": RICO_MT5_PROVIDER,
                "instrument_family": "WIN",
                "instrument": instrument,
                "capture_scope": capture_scope,
                "run_id": evidence.run_id,
                "tick_frames": tick_count,
                "candle_frames": candle_count,
                "tick_bytes": len(tick_bytes),
                "candle_bytes": len(candle_bytes),
                "tick_sha256": hashlib.sha256(tick_bytes).hexdigest(),
                "candle_sha256": hashlib.sha256(candle_bytes).hexdigest(),
                "latency_samples": tick_count + candle_count,
                "health_samples_present": bool(health_bytes),
                "health_remained_ready": True,
                "real_money": False,
                "trading_capability": False,
                "metatrader_control_api": False,
            }
        )
        evidence.record(summary, "rico-capture-summary", finished_at)
        session_succeeded = True
        return session_root
    finally:
        stopped_at = wall_now()
        if not session_succeeded:
            if not buffers_persisted:
                _persist_buffers(
                    evidence,
                    tick_bytes=tick_bytes,
                    candle_bytes=candle_bytes,
                    latency_bytes=latency_bytes,
                    health_bytes=health_bytes,
                    observed_at=stopped_at,
                )
            failure = _canonical_json(
                {
                    "schema": 1,
                    "provider": RICO_MT5_PROVIDER,
                    "run_id": evidence.run_id,
                    "outcome": "FAILED",
                    "tick_frames_preserved": tick_count,
                    "candle_frames_preserved": candle_count,
                    "real_money": False,
                    "trading_capability": False,
                }
            )
            evidence.record(failure, "rico-session-failed", stopped_at, TechnicalEventKind.ANOMALY)
        evidence.stop(stopped_at)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rico/MT5 Sprint 1 local read-only evidence harness"
    )
    parser.add_argument("--instrument", required=True, help="explicit point-in-time WIN symbol")
    parser.add_argument("--capture-scope", required=True)
    parser.add_argument("--code-revision", required=True, help="exact reviewed 40-char Git SHA")
    parser.add_argument("--discovery-file", required=True, type=Path)
    parser.add_argument("--tick-file", required=True, type=Path)
    parser.add_argument("--candle-file", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--clock-scope", required=True)
    parser.add_argument("--discovery-timeout-seconds", required=True, type=float)
    parser.add_argument("--capture-seconds", required=True, type=float)
    parser.add_argument("--poll-interval-ms", required=True, type=int)
    parser.add_argument("--heartbeat-timeout-ms", required=True, type=int)
    parser.add_argument("--market-staleness-ms", required=True, type=int)
    return parser


def main() -> int:
    args = _parser().parse_args()
    session_root = run_first_lab(
        instrument=args.instrument,
        capture_scope=args.capture_scope,
        code_revision=args.code_revision,
        discovery_file=args.discovery_file,
        tick_file=args.tick_file,
        candle_file=args.candle_file,
        output_root=args.output_root,
        clock_scope=args.clock_scope,
        discovery_timeout_seconds=args.discovery_timeout_seconds,
        capture_seconds=args.capture_seconds,
        poll_interval_ms=args.poll_interval_ms,
        heartbeat_timeout_ms=args.heartbeat_timeout_ms,
        market_staleness_ms=args.market_staleness_ms,
    )
    print(f"controlled local read-only capture evidence: {session_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
