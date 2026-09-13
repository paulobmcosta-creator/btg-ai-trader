"""Execute invariant mutants against temporary source copies, never canonical source."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import pytest


@dataclass(frozen=True)
class Mutant:
    name: str
    module: str
    before: str
    after: str
    group: str


MUTANTS = (
    Mutant(
        "fifo_returns_newest", "ingestion.py",
        "return TakeResult(queue.items[0], ObservationQueue(snapshot, queue.items[1:]))",
        "return TakeResult(queue.items[-1], ObservationQueue(snapshot, queue.items[1:]))",
        "generated_queue",
    ),
    Mutant(
        "backpressure_counter_stalls", "ingestion.py",
        "backpressure_count=before.backpressure_count + 1",
        "backpressure_count=before.backpressure_count",
        "generated_queue",
    ),
    Mutant(
        "dedup_ignores_payload_conflict", "dedup.py",
        "        event.payload,\n", "        None,\n", "generated_dedup",
    ),
    Mutant(
        "dedup_reports_new_when_full", "dedup.py",
        "return DedupResult(DedupStatus.CAPACITY_EXHAUSTED, incoming, None, state)",
        "return DedupResult(DedupStatus.NEW, incoming, None, state)",
        "generated_dedup",
    ),
    Mutant(
        "codec_accepts_noncanonical", "storage_records.py",
        "if encode_record(record) != data:", "if False:", "generated_canonical_codec",
    ),
    Mutant(
        "codec_ignores_raw_hash", "storage_records.py",
        "if content_hash(self.raw) != self.input_identity.content_hash:",
        "if False:", "generated_canonical_codec",
    ),
    Mutant(
        "admission_allows_duplicate_keys", "admission.py",
        "if key in result:", "if False:", "generated_json_quarantine",
    ),
    Mutant(
        "late_equality_is_late", "dedup.py",
        "if event_time.value < frontier_time.value",
        "if event_time.value <= frontier_time.value",
        "generated_late",
    ),
    Mutant(
        "lineage_allows_cycles", "lineage.py",
        "if visited != len(indegrees):", "if False:", "generated_lineage",
    ),
    Mutant(
        "lineage_allows_hash_rewrite", "lineage.py",
        "if previous is not None and previous != ref.content_hash:",
        "if False:", "generated_lineage",
    ),
)

_BOOTSTRAP = """
import pathlib
import sys
import btg_ai_trader.observer.ingestion as ingestion
import pytest

root = pathlib.Path(sys.argv[1]).resolve()
loaded = pathlib.Path(ingestion.__file__).resolve()
assert loaded.is_relative_to(root), (loaded, root)
raise SystemExit(pytest.main(sys.argv[2:]))
"""


@dataclass(frozen=True)
class Execution:
    returncode: int
    cases: int
    failures: int
    errors: int
    output: str


def _execute_variant(
    directory: Path, repository: Path, mutant: Mutant | None
) -> tuple[Execution, str | None]:
    source = directory / "src"
    source.mkdir(parents=True)
    shutil.copytree(
        repository / "src" / "btg_ai_trader", source / "btg_ai_trader",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    changed_hash = None
    if mutant is not None:
        target = source / "btg_ai_trader" / "observer" / mutant.module
        text = target.read_text(encoding="utf-8")
        assert text.count(mutant.before) == 1, f"ambiguous mutation anchor: {mutant.name}"
        changed = text.replace(mutant.before, mutant.after, 1)
        target.write_text(changed, encoding="utf-8")
        changed_hash = hashlib.sha256(target.read_bytes()).hexdigest()
    property_file = directory / "test_generated_properties.py"
    shutil.copyfile(
        repository / "tests" / "observer" / "test_generated_properties.py", property_file
    )
    report = directory / "results.xml"
    arguments = [
        sys.executable, "-c", _BOOTSTRAP, str(source),
        "-q", "-p", "no:cacheprovider", "--tb=short",
        f"--junitxml={report}", str(property_file),
    ]
    if mutant is not None:
        arguments.extend(("-k", mutant.group))
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(source)
    environment["PYTEST_ADDOPTS"] = ""
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    environment.pop("PYTEST_PLUGINS", None)
    environment.pop("COVERAGE_PROCESS_START", None)
    completed = subprocess.run(
        arguments, cwd=directory, env=environment, capture_output=True,
        text=True, timeout=60, check=False,
    )
    assert report.is_file(), completed.stdout + completed.stderr
    root = ET.parse(report).getroot()
    cases = list(root.iter("testcase"))
    execution = Execution(
        completed.returncode, len(cases),
        sum(case.find("failure") is not None for case in cases),
        sum(case.find("error") is not None for case in cases),
        completed.stdout + completed.stderr,
    )
    return execution, changed_hash


def test_real_mutation_campaign_kills_selected_invariant_faults(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repository = Path(__file__).resolve().parents[2]
    package = repository / "src" / "btg_ai_trader"
    original_hashes = {
        str(path.relative_to(package)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in package.rglob("*.py")
    }
    baseline, _ = _execute_variant(tmp_path / "baseline", repository, None)
    assert baseline.returncode == 0 and baseline.cases == 36, baseline.output
    assert baseline.failures == baseline.errors == 0, baseline.output
    outcomes: list[dict[str, object]] = []
    for mutant in MUTANTS:
        execution, changed_hash = _execute_variant(tmp_path / mutant.name, repository, mutant)
        killed = (
            execution.returncode == 1 and execution.cases == 6
            and execution.failures > 0 and execution.errors == 0
        )
        outcomes.append({
            "name": mutant.name, "group": mutant.group, "changed_sha256": changed_hash,
            "returncode": execution.returncode, "cases": execution.cases,
            "failures": execution.failures, "errors": execution.errors, "killed": killed,
        })
        assert killed, f"mutant survived or harness failed: {mutant.name}\n{execution.output}"
    current_hashes = {
        str(path.relative_to(package)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in package.rglob("*.py")
    }
    assert current_hashes == original_hashes, "canonical package source changed during mutation"
    report = {
        "baseline_cases": baseline.cases, "seeds": 6, "property_groups": 6,
        "mutants": len(outcomes), "killed": sum(item["killed"] is True for item in outcomes),
        "survivors": sum(item["killed"] is not True for item in outcomes),
        "source_sha256": original_hashes, "outcomes": outcomes,
    }
    report_path = tmp_path / "mutation-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    with capsys.disabled():
        print("MUTATION_CAMPAIGN " + json.dumps(report, sort_keys=True), flush=True)
