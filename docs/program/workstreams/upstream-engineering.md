# Pinned upstream engineering verification

This workflow closes the evidence gap for upstream commits that predate their own CI workflow. It does not change those commits or fabricate status checks on them. Run/check-suite ownership remains the verifier branch SHA; target identities are explicit in each job and its logs.

- Documentation target: base `dabce69d92054b77cad72809669d4340c211c328`, head `dae6ff6e88ebb8c66e06f965224f9ee77f67a74f` (PR #7), exactly ten reviewed Markdown changes.
- CI target: base `183203307169f41ce40e035fe19f1d0a570e3e16`, head `3bbdcefee96a9d3662112cac97feeb86d7cc7093` (PR #8), exactly one workflow and one Markdown document added. Workflow blob `6145e4eae0d887ef35d5d92ccb9ab57d3cec4a2d` must match the independently reviewed version.

Each target gets a separate GitHub-hosted Ubuntu/Python 3.12 job. The verifier checks exact HEAD, clean checkout, exact path/change-kind allowlist, unchanged src/tests/scripts/config/dependency metadata, five frozen Foundation blobs and contract counters, and git diff --check. No rename, deletion or unreviewed extra path is accepted. Mutation tests exercise path/status mismatches, duplicates and omissions.

Only after scope checks pass, the job installs that target's existing development dependencies and runs its tests/coverage, Ruff, mypy, compilation and pip check. Commands fail on nonzero exit. This is real execution against the pinned target, not substitution of a later branch's passing suite.

The two targets contain bootstrap-only application code. These checks establish scoped engineering and negative-change evidence for documentation/CI; they are not an official Codex Security scan, full secrets scan, runtime NEG-CAP proof, integrated Observer test or approval of any promotion. Root review and all applicable gates remain required before a merge. Changes to upstream targets require explicit new pins and new evidence.

Execution evidence is recorded on PR #13 with verifier SHA, target SHAs, run URLs and applicable step conclusions. Before the first successful run, execution is pending; workflow presence alone is not a pass. No user-machine checkout is used.
