# Sprint 1 — RQM and Exit-Criteria Evidence Status

This is a current evidence snapshot, not a normative rewrite and not a Sprint 1 approval record. Immutable authority remains `docs/foundation/0F-E_sprint1_entry_contract.md`.

## Integrated baseline

```text
SPRINT_BRANCH = sprint/1-market-observer
INTEGRATED_IMPLEMENTATION_BASELINE = 5a9fa177b609e56e06e7835b291beac821c8bbd6
PR_34_PROVIDER = MERGED
PR_35_CAPTURE_HARNESS = MERGED
PR_40_SECURE_LAB_RUNNER = MERGED
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
DD_60_INITIAL_REAL_PROVIDER = ACCEPTED_BTG_SOLUTIONS_DATA_SERVICES
DD_68_FIRST_LAB = RESOLVED_WIN_TRADES_REALTIME
AC_05_PROVIDER_ADAPTER = INTEGRATED_READ_ONLY
CONTROLLED_CAPTURE_HARNESS = INTEGRATED_READ_ONLY
SECURE_REAL_LAB_RUNNER = INTEGRATED_NOT_EXECUTED
BTG_LAB_ENVIRONMENT = EXTERNAL_CONFIGURATION_NOT_VERIFIED
REAL_PROVIDER_SESSION = NOT_EXECUTED
SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_ACCEPTANCE = NOT_GRANTED
REAL_MONEY_PATH = ABSENT
TRADING_CAPABILITY = ABSENT
```

## Principal integrated evidence

| Area | Evidence | Result |
|---|---|---|
| Observer core | PRs #28–#33 | Passive observation, provenance, latency, transition evidence, temporal lineage and point-in-time discovery integrated |
| Selected provider | PR #34 | BTG Data Services read-only adapter integrated after exact-head CI/provider/upstream PASS |
| Capture harness | PR #35 | One-session WIN/realtime/trades harness integrated after fail-closed discovery remediation and exact-head PASS |
| Secure laboratory runner | PR #40 | Protected-environment runner integrated after exact-head tests/Ruff/mypy/compile/dependencies/Foundation/boundary/diff/upstream PASS |

## 41 RQMs

The per-RQM classification remains unchanged by PR #40 because the runner prepares execution but does not supply real provider evidence.

```text
SATISFIED_OR_FIXTURE_SCOPE = 39
BLOCKED_SECURITY_SCAN = 2  # RQM-018, RQM-036
PARTIAL = 0
TOTAL = 41
```

Material limits remain:

- RQM-017/022/024/028/041 retain fixture/integrated implementation evidence but await real-provider qualification where applicable.
- RQM-018 remains `BLOCKED_SECURITY_SCAN`: structural/config/possible-secret checks pass, but the official Security Diff Scan has not executed.
- RQM-036 remains `BLOCKED_SECURITY_SCAN`: no order/account/execution SDK path or trading-credential consumption exists in the integrated tree, but the official Security Diff Scan is still absent.

## Positive capability view

| Capability | Current state |
|---|---|
| AC-01 Instrument Discovery & Resolution | SATISFIED_FIXTURE_SCOPE; real provider discovery pending |
| AC-02 Provider Symbol / Reference Mapping | SATISFIED_FIXTURE_SCOPE; DD-68 point-in-time policy fixed |
| AC-03 Provider Capability Discovery | IMPLEMENTED_INTEGRATED; real evidence pending |
| AC-04 Read-Only Provider Authentication | PENDING_REAL_PROVIDER_EVIDENCE |
| AC-05 Read-Only Market-Data Subscription | IMPLEMENTED_INTEGRATED / PENDING_REAL_PROVIDER_EVIDENCE |
| AC-06 Historical Request | NOT_TRIGGERED_CONDITIONAL |
| AC-07 Tick & Candle Observation | SATISFIED_FIXTURE_SCOPE; first real lab is `trades/realtime` |
| AC-08 Heartbeat & Liveness | SATISFIED_FIXTURE_SCOPE; real provider behavior pending |
| AC-09 Observable Latency Measurement | SATISFIED_FIXTURE_SCOPE |
| AC-10 Quality / Admission | SATISFIED_FIXTURE_SCOPE |
| AC-11 Invalid Event Quarantine | SATISFIED |
| AC-12 Capture Context & Provenance | SATISFIED_FIXTURE_SCOPE; real run pending |
| AC-13 Technical Evidence Persistence | SATISFIED_FIXTURE_SCOPE; canonical store integrated |
| AC-14 Telemetry / Dedup / Backpressure | SATISFIED |

## Secure laboratory state

PR #40 does not qualify the provider by itself. It adds a controlled execution boundary with:

```text
ENVIRONMENT = btg-readonly-lab
LAB_API_KEY_SECRET = BTG_LAB_DATASERVICES_API_KEY
LAB_EVIDENCE_SECRET = BTG_LAB_EVIDENCE_PASSPHRASE
REQUEST_BRANCH = lab/btg-s1-first-capture
REQUEST_FILE = config/btg-first-lab-request.json
RAW_PUBLIC_ARTIFACT = NO
ENCRYPTED_RAW_ARTIFACT = YES
SANITIZED_REMOTE_SUMMARY = YES
```

The current GitHub connector cannot inspect or modify Environment/secrets administration, so actual configuration of those external controls is not asserted.

## 11 Exit Criteria

| XC | Status | Evidence / blocker |
|---|---|---|
| XC-01 Required capabilities | PARTIAL | Provider and runner are integrated; real authenticated provider evidence absent |
| XC-02 Decision gates | SATISFIED | DD-60/DD-68 resolved; DD-43 policy defined |
| XC-03 All 41 RQMs | PARTIAL | 39 direct/fixture; RQM-018 and RQM-036 await official Security Diff Scan |
| XC-04 HQI/QPI evidence | PARTIAL | Technical causal evidence present; real-provider/security evidence incomplete |
| XC-05 NEG-CAP-01..10 | SATISFIED_CURRENT_TREE | No strategy/order/execution/economic authority introduced through PR #40 |
| XC-06 READ_ONLY_BY_CONSTRUCTION | SATISFIED_CURRENT_TREE | Provider, harness and runner are market-data-only by construction |
| XC-07 STRUCTURAL_ESCALATION | SATISFIED_CURRENT_TREE | Config/credential swap cannot create financial execution capability |
| XC-08 Zero trading credentials / ledger mutation | PARTIAL | No trading credential/ledger path; official scan and final evidence outstanding |
| XC-09 Strict code / typing / lint | SATISFIED_INTEGRATION_EVIDENCE | #34/#35/#40 exact heads were green before merge; final-tree rerun still required after final evidence tree |
| XC-10 RunManifest / CaptureContext | SATISFIED_FIXTURE_SCOPE | Integrated harness emits canonical context; real WIN session pending |
| XC-11 No Sprint-2+ escape | SATISFIED_CURRENT_TREE | Formal replay/Paper/Risk/strategy/execution remain outside Sprint 1 graph |

## Remaining blockers before formal Sprint 1 PASS

```text
B1 = EXTERNAL_LAB_CONFIGURATION: configure/protect `btg-readonly-lab` and provision Environment secrets outside chat/repository
B2 = REAL_PROVIDER_SESSION: execute controlled WIN trades/realtime discovery/confirmation/subscription/capture
B3 = REAL_PROVIDER_EVIDENCE: adjudicate authentication, discovery, confirmation, trade observation and close/restart evidence
B4 = EXACT_FINAL_TREE_EVIDENCE: rerun CI/RQM/NEG-CAP after final evidence/documentation tree is fixed
B5 = SECURITY_DIFF_SCAN: execute official scan for exact final Sprint 1 diff/tree, or apply only a separately explicit governance treatment
```

None of these blockers authorizes a broker account, trading credential, order API, Paper engine, Risk engine or real-money path.
