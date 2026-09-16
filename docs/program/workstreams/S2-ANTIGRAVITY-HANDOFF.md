# Sprint 2 — Antigravity Handoff

## Purpose

Use Antigravity to accelerate Sprint 2 implementation **after** the entry gate is merged. Antigravity is an implementation agent, not a source of authority. The repository governs scope.

## Mandatory read order

Before editing code, Antigravity must read, in order:

1. `AGENTS.md`
2. `docs/program/S2_ENTRY_CONTRACT.md`
3. `docs/program/S2_DECISION_REGISTER.md`
4. `docs/program/S2_CAPABILITY_MATRIX.md`
5. `docs/sprints/SPRINT_2.md`
6. `docs/program/PROGRAM_EXECUTION.md`
7. relevant accepted Sprint 1 domain/temporal/provenance code and tests

Historical PRs #9 and #37 are research references only. Do not merge or cherry-pick them wholesale. Re-derive any useful idea against the current accepted types.

## First Antigravity assignment

Create a child branch from `sprint/2-data-platform-replay` named approximately:

```text
s2/01-causal-replay-core
```

Implement only the first causal replay core:

- new S2 namespace isolated from `observer`, preferably `src/btg_ai_trader/replay/`;
- immutable schedule consuming existing immutable `EventEnvelope` values;
- one explicit `(provider_id, capture_scope)` causal lane;
- require known timezone-aware/UTC-compatible `knowledge_time` for scheduling;
- preserve supplied causal order;
- reject mixed lanes, duplicate EventIds and knowledge-time regression;
- inclusive monotonic `advance_to(knowledge_cutoff)`;
- exact positive rational speed representation;
- deterministic immutable replay emissions/state;
- tests for all positive and negative semantics.

## Strict exclusions for the first assignment

Do not implement or introduce:

```text
network/provider I/O
broker/account APIs
MetaTrader5 import in trusted Python
credentials or secrets
StrategyDecision / TradeIntent
Signal or Risk engines
OrderIntent / OrderPlan / ExecutionOrder
Paper or Live execution
FinancialLedger or portfolio accounting
P&L
spread/fee/slippage economics
queue/fill simulation
economic latency
feature engineering
predictive ML
continuous futures stitching
resampling policy
persistent research dataset format
external historical vendor integration
wall-clock sleep/scheduling
```

If an implementation appears to require one of these, STOP and record a finding/decision request instead of widening scope.

## Temporal contract

Antigravity must treat `knowledge_time` as the causal visibility boundary. `event_time` cannot be used as a substitute for unavailable knowledge. Equal knowledge times preserve existing order. Backward cutoff/clock changes fail without partial state mutation.

Do not sort input to repair chronology. Invalid chronology is evidence to reject, not something to normalize away.

## Determinism

For the first increment, deterministic equivalence means identical accepted logical inputs, code revision and configuration produce the same ordered logical output identities and exact pacing values. Do not claim byte-level dataset equivalence before DD-82/DD-83 are materialized.

## Engineering workflow

Antigravity should:

1. inspect current canonical Sprint 2 head before editing;
2. create a narrow child branch;
3. make a docs-first decision update only if a material new choice is needed;
4. implement one bounded increment;
5. add/modify tests with production code;
6. run the Sprint 2 GitHub CI on the exact pushed head;
7. fix all test/lint/type/compile/foundation/s2-boundary/diff failures;
8. open a PR to `sprint/2-data-platform-replay`;
9. do not merge with failed/pending checks;
10. report exact branch, head SHA, changed files, CI run IDs, test count and unresolved findings.

## Required tests for first replay core

At minimum:

- empty schedule;
- input copy / immutability;
- multiple instruments in same lane;
- mixed provider rejection;
- mixed capture-scope rejection;
- missing/unknown/naive knowledge-time rejection where scheduling requires a known instant;
- knowledge-time regression rejection;
- duplicate EventId rejection;
- equal knowledge time preserving supplied order;
- before/at/after inclusive cutoff behavior;
- backward cutoff rollback safety;
- exact 1x, 2x and 0.5x pacing;
- arbitrary positive rational speed;
- zero/negative speed rejection;
- deterministic repeated construction/replay;
- no wall-clock/sleep/network/financial capability.

## Completion report format

Antigravity must end each assignment with:

```text
BRANCH = ...
HEAD = ...
BASE = ...
CHANGED_FILES = ...
TESTS = ...
LINT = PASS/FAIL
TYPES = PASS/FAIL
COMPILE = PASS/FAIL
FOUNDATION = PASS/FAIL
S2_BOUNDARY = PASS/FAIL
DIFF = PASS/FAIL
CI_RUN = ...
FINDINGS = ...
MERGE_RECOMMENDATION = YES/NO
```

No statement of Sprint 2 completion is permitted from a single increment.