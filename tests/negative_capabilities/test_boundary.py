"""Adversarial structural fixtures; composition NEG-CAP runtime is still pending."""

import hashlib
import json
from pathlib import Path

import pytest
from scripts.check_s1_boundary import (
    MANIFEST,
    check_packaging,
    check_sources,
    main,
    possible_secrets,
    verify,
)

ROOT = Path(__file__).resolve().parents[2]
PATH = "src/btg_ai_trader/observer/sample.py"


def git_blob(data: bytes) -> str:
    return hashlib.sha1(
        f"blob {len(data)}\0".encode() + data, usedforsecurity=False
    ).hexdigest()


def repin(root: Path) -> None:
    paths = [root / "pyproject.toml", root / ".python-version"]
    paths.extend(path for folder in ("src", "config")
                 for path in (root / folder).rglob("*") if path.is_file())
    pins = {path.relative_to(root).as_posix(): git_blob(path.read_bytes()) for path in paths}
    manifest = root / MANIFEST
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({
        "schema": 1, "assembly_revision": "fixture-only", "composition_status": "PENDING",
        "files": pins,
    }), encoding="utf-8")


@pytest.fixture
def fixture_root(tmp_path: Path) -> Path:
    source = tmp_path / PATH
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "config").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\ndependencies = []\n")
    (tmp_path / ".python-version").write_text("3.12\n")
    repin(tmp_path)
    return tmp_path


def test_reviewed_inventory_ast_config_and_secret_subset() -> None:
    assert verify(ROOT) == []


@pytest.mark.parametrize(
    "source",
    [
        "import subprocess as innocent\ninnocent.run(['x'])\n",
        "import os as harmless\nrunner = harmless.system\nrunner('x')\n",
        "from os import system as harmless\nharmless('x')\n",
        "from btg_ai_trader.research.replay import clock\n",
        "from json import *\n",
        "from . import concealed\n",
        "run = __import__\nrun('os')\n",
        "run = eval\nrun('1')\n",
        "exec('x = 1')\n",
        "get = getattr\nget(object(), 'run')()\n",
        "getattr(object(), 'run')()\n",
        "type('Dynamic', (), {})\n",
        "object().__class__.__subclasses__()\n",
        "class OrderIntent:\n    pass\n",
        "import os\ndef hidden(os):\n    return os.system('x')\n",
        "import os\nos = object()\n",
        "import os\nos.link = lambda *args: None\n",
    ],
)
def test_structural_mutants_fail_even_after_repinning(
    fixture_root: Path, source: str
) -> None:
    (fixture_root / PATH).write_text(source, encoding="utf-8")
    repin(fixture_root)
    findings = verify(fixture_root)
    assert findings
    assert all(finding.rule != "scope-blob-mismatch" for finding in findings)
    assert check_sources({PATH: source})


def test_import_alias_allowance_is_resolved_by_ast() -> None:
    assert check_sources({PATH: "import json as codec\nvalue = codec.loads('{}')\n"}) == []
    assert check_sources({PATH: "import json as codec\nvalue = codec.load('x')\n"})


def test_literal_field_validation_is_not_unbounded_capability_reflection() -> None:
    path = "src/btg_ai_trader/observer/envelope.py"
    allowed = (
        "def validate(self):\n"
        "    for field in ('envelope_version', 'schema_version'):\n"
        "        value = getattr(self, field)\n"
        "        if value != 1: raise ValueError('version')\n"
    )
    assert check_sources({path: allowed}) == []
    changed_field = allowed.replace("'schema_version'", "'order_send'")
    assert check_sources({path: changed_field})
    invoked = allowed.replace("if value != 1: raise ValueError('version')", "value()")
    assert check_sources({path: invoked})
    overwritten = allowed.replace("value = getattr", "field = 'run'\n        value = getattr")
    assert check_sources({path: overwritten})


def test_inventory_rejects_unlisted_modified_and_missing_files(fixture_root: Path) -> None:
    original = (fixture_root / PATH).read_text()
    (fixture_root / PATH).write_text(original + "\n")
    assert any(f.rule == "scope-blob-mismatch" for f in verify(fixture_root))
    (fixture_root / PATH).write_text(original)
    extra = fixture_root / "src" / "unreviewed.py"
    extra.write_text("VALUE = 2\n")
    assert any(f.rule == "scope-inventory-mismatch" for f in verify(fixture_root))
    extra.unlink()
    (fixture_root / PATH).unlink()
    assert any(f.rule == "scope-inventory-mismatch" for f in verify(fixture_root))


def test_scope_rejects_symlink_files(fixture_root: Path) -> None:
    original = fixture_root / PATH
    target = fixture_root / "source-copy.py"
    original.rename(target)
    original.symlink_to(target)
    assert any(f.rule == "scope-symlink" for f in verify(fixture_root))


@pytest.mark.parametrize(
    "text",
    [
        "[project]\ndependencies=['execution-sdk']\n",
        "[project]\ndependencies=[]\n[project.scripts]\ntrade='hidden:main'\n",
        "[project]\ndependencies=[]\n[project.gui-scripts]\ntrade='hidden:main'\n",
        "[project]\ndependencies=[]\n[project.entry-points.plugin]\nx='hidden:main'\n",
        "broken ! toml",
        "[unrelated]\nx=1",
    ],
)
def test_runtime_dependency_and_entrypoint_configuration_is_closed(text: str) -> None:
    assert check_packaging(text)


@pytest.mark.parametrize(
    ("path", "template"),
    [
        ("src/sample.py", 'api_key = "{value}"'),
        ("src/sample.py", 'data = {{"password": "{value}"}}'),
        ("config/settings.toml", 'password = "{value}"'),
        (".github/workflows/check.yml", 'auth_token: "{value}"'),
    ],
)
def test_possible_secret_literals_are_detected_without_disclosing_values(
    path: str, template: str
) -> None:
    marker = "synthetic-sensitive-tripwire"
    findings = possible_secrets(path, template.format(value=marker))
    assert findings
    assert marker not in "\n".join(map(str, findings))


@pytest.mark.parametrize(
    "marker",
    ["AKIA" + "A" * 16, "ghp_" + "A" * 36, "sk-" + "a" * 30,
     "-----BEGIN PRIVATE KEY-----", "https://fixture:synthetic@host/"],
)
def test_possible_secret_shapes_are_detected_without_echo(marker: str) -> None:
    findings = possible_secrets("src/sample.py", "VALUE = " + repr(marker))
    assert findings
    assert marker not in repr(findings)


def test_secret_heuristic_allows_reference_without_claiming_general_detection() -> None:
    assert possible_secrets("config/settings.toml", "api_key = \"\"") == []
    reference = "auth_token: \u0024{{ vars.READ_ONLY }}"
    assert possible_secrets(".github/workflows/check.yml", reference) == []
    assert possible_secrets("src/sample.py", "password: str\n") == []


def test_pending_runtime_is_reported_not_skipped_or_claimed_pass(
    fixture_root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["check_s1_boundary.py", "--root", str(fixture_root)])
    assert main() == 0
    output = capsys.readouterr().out
    assert "PASS_SCOPE:" in output
    assert "NEG_RUNTIME_NOT_EXECUTED:" in output
    assert "not an official Security scan" in output


def test_workflow_literal_findings_are_separate_from_main_ast(fixture_root: Path) -> None:
    workflows = fixture_root / ".github/workflows"
    workflows.mkdir(parents=True)
    (workflows / "fixture.yml").write_text("password: synthetic-tripwire\n")
    findings = verify(fixture_root)
    assert any(f.rule == "possible-credential-literal" for f in findings)
    assert all("synthetic-tripwire" not in str(f) for f in findings)
