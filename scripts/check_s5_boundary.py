"""Verify the Sprint 5 ML Engine capability boundary and integrity.

Checks that src/btg_ai_trader/ml_engine adheres strictly to:
- SPRINT_5_READ_ONLY_BY_CONSTRUCTION = TRUE
- SPRINT_5_EXECUTION_PROHIBITED = TRUE
- Prohibits broker imports, network calls, order execution, strategy/risk symbols
- Prohibits deep learning (torch/tensorflow) and AutoML tools
- Prohibits wall-clock time in core ML evaluation/inference
- Prohibits unseeded stochastics and secrets/credentials
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

S5_ROOTS = (Path("src/btg_ai_trader/ml_engine"),)

FORBIDDEN_IMPORT_PREFIXES = {
    "MetaTrader5",
    "requests",
    "httpx",
    "aiohttp",
    "socket",
    "urllib.request",
    "xgboost",
    "lightgbm",
    "catboost",
    "tensorflow",
    "torch",
    "keras",
    "optuna",
    "hyperopt",
    "automl",
    "auto_sklearn",
    "flaml",
    "mlflow",
    "wandb",
}

FORBIDDEN_OPERATIONAL_NAMES = {
    "TradeIntent",
    "StrategyDecision",
    "StrategyEngine",
    "SignalGenerator",
    "SignalEngine",
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

FORBIDDEN_UNSAFE_CALLS = {
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
}

FORBIDDEN_PROCESS_CALLS = {
    "subprocess.Popen",
    "subprocess.run",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
    "os.system",
    "os.popen",
    "os.spawn",
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

FORBIDDEN_STOCHASTIC_EXACT = {
    "uuid4",
    "uuid.uuid4",
    "os.urandom",
    "urandom",
    "SystemRandom",
    "random.SystemRandom",
    "secrets",
}

FORBIDDEN_STOCHASTIC_PREFIXES = (
    "secrets.",
)

FORBIDDEN_STOCHASTIC_MODULES = {"secrets"}

SECRET_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws-key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    "github-token": re.compile(
        r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"
    ),
    "api-token": re.compile(r"\bsk-[A-Za-z0-9_-]{24,}"),
    "url-credential": re.compile(r"https?://[^\s/@:]+:[^\s/@]+@"),
}
SECRET_NAME = re.compile(
    r"(?:password|secret|api[_-]?key|access[_-]?token|auth[_-]?token)", re.I
)


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


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts: list[str] = []
        curr: ast.AST = func
        while isinstance(curr, ast.Attribute):
            parts.append(curr.attr)
            curr = curr.value
        if isinstance(curr, ast.Name):
            parts.append(curr.id)
        return ".".join(reversed(parts))
    return ""


def _is_forbidden_stochastic_call(cname: str) -> bool:
    if cname in FORBIDDEN_STOCHASTIC_EXACT:
        return True
    if any(cname.startswith(p) for p in FORBIDDEN_STOCHASTIC_PREFIXES):
        return True
    parts = cname.split(".")
    if parts[0] in FORBIDDEN_STOCHASTIC_MODULES or parts[0] in FORBIDDEN_STOCHASTIC_EXACT:
        return True
    return False


def _resolve_expr(
    node: ast.AST,
    module_aliases: dict[str, str],
    symbol_aliases: dict[str, str],
) -> str:
    if isinstance(node, ast.Name):
        if node.id in symbol_aliases:
            return symbol_aliases[node.id]
        if node.id in module_aliases:
            return module_aliases[node.id]
        return node.id
    if isinstance(node, ast.Attribute):
        parts: list[str] = []
        curr: ast.AST = node
        while isinstance(curr, ast.Attribute):
            parts.append(curr.attr)
            curr = curr.value
        if isinstance(curr, ast.Name):
            base = curr.id
            if base in symbol_aliases:
                base = symbol_aliases[base]
            elif base in module_aliases:
                base = module_aliases[base]
            parts.append(base)
            return ".".join(reversed(parts))
    return ""


def _scan_ast(path: Path, tree: ast.AST) -> list[Finding]:
    findings: list[Finding] = []
    str_path = str(path).replace("\\", "/")
    module_aliases: dict[str, str] = {}
    symbol_aliases: dict[str, str] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod_name = alias.name
                local_name = alias.asname or alias.name
                module_aliases[local_name] = mod_name
                if (
                    mod_name in FORBIDDEN_STOCHASTIC_MODULES
                    or mod_name.startswith("secrets.")
                ):
                    findings.append(
                        Finding(str_path, node.lineno, f"forbidden stochastic import: {mod_name}")
                    )
                if _is_forbidden_import(mod_name):
                    findings.append(Finding(str_path, node.lineno, f"forbidden import: {mod_name}"))
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if (
                mod in FORBIDDEN_STOCHASTIC_MODULES
                or mod.startswith("secrets.")
            ):
                findings.append(
                    Finding(str_path, node.lineno, f"forbidden stochastic import: {mod}")
                )
            for alias in node.names:
                imported_symbol = alias.name
                local_name = alias.asname or alias.name
                canonical_symbol = f"{mod}.{imported_symbol}" if mod else imported_symbol
                symbol_aliases[local_name] = canonical_symbol
                module_aliases[local_name] = canonical_symbol

                if imported_symbol == "uuid4":
                    findings.append(
                        Finding(str_path, node.lineno, "forbidden stochastic import: uuid4")
                    )
                elif imported_symbol == "urandom" and mod == "os":
                    findings.append(
                        Finding(str_path, node.lineno, "forbidden stochastic import: os.urandom")
                    )
                elif imported_symbol == "SystemRandom":
                    findings.append(
                        Finding(str_path, node.lineno, "forbidden stochastic import: SystemRandom")
                    )
                elif (
                    mod in FORBIDDEN_STOCHASTIC_MODULES
                    or mod.startswith("secrets")
                ):
                    findings.append(
                        Finding(
                            str_path,
                            node.lineno,
                            f"forbidden stochastic import: {canonical_symbol}",
                        )
                    )
                elif _is_forbidden_import(canonical_symbol):
                    findings.append(
                        Finding(str_path, node.lineno, f"forbidden import: {canonical_symbol}")
                    )
                elif canonical_symbol in FORBIDDEN_PROCESS_CALLS:
                    findings.append(
                        Finding(
                            str_path,
                            node.lineno,
                            f"forbidden process import: {canonical_symbol}",
                        )
                    )
                elif canonical_symbol in WALL_CLOCK_CALLS:
                    findings.append(
                        Finding(
                            str_path,
                            node.lineno,
                            f"forbidden wall-clock import: {canonical_symbol}",
                        )
                    )
                elif imported_symbol in FORBIDDEN_OPERATIONAL_NAMES:
                    findings.append(
                        Finding(
                            str_path,
                            node.lineno,
                            f"forbidden operational import: {imported_symbol}",
                        )
                    )

            imp = _import_name(node)
            if _is_forbidden_import(imp):
                findings.append(Finding(str_path, node.lineno, f"forbidden import: {imp}"))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    target_name = target.id
                    if SECRET_NAME.search(target_name):
                        if (
                            isinstance(node.value, ast.Constant)
                            and isinstance(node.value.value, str)
                        ):
                            val = node.value.value.strip()
                            if val and not val.startswith("$") and not val.startswith("env:"):
                                findings.append(
                                    Finding(
                                        str_path,
                                        node.lineno,
                                        f"suspected literal credential in {target_name}",
                                    )
                                )
                    if isinstance(node.value, ast.Name):
                        val_name = node.value.id
                        if val_name in module_aliases:
                            module_aliases[target_name] = module_aliases[val_name]
                        if val_name in symbol_aliases:
                            symbol_aliases[target_name] = symbol_aliases[val_name]
                    elif isinstance(node.value, ast.Attribute):
                        resolved_attr = _resolve_expr(node.value, module_aliases, symbol_aliases)
                        if resolved_attr:
                            symbol_aliases[target_name] = resolved_attr
        elif isinstance(node, ast.Name):
            if node.id in FORBIDDEN_OPERATIONAL_NAMES:
                findings.append(
                    Finding(str_path, node.lineno, f"forbidden operational name: {node.id}")
                )
        elif isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_OPERATIONAL_NAMES:
                findings.append(
                    Finding(str_path, node.lineno, f"forbidden operational attribute: {node.attr}")
                )
        elif isinstance(node, ast.Call):
            resolved_call = _resolve_expr(node.func, module_aliases, symbol_aliases)
            cname = resolved_call or _call_name(node)
            if cname in FORBIDDEN_UNSAFE_CALLS:
                findings.append(
                    Finding(str_path, node.lineno, f"forbidden unsafe dynamic/deserialization call: {cname}")
                )
            elif cname in WALL_CLOCK_CALLS:
                findings.append(
                    Finding(str_path, node.lineno, f"forbidden wall-clock call: {cname}")
                )
            elif cname in FORBIDDEN_PROCESS_CALLS:
                findings.append(
                    Finding(str_path, node.lineno, f"forbidden process call: {cname}")
                )
            elif _is_forbidden_import(cname):
                findings.append(
                    Finding(str_path, node.lineno, f"forbidden call to external module: {cname}")
                )
            elif _is_forbidden_stochastic_call(cname):
                findings.append(
                    Finding(
                        str_path,
                        node.lineno,
                        f"forbidden stochastic call in ML engine: {cname}",
                    )
                )
    return findings


def _scan_text(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    str_path = str(path).replace("\\", "/")
    for line_no, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in SECRET_PATTERNS.items():
            if pattern.search(line):
                findings.append(Finding(str_path, line_no, f"suspected credential pattern: {kind}"))
    return findings


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    str_path = str(path).replace("\\", "/")
    if path.is_symlink():
        return [Finding(str_path, 1, "symlinks are forbidden under boundary roots")]
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [Finding(str_path, 1, "file is not valid UTF-8 text")]
    except OSError as err:
        return [Finding(str_path, 1, f"read error: {err}")]

    findings.extend(_scan_text(path, text))
    if path.suffix == ".py":
        try:
            tree = ast.parse(text, filename=str_path)
        except SyntaxError as err:
            return [Finding(str_path, err.lineno or 1, f"syntax error: {err}")]
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
    all_findings: list[Finding] = []
    repo_root = Path.cwd()
    for rel_root in S5_ROOTS:
        target = repo_root / rel_root
        all_findings.extend(scan_tree(target))

    if all_findings:
        print(f"FAILED: {len(all_findings)} boundary violation(s) found:")
        for f in all_findings:
            print(f"  {f}")
        return 1

    print("PASS: Sprint 5 capability boundary verified successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
