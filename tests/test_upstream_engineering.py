"""Negative scope cases for the exact upstream engineering verifier."""

import pytest

from scripts.check_upstream_engineering import TARGETS, validate_delta


@pytest.mark.parametrize("kind", ["docs", "ci"])
def test_exact_reviewed_scope_is_accepted_independently_of_git_sort_order(kind: str) -> None:
    expected = TARGETS[kind].delta
    validate_delta("\n".join(reversed(expected)), expected)


@pytest.mark.parametrize(
    "mutation",
    [
        "A\tsrc/btg_ai_trader/unauthorized.py",
        "M\tpyproject.toml",
        "A\tdocs/unreviewed.md",
        "D\tREADME.md",
        "R100\tREADME.md\tdocs/renamed.md",
    ],
)
def test_unreviewed_source_dependency_document_or_change_kind_is_rejected(mutation: str) -> None:
    expected = TARGETS["docs"].delta
    with pytest.raises(ValueError, match="allowlist"):
        validate_delta("\n".join((*expected, mutation)), expected)


def test_missing_or_duplicate_expected_path_is_rejected() -> None:
    expected = TARGETS["ci"].delta
    for candidate in (expected[:-1], (*expected, expected[0]), ()):
        with pytest.raises(ValueError, match="allowlist"):
            validate_delta("\n".join(candidate), expected)


def test_same_path_with_wrong_change_kind_is_rejected() -> None:
    expected = TARGETS["ci"].delta
    changed = (expected[0].replace("A\t", "M\t", 1), *expected[1:])
    with pytest.raises(ValueError, match="allowlist"):
        validate_delta("\n".join(changed), expected)
