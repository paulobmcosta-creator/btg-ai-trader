"""Technical persistence on a disposable CI filesystem; no financial authority."""

import json
import os
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import UUID

import pytest

from btg_ai_trader.observer.identity import EventId, RunId
from btg_ai_trader.observer.provenance import (
    CaptureContext,
    CodeRevision,
    ConfigHash,
    ContentHash,
    InputIdentity,
    ProvenanceLabel,
)
from btg_ai_trader.observer.storage import (
    PersistenceStatus,
    StorageIntegrityError,
    TechnicalEvidenceStore,
    WriteFailed,
    WriteUncertain,
)
from btg_ai_trader.observer.storage_records import (
    EvidenceRecord,
    PersistenceRecordId,
    TechnicalEventKind,
    TechnicalJournalRecord,
    content_hash,
    decode_record,
    encode_record,
)

T0 = datetime(2026, 9, 13, 12, tzinfo=UTC)


def logical_id(number: int) -> PersistenceRecordId:
    return PersistenceRecordId(str(UUID(int=number)))


def evidence(number: int = 1, raw: bytes = b"raw") -> EvidenceRecord:
    return EvidenceRecord(
        logical_id(number), InputIdentity(EventId(str(UUID(int=10))), content_hash(raw)),
        T0, raw,
    )


def journal(number: int = 1) -> TechnicalJournalRecord:
    return TechnicalJournalRecord(
        logical_id(number), RunId(str(UUID(int=20))), T0,
        TechnicalEventKind.ANOMALY, ProvenanceLabel("fixture-gap"), logical_id(1),
    )


@pytest.fixture
def store(tmp_path: Path) -> TechnicalEvidenceStore:
    (tmp_path / "archive").mkdir()
    (tmp_path / "journal").mkdir()
    return TechnicalEvidenceStore(
        archive_root=tmp_path / "archive", journal_root=tmp_path / "journal",
        max_record_bytes=8192,
    )


@pytest.mark.parametrize("raw", [b"", bytes(range(256)), b"line\n\x00tail", "ação".encode()])
def test_raw_roundtrip_and_capture_context_are_exact(raw: bytes) -> None:
    context = CaptureContext(
        RunId(str(UUID(int=30))), CodeRevision("a" * 40), ConfigHash("b" * 64),
        ProvenanceLabel("fixture"),
    )
    record = replace(evidence(raw=raw), capture=context)
    decoded = decode_record(encode_record(record))
    assert decoded == record
    assert isinstance(decoded, EvidenceRecord)
    assert decoded.raw == raw
    assert decoded.capture == context
    assert decode_record(encode_record(evidence(raw=raw))) == evidence(raw=raw)


def test_planes_are_separate_even_with_the_same_logical_id(
    store: TechnicalEvidenceStore, tmp_path: Path
) -> None:
    source, event = evidence(), journal()
    raw_receipt = store.append_evidence(source)
    journal_receipt = store.append_journal(event)
    assert raw_receipt.status is PersistenceStatus.SYNC_REQUESTS_COMPLETED
    assert journal_receipt.status is PersistenceStatus.SYNC_REQUESTS_COMPLETED
    assert store.resolve_evidence(source.record_id, raw_receipt.record_hash) == source
    assert store.resolve_journal(event.record_id, journal_receipt.record_hash) == event
    assert raw_receipt.record_hash != journal_receipt.record_hash
    assert len(list((tmp_path / "archive").iterdir())) == 1
    assert len(list((tmp_path / "journal").iterdir())) == 1
    with pytest.raises(ValueError, match="only EvidenceRecord"):
        store.append_evidence(cast(EvidenceRecord, event))
    with pytest.raises(ValueError, match="only TechnicalJournalRecord"):
        store.append_journal(cast(TechnicalJournalRecord, source))


def test_idempotence_and_correction_preserve_existing_bytes(
    store: TechnicalEvidenceStore, tmp_path: Path
) -> None:
    original = evidence()
    first = store.append_evidence(original)
    path = tmp_path / "archive" / (original.record_id.value + ".json")
    before = path.read_bytes(), path.stat().st_mtime_ns
    second = store.append_evidence(original)
    assert second.status is PersistenceStatus.ALREADY_PRESENT
    assert second.record_hash == first.record_hash
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before
    with pytest.raises(StorageIntegrityError, match="conflicting"):
        store.append_evidence(replace(original, observed_at=T0.replace(hour=13)))
    corrected = replace(evidence(2, b"corrected"), supersedes=original.record_id)
    receipt = store.append_evidence(corrected)
    assert store.resolve_evidence(corrected.record_id, receipt.record_hash) == corrected
    assert store.resolve_evidence(original.record_id, first.record_hash) == original
    assert path.read_bytes() == before[0]


@pytest.mark.parametrize(
    "case", ["schema", "extra", "raw", "hash", "kind", "timestamp", "duplicate", "pretty"]
)
def test_codec_rejects_incompatible_or_corrupt_representation(case: str) -> None:
    encoded = encode_record(evidence())
    fields = cast(dict[str, object], json.loads(encoded))
    if case == "schema":
        fields["schema"] = True
    elif case == "extra":
        fields["unapproved_metadata"] = {}
    elif case == "raw":
        fields["raw_base64"] = "%%%bad"
    elif case == "hash":
        cast(dict[str, object], fields["input"])["sha256"] = "f" * 64
    elif case == "kind":
        cast(dict[str, object], fields["input"])["kind"] = "run"
    elif case == "timestamp":
        fields["observed_at"] = "2026-09-13T12:00:00"
    elif case == "duplicate":
        with pytest.raises(ValueError, match="duplicate"):
            decode_record(encoded.replace(b'"schema":1', b'"schema":1,"schema":1'))
        return
    elif case == "pretty":
        with pytest.raises(ValueError, match="canonical"):
            decode_record(json.dumps(fields, indent=2).encode())
        return
    invalid = (json.dumps(fields, sort_keys=True, separators=(",", ":")) + "\n").encode()
    with pytest.raises(ValueError):
        decode_record(invalid)


def test_record_construction_rejects_hash_mismatch_and_self_supersession() -> None:
    original = evidence()
    with pytest.raises(ValueError, match="input hash"):
        replace(original, raw=b"different")
    with pytest.raises(ValueError, match="supersede itself"):
        replace(original, supersedes=original.record_id)
    with pytest.raises(ValueError, match="technical event kind"):
        replace(journal(), kind=cast(TechnicalEventKind, "BUY"))
    with pytest.raises(ValueError, match="bounded logical label"):
        replace(journal(), detail=cast(ProvenanceLabel, {"anything": "else"}))


@pytest.mark.parametrize("value", ["../outside", "/tmp/outside", "a" * 32, "", None])
def test_logical_ids_cannot_supply_storage_paths(value: object) -> None:
    with pytest.raises(ValueError):
        PersistenceRecordId(cast(str, value))


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, None])
def test_storage_requires_explicit_positive_integer_limit(tmp_path: Path, limit: object) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        TechnicalEvidenceStore(
            archive_root=tmp_path, journal_root=tmp_path, max_record_bytes=cast(int, limit)
        )


def test_roots_reject_overlap_symlinks_and_aliases(tmp_path: Path) -> None:
    archive, other = tmp_path / "archive", tmp_path / "other"
    nested = archive / "nested"
    archive.mkdir()
    nested.mkdir()
    other.mkdir()
    for journal_root in (archive, nested):
        with pytest.raises(ValueError, match="separate"):
            TechnicalEvidenceStore(
                archive_root=archive, journal_root=journal_root, max_record_bytes=8192
            )
    alias = tmp_path / "alias"
    alias.symlink_to(archive, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinks"):
        TechnicalEvidenceStore(archive_root=alias, journal_root=other, max_record_bytes=8192)
    with pytest.raises(ValueError, match="symlinks"):
        TechnicalEvidenceStore(
            archive_root=alias / "nested", journal_root=other, max_record_bytes=8192
        )


def test_root_replacement_is_detected(store: TechnicalEvidenceStore, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    root.rename(tmp_path / "old")
    root.mkdir()
    with pytest.raises(StorageIntegrityError, match="physical identity"):
        store.append_evidence(evidence())
    assert not list(root.iterdir())


def test_existing_symlink_or_malformed_file_never_counts_as_success(
    store: TechnicalEvidenceStore, tmp_path: Path
) -> None:
    record = evidence()
    path = tmp_path / "archive" / (record.record_id.value + ".json")
    elsewhere = tmp_path / "outside"
    elsewhere.write_bytes(encode_record(record))
    path.symlink_to(elsewhere)
    with pytest.raises(StorageIntegrityError, match="regular file"):
        store.append_evidence(record)
    path.unlink()
    path.write_bytes(b'{"partial"')
    with pytest.raises(StorageIntegrityError, match="malformed"):
        store.append_evidence(record)
    assert path.read_bytes() == b'{"partial"'
    with pytest.raises(StorageIntegrityError, match="malformed"):
        store.resolve_evidence(record.record_id, content_hash(encode_record(record)))


def test_lookup_checks_id_plane_and_expected_hash(
    store: TechnicalEvidenceStore, tmp_path: Path
) -> None:
    record = evidence()
    expected = content_hash(encode_record(record))
    assert store.resolve_evidence(record.record_id, expected) is None
    receipt = store.append_evidence(record)
    with pytest.raises(StorageIntegrityError, match="hash differs"):
        store.resolve_evidence(record.record_id, ContentHash("0" * 64))
    path = tmp_path / "journal" / (record.record_id.value + ".json")
    path.write_bytes(encode_record(record))
    with pytest.raises(StorageIntegrityError, match="plane mismatch"):
        store.resolve_journal(record.record_id, receipt.record_hash)
    path.unlink()
    path = tmp_path / "archive" / (logical_id(2).value + ".json")
    path.write_bytes(encode_record(record))
    with pytest.raises(StorageIntegrityError, match="identity"):
        store.resolve_evidence(logical_id(2), receipt.record_hash)


def test_record_limit_applies_on_write_and_existing_read(tmp_path: Path) -> None:
    archive, journal_root = tmp_path / "archive", tmp_path / "journal"
    archive.mkdir()
    journal_root.mkdir()
    bounded = TechnicalEvidenceStore(
        archive_root=archive, journal_root=journal_root, max_record_bytes=32
    )
    record = evidence()
    with pytest.raises(ValueError, match="byte limit"):
        bounded.append_evidence(record)
    assert not list(archive.iterdir())
    (archive / (record.record_id.value + ".json")).write_bytes(b"x" * 33)
    with pytest.raises(StorageIntegrityError, match="byte limit"):
        bounded.resolve_evidence(record.record_id, content_hash(encode_record(record)))


def test_file_sync_failure_does_not_publish_a_record(
    store: TechnicalEvidenceStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_sync(descriptor: int) -> None:
        raise OSError("fixture sync unavailable")

    monkeypatch.setattr("btg_ai_trader.observer.storage.os.fsync", fail_sync)
    with pytest.raises(WriteFailed, match="before publication"):
        store.append_evidence(evidence())
    assert not list((tmp_path / "archive").iterdir())


def test_lost_publication_response_is_unknown_and_resolvable_without_new_identity(
    store: TechnicalEvidenceStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    link = os.link
    calls = 0

    def link_then_fail(source: Path, target: Path) -> None:
        nonlocal calls
        calls += 1
        link(source, target)
        raise OSError("fixture lost response")

    monkeypatch.setattr("btg_ai_trader.observer.storage.os.link", link_then_fail)
    record = evidence()
    with pytest.raises(WriteUncertain) as failed:
        store.append_evidence(record)
    assert calls == 1
    assert failed.value.record_id == record.record_id
    assert store.resolve_evidence(
        failed.value.record_id, failed.value.expected_hash
    ) == record
    repeated = store.append_evidence(record)
    assert repeated.status is PersistenceStatus.ALREADY_PRESENT
    assert calls == 1


def test_directory_sync_failure_never_claims_completed_sync(
    store: TechnicalEvidenceStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_sync(root: Path) -> None:
        raise OSError("fixture directory sync unavailable")

    monkeypatch.setattr("btg_ai_trader.observer.storage._sync_directory", fail_sync)
    record = journal()
    with pytest.raises(WriteUncertain) as failed:
        store.append_journal(record)
    assert store.resolve_journal(record.record_id, failed.value.expected_hash) == record


def test_link_failure_is_unknown_even_when_lookup_observes_absence(
    store: TechnicalEvidenceStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_link(source: Path, target: Path) -> None:
        raise OSError("fixture unsupported filesystem")

    monkeypatch.setattr("btg_ai_trader.observer.storage.os.link", fail_link)
    with pytest.raises(WriteUncertain) as failed:
        store.append_evidence(evidence())
    assert store.resolve_evidence(failed.value.record_id, failed.value.expected_hash) is None


def test_exclusive_publication_handles_an_existing_identical_record(
    store: TechnicalEvidenceStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = evidence()

    def collide(source: Path, target: Path) -> None:
        target.write_bytes(encode_record(record))
        raise FileExistsError("fixture competing publication")

    monkeypatch.setattr("btg_ai_trader.observer.storage.os.link", collide)
    receipt = store.append_evidence(record)
    assert receipt.status is PersistenceStatus.ALREADY_PRESENT
    assert store.resolve_evidence(record.record_id, receipt.record_hash) == record
