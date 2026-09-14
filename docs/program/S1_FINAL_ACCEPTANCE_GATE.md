# Sprint 1 — Final Acceptance Gate Checkpoint

## Gate purpose

This living checkpoint records whether the current Sprint 1 baseline may be declared a formal PASS under immutable 0F-E. It does not rewrite 0F-B, 0F-E or 0F-F.

## Current state

```text
FOUNDATION = FORMALLY_CLOSED
SPRINT_1 = OPEN
INTEGRATED_IMPLEMENTATION_BASELINE = ac3d1083f483bb85220f7637d21b4d5a4e34b11d
CURRENT_PROVIDER_DECISION = ADR-0025
CURRENT_PROVIDER_SELECTION = RICO_SUPPLIED_MT5
ZERO_ADDITIONAL_RECURRING_COST = HARD_CONSTRAINT
REALTIME_REQUIREMENT = PRESERVED
RICO_MT5_TICK_BRIDGE = INTEGRATED
RICO_MT5_FINAL_CANDLE_BRIDGE = INTEGRATED
RICO_MT5_SYMBOL_DISCOVERY = INTEGRATED
RICO_MT5_RUNTIME_RUNBOOK = INTEGRATED
RICO_MT5_LOCAL_EVIDENCE_HARNESS = INTEGRATED_OFFLINE_TESTED
READ_ONLY_BY_CONSTRUCTION_CURRENT_TREE = SATISFIED
STRUCTURAL_ESCALATION_CURRENT_TREE = SATISFIED
TRADING_CAPABILITY = ABSENT
REAL_MONEY_PATH = ABSENT
REAL_PROVIDER_SESSION = NOT_EXECUTED
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
| NEG-CAP-01..10 | PASS_CURRENT_TREE | Structural/runtime negative-capability evidence remains green after Rico harness merge |
| Current provider decision | PASS_DECISION | ADR-0025 selects Rico-supplied MT5 for qualification under the zero-additional-cost constraint |
| Historical BTG provider path | HISTORICAL_ONLY | ADR-0023/BTG Data Services remain auditable reference history, not the active qualification path |
| Cedro free-trial path | REJECTED_CANONICAL | Historical trial path was explicitly reverted because it is not sustainable at R$0 |
| Rico tick bridge | PASS_IMPLEMENTATION | Passive append-only FILE_COMMON tick transport integrated and offline tested |
| Rico finalized-candle bridge | PASS_IMPLEMENTATION | Genuine finalized-candle transport integrated and offline tested |
| Rico WIN discovery | PASS_IMPLEMENTATION | Passive candidate enumeration integrated; no automatic contract selection or mapping |
| Rico local evidence harness | PASS_IMPLEMENTATION | Local file-only harness integrated after exact-head CI/upstream PASS and post-merge CI PASS |
| Read-only authentication | FAIL_OPEN | Concrete Investor/read-only account session has not been executed or evidenced |
| Zero-cost entitlement | FAIL_OPEN | Concrete Rico account entitlement/no-minimum-trade condition has not yet been verified as runtime evidence |
| AC-05 real market data | FAIL_OPEN | No controlled real Rico/MT5 realtime session executed |
| AC-07 real ticks/candles | FAIL_OPEN | No real tick/final-candle capture has been adjudicated |
| Heartbeat/staleness/latency | FAIL_OPEN_REAL_SCOPE | Offline instrumentation exists; real-feed thresholds/evidence remain unadjudicated |
| Real laboratory evidence | FAIL_OPEN | No Rico/MT5 runtime evidence session yet |
| Official Security Diff Scan | FAIL_OPEN | Not executed; other checks are not relabeled as the official scan |

## Integrated Rico/MT5 laboratory policy

```text
PROVIDER = Rico-supplied MetaTrader 5
INSTRUMENT_FAMILY = WIN
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

Passive discovery must preserve the broker/server WIN candidates without ranking them. The exact provider symbol is selected explicitly for the controlled session. Ambiguous, incomplete, malformed or inconsistent discovery evidence fails closed.

The local evidence harness consumes only fresh append-only discovery/tick/candle files. It records technical evidence through the existing Sprint 1 evidence primitives and has no terminal-control, account, position, order, Paper or real-money authority.

## Historical decisions and superseded operational paths

BTG Data Services, its adapter, the historical controlled-capture harness and the historical secure runner remain in repository/Git history as auditable implementation evidence from the earlier provider decision. They are not the active runtime qualification path after ADR-0025.

The former BTG-specific Environment/secrets procedure is therefore not a current Sprint 1 blocker for Rico qualification. It must not be executed merely to satisfy obsolete checklist text.

DD-68 remains historical evidence for the earlier BTG laboratory profile; it is not silently rewritten into the Rico tick/final-candle procedure. The active Rico procedure is documented in `docs/program/workstreams/S1-RICO-MT5-FIRST-RUNTIME-QUALIFICATION.md`.

## Review treatment

Prior provider and harness reviews performed by the coordinating agent are not claimed as independent. This does not waive immutable Foundation conditions, real-provider evidence, exact-final-tree checks or the Security Diff Scan requirement.

## Current adjudication

```text
SPRINT1_INTERNAL_OBSERVER_CORE = COMPLETE_CURRENT_SCOPE
SPRINT1_CURRENT_PROVIDER_DECISION = COMPLETE
SPRINT1_RICO_OFFLINE_PROVIDER_BOUNDARY = INTEGRATED
SPRINT1_RICO_DISCOVERY = INTEGRATED
SPRINT1_RICO_LOCAL_EVIDENCE_HARNESS = INTEGRATED_OFFLINE_TESTED
SPRINT1_REAL_PROVIDER_QUALIFICATION = OPEN
SPRINT1_REAL_CAPTURE_GATE = OPEN
SPRINT1_SECURITY_GATE = OPEN
SPRINT1_ACCEPTANCE = NO
PROMOTION_TO_SPRINT_2 = NO
```

## Mandatory remaining sequence

1. Verify the concrete Rico account's MT5/platform/market-data entitlement at R$0 additional recurring cost and verify that retaining it does not require a minimum real-money operation.
2. Establish MT5 Investor/read-only authorization locally; do not disclose master/investor credentials to Git, chat, command-line arguments or evidence.
3. Create a fresh session namespace for discovery/tick/candle append-only files and a controlled local evidence output root.
4. Execute passive WIN discovery and explicitly resolve the exact current provider symbol; no automatic front-contract selection, rollover or fallback.
5. Execute the custom indicator plus `scripts/rico_mt5_first_lab_capture.py` for one controlled realtime observation session.
6. Require real tick flow and at least one genuinely finalized candle for the exact confirmed symbol; preserve the complete bounded consumed prefixes and technical evidence.
7. Review provenance, RunId, source/provider identity, continuity, heartbeat/staleness and local monotonic latency evidence. Runtime thresholds must be justified from real-feed evidence rather than inherited from fixtures.
8. Reconcile the real-provider evidence into AC/RQM/XC without upgrading any claim beyond the observed evidence.
9. Re-run full exact-final-tree CI, boundary and NEG-CAP after runtime evidence/documentation changes.
10. Execute the official Security Diff Scan on the exact final Sprint 1 diff/tree when the supported action is available, unless governance explicitly authorizes another treatment.
11. Adjudicate all 11 exit criteria conjunctively.
12. Promote to Sprint 2 only after formal Sprint 1 PASS.

## Explicit prohibitions remain in force

No open, implemented or passed gate authorizes Strategy, ML production wiring, Paper execution, Risk authorization, broker order APIs, trading credentials, ledger mutation, economic commitment or real-money operation.
