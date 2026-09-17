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
SPRINT_2_LIFECYCLE = FORMALLY_CLOSED
SPRINT_2_FINAL_VERDICT = PASS
SPRINT_2_CANONICAL_HEAD = ba6c0c41988fc9fefbdff13b0daedf96301dd74c
SPRINT_2_SCOPE = DATA_PLATFORM_AND_CAUSAL_MARKET_REPLAY
SPRINT_2_ENTRY_CONTRACT = docs/program/S2_ENTRY_CONTRACT.md
SPRINT_2_DECISION_REGISTER = docs/program/S2_DECISION_REGISTER.md
SPRINT_2_CAPABILITY_MATRIX = docs/program/S2_CAPABILITY_MATRIX.md
SPRINT_2_ENTRY_GATE = PASS
S2_A = ACCEPTED (PR #65, 9faa43c3bc112c1d2e558aa3e1518371880cc518)
S2_B = ACCEPTED (PR #67, 071e004f2be8e5925b0de63db97af61cbbf37b30)
S2_C = ACCEPTED (PR #70, ba6c0c41988fc9fefbdff13b0daedf96301dd74c)
PROMOTION_TO_SPRINT_3_GATE = YES

SPRINT_3_BRANCH = sprint/3-deterministic-economic-backtesting
SPRINT_3_LIFECYCLE = CLOSURE_CANDIDATE
SPRINT_3_FINAL_VERDICT = PROPOSED_PASS
SPRINT_3_SCOPE = DETERMINISTIC_ECONOMIC_BACKTESTING
SPRINT_3_ENTRY_CONTRACT = docs/program/S3_ENTRY_CONTRACT.md
SPRINT_3_DECISION_REGISTER = docs/program/S3_DECISION_REGISTER.md
SPRINT_3_CAPABILITY_MATRIX = docs/program/S3_CAPABILITY_MATRIX.md
SPRINT_3_FINAL_ACCEPTANCE = docs/program/S3_FINAL_ACCEPTANCE.md
SPRINT_3_ENTRY_GATE = PASS
S3_TASK_PACKET = docs/program/workstreams/S3-ANTIGRAVITY-FULL-SPRINT.md
S3_WORK_BRANCH = s3/00-full-deterministic-economic-backtesting
S3_BASE_SHA = ba6c0c41988fc9fefbdff13b0daedf96301dd74c
MERGE_AUTHORIZED = NO
PROMOTION_TO_SPRINT_4_GATE = NO_UNTIL_INDEPENDENT_REAUDIT

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

## Sprint 2 completed increments & final reconciliation

### S2-A — Causal Replay Core
- **PR:** #65 (merged at `9faa43c3bc112c1d2e558aa3e1518371880cc518`)
- **CI / Upstream:** runs `35150432340` (8/8 PASS) and `35150432259` (2/2 PASS)
- **Scope:** Bounded causal replay core (`CausalMarketReplaySchedule`, `CausalMarketReplayCursor`, `CausalLane`, `ReplaySpeed`, `ReplayEmission`, `ReplayEmissionLineage`, `ReplayInputBoundary` per DD-15). Single `(provider_id, capture_scope)` lane, monotonic inclusive cutoffs, UTC `knowledge_time` visibility, exact rational speeds, zero wall-clock dependencies.

### S2-B — Lossless Normalization & Data-Quality Evidence
- **PR:** #67 (merged at `071e004f2be8e5925b0de63db97af61cbbf37b30`)
- **CI / Upstream:** runs `35163848955` (8/8 PASS) and `35163848942` (2/2 PASS)
- **Scope:** In-memory lossless Data Platform normalization (`NormalizedMarketBatch`, `normalize_market_batch`, `QualityFinding`). Preserves all source facts and `MissingReason` (DD-80), flags replay-blocking vs. non-blocking quality findings, zero silent imputation or synthetic temporal fabrication.

### S2-C — Final Acceptance Reconciliation & Sprint 2 Closure Gate
- **Branch:** `s2/03-final-acceptance-reconciliation`
- **Issue:** #68
- **PR:** #70
- **Artifact:** `docs/program/S2_FINAL_ACCEPTANCE.md`
- **Scope:** Full conjunctive audit of S2-AC-01..14, S2-NC-01..16, and active decisions DD-05..83. Zero new functional code. Formal proposal of Sprint 2 closure.

Historical PRs #9 and #37 remained research-only sources throughout Sprint 2; no historical branch was merged or cherry-picked.

## Sprint 3 — Deterministic Economic Backtesting — Candidate Closure

Sprint 3 has been fully implemented and verified under single-batch autonomous execution mode:

- **Work Branch:** `s3/00-full-deterministic-economic-backtesting`
- **Canonical Target:** `sprint/3-deterministic-economic-backtesting`
- **Issue:** #71
- **Artifact:** `docs/program/S3_FINAL_ACCEPTANCE.md`
- **Scope:** Complete Deterministic Execution Economics Kernel (`btg_ai_trader.backtesting`):
  - Domain, actions, and simulated fills (`domain.py`)
  - Side-aware spread, adverse slippage, configurable fees, and virtual latency (`assumptions.py`)
  - Causal execution engine with fail-closed missingness and quote staleness detection (`execution.py`)
  - Isolated backtest position accounting, WACB, realized/unrealized P&L, non-double-counting, and end-of-window policy (`accounting.py`)
  - Descriptive backtest statistics and drawdown metrics (`metrics.py`)
  - Deterministic replay orchestrator and session engine (`engine.py`)
  - Cryptographic input boundaries, manifest generation, and provenance (`provenance.py`)
  - Sensitivity sweeps and monotonicity invariant verification (`sensitivity.py`)
- **Verification:** 91% combined coverage on backtesting kernel (1,328 statements, 86 missed, 598 branches, 57 missed/partial; 126 passed S3 tests, including 87 unit and 39 boundary/acceptance cases; 757 full repository tests), zero lint errors, zero type errors, all boundary checks PASS.
- **Verdict:** `PROPOSED_SPRINT_3_VERDICT = PROPOSED_PASS`, `SPRINT_3_LIFECYCLE = CLOSURE_CANDIDATE`, `MERGE_AUTHORIZED = NO`, `PROMOTION_TO_SPRINT_4_GATE = NO_UNTIL_INDEPENDENT_REAUDIT`.

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

Administrative branch/ruleset protection remains tracked in Issue #61 because the connected GitHub integration does not expose branch-protection/ruleset write administration. Administrative branch/ruleset protection remains absent/pending, and Issue #61 remains open as defense-in-depth. CI, boundary scanners, and manual pull request review provide technical verification gates, but these mechanisms do not replace GitHub administrative enforcement. Under the governing contract, administrative protection is not a functional closure requirement for Sprint 2.