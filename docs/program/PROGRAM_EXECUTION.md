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
SPRINT_2_ENTRY_DOC = docs/sprints/SPRINT_2.md
SPRINT_2_FUNCTIONAL_IMPLEMENTATION = BLOCKED_UNTIL_ENTRY_MATERIALIZATION

OFFICIAL_CODEX_SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_GITHUB_NATIVE_SECURITY_GATE = PASS

REAL_MONEY = NO
LIVE_TRADING = NO
PAPER_TRADING = NO
STRATEGY_OPERATIONAL_PATH = ABSENT
RISK_OPERATIONAL_PATH = ABSENT
BROKER_ORDER_API = ABSENT
FINANCIAL_LEDGER_MUTATION = ABSENT
ECONOMIC_COMMITMENT = IMPOSSIBLE
```

## Sprint 1 accepted baseline

The canonical Sprint 1 merge `57d820e256dd386624c1842c6f60b6797ba792aa` formally closed the Market Observer and authorized Sprint 2. Its push-triggered Remote Python CI run `35129410553` completed successfully after merge.

The qualified provider remains XP-supplied MetaTrader 5 for the passive Sprint 1 observation purpose under ADR-0026. The successful qualifying capture is `s1-xp-capture-a12` against `WINV26` / M1 on revision `e622658922ff38e49e1112a48d91eecb2d43a522`.

The Official Codex Security Diff Scan was not executed. The accepted Sprint 1 security instrument is the explicit GitHub-native alternative recorded in `docs/program/S1_GITHUB_SECURITY_ALTERNATIVE_GATE_2026-09-16.md`.

## Sprint 2 authority

Sprint 2 is open only for **Data Platform & Causal Market Replay**. Its canonical entry/scope record is `docs/sprints/SPRINT_2.md`.

Authorized design/engineering domains include:

- market-data normalization while preserving source facts and missingness;
- historical capture/dataset contracts and provenance;
- causal replay of preserved market events;
- explicit knowledge cutoffs;
- virtual/control clock semantics;
- deterministic replay ordering and reproducibility;
- historical data quality and lineage;
- replay-specific tests and evidence.

## Sprint 2 exclusions

Sprint 2 does not authorize:

```text
StrategyDecision operational path
TradeIntent operational path
RiskAuthorization operational path
OrderIntent / OrderPlan / ExecutionOrder
Paper execution
Live execution
broker order APIs
real-money operation
P&L simulation
economic spread/cost model
slippage model
queue/fill simulation
financial Ledger mutation
predictive ML operational wiring
```

Economic backtesting belongs to Sprint 3 or a later formally authorized stage.

## Historical speculative work

PRs #9 and #37 are closed as superseded research precursors. They may be consulted as historical design evidence but are not part of the Sprint 2 baseline and must not be merged or promoted automatically.

## Current gate

```text
S2_CURRENT_GATE = ENTRY_MATERIALIZATION
S2_FIRST_FUNCTIONAL_CODE = NOT_AUTHORIZED_YET
```

Before new Sprint 2 functional code, materialize the Sprint 2 entry contract/scope gate, capability matrix, temporal/replay decisions and verification plan against the accepted Sprint 1 baseline.

## Repository hardening

Administrative branch/ruleset protection remains tracked in Issue #61 because the connected GitHub integration does not expose branch-protection/ruleset write administration. This administrative limitation does not waive CI or sprint gates.