"""Provenance preserves external identity and explicit immutable context."""

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from itertools import permutations
from typing import cast
from uuid import UUID

import pytest

from btg_ai_trader.observer.envelope import EventEnvelope
from btg_ai_trader.observer.identity import (
    ArtifactId,
    EventId,
    LineageRecordId,
    ReceiptId,
    RunId,
)
from btg_ai_trader.observer.lineage import (
    ArtifactLineageRecord,
    LineageGraph,
    TransformationKind,
)
from btg_ai_trader.observer.provenance import (
    CaptureContext,
    CodeRevision,
    ConfigHash,
    ContentHash,
    InputIdentity,
    ProcessingReceipt,
    ProvenanceLabel,
    RunCompletionRecord,
    RunManifest,
    RunOutcome,
    RunRelation,
    RunRelationKind,
    complete_run,
    restart_run,
    start_run,
)

T0 = datetime(2026, 9, 13, 12, tzinfo=UTC)
CODE = CodeRevision("5158dc3375fd9ed0a311dd745a981fadf2ea643a")
CONFIG = ConfigHash("ab" * 32)


def uuid_text(number: int) -> str:
    return str(UUID(int=number))


def input_ref(number: int, *, external: bool = False) -> InputIdentity:
    identity = EventId(uuid_text(number)) if external else ArtifactId(uuid_text(number))
    return InputIdentity(identity, ContentHash(f"{number:064x}"))


def manifest() -> RunManifest:
    return RunManifest(RunId(uuid_text(1)), T0, CODE, CONFIG, (input_ref(10, external=True),))


def receipt(run: RunManifest, number: int) -> ProcessingReceipt:
    return ProcessingReceipt(
        ReceiptId(uuid_text(number)),
        run.inputs[0],
        run.run_id,
        ProvenanceLabel("observer"),
        ProvenanceLabel("admission"),
        T0,
        T0 + timedelta(seconds=1),
    )


def derivation(
    number: int, sources: tuple[int, ...], targets: tuple[int, ...]
) -> ArtifactLineageRecord:
    return ArtifactLineageRecord(
        LineageRecordId(uuid_text(number)),
        RunId(uuid_text(1)),
        TransformationKind.NORMALIZATION,
        tuple(input_ref(i) for i in sources),
        tuple(input_ref(i) for i in targets),
    )


@pytest.mark.parametrize("alias", ["latest", "current", "production", "", "a" * 39, "A" * 40])
def test_code_revision_rejects_aliases_abbreviation_and_noncanonical_text(alias: str) -> None:
    with pytest.raises(ValueError, match="code_revision"):
        CodeRevision(alias)


@pytest.mark.parametrize("invalid", ["latest", "current", "production", "a" * 63, "A" * 64, None])
def test_hash_references_require_full_sha256(invalid: object) -> None:
    with pytest.raises(ValueError, match="config_hash"):
        ConfigHash(cast(str, invalid))
    with pytest.raises(ValueError, match="content_hash"):
        ContentHash(cast(str, invalid))


def test_input_references_are_typed_and_not_owned_by_a_run() -> None:
    source = input_ref(10, external=True)
    assert isinstance(source.artifact_id, EventId)
    with pytest.raises(ValueError, match="EventId or ArtifactId"):
        InputIdentity(cast(EventId, RunId(uuid_text(10))), source.content_hash)
    with pytest.raises(ValueError, match="ContentHash"):
        InputIdentity(source.artifact_id, cast(ContentHash, "latest"))
    assert "run_id" not in {field.name for field in fields(source)}
    assert "run_id" not in {field.name for field in fields(EventEnvelope)}


def test_manifest_accepts_only_immutable_unique_input_references() -> None:
    run = manifest()
    with pytest.raises(ValueError, match="tuple"):
        replace(run, inputs=cast(tuple[InputIdentity, ...], list(run.inputs)))
    with pytest.raises(ValueError, match="repeat"):
        replace(run, inputs=(*run.inputs, *run.inputs))
    field_name = "inputs"
    with pytest.raises(FrozenInstanceError):
        setattr(run, field_name, ())
    assert run.inputs == manifest().inputs


def test_start_and_restart_allocate_distinct_identities_with_explicit_continuity() -> None:
    runs = [
        start_run(started_at=T0, code_revision=CODE, config_hash=CONFIG, inputs=())
        for _ in range(20)
    ]
    assert len({run.run_id for run in runs}) == 20
    previous = manifest()
    restarted = restart_run(
        previous,
        started_at=T0 + timedelta(seconds=1),
        code_revision=CODE,
        config_hash=ConfigHash("cd" * 32),
        inputs=previous.inputs,
    )
    assert restarted.run_id != previous.run_id
    assert restarted.config_hash != previous.config_hash
    assert restarted.relation == RunRelation(
        restarted.run_id, previous.run_id, RunRelationKind.RESUMES_FROM
    )
    assert previous == manifest()
    with pytest.raises(ValueError, match="predecessor start"):
        restart_run(
            previous,
            started_at=T0 - timedelta(seconds=1),
            code_revision=CODE,
            config_hash=CONFIG,
            inputs=(),
        )


def test_restart_rejects_identity_reuse_even_if_uuid_source_collides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    previous = manifest()
    monkeypatch.setattr(
        "btg_ai_trader.observer.provenance.uuid4", lambda: UUID(previous.run_id.value)
    )
    with pytest.raises(ValueError, match="reuse"):
        restart_run(
            previous, started_at=T0, code_revision=CODE, config_hash=CONFIG, inputs=()
        )


def test_terminal_record_never_mutates_the_start_descriptor() -> None:
    run = manifest()
    completion = complete_run(run, completed_at=T0, outcome=RunOutcome.COMPLETED)
    assert isinstance(completion, RunCompletionRecord)
    assert completion.run_id == run.run_id
    assert run == manifest()
    assert "outcome" not in {field.name for field in fields(run)}
    with pytest.raises(ValueError, match="run start"):
        complete_run(run, completed_at=T0 - timedelta(seconds=1), outcome=RunOutcome.FAILED)


def test_capture_context_pins_code_config_run_and_provider_without_configuration_payload() -> None:
    run = manifest()
    context = CaptureContext.from_manifest(run, ProvenanceLabel("fixture.market-data"))
    assert context.run_id == run.run_id
    assert context.code_revision == run.code_revision
    assert context.config_hash == run.config_hash
    assert context.provider.value == "fixture.market-data"
    assert {field.name for field in fields(context)} == {
        "run_id", "code_revision", "config_hash", "provider"
    }
    field_name = "config_hash"
    with pytest.raises(FrozenInstanceError):
        setattr(context, field_name, CONFIG)
    for value in ("https://host/auth?token=value", "password=value", "/secret/path", "x" * 65):
        with pytest.raises(ValueError, match="label"):
            ProvenanceLabel(value)


def test_multiple_processing_runs_preserve_external_fact_identity() -> None:
    first = manifest()
    second = restart_run(
        first, started_at=T0, code_revision=CODE, config_hash=CONFIG, inputs=first.inputs
    )
    a, b = receipt(first, 100), receipt(second, 101)
    assert a.run_id != b.run_id
    assert a.input_identity is b.input_identity
    assert a.input_identity == input_ref(10, external=True)
    assert a.receipt_id != b.receipt_id
    assert first.inputs == manifest().inputs
    with pytest.raises(ValueError, match="processing start"):
        replace(a, completed_at=T0 - timedelta(microseconds=1))


def test_lineage_supports_n_to_m_with_roles_without_transforming_raw_inputs() -> None:
    record = replace(
        derivation(100, (10, 11), (20, 21)),
        transformation=TransformationKind.FILTERING,
        input_roles=(ProvenanceLabel("raw"), ProvenanceLabel("raw")),
        output_roles=(ProvenanceLabel("filtered"), ProvenanceLabel("quality")),
    )
    graph = LineageGraph().with_record(record)
    assert len(graph.records[0].inputs) == len(graph.records[0].outputs) == 2
    assert record.inputs == (input_ref(10), input_ref(11))
    with pytest.raises(ValueError, match="roles"):
        replace(record, input_roles=(ProvenanceLabel("raw"),))


def test_lineage_rejects_self_derivation_and_external_identity_as_generated_output() -> None:
    with pytest.raises(ValueError, match="itself"):
        derivation(100, (10,), (10,))
    with pytest.raises(ValueError, match="external EventId"):
        replace(derivation(100, (10,), (20,)), outputs=(input_ref(20, external=True),))


def test_lineage_is_acyclic_independently_of_record_order() -> None:
    records = (
        derivation(100, (10,), (20, 21)),
        derivation(101, (20, 21), (30,)),
        derivation(102, (30,), (40,)),
    )
    for ordered in permutations(records):
        graph = LineageGraph(ordered)
        assert len(graph.records) == 3
        with pytest.raises(ValueError, match="acyclic"):
            graph.with_record(derivation(103, (40,), (10,)))
        assert graph.records == ordered


def test_lineage_rejects_hash_rewrites_duplicate_records_and_reused_produced_artifacts() -> None:
    original = derivation(100, (10,), (20,))
    graph = LineageGraph((original,))
    with pytest.raises(ValueError, match="unique"):
        graph.with_record(original)
    conflicting = replace(
        derivation(101, (20,), (30,)),
        inputs=(InputIdentity(ArtifactId(uuid_text(20)), ContentHash("ff" * 32)),),
    )
    with pytest.raises(ValueError, match="content hash"):
        graph.with_record(conflicting)
    with pytest.raises(ValueError, match="production record"):
        graph.with_record(derivation(102, (30,), (20,)))
    assert graph.records == (original,)


def test_lineage_refuses_mutable_container_and_empty_derivations() -> None:
    record = derivation(100, (10,), (20,))
    with pytest.raises(ValueError, match="tuple"):
        LineageGraph(cast(tuple[ArtifactLineageRecord, ...], [record]))
    with pytest.raises(ValueError, match="nonempty"):
        replace(record, inputs=())
    field_name = "records"
    graph = LineageGraph((record,))
    with pytest.raises(FrozenInstanceError):
        setattr(graph, field_name, ())


def test_manifest_relation_must_belong_to_the_described_run() -> None:
    run = manifest()
    foreign = RunRelation(
        RunId(uuid_text(2)), RunId(uuid_text(3)), RunRelationKind.RESUMES_FROM
    )
    with pytest.raises(ValueError, match="identify this run"):
        replace(run, relation=foreign)
    assert run.relation is None
    assert foreign.run_id == RunId(uuid_text(2))


def test_pinned_reference_wrappers_cannot_be_interchanged() -> None:
    run = manifest()
    context = CaptureContext.from_manifest(run, ProvenanceLabel("fixture"))
    content_hash = ContentHash(CONFIG.value)
    for value in (run, context):
        with pytest.raises(ValueError, match="pinned CodeRevision"):
            replace(value, code_revision=cast(CodeRevision, CONFIG))
        with pytest.raises(ValueError, match="pinned ConfigHash"):
            replace(value, config_hash=cast(ConfigHash, content_hash))
    with pytest.raises(ValueError, match="pinned ContentHash"):
        InputIdentity(run.inputs[0].artifact_id, cast(ContentHash, CONFIG))
    assert context.config_hash == run.config_hash == CONFIG


@pytest.mark.parametrize(
    "invalid",
    [
        T0.replace(tzinfo=None),
        T0.astimezone(timezone(timedelta(hours=-3))),
        None,
        "2026-09-13T12:00:00Z",
    ],
)
def test_lifecycle_factories_reject_non_utc_and_unparsed_timestamps(invalid: object) -> None:
    run = manifest()
    timestamp = cast(datetime, invalid)
    with pytest.raises(ValueError, match="UTC-aware"):
        start_run(started_at=timestamp, code_revision=CODE, config_hash=CONFIG, inputs=())
    with pytest.raises(ValueError, match="UTC-aware"):
        restart_run(
            run, started_at=timestamp, code_revision=CODE, config_hash=CONFIG, inputs=()
        )
    with pytest.raises(ValueError, match="UTC-aware"):
        complete_run(run, completed_at=timestamp, outcome=RunOutcome.STOPPED)
    original = receipt(run, 100)
    with pytest.raises(ValueError, match="UTC-aware"):
        replace(original, started_at=timestamp)
    with pytest.raises(ValueError, match="UTC-aware"):
        replace(original, completed_at=timestamp)
    assert run == manifest()
    assert original.started_at == T0


def test_run_relation_rejects_other_identity_and_untyped_relation_kind() -> None:
    run_id = RunId(uuid_text(1))
    with pytest.raises(ValueError, match="RunId identities"):
        RunRelation(
            run_id, cast(RunId, EventId(uuid_text(2))), RunRelationKind.RESUMES_FROM
        )
    with pytest.raises(ValueError, match="relation kind"):
        RunRelation(run_id, RunId(uuid_text(2)), cast(RunRelationKind, "RESUMES_FROM"))
