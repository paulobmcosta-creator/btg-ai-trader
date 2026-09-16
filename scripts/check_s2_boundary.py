"""Verify the Sprint 2 replay/data boundary without applying the Sprint 1 scanner."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

S2_ROOTS = (
    Path("src/btg_ai_trader/replay"),
    Path("src/btg_ai_trader/data_platform"),
)

FORBIDDEN_IMPORT_PREFIXES = {
    "MetaTrader5",
    "requests",
    "httpx",
    "aiohttp",
    "socket",
}

FORBIDDEN_NAMES = {
    "TradeIntent",
    "StrategyDecision",
    "StrategyEngine",
    "SignalGenerator",
    "RiskAuthorization",
    "RiskEngine",
    "OrderIntent",
    "OrderPlan",
    "ExecutionOrder",
    "ExecutionEngine",
    "OrderManager",
    "FinancialLedger",
    "PositionTracker",
    "PaperExecution",
    "order_send",
    "order_check",
    "order_calc_margin",
    "account_info",
    "positions_get",
}

FORBIDDEN_ECONOMIC_NAMES = {
    "PnL",
    "ProfitAndLoss",
    "SlippageModel",
    "FeeModel",
    "SpreadModel",
    "FillModel",
    "QueueFillModel",
    "EconomicBacktest",
}

WALL_CLOCK_CALLS = {
    "time.sleep",
    "asyncio.sleep",
    "datetime.now",
    "datetime.datetime.now",
    "datetime.utcnow",
    "datetime.datetime.utcnow",
    "time.time",
}

SECRET_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws-key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    "github-token": re.compile(
        r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"
    ),
    "api-token": re.compile(r"\bsk-[A-Za-z0-9_-]{24,}"),
    "url-credential": re.compile(r"https?://[^\s/@:]+:[^\s/@]+@"),
}


@dataclass(frozen=True, slots=True)
class Finding:
    path: str
    line: int
    rule: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.rule}"


def _import_name(node: ast.Import | ast.ImportFrom) -> str:
    if isinstance(node, ast.Import):
        return node.names[0].name if node.names else ""
    return node.module or ""


def _is_forbidden_import(name: str) -> bool:
    return any(
        name == prefix or name.startswith(prefix + ".")
        for prefix in FORBIDDEN_IMPORT_PREFIXES
    )


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        parts: list[str] = [node.func.attr]
        value = node.func.value
        while isinstance(value, ast.Attribute):
            parts.append(value.attr)
            value = value.value
        if isinstance(value, ast.Name):
            parts.append(value.id)
        return ".".join(reversed(parts))
    return None


def scan_secrets(source: str, path_str: str) -> list[Finding]:
    findings: list[Finding] = []
    for rule, pattern in SECRET_PATTERNS.items():
        for match in pattern.finditer(source):
            line = source.count("\n", 0, match.start()) + 1
            findings.append(Finding(path_str, line, f"possible-secret:{rule}"))
    return findings


def check_python_ast(source: str, path_str: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        tree = ast.parse(source, filename=path_str)
    except SyntaxError as error:
        return [Finding(path_str, error.lineno or 1, "invalid-python")]

    prohibited_names = FORBIDDEN_NAMES | FORBIDDEN_ECONOMIC_NAMES
    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom):
            name = _import_name(node)
            if _is_forbidden_import(name):
                findings.append(Finding(path_str, node.lineno, f"forbidden-import:{name}"))
        if isinstance(node, ast.Name) and node.id in prohibited_names:
            findings.append(Finding(path_str, node.lineno, f"forbidden-name:{node.id}"))
        if isinstance(node, ast.Attribute) and node.attr in prohibited_names:
            findings.append(Finding(path_str, node.lineno, f"forbidden-attribute:{node.attr}"))
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            if node.name in prohibited_names:
                findings.append(
                    Finding(path_str, node.lineno, f"forbidden-definition:{node.name}")
                )
        if isinstance(node, ast.Call):
            called = _call_name(node)
            if called in WALL_CLOCK_CALLS:
                findings.append(Finding(path_str, node.lineno, f"wall-clock-call:{called}"))
            if called is not None and called.split(".")[-1] in FORBIDDEN_NAMES:
                findings.append(Finding(path_str, node.lineno, f"forbidden-call:{called}"))
    return findings


def check_file(path: Path) -> list[Finding]:
    path_str = str(path)
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        return [Finding(path_str, 1, f"unreadable-file:{type(err).__name__}")]

    findings = scan_secrets(source, path_str)
    if path.suffix == ".py":
        findings.extend(check_python_ast(source, path_str))
    return findings


def verify_s2_boundary(roots: tuple[Path, ...] = S2_ROOTS) -> list[Finding]:
    findings: list[Finding] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if "__pycache__" in path.parts:
                continue
            if path.is_symlink():
                findings.append(Finding(str(path), 1, "s2-symlink-rejected"))
                continue
            if path.is_file():
                findings.extend(check_file(path))
    return findings


def main() -> int:
    findings = verify_s2_boundary(S2_ROOTS)
    if findings:
        for finding in findings:
            print(finding)
        return 1

    file_count = 0
    for root in S2_ROOTS:
        if root.exists():
            file_count += sum(
                1 for p in root.rglob("*")
                if p.is_file() and not p.is_symlink() and "__pycache__" not in p.parts
            )

    print(f"S2 boundary PASS: {file_count} Sprint 2 file(s) inspected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
