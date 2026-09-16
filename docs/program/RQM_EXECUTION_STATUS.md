# Sprint 1 — RQM and Exit-Criteria Evidence Status

This is a current evidence snapshot, not a normative rewrite and not a Sprint 1 approval record. Immutable authority remains `docs/foundation/0F-E_sprint1_entry_contract.md`.

## Integrated/reconciliation baseline

```text
SPRINT_BRANCH = sprint/1-market-observer
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
MT5_LOCAL_EVIDENCE_HARNESS = INTEGRATED_AND_REALTIME_EXERCISED
XP_PRELIMINARY_SESSION = EXECUTED_NONQUALIFYING
REAL_QUALIFYING_PROVIDER_SESSION = PASS_RUNTIME
RUNTIME_EVIDENCE_CODE_REVISION = e622658922ff38e49e1112a48d91eecb2d43a522
RUNTIME_EVIDENCE_SCOPE = s1-xp-capture-a12
SPRINT1_PROVIDER_QUALIFIED = NO_PENDING_FINAL_TREE_GATES
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
| XP concrete entitlement | Non-secret account/interface evidence + public XP comparison | R$0 additional recurring MT5/platform/data entitlement; no minimum real-money operation requirement identified |
| XP Investor/read-only | Local operator evidence | Investor/read-only authorization established without credential disclosure or order testing |
| Exact post-fix compile | Local MetaEditor compile | `XPMarketDataBridge.mq5`: `0 errors, 0 warnings` |
| XP qualifying runtime capture | `S1-XP-MT5-RUNTIME-EVIDENCE-2026-09-16.md` / Issue #54 | `s1-xp-capture-a12` completed on exact revision `e622658...`; `WINV26`, M1, 8,005 ticks, 2 candle records, complete 18-record discovery snapshot |
| MT5 read-only bridge | Current tree + a12 | One-way custom-indicator-to-FILE_COMMON transport exercised against live XP feed; Python has no MT5 control/account/order API |
| XP runtime runbook | `S1-XP-MT5-FIRST-RUNTIME-QUALIFICATION.md` | Controlled procedure executed successfully for a12 |
| Local evidence harness | `scripts/rico_mt5_first_lab_capture.py` | File-only harness validated exact symbol/provider, contiguous sequences, finalized candle, health, latency, provenance and persistence; active provenance is `xp-mt5` |

Raw provider payloads and the full evidence-session directory remain outside Git. Sanitized counts, byte lengths and SHA-256 fingerprints are recorded in `docs/program/workstreams/S1-XP-MT5-RUNTIME-EVIDENCE-2026-09-16.md`.

## 41 RQMs

The successful XP realtime session resolves the previously open real-provider evidence gap. It does not replace the official Security Diff Scan.

```text
SATISFIED_OR_CURRENT_SCOPE = 39
BLOCKED_SECURITY_SCAN = 2  # RQM-018, RQM-036
PARTIAL = 0
TOTAL = 41
```

Material limits remain:

- RQM-017/022/024/028/041 now have real-provider evidence where applicable through the controlled a12 session, subject to final conjunctive adjudication.
- RQM-018 remains `BLOCKED_SECURITY_SCAN`: structural/config/possible-secret checks may pass, but the official Security Diff Scan has not executed on the exact final reconciled tree.
- RQM-036 remains `BLOCKED_SECURITY_SCAN`: no order/account/execution SDK path or trading-credential consumption is authorized in Sprint 1, but the official Security Diff Scan is still absent.
- Historical BTG/Rico evidence is not relabeled as XP realtime evidence.

## Positive capability view

| Capability | Current state |
|---|---|
| AC-01 Instrument Discovery & Resolution | SATISFIED_RUNTIME_EVIDENCE — complete a12 discovery snapshot preserved; all candidates retained |
| AC-02 Provider Symbol / Reference Mapping | SATISFIED_RUNTIME_EVIDENCE — explicit point-in-time `WINV26` confirmation; no automatic selection/rollover |
| AC-03 Provider Capability Discovery | SATISFIED_CURRENT_RUNTIME_SCOPE — live XP MT5 passive observation path exercised |
| AC-04 Read-Only Provider Authentication | SATISFIED_LOCAL_EVIDENCE — Investor/read-only authorization established without order testing |
| AC-05 Read-Only Market-Data Subscription / Access | SATISFIED_RUNTIME_EVIDENCE — live XP `WINV26` tick flow captured through passive boundary |
| AC-06 Historical Request | NOT_TRIGGERED_CONDITIONAL |
| AC-07 Tick & Candle Observation | SATISFIED_RUNTIME_EVIDENCE — 8,005 realtime ticks and qualifying finalized-candle evidence captured |
| AC-08 Heartbeat & Liveness | SATISFIED_RUNTIME_EVIDENCE_WITHIN_SESSION_POLICY — harness maintained continuously `READY` path |
| AC-09 Observable Latency Measurement | SATISFIED_RUNTIME_EVIDENCE_LOCAL_MONOTONIC_SCOPE — ingress-to-validated-availability only |
| AC-10 Quality / Admission | SATISFIED_CURRENT_SCOPE — fail-closed validation and exact symbol/provider checks preserved |
| AC-11 Invalid Event Quarantine | SATISFIED |
| AC-12 Capture Context & Provenance | SATISFIED_RUNTIME_EVIDENCE — exact revision/config/run/provider context persisted |
| AC-13 Technical Evidence Persistence | SATISFIED_RUNTIME_EVIDENCE — raw prefixes and technical evidence persisted outside Git with sanitized fingerprints versioned |
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

The controlled runbook is `docs/program/workstreams/S1-XP-MT5-FIRST-RUNTIME-QUALIFICATION.md`. The successful sanitized record is `docs/program/workstreams/S1-XP-MT5-RUNTIME-EVIDENCE-2026-09-16.md`. The local evidence harness retains the compatibility filename `scripts/rico_mt5_first_lab_capture.py`.

## 11 Exit Criteria

| XC | Status | Evidence / blocker |
|---|---|---|
| XC-01 Required capabilities | SATISFIED_RUNTIME_SCOPE | Required passive provider capabilities now have real XP evidence; final gate remains conjunctive |
| XC-02 Decision gates | SATISFIED_CURRENT_DECISIONS | ADR-0026 is current; ADR-0025/0023 remain preserved history |
| XC-03 All 41 RQMs | PARTIAL | 39 satisfied/current scope; RQM-018 and RQM-036 await official Security Diff Scan |
| XC-04 HQI/QPI evidence | PARTIAL_FINAL_GATE | Runtime technical evidence now present; exact-final-tree/security evidence still incomplete |
| XC-05 NEG-CAP-01..10 | SATISFIED_CURRENT_SCOPE | XP runtime path adds no strategy/order/execution/economic authority; exact-final-tree rerun pending |
| XC-06 READ_ONLY_BY_CONSTRUCTION | SATISFIED_RUNTIME_SCOPE | Custom-indicator/file-only path exercised against real feed; trusted Python receives no terminal/account/order API |
| XC-07 STRUCTURAL_ESCALATION | SATISFIED_CURRENT_SCOPE | Configuration/credential changes cannot create financial execution capability in the integrated graph |
| XC-08 Zero trading credentials / ledger mutation | PARTIAL_FINAL_SCAN | No trading credential/ledger path observed; official Security Diff Scan pending |
| XC-09 Strict code / typing / lint | REQUIRES_EXACT_FINAL_TREE_CI | Prior CI green; reconciled final-tree checks must run after this documentation update |
| XC-10 RunManifest / CaptureContext | SATISFIED_RUNTIME_EVIDENCE | a12 persisted canonical run/capture context under active provider identity |
| XC-11 No Sprint-2+ escape | SATISFIED_CURRENT_SCOPE | Formal replay/Paper/Risk/strategy/execution remain outside Sprint 1 graph |

## Remaining blockers before formal Sprint 1 PASS

```text
B6 = EXACT_FINAL_TREE_EVIDENCE: rerun CI/typing/lint/Foundation/boundary/NEG-CAP after runtime evidence/documentation reconciliation
B7 = SECURITY_DIFF_SCAN: execute official scan for the exact final Sprint 1 diff/tree
B8 = CONJUNCTIVE_EXIT_GATE: all 11 exit criteria must pass before Sprint 2 promotion
```

Resolved by the a12 qualification sequence and preserved supporting evidence:

```text
B1 XP_ACCOUNT_ENTITLEMENT = RESOLVED
B2 POST_RECONCILIATION_COMPILE = RESOLVED
B3 QUALIFYING_DISCOVERY_MAPPING = RESOLVED
B4 REAL_PROVIDER_SESSION = RESOLVED
B5 REAL_PROVIDER_EVIDENCE = RESOLVED_RUNTIME_SCOPE
```

None of the remaining gates authorizes broker order APIs, master/trading credentials, Paper, Risk, Strategy, financial-ledger mutation or real money.