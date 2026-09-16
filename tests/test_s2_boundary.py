"""Tests for Sprint 2 capability and generic security boundary verifier."""

import os
from pathlib import Path

import pytest
from scripts.check_s2_boundary import S2_ROOTS, main, verify_s2_boundary


def test_allowed_python_file_passes(tmp_path: Path) -> None:
    s2_root = tmp_path / "replay"
    s2_root.mkdir(parents=True)
    allowed = s2_root / "allowed.py"
    allowed.write_text(
        "from dataclasses import dataclass\n"
        "@dataclass(frozen=True)\n"
        "class ValidReplayRecord:\n"
        "    sequence: int\n",
        encoding="utf-8",
    )
    findings = verify_s2_boundary((s2_root,))
    assert findings == []


@pytest.mark.parametrize(
    ("filename", "secret_text", "expected_rule"),
    [
        ("cert.txt", "-----BEGIN RSA PRIVATE KEY-----\nMIIE\n", "possible-secret:private-key"),
        ("config.json", '{"key": "AKIAABCDEFGHIJKLMNOP"}\n', "possible-secret:aws-key"),
        ("token.md", "token: ghp_" + "A" * 36 + "\n", "possible-secret:github-token"),
        (
            "endpoint.txt",
            "url = https://user:secretpass@broker.internal/\n",
            "possible-secret:url-credential",
        ),
    ],
)
def test_non_python_file_with_secret_fails(
    tmp_path: Path, filename: str, secret_text: str, expected_rule: str
) -> None:
    s2_root = tmp_path / "replay"
    s2_root.mkdir(parents=True, exist_ok=True)
    target = s2_root / filename
    target.write_text(secret_text, encoding="utf-8")

    findings = verify_s2_boundary((s2_root,))
    assert any(f.rule == expected_rule for f in findings)


def test_symlink_under_s2_root_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    s2_root = tmp_path / "replay"
    s2_root.mkdir(parents=True)
    real_file = s2_root / "target.py"
    real_file.write_text("x = 1\n", encoding="utf-8")
    link_path = s2_root / "linked.py"

    try:
        os.symlink(real_file, link_path)
        symlink_created = True
    except OSError:
        symlink_created = False

    if symlink_created:
        findings = verify_s2_boundary((s2_root,))
        assert any(f.rule == "s2-symlink-rejected" for f in findings)
    else:
        orig_is_symlink = Path.is_symlink
        monkeypatch.setattr(
            Path,
            "is_symlink",
            lambda self: True if self.name == "mock_symlink.py" else orig_is_symlink(self),
        )
        mock_file = s2_root / "mock_symlink.py"
        mock_file.write_text("x = 1\n", encoding="utf-8")
        findings = verify_s2_boundary((s2_root,))
        assert any(f.rule == "s2-symlink-rejected" for f in findings)


@pytest.mark.parametrize(
    ("source", "expected_rule_substring"),
    [
        ("import MetaTrader5\n", "forbidden-import:MetaTrader5"),
        ("import requests\n", "forbidden-import:requests"),
        ("import socket\n", "forbidden-import:socket"),
        ("class TradeIntent:\n    pass\n", "forbidden-definition:TradeIntent"),
        ("class OrderIntent:\n    pass\n", "forbidden-definition:OrderIntent"),
        ("class StrategyDecision:\n    pass\n", "forbidden-definition:StrategyDecision"),
        ("class RiskAuthorization:\n    pass\n", "forbidden-definition:RiskAuthorization"),
        ("class PnL:\n    pass\n", "forbidden-definition:PnL"),
        ("class SpreadModel:\n    pass\n", "forbidden-definition:SpreadModel"),
        ("import time\ntime.sleep(1)\n", "wall-clock-call:time.sleep"),
        ("from datetime import datetime\ndatetime.now()\n", "wall-clock-call:datetime.now"),
        ("from datetime import datetime\ndatetime.utcnow()\n", "wall-clock-call:datetime.utcnow"),
        ("import time\ntime.time()\n", "wall-clock-call:time.time"),
    ],
)
def test_financial_and_temporal_prohibitions_fail(
    tmp_path: Path, source: str, expected_rule_substring: str
) -> None:
    s2_root = tmp_path / "replay"
    s2_root.mkdir(parents=True, exist_ok=True)
    target = s2_root / "prohibited.py"
    target.write_text(source, encoding="utf-8")

    findings = verify_s2_boundary((s2_root,))
    assert any(expected_rule_substring in f.rule for f in findings)


def test_repo_s2_roots_pass_boundary() -> None:
    findings = verify_s2_boundary(S2_ROOTS)
    assert findings == []


def test_main_cli_returns_expected_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    s2_root = tmp_path / "replay"
    s2_root.mkdir(parents=True)
    (s2_root / "ok.py").write_text("VALID = 1\n", encoding="utf-8")
    monkeypatch.setattr("scripts.check_s2_boundary.S2_ROOTS", (s2_root,))
    assert main() == 0
    assert "S2 boundary PASS" in capsys.readouterr().out

    (s2_root / "bad.py").write_text("import requests\n", encoding="utf-8")
    assert main() == 1
    assert "forbidden-import:requests" in capsys.readouterr().out
