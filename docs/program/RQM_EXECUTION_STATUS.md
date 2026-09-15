# Sprint 1 — RQM and Exit-Criteria Evidence Status

This is a current evidence snapshot, not a normative rewrite and not a Sprint 1 approval record. Immutable authority remains `docs/foundation/0F-E_sprint1_entry_contract.md`.

## Integrated/reconciliation baseline

```text
SPRINT_BRANCH = sprint/1-market-observer
RECONCILIATION_BASELINE = bd9c9ce96cf0b0e44d609f16fc4d613efd1d3647
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
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
XP_PRELIMINARY_SESSION = EXECUTED_NONQUALIFYING
REAL_QUALIFYING_PROVIDER_SESSION = NOT_EXECUTED
SPRINT1_PROVIDER_QUALIFIED = NO
SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_ACCEPTANCE = NOT_GRANTED
REAL_MONEY_PATH = ABSENT
TRADING_CAPABILITY = ABSENT
```

## Principal evidence

| Area | Evidence | Result |
|---|---|---|
| Observer core | Prior Sprint 1 increments | Passive observation, provenance, latency, transition evidence, temporal lineage and technical persistence integrated |
| Historical BTG provider path | ADR-0023 | Auditable reference implementation only |
| Historical Rico provider path | ADR-0025 | MT5 implementation source and failed operational provider path preserved; superseded for active qualification |
| Current provider decision | ADR-0026 | XP-supplied MT5 selected for qualification under zero-additional-recurring-cost constraint |
| XP preliminary authentication | Owner session 14/09/2026 | XP MT5 login and Investor/read-only observed locally; no credentials versioned/shared |
| XP preliminary compile | Owner session 14/09/2026 | Pre-reconciliation reviewed indicator compiled `0 errors, 0 warnings`; must be repeated on final revised source |
| XP preliminary discovery | Owner session 14/09/2026 | 57.414 server symbols; 16 WIN matches/emitted; zero prefix/enumeration errors; WINV26 present; nonqualifying |
| MT5 read-only bridge | Current tree | One-way custom-indicator-to-FILE_COMMON transport; Python has no MT5 control/account/order API |
| MT5 finalized candles | Current tree | Finalized-candle bridge integrated and offline tested |
| MT5 symbol discovery | Current tree | Passive WIN candidate enumeration; ambiguity preserved; no automatic mapping/selection |
| XP runtime runbook | `S1-XP-MT5-FIRST-RUNTIME-QUALIFICATION.md` | Controlled procedure; qualifying runtime evidence still absent |
| Local evidence harness | `scripts/rico_mt5_first_lab_capture.py` | Legacy filename; file-only harness integrated/offline tested; active provenance is `xp-mt5` |

## 41 RQMs

The provider reconciliation and preliminary XP session do not convert missing realtime evidence into satisfied runtime evidence and do not replace the official Security Diff Scan.

```text
SATISFIED_OR_FIXTURE_SCOPE = 39
BLOCKED_SECURITY_SCAN = 2  # RQM-018, RQM-036
PARTIAL = 0
TOTAL = 41
```

Material limits remain:

- RQM-017/022/024/028/041 retain integrated/fixture evidence but require real-provider qualification where applicable before final adjudication.
- RQM-018 remains `BLOCKED_SECURITY_SCAN`: structural/config/possible-secret checks may pass, but the official Security Diff Scan has not executed.
- RQM-036 remains `BLOCKED_SECURITY_SCAN`: no order/account/execution SDK path or trading-credential consumption is authorized in Sprint 1, but the official Security Diff Scan is still absent.
- Historical BTG/Rico evidence is not relabeled as XP realtime evidence.

## Positive capability view

| Capability | Current state |
|---|---|
| AC-01 Instrument Discovery & Resolution | PRELIMINARY_XP_DISCOVERY_SUPPORTED; fresh qualifying-session discovery/review pending |
| AC-02 Provider Symbol / Reference Mapping | PRELIMINARY_WINV26_MAPPING_SUPPORTED; exact point-in-time qualifying evidence pending |
| AC-03 Provider Capability Discovery | IMPLEMENTED_INTEGRATED; real XP feed behavior pending |
| AC-04 Read-Only Provider Authentication | PRELIMINARY_XP_INVESTOR_EVIDENCE_AVAILABLE; qualifying-session review pending |
| AC-05 Read-Only Market-Data Subscription / Access | XP_MT5_BOUNDARY_IMPLEMENTED; real realtime evidence pending |
| AC-06 Historical Request | NOT_TRIGGERED_CONDITIONAL |
| AC-07 Tick & Candle Observation | IMPLEMENTED_OFFLINE_MT5; real tick + genuine finalized-candle evidence pending |
| AC-08 Heartbeat & Liveness | INSTRUMENTED_OFFLINE; real-feed evidence/threshold adjudication pending |
| AC-09 Observable Latency Measurement | INSTRUMENTED_OFFLINE; real local monotonic evidence pending |
| AC-10 Quality / Admission | SATISFIED_FIXTURE_SCOPE; real-provider reconciliation pending where applicable |
| AC-11 Invalid Event Quarantine | SATISFIED |
| AC-12 Capture Context & Provenance | IMPLEMENTED_INTEGRATED; real XP qualifying run pending |
| AC-13 Technical Evidence Persistence | IMPLEMENTED_INTEGRATED; real XP evidence pending |
| AC-14 Telemetry / Dedup / Backpressure | SATISFIED_CURRENT_SCOPE |

## XP runtime qualification state

```text
PROVIDER = XP-supplied MetaTrader 5
PROVIDER_ID = xp-mt5
AUTHORIZATION = Investor/read-only only
MQL5_PROGRAM_TYPE = custom indicator
TRANSPORT = append-only FILE_COMMON
PYTHON_METATRADER5_IMPORT = NO
PYTHON_ACCOUNT_API = NO
PYTHON_ORDER_API = NO
MASTER_PASSWORD_IN_PROJECT_OR_CHAT = NO
AUTO_CONTRACT_SELECTION = NO
AUTO_ROLLOVER = NO
AUTO_FALLBACK = NO
ORDER_TEST_FOR_READ_ONLY = FORBIDDEN
```

The runtime operator must verify the concrete XP account's zero-additional-recurring-cost entitlement and absence of a minimum real-money operation requirement before qualification. Public XP marketing/comparison evidence supports selection only.

The controlled runbook is `docs/program/workstreams/S1-XP-MT5-FIRST-RUNTIME-QUALIFICATION.md`. The local evidence harness retains the compatibility filename `scripts/rico_mt5_first_lab_capture.py`.

## 11 Exit Criteria

| XC | Status | Evidence / blocker |
|---|---|---|
| XC-01 Required capabilities | PARTIAL | Passive MT5 boundary plus preliminary XP discovery/auth evidence exist; realtime provider evidence absent |
| XC-02 Decision gates | SATISFIED_CURRENT_DECISIONS | ADR-0026 is current; ADR-0025/0023 remain preserved history |
| XC-03 All 41 RQMs | PARTIAL | 39 direct/fixture scope; RQM-018 and RQM-036 await official Security Diff Scan; real-provider limits remain explicit |
| XC-04 HQI/QPI evidence | PARTIAL | Technical causal/offline evidence present; real-provider/security evidence incomplete |
| XC-05 NEG-CAP-01..10 | SATISFIED_CURRENT_SCOPE | Provider migration adds no strategy/order/execution/economic authority |
| XC-06 READ_ONLY_BY_CONSTRUCTION | SATISFIED_CURRENT_SCOPE | Custom-indicator/file-only path; trusted Python receives no terminal/account/order API |
| XC-07 STRUCTURAL_ESCALATION | SATISFIED_CURRENT_SCOPE | Configuration/credential changes cannot create financial execution capability in the integrated graph |
| XC-08 Zero trading credentials / ledger mutation | PARTIAL | No trading credential/ledger path; official scan and final runtime evidence outstanding |
| XC-09 Strict code / typing / lint | REQUIRES_PR_HEAD_CI | Previous baseline green; provider-reconciliation head must pass full checks before merge/final adjudication |
| XC-10 RunManifest / CaptureContext | IMPLEMENTED_OFFLINE | Harness emits canonical run/capture context using active provider identity; real WIN session pending |
| XC-11 No Sprint-2+ escape | SATISFIED_CURRENT_SCOPE | Formal replay/Paper/Risk/strategy/execution remain outside Sprint 1 graph |

## Remaining blockers before formal Sprint 1 PASS

```text
B1 = XP_ACCOUNT_ENTITLEMENT: verify concrete R$0 additional recurring platform/data entitlement and no minimum real-money operation requirement
B2 = POST_RECONCILIATION_COMPILE: compile exact reviewed XP-provenance indicator with 0 errors / 0 warnings
B3 = QUALIFYING_DISCOVERY_MAPPING: execute fresh complete WIN discovery and explicitly confirm the exact point-in-time contract
B4 = REAL_PROVIDER_SESSION: capture realtime ticks + genuinely finalized candle through the passive bridge
B5 = REAL_PROVIDER_EVIDENCE: adjudicate provider identity, continuity, provenance, heartbeat/staleness, latency and data fidelity
B6 = EXACT_FINAL_TREE_EVIDENCE: rerun CI/RQM/NEG-CAP after runtime evidence/documentation reconciliation
B7 = SECURITY_DIFF_SCAN: execute official scan for exact final Sprint 1 diff/tree
B8 = CONJUNCTIVE_EXIT_GATE: all 11 exit criteria must pass before Sprint 2 promotion
```

None of these blockers authorizes broker order APIs, master/trading credentials, Paper, Risk, Strategy, financial-ledger mutation or real money.