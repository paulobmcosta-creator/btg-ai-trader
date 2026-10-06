from __future__ import annotations

import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest


def _scan_file(path: Path) -> list[object]:
    namespace = runpy.run_path("scripts/check_s8_strategy_boundary.py")
    scanner = cast(Callable[[Path], list[object]], namespace["scan_file"])
    return scanner(path)


@pytest.mark.parametrize(
    "source",
    [
        "class PaperTrader:\n    pass\n",
        "def order_send():\n    pass\n",
        "async def positions_get():\n    pass\n",
    ],
)
def test_scanner_rejects_forbidden_declaration_names(tmp_path: Path, source: str) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any("forbidden operational declaration" in str(finding) for finding in findings)


def test_scanner_allows_unrelated_declaration_names(tmp_path: Path) -> None:
    target = tmp_path / "probe.py"
    target.write_text("class StrategyHelper:\n    pass\n", encoding="utf-8")

    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        "from btg_ai_trader.risk_engine import evaluate_risk\n",
        "from btg_ai_trader.risk_engine import RiskAuthorization\n",
        "import btg_ai_trader.risk_engine\n",
        "from btg_ai_trader import risk_engine\n",
    ],
)
def test_risk_adapter_rejects_broader_risk_engine_authority(
    tmp_path: Path,
    source: str,
) -> None:
    strategy_dir = tmp_path / "strategy"
    strategy_dir.mkdir()
    target = strategy_dir / "risk_adapter.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert findings
    assert any(
        "Risk Engine" in str(finding) or "risk_adapter" in str(finding)
        for finding in findings
    )


def test_risk_adapter_allows_only_required_risk_proposal_symbols(tmp_path: Path) -> None:
    strategy_dir = tmp_path / "strategy"
    strategy_dir.mkdir()
    target = strategy_dir / "risk_adapter.py"
    target.write_text(
        "from btg_ai_trader.risk_engine import EconomicDirection as RiskEconomicDirection\n"
        "from btg_ai_trader.risk_engine import RiskProposal\n",
        encoding="utf-8",
    )

    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        "from urllib import request\nrequest.urlopen('https://example.invalid')\n",
        "from urllib import request as req\nreq.urlopen('https://example.invalid')\n",
    ],
)
def test_scanner_rejects_split_forbidden_imports(tmp_path: Path, source: str) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any("forbidden import: urllib.request" in str(finding) for finding in findings)


@pytest.mark.parametrize(
    "source",
    [
        "import http.client\nhttp.client.HTTPSConnection('example.invalid')\n",
        "from http import client\nclient.HTTPSConnection('example.invalid')\n",
        "from http.client import HTTPSConnection\nHTTPSConnection('example.invalid')\n",
        "import ftplib\nftplib.FTP('example.invalid')\n",
    ],
)
def test_scanner_rejects_network_clients_outside_import_allowlist(
    tmp_path: Path,
    source: str,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any("outside Strategy allowlist" in str(finding) for finding in findings)


def test_scanner_allows_only_current_strategy_dependency_surface(tmp_path: Path) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "from __future__ import annotations\n"
        "import hashlib\n"
        "import json\n"
        "import types\n"
        "from collections.abc import Mapping\n"
        "from dataclasses import dataclass\n"
        "from datetime import datetime\n"
        "from decimal import Decimal\n"
        "from enum import Enum\n"
        "from btg_ai_trader.observer.identity import TradableInstrumentId\n"
        "from btg_ai_trader.strategy.domain import CandidateStrategy\n",
        encoding="utf-8",
    )

    assert _scan_file(target) == []
