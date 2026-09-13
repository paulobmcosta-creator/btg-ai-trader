"""Mutation tests for the read-only Foundation integrity verifier."""

from pathlib import Path

from scripts.check_foundation_contract import (
    ENTRY_PATH,
    FROZEN_BLOBS,
    git_blob_sha,
    verify_entry_contract,
    verify_foundation,
)

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_remote_snapshot_and_counters_pass() -> None:
    assert verify_foundation(ROOT) == []


def test_whitespace_mutation_changes_byte_identity() -> None:
    original = (ROOT / ENTRY_PATH).read_bytes()
    assert git_blob_sha(original) == FROZEN_BLOBS[ENTRY_PATH]
    assert git_blob_sha(original + b"\n") != FROZEN_BLOBS[ENTRY_PATH]


def test_duplicate_clause_is_rejected_even_when_unique_set_matches() -> None:
    original = (ROOT / ENTRY_PATH).read_text(encoding="utf-8")
    clause = next(line for line in original.splitlines() if line.startswith("| **S1-EC-001**"))
    assert verify_entry_contract(original + "\n" + clause)


def test_missing_clause_and_changed_type_are_rejected() -> None:
    original = (ROOT / ENTRY_PATH).read_text(encoding="utf-8")
    clause = next(line for line in original.splitlines() if line.startswith("| **S1-EC-001**"))
    assert verify_entry_contract(original.replace(clause, ""))
    changed = clause.replace("`ENTRY_PRECONDITION`", "`EXIT_CRITERION`")
    assert verify_entry_contract(original.replace(clause, changed))


def test_dd_cardinality_is_not_a_substitute_for_identity() -> None:
    original = (ROOT / ENTRY_PATH).read_text(encoding="utf-8")
    changed = original.replace(
        "DD-01, DD-02, DD-03, DD-04, DD-20",
        "DD-99, DD-02, DD-03, DD-04, DD-20",
        1,
    )
    assert verify_entry_contract(changed)


def test_missing_artifacts_fail_closed_without_writes(tmp_path: Path) -> None:
    errors = verify_foundation(tmp_path)
    assert len(errors) == 6
    assert list(tmp_path.iterdir()) == []
