"""Verify the S8-B01 operational Strategy capability and safety boundary."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

STRATEGY_ROOT = Path("src/btg_ai_trader/strategy")
RISK_ENGINE_MODULE = "btg_ai_trader.risk_engine"
ALLOWED_RISK_ADAPTER_IMPORTS = {"EconomicDirection", "RiskProposal"}

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
}

FORBIDDEN_OPERATIONAL_NAMES = {
    "AuthorizationAllocation",
    "OrderIntent",
    "OrderPlan",
    "ExecutionOrder",
    "EconomicExecutionCommand",
    "ExecutionAttempt",
    "FinancialLedger",
    "PaperExecution",
    "PaperTrader",
    "LiveExecution",
    "LiveTrader",
    "BrokerClient",
    "OrderManager",
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
    "compile",
    "open",
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

FORBIDDEN_IO_METHODS = {
    "write_text",
    "write_bytes",
    "read_text",
    "read_bytes",
    "open",
    "unlink",
    "rename",
    "replace",
    "mkdir",
    "rmdir",
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
    return any(
        name == prefix or name.startswith(prefix + ".")
        for prefix in FORBIDDEN_IMPORT_PREFIXES
    )


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
    risk_adapter = normalized.endswith("/strategy/risk_adapter.py")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
                if _is_forbidden_import(alias.name):
                    findings.append(
                        Finding(normalized, node.lineno, f"forbidden import: {alias.name}")
                    )
                if alias.name.startswith(RISK_ENGINE_MODULE):
                    rule = (
                        "Risk Engine namespace import forbidden in risk_adapter"
                        if risk_adapter
                        else "Risk Engine import allowed only in risk_adapter"
                    )
                    findings.append(Finding(normalized, node.lineno, rule))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            module_forbidden = _is_forbidden_import(module)
            if module_forbidden:
                findings.append(Finding(normalized, node.lineno, f"forbidden import: {module}"))

            for alias in node.names:
                qualified = f"{module}.{alias.name}" if module else alias.name
                aliases[alias.asname or alias.name] = qualified

                if not module_forbidden and _is_forbidden_import(qualified):
                    findings.append(
                        Finding(normalized, node.lineno, f"forbidden import: {qualified}")
                    )

                risk_import = module.startswith(RISK_ENGINE_MODULE) or qualified.startswith(
                    RISK_ENGINE_MODULE
                )
                if not risk_import:
                    continue
                if not risk_adapter:
                    findings.append(
                        Finding(
                            normalized,
                            node.lineno,
                            "Risk Engine import allowed only in risk_adapter",
                        )
                    )
                    continue
                if module != RISK_ENGINE_MODULE or alias.name not in ALLOWED_RISK_ADAPTER_IMPORTS:
                    findings.append(
                        Finding(
                            normalized,
                            node.lineno,
                            "risk_adapter may import only EconomicDirection and RiskProposal",
                        )
                    )
        elif isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            if node.name in FORBIDDEN_OPERATIONAL_NAMES:
                findings.append(
                    Finding(
                        normalized,
                        node.lineno,
                        f"forbidden operational declaration: {node.name}",
                    )
                )
        elif isinstance(node, ast.Call):
            call_name = _resolve_expr(node.func, aliases)
            if call_name in FORBIDDEN_CALLS:
                findings.append(Finding(normalized, node.lineno, f"forbidden call: {call_name}"))
            if isinstance(node.func, ast.Attribute) and node.func.attr in FORBIDDEN_IO_METHODS:
                findings.append(
                    Finding(normalized, node.lineno, f"forbidden I/O method: {node.func.attr}")
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


def main() -> int:
    if not STRATEGY_ROOT.is_dir():
        print("FAILED: operational Strategy package is absent")
        return 1

    findings: list[Finding] = []
    for path in sorted(STRATEGY_ROOT.rglob("*")):
        if "__pycache__" in path.parts:
            continue
        if path.is_dir():
            if path.is_symlink():
                findings.append(
                    Finding(
                        str(path).replace("\\", "/"),
                        1,
                        "directory symlink forbidden",
                    )
                )
            continue
        findings.extend(scan_file(path))

    if findings:
        print(f"FAILED: {len(findings)} S8 Strategy boundary violation(s):")
        for finding in findings:
            print(f"  {finding}")
        return 1
    print("PASS: S8 operational Strategy boundary verified; no Paper/Live/broker authority found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
