# Sprint 1 — Final Acceptance Gate Checkpoint

## Gate purpose

This living checkpoint records whether the current Sprint 1 state may be declared a formal PASS under immutable 0F-E. It does not rewrite 0F-B, 0F-E or 0F-F.

## Current state

```text
FOUNDATION = FORMALLY_CLOSED
SPRINT_1 = OPEN
RECONCILIATION_BASELINE = bd9c9ce96cf0b0e44d609f16fc4d613efd1d3647
CURRENT_PROVIDER_DECISION = ADR-0026
CURRENT_PROVIDER_SELECTION = XP_SUPPLIED_MT5
PROVIDER_ID = xp-mt5
ZERO_ADDITIONAL_RECURRING_COST = HARD_CONSTRAINT
REALTIME_REQUIREMENT = PRESERVED
MT5_TICK_BRIDGE = INTEGRATED
MT5_FINAL_CANDLE_BRIDGE = INTEGRATED
MT5_SYMBOL_DISCOVERY = INTEGRATED
XP_MT5_RUNTIME_RUNBOOK = INTEGRATED
MT5_LOCAL_EVIDENCE_HARNESS = INTEGRATED_OFFLINE_TESTED
READ_ONLY_BY_CONSTRUCTION_CURRENT_SCOPE = SATISFIED
STRUCTURAL_ESCALATION_CURRENT_SCOPE = SATISFIED
TRADING_CAPABILITY = ABSENT
REAL_MONEY_PATH = ABSENT
XP_PRELIMINARY_SESSION = EXECUTED_NONQUALIFYING
REAL_QUALIFYING_PROVIDER_SESSION = NOT_EXECUTED
SPRINT1_PROVIDER_QUALIFIED = NO
SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_ACCEPTANCE = NO
```

## Evidence adjudication

| Gate area | Result | Basis |
|---|---|---|
| Foundation integrity | PASS | Frozen Foundation artifacts remain unchanged |
| Functional Observer core | PASS_CURRENT_SCOPE | Passive Observer core integrated |
| 41 RQMs | CONDITIONAL | Existing direct/fixture evidence remains; RQM-018 and RQM-036 still await official Security Diff Scan |
| NEG-CAP-01..10 | PASS_CURRENT_SCOPE | Provider migration introduces no strategy/order/execution/economic authority |
| Current provider decision | PASS_DECISION | ADR-0026 selects XP-supplied MT5 for qualification; selection is not qualification |
| Historical BTG provider path | HISTORICAL_ONLY | ADR-0023 remains auditable reference history |
| Historical Rico provider path | HISTORICAL_SUPERSEDED | ADR-0025 and Rico-named implementation lineage preserved; active qualification moves to XP |
| MT5 tick bridge | PASS_IMPLEMENTATION | Passive append-only FILE_COMMON tick transport integrated/offline tested |
| MT5 finalized-candle bridge | PASS_IMPLEMENTATION | Genuine finalized-candle transport integrated/offline tested |
| MT5 WIN discovery | PASS_IMPLEMENTATION | Passive candidate enumeration; no automatic contract selection/mapping |
| XP preliminary authentication | PRELIMINARY_PASS | XP login + Investor/read-only observed locally; must remain credential-free |
| XP preliminary discovery | PRELIMINARY_PASS | Complete nonqualifying snapshot: 57.414 server symbols, 16 WIN candidates, zero discovery errors, WINV26 present |
| Post-reconciliation MQL5 compile | FAIL_OPEN | Revised provider-provenance source must be compiled again from exact reviewed SHA |
| Zero-cost concrete entitlement | FAIL_OPEN | Account-level R$0/no-minimum-real-trade condition still requires preserved evidence |
| AC-05 real market data | FAIL_OPEN | No controlled qualifying realtime XP session executed |
| AC-07 real ticks/candles | FAIL_OPEN | No qualifying real tick/final-candle capture adjudicated |
| Heartbeat/staleness/latency | FAIL_OPEN_REAL_SCOPE | Offline instrumentation exists; real-feed evidence/thresholds remain unadjudicated |
| Official Security Diff Scan | FAIL_OPEN | Not executed; other checks cannot be relabeled as the official scan |

## Integrated XP/MT5 laboratory policy

```text
PROVIDER = XP-supplied MetaTrader 5
PROVIDER_ID = xp-mt5
INSTRUMENT_FAMILY = WIN
PRELIMINARY_TARGET = WINV26
CONCRETE_CONTRACT = EXPLICIT_POINT_IN_TIME_PROVIDER_SYMBOL
AUTHORIZATION = INVESTOR_READ_ONLY_ONLY
MQL5_PROGRAM_TYPE = CUSTOM_INDICATOR
TRANSPORT = APPEND_ONLY_FILE_COMMON
PYTHON_METATRADER5_IMPORT = FORBIDDEN
PROGRAMMATIC_MARKET_WATCH_MUTATION = FORBIDDEN
AUTO_CONTRACT_SELECTION = FORBIDDEN
AUTO_ROLLOVER = FORBIDDEN
AUTO_FALLBACK = FORBIDDEN
REAL_MONEY_ORDER_TEST = FORBIDDEN
RAW_PUBLIC_ARTIFACT = NO
```

`WINV26` is a preliminary mapping and must be explicitly re-confirmed/preserved at qualification time. Passive discovery must preserve all server candidates without ranking. Ambiguous/incomplete/malformed evidence fails closed.

The custom indicator now emits explicit provider identity `xp-mt5`. Physical Rico-named artifact/class/script names are temporarily retained as compatibility names and must not be confused with runtime provenance.

## Historical decisions and superseded paths

BTG Data Services and the Rico/MT5 provider selection remain auditable history. No historical evidence is rewritten into XP evidence.

The earlier Rico runtime runbook remains historical. The active procedure is:

```text
docs/program/workstreams/S1-XP-MT5-FIRST-RUNTIME-QUALIFICATION.md
```

The evidence harness remains file-only under its compatibility filename:

```text
scripts/rico_mt5_first_lab_capture.py
```

## Current adjudication

```text
SPRINT1_INTERNAL_OBSERVER_CORE = COMPLETE_CURRENT_SCOPE
SPRINT1_CURRENT_PROVIDER_DECISION = COMPLETE
SPRINT1_XP_OFFLINE_PROVIDER_BOUNDARY = INTEGRATED
SPRINT1_XP_PRELIMINARY_AUTH_DISCOVERY = AVAILABLE_NONQUALIFYING
SPRINT1_MT5_LOCAL_EVIDENCE_HARNESS = INTEGRATED_OFFLINE_TESTED
SPRINT1_REAL_PROVIDER_QUALIFICATION = OPEN
SPRINT1_REAL_CAPTURE_GATE = OPEN
SPRINT1_SECURITY_GATE = OPEN
SPRINT1_ACCEPTANCE = NO
PROMOTION_TO_SPRINT_2 = NO
```

## Mandatory remaining sequence

1. Pass CI/typing/lint/Foundation/boundary/NEG-CAP on the provider-reconciliation PR head before integration.
2. After integration, verify the concrete XP MT5/platform/feed entitlement at R$0 additional recurring cost and no minimum real-money operation requirement.
3. Re-establish/reconfirm Investor/read-only locally without exposing credentials or attempting an order.
4. Compile the exact integrated custom indicator with `0 errors, 0 warnings`.
5. Execute fresh passive WIN discovery and explicitly re-confirm the exact current provider symbol; no automatic front-contract selection, rollover or fallback.
6. Start the local file-only harness before attaching the indicator in a fresh qualifying namespace.
7. Capture genuine realtime tick flow and at least one genuinely finalized candle for the exact confirmed symbol.
8. Review provider identity `xp-mt5`, continuity, provenance, RunId/config hash, heartbeat/staleness and local monotonic latency evidence without overstating scope.
9. Reconcile real-provider evidence into AC/RQM/XC without upgrading unsupported claims.
10. Re-run full exact-final-tree CI/boundary/NEG-CAP after runtime evidence/documentation reconciliation.
11. Execute the official Security Diff Scan on the exact final Sprint 1 diff/tree.
12. Adjudicate all 11 exit criteria conjunctively.
13. Promote to Sprint 2 only after formal Sprint 1 PASS.

## Explicit prohibitions remain in force

No open, implemented or passed gate authorizes Strategy, ML production wiring, Paper execution, Risk authorization, broker order APIs, trading credentials, financial-ledger mutation, economic commitment or real-money operation.