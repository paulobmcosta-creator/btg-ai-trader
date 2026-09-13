# Remote CI — engineering verification workstream

## Scope and status

This workstream provides engineering checks on GitHub-hosted runners without depending on the user's computer. It introduces no runtime dependency, provider, market-data connection, broker, credential, order path, cloud trading node or deployment.

```text
WORKSTREAM = REMOTE_ENGINEERING_CI
BASELINE = 183203307169f41ce40e035fe19f1d0a570e3e16
IMPLEMENTATION = WORKFLOW_DEFINED
REMOTE_EXECUTION = PENDING_VERIFIED_RUN
SECURITY_DIFF_SCAN = NOT_RUN
NEGATIVE_CAPABILITY_TESTS = NOT_IMPLEMENTED
TRADING_CAPABILITY = ABSENT
```

A workflow definition is not passing evidence. The implementation state above does not assert successful execution. Run results are authoritative only for their recorded head SHA and comparison base; later commits require new results.

## Execution contract

The workflow is `.github/workflows/remote-python-ci.yml`. It runs on `ubuntu-24.04`, with Python `3.12` for Python checks. Development dependencies and the build backend remain pinned by the existing `pyproject.toml`; this workstream does not change those pins.

Six independent matrix jobs run with `fail-fast: false`:

| Check | Command | Evidence and limit |
| --- | --- | --- |
| tests | `python -m pytest --cov=btg_ai_trader --cov-report=term-missing --cov-report=xml` | Test results and branch coverage in job logs. Current bootstrap coverage does not demonstrate domain or security correctness. |
| lint | `python -m ruff check .` | Existing configured lint rules. |
| types | `python -m mypy src tests` | Source and test type checking using existing strict configuration. |
| compile | `python -m compileall -q src tests` | Python compilation only. |
| dependencies | `python -m pip check` | Consistency of installed requirements only. |
| diff | `git diff --check BASE HEAD` | Whitespace/conflict-marker check over the recorded comparison. This is not a semantic code review or security scan. |

Each job fails on its command's nonzero exit. Setup or installation failures are failures, not substituted successes. No `continue-on-error`, tolerated failures, synthetic passing statuses, or self-hosted runners are configured.

Pull-request runs check the exact PR head and compare against the event's base SHA. Push runs compare against the previous commit recorded by the event; a new-branch event uses the explicit baseline above. The diff job verifies that the comparison commit exists and logs the comparison base and checked head. Checkout fetches full history for these comparisons.

Triggers cover push events on `s1/**`, `s11/**` and `sprint/1-market-observer`, and pull requests targeting `sprint/1-market-observer` or staged `s1/**` branches. The pull-request workflow does not use `pull_request_target`. Permissions are restricted to `contents: read`; checkout does not persist credentials. Each job has a ten-minute timeout. Concurrency cancels superseded runs for the same workflow/ref.

## Action provenance

The following official action tag references and their action metadata were read through GitHub on 2026-09-13; immutable commit SHAs are used:

- [actions/checkout v4](https://github.com/actions/checkout/tree/11d5960a326750d5838078e36cf38b85af677262): `11d5960a326750d5838078e36cf38b85af677262`.
- [actions/setup-python v5](https://github.com/actions/setup-python/tree/a26af69be951a213d495a4c3e4e4022e16d87065): `a26af69be951a213d495a4c3e4e4022e16d87065`.

## Evidence and promotion

Before requesting promotion, record in the pull request the tested head SHA, run URL, actual conclusion of all six checks, and unresolved limitations. Missing or unavailable workflow execution is not a pass; keep the PR draft when checks cannot run. CI success does not authorize merge or any trading capability.

The first functional Sprint 1 pull request still requires the mandated Codex Security Security Diff Scan over its exact diff and the applicable 0F-E negative-capability tests. This engineering workflow neither implements nor substitutes those obligations. Full contract conformance remains governed by [0F-E](../../foundation/0F-E_sprint1_entry_contract.md) and [Sprint 1](../../sprints/SPRINT_1.md).
