"""Tests for Sprint 3 capability boundary verifier."""

import os
from pathlib import Path

import pytest
from scripts.check_s3_boundary import main, scan_tree


def test_allowed_python_file_passes(tmp_path: Path) -> None:
    s3_root = tmp_path / "backtesting"
    s3_root.mkdir(parents=True)
    allowed = s3_root / "allowed.py"
    allowed.write_text(
        "from dataclasses import dataclass\n"
        "from decimal import Decimal\n"
        "@dataclass(frozen=True)\n"
        "class BacktestAction:\n"
        "    quantity: Decimal\n",
        encoding="utf-8",
    )
    findings = scan_tree(s3_root)
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
    s3_root = tmp_path / "backtesting"
    s3_root.mkdir(parents=True, exist_ok=True)
    target = s3_root / filename
    target.write_text(secret_text, encoding="utf-8")

    findings = scan_tree(s3_root)
    assert any(f.rule == expected_rule for f in findings)


def test_python_named_credential_literal_fails(tmp_path: Path) -> None:
    s3_root = tmp_path / "backtesting"
    s3_root.mkdir(parents=True)
    (s3_root / "config.py").write_text('password = "literal-value"\n', encoding="utf-8")

    findings = scan_tree(s3_root)
    assert any("suspected literal credential" in f.rule for f in findings)


def test_symlink_under_s3_root_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    s3_root = tmp_path / "backtesting"
    s3_root.mkdir(parents=True)
    real_file = s3_root / "target.py"
    real_file.write_text("x = 1\n", encoding="utf-8")
    link_path = s3_root / "linked.py"

    try:
        os.symlink(real_file, link_path)
        symlink_created = True
    except OSError:
        symlink_created = False

    if symlink_created:
        findings = scan_tree(s3_root)
        assert any("symlink" in f.rule for f in findings)
    else:
        orig_is_symlink = Path.is_symlink
        monkeypatch.setattr(
            Path,
            "is_symlink",
            lambda self: True if self.name == "mock_symlink.py" else orig_is_symlink(self),
        )
        mock_file = s3_root / "mock_symlink.py"
        mock_file.write_text("x = 1\n", encoding="utf-8")
        findings = scan_tree(s3_root)
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
    ],
)
def test_prohibited_constructs_detected(
    tmp_path: Path, source: str, expected_rule_substring: str
) -> None:
    s3_root = tmp_path / "backtesting"
    s3_root.mkdir(parents=True, exist_ok=True)
    test_file = s3_root / "sample.py"
    test_file.write_text(source, encoding="utf-8")

    findings = scan_tree(s3_root)
    assert any(expected_rule_substring in f.rule for f in findings)


def test_main_passes_on_clean_repo() -> None:
    assert main() == 0


def test_non_utf8_file_fails(tmp_path: Path) -> None:
    s3_root = tmp_path / "backtesting"
    s3_root.mkdir(parents=True, exist_ok=True)
    bad_file = s3_root / "bad.txt"
    bad_file.write_bytes(b"\x80\x81\x82")

    findings = scan_tree(s3_root)
    assert any("not valid UTF-8 text" in f.rule for f in findings)
