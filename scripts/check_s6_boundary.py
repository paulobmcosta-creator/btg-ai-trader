"""Verify Sprint 6 Scenario Engine capability and security boundaries."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

S6_ROOTS = (Path("src/btg_ai_trader/scenario_engine"),)

FORBIDDEN_IMPORT_PREFIXES = {
    "MetaTrader5",
    "requests",
    "httpx",
    "aiohttp",
    "socket",
    "urllib.request",
    "subprocess",
    "pickle",
    "joblib",
    "cloudpickle",
    "dill",
    "random",
    "secrets",
    "numpy",
    "scipy",
    "sklearn",
    "btg_ai_trader.ml_engine",
}

FORBIDDEN_OPERATIONAL_NAMES = {
    "TradeIntent",
    "StrategyDecision",
    "StrategyEngine",
    "SignalGenerator",
    "SignalEngine",
    "RiskDecision",
    "RiskAuthorization",
    "RiskEngine",
    "OrderIntent",
    "OrderPlan",
    "ExecutionOrder",
    "ExecutionEngine",
    "OrderManager",
    "FinancialLedger",
    "PaperExecution",
    "LiveExecution",
    "order_send",
    "order_check",
    "order_calc_margin",
    "account_info",
    "positions_get",
}

FORBIDDEN_CALLS = {
    "__import__",
    "eval",
    "exec",
    "importlib.import_module",
    "pickle.load",
    "pickle.loads",
    "joblib.load",
    "cloudpickle.load",
    "cloudpickle.loads",
    "dill.load",
    "dill.loads",
    "subprocess.Popen",
    "subprocess.run",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
    "os.system",
    "os.popen",
    "os.spawn",
    "socket.socket",
    "uuid4",
    "uuid.uuid4",
    "os.urandom",
    "random.random",
    "random.randint",
    "random.randrange",
    "random.choice",
    "random.shuffle",
    "time.time",
    "datetime.now",
    "datetime.datetime.now",
    "datetime.utcnow",
    "datetime.datetime.utcnow",
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


def _is_forbidden_import(name: str) -> bool:
    return any(name == prefix or name.startswith(prefix + ".") for prefix in FORBIDDEN_IMPORT_PREFIXES)


def _resolve_expr(node: ast.AST, aliases: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        parts: list[str] = []
        current: ast.AST = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(aliases.get(current.id, current.id))
        return ".".join(reversed(parts))
    return ""


def _scan_ast(path: Path, tree: ast.AST) -> list[Finding]:
    findings: list[Finding] = []
    aliases: dict[str, str] = {}
    normalized = str(path).replace("\\", "/")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
                if _is_forbidden_import(alias.name):
                    findings.append(
                        Finding(normalized, node.lineno, f"forbidden import: {alias.name}")
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if _is_forbidden_import(module):
                findings.append(Finding(normalized, node.lineno, f"forbidden import: {module}"))
            for alias in node.names:
                canonical = f"{module}.{alias.name}" if module else alias.name
                aliases[alias.asname or alias.name] = canonical
                if _is_forbidden_import(canonical):
                    findings.append(
                        Finding(normalized, node.lineno, f"forbidden import: {canonical}")
                    )
        elif isinstance(node, ast.Call):
            call_name = _resolve_expr(node.func, aliases)
            if call_name in FORBIDDEN_CALLS:
                findings.append(Finding(normalized, node.lineno, f"forbidden call: {call_name}"))
            if _is_forbidden_import(call_name):
                findings.append(
                    Finding(normalized, node.lineno, f"forbidden external call: {call_name}")
                )
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_OPERATIONAL_NAMES:
            findings.append(
                Finding(normalized, node.lineno, f"forbidden operational name: {node.id}")
            )
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_OPERATIONAL_NAMES:
            findings.append(
                Finding(normalized, node.lineno, f"forbidden operational attribute: {node.attr}")
            )
    return findings


def _scan_text(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    normalized = str(path).replace("\\", "/")
    for line_no, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in SECRET_PATTERNS.items():
            if pattern.search(line):
                findings.append(
                    Finding(normalized, line_no, f"suspected credential pattern: {kind}")
                )
    return findings


def scan_file(path: Path) -> list[Finding]:
    if path.is_symlink():
        return [Finding(str(path).replace("\\", "/"), 1, "symlinks are forbidden")]
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [Finding(str(path).replace("\\", "/"), 1, "file is not valid UTF-8 text")]
    except OSError as error:
        return [Finding(str(path).replace("\\", "/"), 1, f"read error: {error}")]

    findings = _scan_text(path, text)
    if path.suffix == ".py":
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as error:
            return [
                Finding(
                    str(path).replace("\\", "/"),
                    error.lineno or 1,
                    f"syntax error: {error}",
                )
            ]
        findings.extend(_scan_ast(path, tree))
    return findings


def scan_tree(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not root.exists():
        return findings
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.parts:
            continue
        if path.is_dir():
            if path.is_symlink():
                findings.append(
                    Finding(str(path).replace("\\", "/"), 1, "directory symlink forbidden")
                )
            continue
        findings.extend(scan_file(path))
    return findings


def main() -> int:
    findings: list[Finding] = []
    for root in S6_ROOTS:
        findings.extend(scan_tree(root))
    if findings:
        print(f"FAILED: {len(findings)} Sprint 6 boundary violation(s):")
        for finding in findings:
            print(f"  {finding}")
        return 1
    print("PASS: Sprint 6 Scenario Engine boundary verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
