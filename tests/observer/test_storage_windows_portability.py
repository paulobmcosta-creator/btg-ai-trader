"""Windows portability checks for technical evidence publication."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

import btg_ai_trader.observer.storage as storage_module
from btg_ai_trader.observer.identity import EventId
from btg_ai_trader.observer.provenance import InputIdentity
from btg_ai_trader.observer.storage import PersistenceStatus, TechnicalEvidenceStore
from btg_ai_trader.observer.storage_records import EvidenceRecord, PersistenceRecordId, content_hash

T0 = datetime(2026, 9, 15, 12, tzinfo=UTC)


def _evidence() -> EvidenceRecord:
    raw = b"windows-portability"
    return EvidenceRecord(
        PersistenceRecordId(str(UUID(int=1))),
        InputIdentity(EventId(str(UUID(int=2))), content_hash(raw)),
        T0,
        raw,
    )


def test_directory_descriptor_sync_support_tracks_platform() -> None:
    assert storage_module._directory_descriptor_sync_supported() is (storage_module.os.name != "nt")


def test_directory_sync_does_not_open_directory_when_unsupported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(storage_module, "_directory_descriptor_sync_supported", lambda: False)

    def unexpected_open(*args: object, **kwargs: object) -> int:
        raise AssertionError("directory os.open must not run on unsupported platforms")

    monkeypatch.setattr(storage_module.os, "open", unexpected_open)
    storage_module._sync_directory(tmp_path)


def test_exclusive_publication_succeeds_without_directory_descriptor_sync(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "archive"
    journal = tmp_path / "journal"
    archive.mkdir()
    journal.mkdir()
    monkeypatch.setattr(storage_module, "_directory_descriptor_sync_supported", lambda: False)
    store = TechnicalEvidenceStore(
        archive_root=archive,
        journal_root=journal,
        max_record_bytes=8192,
    )
    record = _evidence()

    receipt = store.append_evidence(record)

    assert receipt.status is PersistenceStatus.SYNC_REQUESTS_COMPLETED
    assert store.resolve_evidence(record.record_id, receipt.record_hash) == record
