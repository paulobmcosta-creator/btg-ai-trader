"""Verify that symbols and paths cited in S5_FINAL_ACCEPTANCE.md actually exist in the codebase.

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
import re
import sys
from pathlib import Path
from typing import NamedTuple

ACCEPTANCE_DOC = Path("docs/program/S5_FINAL_ACCEPTANCE.md")

BANNED_PHANTOM_SYMBOLS = (
    "AutoMLSearch",
    "DeepNeuralNetwork",
    "ReinforcementLearner",
    "OnlineExecutionPolicy",
    "LiveOrderDispatcher",
)

EXCLUDED_NON_CLASSES = {
    "Decimal",
    "UTC",
    "NotImplementedError",
    "ValueError",
    "TypeError",
    "KeyError",
    "AttributeError",
    "RuntimeError",
    "Exception",
    "MetaTrader5",
    "FinancialLedger",
    "PaperExecution",
    "LiveExecution",
    "ExecutionEngine",
    "StrategyEngine",
    "StrategyDecision",
    "SignalEngine",
    "SignalGenerator",
    "RiskEngine",
    "RiskAuthorization",
    "OrderManager",
    "OrderIntent",
    "OrderPlan",
    "ExecutionOrder",
    "TradeIntent",
    "GridSearchCV",
    "Optuna",
    "RandomizedSearchCV",
    "AccountInfo",
    "TerminalInfo",
    "LogisticRegression",
    "Ridge",
    "RandomForestClassifier",
    "RandomForestRegressor",
    "GradientBoostingClassifier",
    "GradientBoostingRegressor",
    "Protocol",
    "ABC",
    "Any",
    "Sequence",
    "Mapping",
    "Callable",
    "TypeVar",
    "Generic",
}


class SymbolInventory(NamedTuple):
    classes: set[str]
    functions: set[str]
    methods: set[str]
    enum_members: set[str]


def collect_codebase_symbols(src_dir: Path | None = None) -> SymbolInventory:
    """Collect real classes, functions, methods, and enum members from source directory via AST."""
    if src_dir is None:
        src_dir = Path("src/btg_ai_trader")

    classes: set[str] = set()
    functions: set[str] = set()
    methods: set[str] = set()
    enum_members: set[str] = set()

    for py_file in src_dir.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    cls_name = node.name
                    classes.add(cls_name)
                    is_enum = any(
                        (isinstance(b, ast.Name) and b.id == "Enum")
                        or (isinstance(b, ast.Attribute) and b.attr == "Enum")
                        for b in node.bases
                    )
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                            methods.add(f"{cls_name}.{item.name}")
                        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            methods.add(f"{cls_name}.{item.target.id}")
                            if is_enum:
                                enum_members.add(f"{cls_name}.{item.target.id}")
                        elif isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    methods.add(f"{cls_name}.{target.id}")
                                    if is_enum:
                                        enum_members.add(f"{cls_name}.{target.id}")
                elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    functions.add(node.name)
        except Exception as err:
            print(f"ERROR: failed to parse {py_file}: {err}", file=sys.stderr)

    return SymbolInventory(
        classes=classes,
        functions=functions,
        methods=methods,
        enum_members=enum_members,
    )


def collect_test_functions_from_ast(test_dir: Path | None = None) -> set[str]:
    """Parse all test files using AST and return a set of all test function names."""
    if test_dir is None:
        test_dir = Path("tests")

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


def extract_markdown_candidates(
    doc_path: Path | str = ACCEPTANCE_DOC,
    content: str | None = None,
) -> dict[str, set[str]]:
    """Extract candidate symbols and paths from markdown content purely by syntax."""
    if content is None:
        content = Path(doc_path).read_text(encoding="utf-8")

    content_no_blocks = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
    lines = content_no_blocks.splitlines()

    cited_paths: set[str] = set()
    cited_tests: set[str] = set()
    cited_functions: set[str] = set()
    cited_methods: set[str] = set()
    cited_enum_members: set[str] = set()
    cited_classes: set[str] = set()

    branch_prefixes = ("s5/", "sprint/", "origin/", "main")
    file_extensions = (".py", ".md", ".toml", ".yml", ".yaml", ".json", ".txt")

    for line in lines:
        for match in re.finditer(r"`([^`]+)`", line):
            token = match.group(1).strip()
            if not token or " " in token:
                continue

            # Check for file paths
            if "/" in token or "\\" in token:
                clean_path = token.replace("\\", "/")
                if any(clean_path.startswith(bp) for bp in branch_prefixes):
                    continue
                if clean_path.startswith("http://") or clean_path.startswith("https://"):
                    continue
                if any(clean_path.endswith(ext) for ext in file_extensions) or "/" in clean_path:
                    clean_path = clean_path.split(":")[0]
                    clean_path = clean_path.split("#")[0]
                    if any(clean_path.endswith(ext) for ext in file_extensions):
                        cited_paths.add(clean_path)
                continue

            # Method / enum member syntax: Class.member or Class.func()
            if "." in token and not any(token.endswith(ext) for ext in file_extensions):
                parts = token.split(".")
                if len(parts) == 2:
                    cls_part, member_part = parts
                    member_clean = member_part.rstrip("()")
                    if (
                        cls_part
                        and cls_part[0].isupper()
                        and not cls_part.isupper()
                        and member_clean.isidentifier()
                    ):
                        if member_clean.isupper():
                            cited_enum_members.add(f"{cls_part}.{member_clean}")
                        else:
                            cited_methods.add(f"{cls_part}.{member_clean}")
                continue

            # Function / test syntax: func() or test_*
            if token.startswith("test_"):
                cited_tests.add(token.rstrip("()"))
                continue

            if token.endswith("()"):
                func_name = token[:-2]
                if func_name.isidentifier() and not func_name.startswith("test_"):
                    if func_name[0].islower() or "_" in func_name:
                        cited_functions.add(func_name)
                continue

            # Class syntax: PascalCase
            if (
                token.isidentifier()
                and token[0].isupper()
                and not token.isupper()
                and not token.startswith("S5-")
                and not token.startswith("DD-")
            ):
                if token not in EXCLUDED_NON_CLASSES:
                    cited_classes.add(token)

    return {
        "paths": cited_paths,
        "tests": cited_tests,
        "functions": cited_functions,
        "methods": cited_methods,
        "enum_members": cited_enum_members,
        "classes": cited_classes,
    }


def run_symbol_verification(
    doc_path: Path | str = ACCEPTANCE_DOC,
    content: str | None = None,
    src_dir: Path | None = None,
    test_dir: Path | None = None,
) -> tuple[int, dict[str, set[str]]]:
    """Run verification checks on acceptance markdown content against codebase symbols."""
    target_path = Path(doc_path)
    if content is None and not target_path.is_file():
        print(f"FAIL: Acceptance document not found at {target_path}", file=sys.stderr)
        return 1, {}

    if content is None:
        content = target_path.read_text(encoding="utf-8")

    findings: list[str] = []

    # 1. Check for banned phantom symbols
    for banned in BANNED_PHANTOM_SYMBOLS:
        matches = [
            i + 1 for i, line in enumerate(content.splitlines()) if banned in line
        ]
        if matches:
            findings.append(
                f"Banned phantom symbol '{banned}' found on line(s): {matches}"
            )

    # 2. Extract syntax candidates from markdown independently of real symbols
    candidates = extract_markdown_candidates(target_path, content=content)

    # 3. Collect real symbols independently via AST
    code_symbols = collect_codebase_symbols(src_dir)
    real_tests = collect_test_functions_from_ast(test_dir)

    repo_basenames = {
        p.name: p.as_posix()
        for p in Path(".").rglob("*")
        if not any(part.startswith(".") for part in p.parts)
    }
    real_paths = {p for p in candidates["paths"] if Path(p).exists() or p in repo_basenames}

    # 4. Compute exact set differences
    diff_paths = candidates["paths"] - real_paths
    diff_classes = candidates["classes"] - code_symbols.classes
    diff_functions = candidates["functions"] - code_symbols.functions
    diff_methods = candidates["methods"] - code_symbols.methods
    diff_enum_members = candidates["enum_members"] - code_symbols.enum_members
    diff_tests = candidates["tests"] - real_tests

    diffs = {
        "paths": diff_paths,
        "classes": diff_classes,
        "functions": diff_functions,
        "methods": diff_methods,
        "enum_members": diff_enum_members,
        "tests": diff_tests,
    }

    if diff_paths:
        findings.append(f"CITED_PATHS - REAL_PATHS = {sorted(diff_paths)}")
    if diff_classes:
        findings.append(f"CITED_CLASSES - REAL_CLASSES = {sorted(diff_classes)}")
    if diff_functions:
        findings.append(f"CITED_FUNCTIONS - REAL_FUNCTIONS = {sorted(diff_functions)}")
    if diff_methods:
        findings.append(f"CITED_METHODS - REAL_METHODS = {sorted(diff_methods)}")
    if diff_enum_members:
        findings.append(f"CITED_ENUM_MEMBERS - REAL_ENUM_MEMBERS = {sorted(diff_enum_members)}")
    if diff_tests:
        findings.append(f"CITED_TESTS - REAL_TESTS = {sorted(diff_tests)}")

    print(f"CITED_PATHS - REAL_PATHS = {diff_paths}")
    print(f"CITED_CLASSES - REAL_CLASSES = {diff_classes}")
    print(f"CITED_FUNCTIONS - REAL_FUNCTIONS = {diff_functions}")
    print(f"CITED_METHODS - REAL_METHODS = {diff_methods}")
    print(f"CITED_ENUM_MEMBERS - REAL_ENUM_MEMBERS = {diff_enum_members}")
    print(f"CITED_TESTS - REAL_TESTS = {diff_tests}")

    if findings:
        print(
            f"\nFAIL: S5 Acceptance Symbol Verification found {len(findings)} issue(s):",
            file=sys.stderr,
        )
        for f in findings:
            print(f"  - {f}", file=sys.stderr)
        return 1, diffs

    print(
        f"\nPASS: S5 Acceptance Symbol Verification passed.\n"
        f"  - Zero banned phantom symbols found\n"
        f"  - {len(candidates['paths'])} cited paths verified\n"
        f"  - {len(candidates['classes'])} cited classes verified\n"
        f"  - {len(candidates['functions'])} cited functions verified\n"
        f"  - {len(candidates['methods'])} cited methods verified\n"
        f"  - {len(candidates['enum_members'])} cited enum members verified\n"
        f"  - {len(candidates['tests'])} cited test functions verified against AST"
    )
    return 0, diffs


def verify_acceptance_symbols(
    doc_path: Path | str = ACCEPTANCE_DOC,
    content: str | None = None,
    src_dir: Path | None = None,
    test_dir: Path | None = None,
) -> int:
    """Run verification and return 0 on success, 1 on failure."""
    code, _ = run_symbol_verification(
        doc_path=doc_path,
        content=content,
        src_dir=src_dir,
        test_dir=test_dir,
    )
    return code


def main() -> None:
    sys.exit(verify_acceptance_symbols())


if __name__ == "__main__":
    main()
