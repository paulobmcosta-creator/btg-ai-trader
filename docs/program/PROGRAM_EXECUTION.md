# Program Execution — BTG AI Trader

## Current remote checkpoint

```text
AUTHORITATIVE_STATE = GITHUB_REMOTE
REPOSITORY = paulobmcosta-creator/btg-ai-trader
CANONICAL_SPRINT1_BRANCH = sprint/1-market-observer
FINAL_RECONCILIATION_BRANCH = s1/30-final-acceptance-github-security
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
SPRINT_1_LIFECYCLE = FORMALLY_CLOSED
SPRINT_1_FINAL_VERDICT = PASS

PROVIDER_DECISION = ADR-0026
PROVIDER_SELECTION = XP_SUPPLIED_MT5
PROVIDER_ID = xp-mt5
ZERO_ADDITIONAL_RECURRING_COST = HARD_CONSTRAINT
REALTIME_REQUIREMENT = PRESERVED
REAL_QUALIFYING_PROVIDER_SESSION = PASS_RUNTIME
RUNTIME_EVIDENCE_CODE_REVISION = e622658922ff38e49e1112a48d91eecb2d43a522
RUNTIME_EVIDENCE_SCOPE = s1-xp-capture-a12

PRE_RECONCILIATION_INTEGRATED_HEAD = 6457ae1dfec6e91034741e57c6343397f368cbc2
PRE_RECONCILIATION_EXACT_TREE_CI = PASS
PRE_RECONCILIATION_GITHUB_ACTIONS_RUN = 35126543429
FINAL_RECONCILIATION_VALIDATED_HEAD = 977923a4693b4b14d1ddab47a77d7bf86cb250b9
FINAL_RECONCILIATION_REMOTE_CI_RUN = 35128804489
FINAL_RECONCILIATION_PINNED_UPSTREAM_RUN = 35128804436
FINAL_RECONCILIATION_CI = PASS

OFFICIAL_CODEX_SECURITY_DIFF_SCAN = NOT_EXECUTED
GITHUB_NATIVE_SECURITY_ALTERNATIVE = ACCEPTED_BY_HUMAN_DECISION
GITHUB_NATIVE_SECURITY_GATE = PASS
SECURITY_ALTERNATIVE_RECORD = docs/program/S1_GITHUB_SECURITY_ALTERNATIVE_GATE_2026-09-16.md

SPRINT1_PROVIDER_QUALIFIED = YES
SPRINT1_ACCEPTANCE = YES
PROMOTION_TO_SPRINT_2 = YES
SPRINT_2_LIFECYCLE = AUTHORIZED_TO_OPEN

REAL_MONEY = NO
LIVE_TRADING = NO
PAPER_TRADING = NO
TRADING_CREDENTIALS_IN_PROJECT = NO
TRADING_CAPABILITY = ABSENT
```

The final adjudication commit itself is documentary only. It must also remain green under the same GitHub CI/Foundation/boundary checks before merge into the canonical Sprint 1 branch; merge is the materialization of this already-supported verdict, not a waiver of validation.

## Preserved authorities

The frozen Foundation artifacts remain unchanged. Sprint 1 closes as a passive Market Observer only. Formal causal market-data replay belongs to Sprint 2 and deterministic economic backtesting belongs to Sprint 3.

No Strategy operational path, TradeIntent operational path, RiskAuthorization Engine, OrderIntent, OrderPlan, ExecutionOrder, Paper execution, broker execution, financial-ledger mutation or real-money authority is authorized by Sprint 1 closure or Sprint 2 opening.

## Provider history and final Sprint 1 authority

ADR-0023 selected BTG Solutions Data Services historically. A Cedro free-trial path was explored and explicitly reverted because a temporary trial cannot satisfy the sustainable zero-additional-cost constraint. ADR-0025 then selected Rico-supplied MetaTrader 5, but the concrete Rico path did not reach a qualifying runtime session.

ADR-0026 selects **XP-supplied MetaTrader 5** as the qualified Sprint 1 provider. Historical decisions remain immutable evidence.

```text
BTG_DATA_SERVICES = HISTORICAL_REFERENCE_IMPLEMENTATION
CEDRO_FREE_TRIAL = REJECTED_AS_CANONICAL_LONG_TERM_PROVIDER
RICO_MT5 = HISTORICAL_SUPERSEDED_PROVIDER_PATH
XP_MT5 = SPRINT1_PROVIDER_QUALIFIED
```

The successful sanitized session record is `docs/program/workstreams/S1-XP-MT5-RUNTIME-EVIDENCE-2026-09-16.md`.

## XP/MT5 read-only boundary

```text
XP / MT5 server
-> MetaTrader 5 terminal
   -> Investor / read-only authorization
   -> custom MQL5 indicator
      -> ProviderId = xp-mt5
      -> passive WIN discovery
      -> passive ticks
      -> finalized candles
      -> append-only FILE_COMMON transport
         -> trusted Python bridge/discovery readers
            -> local read-only evidence harness
               -> technical evidence / provenance / health / latency
```

Trusted Python does not import the dual-use `MetaTrader5` package and receives no terminal-control, account, position or order interface. Legacy Rico-named files/classes remain compatibility names only; active provenance is `xp-mt5`.

## XP entitlement and runtime evidence

```text
XP_ZERO_ADDITIONAL_RECURRING_COST = PASS
XP_MINIMUM_REAL_MONEY_OPERATION_REQUIRED = NO
XP_INVESTOR_READ_ONLY = PASS_LOCAL
CREDENTIAL_DISCLOSURE = NO
ORDER_TEST_FOR_READ_ONLY = NO
```

On 2026-09-16, controlled passive capture `s1-xp-capture-a12` completed against `WINV26` / M1 on exact code revision `e622658922ff38e49e1112a48d91eecb2d43a522`, with a clean worktree. The exact reviewed indicator compiled `0 errors, 0 warnings` and returned to `IDLE` after capture.

```text
DISCOVERY_RECORDS = 18
TICK_RECORDS = 8005
FINAL_CANDLE_RECORDS_IN_RAW_CHANNEL = 2
DISCOVERY_BYTES = 2011
TICK_BYTES = 1517016
CANDLE_BYTES = 538
```

Raw provider payloads remain outside Git; sanitized counts, sizes and SHA-256 fingerprints are versioned in the runtime-evidence record.

## Negative capabilities preserved at closure

```text
TRUSTED_PYTHON_IMPORTS_METATRADER5 = NO
MT5_MASTER_PASSWORD_IN_PROJECT = NO
MT5_MASTER_PASSWORD_IN_CHAT = NO
MT5_INVESTOR_PASSWORD_ONLY = YES
MQL5_BRIDGE_PROGRAM_TYPE = CUSTOM_INDICATOR
PROGRAMMATIC_MARKET_WATCH_MUTATION = NO
PYTHON_ORDER_API = ABSENT
BROKER_ACCOUNT_API = ABSENT
ORDER_SUBMISSION = IMPOSSIBLE
ORDER_MODIFICATION = IMPOSSIBLE
ORDER_CANCELLATION = IMPOSSIBLE
FINANCIAL_LEDGER_MUTATION = ABSENT
PAPER_PATH = ABSENT
LIVE_TRADING_PATH = ABSENT
REAL_MONEY_AUTHORITY = ABSENT
ECONOMIC_COMMITMENT = IMPOSSIBLE
```

## Exact-tree engineering evidence

The post-PR-#59 integrated head `6457ae1dfec6e91034741e57c6343397f368cbc2` passed GitHub Actions run `35126543429`.

The final reconciliation head `977923a4693b4b14d1ddab47a77d7bf86cb250b9` then passed:

```text
Remote Python CI = PASS (run 35128804489)
Pinned upstream engineering verification = PASS (run 35128804436)
```

The Remote Python CI includes tests, lint, types, compile, dependencies, Foundation integrity, scoped boundary/config/possible-secret heuristics and diff checks. The earlier transient failure was solely trailing Markdown whitespace and was corrected before these green runs.

## Security assurance decision

The Official Codex Security Diff Scan was not executed and is not represented as executed. By explicit human coordination decision on 2026-09-16, the final Sprint 1 security gate uses the GitHub-native assurance package documented in `S1_GITHUB_SECURITY_ALTERNATIVE_GATE_2026-09-16.md`.

That package combines exact-tree GitHub Actions, NEG-CAP tests, boundary/static/config/possible-secret inspection, the PR #59 GitHub security review, repository/history secret-scanner controls and a formal human gate record. It changes the evidence instrument, not the 0F-E safety requirements.

```text
OFFICIAL_CODEX_SECURITY_DIFF_SCAN = NOT_EXECUTED
GITHUB_NATIVE_SECURITY_GATE = PASS
RQM_018_SECURITY_EVIDENCE = SATISFIED_BY_ACCEPTED_ALTERNATIVE
RQM_036_SECURITY_EVIDENCE = SATISFIED_BY_ACCEPTED_ALTERNATIVE
```

## Sprint 1 final adjudication

```text
RQMS = 41/41 PASS_OR_CURRENT_SCOPE
NEG_CAP_01_TO_10 = PASS
XC_01_TO_11 = PASS
SPRINT1_PROVIDER_QUALIFIED = YES
SPRINT1_ACCEPTANCE = YES
PROMOTION_TO_SPRINT_2 = YES
```

## Next canonical action

Open Sprint 2 — Data Platform & Causal Market Replay — from the formally accepted Sprint 1 head after the final adjudication PR is merged. Sprint 2 inherits every negative financial capability of Sprint 1 unless and until a later explicit gate changes authority.

Sprint 2 does **not** authorize execution, Paper, Risk, Strategy, ML operational wiring, economic backtesting, broker orders or real money.