"""Verify frozen Foundation artifacts and normalized S1 contract counters.

Read-only repository check for remote CI. This is not a security scan, a review
of implementation compliance, or authorization to promote a sprint.
"""

import hashlib
import re
from pathlib import Path

FROZEN_BLOBS = {
    "docs/foundation/0F-B_deferred_decision_register.md":
        "819397f0a3fe322ef199d053b2ccbe9a6fdb5747",
    "docs/foundation/0F-B_provenance_navigation.md":
        "25d14e7baad1746ea864d328db3438eb663729cd",
    "docs/foundation/0F-E_sprint1_entry_contract.md":
        "b04901dcc5612d3d418a6603a3a51a8e6e18ae08",
    "docs/foundation/0F-F_foundation_final_gate.md":
        "7204d409edd1239853ab2282e9a7a4411a068bba",
    "docs/protocols/quantitative/TRACEABILITY.md":
        "e7a263a4b576290ab2809f8a7630146ee0e512ed",
}

ENTRY_PATH = "docs/foundation/0F-E_sprint1_entry_contract.md"
CLAUSE_COUNTS = {
    "ENTRY_PRECONDITION": 9,
    "ALLOWED_CAPABILITY": 14,
    "PROHIBITED_CAPABILITY": 20,
    "DECISION_GATE": 28,
    "SAFETY_INVARIANT": 9,
    "IMPLEMENTATION_INVARIANT": 12,
    "VERIFICATION_OBLIGATION": 15,
    "EXIT_CRITERION": 11,
}
DECISION_IDS = {
    1, 2, 3, 4, 20, 21, 22, 26, 33, 36, 37, 40, 41, 43, 54, 56,
    57, 58, 59, 60, 61, 62, 65, 67, 68, 79,
}


def git_blob_sha(content: bytes) -> str:
    """Compute Git's object identity; this is byte identity, not a security hash."""
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content, usedforsecurity=False).hexdigest()


def verify_entry_contract(text: str) -> list[str]:
    """Validate every normalized clause row and the separate DD/RQM universes."""
    errors: list[str] = []
    rows = re.findall(r"^\| \*\*S1-EC-(\d{3})\*\* \|(.+)$", text, re.MULTILINE)
    ids = [int(identifier) for identifier, _ in rows]
    if sorted(ids) != list(range(1, 119)):
        errors.append("normalized S1-EC rows must contain each of 001..118 exactly once")
    for clause_type, expected in CLAUSE_COUNTS.items():
        actual = sum(f"`{clause_type}`" in row for _, row in rows)
        if actual != expected:
            errors.append(f"{clause_type}: expected {expected}, found {actual}")
    rqm_ids = re.findall(r"^\| \*\*RQM-(\d{3})\*\* \|", text, re.MULTILINE)
    if sorted(map(int, rqm_ids)) != list(range(1, 42)):
        errors.append("RQM table must contain each of 001..041 exactly once")
    decision_set = re.search(
        r"SPRINT1_DECISION_GATE_DD_SET = \{([^}]+)\}", text
    )
    decisions = [] if decision_set is None else re.findall(r"DD-(\d+)", decision_set[1])
    if len(decisions) != 26 or set(map(int, decisions)) != DECISION_IDS:
        errors.append("the 26 in-sprint DDs must remain distinct from the 28 gate clauses")
    for prefix, expected in (("NC", 20), ("NEG-CAP", 10)):
        numbers = re.findall(
            rf"^\| \*\*{prefix}-(\d{{2}})\*\* \|", text, re.MULTILINE
        )
        if sorted(map(int, numbers)) != list(range(1, expected + 1)):
            errors.append(f"{prefix} table must contain each ID exactly once")
    return errors


def verify_foundation(root: Path) -> list[str]:
    errors: list[str] = []
    for relative_path, expected in FROZEN_BLOBS.items():
        path = root / relative_path
        try:
            content = path.read_bytes()
        except OSError:
            errors.append(f"missing or unreadable frozen artifact: {relative_path}")
            continue
        if git_blob_sha(content) != expected:
            errors.append(f"frozen artifact byte identity changed: {relative_path}")
    try:
        entry = (root / ENTRY_PATH).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        errors.append("entry contract is missing, unreadable, or not UTF-8")
    else:
        errors.extend(verify_entry_contract(entry))
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = verify_foundation(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: five frozen blobs; 118 clauses; 41 RQMs; 26 DDs; 20 NCs; 10 NEG-CAP rows")
    print("LIMIT: document integrity only; implementation and security gates are not assessed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
