"""Verify the S8-B01 operational Strategy capability and safety boundary."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

STRATEGY_ROOT = Path("src/btg_ai_trader/strategy")
RISK_ENGINE_MODULE = "btg_ai_trader.risk_engine"
ALLOWED_RISK_ADAPTER_IMPORTS = {"EconomicDirection", "RiskProposal"}
ALLOWED_MODULE_IMPORTS = {"hashlib", "json", "types", "weakref"}
ALLOWED_MODULE_ATTRIBUTES = {
    "hashlib": {"sha256"},
    "json": {"dumps"},
    "types": {"MappingProxyType"},
    "weakref": {"ReferenceType", "ref"},
}
ALLOWED_FROM_IMPORTS = {
    "__future__": {"annotations"},
    "collections.abc": {"Callable", "Mapping", "Sequence"},
    "dataclasses": {"dataclass", "field"},
    "datetime": {"UTC", "datetime", "timedelta"},
    "decimal": {"Decimal"},
    "enum": {"Enum"},
    "btg_ai_trader.observer.identity": {"TradableInstrumentId"},
    "btg_ai_trader.strategy.domain": {
        "CandidateStrategy",
        "ComparisonOperator",
        "DecisionOpportunity",
        "DecisionReason",
        "EconomicDirection",
        "EconomicObjective",
        "StrategyDecision",
        "StrategyDisposition",
        "StrategyEvaluationResult",
        "StrategyEvidenceQuality",
        "StrategyRule",
        "TradeIntent",
    },
    "btg_ai_trader.strategy.engine": {
        "evaluate_strategy",
        "verify_deterministic_equivalence",
    },
    "btg_ai_trader.strategy.risk_adapter": {"to_risk_proposal"},
}

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

FORBIDDEN_REFLECTION_NAMES = {
    "__builtins__",
    "__class__",
    "__closure__",
    "__code__",
    "__dict__",
    "__func__",
    "__getattribute__",
    "__globals__",
    "__loader__",
    "__mro__",
    "__base__",
    "__bases__",
    "__self__",
    "__spec__",
    "__subclasses__",
    "__traceback__",
    "tb_frame",
    "tb_next",
    "f_globals",
    "f_locals",
    "f_builtins",
    "f_back",
    "f_code",
    "gi_frame",
    "cr_frame",
    "ag_frame",
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
    "submit_order",
    "cancel_order",
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
    "getattr",
    "setattr",
    "delattr",
    "globals",
    "locals",
    "vars",
    "dir",
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
    "datetime.today",
    "datetime.datetime.today",
}

FORBIDDEN_IO_METHODS = {
    "read",
    "write",
    "readline",
    "readlines",
    "writelines",
    "readinto",
    "readinto1",
    "seek",
    "truncate",
    "flush",
    "write_text",
    "write_bytes",
    "read_text",
    "read_bytes",
    "get_data",
    "set_data",
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
    if isinstance(node, ast.NamedExpr):
        return _resolve_expr(node.value, aliases)
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        parts: list[str] = []
        current: ast.AST = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        root = _resolve_expr(current, aliases)
        if root:
            parts.append(root)
        return ".".join(reversed(parts))
    return ""


def _contains_module_value(node: ast.AST, aliases: dict[str, str]) -> bool:
    """Detect module values transferred through opaque binding expressions.

    Attribute calls like json.dumps() do not transfer the module itself.
    Direct, simple module aliases are handled by the existing alias map.
    Unsupported compound bindings fail closed rather than being guessed.
    """
    if isinstance(node, ast.Attribute):
        return False
    if isinstance(node, ast.Name):
        return _resolve_expr(node, aliases) in ALLOWED_MODULE_IMPORTS
    return any(
        _contains_module_value(child, aliases) for child in ast.iter_child_nodes(node)
    )


def _has_module_default(arguments: ast.arguments, aliases: dict[str, str]) -> bool:
    """Reject module capabilities captured in positional or keyword defaults."""
    return any(
        _contains_module_value(value, aliases)
        for value in (*arguments.defaults, *arguments.kw_defaults)
        if value is not None
    )



# A closed set of reviewed Strategy call sites. All new call capabilities must
# be explicitly reviewed and added here rather than implicitly inheriting the
# authority of an arbitrary caller-supplied receiver or callback.
ALLOWED_STRATEGY_CALLS = frozenset(
    {
        "ValueError",
        "Decimal",
        "RiskProposal",
        "StrategyDecision",
        "StrategyDecision._issue",
        "StrategyEvaluationResult",
        "TradeIntent",
        "TradeIntent._build",
        "_digest",
        "_evaluate_outcome",
        "_freeze_signals",
        "_issue_strategy_decision",
        "_issue_trade_intent",
        "_jsonable",
        "_make_decision_issuance",
        "_make_intent_issuance",
        "_matches",
        "_require_aware",
        "_require_decimal",
        "_require_text",
        "_utc_instant",
        "_verify_decision_issuance",
        "_verify_intent_issuance",
        "all",
        "any",
        "dataclass",
        "evaluate_strategy",
        "field",
        "hashlib.sha256",
        "id",
        "isinstance",
        "json.dumps",
        "ledger.get",
        "ledger.pop",
        "len",
        "object.__setattr__",
        "records.get",
        "remember",
        "set",
        "signals.items",
        "sorted",
        "str",
        "self._expected_digest",
        "timedelta",
        "tuple",
        "types.MappingProxyType",
        "value.astimezone",
        "value.is_finite",
        "value.isoformat",
        "value.items",
        "value.strip",
        "value.tzinfo.utcoffset",
        "weakref.ref",
    }
)

# Narrowly permitted modules from the existing from-import contract.
# Resolve only audited functions/types imported from those modules.
ALLOWED_STRATEGY_IMPORTED_CALL_PREFIXES = (
    "dataclasses.",
    "decimal.",
    "datetime.",
    "btg_ai_trader.strategy.domain.",
    "btg_ai_trader.strategy.engine.",
    "btg_ai_trader.risk_engine.",
)

# Only these previously reviewed methods may be chained off an approved
# primitive-producing call. Generic attribute calls on unresolved objects
# never receive this allowance.
ALLOWED_STRATEGY_CALL_CHAINS = {
    ("json.dumps", "encode"),
    ("hashlib.sha256", "hexdigest"),
}


def _approved_strategy_call(
    node: ast.Call, aliases: dict[str, str], local_declarations: set[str]
) -> bool:
    """Permit only reviewed call sites or non-shadowed locally defined helpers."""
    name = _resolve_expr(node.func, aliases)
    if name in ALLOWED_STRATEGY_CALLS or name in local_declarations:
        return True
    for prefix in ALLOWED_STRATEGY_IMPORTED_CALL_PREFIXES:
        if name.startswith(prefix) and name[len(prefix):] in ALLOWED_STRATEGY_CALLS:
            return True
    if (
        isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Call)
    ):
        inner = _resolve_expr(node.func.value.func, aliases)
        return (inner, node.func.attr) in ALLOWED_STRATEGY_CALL_CHAINS
    # The only supported indirect call is the weakref stored by our
    # issuance ledger. All arbitrary subscripted callbacks are denied.
    return (
        isinstance(node.func, ast.Subscript)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "current"
        and isinstance(node.func.slice, ast.Constant)
        and node.func.slice.value == 0
    )


def _scan_ast(path: Path, tree: ast.AST) -> list[Finding]:
    findings: list[Finding] = []
    aliases: dict[str, str] = {}
    # Local function/class construction is allowed after scanning their bodies,
    # but a parameter or assignment can shadow that symbol with an injected
    # callback. Exclude such names from this dynamic whitelist.
    local_declarations: set[str] = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
    }
    shadowed: set[str] = set()
    parameters: set[str] = set()
    for declaration in ast.walk(tree):
        if isinstance(declaration, ast.arg):
            shadowed.add(declaration.arg)
            parameters.add(declaration.arg)
        elif isinstance(declaration, ast.Assign):
            shadowed.update(
                bound.id for target in declaration.targets
                for bound in ast.walk(target) if isinstance(bound, ast.Name)
            )
        elif isinstance(declaration, ast.AnnAssign | ast.NamedExpr):
            shadowed.update(
                bound.id for bound in ast.walk(declaration.target)
                if isinstance(bound, ast.Name)
            )
        elif isinstance(declaration, ast.For | ast.AsyncFor | ast.comprehension):
            shadowed.update(
                bound.id for bound in ast.walk(declaration.target)
                if isinstance(bound, ast.Name)
            )
    local_declarations.difference_update(shadowed)
    normalized = str(path).replace("\\", "/")
    risk_adapter = normalized.endswith("/strategy/risk_adapter.py")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
                if alias.name.startswith(RISK_ENGINE_MODULE):
                    rule = (
                        "Risk Engine namespace import forbidden in risk_adapter"
                        if risk_adapter
                        else "Risk Engine import allowed only in risk_adapter"
                    )
                    findings.append(Finding(normalized, node.lineno, rule))
                    continue
                if alias.name not in ALLOWED_MODULE_IMPORTS:
                    rule = (
                        f"forbidden import: {alias.name}"
                        if _is_forbidden_import(alias.name)
                        else f"import outside Strategy allowlist: {alias.name}"
                    )
                    findings.append(Finding(normalized, node.lineno, rule))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                qualified = f"{module}.{alias.name}" if module else alias.name
                aliases[alias.asname or alias.name] = qualified

                risk_import = module.startswith(RISK_ENGINE_MODULE) or qualified.startswith(
                    RISK_ENGINE_MODULE
                )
                if risk_import:
                    if not risk_adapter:
                        findings.append(
                            Finding(
                                normalized,
                                node.lineno,
                                "Risk Engine import allowed only in risk_adapter",
                            )
                        )
                        continue
                    if (
                        module != RISK_ENGINE_MODULE
                        or alias.name not in ALLOWED_RISK_ADAPTER_IMPORTS
                    ):
                        findings.append(
                            Finding(
                                normalized,
                                node.lineno,
                                "risk_adapter may import only EconomicDirection and RiskProposal",
                            )
                        )
                    continue

                allowed_symbols = ALLOWED_FROM_IMPORTS.get(module)
                if allowed_symbols is None:
                    if _is_forbidden_import(module):
                        rule = f"forbidden import: {module}"
                    elif _is_forbidden_import(qualified):
                        rule = f"forbidden import: {qualified}"
                    else:
                        rule = f"import outside Strategy allowlist: {module or qualified}"
                    findings.append(Finding(normalized, node.lineno, rule))
                    continue
                if alias.name not in allowed_symbols:
                    findings.append(
                        Finding(
                            normalized,
                            node.lineno,
                            f"symbol outside Strategy import allowlist: {qualified}",
                        )
                    )
        elif isinstance(node, ast.Assign):
            resolved = _resolve_expr(node.value, aliases)
            simple_targets = all(isinstance(target, ast.Name) for target in node.targets)
            if _contains_module_value(node.value, aliases) and not (
                simple_targets and resolved in ALLOWED_MODULE_IMPORTS
            ):
                findings.append(
                    Finding(
                        normalized,
                        node.lineno,
                        "unverifiable module alias binding: compound assignment",
                    )
                )
            if (
                resolved in ALLOWED_MODULE_IMPORTS
                or (resolved in ALLOWED_STRATEGY_CALLS and "." in resolved)
            ) and simple_targets:
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id not in parameters:
                        aliases[target.id] = resolved
            else:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        aliases.pop(target.id, None)
        elif isinstance(node, ast.AnnAssign):
            resolved = _resolve_expr(node.value, aliases) if node.value is not None else ""
            if node.value is not None and _contains_module_value(node.value, aliases):
                findings.append(
                    Finding(
                        normalized,
                        node.lineno,
                        "unverifiable module alias binding: annotated assignment",
                    )
                )
            if isinstance(node.target, ast.Name):
                aliases.pop(node.target.id, None)
        elif isinstance(node, ast.NamedExpr):
            resolved = _resolve_expr(node.value, aliases)
            if isinstance(node.target, ast.Name):
                if resolved in ALLOWED_MODULE_IMPORTS:
                    aliases[node.target.id] = resolved
                else:
                    aliases.pop(node.target.id, None)
                    if _contains_module_value(node.value, aliases):
                        findings.append(
                            Finding(
                                normalized,
                                node.lineno,
                                "unverifiable module alias binding: named expression",
                            )
                        )
        elif isinstance(node, ast.For | ast.AsyncFor | ast.comprehension):
            if _contains_module_value(node.iter, aliases):
                findings.append(
                    Finding(
                        normalized,
                        node.iter.lineno,
                        "unverifiable module alias binding: loop/comprehension",
                    )
                )
        elif isinstance(node, ast.Return | ast.Yield | ast.YieldFrom):
            if node.value is not None and _contains_module_value(node.value, aliases):
                findings.append(
                    Finding(
                        normalized,
                        node.lineno,
                        "unverifiable module alias binding: returned/yielded module",
                    )
                )
        elif isinstance(node, ast.Lambda):
            if _contains_module_value(node.body, aliases):
                findings.append(
                    Finding(
                        normalized,
                        node.lineno,
                        "unverifiable module alias binding: lambda module return",
                    )
                )
            if _has_module_default(node.args, aliases):
                findings.append(
                    Finding(
                        normalized,
                        node.lineno,
                        "unverifiable module alias binding: lambda argument default",
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
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if _has_module_default(node.args, aliases):
                    findings.append(
                        Finding(
                            normalized,
                            node.lineno,
                            "unverifiable module alias binding: function argument default",
                        )
                    )
        elif isinstance(node, ast.Call):
            if not _approved_strategy_call(node, aliases, local_declarations):
                findings.append(
                    Finding(
                        normalized,
                        node.lineno,
                        "call outside audited Strategy allowlist",
                    )
                )
            # A module passed to an unknown function can emerge via its
            # return value or be used for I/O. Do not assume pure helpers.
            # This also catches nested, *args and **kwargs transfers.
            if any(
                _contains_module_value(argument, aliases)
                for argument in (*node.args, *(kw.value for kw in node.keywords))
            ):
                findings.append(
                    Finding(
                        normalized,
                        node.lineno,
                        "unverifiable module alias binding: module-valued call argument",
                    )
                )
            call_name = _resolve_expr(node.func, aliases)
            if call_name in FORBIDDEN_CALLS:
                findings.append(Finding(normalized, node.lineno, f"forbidden call: {call_name}"))
            if isinstance(node.func, ast.Attribute) and node.func.attr in FORBIDDEN_IO_METHODS:
                findings.append(
                    Finding(normalized, node.lineno, f"forbidden I/O method: {node.func.attr}")
                )
        elif isinstance(node, ast.Name):
            resolved = _resolve_expr(node, aliases)
            if resolved in FORBIDDEN_CALLS:
                findings.append(
                    Finding(
                        normalized,
                        node.lineno,
                        f"forbidden callable reference: {resolved}",
                    )
                )
            if node.id in FORBIDDEN_REFLECTION_NAMES:
                findings.append(
                    Finding(
                        normalized,
                        node.lineno,
                        f"forbidden reflection namespace: {node.id}",
                    )
                )
            if node.id in FORBIDDEN_OPERATIONAL_NAMES:
                findings.append(
                    Finding(normalized, node.lineno, f"forbidden operational name: {node.id}")
                )
        elif isinstance(node, ast.Attribute):
            resolved = _resolve_expr(node, aliases)
            module_name, separator, remainder = resolved.partition(".")
            if separator and module_name in ALLOWED_MODULE_ATTRIBUTES:
                first_attribute = remainder.split(".", maxsplit=1)[0]
                if first_attribute not in ALLOWED_MODULE_ATTRIBUTES[module_name]:
                    findings.append(
                        Finding(
                            normalized,
                            node.lineno,
                            f"module attribute outside Strategy allowlist: {resolved}",
                        )
                    )
            if resolved in FORBIDDEN_CALLS:
                findings.append(
                    Finding(
                        normalized,
                        node.lineno,
                        f"forbidden callable reference: {resolved}",
                    )
                )
            if node.attr in FORBIDDEN_REFLECTION_NAMES:
                findings.append(
                    Finding(
                        normalized,
                        node.lineno,
                        f"forbidden reflection namespace: {node.attr}",
                    )
                )
            if node.attr in FORBIDDEN_OPERATIONAL_NAMES:
                findings.append(
                    Finding(
                        normalized,
                        node.lineno,
                        f"forbidden operational attribute: {node.attr}",
                    )
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
