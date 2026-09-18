"""Tests for S5 acceptance symbol verification script (negative and positive).

Verifies that phantom classes, functions, methods, enums, tests, and paths
are detected and rejected.
"""

from pathlib import Path

from scripts.verify_s5_acceptance_symbols import (
    BANNED_PHANTOM_SYMBOLS,
    run_symbol_verification,
    verify_acceptance_symbols,
)


def test_phantom_class_negative(tmp_path: Path) -> None:
    doc = tmp_path / "acceptance.md"
    doc.write_text("Reference to `ImaginaryMLModel` in test.", encoding="utf-8")
    code, diffs = run_symbol_verification(doc_path=doc)
    assert code == 1
    assert "ImaginaryMLModel" in diffs["classes"]


def test_phantom_function_negative(tmp_path: Path) -> None:
    doc = tmp_path / "acceptance.md"
    doc.write_text("Reference to `imaginary_ml_function()` in test.", encoding="utf-8")
    code, diffs = run_symbol_verification(doc_path=doc)
    assert code == 1
    assert "imaginary_ml_function" in diffs["functions"]


def test_phantom_method_negative(tmp_path: Path) -> None:
    doc = tmp_path / "acceptance.md"
    doc.write_text("Reference to `ModelTrainer.imaginary_method()` in test.", encoding="utf-8")
    code, diffs = run_symbol_verification(doc_path=doc)
    assert code == 1
    assert "ModelTrainer.imaginary_method" in diffs["methods"]


def test_phantom_enum_negative(tmp_path: Path) -> None:
    doc = tmp_path / "acceptance.md"
    doc.write_text("Reference to `FeatureType.IMAGINARY` in test.", encoding="utf-8")
    code, diffs = run_symbol_verification(doc_path=doc)
    assert code == 1
    assert "FeatureType.IMAGINARY" in diffs["enum_members"]


def test_phantom_test_negative(tmp_path: Path) -> None:
    doc = tmp_path / "acceptance.md"
    doc.write_text("Reference to `test_imaginary_s5_evidence` in test.", encoding="utf-8")
    code, diffs = run_symbol_verification(doc_path=doc)
    assert code == 1
    assert "test_imaginary_s5_evidence" in diffs["tests"]


def test_phantom_path_negative(tmp_path: Path) -> None:
    doc = tmp_path / "acceptance.md"
    doc.write_text("Reference to `docs/program/DOES_NOT_EXIST.md` in test.", encoding="utf-8")
    code, diffs = run_symbol_verification(doc_path=doc)
    assert code == 1
    assert "docs/program/DOES_NOT_EXIST.md" in diffs["paths"]


def test_banned_phantom_symbol_negative(tmp_path: Path) -> None:
    for banned in BANNED_PHANTOM_SYMBOLS:
        doc = tmp_path / f"banned_{banned}.md"
        doc.write_text(f"Text mentioning {banned} here.", encoding="utf-8")
        code, _ = run_symbol_verification(doc_path=doc)
        assert code == 1


def test_missing_acceptance_document_returns_failure(tmp_path: Path) -> None:
    missing = tmp_path / "non_existent.md"
    code = verify_acceptance_symbols(doc_path=missing)
    assert code == 1
