# Sprint 1 — RQM and Exit-Criteria Evidence Status

This is a current evidence snapshot, not a normative rewrite and not a Sprint 1 approval record. Immutable authority remains `docs/foundation/0F-E_sprint1_entry_contract.md`.

## Integrated baseline

```text
SPRINT_BRANCH = sprint/1-market-observer
INTEGRATED_IMPLEMENTATION_BASELINE = ac3d1083f483bb85220f7637d21b4d5a4e34b11d
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
CURRENT_PROVIDER_DECISION = ADR-0025
CURRENT_PROVIDER_SELECTION = RICO_SUPPLIED_MT5
ZERO_ADDITIONAL_RECURRING_COST = HARD_CONSTRAINT
REALTIME_REQUIREMENT = PRESERVED
RICO_MT5_TICK_BRIDGE = INTEGRATED
RICO_MT5_FINAL_CANDLE_BRIDGE = INTEGRATED
RICO_MT5_SYMBOL_DISCOVERY = INTEGRATED
RICO_MT5_RUNTIME_RUNBOOK = INTEGRATED
RICO_MT5_LOCAL_EVIDENCE_HARNESS = INTEGRATED_OFFLINE_TESTED
REAL_PROVIDER_SESSION = NOT_EXECUTED
SPRINT1_PROVIDER_QUALIFIED = NO
SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_ACCEPTANCE = NOT_GRANTED
REAL_MONEY_PATH = ABSENT
TRADING_CAPABILITY = ABSENT
```

## Principal integrated evidence

| Area | Evidence | Result |
|---|---|---|
| Observer core | Prior Sprint 1 increments | Passive observation, provenance, latency, transition evidence, temporal lineage and technical persistence integrated |
| Historical BTG provider path | ADR-0023 and historical PRs | Auditable reference implementation only; no longer the active qualification provider |
| Current provider decision | ADR-0025 | Rico-supplied MT5 selected for qualification under zero-additional-recurring-cost constraint |
| Rico read-only bridge | Integrated current tree | One-way custom-indicator-to-FILE_COMMON transport; Python has no MT5 control/account/order API |
| Rico finalized candles | Integrated current tree | Finalized-candle bridge integrated and offline tested |
| Rico symbol discovery | Integrated current tree | Passive WIN candidate enumeration; ambiguity preserved; no automatic mapping/selection |
| Rico runtime runbook | `S1-RICO-MT5-FIRST-RUNTIME-QUALIFICATION.md` | Controlled operator procedure materialized; no runtime evidence asserted |
| Rico local evidence harness | PR #51 / baseline `ac3d1083...` | File-only evidence harness integrated after exact-head CI/upstream PASS and post-merge CI PASS |

## 41 RQMs

The current provider change and offline Rico instrumentation do not convert missing real-provider evidence into satisfied runtime evidence and do not replace the official Security Diff Scan.

```text
SATISFIED_OR_FIXTURE_SCOPE = 39
BLOCKED_SECURITY_SCAN = 2  # RQM-018, RQM-036
PARTIAL = 0
TOTAL = 41
```

Material limits remain:

- RQM-017/022/024/028/041 retain integrated/fixture evidence but require real-provider qualification where applicable before final adjudication.
- RQM-018 remains `BLOCKED_SECURITY_SCAN`: structural/config/possible-secret checks pass, but the official Security Diff Scan has not executed.
- RQM-036 remains `BLOCKED_SECURITY_SCAN`: no order/account/execution SDK path or trading-credential consumption exists in the integrated Sprint 1 runtime graph, but the official Security Diff Scan is still absent.
- Historical BTG real-lab assumptions are not reused as Rico runtime evidence.

## Positive capability view

| Capability | Current state |
|---|---|
| AC-01 Instrument Discovery & Resolution | IMPLEMENTED_OFFLINE_RICO; real provider discovery pending |
| AC-02 Provider Symbol / Reference Mapping | POLICY_AND_DISCOVERY_IMPLEMENTED; explicit real point-in-time mapping pending |
| AC-03 Provider Capability Discovery | IMPLEMENTED_INTEGRATED; real Rico feed behavior pending |
| AC-04 Read-Only Provider Authentication | PENDING_REAL_RICO_INVESTOR_EVIDENCE |
| AC-05 Read-Only Market-Data Subscription / Access | RICO_BOUNDARY_IMPLEMENTED_OFFLINE; real realtime feed evidence pending |
| AC-06 Historical Request | NOT_TRIGGERED_CONDITIONAL |
| AC-07 Tick & Candle Observation | IMPLEMENTED_OFFLINE_RICO; real tick + genuine finalized-candle evidence pending |
| AC-08 Heartbeat & Liveness | INSTRUMENTED_OFFLINE; real-feed evidence/threshold adjudication pending |
| AC-09 Observable Latency Measurement | INSTRUMENTED_OFFLINE; real local monotonic evidence pending |
| AC-10 Quality / Admission | SATISFIED_FIXTURE_SCOPE; real-provider reconciliation pending where applicable |
| AC-11 Invalid Event Quarantine | SATISFIED |
| AC-12 Capture Context & Provenance | IMPLEMENTED_INTEGRATED; real Rico run pending |
| AC-13 Technical Evidence Persistence | IMPLEMENTED_INTEGRATED; real Rico evidence pending |
| AC-14 Telemetry / Dedup / Backpressure | SATISFIED_CURRENT_SCOPE |

## Rico runtime qualification state

The current execution path is local and intentionally does not require the historical BTG protected GitHub Environment or BTG API-key/evidence secrets.

```text
PROVIDER = Rico-supplied MetaTrader 5
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

The runtime operator must verify the concrete account's zero-additional-recurring-cost entitlement and absence of a minimum real-money operation requirement before qualification. Those account-specific facts are not inferred from public marketing or offline code.

The controlled runbook is `docs/program/workstreams/S1-RICO-MT5-FIRST-RUNTIME-QUALIFICATION.md`. The local evidence harness is `scripts/rico_mt5_first_lab_capture.py`.

## 11 Exit Criteria

| XC | Status | Evidence / blocker |
|---|---|---|
| XC-01 Required capabilities | PARTIAL | Rico passive boundary and evidence harness integrated; real provider evidence absent |
| XC-02 Decision gates | SATISFIED_CURRENT_DECISIONS | Current provider authority is ADR-0025; historical decisions remain preserved rather than rewritten |
| XC-03 All 41 RQMs | PARTIAL | 39 direct/fixture scope; RQM-018 and RQM-036 await official Security Diff Scan; real-provider limits remain explicit |
| XC-04 HQI/QPI evidence | PARTIAL | Technical causal/offline evidence present; real-provider/security evidence incomplete |
| XC-05 NEG-CAP-01..10 | SATISFIED_CURRENT_TREE | No strategy/order/execution/economic authority introduced through Rico bridge/harness |
| XC-06 READ_ONLY_BY_CONSTRUCTION | SATISFIED_CURRENT_TREE | Custom-indicator/file-only path; trusted Python receives no terminal/account/order API |
| XC-07 STRUCTURAL_ESCALATION | SATISFIED_CURRENT_TREE | Config/credential changes cannot create financial execution capability in the integrated graph |
| XC-08 Zero trading credentials / ledger mutation | PARTIAL | No trading credential/ledger path; official scan and final runtime evidence outstanding |
| XC-09 Strict code / typing / lint | SATISFIED_INTEGRATION_EVIDENCE | PR #51 exact head and merge baseline passed tests/Ruff/mypy/compile/dependencies/Foundation/boundary/diff; final-tree rerun still required after runtime evidence reconciliation |
| XC-10 RunManifest / CaptureContext | IMPLEMENTED_OFFLINE | Rico harness emits canonical run/capture context; real WIN session pending |
| XC-11 No Sprint-2+ escape | SATISFIED_CURRENT_TREE | Formal replay/Paper/Risk/strategy/execution remain outside Sprint 1 graph |

## Remaining blockers before formal Sprint 1 PASS

```text
B1 = RICO_ACCOUNT_ENTITLEMENT: verify concrete R$0 additional recurring platform/data entitlement and no minimum real-money operation requirement
B2 = RICO_INVESTOR_AUTH: establish local Investor/read-only authorization without credential exposure or order testing
B3 = REAL_PROVIDER_SESSION: execute controlled WIN discovery + exact symbol + realtime tick/final-candle observation through the passive bridge
B4 = REAL_PROVIDER_EVIDENCE: adjudicate provider identity, continuity, provenance, heartbeat/staleness, latency and observed data without exceeding evidence
B5 = EXACT_FINAL_TREE_EVIDENCE: rerun CI/RQM/NEG-CAP after real evidence/documentation reconciliation
B6 = SECURITY_DIFF_SCAN: execute official scan for exact final Sprint 1 diff/tree, or apply only a separately explicit governance treatment
B7 = CONJUNCTIVE_EXIT_GATE: all 11 exit criteria must pass before Sprint 2 promotion
```

None of these blockers authorizes a broker order API, master/trading credential, Paper engine, Risk engine, financial ledger mutation or real-money path.
