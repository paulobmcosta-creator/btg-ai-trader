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
