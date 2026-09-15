# Program Execution — BTG AI Trader

## Current remote checkpoint

```text
AUTHORITATIVE_STATE = GITHUB_REMOTE
REPOSITORY = paulobmcosta-creator/btg-ai-trader
SPRINT_BRANCH = sprint/1-market-observer
RECONCILIATION_BASELINE = bd9c9ce96cf0b0e44d609f16fc4d613efd1d3647
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
REAL_QUALIFYING_PROVIDER_SESSION = NOT_EXECUTED
SPRINT1_PROVIDER_QUALIFIED = NO
SPRINT1_ACCEPTANCE = NOT_GRANTED
PROMOTION_TO_SPRINT_2 = NO
SECURITY_DIFF_SCAN = NOT_EXECUTED

MT5_OFFLINE_TICK_BRIDGE = INTEGRATED
MT5_OFFLINE_FINAL_CANDLE_BRIDGE = INTEGRATED
MT5_OFFLINE_SYMBOL_DISCOVERY = INTEGRATED
XP_MT5_RUNTIME_RUNBOOK = INTEGRATED
MT5_RUNTIME_EVIDENCE_HARNESS = INTEGRATED_OFFLINE_TESTED

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

ADR-0026 now selects **XP-supplied MetaTrader 5** as the active provider for qualification. ADR-0025 remains immutable historical evidence; the provider change does not rewrite the Observer contract.

```text
BTG_DATA_SERVICES = HISTORICAL_REFERENCE_IMPLEMENTATION
CEDRO_FREE_TRIAL = REJECTED_AS_CANONICAL_LONG_TERM_PROVIDER
RICO_MT5 = HISTORICAL_SUPERSEDED_PROVIDER_PATH
XP_MT5 = ACCEPTED_FOR_QUALIFICATION
XP_MT5_RUNTIME_QUALIFICATION = OPEN
```

Runtime qualification is tracked in Issue #54.

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

## Preliminary XP evidence — not qualification

On 14/09/2026 the owner established a non-financial preliminary session:

```text
XP_MT5_AUTHENTICATION = OBSERVED
XP_INVESTOR_READ_ONLY = OBSERVED_LOCALLY
PRE_RECONCILIATION_MQL5_COMPILATION = 0_ERRORS_0_WARNINGS
XP_WIN_DISCOVERY = COMPLETE_PRELIMINARY
XP_SERVER_SYMBOL_TOTAL = 57414
XP_WIN_PREFIX_MATCHES = 16
XP_WIN_EMITTED_SYMBOLS = 16
XP_WIN_PREFIX_ERRORS = 0
XP_WIN_ENUMERATION_ERRORS = 0
PRELIMINARY_TARGET = WINV26
```

This supports the provider migration but does not satisfy realtime AC-05/AC-07. The raw discovery file is not committed. `WINV26` must be re-confirmed and preserved point-in-time in the qualifying-session evidence.

The post-reconciliation indicator must be compiled again from the exact reviewed revision because the provider provenance changes from `rico-mt5` to `xp-mt5`.

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

Active file-only harness, retained under its historical filename:

```text
scripts/rico_mt5_first_lab_capture.py
```

The harness consumes only append-only discovery/tick/candle files. It records RunId, code revision, config hash, provider CaptureContext, preserved raw prefixes, local monotonic ingress-to-validated-availability evidence and health/staleness samples. It has no MT5 control API, account API, order API, credential input or economic authority.

## Runtime qualification gate

XP can be promoted to `SPRINT1_PROVIDER_QUALIFIED = YES` only after reviewed evidence demonstrates all of the following:

1. concrete XP MT5/platform/feed entitlement used by the qualification is R$0 additional recurring cost;
2. retaining that entitlement requires no minimum real-money operation, RLP, brokerage spend or equivalent;
3. Investor/read-only authorization is established without credential exposure or order testing;
4. passive discovery is complete and the exact current WIN symbol is explicitly confirmed point-in-time;
5. realtime WIN observations satisfy AC-05/AC-07, including genuine tick flow and at least one genuinely finalized candle;
6. bridge remains a custom MQL5 indicator only;
7. trusted Python remains free of `MetaTrader5`, master password and account/order APIs;
8. raw/passive evidence, provenance, heartbeat/staleness and local latency evidence are preserved/reviewed within their actual clock scope;
9. exact-final-tree CI and negative-capability verification are green after evidence reconciliation;
10. the official Security Diff Scan executes on the exact final Sprint 1 tree.

Failure of any item rejects XP qualification under current constraints; it does not relax the Sprint 1 contract.

## Evidence state

```text
FIXTURE_AND_OFFLINE_ENGINEERING_EVIDENCE = AVAILABLE
XP_PRELIMINARY_AUTH_DISCOVERY_COMPILE = AVAILABLE_NONQUALIFYING
XP_OFFLINE_TICK_AND_CANDLE_TRANSPORT = INTEGRATED
XP_OFFLINE_SYMBOL_DISCOVERY = INTEGRATED
XP_OFFLINE_EVIDENCE_HARNESS = INTEGRATED_AND_TESTED
REAL_XP_MT5_QUALIFYING_EVIDENCE = NOT_EXECUTED
REALTIME_AC_05_AC_07 = NOT_YET_SATISFIED_BY_XP
RUNTIME_PROVENANCE_HEARTBEAT_LATENCY_EVIDENCE = NOT_YET_SATISFIED_BY_XP
OFFICIAL_SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_ACCEPTANCE = NO
```

Historical BTG/Rico fixture/provider evidence remains auditable and is not relabeled as proof of the XP realtime feed.

## Remaining Sprint 1 sequence

```text
1. Confirm concrete XP R$0 platform/feed entitlement and no minimum real-money operation requirement.
2. Reconfirm Investor/read-only locally without exposing credentials or attempting an order.
3. Compile the exact post-reconciliation custom indicator: 0 errors, 0 warnings.
4. Execute fresh XP WIN discovery and explicitly re-confirm WINV26 (or the then-current contract) point-in-time.
5. Create a fresh qualifying namespace with empty/absent transport files and a non-repository evidence root.
6. Start the file-only harness before attaching the indicator.
7. Capture realtime ticks and at least one genuine finalized M1 candle for the exact confirmed symbol.
8. Preserve/review raw evidence, RunId, config hash, provenance, heartbeat/staleness and local monotonic latency.
9. Reconcile evidence against AC/RQM/XC without upgrading unsupported claims.
10. Re-run exact-final-tree CI and NEG-CAP checks.
11. Execute official Security Diff Scan on the exact final tree.
12. Adjudicate all 11 exit criteria conjunctively and promote only after formal PASS.
```

No step above authorizes execution, Paper, Risk, Strategy, ML operational wiring or real money.