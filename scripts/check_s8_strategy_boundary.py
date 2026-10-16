"""Verify the S8-B01 operational Strategy capability and safety boundary."""

from __future__ import annotations

import ast
import hashlib
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
        "_utc_instant",
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



# A lexical exception is allowed only for read-only methods of validated
# domain inputs within their existing audited functions.
AUDITED_PARAMETER_METHODS = frozenset(
    {
        ("_require_text", "value.strip"),
        ("_require_aware", "value.tzinfo.utcoffset"),
        ("_utc_instant", "value.astimezone"),
        ("_require_decimal", "value.is_finite"),
        ("_jsonable", "value.isoformat"),
        ("_jsonable", "value.items"),
        ("_freeze_signals", "signals.items"),
        ("is_engine_issued", "self._expected_digest"),
    }
)


def _enclosing_functions(
    node: ast.AST, parents: dict[ast.AST, ast.AST]
) -> tuple[ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda, ...]:
    scopes: list[ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda] = []
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
            scopes.append(current)
    return tuple(scopes)


def _scope_parameters(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> set[str]:
    parameter_names: set[str] = set()
    for scope in _enclosing_functions(node, parents):
        args = scope.args
        parameter_names.update(arg.arg for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs))
        if args.vararg is not None:
            parameter_names.add(args.vararg.arg)
        if args.kwarg is not None:
            parameter_names.add(args.kwarg.arg)
    return parameter_names


def _call_root(node: ast.AST) -> str:
    current = node
    while isinstance(current, ast.Attribute | ast.Subscript):
        current = current.value
    return current.id if isinstance(current, ast.Name) else ""


def _approved_write_target(
    node: ast.Attribute | ast.Subscript,
    path: Path,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    if not isinstance(node, ast.Subscript) or not isinstance(node.ctx, ast.Store):
        return False
    if not str(path).replace("\\", "/").endswith("/strategy/domain.py"):
        return False
    if not isinstance(node.value, ast.Name):
        return False
    if node.value.id in _scope_parameters(node, parents):
        return False
    functions = {
        scope.name for scope in _enclosing_functions(node, parents)
        if isinstance(scope, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    return (
        (node.value.id == "frozen" and "_freeze_signals" in functions)
        or (
            node.value.id == "ledger"
            and bool(functions & {"_make_decision_issuance", "_make_intent_issuance"})
        )
    )



# A spelling in ALLOWED_STRATEGY_CALLS is never sufficient provenance.
# Detect unsafe rebinding in each lexical function and at module level;
# a locally bound callback must not inherit authority from an approved name.
def _trusted_assignment_source(node: ast.AST, aliases: dict[str, str]) -> bool:
    if isinstance(node, ast.Dict):
        return not node.keys and not node.values
    if isinstance(node, ast.Attribute):
        return _resolve_expr(node, aliases) in {"hashlib.sha256", "json.dumps"}
    if isinstance(node, ast.Name):
        return _resolve_expr(node, aliases) in ALLOWED_MODULE_IMPORTS
    if isinstance(node, ast.Call):
        return _resolve_expr(node.func, aliases) == "types.MappingProxyType"
    return False


def _lexical_scopes(
    node: ast.AST, parents: dict[ast.AST, ast.AST]
) -> tuple[ast.AST, ...]:
    scopes: list[ast.AST] = []
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(
            current, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda | ast.ClassDef
        ):
            scopes.append(current)
    return tuple(scopes)


def _root_scopes(
    parents: dict[ast.AST, ast.AST], node: ast.AST
) -> tuple[ast.AST, ...]:
    current = node
    while current in parents:
        current = parents[current]
    return (current,)


def _unsafe_binding_roots(
    tree: ast.AST,
    parents: dict[ast.AST, ast.AST],
    imported_aliases: dict[str, str],
    path: Path,
) -> dict[str, set[ast.AST]]:
    unsafe: dict[str, set[ast.AST]] = {}
    for bound in ast.walk(tree):
        if not isinstance(bound, ast.Name) or not isinstance(bound.ctx, ast.Store):
            continue
        scopes = _lexical_scopes(bound, parents)
        owner: ast.AST = scopes[0] if scopes else tree
        parent = parents.get(bound)
        while parent is not None and not isinstance(
            parent,
            ast.Assign | ast.AnnAssign | ast.NamedExpr | ast.For | ast.AsyncFor
            | ast.comprehension | ast.With | ast.AsyncWith,
        ):
            parent = parents.get(parent)
        trusted = False
        if isinstance(parent, ast.Assign | ast.AnnAssign | ast.NamedExpr):
            rhs = parent.value
            trusted = rhs is not None and _trusted_assignment_source(rhs, imported_aliases)
            if isinstance(rhs, ast.Call):
                # A verifier's retained read-only ledger supplies the weakref;
                # do not authorize untrusted getters or injected receivers.
                trusted = trusted or (
                    path.name == "domain.py"
                    and isinstance(owner, ast.FunctionDef)
                    and owner.name == "verify"
                    and bound.id == "current"
                    and _resolve_expr(rhs.func, imported_aliases) == "records.get"
                )
                # The two issuer factories are audited module-owned constructors.
                trusted = trusted or (
                    owner is tree
                    and bound.id.startswith(("_issue_", "_verify_"))
                    and _resolve_expr(rhs.func, imported_aliases)
                    in {"_make_decision_issuance", "_make_intent_issuance"}
                )
        if not trusted:
            unsafe.setdefault(bound.id, set()).add(owner)
    return unsafe


def _approved_strategy_call(
    node: ast.Call,
    aliases: dict[str, str],
    local_declarations: set[str],
    path: Path,
    parents: dict[ast.AST, ast.AST],
    unsafe_binding_roots: dict[str, set[ast.AST]],
) -> bool:
    """Deny injected capabilities even when they shadow audited names."""
    name = _resolve_expr(node.func, aliases)
    root = _call_root(node.func)
    current_scopes = _lexical_scopes(node, parents)
    if root and root in unsafe_binding_roots:
        unsafe_owners = unsafe_binding_roots[root]
        if next(iter(_root_scopes(parents, node))) in unsafe_owners or any(
            scope in unsafe_owners for scope in current_scopes
        ):
            return False
    scoped_parameters = _scope_parameters(node, parents)
    if root and root in scoped_parameters:
        functions = _enclosing_functions(node, parents)
        function_name = (
            functions[0].name
            if functions and isinstance(functions[0], ast.FunctionDef | ast.AsyncFunctionDef)
            else ""
        )
        if (
            path.name != "domain.py"
            or (function_name, name) not in AUDITED_PARAMETER_METHODS
        ):
            return False
    if name == "object.__setattr__":
        functions = _enclosing_functions(node, parents)
        if not (
            functions
            and isinstance(functions[0], ast.FunctionDef)
            and functions[0].name == "__post_init__"
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "self"
            and path.name == "domain.py"
        ):
            return False
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



# Explicitly reviewed iterable expressions in the existing immutable Strategy
# domain. This is deliberately NOT a general allowance for caller-supplied
# iterables: arbitrary __iter__/__next__ implementations can cause effects.
AUDITED_STRATEGY_ITERATIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("issue", "candidate.rules"),
        ("_jsonable", "sorted(value.items(), key=lambda pair: str(pair[0]))"),
        ("_jsonable", "value"),
        ("_freeze_signals", "sorted(signals.items())"),
        ("__post_init__", "self.rules"),
        ("__post_init__", "self.reason_codes"),
        ("required_signals", "self.rules"),
        ("candidate_digest", "self.rules"),
        ("_evaluate_outcome", "candidate.required_signals"),
        ("_evaluate_outcome", "candidate.rules"),
    }
)

AUDITED_STRATEGY_UNPACK_CALLS = frozenset(
    {
        ("issue", "_evaluate_outcome"),
        ("<module>", "_make_decision_issuance"),
        ("<module>", "_make_intent_issuance"),
    }
)


def _source_function(
    node: ast.AST, parents: dict[ast.AST, ast.AST]
) -> str:
    scopes = _enclosing_functions(node, parents)
    if scopes and isinstance(scopes[0], ast.FunctionDef | ast.AsyncFunctionDef):
        return scopes[0].name
    return "<module>"


def _literal_iterable(node: ast.AST) -> bool:
    """Only builtin literal containers; no starred unpacking or generators."""
    if isinstance(node, ast.Tuple | ast.List | ast.Set):
        return not any(isinstance(item, ast.Starred) for item in node.elts)
    if isinstance(node, ast.Dict):
        return all(key is not None for key in node.keys)
    return isinstance(node, ast.Constant) and isinstance(node.value, str | bytes)


def _approved_iteration(
    node: ast.AST, path: Path, parents: dict[ast.AST, ast.AST]
) -> bool:
    if _literal_iterable(node):
        return True
    return (
        path.name == "domain.py"
        and (_source_function(node, parents), ast.unparse(node))
        in AUDITED_STRATEGY_ITERATIONS
    )


def _approved_unpacking(
    rhs: ast.AST, path: Path, parents: dict[ast.AST, ast.AST]
) -> bool:
    if _literal_iterable(rhs):
        return True
    return (
        path.name == "domain.py"
        and isinstance(rhs, ast.Call)
        and (
            _source_function(rhs, parents),
            _resolve_expr(rhs.func, {}),
        ) in AUDITED_STRATEGY_UNPACK_CALLS
    )



# Decorators execute at definition time. Only the immutable domain's existing,
# module-level classes and known methods may use their reviewed decorators.
REVIEWED_DATACLASSES = {
    "EconomicObjective": False,
    "StrategyRule": False,
    "CandidateStrategy": False,
    "DecisionOpportunity": False,
    "StrategyDecision": True,
    "TradeIntent": True,
    "StrategyEvaluationResult": False,
}
REVIEWED_METHOD_DECORATORS = frozenset(
    {
        ("EconomicObjective", "objective_digest", "property"),
        ("StrategyRule", "rule_digest", "property"),
        ("CandidateStrategy", "required_signals", "property"),
        ("CandidateStrategy", "candidate_digest", "property"),
        ("CandidateStrategy", "candidate_id", "property"),
        ("DecisionOpportunity", "opportunity_digest", "property"),
        ("StrategyDecision", "is_engine_issued", "property"),
        ("StrategyDecision", "_issue", "classmethod"),
        ("TradeIntent", "is_engine_issued", "property"),
        ("TradeIntent", "_build", "classmethod"),
    }
)


def _unsafe_decorator_bindings(tree: ast.AST) -> set[str]:
    protected = {"dataclass", "property", "classmethod"}
    unsafe: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if node.id in protected:
                unsafe.add(node.id)
        elif isinstance(node, ast.arg) and node.arg in protected:
            unsafe.add(node.arg)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            if node.name in protected:
                unsafe.add(node.name)
    return unsafe


def _approved_decorator(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    decorator: ast.expr,
    path: Path,
    tree: ast.AST,
    parents: dict[ast.AST, ast.AST],
    imports: dict[str, str],
    unsafe_names: set[str],
) -> bool:
    if not str(path).replace("\\", "/").endswith("/strategy/domain.py"):
        return False
    parent = parents.get(node)
    if isinstance(node, ast.ClassDef):
        if parent is not tree or node.name not in REVIEWED_DATACLASSES:
            return False
        if "dataclass" in unsafe_names:
            return False
        if imports.get("dataclass") != "dataclasses.dataclass":
            return False
        if not isinstance(decorator, ast.Call) or decorator.args:
            return False
        if not isinstance(decorator.func, ast.Name):
            return False
        if decorator.func.id != "dataclass":
            return False
        actual = {keyword.arg: keyword.value for keyword in decorator.keywords}
        expected = {"frozen", "slots"}
        if REVIEWED_DATACLASSES[node.name]:
            expected.add("weakref_slot")
        return set(actual) == expected and all(
            isinstance(value, ast.Constant) and value.value is True
            for value in actual.values()
        )
    if not isinstance(node, ast.FunctionDef):
        return False
    if not isinstance(parent, ast.ClassDef) or parents.get(parent) is not tree:
        return False
    if not isinstance(decorator, ast.Name):
        return False
    if decorator.id in unsafe_names:
        return False
    return (parent.name, node.name, decorator.id) in REVIEWED_METHOD_DECORATORS



# Pin the exact already-reviewed Strategy runtime sources for attribute loads.
# A new attribute in any Strategy module MUST trigger a new explicit
# source-integrity review; spelling-only allowlists are not a security proof.
# Values are Git blob SHA-1s (SHA-1 over "blob <len>\\0" + raw bytes).
REVIEWED_STRATEGY_ATTRIBUTE_BLOBS = {
    "domain.py": "137f0998719f37f021280c6a672e6ceda606653f",
    "engine.py": "65cda8d12e2b640c68c45c1bcff538223a3b496b",
    "risk_adapter.py": "f549b88c1b3d07d501afd39419944c20e124c7f3",
}


def _reviewed_attribute_source(path: Path) -> bool:
    normalized = str(path).replace("\\", "/")
    expected = REVIEWED_STRATEGY_ATTRIBUTE_BLOBS.get(path.name)
    if expected is None or not normalized.endswith(f"/strategy/{path.name}"):
        return False
    data = path.read_bytes()
    git_blob = b"blob " + str(len(data)).encode("ascii") + b"\\0" + data
    return hashlib.sha1(git_blob).hexdigest() == expected


def _approved_unpinned_attribute_read(
    node: ast.Attribute,
    aliases: dict[str, str],
    imported_aliases: dict[str, str],
    parents: dict[ast.AST, ast.AST],
    unsafe_binding_roots: dict[str, set[ast.AST]],
) -> bool:
    """Only sealed primitive library reads; no caller-property dispatch."""
    root = _call_root(node)
    if not root or root in _scope_parameters(node, parents):
        return False
    if root in unsafe_binding_roots:
        unsafe_owners = unsafe_binding_roots[root]
        if next(iter(_root_scopes(parents, node))) in unsafe_owners or any(
            scope in unsafe_owners for scope in _lexical_scopes(node, parents)
        ):
            return False
    resolved = _resolve_expr(node, aliases)
    module, separator, member = resolved.partition(".")
    if separator and module in ALLOWED_MODULE_ATTRIBUTES:
        if (
            member in ALLOWED_MODULE_ATTRIBUTES[module]
            and (imported_aliases.get(root) == module or root in aliases)
        ):
            return True
    # Preserve the two audited methods chained from pure primitive calls.
    if isinstance(node.value, ast.Call):
        receiver = _resolve_expr(node.value.func, aliases)
        if (receiver, node.attr) in ALLOWED_STRATEGY_CALL_CHAINS:
            return True
    return False


def _scan_ast(path: Path, tree: ast.AST) -> list[Finding]:
    findings: list[Finding] = []
    aliases: dict[str, str] = {}
    parents = {
        child: node for node in ast.walk(tree)
        for child in ast.iter_child_nodes(node)
    }
    imported_aliases: dict[str, str] = {}
    for imported in ast.walk(tree):
        if isinstance(imported, ast.Import):
            for alias in imported.names:
                imported_aliases[alias.asname or alias.name] = alias.name
        elif isinstance(imported, ast.ImportFrom):
            for alias in imported.names:
                imported_aliases[alias.asname or alias.name] = (
                    f"{imported.module}.{alias.name}"
                )
    unsafe_binding_roots = _unsafe_binding_roots(
        tree, parents, imported_aliases, path
    )
    unsafe_decorator_names = _unsafe_decorator_bindings(tree)
    reviewed_attribute_source = _reviewed_attribute_source(path)
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
            if any(isinstance(target, ast.Tuple | ast.List) for target in node.targets):
                if not _approved_unpacking(node.value, path, parents):
                    findings.append(
                        Finding(
                            normalized,
                            node.lineno,
                            "unverified iterable destructuring forbidden",
                        )
                    )
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
            if (
                isinstance(node, ast.AsyncFor)
                or (isinstance(node, ast.comprehension) and node.is_async)
                or not _approved_iteration(node.iter, path, parents)
            ):
                findings.append(
                    Finding(
                        normalized,
                        node.iter.lineno,
                        "unverified iterable execution forbidden",
                    )
                )
            if _contains_module_value(node.iter, aliases):
                findings.append(
                    Finding(
                        normalized,
                        node.iter.lineno,
                        "unverifiable module alias binding: loop/comprehension",
                    )
                )
        elif isinstance(node, ast.Return | ast.Yield | ast.YieldFrom):
            if isinstance(node, ast.YieldFrom) and node.value is not None:
                if not _approved_iteration(node.value, path, parents):
                    findings.append(
                        Finding(
                            normalized,
                            node.lineno,
                            "unverified iterable execution forbidden",
                        )
                    )
            if node.value is not None and _contains_module_value(node.value, aliases):
                findings.append(
                    Finding(
                        normalized,
                        node.lineno,
                        "unverifiable module alias binding: returned/yielded module",
                    )
                )
        elif isinstance(node, ast.Starred) and isinstance(node.ctx, ast.Load):
            if not _approved_iteration(node.value, path, parents):
                findings.append(
                    Finding(
                        normalized,
                        node.lineno,
                        "unverified iterable expansion forbidden",
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
            for decorator in node.decorator_list:
                if not _approved_decorator(
                    node, decorator, path, tree, parents,
                    imported_aliases, unsafe_decorator_names,
                ):
                    findings.append(
                        Finding(
                            normalized,
                            decorator.lineno,
                            "untrusted or unaudited decorator execution forbidden",
                        )
                    )
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
        elif isinstance(node, ast.Attribute | ast.Subscript):
            if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                if not reviewed_attribute_source and not _approved_unpinned_attribute_read(
                    node, aliases, imported_aliases, parents, unsafe_binding_roots,
                ):
                    findings.append(
                        Finding(
                            normalized,
                            node.lineno,
                            "unverified attribute read may invoke external property",
                        )
                    )
            if isinstance(node.ctx, ast.Store | ast.Del):
                if not _approved_write_target(node, path, parents):
                    findings.append(
                        Finding(
                            normalized,
                            node.lineno,
                            "external or unverified mutation target forbidden",
                        )
                    )
            if isinstance(node, ast.Attribute):
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
        elif isinstance(node, ast.With | ast.AsyncWith):
            # Both context-manager forms call __enter__/__exit__ (or their
            # async counterparts) on potentially injected external objects.
            # There are no audited Strategy-owned context managers.
            findings.append(
                Finding(
                    normalized,
                    node.lineno,
                    "implicit context-manager execution forbidden",
                )
            )
        elif isinstance(node, ast.Await | ast.Match):
            # Await dispatches __await__, while structural matching may
            # invoke __match_args__/attribute access and custom equality.
            # Neither construct belongs to the reviewed Strategy surface.
            findings.append(
                Finding(
                    normalized,
                    node.lineno,
                    "unreviewed implicit dispatch construct forbidden",
                )
            )
        elif isinstance(node, ast.Global | ast.Nonlocal):
            findings.append(
                Finding(
                    normalized,
                    node.lineno,
                    "global/nonlocal state is forbidden in Strategy",
                )
            )
        elif isinstance(node, ast.Call):
            if not _approved_strategy_call(
                node, aliases, local_declarations, path, parents, unsafe_binding_roots
            ):
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
