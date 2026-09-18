"""Tests for Sprint 5 ML Engine capability boundary verifier."""

import ast
from pathlib import Path

from scripts.check_s5_boundary import (
    Finding,
    _call_name,
    _import_name,
    _is_forbidden_import,
    _is_forbidden_stochastic_call,
    _resolve_expr,
    _scan_ast,
    _scan_text,
    main,
    scan_file,
    scan_tree,
)


def test_finding_str_representation() -> None:
    f = Finding("path/to/file.py", 42, "violation rule")
    assert str(f) == "path/to/file.py:42: violation rule"


def test_import_name_edge_cases() -> None:
    imp = ast.Import(names=[])
    assert _import_name(imp) == ""
    imp_from = ast.ImportFrom(module=None, names=[ast.alias(name="bar")], level=0)
    assert _import_name(imp_from) == ""


def test_call_name_edge_cases() -> None:
    call_subscript = ast.Call(
        func=ast.Subscript(
            value=ast.Name(id="f", ctx=ast.Load()),
            slice=ast.Constant(value=0),
            ctx=ast.Load(),
        ),
        args=[],
        keywords=[],
    )
    assert _call_name(call_subscript) == ""

    call_name = ast.Call(func=ast.Name(id="func_name", ctx=ast.Load()), args=[], keywords=[])
    assert _call_name(call_name) == "func_name"

    call_chained = ast.Call(
        func=ast.Attribute(
            value=ast.Attribute(
                value=ast.Name(id="a", ctx=ast.Load()),
                attr="b",
                ctx=ast.Load(),
            ),
            attr="c",
            ctx=ast.Load(),
        ),
        args=[],
        keywords=[],
    )
    assert _call_name(call_chained) == "a.b.c"


def test_is_forbidden_import() -> None:
    assert _is_forbidden_import("MetaTrader5")
    assert _is_forbidden_import("MetaTrader5.order_send")
    assert _is_forbidden_import("torch")
    assert _is_forbidden_import("torch.nn")
    assert _is_forbidden_import("tensorflow")
    assert _is_forbidden_import("optuna")
    assert _is_forbidden_import("mlflow")
    assert not _is_forbidden_import("sklearn")
    assert not _is_forbidden_import("numpy")


def test_is_forbidden_stochastic_call() -> None:
    assert _is_forbidden_stochastic_call("uuid4")
    assert _is_forbidden_stochastic_call("uuid.uuid4")
    assert _is_forbidden_stochastic_call("secrets.token_hex")
    assert _is_forbidden_stochastic_call("os.urandom")
    assert not _is_forbidden_stochastic_call("int")


def test_resolve_expr() -> None:
    mod_aliases = {"np": "numpy"}
    sym_aliases = {"r_int": "random.randint"}
    node_name = ast.Name(id="np", ctx=ast.Load())
    assert _resolve_expr(node_name, mod_aliases, sym_aliases) == "numpy"

    node_sym = ast.Name(id="r_int", ctx=ast.Load())
    assert _resolve_expr(node_sym, mod_aliases, sym_aliases) == "random.randint"

    node_unresolved = ast.Name(id="other", ctx=ast.Load())
    assert _resolve_expr(node_unresolved, mod_aliases, sym_aliases) == "other"

    node_attr = ast.Attribute(
        value=ast.Name(id="np", ctx=ast.Load()),
        attr="zeros",
        ctx=ast.Load(),
    )
    assert _resolve_expr(node_attr, mod_aliases, sym_aliases) == "numpy.zeros"


def test_scan_text_secrets() -> None:
    path = Path("fake.py")
    findings = _scan_text(path, "key = 'AKIA1234567890123456'")
    assert len(findings) == 1
    assert "suspected credential pattern: aws-key" in findings[0].rule


def test_scan_file_edge_cases(tmp_path: Path) -> None:
    py_file = tmp_path / "syntax_error.py"
    py_file.write_text("def invalid_syntax(:", encoding="utf-8")
    findings = scan_file(py_file)
    assert len(findings) == 1
    assert "syntax error" in findings[0].rule

    non_utf8 = tmp_path / "bad.py"
    non_utf8.write_bytes(b"\xff\xfe\x00\x00")
    findings = scan_file(non_utf8)
    assert len(findings) == 1
    assert "file is not valid UTF-8 text" in findings[0].rule


def test_scan_ast_forbidden_patterns(tmp_path: Path) -> None:
    code = """
import MetaTrader5
import torch
import secrets
from os import urandom
import subprocess
from time import sleep

def bad_func():
    subprocess.run(['ls'])
    sleep(1)
    secret_key = 'fake_key_123'
    x = order_send()
"""
    py_file = tmp_path / "bad_code.py"
    py_file.write_text(code, encoding="utf-8")
    tree = ast.parse(code)
    findings = _scan_ast(py_file, tree)

    rules = [f.rule for f in findings]
    assert any("forbidden import: MetaTrader5" in r for r in rules)
    assert any("forbidden import: torch" in r for r in rules)
    assert any("forbidden stochastic import: secrets" in r for r in rules)
    assert any("forbidden stochastic import: os.urandom" in r for r in rules)
    assert any("forbidden wall-clock call: time.sleep" in r for r in rules)
    assert any("forbidden process call: subprocess.run" in r for r in rules)
    assert any("forbidden operational name: order_send" in r for r in rules)


def test_scan_tree_and_main(tmp_path: Path) -> None:
    clean_code = "import numpy as np\nprint('clean')\n"
    py_file = tmp_path / "clean.py"
    py_file.write_text(clean_code, encoding="utf-8")
    findings = scan_tree(tmp_path)
    assert len(findings) == 0

    assert main() == 0
