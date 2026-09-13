"""Versioned technical record codec; raw bytes are preserved, never admitted here."""

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import cast

from btg_ai_trader.observer.identity import ArtifactId, EventId, RunId
from btg_ai_trader.observer.provenance import (
    CaptureContext,
    CodeRevision,
    ConfigHash,
    ContentHash,
    InputIdentity,
    ProvenanceLabel,
)
from btg_ai_trader.observer.temporal import require_utc


@dataclass(frozen=True, slots=True)
class PersistenceRecordId:
    """Logical persistence identity; distinct from artifact identity and location."""

    value: str

    def __post_init__(self) -> None:
        EventId(self.value)


def content_hash(data: bytes) -> ContentHash:
    if type(data) is not bytes:
        raise ValueError("content must be immutable bytes")
    return ContentHash(hashlib.sha256(data).hexdigest())


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    record_id: PersistenceRecordId
    input_identity: InputIdentity
    observed_at: datetime
    raw: bytes
    capture: CaptureContext | None = None
    supersedes: PersistenceRecordId | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, PersistenceRecordId):
            raise ValueError("evidence requires a logical persistence identity")
        if not isinstance(self.input_identity, InputIdentity):
            raise ValueError("evidence requires explicit input identity")
        require_utc(self.observed_at, "observed_at")
        if content_hash(self.raw) != self.input_identity.content_hash:
            raise ValueError("raw bytes must match declared input hash")
        if self.capture is not None and not isinstance(self.capture, CaptureContext):
            raise ValueError("capture must be explicit or absent")
        if self.supersedes is not None:
            if not isinstance(self.supersedes, PersistenceRecordId):
                raise ValueError("supersedes requires a logical persistence identity")
            if self.supersedes == self.record_id:
                raise ValueError("a record cannot supersede itself")


class TechnicalEventKind(Enum):
    OBSERVATION_RECORDED = "OBSERVATION_RECORDED"
    STARTED = "STARTED"
    STOPPED = "STOPPED"
    ANOMALY = "ANOMALY"
    HEALTH_CHANGED = "HEALTH_CHANGED"


@dataclass(frozen=True, slots=True)
class TechnicalJournalRecord:
    record_id: PersistenceRecordId
    run_id: RunId
    observed_at: datetime
    kind: TechnicalEventKind
    detail: ProvenanceLabel
    evidence_ref: PersistenceRecordId | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, PersistenceRecordId):
            raise ValueError("journal requires a logical persistence identity")
        if not isinstance(self.run_id, RunId):
            raise ValueError("journal requires an explicit run")
        require_utc(self.observed_at, "observed_at")
        if not isinstance(self.kind, TechnicalEventKind):
            raise ValueError("journal requires a technical event kind")
        if not isinstance(self.detail, ProvenanceLabel):
            raise ValueError("journal detail must be a bounded logical label")
        if self.evidence_ref is not None and not isinstance(
            self.evidence_ref, PersistenceRecordId
        ):
            raise ValueError("journal evidence reference must be a logical identity")


type TechnicalRecord = EvidenceRecord | TechnicalJournalRecord


def _capture_fields(context: CaptureContext | None) -> dict[str, str] | None:
    if context is None:
        return None
    return {
        "run_id": context.run_id.value,
        "code_revision": context.code_revision.value,
        "config_hash": context.config_hash.value,
        "provider": context.provider.value,
    }


def encode_record(record: TechnicalRecord) -> bytes:
    """Canonical version 1 JSON; no arbitrary metadata or inferred timestamps."""
    if not isinstance(record, EvidenceRecord | TechnicalJournalRecord):
        raise ValueError("only typed technical records can be encoded")
    fields: dict[str, object] = {
        "schema": 1,
        "record_id": record.record_id.value,
        "observed_at": record.observed_at.isoformat(timespec="microseconds"),
    }
    if isinstance(record, EvidenceRecord):
        reference = record.input_identity
        fields.update({
            "plane": "evidence",
            "input": {
                "kind": "event" if isinstance(reference.artifact_id, EventId) else "artifact",
                "id": reference.artifact_id.value,
                "sha256": reference.content_hash.value,
            },
            "raw_base64": base64.b64encode(record.raw).decode("ascii"),
            "capture": _capture_fields(record.capture),
            "supersedes": None if record.supersedes is None else record.supersedes.value,
        })
    else:
        fields.update({
            "plane": "journal",
            "run_id": record.run_id.value,
            "kind": record.kind.value,
            "detail": record.detail.value,
            "evidence_ref": None if record.evidence_ref is None else record.evidence_ref.value,
        })
    return (json.dumps(
        fields, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")
    ) + "\n").encode("utf-8")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _object(value: object, keys: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys:
        raise ValueError("record fields must exactly match schema")
    return cast(dict[str, object], value)


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("expected explicit text")
    return value


def _reference(value: object) -> PersistenceRecordId | None:
    return None if value is None else PersistenceRecordId(_text(value))


def _decode_capture(value: object) -> CaptureContext | None:
    if value is None:
        return None
    fields = _object(value, {"run_id", "code_revision", "config_hash", "provider"})
    return CaptureContext(
        RunId(_text(fields["run_id"])),
        CodeRevision(_text(fields["code_revision"])),
        ConfigHash(_text(fields["config_hash"])),
        ProvenanceLabel(_text(fields["provider"])),
    )


def decode_record(data: bytes) -> TechnicalRecord:
    """Reject malformed, noncanonical, unknown-version or hash-inconsistent records."""
    if type(data) is not bytes:
        raise ValueError("record must be immutable bytes")
    parsed: object = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_object)
    if type(parsed) is not dict:
        raise ValueError("record must be a JSON object")
    fields = cast(dict[str, object], parsed)
    if type(fields.get("schema")) is not int or fields["schema"] != 1:
        raise ValueError("unknown record schema")
    common = {"schema", "plane", "record_id", "observed_at"}
    plane = fields.get("plane")
    if plane == "evidence":
        fields = _object(fields, common | {"input", "raw_base64", "capture", "supersedes"})
        reference = _object(fields["input"], {"kind", "id", "sha256"})
        if reference["kind"] == "event":
            identity: EventId | ArtifactId = EventId(_text(reference["id"]))
        elif reference["kind"] == "artifact":
            identity = ArtifactId(_text(reference["id"]))
        else:
            raise ValueError("unknown input identity kind")
        record: TechnicalRecord = EvidenceRecord(
            PersistenceRecordId(_text(fields["record_id"])),
            InputIdentity(identity, ContentHash(_text(reference["sha256"]))),
            datetime.fromisoformat(_text(fields["observed_at"])),
            base64.b64decode(_text(fields["raw_base64"]), validate=True),
            _decode_capture(fields["capture"]),
            _reference(fields["supersedes"]),
        )
    elif plane == "journal":
        fields = _object(fields, common | {"run_id", "kind", "detail", "evidence_ref"})
        record = TechnicalJournalRecord(
            PersistenceRecordId(_text(fields["record_id"])),
            RunId(_text(fields["run_id"])),
            datetime.fromisoformat(_text(fields["observed_at"])),
            TechnicalEventKind(_text(fields["kind"])),
            ProvenanceLabel(_text(fields["detail"])),
            _reference(fields["evidence_ref"]),
        )
    else:
        raise ValueError("unknown persistence plane")
    if encode_record(record) != data:
        raise ValueError("record representation must be canonical")
    return record
