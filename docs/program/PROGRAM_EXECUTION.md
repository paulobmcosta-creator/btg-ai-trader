# Program Execution — BTG AI Trader

## Current remote checkpoint

```text
AUTHORITATIVE_STATE = GITHUB_REMOTE
REPOSITORY = paulobmcosta-creator/btg-ai-trader
SPRINT_BRANCH = sprint/1-market-observer
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
SPRINT_1_LIFECYCLE = OPEN
S1_A_AUTHORIZED = YES

PROVIDER_DECISION = ADR-0026
PROVIDER_SELECTION = XP_SUPPLIED_MT5
PROVIDER_ID = xp-mt5
PROVIDER_SELECTION_STATUS = ACCEPTED_FOR_QUALIFICATION
ZERO_ADDITIONAL_RECURRING_COST = HARD_CONSTRAINT
REALTIME_REQUIREMENT = PRESERVED
PRELIMINARY_XP_SESSION = EXECUTED_NONQUALIFYING
REAL_QUALIFYING_PROVIDER_SESSION = PASS_RUNTIME
RUNTIME_EVIDENCE_CODE_REVISION = e622658922ff38e49e1112a48d91eecb2d43a522
RUNTIME_EVIDENCE_SCOPE = s1-xp-capture-a12
SPRINT1_PROVIDER_QUALIFIED = NO_PENDING_FINAL_TREE_GATES
SPRINT1_ACCEPTANCE = NOT_GRANTED
PROMOTION_TO_SPRINT_2 = NO
SECURITY_DIFF_SCAN = NOT_EXECUTED

MT5_OFFLINE_TICK_BRIDGE = INTEGRATED
MT5_OFFLINE_FINAL_CANDLE_BRIDGE = INTEGRATED
MT5_OFFLINE_SYMBOL_DISCOVERY = INTEGRATED
XP_MT5_RUNTIME_RUNBOOK = INTEGRATED
MT5_RUNTIME_EVIDENCE_HARNESS = INTEGRATED_AND_REALTIME_EXERCISED

REAL_MONEY = NO
LIVE_TRADING = NO
PAPER_TRADING = NO
TRADING_CREDENTIALS_IN_PROJECT = NO
TRADING_CAPABILITY = ABSENT
```

Historical execution detail remains in Git history and prior PRs. This living file records only the state required to resume safely.

## Preserved authorities

The frozen Foundation artifacts remain unchanged. Sprint 1 remains passive Market Observer only. Formal causal replay belongs to Sprint 2 and deterministic economic backtesting belongs to Sprint 3.

No Strategy operational path, TradeIntent operational path, RiskAuthorization Engine, OrderIntent, OrderPlan, ExecutionOrder, Paper execution, broker execution, financial-ledger mutation or real-money authority may appear in Sprint 1.

## Provider history and current authority

ADR-0023 selected BTG Solutions Data Services historically. A Cedro free-trial path was explored and explicitly reverted because a temporary trial cannot satisfy the sustainable zero-additional-cost constraint.

ADR-0025 then selected Rico-supplied MetaTrader 5. The MT5 boundary developed under that decision remains technically useful, but the concrete Rico provisioning path did not reach a qualifying runtime session.

ADR-0026 selects **XP-supplied MetaTrader 5** as the active provider for qualification. ADR-0025 remains immutable historical evidence; the provider change does not rewrite the Observer contract.

```text
BTG_DATA_SERVICES = HISTORICAL_REFERENCE_IMPLEMENTATION
CEDRO_FREE_TRIAL = REJECTED_AS_CANONICAL_LONG_TERM_PROVIDER
RICO_MT5 = HISTORICAL_SUPERSEDED_PROVIDER_PATH
XP_MT5 = ACCEPTED_FOR_QUALIFICATION
XP_MT5_RUNTIME_QUALIFICATION = RUNTIME_EVIDENCE_PASS_FINAL_TREE_GATES_PENDING
```

Runtime qualification is tracked in Issue #54. The sanitized successful-session record is `docs/program/workstreams/S1-XP-MT5-RUNTIME-EVIDENCE-2026-09-16.md`.

## XP/MT5 read-only boundary

```text
XP / MT5 server
-> MetaTrader 5 terminal
   -> Investor / read-only authorization
   -> custom MQL5 indicator
      -> ProviderId = xp-mt5
      -> passive WIN symbol discovery
      -> passive tick observations
      -> finalized candle observations
      -> bounded append-only FILE_COMMON transport
         -> trusted Python bridge/discovery readers
            -> local read-only evidence harness
               -> canonical technical evidence / provenance / health / latency
```

The bridge is one-way. Trusted Python does not import the dual-use `MetaTrader5` package and receives no terminal-control, account, position or order interface.

The implementation still contains legacy Rico-named files/classes (`rico_mt5_bridge.py`, `RicoMt5BridgeReader`, `RicoMarketDataBridge.mq5`, `scripts/rico_mt5_first_lab_capture.py`). These are compatibility names only. Provider provenance is `xp-mt5` under ADR-0026.

## XP entitlement and read-only evidence

Non-secret operator evidence established the concrete XP MetaTrader 5 entitlement used by this work as R$0 additional recurring platform/data cost, with no minimum real-money operation requirement identified for retaining the entitlement. Investor/read-only authorization was established locally without exposing credentials or using an order attempt as a test.

```text
XP_ZERO_ADDITIONAL_RECURRING_COST = PASS
XP_MINIMUM_REAL_MONEY_OPERATION_REQUIRED = NO
XP_INVESTOR_READ_ONLY = PASS_LOCAL
CREDENTIAL_DISCLOSURE = NO
ORDER_TEST_FOR_READ_ONLY = NO
```

Raw account/interface screenshots remain outside Git.

## Successful realtime qualification session

On 16/09/2026, the controlled passive launcher completed `s1-xp-capture-a12` against `WINV26` / M1 on exact code revision `e622658922ff38e49e1112a48d91eecb2d43a522`, with a clean worktree at capture time.

The exact reviewed `XPMarketDataBridge.mq5` source had been recompiled with `0 errors, 0 warnings` after the `FILE_COMMON` existence-check correction. The qualifying session then completed normally and returned the bridge to `IDLE`.

Sanitized transport inventory:

```text
DISCOVERY_RECORDS = 18
TICK_RECORDS = 8005
FINAL_CANDLE_RECORDS_IN_RAW_CHANNEL = 2
DISCOVERY_BYTES = 2011
TICK_BYTES = 1517016
CANDLE_BYTES = 538
```

The harness success condition validates complete discovery with exact `WINV26` presence, provider/symbol consistency, contiguous tick/candle sequences from one, at least two realtime ticks, at least one explicitly finalized candle, local monotonic latency evidence and a continuously `READY` health path. Raw files and the full evidence-session directory remain outside Git; their hashes are recorded in `S1-XP-MT5-RUNTIME-EVIDENCE-2026-09-16.md` and Issue #54.

This successful runtime session supplies the previously missing real-provider evidence for the runtime portions of AC-01/02/05/07/08/09/12/13. It does not by itself satisfy the final-tree CI/NEG-CAP or official Security Diff Scan gates.

## Negative capabilities

```text
TRUSTED_PYTHON_IMPORTS_METATRADER5 = NO
MT5_MASTER_PASSWORD_IN_PROJECT = NO
MT5_MASTER_PASSWORD_IN_CHAT = NO
MT5_MASTER_PASSWORD_IN_SECRET_STORE = NO
MT5_INVESTOR_PASSWORD_ONLY = YES
MQL5_BRIDGE_PROGRAM_TYPE = CUSTOM_INDICATOR
PROGRAMMATIC_MARKET_WATCH_MUTATION = NO
PYTHON_ORDER_API = ABSENT
BROKER_ACCOUNT_API = ABSENT
ORDER_SUBMISSION = IMPOSSIBLE
ORDER_MODIFICATION = IMPOSSIBLE
ORDER_CANCELLATION = IMPOSSIBLE
PAPER_PATH = ABSENT
LIVE_TRADING_PATH = ABSENT
REAL_MONEY_AUTHORITY = ABSENT
ECONOMIC_COMMITMENT = IMPOSSIBLE
```

No order attempt is permitted as a test of Investor/read-only status.

## Runtime qualification runbook and harness

Active runbook:

```text
docs/program/workstreams/S1-XP-MT5-FIRST-RUNTIME-QUALIFICATION.md
```

Successful sanitized evidence record:

```text
docs/program/workstreams/S1-XP-MT5-RUNTIME-EVIDENCE-2026-09-16.md
```

Active file-only harness, retained under its historical filename:

```text
scripts/rico_mt5_first_lab_capture.py
```

The harness consumes only append-only discovery/tick/candle files. It records RunId, code revision, config hash, provider CaptureContext, preserved raw prefixes, local monotonic ingress-to-validated-availability evidence and health/staleness samples. It has no MT5 control API, account API, order API, credential input or economic authority.

## Runtime qualification gate

XP can be promoted to `SPRINT1_PROVIDER_QUALIFIED = YES` only after reviewed evidence demonstrates all of the following:

1. concrete XP MT5/platform/feed entitlement used by the qualification is R$0 additional recurring cost — **PASS**;
2. retaining that entitlement requires no minimum real-money operation, RLP, brokerage spend or equivalent — **PASS**;
3. Investor/read-only authorization is established without credential exposure or order testing — **PASS**;
4. passive discovery is complete and the exact current WIN symbol is explicitly confirmed point-in-time — **PASS (`WINV26`, a12)**;
5. realtime WIN observations satisfy AC-05/AC-07, including genuine tick flow and at least one genuinely finalized candle — **PASS_RUNTIME**;
6. bridge remains a custom MQL5 indicator only — **PASS**;
7. trusted Python remains free of `MetaTrader5`, master password and account/order APIs — **PASS_CURRENT_TREE**;
8. raw/passive evidence, provenance, heartbeat/staleness and local latency evidence are preserved/reviewed within their actual clock scope — **PASS_RUNTIME**;
9. exact-final-tree CI and negative-capability verification are green after evidence reconciliation — **PENDING**;
10. the official Security Diff Scan executes on the exact final Sprint 1 tree — **PENDING**.

Failure of either remaining item blocks XP qualification and Sprint 1 acceptance; it does not relax the Sprint 1 contract.

## Evidence state

```text
FIXTURE_AND_OFFLINE_ENGINEERING_EVIDENCE = AVAILABLE
XP_PRELIMINARY_AUTH_DISCOVERY_COMPILE = AVAILABLE_NONQUALIFYING
XP_REALTIME_QUALIFYING_CAPTURE = PASS_RUNTIME
XP_REALTIME_CAPTURE_SCOPE = s1-xp-capture-a12
REALTIME_AC_05_AC_07 = SATISFIED_RUNTIME_EVIDENCE
RUNTIME_PROVENANCE_HEARTBEAT_LATENCY_EVIDENCE = SATISFIED_RUNTIME_EVIDENCE
EXACT_FINAL_TREE_CI_NEG_CAP = PENDING
OFFICIAL_SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_PROVIDER_QUALIFIED = NO_PENDING_FINAL_TREE_GATES
SPRINT1_ACCEPTANCE = NO
```

Historical BTG/Rico fixture/provider evidence remains auditable and is not relabeled as proof of the XP realtime feed.

## Remaining Sprint 1 sequence

```text
1. Complete this post-runtime documentation/evidence reconciliation without modifying frozen Foundation artifacts.
2. Run exact-final-tree CI, typing, lint, Foundation, boundary and NEG-CAP checks on the reconciled tree.
3. Execute the official Security Diff Scan on that exact final Sprint 1 tree/diff.
4. Reconcile any findings without weakening 0F-E or the read-only boundary.
5. Adjudicate all 11 Sprint 1 exit criteria conjunctively.
6. Promote to Sprint 2 only after formal Sprint 1 PASS.
```

No step above authorizes execution, Paper, Risk, Strategy, ML operational wiring or real money.