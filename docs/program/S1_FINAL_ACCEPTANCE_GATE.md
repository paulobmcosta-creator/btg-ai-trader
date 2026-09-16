# Sprint 1 — Final Acceptance Gate Checkpoint

## Gate purpose

This living checkpoint records whether the current Sprint 1 state may be declared a formal PASS under immutable 0F-E. It does not rewrite 0F-B, 0F-E or 0F-F.

## Current state

```text
FOUNDATION = FORMALLY_CLOSED
SPRINT_1 = OPEN
CURRENT_PROVIDER_DECISION = ADR-0026
CURRENT_PROVIDER_SELECTION = XP_SUPPLIED_MT5
PROVIDER_ID = xp-mt5
ZERO_ADDITIONAL_RECURRING_COST = HARD_CONSTRAINT
REALTIME_REQUIREMENT = PRESERVED
MT5_TICK_BRIDGE = INTEGRATED
MT5_FINAL_CANDLE_BRIDGE = INTEGRATED
MT5_SYMBOL_DISCOVERY = INTEGRATED
XP_MT5_RUNTIME_RUNBOOK = INTEGRATED
MT5_LOCAL_EVIDENCE_HARNESS = INTEGRATED_AND_REALTIME_EXERCISED
READ_ONLY_BY_CONSTRUCTION_CURRENT_SCOPE = SATISFIED
STRUCTURAL_ESCALATION_CURRENT_SCOPE = SATISFIED
TRADING_CAPABILITY = ABSENT
REAL_MONEY_PATH = ABSENT
XP_PRELIMINARY_SESSION = EXECUTED_NONQUALIFYING
REAL_QUALIFYING_PROVIDER_SESSION = PASS_RUNTIME
RUNTIME_EVIDENCE_CODE_REVISION = e622658922ff38e49e1112a48d91eecb2d43a522
RUNTIME_EVIDENCE_SCOPE = s1-xp-capture-a12
SPRINT1_PROVIDER_QUALIFIED = NO_PENDING_FINAL_TREE_GATES
SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_ACCEPTANCE = NO
```

## Evidence adjudication

| Gate area | Result | Basis |
|---|---|---|
| Foundation integrity | PASS | Frozen Foundation artifacts remain unchanged |
| Functional Observer core | PASS_CURRENT_SCOPE | Passive Observer core integrated |
| 41 RQMs | CONDITIONAL | Real-provider evidence gap is resolved; RQM-018 and RQM-036 still await official Security Diff Scan |
| NEG-CAP-01..10 | PASS_CURRENT_SCOPE | XP runtime path introduces no strategy/order/execution/economic authority; exact-final-tree rerun pending |
| Current provider decision | PASS_DECISION | ADR-0026 selects XP-supplied MT5 for qualification |
| Historical BTG provider path | HISTORICAL_ONLY | ADR-0023 remains auditable reference history |
| Historical Rico provider path | HISTORICAL_SUPERSEDED | ADR-0025 and Rico-named implementation lineage preserved; active qualification is XP |
| MT5 tick bridge | PASS_RUNTIME | Passive append-only FILE_COMMON tick transport exercised against live XP feed |
| MT5 finalized-candle bridge | PASS_RUNTIME | Qualifying session captured explicitly finalized candle evidence |
| MT5 WIN discovery | PASS_RUNTIME | Complete candidate snapshot preserved; `WINV26` explicitly confirmed without automatic selection |
| XP Investor/read-only | PASS_LOCAL | Read-only authorization established without credential disclosure or order testing |
| Post-fix MQL5 compile | PASS | Exact reviewed source compiled `0 errors, 0 warnings` before a12 |
| Zero-cost concrete entitlement | PASS_EVIDENCE | Concrete account/interface evidence supports R$0 additional recurring entitlement and no minimum real-money operation requirement |
| AC-05 real market data | PASS_RUNTIME | a12 captured 8,005 realtime `WINV26` tick records through passive boundary |
| AC-07 real ticks/candles | PASS_RUNTIME | a12 completed with qualifying tick flow and explicitly finalized candle evidence |
| Heartbeat/staleness/latency | PASS_RUNTIME_SCOPE | Harness preserved continuously `READY` health evidence and local monotonic ingress-to-validated-availability measurements |
| Capture context/provenance/persistence | PASS_RUNTIME | Exact revision, run/config/provider context and preserved technical evidence recorded outside Git; sanitized hashes versioned |
| Exact-final-tree CI / NEG-CAP | FAIL_OPEN | Must be rerun after this evidence/documentation reconciliation |
| Official Security Diff Scan | FAIL_OPEN | Not executed; other checks cannot be relabeled as the official scan |

## Integrated XP/MT5 laboratory policy

```text
PROVIDER = XP-supplied MetaTrader 5
PROVIDER_ID = xp-mt5
INSTRUMENT_FAMILY = WIN
QUALIFIED_RUNTIME_TARGET = WINV26
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

The qualifying a12 discovery explicitly confirmed `WINV26` while preserving all discovered `WIN*` candidates without ranking. Ambiguous/incomplete/malformed evidence remains fail-closed.

The custom indicator emits explicit provider identity `xp-mt5`. Physical Rico-named artifact/class/script names are temporarily retained as compatibility names and must not be confused with runtime provenance.

## Successful qualifying-session record

Sanitized evidence is versioned at:

```text
docs/program/workstreams/S1-XP-MT5-RUNTIME-EVIDENCE-2026-09-16.md
```

The successful session was:

```text
CAPTURE_SCOPE = s1-xp-capture-a12
CODE_REVISION = e622658922ff38e49e1112a48d91eecb2d43a522
INSTRUMENT = WINV26
TIMEFRAME = PERIOD_M1
DISCOVERY_RECORDS = 18
TICK_RECORDS = 8005
CANDLE_RECORDS = 2
BRIDGE_FINAL_STATE = IDLE
GIT_WORKTREE_AT_CAPTURE = CLEAN
```

Raw transport payloads and the complete evidence-session directory remain outside Git. Their sanitized sizes and SHA-256 fingerprints are preserved in the evidence record and Issue #54.

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
SPRINT1_XP_PROVIDER_BOUNDARY = REALTIME_EXERCISED
SPRINT1_XP_ENTITLEMENT_READ_ONLY = PASS_EVIDENCE
SPRINT1_REAL_PROVIDER_RUNTIME_EVIDENCE = PASS
SPRINT1_REAL_CAPTURE_GATE = CLOSED_RUNTIME_SCOPE
SPRINT1_PROVIDER_QUALIFICATION = PENDING_FINAL_TREE_GATES
SPRINT1_EXACT_FINAL_TREE_CI_GATE = OPEN
SPRINT1_SECURITY_GATE = OPEN
SPRINT1_ACCEPTANCE = NO
PROMOTION_TO_SPRINT_2 = NO
```

## Mandatory remaining sequence

1. Complete the post-runtime documentation/evidence reconciliation without changing frozen Foundation artifacts.
2. Run full exact-final-tree tests, typing, lint, Foundation, boundary and NEG-CAP checks on the reconciled tree.
3. Execute the official Security Diff Scan on that exact final Sprint 1 diff/tree.
4. Reconcile any finding without weakening 0F-E, read-only-by-construction or structural-escalation requirements.
5. Adjudicate all 11 exit criteria conjunctively.
6. Set `SPRINT1_PROVIDER_QUALIFIED = YES` and `SPRINT1_ACCEPTANCE = YES` only if every remaining gate passes.
7. Promote to Sprint 2 only after formal Sprint 1 PASS.

## Explicit prohibitions remain in force

No open, implemented or passed gate authorizes Strategy, ML production wiring, Paper execution, Risk authorization, broker order APIs, trading credentials, financial-ledger mutation, economic commitment or real-money operation.