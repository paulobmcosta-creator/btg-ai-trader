"""Tests for Sprint 4 capability boundary verifier."""

import ast
import os
import runpy
import sys
from pathlib import Path

import pytest
from scripts.check_s4_boundary import (
    Finding,
    _call_name,
    _import_name,
    _is_forbidden_stochastic_call,
    _resolve_expr,
    _scan_ast,
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

    call_not_name = ast.Call(
        func=ast.Attribute(value=ast.Constant(value=1), attr="b", ctx=ast.Load()),
        args=[],
        keywords=[],
    )
    assert _call_name(call_not_name) == "b"


def test_is_forbidden_stochastic_call() -> None:
    assert _is_forbidden_stochastic_call("uuid.uuid4") is True
    assert _is_forbidden_stochastic_call("random.randint") is True
    assert _is_forbidden_stochastic_call("urandom.something") is True
    assert _is_forbidden_stochastic_call("math.sin") is False


def test_resolve_expr_edge_cases() -> None:
    mod_aliases = {"np": "numpy"}
    sym_aliases = {"rnd": "random"}

    name_sym = ast.Name(id="rnd", ctx=ast.Load())
    assert _resolve_expr(name_sym, mod_aliases, sym_aliases) == "random"

    name_mod = ast.Name(id="np", ctx=ast.Load())
    assert _resolve_expr(name_mod, mod_aliases, sym_aliases) == "numpy"

    name_plain = ast.Name(id="foo", ctx=ast.Load())
    assert _resolve_expr(name_plain, mod_aliases, sym_aliases) == "foo"

    attr_mod = ast.Attribute(
        value=ast.Name(id="np", ctx=ast.Load()), attr="array", ctx=ast.Load()
    )
    assert _resolve_expr(attr_mod, mod_aliases, sym_aliases) == "numpy.array"

    attr_sym = ast.Attribute(
        value=ast.Name(id="rnd", ctx=ast.Load()), attr="choice", ctx=ast.Load()
    )
    assert _resolve_expr(attr_sym, mod_aliases, sym_aliases) == "random.choice"

    attr_deep = ast.Attribute(
        value=ast.Attribute(value=ast.Name(id="a", ctx=ast.Load()), attr="b", ctx=ast.Load()),
        attr="c",
        ctx=ast.Load(),
    )
    assert _resolve_expr(attr_deep, mod_aliases, sym_aliases) == "a.b.c"

    other_expr = ast.Constant(value=123)
    assert _resolve_expr(other_expr, mod_aliases, sym_aliases) == ""

    attr_not_name = ast.Attribute(value=ast.Constant(value=1), attr="b", ctx=ast.Load())
    assert _resolve_expr(attr_not_name, mod_aliases, sym_aliases) == ""


def test_scan_ast_alias_and_attribute_resolution(tmp_path: Path) -> None:
    source = (
        "import random as rnd\n"
        "import numpy.random as nr\n"
        "from random import choice as ch\n"
        "from os import urandom\n"
        "from uuid import uuid4\n"
        "from random import SystemRandom\n"
        "secret_key = '   '\n"
        "api_key = 12345\n"
        "auth_token = '$ENV_VAR'\n"
        "mod_alias = rnd\n"
        "sym_alias = ch\n"
        "alias_from_sym = sym_alias\n"
        "attr_alias = mod_alias.choice\n"
        "attr_call = attr_alias()\n"
        "unresolved_attr = (1).attr\n"
        "target_attr.foo = 1\n"
        "forbidden_attr = obj.TradeIntent\n"
    )
    tree = ast.parse(source, filename="test.py")
    findings = _scan_ast(tmp_path / "test.py", tree)
    assert len(findings) > 0


def test_allowed_python_file_passes(tmp_path: Path) -> None:
    s4_root = tmp_path / "statistical_baselines"
    s4_root.mkdir(parents=True)
    allowed = s4_root / "allowed.py"
    allowed.write_text(
        "from dataclasses import dataclass\n"
        "from decimal import Decimal\n"
        "@dataclass(frozen=True)\n"
        "class StatisticalSample:\n"
        "    reference_value: Decimal\n",
        encoding="utf-8",
    )
    findings = scan_tree(s4_root)
    assert findings == []


@pytest.mark.parametrize(
    ("filename", "secret_text", "expected_rule"),
    [
        (
            "cert.txt",
            "-----BEGIN RSA PRIVATE KEY-----\nMIIE\n",
            "suspected credential pattern: private-key",
        ),
        (
            "config.json",
            '{"key": "AKIAABCDEFGHIJKLMNOP"}\n',
            "suspected credential pattern: aws-key",
        ),
        (
            "token.md",
            "token: ghp_" + "A" * 36 + "\n",
            "suspected credential pattern: github-token",
        ),
        (
            "endpoint.txt",
            "url = https://user:secretpass@broker.internal/\n",
            "suspected credential pattern: url-credential",
        ),
    ],
)
def test_non_python_file_with_secret_fails(
    tmp_path: Path, filename: str, secret_text: str, expected_rule: str
) -> None:
    s4_root = tmp_path / "statistical_baselines"
    s4_root.mkdir(parents=True, exist_ok=True)
    target = s4_root / filename
    target.write_text(secret_text, encoding="utf-8")

    findings = scan_tree(s4_root)
    assert any(f.rule == expected_rule for f in findings)


def test_python_named_credential_literal_fails(tmp_path: Path) -> None:
    s4_root = tmp_path / "statistical_baselines"
    s4_root.mkdir(parents=True)
    (s4_root / "config.py").write_text('password = "literal-value"\n', encoding="utf-8")

    findings = scan_tree(s4_root)
    assert any("suspected literal credential" in f.rule for f in findings)


def test_symlink_under_s4_root_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    s4_root = tmp_path / "statistical_baselines"
    s4_root.mkdir(parents=True)
    real_file = s4_root / "target.py"
    real_file.write_text("x = 1\n", encoding="utf-8")
    link_path = s4_root / "linked.py"

    try:
        os.symlink(real_file, link_path)
        symlink_created = True
    except OSError:
        symlink_created = False

    if symlink_created:
        findings = scan_tree(s4_root)
        assert any("symlink" in f.rule for f in findings)
    else:
        orig_is_symlink = Path.is_symlink
        monkeypatch.setattr(
            Path,
            "is_symlink",
            lambda self: True if self.name == "mock_symlink.py" else orig_is_symlink(self),
        )
        mock_file = s4_root / "mock_symlink.py"
        mock_file.write_text("x = 1\n", encoding="utf-8")
        findings = scan_tree(s4_root)
        assert any("symlink" in f.rule for f in findings)


@pytest.mark.parametrize(
    ("source", "expected_rule_substring"),
    [
        ("import MetaTrader5\n", "forbidden import: MetaTrader5"),
        ("import requests\n", "forbidden import: requests"),
        ("import httpx\n", "forbidden import: httpx"),
        ("import aiohttp\n", "forbidden import: aiohttp"),
        ("import socket\n", "forbidden import: socket"),
        ("import urllib.request\n", "forbidden import: urllib.request"),
        ("import sklearn\n", "forbidden import: sklearn"),
        ("import xgboost\n", "forbidden import: xgboost"),
        ("import lightgbm\n", "forbidden import: lightgbm"),
        ("import catboost\n", "forbidden import: catboost"),
        ("import torch\n", "forbidden import: torch"),
        ("import tensorflow\n", "forbidden import: tensorflow"),
        ("import keras\n", "forbidden import: keras"),
        ("from sklearn.model_selection import train_test_split\n", "forbidden import: sklearn"),
        ("from sklearn import datasets\n", "forbidden import: sklearn"),
        ("x = StrategyEngine()\n", "forbidden operational name: StrategyEngine"),
        ("x = SignalEngine()\n", "forbidden operational name: SignalEngine"),
        ("x = RiskEngine()\n", "forbidden operational name: RiskEngine"),
        ("x = TradeIntent()\n", "forbidden operational name: TradeIntent"),
        ("x = OrderIntent()\n", "forbidden operational name: OrderIntent"),
        ("x = ExecutionOrder()\n", "forbidden operational name: ExecutionOrder"),
        ("x = FinancialLedger()\n", "forbidden operational name: FinancialLedger"),
        ("order_send(req)\n", "forbidden operational name: order_send"),
        ("import time\ntime.sleep(1)\n", "forbidden wall-clock call: time.sleep"),
        (
            "import asyncio\nasync def f(): await asyncio.sleep(1)\n",
            "forbidden wall-clock call: asyncio.sleep",
        ),
        (
            "import random\nx = random.random()\n",
            "forbidden stochastic call in baseline: random.random",
        ),
        ("import subprocess\nsubprocess.run(['ls'])\n", "forbidden process call: subprocess.run"),
        (
            "import uuid as u\nx = u.uuid4()\n",
            "forbidden stochastic call in baseline: uuid.uuid4",
        ),
        (
            "from uuid import uuid4 as make_id\nx = make_id()\n",
            "forbidden stochastic call in baseline: uuid.uuid4",
        ),
        (
            "import os as operating_system\nx = operating_system.urandom(16)\n",
            "forbidden stochastic call in baseline: os.urandom",
        ),
        (
            "import secrets as sec\nx = sec.token_bytes(16)\n",
            "forbidden stochastic call in baseline: secrets.token_bytes",
        ),
        (
            "from random import SystemRandom\nsr = SystemRandom()\n",
            "forbidden stochastic import: SystemRandom",
        ),
    ],
)
def test_prohibited_constructs_detected(
    tmp_path: Path, source: str, expected_rule_substring: str
) -> None:
    s4_root = tmp_path / "statistical_baselines"
    s4_root.mkdir(parents=True, exist_ok=True)
    test_file = s4_root / "sample.py"
    test_file.write_text(source, encoding="utf-8")

    findings = scan_tree(s4_root)
    assert any(expected_rule_substring in f.rule for f in findings)


def test_main_passes_on_clean_repo() -> None:
    assert main() == 0


def test_main_fails_with_findings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import scripts.check_s4_boundary as s4b
    bad_root = tmp_path / "statistical_baselines"
    bad_root.mkdir(parents=True)
    (bad_root / "bad.py").write_text("import sklearn\n", encoding="utf-8")
    monkeypatch.setattr(s4b, "S4_ROOTS", (bad_root,))
    assert s4b.main() == 1


def test_scan_tree_non_existent_root(tmp_path: Path) -> None:
    non_existent = tmp_path / "does_not_exist"
    assert scan_tree(non_existent) == []


def test_non_utf8_file_fails(tmp_path: Path) -> None:
    s4_root = tmp_path / "statistical_baselines"
    s4_root.mkdir(parents=True, exist_ok=True)
    bad_file = s4_root / "bad.txt"
    bad_file.write_bytes(b"\x80\x81\x82")

    findings = scan_tree(s4_root)
    assert any("not valid UTF-8 text" in f.rule for f in findings)


def test_scan_file_os_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "error_file.py"
    target.write_text("x = 1\n", encoding="utf-8")

    def mock_read_text(self: Path, encoding: str = "utf-8") -> str:
        raise OSError("Permission denied")

    monkeypatch.setattr(Path, "read_text", mock_read_text)
    findings = scan_file(target)
    assert any("read error" in f.rule for f in findings)


def test_scan_file_syntax_error(tmp_path: Path) -> None:
    syntax_error_file = tmp_path / "syntax_err.py"
    syntax_error_file.write_text("def foo(:", encoding="utf-8")
    findings = scan_file(syntax_error_file)
    assert any("syntax error" in f.rule for f in findings)


def test_directory_symlink_under_s4_root_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    s4_root = tmp_path / "statistical_baselines"
    s4_root.mkdir(parents=True)
    sub_dir = s4_root / "subdir"
    sub_dir.mkdir()
    link_dir = s4_root / "linkdir"

    try:
        os.symlink(sub_dir, link_dir, target_is_directory=True)
        symlink_created = True
    except OSError:
        symlink_created = False

    if symlink_created:
        findings = scan_tree(s4_root)
        assert any("directory symlink forbidden" in f.rule for f in findings)
    else:
        orig_is_symlink = Path.is_symlink
        monkeypatch.setattr(
            Path,
            "is_symlink",
            lambda self: True if self.name == "mock_linkdir" else orig_is_symlink(self),
        )
        mock_dir = s4_root / "mock_linkdir"
        mock_dir.mkdir()
        findings = scan_tree(s4_root)
        assert any("directory symlink forbidden" in f.rule for f in findings)


def test_scan_tree_traverses_normal_directory(tmp_path: Path) -> None:
    root = tmp_path / "statistical_baselines"
    root.mkdir()
    sub = root / "sub"
    sub.mkdir()
    pycache = root / "__pycache__"
    pycache.mkdir()
    (pycache / "cached.pyc").write_bytes(b"dummy")
    f = sub / "clean.py"
    f.write_text("x = 1\n", encoding="utf-8")
    assert scan_tree(root) == []


def test_main_cli_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["check_s4_boundary.py"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("scripts.check_s4_boundary", run_name="__main__")
    assert exc.value.code == 0
