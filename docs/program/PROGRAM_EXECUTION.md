# Program Execution — BTG AI Trader

## Current remote checkpoint

```text
AUTHORITATIVE_STATE = GITHUB_REMOTE
REPOSITORY = paulobmcosta-creator/btg-ai-trader
CANONICAL_SPRINT1_BRANCH = sprint/1-market-observer
FINAL_RECONCILIATION_BRANCH = s1/30-final-acceptance-github-security
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
SPRINT_1_LIFECYCLE = FINAL_ACCEPTANCE_RECONCILIATION

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

OFFICIAL_CODEX_SECURITY_DIFF_SCAN = NOT_EXECUTED
GITHUB_NATIVE_SECURITY_ALTERNATIVE = ACCEPTED_BY_HUMAN_DECISION
GITHUB_NATIVE_SECURITY_GATE = PASS
SECURITY_ALTERNATIVE_RECORD = docs/program/S1_GITHUB_SECURITY_ALTERNATIVE_GATE_2026-09-16.md

SPRINT1_PROVIDER_QUALIFIED = YES_CONDITIONAL_ON_FINAL_RECONCILIATION_CI
SPRINT1_ACCEPTANCE = PENDING_FINAL_RECONCILIATION_CI
PROMOTION_TO_SPRINT_2 = PENDING_FINAL_RECONCILIATION_CI

REAL_MONEY = NO
LIVE_TRADING = NO
PAPER_TRADING = NO
TRADING_CREDENTIALS_IN_PROJECT = NO
TRADING_CAPABILITY = ABSENT
```

Historical execution detail remains in Git history and prior PRs. This living file records the state required to resume safely.

## Preserved authorities

The frozen Foundation artifacts remain unchanged. Sprint 1 remains a passive Market Observer only. Formal causal market-data replay belongs to Sprint 2 and deterministic economic backtesting belongs to Sprint 3.

No Strategy operational path, TradeIntent operational path, RiskAuthorization Engine, OrderIntent, OrderPlan, ExecutionOrder, Paper execution, broker execution, financial-ledger mutation or real-money authority is authorized by Sprint 1 closure.

## Provider history and current authority

ADR-0023 selected BTG Solutions Data Services historically. A Cedro free-trial path was explored and explicitly reverted because a temporary trial cannot satisfy the sustainable zero-additional-cost constraint. ADR-0025 then selected Rico-supplied MetaTrader 5, but the concrete Rico path did not reach a qualifying runtime session.

ADR-0026 selects **XP-supplied MetaTrader 5** as the active Sprint 1 provider. The historical decisions remain immutable evidence.

```text
BTG_DATA_SERVICES = HISTORICAL_REFERENCE_IMPLEMENTATION
CEDRO_FREE_TRIAL = REJECTED_AS_CANONICAL_LONG_TERM_PROVIDER
RICO_MT5 = HISTORICAL_SUPERSEDED_PROVIDER_PATH
XP_MT5 = QUALIFIED_RUNTIME_PROVIDER
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

## Negative capabilities

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

The post-PR-#59 integrated head `6457ae1dfec6e91034741e57c6343397f368cbc2` triggered GitHub Actions run `35126543429`. All required jobs passed on that exact head:

```text
tests = PASS
lint = PASS
types = PASS
compile = PASS
dependencies = PASS
foundation = PASS
boundary = PASS
diff = PASS
```

This resolves the former B6 blocker for the integrated pre-reconciliation tree. The final documentary reconciliation branch must pass the same checks before merge; because this reconciliation changes no functional source, a green exact-head run will close the final-tree evidence requirement.

## Security assurance decision

The Official Codex Security Diff Scan was not executed and is not represented as executed. By explicit human coordination decision on 2026-09-16, the final Sprint 1 security gate uses the GitHub-native assurance package documented in `S1_GITHUB_SECURITY_ALTERNATIVE_GATE_2026-09-16.md`.

That package combines exact-tree GitHub Actions, NEG-CAP tests, boundary/static/config/possible-secret inspection, the PR #59 GitHub security review, repository/history secret-scanner controls and a formal human gate record. It changes the evidence instrument, not the 0F-E safety requirements.

```text
OFFICIAL_CODEX_SECURITY_DIFF_SCAN = NOT_EXECUTED
GITHUB_NATIVE_SECURITY_GATE = PASS
RQM_018_SECURITY_EVIDENCE = SATISFIED_BY_ACCEPTED_ALTERNATIVE
RQM_036_SECURITY_EVIDENCE = SATISFIED_BY_ACCEPTED_ALTERNATIVE
```

## Final closure sequence

```text
1. Run exact-head CI/Foundation/boundary/NEG-CAP on this final reconciliation branch.
2. If green, record the exact run/head in the final acceptance gate.
3. Adjudicate XC-01..XC-11 conjunctively as PASS.
4. Merge the documentary closure into sprint/1-market-observer.
5. Mark Sprint 1 formally accepted and provider qualification final.
6. Open Sprint 2 on a new canonical sprint branch from the accepted Sprint 1 head.
```

No step above authorizes execution, Paper, Risk, Strategy, ML operational wiring or real money.