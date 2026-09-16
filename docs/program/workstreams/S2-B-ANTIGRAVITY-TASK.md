# S2-B — Antigravity Task Packet: Lossless Normalization & Data-Quality Evidence

## Execute this task on the current branch only

```text
REPOSITORY = paulobmcosta-creator/btg-ai-trader
CANONICAL_BASE = sprint/2-data-platform-replay
ACCEPTED_BASE_SHA = 9faa43c3bc112c1d2e558aa3e1518371880cc518
WORK_BRANCH = s2/02-normalization-quality
ISSUE = #66
IMPLEMENTATION_AUTHORITY = BOUNDED_S2_LOSSLESS_NORMALIZATION_AND_QUALITY_ONLY
```

Do not switch implementation to `main`, historical research branches, Sprint 1 branches or any other branch.

## Mandatory read order

Before editing functional code, read:

1. `AGENTS.md`
2. `docs/program/S2_ENTRY_CONTRACT.md`
3. `docs/program/S2_DECISION_REGISTER.md`
4. `docs/program/S2_CAPABILITY_MATRIX.md`
5. `docs/program/S2_ENTRY_GATE.md`
6. `docs/sprints/SPRINT_2.md`
7. `docs/program/workstreams/S2-ANTIGRAVITY-HANDOFF.md`
8. this file
9. accepted S2-A replay/input-boundary code and tests
10. accepted Sprint 1 `EventEnvelope`, market, temporal, values, identity and provenance types/tests

PRs #9 and #37 remain historical research only. Do not merge or cherry-pick them wholesale.

## Objective

Implement a pure, deterministic, in-memory Data Platform normalization layer that preserves accepted source evidence losslessly and produces separate immutable data-quality evidence.

Prefer:

```text
src/btg_ai_trader/data_platform/
tests/data_platform/
```

The accepted `EventEnvelope` remains the source-event model. Do not invent a competing market-event type.

## Required semantics

1. One normalization batch/boundary is one explicit `(provider_id, capture_scope)` lane.
2. Multiple instruments are allowed inside the same lane.
3. Preserve supplied event order exactly; do not sort or synthesize cross-lane order.
4. Preserve every accepted source fact exactly: EventId, provider/scope/symbol, instrument identity or explicit missingness, all temporal evidence, Tick/Candle payload values, envelope/schema versions, source sequence/evidence and ingestion order.
5. Preserve every `MissingReason` exactly. Missing data is evidence, not zero, `None` or a guessed value.
6. Never derive `knowledge_time` from event time, ingestion time, effective time, current time or file order.
7. Missing/unknown `knowledge_time` must remain unchanged and yield explicit replay-blocking quality evidence.
8. Explicitly missing event-time value/basis/resolution must remain unchanged and yield deterministic quality evidence appropriate to the missing field.
9. Explicitly missing Tick/Candle numeric fields must remain unchanged and yield deterministic quality evidence without imputation.
10. Quality findings must be immutable, deterministic, separate from the source envelope and traceable to the source EventId.
11. The normalization result must defensively capture inputs and must not mutate source envelopes.
12. Structurally incompatible lane input must fail closed rather than be repaired.
13. The same accepted logical inputs/configuration must produce the same ordered normalized outputs and quality evidence.

## Quality evidence boundary

Design the minimum typed model needed to express deterministic quality findings. It must distinguish at least whether a finding blocks causal replay.

Do not equate explicit missingness with a fabricated source error. Use neutral evidence categories/codes tied to concrete facts, for example missing temporal evidence or missing reported market fields.

Do not create economic interpretations, scores, rankings, signal quality, tradability judgments or trading readiness labels.

## Explicitly forbidden

```text
source-evidence mutation
silent imputation
zero-filling
forward/backward fill
interpolation
resampling or aggregation policy
continuous futures stitching or back-adjustment
synthetic cross-lane ordering
external historical-data provider integration
canonical persisted research dataset format
dataset registry/version technology
retention/archival policy
wall-clock scheduling or causal semantics
Strategy / Signal / Risk operational paths
TradeIntent / OrderIntent / OrderPlan / ExecutionOrder
Paper / Live execution
broker/account/order APIs
FinancialLedger / position / portfolio accounting
P&L or economic backtest
spread / fees / slippage / queue / fill models
feature engineering
predictive ML
```

DD-80 is active: preserve missingness and forbid silent imputation. DD-81 remains deferred/forbidden. DD-82/83 persistence technology is not triggered because S2-B is in-memory only.

## Required tests

At minimum:

- empty normalization batch;
- defensive input capture and immutability;
- multiple instruments in same lane;
- mixed provider rejection;
- mixed capture-scope rejection;
- exact preservation of EventId/source/instrument/times/payload/schema/order evidence;
- Tick missingness preservation for bid/ask/last/volume;
- Candle missingness preservation for OHLC/volume and temporal evidence;
- missing/unknown knowledge time remains unchanged and creates replay-blocking finding;
- known knowledge time remains unchanged;
- missing event-time value/basis/resolution remains unchanged and is reported;
- no temporal-axis substitution;
- deterministic repeated normalization;
- source envelope identity/content remains unchanged;
- every finding traces to source EventId;
- static absence of imputation, network, wall-clock and financial/economic capability.

Add property tests where useful without expanding scope.

## Required CI

Exact proposed HEAD must pass Sprint 2 Python CI:

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

and Pinned upstream engineering verification:

```text
pinned-docs-engineering
pinned-ci-engineering
```

Fix failures without weakening gates or suppressing checks.

## Pull request

Open a PR only after the exact proposed head is green:

```text
head = s2/02-normalization-quality
base = sprint/2-data-platform-replay
```

Do not merge automatically.

## Completion report

```text
BRANCH = s2/02-normalization-quality
HEAD = <exact SHA>
BASE = 9faa43c3bc112c1d2e558aa3e1518371880cc518
CHANGED_FILES = <list/count>
TESTS = <count/result>
LINT = PASS/FAIL
TYPES = PASS/FAIL
COMPILE = PASS/FAIL
FOUNDATION = PASS/FAIL
S2_BOUNDARY = PASS/FAIL
DIFF = PASS/FAIL
LOSSLESS_NORMALIZATION = PASS/FAIL
MISSINGNESS_PRESERVATION = PASS/FAIL
DATA_QUALITY_EVIDENCE = PASS/FAIL
CI_RUN = <id>
UPSTREAM_RUN = <id>
FINDINGS = <none or explicit list>
MERGE_RECOMMENDATION = YES/NO
```

Do not claim Sprint 2 completion, persisted-dataset readiness, economic backtest readiness, Paper/Live readiness or trading readiness.