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
        "import weakref\n"
        "from collections.abc import Callable, Mapping\n"
        "from dataclasses import dataclass, field\n"
        "from datetime import UTC, datetime, timedelta\n"
        "from decimal import Decimal\n"
        "from enum import Enum\n"
        "from btg_ai_trader.observer.identity import TradableInstrumentId\n"
        "from btg_ai_trader.strategy.domain import CandidateStrategy\n",
        encoding="utf-8",
    )

    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        "file_open = open\nfile_open('state', 'w')\n",
        "runner = eval\nrunner('1 + 1')\n",
        "from datetime import datetime\nclock = datetime.now\nclock()\n",
        "from datetime import datetime as dt\nclock = dt.utcnow\nclock()\n",
    ],
)
def test_scanner_rejects_references_to_forbidden_callables(
    tmp_path: Path,
    source: str,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any("forbidden callable reference" in str(finding) for finding in findings)


def test_scanner_allows_reference_to_safe_callable(tmp_path: Path) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "import hashlib\n"
        "digest = hashlib.sha256\n"
        "value = digest(b'payload').hexdigest()\n",
        encoding="utf-8",
    )

    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        (
            "from btg_ai_trader.strategy.domain import datetime as clock\n"
            "clock.now()\n"
        ),
        "from btg_ai_trader.strategy.domain import json\n",
        "from btg_ai_trader.strategy.engine import StrategyDecision\n",
        "from datetime import timezone\n",
    ],
)
def test_scanner_rejects_reexports_and_unapproved_symbols(
    tmp_path: Path,
    source: str,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any("symbol outside Strategy import allowlist" in str(finding) for finding in findings)


def test_scanner_rejects_namespace_import_of_allowlisted_internal_module(
    tmp_path: Path,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "import btg_ai_trader.strategy.domain as domain\n"
        "clock = domain.datetime\n",
        encoding="utf-8",
    )

    findings = _scan_file(target)

    assert any("outside Strategy allowlist" in str(finding) for finding in findings)


@pytest.mark.parametrize(
    "source",
    [
        (
            "import json\n"
            "json.__builtins__['open']('state', 'w').write('x')\n"
        ),
        "__builtins__['open']('state', 'w')\n",
        (
            "import json\n"
            "json.__dict__['__builtins__']['open']('state', 'w')\n"
        ),
        (
            "import json\n"
            "getattr(json, '__builtins__')['open']('state', 'w')\n"
        ),
        "globals()['__builtins__']['open']('state', 'w')\n",
    ],
)
def test_scanner_rejects_reflection_paths_to_forbidden_builtins(
    tmp_path: Path,
    source: str,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any(
        "forbidden reflection namespace" in str(finding)
        or "forbidden callable reference" in str(finding)
        for finding in findings
    )


def test_scanner_keeps_required_object_setattr_internal_pattern_allowed(
    tmp_path: Path,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "class Holder:\n"
        "    pass\n"
        "holder = Holder()\n"
        "object.__setattr__(holder, 'value', 1)\n",
        encoding="utf-8",
    )

    assert _scan_file(target) == []


@pytest.mark.parametrize(
    "source",
    [
        "from datetime import datetime\ndatetime.today()\n",
        "from datetime import datetime as dt\ndt.today()\n",
        "from datetime import datetime\nclock = datetime.today\nclock()\n",
    ],
)
def test_scanner_rejects_datetime_today_wall_clock(
    tmp_path: Path,
    source: str,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any(
        "datetime.today" in str(finding)
        and (
            "forbidden call" in str(finding)
            or "forbidden callable reference" in str(finding)
        )
        for finding in findings
    )


@pytest.mark.parametrize(
    "source",
    [
        (
            "import json\n"
            "json.__loader__.set_data('/tmp/state', b'changed')\n"
        ),
        (
            "import json\n"
            "json.__spec__.loader.set_data('/tmp/state', b'changed')\n"
        ),
        (
            "import json\n"
            "json.__loader__.get_data('/tmp/state')\n"
        ),
    ],
)
def test_scanner_rejects_loader_and_spec_reflection(
    tmp_path: Path,
    source: str,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any(
        "forbidden reflection namespace" in str(finding)
        or "forbidden I/O method" in str(finding)
        for finding in findings
    )


@pytest.mark.parametrize(
    "source",
    [
        "import json\njson.dump({'x': 1}, handle)\n",
        "import json\njson.load(handle)\n",
        "import json as codec\ncodec.dump({'x': 1}, handle)\n",
        "import json as codec\ncodec.load(handle)\n",
    ],
)
def test_scanner_rejects_json_file_helpers(
    tmp_path: Path,
    source: str,
) -> None:
    target = tmp_path / "probe.py"
    target.write_text(source, encoding="utf-8")

    findings = _scan_file(target)

    assert any(
        "module attribute outside Strategy allowlist" in str(finding)
        for finding in findings
    )


def test_scanner_allows_only_required_namespace_module_apis(tmp_path: Path) -> None:
    target = tmp_path / "probe.py"
    target.write_text(
        "import hashlib\n"
        "import json\n"
        "import types\n"
        "import weakref\n"
        "digest = hashlib.sha256(b'x').hexdigest()\n"
        "encoded = json.dumps({'digest': digest})\n"
        "proxy = types.MappingProxyType({'encoded': encoded})\n"
        "reference_type = weakref.ReferenceType\n"
        "reference_factory = weakref.ref\n",
        encoding="utf-8",
    )

    assert _scan_file(target) == []
