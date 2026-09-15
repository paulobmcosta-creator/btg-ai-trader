"""Single-writer technical files with exclusive publication, not a financial journal."""

import os
import stat
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from btg_ai_trader.observer.provenance import ContentHash
from btg_ai_trader.observer.storage_records import (
    EvidenceRecord,
    PersistenceRecordId,
    TechnicalJournalRecord,
    TechnicalRecord,
    content_hash,
    decode_record,
    encode_record,
)


class StorageIntegrityError(ValueError):
    """Existing evidence is conflicting, malformed or not a regular record."""


class WriteFailed(OSError):
    """Failure before publication was attempted; no success receipt is issued."""


class WriteUncertain(OSError):
    """Resolve this same logical identity/hash; never blindly allocate a new identity."""

    def __init__(self, record_id: PersistenceRecordId, expected_hash: ContentHash) -> None:
        super().__init__("publication outcome unknown; resolve the same identity and hash")
        self.record_id = record_id
        self.expected_hash = expected_hash


class PersistenceStatus(Enum):
    SYNC_REQUESTS_COMPLETED = "SYNC_REQUESTS_COMPLETED"
    ALREADY_PRESENT = "ALREADY_PRESENT"


@dataclass(frozen=True, slots=True)
class PersistenceReceipt:
    record_id: PersistenceRecordId
    record_hash: ContentHash
    status: PersistenceStatus


def _controlled_root(path: Path) -> Path:
    if not isinstance(path, Path):
        raise ValueError("root must be an explicit Path")
    absolute = path.absolute()
    if any(part.is_symlink() for part in (absolute, *absolute.parents)):
        raise ValueError("root and ancestors must not be symlinks")
    root = absolute.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("root must be an existing controlled directory")
    return root


def _directory_descriptor_sync_supported(root: Path) -> bool:
    """Whether this resolved path uses a directory descriptor shape supported by os.open."""
    return root.drive == ""


def _sync_directory(root: Path) -> None:
    """Request local metadata sync where directory descriptors are supported."""
    if not _directory_descriptor_sync_supported(root):
        return
    descriptor = os.open(root, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class TechnicalEvidenceStore:
    """Preexisting controlled roots, one writer, no hostile concurrent filesystem mutation."""

    def __init__(
        self, *, archive_root: Path, journal_root: Path, max_record_bytes: int
    ) -> None:
        if type(max_record_bytes) is not int or max_record_bytes <= 0:
            raise ValueError("max_record_bytes must be an explicit positive integer")
        archive = _controlled_root(archive_root)
        journal = _controlled_root(journal_root)
        if (
            archive == journal
            or archive in journal.parents
            or journal in archive.parents
            or archive.samefile(journal)
        ):
            raise ValueError("archive and journal roots must be separate and not nested")
        self._archive = archive
        self._journal = journal
        self._max_bytes = max_record_bytes
        self._roots = tuple(
            (root, root.stat().st_dev, root.stat().st_ino) for root in (archive, journal)
        )

    def _check_roots(self) -> None:
        for root, device, inode in self._roots:
            if _controlled_root(root) != root:
                raise StorageIntegrityError("root location changed")
            current = root.stat()
            if (current.st_dev, current.st_ino) != (device, inode):
                raise StorageIntegrityError("root physical identity changed")

    def _read(
        self, root: Path, record_id: PersistenceRecordId
    ) -> tuple[bytes, TechnicalRecord] | None:
        self._check_roots()
        if not isinstance(record_id, PersistenceRecordId):
            raise ValueError("lookup requires a logical persistence identity")
        path = root / (record_id.value + ".json")
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            return None
        if not stat.S_ISREG(metadata.st_mode):
            raise StorageIntegrityError("record must be a regular file, never a symlink")
        with path.open("rb") as stream:
            data = stream.read(self._max_bytes + 1)
        if len(data) > self._max_bytes:
            raise StorageIntegrityError("record exceeds configured byte limit")
        try:
            record = decode_record(data)
        except (ValueError, RecursionError) as error:
            raise StorageIntegrityError("existing record is malformed") from error
        expected_type = EvidenceRecord if root == self._archive else TechnicalJournalRecord
        if not isinstance(record, expected_type) or record.record_id != record_id:
            raise StorageIntegrityError("record identity or persistence plane mismatch")
        return data, record

    def _existing_receipt(
        self, root: Path, record_id: PersistenceRecordId, data: bytes
    ) -> PersistenceReceipt | None:
        existing = self._read(root, record_id)
        if existing is None:
            return None
        if existing[0] != data:
            raise StorageIntegrityError("logical persistence identity has conflicting bytes")
        return PersistenceReceipt(
            record_id, content_hash(data), PersistenceStatus.ALREADY_PRESENT
        )

    def _append(self, root: Path, record: TechnicalRecord) -> PersistenceReceipt:
        data = encode_record(record)
        if len(data) > self._max_bytes:
            raise ValueError("record exceeds configured byte limit")
        existing = self._existing_receipt(root, record.record_id, data)
        if existing is not None:
            return existing
        expected_hash = content_hash(data)
        temporary: Path | None = None
        publication_attempted = False
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=".pending-", dir=root, delete=False
            ) as stream:
                temporary = Path(stream.name)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            self._check_roots()
            publication_attempted = True
            try:
                os.link(temporary, root / (record.record_id.value + ".json"))
            except FileExistsError:
                repeated = self._existing_receipt(root, record.record_id, data)
                if repeated is None:
                    raise WriteUncertain(record.record_id, expected_hash) from None
                return repeated
            _sync_directory(root)
            return PersistenceReceipt(
                record.record_id, expected_hash, PersistenceStatus.SYNC_REQUESTS_COMPLETED
            )
        except OSError as error:
            if publication_attempted:
                raise WriteUncertain(record.record_id, expected_hash) from error
            raise WriteFailed("write failed before publication") from error
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass  # Orphan staging files are not published logical records.

    def append_evidence(self, record: EvidenceRecord) -> PersistenceReceipt:
        if not isinstance(record, EvidenceRecord):
            raise ValueError("archive accepts only EvidenceRecord")
        return self._append(self._archive, record)

    def append_journal(self, record: TechnicalJournalRecord) -> PersistenceReceipt:
        if not isinstance(record, TechnicalJournalRecord):
            raise ValueError("journal accepts only TechnicalJournalRecord")
        return self._append(self._journal, record)

    def _resolve(
        self, root: Path, record_id: PersistenceRecordId, expected_hash: ContentHash
    ) -> TechnicalRecord | None:
        if not isinstance(expected_hash, ContentHash):
            raise ValueError("resolution requires the expected canonical record hash")
        existing = self._read(root, record_id)
        if existing is None:
            return None
        if content_hash(existing[0]) != expected_hash:
            raise StorageIntegrityError("resolved record hash differs from expected hash")
        return existing[1]

    def resolve_evidence(
        self, record_id: PersistenceRecordId, expected_hash: ContentHash
    ) -> EvidenceRecord | None:
        """Observed absence is not proof about a previous write or future durability."""
        result = self._resolve(self._archive, record_id, expected_hash)
        if result is not None and not isinstance(result, EvidenceRecord):
            raise StorageIntegrityError("expected evidence")
        return result

    def resolve_journal(
        self, record_id: PersistenceRecordId, expected_hash: ContentHash
    ) -> TechnicalJournalRecord | None:
        result = self._resolve(self._journal, record_id, expected_hash)
        if result is not None and not isinstance(result, TechnicalJournalRecord):
            raise StorageIntegrityError("expected technical journal")
        return result
