"""Verify that symbols cited in S3_FINAL_ACCEPTANCE.md actually exist in the codebase.

Prevents phantom citations, stale symbol references, and documentary drift.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ACCEPTANCE_DOC = Path("docs/program/S3_FINAL_ACCEPTANCE.md")

BANNED_PHANTOM_SYMBOLS = (
    "CausalMarketReplayCursor",
    "calculate_spread",
    "executable_price",
    "quote_event_id",
    "max_lot_size",
    "FORCE_CLOSE_AT_LAST_VALID_EVENT",
)

EXPECTED_BACKTESTING_SYMBOLS = (
    "BacktestAction",
    "SimulatedFill",
    "InstrumentEconomics",
    "ExecutionTiming",
    "ActionIdentity",
    "SpreadModel",
    "ZeroSlippageModel",
    "FixedPointsSlippageModel",
    "FixedBpsSlippageModel",
    "FeeSchedule",
    "LatencyModel",
    "ExecutionPolicy",
    "EconomicAssumptions",
    "BacktestPositionState",
    "BacktestPnL",
    "BacktestEconomicState",
    "DescriptiveBacktestMetrics",
    "DeterministicEconomicBacktester",
    "BacktestInputBoundary",
    "BacktestRunManifest",
    "EndOfWindowPolicy",
    "OrderStyle",
    "Side",
    "ExecutionOutcome",
)


def collect_test_functions_from_ast(test_dir: Path) -> set[str]:
    """Parse all test files using AST and return a set of all test function names."""
    test_functions: set[str] = set()
    for py_file in test_dir.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    test_functions.add(node.name)
        except Exception as err:
            print(f"ERROR: failed to parse {py_file}: {err}", file=sys.stderr)
    return test_functions


def verify_acceptance_symbols() -> int:
    """Run verification checks on S3_FINAL_ACCEPTANCE.md."""
    if not ACCEPTANCE_DOC.is_file():
        print(f"FAIL: Acceptance document not found at {ACCEPTANCE_DOC}", file=sys.stderr)
        return 1

    content = ACCEPTANCE_DOC.read_text(encoding="utf-8")
    findings: list[str] = []

    # 1. Check for banned / phantom symbols
    for banned in BANNED_PHANTOM_SYMBOLS:
        matches = [
            i + 1 for i, line in enumerate(content.splitlines()) if banned in line
        ]
        if matches:
            findings.append(
                f"Banned phantom symbol '{banned}' found on line(s): {matches}"
            )

    # 2. Check for existence of backtesting symbols in actual codebase
    import btg_ai_trader.backtesting as bt_pkg

    for sym in EXPECTED_BACKTESTING_SYMBOLS:
        if not hasattr(bt_pkg, sym):
            findings.append(
                f"Expected backtesting symbol '{sym}' is not exported by btg_ai_trader.backtesting"
            )

    # 3. Extract and verify test function citations
    # Find all backtick identifiers starting with test_ that do NOT end with .py
    cited_test_names: set[str] = set()
    for match in re.finditer(r"`(test_[a-zA-Z0-9_]+)`", content):
        name = match.group(1)
        cited_test_names.add(name)

    actual_tests = collect_test_functions_from_ast(Path("tests"))
    missing_tests = cited_test_names - actual_tests
    if missing_tests:
        findings.append(
            f"Cited test functions not found in test suite: {sorted(missing_tests)}"
        )

    if findings:
        print(
            f"FAIL: S3 Acceptance Symbol Verification found {len(findings)} issue(s):",
            file=sys.stderr,
        )
        for f in findings:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print(
        f"PASS: S3 Acceptance Symbol Verification passed.\n"
        f"  - Zero banned phantom symbols found\n"
        f"  - {len(EXPECTED_BACKTESTING_SYMBOLS)} core backtesting symbols verified in package\n"
        f"  - {len(cited_test_names)} cited test functions verified against AST in tests/"
    )
    return 0


def main() -> None:
    sys.exit(verify_acceptance_symbols())


if __name__ == "__main__":
    main()
