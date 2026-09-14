"""Fail closed on likely secrets in reachable Git history without printing secret values."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import PurePosixPath

MAX_TEXT_BLOB_BYTES = 2_000_000

TOKEN_PATTERNS: dict[str, re.Pattern[str]] = {
    "private-key-header": re.compile(
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
    ),
    "aws-access-key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    "github-token": re.compile(
        r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{22,})\b"
    ),
    "openai-style-secret": re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
    "google-api-key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "slack-token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "stripe-live-secret": re.compile(r"\bsk_live_[A-Za-z0-9]{20,}\b"),
    "url-embedded-credential": re.compile(r"https?://[^\s/@:]+:[^\s/@]+@"),
}

CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?im)^\s*(?:export\s+)?"
    r"([A-Za-z0-9_.-]*(?:password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)"
    r"[A-Za-z0-9_.-]*)\s*[:=]\s*[\"']?([^\s\"'#]+)"
)

ASSIGNMENT_SCAN_SUFFIXES = {
    ".cfg",
    ".conf",
    ".env",
    ".ini",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
}

PLACEHOLDER_VALUES = {
    "changeme",
    "dummy",
    "example",
    "fake",
    "placeholder",
    "redacted",
    "secret",
    "test",
    "your_key_here",
    "your_token_here",
}

SENSITIVE_PATH_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(^|/)\.env(?:\..+)?$", re.I),
    re.compile(r"\.(?:pem|key|p12|pfx)$", re.I),
    re.compile(r"(^|/)(?:id_rsa|id_dsa|id_ecdsa|id_ed25519)$", re.I),
    re.compile(r"(^|/)(?:credentials?|secrets?)(?:\.[^/]+)?$", re.I),
)


@dataclass(frozen=True, slots=True, order=True)
class Finding:
    rule: str
    location: str


def _git_bytes(*args: str, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        ("git", *args),
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {stderr}")
    return completed.stdout


def _scan_assignments(location: str) -> bool:
    path = PurePosixPath(location)
    return path.name.casefold().startswith(".env") or path.suffix.casefold() in (
        ASSIGNMENT_SCAN_SUFFIXES
    )


def _scan_tokens(location: str, text: str) -> set[Finding]:
    findings: set[Finding] = set()
    for rule, pattern in TOKEN_PATTERNS.items():
        if pattern.search(text):
            findings.add(Finding(rule=rule, location=location))

    if not _scan_assignments(location):
        return findings

    for match in CREDENTIAL_ASSIGNMENT.finditer(text):
        value = match.group(2).strip().strip("\"'")
        normalized = value.casefold()
        if (
            not value
            or normalized in PLACEHOLDER_VALUES
            or value.startswith(("${", "{{", "<", "$", "%"))
            or value.endswith(("}", ">"))
        ):
            continue
        findings.add(Finding(rule="credential-literal-assignment", location=location))
    return findings


def _reachable_objects() -> list[tuple[str, str]]:
    raw = _git_bytes("rev-list", "--objects", "--all").decode(
        "utf-8", errors="surrogateescape"
    )
    seen: set[str] = set()
    objects: list[tuple[str, str]] = []
    for line in raw.splitlines():
        sha, separator, path = line.partition(" ")
        if not sha or sha in seen:
            continue
        seen.add(sha)
        objects.append((sha, path if separator else ""))
    return objects


def _blob_findings() -> set[Finding]:
    findings: set[Finding] = set()
    for sha, path in _reachable_objects():
        if path and any(pattern.search(path) for pattern in SENSITIVE_PATH_PATTERNS):
            findings.add(Finding(rule="sensitive-path-in-history", location=path))

        object_type = _git_bytes("cat-file", "-t", sha).decode(
            "ascii", errors="replace"
        ).strip()
        if object_type != "blob":
            continue
        size_text = _git_bytes("cat-file", "-s", sha).decode(
            "ascii", errors="replace"
        ).strip()
        try:
            size = int(size_text)
        except ValueError as error:
            raise RuntimeError(f"invalid blob size for {sha}") from error
        if size > MAX_TEXT_BLOB_BYTES:
            continue

        content = _git_bytes("cat-file", "-p", sha)
        if b"\x00" in content[:8192]:
            continue
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            continue
        label = path or f"blob:{sha[:12]}"
        findings.update(_scan_tokens(label, text))
    return findings


def _commit_message_findings() -> set[Finding]:
    findings: set[Finding] = set()
    commits = _git_bytes("rev-list", "--all").decode("ascii").splitlines()
    for commit in commits:
        message = _git_bytes("show", "-s", "--format=%B", commit).decode(
            "utf-8", errors="replace"
        )
        findings.update(_scan_tokens(f"commit:{commit[:12]}", message))
    return findings


def main() -> int:
    findings = _blob_findings() | _commit_message_findings()
    if findings:
        print("PUBLIC_HISTORY_SECRET_SCAN = FINDINGS")
        for finding in sorted(findings):
            print(f"{finding.rule}: {finding.location}")
        print("Secret-like values are intentionally not printed.")
        return 1

    print("PUBLIC_HISTORY_SECRET_SCAN = PASS")
    print("Scope: all objects and commit messages reachable from refs available to this checkout.")
    print("Secret-like values are never emitted by this scanner.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
