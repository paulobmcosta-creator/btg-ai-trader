# Sprint 1 — Final Acceptance Gate Checkpoint

## Gate purpose

This living checkpoint records whether the current Sprint 1 baseline may be declared a formal PASS under immutable 0F-E. It does not rewrite 0F-B, 0F-E or 0F-F.

## Current state

```text
FOUNDATION = FORMALLY_CLOSED
SPRINT_1 = OPEN
INTEGRATED_IMPLEMENTATION_BASELINE = 5a9fa177b609e56e06e7835b291beac821c8bbd6
PROVIDER_PR_34 = MERGED
CAPTURE_HARNESS_PR_35 = MERGED
SECURE_LAB_RUNNER_PR_40 = MERGED
READ_ONLY_BY_CONSTRUCTION_CURRENT_TREE = SATISFIED
STRUCTURAL_ESCALATION_CURRENT_TREE = SATISFIED
TRADING_CAPABILITY = ABSENT
REAL_MONEY_PATH = ABSENT
BTG_LAB_ENVIRONMENT = EXTERNAL_CONFIGURATION_NOT_VERIFIED
REAL_PROVIDER_SESSION = NOT_EXECUTED
SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_ACCEPTANCE = NO
```

## Evidence adjudication

| Gate area | Result | Basis |
|---|---|---|
| Foundation integrity | PASS | Frozen Foundation artifacts remain unchanged |
| Functional Observer core | PASS_CURRENT_SCOPE | Passive Observer core integrated |
| 41 RQMs | CONDITIONAL | 39 direct/fixture; RQM-018 and RQM-036 await official Security Diff Scan |
| NEG-CAP-01..10 | PASS_CURRENT_TREE | Structural/runtime negative-capability evidence remains green |
| Instrument discovery/resolution | PASS_FIXTURE_SCOPE | Point-in-time discovery integrated; controlled real evidence pending |
| DD-60 provider decision | PASS_DECISION | BTG Solutions Data Services selected; ADR-0023 |
| DD-43 credential policy | PASS_POLICY | External read-only secret only; no trading credential |
| Provider adapter | PASS_IMPLEMENTATION | PR #34 integrated |
| Capture harness | PASS_IMPLEMENTATION | PR #35 integrated with fail-closed discovery remediation |
| Secure laboratory runner | PASS_IMPLEMENTATION | PR #40 integrated after exact-head CI/upstream PASS; no real session executed by merge |
| Protected Environment configuration | FAIL_OPEN | `btg-readonly-lab` administrative configuration cannot be verified through the current connector |
| AC-05 real subscription | FAIL_OPEN | No authenticated real provider session executed |
| DD-68 laboratory profile | PASS_DECISION | WIN; exact point-in-time confirmation; realtime trades; no fallback/rollover/candles |
| Real laboratory evidence | FAIL_OPEN | No real API-key authentication/discovery/subscription/raw trade capture yet |
| Official Security Diff Scan | FAIL_OPEN | Not executed; other checks are not relabeled as official scan |

## Integrated laboratory policy

```text
INSTRUMENT_FAMILY = WIN
CONCRETE_CONTRACT = EXPLICIT_CANDIDATE_PLUS_PROVIDER_CONFIRMATION_POINT_IN_TIME
STREAM_TYPE = realtime
DATA_TYPE = trades
DATA_SUBTYPE = derivatives
AUTO_FALLBACK = FORBIDDEN
AUTO_ROLLOVER = FORBIDDEN
VENDOR_AUTO_RECONNECT = FORBIDDEN
INITIAL_CANDLES = NO
ENVIRONMENT = btg-readonly-lab
RAW_PUBLIC_ARTIFACT = NO
```

Before any real subscription, provider discovery must confirm the exact WIN candidate. Ambiguous, malformed, mixed or error-bearing discovery evidence must fail closed.

The secure runner requires an explicit request branch/file, checks that the request pins the current remote Sprint 1 SHA, executes the exact clean Sprint 1 code revision, encrypts raw evidence before artifact upload, and exposes only a sanitized no-price/no-raw-payload summary.

## Review treatment

For PRs #34, #35 and #40, the project owner explicitly authorized the same coordinating agent to perform adversarial review and proceed. These reviews are not claimed as independent. This does not waive immutable Foundation conditions, real-provider evidence, exact-final-tree checks or the Security Diff Scan requirement.

## Current adjudication

```text
SPRINT1_INTERNAL_OBSERVER_CORE = COMPLETE_CURRENT_SCOPE
SPRINT1_PROVIDER_DECISION = COMPLETE
SPRINT1_DD68_DECISION = COMPLETE
SPRINT1_PROVIDER_IMPLEMENTATION = INTEGRATED
SPRINT1_CAPTURE_HARNESS = INTEGRATED
SPRINT1_SECURE_LAB_RUNNER = INTEGRATED
SPRINT1_REAL_CAPTURE_GATE = OPEN
SPRINT1_SECURITY_GATE = OPEN
SPRINT1_ACCEPTANCE = NO
PROMOTION_TO_SPRINT_2 = NO
```

## Mandatory remaining sequence

1. Configure/protect GitHub Environment `btg-readonly-lab` for the dedicated laboratory branch.
2. Provision `BTG_LAB_DATASERVICES_API_KEY` and `BTG_LAB_EVIDENCE_PASSPHRASE` as Environment secrets outside repository/chat.
3. Select one explicit concrete WIN candidate; no automatic ranking, nearest-expiry substitution, fallback or rollover.
4. Create the dedicated laboratory request from the then-current Sprint 1 head and execute the secure runner.
5. Require at least one confirmed exact-symbol `trade` event; ACK/control/non-trade messages do not satisfy success.
6. Review the sanitized summary and protected evidence, including discovery/confirmation/subscription/close and one RunId.
7. If restart behavior is tested, use a new explicit auditable session; never vendor auto-reconnect.
8. Reconcile real-provider evidence into RQM/XC without upgrading fixture-only claims beyond evidence.
9. Re-run full CI, boundary and NEG-CAP on the exact final Sprint 1 tree after final evidence/documentation changes.
10. Execute the official Security Diff Scan on the exact final Sprint 1 diff/tree, or only use a separately explicit governance treatment if authorized.
11. Adjudicate all 11 exit criteria conjunctively.
12. Promote to Sprint 2 only after formal Sprint 1 PASS.

## Explicit prohibitions remain in force

No open, implemented or passed gate authorizes Strategy, ML production wiring, Paper execution, Risk authorization, broker order APIs, trading credentials, ledger mutation, economic commitment or real-money operation.
