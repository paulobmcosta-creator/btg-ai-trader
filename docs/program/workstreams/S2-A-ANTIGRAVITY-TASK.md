# S2-A — Antigravity Task Packet: Causal Replay Core

## Execute this task on the current branch only

```text
REPOSITORY = paulobmcosta-creator/btg-ai-trader
CANONICAL_BASE = sprint/2-data-platform-replay
ACCEPTED_BASE_SHA = 00cc56100d5c9a7cb28a34947726eb32bdfab8fd
WORK_BRANCH = s2/01-causal-replay-core
SPRINT_2_ENTRY_GATE = PASS
IMPLEMENTATION_AUTHORITY = BOUNDED_S2_CAUSAL_REPLAY_CORE_ONLY
```

Do not switch the implementation target to `main`, Sprint 1 branches, historical research branches or any other branch.

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
9. existing accepted Sprint 1 `EventEnvelope`, temporal identity and provenance types/tests needed by the implementation

PRs #9 and #37 may be inspected only as historical research. Do not merge, rebase from, or cherry-pick them wholesale. Re-derive any useful idea against the current accepted baseline.

## Objective

Implement the first functional Sprint 2 increment: a pure, deterministic, immutable causal market-data replay core.

Prefer the namespace:

```text
src/btg_ai_trader/replay/
```

and corresponding tests under:

```text
tests/replay/
```

Do not alter accepted Sprint 1 Observer semantics unless a documented incompatibility requires stopping for a decision.

## Required behavior

The core must:

1. consume existing accepted immutable `EventEnvelope` values rather than inventing a parallel market-event type;
2. bind one schedule to one explicit causal lane `(provider_id, capture_scope)`;
3. allow multiple instruments within that same lane;
4. require known, timezone-aware and semantically valid `knowledge_time` for replay scheduling;
5. preserve the supplied causal order;
6. reject knowledge-time regression instead of sorting the input;
7. reject duplicate EventIds;
8. reject mixed providers and mixed capture scopes;
9. preserve equal-knowledge-time input order;
10. expose inclusive monotonic `advance_to(knowledge_cutoff)` behavior;
11. reject a backward cutoff without partial state mutation;
12. represent replay speed as an exact positive rational value;
13. derive logical pacing deterministically without `sleep()` or wall-clock dependence;
14. preserve immutable schedule/state/emission semantics;
15. produce deterministic logical outputs for identical accepted logical input, code/configuration and replay operations.

## Temporal rule

`knowledge_time` is the causal visibility boundary. `event_time` remains source evidence and must not be used to expose information earlier than it became knowable.

Do not repair missing or invalid knowledge-time evidence by copying `event_time`, `ingestion_time`, current time, file order inferred after the fact, or another synthetic timestamp.

Do not sort invalid input to make it acceptable. Reject it fail-closed.

## Explicitly forbidden in S2-A

Do not introduce any of the following:

```text
network/provider I/O
external historical-data vendor integration
MetaTrader5 import in trusted Python
broker/account/order APIs
credentials or secrets
StrategyDecision
TradeIntent
Signal engine
Risk engine / RiskAuthorization
OrderIntent / OrderPlan / ExecutionOrder
Paper execution
Live execution
FinancialLedger / position / portfolio accounting
P&L or economic performance
spread / fees / slippage models
queue / fill simulation
economic latency model
feature engineering
predictive ML
continuous futures stitching / back-adjustment
resampling policy
canonical persisted research dataset format
wall-clock sleep or scheduling
```

If the requested core appears to need any item above, stop that part and report a finding. Do not widen scope.

## Required tests

At minimum cover:

- empty schedule;
- defensive input capture / immutability;
- multiple instruments in same lane;
- mixed provider rejection;
- mixed capture-scope rejection;
- missing / unknown / naive required knowledge-time rejection;
- knowledge-time regression rejection;
- duplicate EventId rejection;
- equal knowledge time preserving supplied order;
- cutoff before first event;
- cutoff exactly at event;
- cutoff after multiple events;
- repeated same cutoff behavior;
- backward cutoff rollback safety;
- exact speed 1x;
- exact speed 2x;
- exact speed 1/2x;
- arbitrary positive rational speed;
- zero speed rejection;
- negative speed rejection;
- deterministic repeated schedule construction/replay;
- static absence of wall-clock, network and financial capability.

Add additional property/regression tests when they materially strengthen the contract without expanding scope.

## Required CI

The exact proposed HEAD must pass `Sprint 2 Python CI`:

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

and `Pinned upstream engineering verification`:

```text
pinned-docs-engineering
pinned-ci-engineering
```

Fix all failures without weakening the gate or suppressing checks. Do not merge with any required check failed or pending.

## Pull request

When implementation and exact-head validation are complete, open a PR:

```text
head = s2/01-causal-replay-core
base = sprint/2-data-platform-replay
```

The PR must state that it is one bounded Sprint 2 increment and does not complete Sprint 2.

## Completion report

Return:

```text
BRANCH = s2/01-causal-replay-core
HEAD = <exact SHA>
BASE = 00cc56100d5c9a7cb28a34947726eb32bdfab8fd
CHANGED_FILES = <list/count>
TESTS = <count/result>
LINT = PASS/FAIL
TYPES = PASS/FAIL
COMPILE = PASS/FAIL
FOUNDATION = PASS/FAIL
S2_BOUNDARY = PASS/FAIL
DIFF = PASS/FAIL
CI_RUN = <id>
UPSTREAM_RUN = <id>
FINDINGS = <none or explicit list>
MERGE_RECOMMENDATION = YES/NO
```

Do not claim Sprint 2 completion, economic readiness, paper readiness, live readiness or trading readiness.