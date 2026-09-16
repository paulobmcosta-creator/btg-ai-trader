# Sprint 1 — RQM and Exit-Criteria Evidence Status

This is the final Sprint 1 evidence snapshot. Immutable authority remains `docs/foundation/0F-E_sprint1_entry_contract.md`; no frozen Foundation artifact is rewritten.

## Final baseline

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
FINAL_RECONCILIATION_VALIDATED_HEAD = 977923a4693b4b14d1ddab47a77d7bf86cb250b9
FINAL_RECONCILIATION_REMOTE_CI_RUN = 35128804489
FINAL_RECONCILIATION_PINNED_UPSTREAM_RUN = 35128804436
FINAL_RECONCILIATION_CI = PASS
OFFICIAL_CODEX_SECURITY_DIFF_SCAN = NOT_EXECUTED
GITHUB_NATIVE_SECURITY_ALTERNATIVE = ACCEPTED_BY_HUMAN_DECISION
GITHUB_NATIVE_SECURITY_GATE = PASS
SPRINT1_PROVIDER_QUALIFIED = YES
SPRINT1_ACCEPTANCE = YES
PROMOTION_TO_SPRINT_2 = YES
REAL_MONEY_PATH = ABSENT
TRADING_CAPABILITY = ABSENT
```

The final adjudication commit is documentary only and must remain green under the same checks before merge. This requirement does not reopen the substantive gate; it prevents a bad documentary merge.

## Principal evidence

| Area | Evidence | Result |
|---|---|---|
| Observer core | Integrated Sprint 1 increments | PASS |
| Current provider decision | ADR-0026 | PASS |
| XP entitlement | Non-secret account/interface evidence | PASS |
| XP Investor/read-only | Local operator evidence | PASS |
| Exact MQL5 compile | MetaEditor compile | PASS — `0 errors, 0 warnings` |
| XP qualifying runtime | `S1-XP-MT5-RUNTIME-EVIDENCE-2026-09-16.md` | PASS_RUNTIME |
| Read-only bridge | Current tree + a12 | PASS_RUNTIME |
| Exact integrated-head CI | GitHub Actions `35126543429` on `6457ae1...` | PASS |
| Final reconciliation CI | GitHub Actions `35128804489` + upstream `35128804436` on `977923a...` | PASS |
| Security assurance | `S1_GITHUB_SECURITY_ALTERNATIVE_GATE_2026-09-16.md` | PASS_GITHUB_NATIVE_ALTERNATIVE |
| Official Codex Security Diff Scan | Historical fact | NOT_EXECUTED |

## 41 RQMs — final result

```text
SATISFIED_OR_CURRENT_SCOPE = 41
BLOCKED = 0
PARTIAL = 0
TOTAL = 41
```

RQM-018 and RQM-036 are satisfied through the explicitly accepted GitHub-native security evidence package. The Official Codex scan remains `NOT_EXECUTED`; no claim to the contrary is made.

Historical BTG/Rico evidence remains historical and is not relabeled as XP realtime evidence.

## Positive capability view

| Capability | Final state |
|---|---|
| AC-01 Instrument Discovery & Resolution | PASS_RUNTIME |
| AC-02 Provider Symbol / Reference Mapping | PASS_RUNTIME — explicit point-in-time `WINV26` |
| AC-03 Provider Capability Discovery | PASS_CURRENT_SCOPE |
| AC-04 Read-Only Provider Authentication | PASS_LOCAL_EVIDENCE |
| AC-05 Read-Only Market-Data Subscription / Access | PASS_RUNTIME |
| AC-06 Historical Request | NOT_TRIGGERED_CONDITIONAL |
| AC-07 Tick & Candle Observation | PASS_RUNTIME |
| AC-08 Heartbeat & Liveness | PASS_RUNTIME_SCOPE |
| AC-09 Observable Latency Measurement | PASS_RUNTIME_LOCAL_MONOTONIC_SCOPE |
| AC-10 Quality / Admission | PASS_CURRENT_SCOPE |
| AC-11 Invalid Event Quarantine | PASS |
| AC-12 Capture Context & Provenance | PASS_RUNTIME |
| AC-13 Technical Evidence Persistence | PASS_RUNTIME |
| AC-14 Telemetry / Dedup / Backpressure | PASS_CURRENT_SCOPE |

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

## 11 Exit Criteria — final conjunctive adjudication

| XC | Final verdict | Evidence |
|---|---|---|
| XC-01 Required capabilities | PASS | Required passive capabilities implemented and evidenced |
| XC-02 Decision gates | PASS | Decisions resolved before material dependencies or legitimately deferred |
| XC-03 All 41 RQMs | PASS | 41/41 satisfied/current scope |
| XC-04 HQI/QPI evidence | PASS | Applicable quality/protocol evidence preserved without unresolved deviation |
| XC-05 NEG-CAP-01..10 | PASS | Integrated NEG-CAP/runtime suite and boundary evidence |
| XC-06 READ_ONLY_BY_CONSTRUCTION | PASS | One-way custom-indicator/file-only boundary physically exercised |
| XC-07 STRUCTURAL_ESCALATION | PASS | Configuration/credential changes cannot create financial execution authority in the integrated graph |
| XC-08 Zero trading credentials / ledger mutation | PASS | No trading-credential consumption or financial-ledger mutation path |
| XC-09 Strict code / typing / lint | PASS | Exact final-reconciliation pre-adjudication head `977923a...` green in GitHub CI |
| XC-10 RunManifest / CaptureContext | PASS | a12 preserved canonical run/capture context |
| XC-11 No Sprint-2+ escape | PASS | Replay/Paper/Risk/Strategy/Execution absent from Sprint 1 baseline |

```text
XC_01_TO_11 = PASS
CONJUNCTIVE_EXIT_GATE = PASS
SPRINT1_PROVIDER_QUALIFIED = YES
SPRINT1_ACCEPTANCE = YES
PROMOTION_TO_SPRINT_2 = YES
```

## Blocker ledger — final

```text
B1 XP_ACCOUNT_ENTITLEMENT = RESOLVED
B2 POST_RECONCILIATION_COMPILE = RESOLVED
B3 QUALIFYING_DISCOVERY_MAPPING = RESOLVED
B4 REAL_PROVIDER_SESSION = RESOLVED
B5 REAL_PROVIDER_EVIDENCE = RESOLVED_RUNTIME_SCOPE
B6 EXACT_FINAL_TREE_EVIDENCE = RESOLVED
B7 SECURITY_ASSURANCE = RESOLVED_BY_EXPLICITLY_ACCEPTED_GITHUB_NATIVE_SECURITY_GATE
B8 CONJUNCTIVE_EXIT_GATE = RESOLVED_PASS
OPEN_BLOCKERS = 0
```

No resolved gate authorizes broker order APIs, master/trading credentials, Paper, Risk, Strategy, financial-ledger mutation or real money.