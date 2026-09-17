# S2-C — Antigravity Task Packet: Final Acceptance Reconciliation & Sprint 2 Closure Gate

## Execute on this branch only

```text
REPOSITORY = paulobmcosta-creator/btg-ai-trader
CANONICAL_BASE = sprint/2-data-platform-replay
ACCEPTED_BASE_SHA = 071e004f2be8e5925b0de63db97af61cbbf37b30
WORK_BRANCH = s2/03-final-acceptance-reconciliation
ISSUE = #68
IMPLEMENTATION_AUTHORITY = DOCUMENTARY_RECONCILIATION_AND_CLOSURE_GATE_ONLY
FUNCTIONAL_CODE_AUTHORITY = NONE
```

Do not switch implementation to `main`, historical research branches, Sprint 1 branches or any other branch.

Sprint 2 is still OPEN while this work is being prepared. This branch may propose formal closure, but closure becomes canonical only after independent audit, exact-head merge and post-merge validation.

## Mandatory read order

Before editing anything, read:

1. `AGENTS.md`
2. `docs/BTG_AI_TRADER_MASTER_PLAN.md`
3. `docs/sprints/SPRINT_2.md`
4. `docs/program/PROGRAM_EXECUTION.md`
5. `docs/program/S2_ENTRY_CONTRACT.md`
6. `docs/program/S2_DECISION_REGISTER.md`
7. `docs/program/S2_CAPABILITY_MATRIX.md`
8. `docs/program/S2_ENTRY_GATE.md`
9. `docs/program/workstreams/S2-ANTIGRAVITY-HANDOFF.md`
10. `docs/program/workstreams/S2-B-ANTIGRAVITY-TASK.md`
11. this file
12. accepted S2-A code/tests and PR #65 evidence
13. accepted S2-B code/tests and PR #67 evidence
14. Issue #62, Issue #64, Issue #66 and Issue #68

Historical PRs #9 and #37 remain research-only. Frozen Foundation artifacts and historical ADR/protocol snapshots must not be rewritten.

## Accepted canonical evidence entering this gate

```text
SPRINT_1_FINAL_VERDICT = PASS
SPRINT_2_LIFECYCLE = OPEN
SPRINT_2_ENTRY_GATE = PASS

S2_A = ACCEPTED
S2_A_PR = #65
S2_A_REVIEWED_HEAD = 3cf3b528aa0c8a953d9d47f6a2ad1ac92d52ee29
S2_A_MERGE_COMMIT = 9faa43c3bc112c1d2e558aa3e1518371880cc518
S2_A_POST_MERGE_S2_CI = 35150432340 PASS
S2_A_POST_MERGE_UPSTREAM = 35150432259 PASS

S2_B = ACCEPTED
S2_B_PR = #67
S2_B_REVIEWED_HEAD = 5c2c94bb5808c660e83b3480341816fe3868bbd4
S2_B_MERGE_COMMIT = 071e004f2be8e5925b0de63db97af61cbbf37b30
S2_B_POST_MERGE_S2_CI = 35163848955 PASS 8/8
S2_B_POST_MERGE_UPSTREAM = 35163848942 PASS 2/2
```

Do not change these historical accepted facts unless remote GitHub evidence proves one is wrong. If a discrepancy exists, stop and report it rather than harmonizing silently.

## Mission

Prepare the final conjunctive acceptance record for Sprint 2 using only already accepted functionality.

This task must:

1. reconcile the complete Sprint 2 positive capability matrix;
2. reconcile all Sprint 2 negative capabilities;
3. verify which conditional decisions/capabilities were actually triggered;
4. prove that untriggered features did not become implicit requirements or implementations;
5. reconcile current living status documents;
6. create one explicit final acceptance artifact;
7. produce a closure candidate suitable for independent audit.

This task must NOT add functional code.

## Required positive-capability reconciliation

Create an evidence table for every `S2-AC-01..14` from `docs/program/S2_CAPABILITY_MATRIX.md`.

For each row record at least:

```text
ID
contractual capability
applicability / trigger status
canonical implementation/evidence
specific tests or checks
accepted PR/commit evidence
verdict
```

Expected classifications must be independently verified, not copied mechanically:

### Required and expected PASS from accepted implementation

- `S2-AC-01` dataset/capture boundary validation — S2-A DD-15 boundary + S2-B explicit normalization boundary.
- `S2-AC-02` lossless normalization — S2-B.
- `S2-AC-03` causal lane partitioning — S2-A/S2-B mixed-lane fail-closed behavior.
- `S2-AC-04` immutable replay schedule — S2-A.
- `S2-AC-05` inclusive knowledge cutoff — S2-A.
- `S2-AC-06` monotonic virtual clock/cutoff advancement — S2-A.
- `S2-AC-07` exact logical replay speed — S2-A.
- `S2-AC-08` replay input provenance — S2-A DD-15 `ReplayInputBoundary` / `RunInputBoundary`.
- `S2-AC-09` replay lineage — S2-A `ReplayEmissionLineage`.
- `S2-AC-10` data-quality evidence — S2-B.
- `S2-AC-12` deterministic replay — S2-A repeated logical replay tests.

### Conditional capabilities — verify trigger state

- `S2-AC-11` schema upcast: `NOT_TRIGGERED` is valid only if canonical Sprint 2 consumes no second schema version / cross-schema replay.
- `S2-AC-13` persisted research dataset: `NOT_TRIGGERED` is valid only if canonical Sprint 2 contains no canonical persisted research dataset feature. Existing Sprint 1 technical evidence storage is not automatically a Sprint 2 research-dataset persistence feature.
- `S2-AC-14` external historical-data ingestion: `NOT_TRIGGERED` is valid only if canonical Sprint 2 wires no external historical-data provider.

Do not call an actually triggered capability `NOT_TRIGGERED` to simplify closure.

## Decision-trigger reconciliation

Explicitly audit these decisions from `S2_DECISION_REGISTER.md`:

- `DD-05` schema migration/upcasting;
- `DD-15` RunInputBoundary;
- `DD-27` durable replay snapshots/checkpoints;
- `DD-28` dataset retention/archival;
- `DD-77` external historical data source/vendor;
- `DD-78` resampling/sampling-resolution policy;
- `DD-80` missing-data treatment;
- `DD-81` continuous-series stitching/adjustment;
- `DD-82` research-dataset physical persistence format;
- `DD-83` dataset hashing/version-registry technology.

For each record:

```text
TRIGGERED_AND_SATISFIED
NOT_TRIGGERED_AND_DEFERRED
BLOCKED
```

Expected evidence direction, subject to verification:

```text
DD-15 = TRIGGERED_AND_SATISFIED
DD-80 = TRIGGERED_AND_SATISFIED
DD-05 = NOT_TRIGGERED_AND_DEFERRED if no cross-schema replay exists
DD-27 = NOT_TRIGGERED_AND_DEFERRED if no durable replay checkpoint exists
DD-28 = NOT_TRIGGERED_AND_DEFERRED if no managed research-dataset retention feature exists
DD-77 = NOT_TRIGGERED_AND_DEFERRED if no external historical vendor exists
DD-78 = NOT_TRIGGERED_AND_DEFERRED if supplied granularity is only preserved and no resampling policy exists
DD-81 = NOT_TRIGGERED_AND_DEFERRED if no continuous-series feature exists
DD-82 = NOT_TRIGGERED_AND_DEFERRED if no canonical persisted research dataset exists
DD-83 = NOT_TRIGGERED_AND_DEFERRED for registry/version technology if no persisted dataset exists; preserved source ContentHash evidence remains valid where available
```

Do not modify frozen `0F-B` to change its historical triage. Reconcile trigger-based Sprint 2 adjudication in the current Sprint 2 acceptance artifact.

## Required negative-capability reconciliation

Audit and report every `S2-NC-01..16` against canonical Sprint 2 code and `scripts/check_s2_boundary.py`.

At minimum prove absence/preservation of:

```text
Strategy operational path
Signal/trade intent operational path
Risk authorization path
Paper execution
Live execution
broker order/account API
FinancialLedger mutation
P&L / economic backtest
spread/fees/slippage/fill economics
predictive ML operational wiring
real-money authority
source-evidence mutation
fabricated temporal evidence
synthetic cross-lane ordering
silent missing-data imputation
wall-clock causal semantics
```

A single negative-capability violation blocks Sprint 2 closure.

## Required final acceptance artifact

Create:

`docs/program/S2_FINAL_ACCEPTANCE.md`

Minimum sections:

1. authority and exact canonical baseline entering final gate;
2. accepted Entry Gate evidence;
3. accepted S2-A evidence;
4. accepted S2-B evidence;
5. S2-AC-01..14 row-by-row reconciliation;
6. S2-NC-01..16 row-by-row reconciliation;
7. DD trigger reconciliation;
8. conditional capability rationale;
9. frozen/historical artifact preservation statement;
10. open issues/blockers inventory;
11. exact CI requirements for closure PR;
12. proposed Sprint 2 verdict;
13. promotion boundary to Sprint 3.

The proposed verdict may be `PASS / FORMALLY_CLOSED` only if every applicable required capability is PASS, every conditional requirement is either satisfied or genuinely NOT_TRIGGERED, all negative capabilities PASS and no Sprint-2 blocker remains.

## Open issues that must be classified, not hidden

At minimum inspect:

- Issue #6 — historical 0F-F/QPI traceability errata;
- Issue #61 — administrative branch/ruleset hardening.

These do not automatically become Sprint 2 functional blockers. Record why they are or are not blockers. If evidence shows either blocks Sprint 2, do not close Sprint 2.

Issue #69 is an accidental administrative issue already closed as `not_planned`; it has no project authority and must not be treated as program work.

## Living documents to reconcile

If and only if the evidence supports proposed closure, update current living documents so the PR is internally coherent:

- `docs/sprints/SPRINT_2.md`;
- `docs/program/PROGRAM_EXECUTION.md`;
- `docs/BTG_AI_TRADER_MASTER_PLAN.md`;
- `AGENTS.md`.

Required principles:

- remove stale language saying the first Sprint 2 increment is still pending/next;
- record S2-A and S2-B accepted evidence accurately;
- preserve `OFFICIAL_CODEX_SECURITY_DIFF_SCAN = NOT_EXECUTED` as the historical Sprint 1 fact;
- do not imply Issue #61 protection/ruleset hardening is completed;
- do not claim persisted-dataset capability when AC-13 is NOT_TRIGGERED;
- do not claim external historical vendor ingestion when AC-14 is NOT_TRIGGERED;
- do not import Sprint 3 economic capabilities into Sprint 2;
- promotion to Sprint 3 means only authority to open its own gate, not authority to implement economic backtesting before that gate is materialized.

## No functional code changes

Do not modify:

```text
src/btg_ai_trader/replay/
src/btg_ai_trader/data_platform/
src/btg_ai_trader/observer/
```

Do not modify tests to make existing behavior easier to classify.

Do not alter capability scanners or workflows unless an independently documented blocker proves the gate itself is defective. If so, stop and report rather than editing the gate in this task.

Do not add dependencies.

## Explicitly forbidden new capabilities

```text
persisted research dataset technology
external historical provider
schema upcasting
resampling / aggregation
continuous futures stitching/back-adjustment
Strategy / Signal / Risk operational code
TradeIntent / OrderIntent / OrderPlan / ExecutionOrder
Paper / Live
broker/account/order APIs
FinancialLedger / portfolio accounting
P&L / economic backtest
spread / fees / slippage / queue / fill models
feature engineering
predictive ML
real money
```

## Required verification

Before opening the PR, the exact proposed HEAD must pass:

### Sprint 2 Python CI

```text
tests
lint
types
compile
dependencies
foundation
s2-boundary
diff
```

### Pinned upstream engineering verification

```text
pinned-docs-engineering
pinned-ci-engineering
```

Run `git diff --check` against exact base `071e004f2be8e5925b0de63db97af61cbbf37b30` and confirm no functional files changed.

## Pull request

Open only after the branch is coherent and the exact head is green:

```text
head = s2/03-final-acceptance-reconciliation
base = sprint/2-data-platform-replay
```

Do not merge automatically.

The PR must clearly state that it is a proposed closure gate and that independent audit plus post-merge canonical validation remain required.

## Completion report

```text
BRANCH = s2/03-final-acceptance-reconciliation
HEAD = <exact SHA>
BASE = 071e004f2be8e5925b0de63db97af61cbbf37b30
PR = <number/url>
CHANGED_FILES = <list/count>
FUNCTIONAL_CODE_CHANGED = NO
S2_AC_01_TO_10 = PASS/FAIL
S2_AC_11 = PASS/NOT_TRIGGERED/BLOCKED
S2_AC_12 = PASS/FAIL
S2_AC_13 = PASS/NOT_TRIGGERED/BLOCKED
S2_AC_14 = PASS/NOT_TRIGGERED/BLOCKED
S2_NC_01_TO_16 = PASS/FAIL
DD_TRIGGER_RECONCILIATION = PASS/FAIL
ISSUE_6_CLASSIFICATION = BLOCKING/NON_BLOCKING
ISSUE_61_CLASSIFICATION = BLOCKING/NON_BLOCKING
OPEN_S2_BLOCKERS = <count/list>
FULL_TESTS = <count/result>
LINT = PASS/FAIL
TYPES = PASS/FAIL
COMPILE = PASS/FAIL
FOUNDATION = PASS/FAIL
S2_BOUNDARY = PASS/FAIL
DIFF = PASS/FAIL
CI_RUN = <id>
UPSTREAM_RUN = <id>
PROPOSED_SPRINT_2_VERDICT = PASS/FAIL
PROMOTION_TO_SPRINT_3_GATE = YES/NO
MERGE_RECOMMENDATION = NO
```

Do not claim canonical Sprint 2 closure before independent audit, merge and post-merge validation.