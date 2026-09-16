# Sprint 1 — RQM and Exit-Criteria Evidence Status

This is the final-acceptance reconciliation snapshot for Sprint 1. Immutable authority remains `docs/foundation/0F-E_sprint1_entry_contract.md`; no frozen Foundation artifact is rewritten.

## Reconciliation baseline

```text
CANONICAL_SPRINT1_BRANCH = sprint/1-market-observer
FINAL_RECONCILIATION_BRANCH = s1/30-final-acceptance-github-security
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
CURRENT_PROVIDER_DECISION = ADR-0026
CURRENT_PROVIDER_SELECTION = XP_SUPPLIED_MT5
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
SPRINT1_ACCEPTANCE = PENDING_FINAL_RECONCILIATION_CI
REAL_MONEY_PATH = ABSENT
TRADING_CAPABILITY = ABSENT
```

## Principal evidence

| Area | Evidence | Result |
|---|---|---|
| Observer core | Integrated Sprint 1 increments | Passive observation, provenance, latency, transition evidence, temporal lineage and technical persistence integrated |
| Current provider decision | ADR-0026 | XP-supplied MT5 selected under the zero-additional-recurring-cost constraint |
| XP entitlement | Non-secret account/interface evidence | R$0 additional recurring entitlement; no minimum real-money operation requirement identified |
| XP Investor/read-only | Local operator evidence | Read-only authorization without credential disclosure or order testing |
| Exact MQL5 compile | Local MetaEditor compile | `XPMarketDataBridge.mq5`: `0 errors, 0 warnings` |
| XP qualifying runtime | `S1-XP-MT5-RUNTIME-EVIDENCE-2026-09-16.md` | a12 completed on exact revision `e622658...`; `WINV26`, M1, 8,005 ticks, 2 candle records, 18-record discovery snapshot |
| Read-only bridge | Current tree + a12 | One-way custom-indicator-to-FILE_COMMON path; Python has no MT5 control/account/order API |
| Exact integrated-head engineering evidence | GitHub Actions run `35126543429` on `6457ae1...` | tests/lint/types/compile/dependencies/Foundation/boundary/diff PASS |
| Security assurance | `S1_GITHUB_SECURITY_ALTERNATIVE_GATE_2026-09-16.md` | GitHub-native security alternative accepted; Official Codex scan remains NOT_EXECUTED |

Raw provider payloads and the full evidence-session directory remain outside Git. Sanitized counts, byte lengths and SHA-256 fingerprints are recorded in the runtime-evidence record.

## 41 RQMs

The successful XP runtime session resolved the real-provider evidence gap. The explicit human security decision resolves the two requirements previously blocked only by the unavailable Official Codex Security Diff Scan through an accepted alternative evidence package, without waiving their substantive security requirements.

```text
SATISFIED_OR_CURRENT_SCOPE = 41
BLOCKED_SECURITY_SCAN = 0
PARTIAL = 0
TOTAL = 41
```

Material adjudication:

- RQM-017/022/024/028/041 have real-provider evidence where applicable through a12.
- RQM-018 is `SATISFIED_BY_ACCEPTED_SECURITY_ALTERNATIVE`: NEG-CAP/static/config/possible-secret checks and GitHub-native review provide the required security evidence; the Official Codex scan remains explicitly `NOT_EXECUTED`.
- RQM-036 is `SATISFIED_BY_ACCEPTED_SECURITY_ALTERNATIVE`: no order/account/execution SDK path or trading-credential consumption is present, with exact-tree boundary evidence and formal security gate record.
- Historical BTG/Rico evidence is not relabeled as XP realtime evidence.

## Positive capability view

| Capability | Current state |
|---|---|
| AC-01 Instrument Discovery & Resolution | SATISFIED_RUNTIME_EVIDENCE |
| AC-02 Provider Symbol / Reference Mapping | SATISFIED_RUNTIME_EVIDENCE — explicit point-in-time `WINV26`; no automatic selection/rollover |
| AC-03 Provider Capability Discovery | SATISFIED_CURRENT_RUNTIME_SCOPE |
| AC-04 Read-Only Provider Authentication | SATISFIED_LOCAL_EVIDENCE |
| AC-05 Read-Only Market-Data Subscription / Access | SATISFIED_RUNTIME_EVIDENCE |
| AC-06 Historical Request | NOT_TRIGGERED_CONDITIONAL |
| AC-07 Tick & Candle Observation | SATISFIED_RUNTIME_EVIDENCE |
| AC-08 Heartbeat & Liveness | SATISFIED_RUNTIME_EVIDENCE_WITHIN_SESSION_POLICY |
| AC-09 Observable Latency Measurement | SATISFIED_RUNTIME_EVIDENCE_LOCAL_MONOTONIC_SCOPE |
| AC-10 Quality / Admission | SATISFIED_CURRENT_SCOPE |
| AC-11 Invalid Event Quarantine | SATISFIED |
| AC-12 Capture Context & Provenance | SATISFIED_RUNTIME_EVIDENCE |
| AC-13 Technical Evidence Persistence | SATISFIED_RUNTIME_EVIDENCE |
| AC-14 Telemetry / Dedup / Backpressure | SATISFIED_CURRENT_SCOPE |

## XP runtime qualification state

```text
PROVIDER = XP-supplied MetaTrader 5
PROVIDER_ID = xp-mt5
AUTHORIZATION = Investor/read-only only
MQL5_PROGRAM_TYPE = custom indicator
TRANSPORT = append-only FILE_COMMON
QUALIFYING_CAPTURE = s1-xp-capture-a12
QUALIFYING_CODE_REVISION = e622658922ff38e49e1112a48d91eecb2d43a522
PYTHON_METATRADER5_IMPORT = NO
PYTHON_ACCOUNT_API = NO
PYTHON_ORDER_API = NO
MASTER_PASSWORD_IN_PROJECT_OR_CHAT = NO
AUTO_CONTRACT_SELECTION = NO
AUTO_ROLLOVER = NO
AUTO_FALLBACK = NO
ORDER_TEST_FOR_READ_ONLY = FORBIDDEN
```

## 11 Exit Criteria — candidate final adjudication

All substantive criteria are satisfied. XC-09 and the formal conjunctive verdict remain conditioned only on a green exact-head run of this documentary reconciliation branch before merge.

| XC | Candidate status | Evidence |
|---|---|---|
| XC-01 Required capabilities | PASS | Required passive capabilities have implementation and real XP evidence |
| XC-02 Decision gates | PASS | Current ADR/DD decisions resolved or legitimately deferred; history preserved |
| XC-03 All 41 RQMs | PASS | 41/41 satisfied/current scope, including RQM-018/036 by accepted security alternative |
| XC-04 HQI/QPI evidence | PASS | Applicable quality/protocol evidence preserved without identified unresolved deviation |
| XC-05 NEG-CAP-01..10 | PASS | Integrated NEG-CAP/runtime suite and boundary evidence; no financial authority |
| XC-06 READ_ONLY_BY_CONSTRUCTION | PASS | One-way custom-indicator/file-only runtime boundary physically exercised |
| XC-07 STRUCTURAL_ESCALATION | PASS | Configuration/credential changes cannot create an execution path in the integrated graph |
| XC-08 Zero trading credentials / ledger mutation | PASS | No trading credential consumption or financial-ledger mutation path present |
| XC-09 Strict code / typing / lint | PASS_PRE_RECONCILIATION; FINAL_RUN_REQUIRED | Exact integrated head `6457ae1...` green; this documentation branch must also be green before merge |
| XC-10 RunManifest / CaptureContext | PASS | a12 persisted run/capture context under active provider identity |
| XC-11 No Sprint-2+ escape | PASS | Replay/Paper/Risk/Strategy/Execution remain outside Sprint 1 baseline |

## Former blockers

```text
B1 XP_ACCOUNT_ENTITLEMENT = RESOLVED
B2 POST_RECONCILIATION_COMPILE = RESOLVED
B3 QUALIFYING_DISCOVERY_MAPPING = RESOLVED
B4 REAL_PROVIDER_SESSION = RESOLVED
B5 REAL_PROVIDER_EVIDENCE = RESOLVED_RUNTIME_SCOPE
B6 EXACT_FINAL_TREE_EVIDENCE = RESOLVED_FOR_6457ae1 / FINAL_DOCUMENTARY_HEAD_RERUN_REQUIRED
B7 OFFICIAL_SECURITY_DIFF_SCAN = REPLACED_BY_EXPLICITLY_ACCEPTED_GITHUB_NATIVE_SECURITY_GATE
B8 CONJUNCTIVE_EXIT_GATE = READY_FOR_FINAL_ADJUDICATION_AFTER_GREEN_RECONCILIATION_HEAD
```

The replacement of B7 changes only the assurance instrument. It does not authorize broker order APIs, master/trading credentials, Paper, Risk, Strategy, financial-ledger mutation or real money.