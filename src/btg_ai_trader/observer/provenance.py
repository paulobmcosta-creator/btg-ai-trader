"""Immutable capture and processing references; no storage or credential access."""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import uuid4

from btg_ai_trader.observer.identity import ArtifactId, EventId, ReceiptId, RunId
from btg_ai_trader.observer.temporal import require_utc


def require_hex(value: str, length: int, field: str) -> None:
    if not isinstance(value, str) or re.fullmatch(rf"[0-9a-f]{{{length}}}", value) is None:
        raise ValueError(f"{field} must be a full lowercase hexadecimal digest")


@dataclass(frozen=True, slots=True)
class CodeRevision:
    value: str

    def __post_init__(self) -> None:
        require_hex(self.value, 40, "code_revision")


@dataclass(frozen=True, slots=True)
class ContentHash:
    value: str

    def __post_init__(self) -> None:
        require_hex(self.value, 64, "content_hash")


@dataclass(frozen=True, slots=True)
class ConfigHash:
    """Hash reference only; this model never receives configuration contents."""

    value: str

    def __post_init__(self) -> None:
        require_hex(self.value, 64, "config_hash")


@dataclass(frozen=True, slots=True)
class ProvenanceLabel:
    """Bounded logical label, not an arbitrary URL, path or metadata payload."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise ValueError("provenance label must be text")
        if re.fullmatch(r"[a-z][a-z0-9_.-]{0,63}", self.value) is None:
            raise ValueError("provenance label must be a bounded lowercase logical name")


@dataclass(frozen=True, slots=True)
class InputIdentity:
    """A declared immutable reference, distinct from evidence of actual processing."""

    artifact_id: EventId | ArtifactId
    content_hash: ContentHash

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_id, EventId | ArtifactId):
            raise ValueError("input identity requires EventId or ArtifactId")
        if not isinstance(self.content_hash, ContentHash):
            raise ValueError("input identity requires a pinned ContentHash")


def require_inputs(inputs: tuple[InputIdentity, ...], field: str) -> None:
    if type(inputs) is not tuple or any(not isinstance(item, InputIdentity) for item in inputs):
        raise ValueError(f"{field} must be a tuple of immutable input identities")
    if len({item.artifact_id for item in inputs}) != len(inputs):
        raise ValueError(f"{field} must not repeat an artifact identity")


class RunRelationKind(Enum):
    RESUMES_FROM = "RESUMES_FROM"


@dataclass(frozen=True, slots=True)
class RunRelation:
    run_id: RunId
    predecessor_id: RunId
    kind: RunRelationKind

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, RunId) or not isinstance(self.predecessor_id, RunId):
            raise ValueError("run relation requires RunId identities")
        if self.run_id == self.predecessor_id:
            raise ValueError("restart must not reuse the predecessor RunId")
        if not isinstance(self.kind, RunRelationKind):
            raise ValueError("run relation requires an explicit relation kind")


@dataclass(frozen=True, slots=True)
class RunManifest:
    """Start descriptor only; a declared input is not a ProcessingReceipt."""

    run_id: RunId
    started_at: datetime
    code_revision: CodeRevision
    config_hash: ConfigHash
    inputs: tuple[InputIdentity, ...]
    relation: RunRelation | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, RunId):
            raise ValueError("manifest requires RunId")
        require_utc(self.started_at, "started_at")
        if not isinstance(self.code_revision, CodeRevision):
            raise ValueError("manifest requires pinned CodeRevision")
        if not isinstance(self.config_hash, ConfigHash):
            raise ValueError("manifest requires pinned ConfigHash")
        require_inputs(self.inputs, "manifest inputs")
        if self.relation is not None:
            if not isinstance(self.relation, RunRelation) or self.relation.run_id != self.run_id:
                raise ValueError("manifest relation must identify this run")


def start_run(
    *,
    started_at: datetime,
    code_revision: CodeRevision,
    config_hash: ConfigHash,
    inputs: tuple[InputIdentity, ...],
) -> RunManifest:
    """Allocate a new run; all resolved context and time are explicit caller inputs."""
    return RunManifest(RunId(str(uuid4())), started_at, code_revision, config_hash, inputs)


def restart_run(
    previous: RunManifest,
    *,
    started_at: datetime,
    code_revision: CodeRevision,
    config_hash: ConfigHash,
    inputs: tuple[InputIdentity, ...],
) -> RunManifest:
    """Record continuity without reusing identity or silently inheriting old context."""
    if not isinstance(previous, RunManifest):
        raise ValueError("restart requires a predecessor manifest")
    require_utc(started_at, "started_at")
    if started_at < previous.started_at:
        raise ValueError("restart must not precede predecessor start")
    run_id = RunId(str(uuid4()))
    relation = RunRelation(run_id, previous.run_id, RunRelationKind.RESUMES_FROM)
    return RunManifest(run_id, started_at, code_revision, config_hash, inputs, relation)


class RunOutcome(Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


@dataclass(frozen=True, slots=True)
class RunCompletionRecord:
    """Terminal observation is separate from the immutable start descriptor."""

    run_id: RunId
    completed_at: datetime
    outcome: RunOutcome

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, RunId):
            raise ValueError("completion requires RunId")
        require_utc(self.completed_at, "completed_at")
        if not isinstance(self.outcome, RunOutcome):
            raise ValueError("completion requires an explicit outcome")


def complete_run(
    manifest: RunManifest, *, completed_at: datetime, outcome: RunOutcome
) -> RunCompletionRecord:
    if not isinstance(manifest, RunManifest):
        raise ValueError("completion requires the start manifest")
    require_utc(completed_at, "completed_at")
    if completed_at < manifest.started_at:
        raise ValueError("completion must not precede run start")
    return RunCompletionRecord(manifest.run_id, completed_at, outcome)


@dataclass(frozen=True, slots=True)
class CaptureContext:
    run_id: RunId
    code_revision: CodeRevision
    config_hash: ConfigHash
    provider: ProvenanceLabel

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, RunId):
            raise ValueError("capture requires RunId")
        if not isinstance(self.code_revision, CodeRevision):
            raise ValueError("capture requires pinned CodeRevision")
        if not isinstance(self.config_hash, ConfigHash):
            raise ValueError("capture requires pinned ConfigHash")
        if not isinstance(self.provider, ProvenanceLabel):
            raise ValueError("capture requires a logical provider label")

    @classmethod
    def from_manifest(cls, manifest: RunManifest, provider: ProvenanceLabel) -> "CaptureContext":
        if not isinstance(manifest, RunManifest):
            raise ValueError("capture requires the start manifest")
        return cls(manifest.run_id, manifest.code_revision, manifest.config_hash, provider)


@dataclass(frozen=True, slots=True)
class ProcessingReceipt:
    """Fact x run x component/stage; never mutates or renames the referenced fact."""

    receipt_id: ReceiptId
    input_identity: InputIdentity
    run_id: RunId
    component: ProvenanceLabel
    stage: ProvenanceLabel
    started_at: datetime
    completed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.receipt_id, ReceiptId):
            raise ValueError("processing receipt requires ReceiptId")
        if not isinstance(self.input_identity, InputIdentity):
            raise ValueError("processing receipt requires immutable input identity")
        if not isinstance(self.run_id, RunId):
            raise ValueError("processing receipt requires RunId")
        if not isinstance(self.component, ProvenanceLabel) or not isinstance(
            self.stage, ProvenanceLabel
        ):
            raise ValueError("processing component and stage require logical labels")
        require_utc(self.started_at, "processing started_at")
        require_utc(self.completed_at, "processing completed_at")
        if self.completed_at < self.started_at:
            raise ValueError("processing completion must not precede processing start")
