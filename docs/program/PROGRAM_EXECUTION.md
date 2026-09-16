# Program Execution — BTG AI Trader

## Current remote checkpoint

```text
AUTHORITATIVE_STATE = GITHUB_REMOTE
REPOSITORY = paulobmcosta-creator/btg-ai-trader
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED

SPRINT_1_BRANCH = sprint/1-market-observer
SPRINT_1_ACCEPTED_HEAD = 57d820e256dd386624c1842c6f60b6797ba792aa
SPRINT_1_POST_MERGE_CI_RUN = 35129410553
SPRINT_1_POST_MERGE_CI = PASS
SPRINT_1_LIFECYCLE = FORMALLY_CLOSED
SPRINT_1_FINAL_VERDICT = PASS
SPRINT1_PROVIDER_QUALIFIED = YES
SPRINT1_ACCEPTANCE = YES

SPRINT_2_BRANCH = sprint/2-data-platform-replay
SPRINT_2_LIFECYCLE = OPEN
SPRINT_2_SCOPE = DATA_PLATFORM_AND_CAUSAL_MARKET_REPLAY
SPRINT_2_ENTRY_CONTRACT = docs/program/S2_ENTRY_CONTRACT.md
SPRINT_2_DECISION_REGISTER = docs/program/S2_DECISION_REGISTER.md
SPRINT_2_CAPABILITY_MATRIX = docs/program/S2_CAPABILITY_MATRIX.md
SPRINT_2_ENTRY_GATE = PASS
SPRINT_2_FIRST_FUNCTIONAL_CODE = AUTHORIZED
SPRINT_2_FIRST_IMPLEMENTATION_TOOL = ANTIGRAVITY
SPRINT_2_NEXT_INCREMENT = CAUSAL_REPLAY_CORE

S2_ENTRY_VALIDATED_HEAD = 8cfb17e3ba7b02c2eccc4d94f17dec986d6bb474
S2_ENTRY_CI_RUN = 35130469411
S2_ENTRY_UPSTREAM_RUN = 35130469284
S2_ENTRY_ENGINEERING = PASS

OFFICIAL_CODEX_SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_GITHUB_NATIVE_SECURITY_GATE = PASS

REAL_MONEY = NO
LIVE_TRADING = NO
PAPER_TRADING = NO
STRATEGY_OPERATIONAL_PATH = ABSENT
RISK_OPERATIONAL_PATH = ABSENT
BROKER_ORDER_API = ABSENT
FINANCIAL_LEDGER_MUTATION = ABSENT
ECONOMIC_BACKTEST = ABSENT_IN_SPRINT_2
ECONOMIC_COMMITMENT = IMPOSSIBLE
```

## Sprint 1 accepted baseline

The canonical Sprint 1 merge `57d820e256dd386624c1842c6f60b6797ba792aa` formally closed the Market Observer and authorized Sprint 2. Its push-triggered Remote Python CI run `35129410553` completed successfully after merge.

The qualified provider remains XP-supplied MetaTrader 5 for the passive Sprint 1 observation purpose under ADR-0026. The successful qualifying capture is `s1-xp-capture-a12` against `WINV26` / M1 on revision `e622658922ff38e49e1112a48d91eecb2d43a522`.

The Official Codex Security Diff Scan was not executed. The accepted Sprint 1 security instrument is the explicit GitHub-native alternative recorded in `docs/program/S1_GITHUB_SECURITY_ALTERNATIVE_GATE_2026-09-16.md`.

## Sprint 2 authority

Sprint 2 is open only for **Data Platform & Causal Market Replay**. The governing records are:

- `docs/sprints/SPRINT_2.md`;
- `docs/program/S2_ENTRY_CONTRACT.md`;
- `docs/program/S2_DECISION_REGISTER.md`;
- `docs/program/S2_CAPABILITY_MATRIX.md`;
- `docs/program/S2_ENTRY_GATE.md`.

The Entry Gate is substantively PASS. The materialization head `8cfb17e3ba7b02c2eccc4d94f17dec986d6bb474` passed all eight Sprint 2 CI jobs in run `35130469411` and both pinned upstream engineering jobs in run `35130469284`.

Because the final PASS declarations themselves change the PR head, the final PR head must also pass the same checks before integration into `sprint/2-data-platform-replay`. This is an exact-tree integration condition, not an unresolved design blocker.

## Sprint 2 authorized engineering domains

- market-data normalization while preserving source facts and missingness;
- historical capture/dataset contracts and provenance;
- causal replay of preserved market events;
- explicit knowledge cutoffs;
- virtual/control clock semantics;
- deterministic replay ordering and reproducibility;
- historical data quality and lineage;
- replay-specific tests and evidence.

## First functional increment

After the Entry Gate PR is merged and the canonical branch remains green, the first new functional increment is authorized via Antigravity under:

```text
docs/program/workstreams/S2-ANTIGRAVITY-HANDOFF.md
```

Preferred child branch:

```text
s2/01-causal-replay-core
```

The first increment is limited to a pure causal replay core over existing accepted `EventEnvelope` values. It must use one explicit `(provider_id, capture_scope)` lane, known `knowledge_time`, monotonic inclusive cutoffs, supplied causal order and exact rational logical speed. It must not depend on wall clock, provider/network access or financial capability.

Historical PRs #9 and #37 are research-only sources. No historical branch is automatically merged or cherry-picked.

## Sprint 2 exclusions

Sprint 2 does not authorize:

```text
StrategyDecision operational path
TradeIntent operational path
RiskAuthorization operational path
OrderIntent / OrderPlan / ExecutionOrder
Paper execution
Live execution
broker order/account APIs
real-money operation
P&L simulation
economic spread/cost model
slippage model
queue/fill simulation
financial Ledger mutation
predictive ML operational wiring
```

Economic backtesting belongs to Sprint 3 or a later formally authorized stage.

## Sprint 2 engineering controls

The canonical Sprint 2 engineering gate now includes:

```text
Sprint 2 Python CI
  tests
  lint
  types
  compile
  dependencies
  foundation
  s2-boundary
  diff

Pinned upstream engineering verification
  pinned-docs-engineering
  pinned-ci-engineering
```

`scripts/check_s2_boundary.py` is the stage-specific boundary checker. The Sprint 1 boundary checker is intentionally not repurposed to reject capabilities that are legitimate only after Sprint 1.

## Repository hardening

Administrative branch/ruleset protection remains tracked in Issue #61 because the connected GitHub integration does not expose branch-protection/ruleset write administration. This administrative limitation does not waive CI or sprint gates.