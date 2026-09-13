"""Single-owner fixture Observer composition; no live provider or financial authority."""

import json
from dataclasses import dataclass, fields, replace
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, cast
from uuid import uuid4

from btg_ai_trader.observer.admission import (
    Admitted,
    IngressMetadata,
    Quarantined,
    admit_fixture,
)
from btg_ai_trader.observer.dedup import (
    DedupResult,
    DedupState,
    DedupStatus,
    LateAnnotation,
    annotate_late,
    classify_duplicate,
)
from btg_ai_trader.observer.envelope import EventEnvelope
from btg_ai_trader.observer.health import (
    HealthPolicy,
    HealthSample,
    RuntimePhase,
    SafetyPosture,
)
from btg_ai_trader.observer.identity import (
    ArtifactId,
    CorrelationId,
    EventId,
    ProviderInstrumentRef,
    RunId,
    TradableInstrumentId,
)
from btg_ai_trader.observer.ingestion import (
    ObservationQueue,
    OfferStatus,
    QueueHealthAssessment,
    TakeResult,
    evaluate_queue_health,
    offer,
    take,
)
from btg_ai_trader.observer.instruments import (
    InstrumentMapping,
    InstrumentRegistry,
    InstrumentResolution,
    ResolutionStatus,
)
from btg_ai_trader.observer.market import Candle, Tick
from btg_ai_trader.observer.provenance import (
    CaptureContext,
    CodeRevision,
    ConfigHash,
    ContentHash,
    InputIdentity,
    ProvenanceLabel,
    RunManifest,
    RunRelation,
)
from btg_ai_trader.observer.provider import FidelityMode
from btg_ai_trader.observer.raw_source import FixtureMarketDataSource, RawFrame
from btg_ai_trader.observer.storage import (
    PersistenceReceipt,
    PersistenceStatus,
    TechnicalEvidenceStore,
    WriteUncertain,
)
from btg_ai_trader.observer.storage_records import (
    EvidenceRecord,
    PersistenceRecordId,
    TechnicalEventKind,
    TechnicalJournalRecord,
    TechnicalRecord,
    content_hash,
    encode_record,
)
from btg_ai_trader.observer.temporal import EventTime, ObservationTimes, require_utc
from btg_ai_trader.observer.values import MissingReason


@dataclass(frozen=True, slots=True)
class ObserverConfig:
    provider: str
    capture_scope: str
    queue_capacity: int
    dedup_capacity: int
    max_payload_bytes: int
    clock_scope: str
    heartbeat_timeout_ns: int
    market_staleness_ns: int

    def __post_init__(self) -> None:
        for name in ("provider", "capture_scope", "clock_scope"):
            ProvenanceLabel(getattr(self, name))
        for name in (
            "queue_capacity", "dedup_capacity", "max_payload_bytes",
            "heartbeat_timeout_ns", "market_staleness_ns",
        ):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be an explicit positive integer")

    @classmethod
    def from_mapping(cls, value: object) -> "ObserverConfig":
        keys = {field.name for field in fields(cls)}
        if type(value) is not dict or set(value) != keys:
            raise ValueError("configuration requires exactly the passive declared fields")
        data = cast(dict[str, object], value)
        text: dict[str, str] = {}
        numbers: dict[str, int] = {}
        for key in ("provider", "capture_scope", "clock_scope"):
            if type(data[key]) is not str:
                raise ValueError("configuration labels must be text")
            text[key] = cast(str, data[key])
        for key in keys - text.keys():
            if type(data[key]) is not int:
                raise ValueError("configuration limits must be integers")
            numbers[key] = cast(int, data[key])
        return cls(
            text["provider"], text["capture_scope"], numbers["queue_capacity"],
            numbers["dedup_capacity"], numbers["max_payload_bytes"], text["clock_scope"],
            numbers["heartbeat_timeout_ns"], numbers["market_staleness_ns"],
        )

    def canonical_bytes(self) -> bytes:
        return _canonical({field.name: getattr(self, field.name) for field in fields(self)})


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                       allow_nan=False) + "\n").encode("utf-8")


def _wire(value: object) -> object:
    """Private serialization of an explicit model allowlist, never arbitrary dataclasses."""
    if value is None or type(value) in (str, int, bool):
        return value
    if isinstance(value, Enum):
        return {"enum": type(value).__name__, "value": value.value}
    if type(value) is Decimal:
        return {"decimal": str(value)}
    if type(value) is datetime:
        return {"utc": value.isoformat(timespec="microseconds")}
    if type(value) is timedelta:
        return {"microseconds": (
            value.days * 86400000000 + value.seconds * 1000000 + value.microseconds
        )}
    if type(value) is tuple:
        return [_wire(item) for item in value]
    models = (
        ArtifactId, CorrelationId, EventId, RunId, TradableInstrumentId, ProviderInstrumentRef,
        CodeRevision, ConfigHash, ContentHash, ProvenanceLabel, InputIdentity, RunRelation,
        RunManifest, IngressMetadata, EventTime, ObservationTimes, EventEnvelope, Tick, Candle,
        InstrumentMapping, InstrumentResolution,
    )
    if type(value) in models:
        return {field.name: _wire(getattr(value, field.name)) for field in fields(cast(Any, value))}
    raise TypeError("unsupported technical serialization type")


def _record_id() -> PersistenceRecordId:
    return PersistenceRecordId(str(uuid4()))


def _artifact(raw: bytes, observed_at: datetime, capture: CaptureContext) -> EvidenceRecord:
    return EvidenceRecord(
        _record_id(), InputIdentity(ArtifactId(str(uuid4())), content_hash(raw)),
        observed_at, raw, capture,
    )


class StepStatus(Enum):
    STARTED = "STARTED"
    EXHAUSTED = "EXHAUSTED"
    ADMITTED = "ADMITTED"
    QUARANTINED = "QUARANTINED"
    REGISTRY_UNRESOLVED = "REGISTRY_UNRESOLVED"
    DUPLICATE = "DUPLICATE"
    IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
    BACKPRESSURE = "BACKPRESSURE"
    DEDUP_FULL = "DEDUP_FULL"
    STORAGE_BLOCKED = "STORAGE_BLOCKED"


@dataclass(frozen=True, slots=True)
class ObservationDecision:
    admission: Admitted | Quarantined
    resolution: InstrumentResolution | None
    dedup: DedupResult | None
    late: LateAnnotation | None
    disposition: StepStatus


@dataclass(frozen=True, slots=True)
class StepResult:
    status: StepStatus
    pending: bool
    raw: RawFrame | None = None
    decision: ObservationDecision | None = None
    raw_receipt: PersistenceReceipt | None = None
    decision_receipt: PersistenceReceipt | None = None
    journal_receipt: PersistenceReceipt | None = None
    health: QueueHealthAssessment | None = None
    error: str | None = None


@dataclass(slots=True)
class _Pending:
    frame: RawFrame
    ingress: IngressMetadata
    valid_at: datetime | MissingReason
    cutoff: datetime
    frontier: EventEnvelope | None
    sample: HealthSample
    raw_record: EvidenceRecord
    raw_receipt: PersistenceReceipt | None = None
    decision: ObservationDecision | None = None
    decision_record: EvidenceRecord | None = None
    journal_record: TechnicalJournalRecord | None = None
    decision_receipt: PersistenceReceipt | None = None
    journal_receipt: PersistenceReceipt | None = None
    staged_queue: ObservationQueue | None = None
    staged_dedup: DedupState | None = None
    waiting_capacity: bool = False
    pressure_reported: bool = False


class FixtureObserver:
    """One explicit owner; retry never advances source or substitutes pending context."""

    def __init__(
        self, config: ObserverConfig, source: FixtureMarketDataSource,
        store: TechnicalEvidenceStore, registry: InstrumentRegistry, *,
        run_id: RunId, code_revision: CodeRevision, started_at: datetime,
        inputs: tuple[InputIdentity, ...] = (),
    ) -> None:
        # Validate every dependency before invoking any of them.
        if (
            type(config) is not ObserverConfig or type(source) is not FixtureMarketDataSource
            or type(store) is not TechnicalEvidenceStore or type(registry) is not InstrumentRegistry
        ):
            raise TypeError("only exact passive concrete dependencies are accepted")
        if type(run_id) is not RunId or type(code_revision) is not CodeRevision:
            raise TypeError("explicit typed run identity and code pin required")
        require_utc(started_at, "started_at")
        descriptor = source.describe_capabilities()
        if (
            descriptor.provider != config.provider
            or descriptor.capture_scope != config.capture_scope
        ):
            raise ValueError("source descriptor must match effective configuration")
        self._config = config
        self._manifest = RunManifest(
            run_id, started_at, code_revision,
            ConfigHash(content_hash(config.canonical_bytes()).value), inputs,
        )
        self._capture = CaptureContext.from_manifest(self.manifest, ProvenanceLabel(config.provider))
        self._source, self._store, self._registry = source, store, registry
        self._queue = ObservationQueue.empty(config.capture_scope, config.queue_capacity)
        self._dedup = DedupState(run_id.value, config.dedup_capacity)
        self._policy = HealthPolicy(
            "fixture-observer", config.heartbeat_timeout_ns, config.market_staleness_ns
        )
        self._unknown_fidelity = descriptor.fidelity is FidelityMode.UNKNOWN
        self._posture = SafetyPosture.DEGRADED if self._unknown_fidelity else SafetyPosture.NORMAL
        self._health: QueueHealthAssessment | None = None
        self._pending: _Pending | None = None
        self._uncertain: TechnicalRecord | None = None
        self._error: str | None = None
        self._started = False
        self._exhausted = False
        self._last_ingestion = started_at
        self._last_order: int | None = None
        manifest_bytes = _canonical({
            "schema": 1, "kind": "fixture-run-manifest",
            "manifest": _wire(self.manifest),
            "effective_config": json.loads(config.canonical_bytes()),
            "code_pin_verification": "CALLER_SUPPLIED",
        })
        self._manifest_record = _artifact(manifest_bytes, started_at, self.capture)
        self._start_journal = TechnicalJournalRecord(
            _record_id(), run_id, started_at, TechnicalEventKind.STARTED,
            ProvenanceLabel("fixture-observer.started"), self.manifest_record.record_id,
        )
        self._manifest_receipt: PersistenceReceipt | None = None
        self._start_receipt: PersistenceReceipt | None = None

    @property
    def config(self) -> ObserverConfig:
        return self._config

    @property
    def manifest(self) -> RunManifest:
        return self._manifest

    @property
    def capture(self) -> CaptureContext:
        return self._capture

    @property
    def manifest_record(self) -> EvidenceRecord:
        return self._manifest_record

    @property
    def queue(self) -> ObservationQueue:
        return self._queue

    @property
    def pending_raw(self) -> RawFrame | None:
        return self._pending.frame if self._pending else None

    @property
    def health(self) -> QueueHealthAssessment | None:
        return self._health

    def _refresh_health(self, sample: HealthSample) -> None:
        result = evaluate_queue_health(
            sample, queue=self._queue,
            phase=RuntimePhase.STOPPED if self._exhausted else RuntimePhase.RUNNING,
            requested_posture=self._posture, policy=self._policy, previous=self._health,
        )
        self._health = result.assessment
        self._posture = result.assessment.health.posture

    def _attempt(self, record: TechnicalRecord) -> PersistenceReceipt | None:
        try:
            if self._uncertain is not None:
                if record != self._uncertain:
                    raise ValueError("uncertain record must be resolved before other writes")
                expected_hash = content_hash(encode_record(record))
                existing = (
                    self._store.resolve_evidence(record.record_id, expected_hash)
                    if isinstance(record, EvidenceRecord)
                    else self._store.resolve_journal(record.record_id, expected_hash)
                )
                self._uncertain = None
                if existing is not None:
                    self._error = None
                    return PersistenceReceipt(
                        record.record_id, expected_hash, PersistenceStatus.ALREADY_PRESENT
                    )
            receipt = (
                self._store.append_evidence(record)
                if isinstance(record, EvidenceRecord) else self._store.append_journal(record)
            )
        except WriteUncertain:
            self._uncertain = record
            self._error = "WriteUncertain"
        except (OSError, ValueError) as error:
            self._error = type(error).__name__
        else:
            self._error = None
            return receipt
        self._posture = SafetyPosture.SAFE_HALT
        if self._pending is not None:
            self._refresh_health(self._pending.sample)
        return None

    def start(self) -> StepResult:
        if self._started:
            return StepResult(StepStatus.STARTED, False, journal_receipt=self._start_receipt)
        if self._manifest_receipt is None:
            self._manifest_receipt = self._attempt(self.manifest_record)
            if self._manifest_receipt is None:
                return StepResult(StepStatus.STORAGE_BLOCKED, True, error=self._error)
        if self._start_receipt is None:
            self._start_receipt = self._attempt(self._start_journal)
            if self._start_receipt is None:
                return StepResult(StepStatus.STORAGE_BLOCKED, True, error=self._error)
        self._started = True
        return StepResult(StepStatus.STARTED, False, journal_receipt=self._start_receipt)

    def advance(
        self, ingress: IngressMetadata, *, valid_at: datetime | MissingReason,
        knowledge_cutoff: datetime, frontier: EventEnvelope | None, health_sample: HealthSample,
    ) -> StepResult:
        if not self._started or self._pending is not None:
            raise ValueError("start must finish and pending work requires explicit retry")
        if type(ingress) is not IngressMetadata or type(health_sample) is not HealthSample:
            raise TypeError("explicit ingress and health sample required")
        if not isinstance(valid_at, MissingReason):
            require_utc(valid_at, "valid_at")
        require_utc(knowledge_cutoff, "knowledge_cutoff")
        if knowledge_cutoff > ingress.ingestion_time:
            raise ValueError("registry cutoff cannot exceed observed ingestion boundary")
        if frontier is not None and type(frontier) is not EventEnvelope:
            raise TypeError("frontier must be an explicit EventEnvelope or None")
        if ingress.ingestion_time < self._last_ingestion:
            raise ValueError("ingestion chronology cannot regress")
        if ingress.ingestion_order is not None and self._last_order is not None:
            if ingress.ingestion_order <= self._last_order:
                raise ValueError("known ingestion order must advance")
        if health_sample.clock_scope != self.config.clock_scope:
            raise ValueError("health clock scope differs from configuration")
        # Evaluate chronology/watermarks before consuming a frame.
        evaluate_queue_health(
            health_sample, queue=self._queue, phase=RuntimePhase.RUNNING,
            requested_posture=self._posture, policy=self._policy, previous=self._health,
        )
        if self._exhausted:
            return StepResult(StepStatus.EXHAUSTED, False, health=self._health)
        frame = self._source.read_next()
        if frame is None:
            self._exhausted = True
            self._refresh_health(health_sample)
            return StepResult(StepStatus.EXHAUSTED, False, health=self._health)
        self._last_ingestion = ingress.ingestion_time
        if ingress.ingestion_order is not None:
            self._last_order = ingress.ingestion_order
        self._pending = _Pending(
            frame, ingress, valid_at, knowledge_cutoff, frontier, health_sample,
            _artifact(frame.payload, ingress.ingestion_time, self.capture),
        )
        self._refresh_health(health_sample)
        return self._progress()

    def _plan(self, pending: _Pending) -> StepStatus | None:
        admission = admit_fixture(
            pending.frame, pending.ingress, max_payload_bytes=self.config.max_payload_bytes
        )
        resolution = None
        duplicate = None
        late = None
        disposition = StepStatus.QUARANTINED
        staged_queue, staged_dedup = self._queue, self._dedup
        if isinstance(admission, Admitted):
            if isinstance(pending.valid_at, datetime):
                resolution = self._registry.resolve(
                    admission.envelope.source, valid_at=pending.valid_at,
                    knowledge_cutoff=pending.cutoff,
                )
            disposition = StepStatus.REGISTRY_UNRESOLVED
            if resolution is not None and resolution.status is ResolutionStatus.RESOLVED:
                declared = admission.envelope.instrument_id
                compatible = (
                    isinstance(declared, MissingReason) or declared == resolution.instrument_id
                )
                if compatible:
                    duplicate = classify_duplicate(self._dedup, admission.envelope)
                    late = (
                        annotate_late(admission.envelope, pending.frontier)
                        if pending.frontier is not None else None
                    )
                    disposition = {
                        DedupStatus.NEW: StepStatus.ADMITTED,
                        DedupStatus.DUPLICATE: StepStatus.DUPLICATE,
                        DedupStatus.IDENTITY_CONFLICT: StepStatus.IDENTITY_CONFLICT,
                        DedupStatus.CAPACITY_EXHAUSTED: StepStatus.DEDUP_FULL,
                    }[duplicate.status]
                    if duplicate.status is DedupStatus.NEW:
                        offered = offer(self._queue, admission.envelope)
                        if offered.status is OfferStatus.BACKPRESSURE:
                            if not pending.pressure_reported:
                                self._queue = offered.queue
                                pending.pressure_reported = True
                            pending.waiting_capacity = True
                            self._posture = SafetyPosture.DEGRADED
                            self._refresh_health(pending.sample)
                            return StepStatus.BACKPRESSURE
                        staged_queue, staged_dedup = offered.queue, duplicate.state
                    elif duplicate.status is DedupStatus.CAPACITY_EXHAUSTED:
                        self._posture = SafetyPosture.SAFE_HALT
                        self._refresh_health(pending.sample)
                        return StepStatus.DEDUP_FULL
        if disposition in (
            StepStatus.QUARANTINED, StepStatus.REGISTRY_UNRESOLVED, StepStatus.IDENTITY_CONFLICT
        ):
            self._posture = SafetyPosture.SAFE_HALT
            self._refresh_health(pending.sample)
        pending.waiting_capacity = False
        pending.decision = ObservationDecision(admission, resolution, duplicate, late, disposition)
        pending.staged_queue, pending.staged_dedup = staged_queue, staged_dedup
        decision_bytes = _canonical({
            "schema": 1, "kind": "fixture-observation-decision-plan",
            "raw_record": pending.raw_record.record_id.value,
            "raw_artifact": pending.raw_record.input_identity.artifact_id.value,
            "raw_hash": pending.raw_record.input_identity.content_hash.value,
            "ingress": _wire(pending.ingress), "disposition": disposition.value,
            "registry_valid_at": _wire(pending.valid_at), "registry_cutoff": _wire(pending.cutoff),
            "registry": _wire(resolution),
            "envelope": _wire(admission.envelope) if isinstance(admission, Admitted) else None,
            "rejection": (
                {"reason": admission.reason.value, "field": admission.field}
                if isinstance(admission, Quarantined) else None
            ),
            "dedup": None if duplicate is None else {
                "status": duplicate.status.value, "canonical": _wire(duplicate.canonical),
                "incoming": _wire(duplicate.incoming),
            },
            "late": None if late is None else {
                "status": late.status.value, "frontier": _wire(late.frontier),
            },
            "processing_completion_time": {"missing": "UNKNOWN"},
            "derived_availability": {"missing": "UNKNOWN"},
            "queue_commit_claim": "NOT_ATOMIC_WITH_PERSISTENCE",
        })
        pending.decision_record = _artifact(
            decision_bytes, pending.ingress.ingestion_time, self.capture
        )
        pending.journal_record = TechnicalJournalRecord(
            _record_id(), self.manifest.run_id, pending.ingress.ingestion_time,
            TechnicalEventKind.OBSERVATION_RECORDED,
            ProvenanceLabel("observer." + disposition.value.lower()),
            pending.decision_record.record_id,
        )
        return None

    def _result(self, status: StepStatus, pending: _Pending) -> StepResult:
        return StepResult(
            status, True, pending.frame, pending.decision, pending.raw_receipt,
            pending.decision_receipt, pending.journal_receipt, self._health, self._error,
        )

    def _progress(self) -> StepResult:
        pending = self._pending
        if pending is None:
            raise ValueError("no pending frame")
        if pending.raw_receipt is None:
            pending.raw_receipt = self._attempt(pending.raw_record)
            if pending.raw_receipt is None:
                return self._result(StepStatus.STORAGE_BLOCKED, pending)
        if pending.decision is None:
            blocked = self._plan(pending)
            if blocked is not None:
                return self._result(blocked, pending)
        assert pending.decision_record is not None and pending.journal_record is not None
        if pending.decision_receipt is None:
            pending.decision_receipt = self._attempt(pending.decision_record)
            if pending.decision_receipt is None:
                return self._result(StepStatus.STORAGE_BLOCKED, pending)
        if pending.journal_receipt is None:
            pending.journal_receipt = self._attempt(pending.journal_record)
            if pending.journal_receipt is None:
                return self._result(StepStatus.STORAGE_BLOCKED, pending)
        assert pending.staged_queue is not None and pending.staged_dedup is not None
        assert pending.decision is not None
        self._queue, self._dedup = pending.staged_queue, pending.staged_dedup
        self._refresh_health(pending.sample)
        result = replace(self._result(pending.decision.disposition, pending), pending=False)
        self._pending = None
        return result

    def retry_pending(self) -> StepResult:
        if not self._started:
            return self.start()
        return self._progress()

    def take(self) -> TakeResult:
        if self._pending is not None and not self._pending.waiting_capacity:
            raise ValueError("drain is prohibited while writes or canonical capacity are pending")
        result = take(self._queue)
        self._queue = result.queue
        if self._health is not None:
            self._refresh_health(self._health.health.sample)
        return result
