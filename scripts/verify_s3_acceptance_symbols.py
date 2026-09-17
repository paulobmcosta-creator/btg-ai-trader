"""Verify that symbols and paths cited in S3_FINAL_ACCEPTANCE.md actually exist in the codebase.

Prevents phantom citations, stale symbol references, and documentary drift.
Programmatically asserts:
  - CITED_PATHS - REAL_PATHS = {}
  - CITED_CLASSES - REAL_CLASSES = {}
  - CITED_FUNCTIONS - REAL_FUNCTIONS = {}
  - CITED_METHODS - REAL_METHODS = {}
  - CITED_ENUM_MEMBERS - REAL_ENUM_MEMBERS = {}
  - CITED_TESTS - REAL_TESTS = {}
"""

from __future__ import annotations

import ast
import inspect
import re
import sys
from enum import Enum
from pathlib import Path

ACCEPTANCE_DOC = Path("docs/program/S3_FINAL_ACCEPTANCE.md")

BANNED_PHANTOM_SYMBOLS = (
    "CausalMarketReplayCursor",
    "calculate_spread",
    "SpreadModel.executable_price",
    "quote_event_id",
    "max_lot_size",
    "FORCE_CLOSE_AT_LAST_VALID_EVENT",
    "resolve_execution_price",
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

    # Extract all inline backticks
    backticks = set(re.findall(r"`([^`\n]+)`", content))

    # --- A. CITED_TESTS ---
    cited_tests: set[str] = {
        b for b in backticks if b.startswith("test_") and not b.endswith(".py")
    }
    real_tests = collect_test_functions_from_ast(Path("tests"))
    diff_tests = cited_tests - real_tests
    if diff_tests:
        findings.append(f"CITED_TESTS - REAL_TESTS = {sorted(diff_tests)}")

    # --- B. CITED_PATHS ---
    repo_basenames = {
        p.name: p.as_posix()
        for p in Path(".").rglob("*")
        if not any(part.startswith(".") for part in p.parts)
    }
    branch_prefixes = ("s3/", "sprint/", "origin/")

    cited_paths: set[str] = set()
    for b in backticks:
        if (
            b.startswith("http")
            or " " in b
            or "<=" in b
            or ">=" in b
            or "==" in b
            or b.startswith(branch_prefixes)
        ):
            continue
        if "/" in b or b.endswith(
            (".py", ".md", ".toml", ".yml", ".yaml", ".json", ".txt")
        ):
            clean_p = b.rstrip(":").rstrip("/*")
            cited_paths.add(clean_p)

    real_paths: set[str] = set()
    for p in cited_paths:
        if Path(p).exists() or p in repo_basenames:
            real_paths.add(p)
    diff_paths = cited_paths - real_paths
    if diff_paths:
        findings.append(f"CITED_PATHS - REAL_PATHS = {sorted(diff_paths)}")

    # --- C. CITED_CLASSES, FUNCTIONS, METHODS, ENUM_MEMBERS ---
    import btg_ai_trader.backtesting as bt_mod

    all_bt_attrs = {name: getattr(bt_mod, name) for name in dir(bt_mod)}
    bt_classes = {name: obj for name, obj in all_bt_attrs.items() if isinstance(obj, type)}
    bt_functions = {name: obj for name, obj in all_bt_attrs.items() if inspect.isfunction(obj)}

    # C.1 Classes
    cited_classes: set[str] = {b for b in backticks if b in bt_classes}
    real_classes: set[str] = set(bt_classes.keys())
    diff_classes = cited_classes - real_classes
    if diff_classes:
        findings.append(f"CITED_CLASSES - REAL_CLASSES = {sorted(diff_classes)}")

    # C.2 Functions
    cited_functions: set[str] = set()
    for b in backticks:
        clean_f = b[:-2] if b.endswith("()") else b
        if clean_f in bt_functions:
            cited_functions.add(clean_f)
    real_functions: set[str] = set(bt_functions.keys())
    diff_functions = cited_functions - real_functions
    if diff_functions:
        findings.append(f"CITED_FUNCTIONS - REAL_FUNCTIONS = {sorted(diff_functions)}")

    # C.3 Methods and Enum Members
    cited_methods: set[str] = set()
    real_methods: set[str] = set()
    cited_enum_members: set[str] = set()
    real_enum_members: set[str] = set()

    dotted_candidates = {
        b
        for b in backticks
        if "." in b
        and "/" not in b
        and not any(
            b.endswith(ext)
            for ext in [".py", ".md", ".yml", ".toml", ".json", ".txt", ".0", ".5"]
        )
    }

    for d in dotted_candidates:
        clean_d = d[:-2] if d.endswith("()") else d
        parts = clean_d.split(".")
        if len(parts) == 2:
            cls_name, member_name = parts
            if cls_name in bt_classes:
                cls = bt_classes[cls_name]
                if issubclass(cls, Enum):
                    cited_enum_members.add(clean_d)
                    if hasattr(cls, member_name):
                        real_enum_members.add(clean_d)
                else:
                    cited_methods.add(clean_d)
                    if hasattr(cls, member_name):
                        real_methods.add(clean_d)

    # Also detect enum members cited in patterns like `OrderStyle` (`MARKET`) or
    # `Side` (`BUY`, `SELL`)
    enum_classes = {name: cls for name, cls in bt_classes.items() if issubclass(cls, Enum)}
    for enum_name, enum_cls in enum_classes.items():
        for member in enum_cls.__members__:
            # check if qualified or unqualified member is cited in markdown
            if f"`{enum_name}.{member}`" in content or f"`{member}`" in content:
                cited_enum_members.add(f"{enum_name}.{member}")
                real_enum_members.add(f"{enum_name}.{member}")

    diff_methods = cited_methods - real_methods
    if diff_methods:
        findings.append(f"CITED_METHODS - REAL_METHODS = {sorted(diff_methods)}")

    diff_enum_members = cited_enum_members - real_enum_members
    if diff_enum_members:
        findings.append(f"CITED_ENUM_MEMBERS - REAL_ENUM_MEMBERS = {sorted(diff_enum_members)}")

    # Programmatic set difference printouts
    print(f"CITED_PATHS - REAL_PATHS = {diff_paths}")
    print(f"CITED_CLASSES - REAL_CLASSES = {diff_classes}")
    print(f"CITED_FUNCTIONS - REAL_FUNCTIONS = {diff_functions}")
    print(f"CITED_METHODS - REAL_METHODS = {diff_methods}")
    print(f"CITED_ENUM_MEMBERS - REAL_ENUM_MEMBERS = {diff_enum_members}")
    print(f"CITED_TESTS - REAL_TESTS = {diff_tests}")

    if findings:
        print(
            f"\nFAIL: S3 Acceptance Symbol Verification found {len(findings)} issue(s):",
            file=sys.stderr,
        )
        for f in findings:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print(
        f"\nPASS: S3 Acceptance Symbol Verification passed.\n"
        f"  - Zero banned phantom symbols found\n"
        f"  - {len(cited_paths)} cited paths verified\n"
        f"  - {len(cited_classes)} cited classes verified\n"
        f"  - {len(cited_functions)} cited functions verified\n"
        f"  - {len(cited_methods)} cited methods verified\n"
        f"  - {len(cited_enum_members)} cited enum members verified\n"
        f"  - {len(cited_tests)} cited test functions verified against AST"
    )
    return 0


def main() -> None:
    sys.exit(verify_acceptance_symbols())


if __name__ == "__main__":
    main()
