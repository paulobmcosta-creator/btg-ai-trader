"""Verify exact remote documentation/CI targets without claiming a security scan."""

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

from scripts.check_foundation_contract import verify_foundation


@dataclass(frozen=True)
class Target:
    base: str
    head: str
    delta: tuple[str, ...]


TARGETS = {
    "docs": Target(
        "dabce69d92054b77cad72809669d4340c211c328",
        "dae6ff6e88ebb8c66e06f965224f9ee77f67a74f",
        (
            "M\tAGENTS.md",
            "M\tREADME.md",
            "M\tdocs/BTG_AI_TRADER_MASTER_PLAN.md",
            "M\tdocs/architecture/README.md",
            "A\tdocs/program/PROGRAM_EXECUTION.md",
            "M\tdocs/protocols/README.md",
            "M\tdocs/sprints/README.md",
            "M\tdocs/sprints/SPRINT_0.md",
            "M\tdocs/sprints/SPRINT_0E.md",
            "M\tdocs/sprints/SPRINT_1.md",
        ),
    ),
    "ci": Target(
        "183203307169f41ce40e035fe19f1d0a570e3e16",
        "3bbdcefee96a9d3662112cac97feeb86d7cc7093",
        (
            "A\t.github/workflows/remote-python-ci.yml",
            "A\tdocs/program/workstreams/remote-ci.md",
        ),
    ),
}
UNCHANGED_PATHS = (
    "src", "tests", "scripts", "config", "pyproject.toml", ".python-version", ".gitignore",
)
CI_WORKFLOW_BLOB = "6145e4eae0d887ef35d5d92ccb9ab57d3cec4a2d"


def validate_delta(output: str, expected: tuple[str, ...]) -> None:
    """Require exact paths and change kinds, retaining duplicate detection."""
    if sorted(output.splitlines()) != sorted(expected):
        raise ValueError("changed paths/statuses do not match the exact reviewed allowlist")


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def verify_target(root: Path, kind: str) -> None:
    target = TARGETS[kind]
    checked_head = git(root, "rev-parse", "HEAD")
    if checked_head != target.head:
        raise ValueError("checkout HEAD is not the exact reviewed target")
    git(root, "cat-file", "-e", f"{target.base}^{{commit}}")
    if git(root, "status", "--porcelain"):
        raise ValueError("target checkout is not clean before verification")
    delta = git(root, "diff", "--name-status", "--no-renames", target.base, target.head)
    validate_delta(delta, target.delta)
    git(root, "diff", "--exit-code", target.base, target.head, "--", *UNCHANGED_PATHS)
    git(root, "diff", "--check", target.base, target.head)
    failures = verify_foundation(root)
    if failures:
        raise ValueError("; ".join(failures))
    if kind == "ci":
        workflow_blob = git(
            root, "rev-parse", f"{target.head}:.github/workflows/remote-python-ci.yml"
        )
        if workflow_blob != CI_WORKFLOW_BLOB:
            raise ValueError("CI workflow differs from the separately reviewed immutable blob")
    print(f"TARGET_KIND={kind}")
    print(f"TARGET_BASE={target.base}")
    print(f"TARGET_HEAD={checked_head}")
    print(f"EXACT_DELTA_PATHS={len(target.delta)}")
    print("PASS: scope allowlist; unchanged app/config/dependencies; frozen contracts; diff")
    print("LIMIT: scoped engineering evidence, not official Security or full runtime NEG-CAP")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=tuple(TARGETS), required=True)
    parser.add_argument("--root", type=Path, required=True)
    arguments = parser.parse_args()
    verify_target(arguments.root.resolve(), arguments.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
