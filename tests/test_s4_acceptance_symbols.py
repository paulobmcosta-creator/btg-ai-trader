"""Tests for S4 acceptance symbol verification script (negative and positive).

Verifies that phantom classes, functions, methods, enums, tests, and paths
are detected and rejected, while the real acceptance document passes.
"""

from pathlib import Path

import pytest
from scripts.verify_s4_acceptance_symbols import (
    ACCEPTANCE_DOC,
    BANNED_PHANTOM_SYMBOLS,
    run_symbol_verification,
    verify_acceptance_symbols,
)


def test_phantom_class_negative(tmp_path: Path) -> None:
    doc = tmp_path / "acceptance.md"
    doc.write_text("Reference to `ImaginaryBaselineModel` in test.", encoding="utf-8")
    code, diffs = run_symbol_verification(doc_path=doc)
    assert code == 1
    assert "ImaginaryBaselineModel" in diffs["classes"]


def test_phantom_function_negative(tmp_path: Path) -> None:
    doc = tmp_path / "acceptance.md"
    doc.write_text("Reference to `imaginary_metric_function()` in test.", encoding="utf-8")
    code, diffs = run_symbol_verification(doc_path=doc)
    assert code == 1
    assert "imaginary_metric_function" in diffs["functions"]


def test_phantom_method_negative(tmp_path: Path) -> None:
    doc = tmp_path / "acceptance.md"
    doc.write_text("Reference to `ConstantBaseline.imaginary_method()` in test.", encoding="utf-8")
    code, diffs = run_symbol_verification(doc_path=doc)
    assert code == 1
    assert "ConstantBaseline.imaginary_method" in diffs["methods"]


def test_phantom_enum_negative(tmp_path: Path) -> None:
    doc = tmp_path / "acceptance.md"
    doc.write_text("Reference to `WindowPolicy.IMAGINARY` in test.", encoding="utf-8")
    code, diffs = run_symbol_verification(doc_path=doc)
    assert code == 1
    assert "WindowPolicy.IMAGINARY" in diffs["enum_members"]


def test_phantom_test_negative(tmp_path: Path) -> None:
    doc = tmp_path / "acceptance.md"
    doc.write_text("Reference to `test_imaginary_acceptance_evidence` in test.", encoding="utf-8")
    code, diffs = run_symbol_verification(doc_path=doc)
    assert code == 1
    assert "test_imaginary_acceptance_evidence" in diffs["tests"]


def test_phantom_path_negative(tmp_path: Path) -> None:
    doc = tmp_path / "acceptance.md"
    doc.write_text("Reference to `docs/program/DOES_NOT_EXIST.md` in test.", encoding="utf-8")
    code, diffs = run_symbol_verification(doc_path=doc)
    assert code == 1
    assert "docs/program/DOES_NOT_EXIST.md" in diffs["paths"]


@pytest.mark.parametrize("banned", BANNED_PHANTOM_SYMBOLS)
def test_banned_phantom_symbol_negative(tmp_path: Path, banned: str) -> None:
    doc = tmp_path / "acceptance.md"
    doc.write_text(f"Citation with `{banned}` in text.", encoding="utf-8")
    code, _ = run_symbol_verification(doc_path=doc)
    assert code == 1


def test_real_acceptance_passes() -> None:
    assert ACCEPTANCE_DOC.is_file()
    assert verify_acceptance_symbols(doc_path=ACCEPTANCE_DOC) == 0
    code, diffs = run_symbol_verification(doc_path=ACCEPTANCE_DOC)
    assert code == 0
    assert diffs["paths"] == set()
    assert diffs["classes"] == set()
    assert diffs["functions"] == set()
    assert diffs["methods"] == set()
    assert diffs["enum_members"] == set()
    assert diffs["tests"] == set()
