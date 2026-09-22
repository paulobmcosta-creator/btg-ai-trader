"""Tests for the Sprint 6 capability/security boundary scanner."""

from pathlib import Path

from scripts.check_s6_boundary import Finding, _scan_ast, _scan_text, main, scan_file, scan_tree

import ast


def test_finding_and_clean_tree(tmp_path: Path) -> None:
    finding = Finding("a.py", 3, "rule")
    assert str(finding) == "a.py:3: rule"
    clean = tmp_path / "clean.py"
    clean.write_text("from decimal import Decimal\nx = Decimal('1')\n", encoding="utf-8")
    assert scan_tree(tmp_path) == []
    assert main() == 0


def test_scanner_rejects_forbidden_imports_calls_and_operational_names(tmp_path: Path) -> None:
    source = """
import requests
import subprocess
from btg_ai_trader.ml_engine import ModelTrainer
import importlib

def bad():
    requests.get("https://example.com")
    subprocess.run(["echo", "x"])
    importlib.import_module("x")
    eval("1")
    x = RiskAuthorization
    return x
"""
    path = tmp_path / "bad.py"
    tree = ast.parse(source)
    findings = _scan_ast(path, tree)
    rules = [finding.rule for finding in findings]
    assert any("forbidden import: requests" in rule for rule in rules)
    assert any("forbidden import: subprocess" in rule for rule in rules)
    assert any("btg_ai_trader.ml_engine" in rule for rule in rules)
    assert any("forbidden external call: requests.get" in rule for rule in rules)
    assert any("forbidden call: subprocess.run" in rule for rule in rules)
    assert any("forbidden call: importlib.import_module" in rule for rule in rules)
    assert any("forbidden call: eval" in rule for rule in rules)
    assert any("forbidden operational name: RiskAuthorization" in rule for rule in rules)


def test_scanner_rejects_stochastic_dynamic_and_credentials(tmp_path: Path) -> None:
    source = """
from uuid import uuid4
import random
import pickle

def bad(payload):
    uuid4()
    random.random()
    pickle.loads(payload)
"""
    path = tmp_path / "unsafe.py"
    path.write_text(source, encoding="utf-8")
    findings = scan_file(path)
    rules = [finding.rule for finding in findings]
    assert any("uuid4" in rule for rule in rules)
    assert any("random" in rule for rule in rules)
    assert any("pickle" in rule for rule in rules)

    text_findings = _scan_text(path, "token = 'AKIA1234567890123456'")
    assert len(text_findings) == 1
    assert "aws-key" in text_findings[0].rule


def test_scanner_handles_syntax_and_encoding_failures(tmp_path: Path) -> None:
    syntax = tmp_path / "syntax.py"
    syntax.write_text("def broken(:", encoding="utf-8")
    assert "syntax error" in scan_file(syntax)[0].rule

    invalid = tmp_path / "invalid.py"
    invalid.write_bytes(b"\xff\xfe")
    assert scan_file(invalid)[0].rule == "file is not valid UTF-8 text"


def test_scanner_rejects_file_symlink(tmp_path: Path) -> None:
    target = tmp_path / "target.py"
    target.write_text("x = 1\n", encoding="utf-8")
    link = tmp_path / "link.py"
    link.symlink_to(target)
    findings = scan_file(link)
    assert findings[0].rule == "symlinks are forbidden"
