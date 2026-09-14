# Program Execution — BTG AI Trader

## Current remote checkpoint

```text
AUTHORITATIVE_STATE = GITHUB_REMOTE
REPOSITORY = paulobmcosta-creator/btg-ai-trader
SPRINT_BRANCH = sprint/1-market-observer
CURRENT_INTEGRATED_BASELINE = e3217863462aabea1d6a8851d6a0c6e04781fada
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
SPRINT_1_LIFECYCLE = OPEN
S1_A_AUTHORIZED = YES

PROVIDER_DECISION = ADR-0025
PROVIDER_SELECTION = RICO_SUPPLIED_MT5
PROVIDER_SELECTION_STATUS = ACCEPTED_FOR_QUALIFICATION
ZERO_ADDITIONAL_RECURRING_COST = HARD_CONSTRAINT
REALTIME_REQUIREMENT = PRESERVED
REAL_PROVIDER_SESSION = NOT_EXECUTED
SPRINT1_PROVIDER_QUALIFIED = NO
SPRINT1_ACCEPTANCE = NOT_GRANTED
PROMOTION_TO_SPRINT_2 = NO
SECURITY_DIFF_SCAN = NOT_EXECUTED

RICO_MT5_OFFLINE_TICK_BRIDGE = IMPLEMENTED
RICO_MT5_OFFLINE_FINAL_CANDLE_BRIDGE = IMPLEMENTED
RICO_MT5_OFFLINE_SYMBOL_DISCOVERY = IMPLEMENTED
RICO_MT5_RUNTIME_RUNBOOK = docs/program/workstreams/S1-RICO-MT5-FIRST-RUNTIME-QUALIFICATION.md
RICO_MT5_RUNTIME_EVIDENCE_HARNESS = NOT_YET_MATERIALIZED

REAL_MONEY = NO
LIVE_TRADING = NO
PAPER_TRADING = NO
TRADING_CREDENTIALS = NO
TRADING_CAPABILITY = ABSENT
```

Historical execution detail remains in Git history and prior PRs. This living file records only the state required to resume safely.

## Preserved authorities

The frozen Foundation artifacts remain unchanged. The Sprint 1 contract remains passive Market Observer only. Formal causal replay belongs to Sprint 2 and deterministic economic backtesting belongs to Sprint 3.

The negative capability baseline remains authoritative: no Strategy operational path, TradeIntent operational path, RiskAuthorization Engine, OrderIntent, OrderPlan, ExecutionOrder, Paper execution, broker execution, financial ledger mutation or real-money authority may appear in Sprint 1.

## Provider history and current authority

ADR-0023 selected BTG Solutions Data Services historically. Its narrow read-only adapter and tests remain useful as an integrated reference implementation, but the owner subsequently established zero additional recurring cost as a hard constraint. BTG Data Services is therefore not the active qualification provider.

A Cedro free-trial path was explored, merged historically and explicitly reverted because a time-limited trial cannot sustain the program after development.

ADR-0025 now selects **Rico-supplied MetaTrader 5 market data for qualification**. Selection is not runtime qualification and does not itself satisfy any realtime acceptance criterion.

```text
BTG_DATA_SERVICES = HISTORICAL_REFERENCE_IMPLEMENTATION
CEDRO_FREE_TRIAL = REJECTED_AS_CANONICAL_LONG_TERM_PROVIDER
RICO_MT5 = ACCEPTED_FOR_QUALIFICATION
RICO_MT5_RUNTIME_EVIDENCE = ABSENT
```

Runtime qualification is tracked in Issue #45.

## Rico/MT5 read-only boundary

The integrated Sprint 1 boundary is:

```text
Rico / MT5 server
-> MetaTrader 5 terminal
   -> Investor / read-only authorization
   -> custom MQL5 indicator
      -> passive WIN symbol discovery
      -> passive tick observations
      -> finalized candle observations
      -> bounded append-only FILE_COMMON transport
         -> trusted Python bridge/discovery readers
            -> later admission and technical-evidence processing
```

The bridge is deliberately one-way. The trusted Python runtime does not import the dual-use `MetaTrader5` package and receives no terminal-control, account, position or order interface.

The integrated offline surface now covers raw ticks, genuinely finalized candles and passive server-symbol discovery. Symbol discovery preserves all candidates and does not rank, select or silently create a canonical instrument mapping. Fixture/file tests are not realtime provider evidence; runtime feed fidelity remains unknown until qualification.

## Negative capabilities for the selected boundary

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

## Historical BTG active-runner treatment

The BTG secure real-lab workflow was appropriate while BTG Data Services was the active qualification provider. Once ADR-0025 selected Rico/MT5 under the zero-cost constraint, keeping that workflow executable would create two conflicting operational paths. It was therefore removed from the active tree while its complete implementation remains preserved in Git history.

The BTG adapter, its unit tests and its non-authenticated provider-surface verification remain historical technical reference only; they do not authorize or schedule a BTG real session.

## Runtime qualification runbook

The controlled operator procedure for the first Rico/MT5 session is materialized at:

```text
docs/program/workstreams/S1-RICO-MT5-FIRST-RUNTIME-QUALIFICATION.md
```

The runbook requires a concrete zero-cost entitlement check, Investor/read-only authorization, unique append-only session namespaces, passive WIN discovery, explicit point-in-time symbol mapping and a separate qualifying realtime tick/candle phase. It prohibits using an order attempt as a read-only test.

The runbook itself is not runtime evidence and does not change Issue #45 acceptance state.

## Runtime evidence instrumentation gap

The offline provider boundary is implemented, but a Rico-specific controlled evidence harness has not yet been materialized. Raw NDJSON files alone do not automatically establish all required provenance, heartbeat/staleness and observable-latency evidence.

Therefore:

```text
RICO_RAW_TRANSPORT = READY_FOR_CONTROLLED_RUNTIME_USE
RICO_SYMBOL_DISCOVERY_PARSER = READY_FOR_CONTROLLED_RUNTIME_USE
RICO_RUNTIME_EVIDENCE_HARNESS = OPEN_WORK
RICO_REAL_SESSION = BLOCKED_FROM_FINAL_QUALIFICATION_UNTIL_EVIDENCE_PATH_IS_READY
```

A real observation may be technically possible before that harness exists, but it must not be treated as sufficient Sprint 1 qualification evidence. The preferred sequence is to materialize the read-only evidence path first so the first controlled session is not needlessly repeated.

## Runtime qualification gate

Rico can be promoted to `SPRINT1_PROVIDER_QUALIFIED = YES` only after evidence demonstrates all of the following:

1. MT5 activation in the concrete Rico account with no additional recurring platform/market-data charge under the qualified account state.
2. Discovery of the current WIN contract and exact provider symbol.
3. Realtime WIN observations sufficient for AC-05 and AC-07.
4. Investor/read-only authorization with trading disabled, without introducing an order test.
5. Bridge execution as a custom MQL5 indicator only.
6. Trusted Python path without `MetaTrader5`, master password or account/order APIs.
7. Required timestamp, provenance, heartbeat and latency evidence.
8. No minimum real-money operation required to retain the entitlement used by the qualification.

Failure of any item rejects the Rico qualification under the current constraints; it does not relax the Sprint 1 contract.

## Evidence state

```text
FIXTURE_AND_OFFLINE_ENGINEERING_EVIDENCE = AVAILABLE
RICO_OFFLINE_TICK_AND_CANDLE_TRANSPORT = IMPLEMENTED
RICO_OFFLINE_SYMBOL_DISCOVERY = IMPLEMENTED
REAL_RICO_MT5_EVIDENCE = NOT_EXECUTED
REALTIME_AC_05_AC_07 = NOT_YET_SATISFIED_BY_RICO
RUNTIME_PROVENANCE_HEARTBEAT_LATENCY_EVIDENCE = NOT_YET_SATISFIED_BY_RICO
OFFICIAL_SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_ACCEPTANCE = NO
```

Historical BTG fixture/provider evidence remains auditable but is not relabeled as proof of the Rico runtime feed.

## Remaining Sprint 1 sequence

```text
1. Materialize and validate a Rico-specific local read-only evidence harness that consumes only the append-only discovery/tick/candle files and existing Observer evidence primitives.
2. Confirm MT5 R$0 activation in the user's concrete Rico account and confirm that the entitlement requires no minimum real-money operation.
3. Establish MT5 Investor/read-only authorization locally; never expose master/investor credentials to Git, shell arguments or chat.
4. Execute passive WIN discovery and explicitly resolve the concrete current provider symbol without automatic rollover/selection.
5. Execute one controlled realtime observation session with the custom indicator bridge for the exact confirmed symbol.
6. Preserve and reconcile raw/passive evidence, timestamps, provenance, heartbeat/staleness and latency without exposing credentials.
7. Reconcile the real-provider evidence against AC-01/02/03/05/07 and the RQM matrix.
8. Re-run exact-final-tree CI and negative-capability verification.
9. Execute the official Security Diff Scan on the exact final Sprint 1 tree when the official action is available.
10. Adjudicate all Sprint 1 exit criteria conjunctively.
11. Promote to Sprint 2 only after formal Sprint 1 PASS.
```

No step above authorizes financial execution, order APIs, master/trading credentials, Paper execution, Risk authorization or real money.
