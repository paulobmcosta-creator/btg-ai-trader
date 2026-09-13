"""Scoped S1 inventory/AST/config checks plus a separate possible-secret heuristic."""

import argparse
import ast
import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import cast

MANIFEST = "docs/program/workstreams/s1-boundary-scope.json"
EXTERNAL_IMPORTS = {
    "base64", "hashlib", "json", "os", "re", "stat", "tempfile",
    "collections.abc.Iterable", "dataclasses.dataclass", "dataclasses.replace",
    "datetime.UTC", "datetime.datetime", "datetime.timedelta",
    "decimal.Decimal", "decimal.InvalidOperation", "enum.Enum", "pathlib.Path",
    "typing.Protocol", "typing.cast", "uuid.UUID", "uuid.uuid4",
}
MODULE_MEMBERS = {
    "base64": {"b64encode", "b64decode"},
    "hashlib": {"sha256"},
    "json": {"loads", "dumps"},
    "os": {"open", "close", "fsync", "link", "O_RDONLY"},
    "re": {"compile", "fullmatch"},
    "stat": {"S_ISREG"},
    "tempfile": {"NamedTemporaryFile"},
    "datetime.datetime": {"fromisoformat", "strptime"},
}
FORBIDDEN_NAMES = {
    "__import__", "eval", "exec", "compile", "globals", "locals", "vars", "setattr",
    "delattr", "breakpoint", "input", "__builtins__",
    "OrderIntent", "TradeIntent", "OrderPlan", "ExecutionOrder", "RiskEngine",
    "RiskAuthorization", "StrategyEngine", "SignalGenerator", "FinancialLedger",
    "PositionTracker", "PaperExecution", "ExecutionEngine", "OrderManager",
    "order_send", "order_calc_margin", "order_check", "auto_flatten",
}
DUNDER_ESCAPE = {
    "__dict__", "__class__", "__bases__", "__subclasses__", "__globals__",
    "__builtins__", "__getattribute__", "__code__", "__closure__",
}
REFLECTION_FIELDS = {
    "envelope": {"envelope_version", "schema_version", "source_sequence", "ingestion_order"},
    "health": {"heartbeat_timeout_ns", "market_staleness_ns", "heartbeat_ns", "market_data_ns"},
    "ingestion": {"depth", "accepted", "dequeued", "backpressure_count"},
    "market": {"open", "high", "low", "close"},
    "provider": {"ticks", "candles", "source_sequence"},
}
SECRET_PATTERNS = {
    "possible-private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "possible-aws-key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    "possible-github-token": re.compile(
        r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"
    ),
    "possible-api-token": re.compile(r"\bsk-[A-Za-z0-9_-]{24,}"),
    "possible-url-credential": re.compile(r"https?://[^\s/@:]+:[^\s/@]+@"),
}
SECRET_NAME = re.compile(r"(?:password|secret|api[_-]?key|access[_-]?token|auth[_-]?token)", re.I)


@dataclass(frozen=True, slots=True)
class Finding:
    path: str
    line: int
    rule: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.rule}"


def _module(path: str) -> str:
    parts = path.removeprefix("src/").removesuffix(".py").split("/")
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _qualified(node: ast.AST, bindings: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return bindings.get(node.id)
    if isinstance(node, ast.Attribute):
        prefix = _qualified(node.value, bindings)
        return None if prefix is None else prefix + "." + node.attr
    return None


def _finite_getattr(
    node: ast.Call, parents: dict[ast.AST, ast.AST], path: str
) -> bool:
    if len(node.args) != 2 or node.keywords or not isinstance(node.args[1], ast.Name):
        return False
    receiver = ast.unparse(node.args[0])
    if receiver not in {"self", "snapshot", "previous.queue"}:
        return False
    variable = node.args[1].id
    ancestor: ast.AST = node
    while ancestor in parents:
        ancestor = parents[ancestor]
        if isinstance(ancestor, ast.For) and isinstance(ancestor.target, ast.Name):
            if ancestor.target.id != variable or not isinstance(ancestor.iter, ast.Tuple):
                continue
            fields = ancestor.iter.elts
            allowed = REFLECTION_FIELDS.get(Path(path).stem, set())
            if not fields or any(
                not isinstance(field, ast.Constant)
                or not isinstance(field.value, str)
                or field.value not in allowed for field in fields
            ):
                return False
            return not any(
                isinstance(part, ast.Name) and isinstance(part.ctx, ast.Store)
                and part.id == variable
                for statement in ancestor.body for part in ast.walk(statement)
            )
    return False


def _reflection_consumer(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    parent = parents.get(node)
    if isinstance(parent, ast.Compare):
        return True
    return (
        isinstance(parent, ast.Call) and isinstance(parent.func, ast.Name)
        and parent.func.id in {"type", "isinstance", "require_numeric", "_reading"}
        and bool(parent.args) and parent.args[0] is node
    )


def _function_scope(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> ast.AST:
    while node in parents:
        node = parents[node]
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            return node
    return node


def check_sources(sources: dict[str, str]) -> list[Finding]:
    """Check syntax and import/member boundaries independently of production blob pins."""
    findings: list[Finding] = []
    modules = {_module(path) for path in sources}
    for path, source in sources.items():
        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError as error:
            findings.append(Finding(path, error.lineno or 1, "invalid-python"))
            continue
        parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        bindings: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports = [(alias.name, alias.asname or alias.name.split(".")[0])
                           for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level or node.module is None:
                    findings.append(Finding(path, node.lineno, "relative-or-unresolved-import"))
                    continue
                imports = [(node.module + "." + alias.name, alias.asname or alias.name)
                           for alias in node.names]
                if node.module.startswith("btg_ai_trader") and node.module not in modules:
                    findings.append(Finding(path, node.lineno, "internal-import-outside-inventory"))
            else:
                continue
            for imported, bound in imports:
                if imported.endswith(".*"):
                    findings.append(Finding(path, node.lineno, "wildcard-import"))
                elif imported.startswith("btg_ai_trader"):
                    module = (
                        imported if isinstance(node, ast.Import) else imported.rsplit(".", 1)[0]
                    )
                    if module not in modules:
                        findings.append(Finding(
                            path, node.lineno, "internal-import-outside-inventory"
                        ))
                elif imported not in EXTERNAL_IMPORTS:
                    findings.append(Finding(path, node.lineno, "external-import-not-allowed"))
                if bound in bindings and bindings[bound] != imported:
                    findings.append(Finding(path, node.lineno, "ambiguous-import-alias"))
                bindings[bound] = imported
        reflected_results: list[tuple[ast.AST, str]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                if node.name in FORBIDDEN_NAMES:
                    findings.append(Finding(path, node.lineno, "prohibited-capability-definition"))
            if isinstance(node, ast.arg) and node.arg in bindings:
                findings.append(Finding(path, node.lineno, "import-alias-shadowed"))
            if isinstance(node, ast.Name):
                if node.id in FORBIDDEN_NAMES:
                    findings.append(Finding(path, node.lineno, "prohibited-capability-name"))
                if isinstance(node.ctx, ast.Store) and node.id in bindings:
                    findings.append(Finding(path, node.lineno, "import-alias-rebound"))
                parent = parents.get(node)
                if (
                    isinstance(node.ctx, ast.Load)
                    and bindings.get(node.id) in {
                        "base64", "hashlib", "json", "os", "re", "stat", "tempfile"
                    }
                    and not (isinstance(parent, ast.Attribute) and parent.value is node)
                ):
                    findings.append(Finding(path, node.lineno, "external-module-escape"))
                if node.id == "getattr":
                    parent = parents.get(node)
                    if not isinstance(parent, ast.Call) or parent.func is not node:
                        findings.append(Finding(path, node.lineno, "indirect-reflection"))
            if isinstance(node, ast.Attribute):
                if (
                    (node.attr in FORBIDDEN_NAMES or node.attr in DUNDER_ESCAPE)
                    and _qualified(node, bindings) != "re.compile"
                ):
                    findings.append(Finding(path, node.lineno, "prohibited-capability-attribute"))
                base = _qualified(node.value, bindings)
                if base in MODULE_MEMBERS and node.attr not in MODULE_MEMBERS[base]:
                    findings.append(Finding(path, node.lineno, "external-member-not-allowed"))
                if isinstance(node.ctx, ast.Store) and base is not None:
                    findings.append(Finding(path, node.lineno, "import-member-mutated"))
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name | ast.Attribute):
                    findings.append(Finding(path, node.lineno, "dynamic-call-target"))
                if (
                    isinstance(node.func, ast.Name) and node.func.id == "type"
                    and len(node.args) != 1
                ):
                    findings.append(Finding(path, node.lineno, "dynamic-type-factory"))
                if isinstance(node.func, ast.Name) and node.func.id == "getattr":
                    if not _finite_getattr(node, parents, path):
                        findings.append(Finding(path, node.lineno, "unbounded-reflection"))
                    parent = parents.get(node)
                    if (
                        isinstance(parent, ast.Assign) and parent.value is node
                        and len(parent.targets) == 1
                        and isinstance(parent.targets[0], ast.Name)
                    ):
                        reflected_results.append((
                            _function_scope(node, parents), parent.targets[0].id
                        ))
                    elif not _reflection_consumer(node, parents):
                        findings.append(Finding(path, node.lineno, "reflected-value-escaped"))
                    scope = _function_scope(node, parents)
                    receiver = ast.unparse(node.args[0]).split(".")[0] if node.args else ""
                    if any(
                        isinstance(part, ast.Name) and isinstance(part.ctx, ast.Store)
                        and part.id == receiver
                        and not (
                            Path(path).stem == "ingestion" and receiver == "snapshot"
                            and isinstance(parents.get(part), ast.Assign)
                            and ast.unparse(parents[part]) == "snapshot = queue.snapshot"
                        )
                        for part in ast.walk(scope)
                    ):
                        findings.append(Finding(path, node.lineno, "reflection-receiver-rebound"))
                if isinstance(node.func, ast.Attribute) and node.func.attr == "__setattr__":
                    if not (
                        Path(path).stem == "instruments"
                        and ast.unparse(node.func.value) == "object"
                        and len(node.args) == 3
                        and isinstance(node.args[1], ast.Constant)
                        and node.args[1].value in {"matches", "mappings"}
                    ):
                        findings.append(Finding(path, node.lineno, "unapproved-frozen-field-write"))
        for scope, name in reflected_results:
            for node in ast.walk(scope):
                if (
                    isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
                    and node.id == name and not _reflection_consumer(node, parents)
                ):
                    findings.append(Finding(path, node.lineno, "reflected-value-escaped"))
    return findings


def possible_secrets(path: str, text: str) -> list[Finding]:
    """Heuristic only. Never include a suspected value in returned findings."""
    findings: list[Finding] = []
    for number, line in enumerate(text.splitlines(), 1):
        for rule, pattern in SECRET_PATTERNS.items():
            if pattern.search(line):
                findings.append(Finding(path, number, rule))
        if not path.endswith(".py"):
            match = re.match(r"\s*([A-Za-z0-9_-]+)\s*[:=]\s*(.+)", line)
            if match and SECRET_NAME.search(match[1]):
                value = match[2].strip().strip("\"'")
                if value and not value.startswith(("\u0024{{", "\u0024{")):
                    findings.append(Finding(path, number, "possible-credential-literal"))
    if path.endswith(".py"):
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return findings
        for node in ast.walk(tree):
            pairs: list[tuple[str, ast.AST]] = []
            if isinstance(node, ast.Assign):
                pairs = [(target.id, node.value) for target in node.targets
                         if isinstance(target, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.value is not None:
                    pairs = [(node.target.id, node.value)]
            elif isinstance(node, ast.Dict):
                pairs = [(key.value, value)
                         for key, value in zip(node.keys, node.values, strict=True)
                         if isinstance(key, ast.Constant) and isinstance(key.value, str)]
            for name, value in pairs:
                if (
                    SECRET_NAME.search(name) and isinstance(value, ast.Constant)
                    and isinstance(value.value, str | bytes) and bool(value.value)
                ):
                    findings.append(Finding(path, value.lineno, "possible-credential-literal"))
    return findings


def check_packaging(text: str) -> list[Finding]:
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return [Finding("pyproject.toml", 1, "invalid-packaging")]
    project = parsed.get("project")
    if not isinstance(project, dict):
        return [Finding("pyproject.toml", 1, "missing-project-config")]
    errors: list[Finding] = []
    if project.get("dependencies") != []:
        errors.append(Finding("pyproject.toml", 1, "unapproved-runtime-dependency"))
    if any(project.get(key) for key in ("scripts", "gui-scripts", "entry-points")):
        errors.append(Finding("pyproject.toml", 1, "unapproved-runtime-entrypoint"))
    return errors


def _blob(data: bytes) -> str:
    return hashlib.sha1(
        f"blob {len(data)}\0".encode("ascii") + data, usedforsecurity=False
    ).hexdigest()


def verify(root: Path) -> list[Finding]:
    manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    if (
        not isinstance(manifest, dict) or manifest.get("schema") != 1
        or manifest.get("composition_status") not in {"PENDING", "SCOPED_TESTS_IMPLEMENTED"}
        or not isinstance(manifest.get("files"), dict)
    ):
        raise ValueError("invalid scope manifest")
    pins = cast(dict[str, str], manifest["files"])
    actual: dict[str, Path] = {}
    findings: list[Finding] = []
    for folder in ("src", "config"):
        for path in (root / folder).rglob("*"):
            if "__pycache__" in path.parts:
                continue
            if path.is_symlink():
                findings.append(Finding(path.relative_to(root).as_posix(), 1, "scope-symlink"))
            if path.is_file():
                actual[path.relative_to(root).as_posix()] = path
    for name in ("pyproject.toml", ".python-version"):
        actual[name] = root / name
    for relative in sorted(set(actual) ^ set(pins)):
        findings.append(Finding(relative, 1, "scope-inventory-mismatch"))
    sources: dict[str, str] = {}
    for relative, location in actual.items():
        try:
            data = location.read_bytes()
            text = data.decode("utf-8")
        except (OSError, UnicodeError):
            findings.append(Finding(relative, 1, "unreadable-scope-file"))
            continue
        if pins.get(relative) != _blob(data):
            findings.append(Finding(relative, 1, "scope-blob-mismatch"))
        if relative.startswith("src/") and relative.endswith(".py"):
            sources[relative] = text
        findings.extend(possible_secrets(relative, text))
    findings.extend(check_sources(sources))
    findings.extend(check_packaging((root / "pyproject.toml").read_text(encoding="utf-8")))
    for path in (root / ".github/workflows").glob("*"):
        if path.is_file():
            findings.extend(possible_secrets(path.relative_to(root).as_posix(), path.read_text()))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        findings = verify(args.root)
    except (OSError, ValueError):
        print("FAIL: unreadable or invalid scope/configuration")
        return 1
    for finding in findings:
        print(f"FAIL: {finding}")
    if findings:
        return 1
    print("PASS_SCOPE: inventory pins, AST/import boundary, packaging/config checks")
    print("POSSIBLE_SECRET_HEURISTIC: no finding in scoped runtime/config/workflows")
    print("LIMIT: not an official Security scan or universal secret detection")
    print("NEG_RUNTIME_NOT_EXECUTED: composition tests are pending; no full NEG-CAP claim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
