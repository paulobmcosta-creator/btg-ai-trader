# Program Execution — BTG AI Trader

## Current remote checkpoint

```text
AUTHORITATIVE_STATE = GITHUB_REMOTE
REPOSITORY = paulobmcosta-creator/btg-ai-trader
SPRINT_BRANCH = sprint/1-market-observer
INTEGRATED_BASELINE_BEFORE_THIS_WORK = fd53f221b09902ec2e79df758bf35e8a04f86267
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

The Sprint 1 target boundary is:

```text
Rico / MT5 server
-> MetaTrader 5 terminal
   -> Investor / read-only authorization
   -> custom MQL5 indicator
      -> passive market observations
      -> bounded append-only FILE_COMMON transport
         -> trusted Python bridge reader
            -> RawFrame / later admission and evidence processing
```

The bridge is deliberately one-way. The trusted Python runtime does not import the dual-use `MetaTrader5` package and receives no terminal-control, account, position or order interface.

The offline bridge may be implemented and tested before a real session, but fixture/file tests are not realtime provider evidence. Runtime feed fidelity remains unknown until qualification.

## Negative capabilities for the selected boundary

```text
TRUSTED_PYTHON_IMPORTS_METATRADER5 = NO
MT5_MASTER_PASSWORD_IN_PROJECT = NO
MT5_MASTER_PASSWORD_IN_CHAT = NO
MT5_MASTER_PASSWORD_IN_SECRET_STORE = NO
MT5_INVESTOR_PASSWORD_ONLY = YES
MQL5_BRIDGE_PROGRAM_TYPE = CUSTOM_INDICATOR
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

The BTG secure real-lab workflow was appropriate while BTG Data Services was the active qualification provider. Once ADR-0025 selected Rico/MT5 under the zero-cost constraint, keeping that workflow executable would create two conflicting operational paths. It is therefore removed from the active tree while its complete implementation remains preserved in Git history.

The BTG adapter, its unit tests and its non-authenticated provider-surface verification may remain as historical technical reference; they do not authorize or schedule a BTG real session.

## Runtime qualification gate

Rico can be promoted to `SPRINT1_PROVIDER_QUALIFIED = YES` only after evidence demonstrates all of the following:

1. MT5 activation in the concrete Rico account with no additional recurring platform/market-data charge under the qualified account state.
2. Discovery of the current WIN contract and exact provider symbol.
3. Realtime WIN observations sufficient for AC-05 and AC-07.
4. Investor/read-only authorization with trading demonstrably disabled.
5. Bridge execution as a custom MQL5 indicator only.
6. Trusted Python path without `MetaTrader5`, master password or account/order APIs.
7. Required timestamp, provenance, heartbeat and latency evidence.
8. No minimum real-money operation required to retain the entitlement used by the qualification.

Failure of any item rejects the Rico qualification under the current constraints; it does not relax the Sprint 1 contract.

## Evidence state

```text
FIXTURE_AND_OFFLINE_ENGINEERING_EVIDENCE = AVAILABLE
REAL_RICO_MT5_EVIDENCE = NOT_EXECUTED
REALTIME_AC_05_AC_07 = NOT_YET_SATISFIED_BY_RICO
OFFICIAL_SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_ACCEPTANCE = NO
```

Historical BTG fixture/provider evidence remains auditable but is not relabeled as proof of the Rico runtime feed.

## Remaining Sprint 1 sequence

```text
1. Complete and validate the offline Rico/MT5 read-only bridge and negative-capability tests.
2. Confirm MT5 R$0 activation in the user's concrete Rico account without a minimum-trade condition.
3. Install/authenticate MT5 using Investor/read-only authorization only and identify the current WIN symbol.
4. Execute one controlled realtime observation session with the custom indicator bridge.
5. Preserve raw/passive evidence, timestamps, provenance, heartbeat and latency without exposing credentials.
6. Reconcile the real-provider evidence against AC-01/02/03/05/07 and the RQM matrix.
7. Re-run exact-final-tree CI and negative-capability verification.
8. Execute the official Security Diff Scan on the exact final Sprint 1 tree when the official action is available.
9. Adjudicate all Sprint 1 exit criteria conjunctively.
10. Promote to Sprint 2 only after formal Sprint 1 PASS.
```

No step above authorizes financial execution, order APIs, master/trading credentials, Paper execution, Risk authorization or real money.
