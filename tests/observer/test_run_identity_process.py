"""Cross-process evidence for fresh RunId allocation on independent S1 starts."""

_CHILD = """
from datetime import UTC, datetime
from btg_ai_trader.observer.provenance import CodeRevision, ConfigHash, start_run
manifest = start_run(
    started_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    code_revision=CodeRevision('a' * 40),
    config_hash=ConfigHash('b' * 64),
    inputs=(),
)
print(manifest.run_id.value)
"""


def _child_run_id() -> str:
    import subprocess
    import sys

    completed = subprocess.run(
        [sys.executable, "-c", _CHILD],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def test_independent_process_starts_allocate_distinct_canonical_run_ids() -> None:
    import uuid

    # Separate interpreter processes exercise the actual uuid4-backed start_run boundary.
    # This is empirical collision/regression evidence, not a mathematical uniqueness proof.
    values = [_child_run_id() for _ in range(8)]
    assert len(set(values)) == len(values)
    assert all(str(uuid.UUID(value)) == value for value in values)
