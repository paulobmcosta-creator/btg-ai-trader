# Sprint 1 — Final Acceptance Gate Checkpoint

## Gate purpose

This living checkpoint records whether the current Sprint 1 baseline may be declared a formal PASS under immutable 0F-E. It does not rewrite 0F-B, 0F-E or 0F-F.

## Current state

```text
FOUNDATION = FORMALLY_CLOSED
SPRINT_1 = OPEN
CURRENT_INTEGRATED_BASELINE = 0c59a19956f43651778441e48d30299e4df72c30
PROVIDER_PR_34 = MERGED @ d1d865d32f88b7420cfd0555823240d793131c19
CAPTURE_HARNESS_PR_35 = MERGED @ 0c59a19956f43651778441e48d30299e4df72c30
ACTIONS_BLOCKER_ISSUE_36 = RESOLVED_CLOSED
READ_ONLY_BY_CONSTRUCTION_CURRENT_TREE = SATISFIED
STRUCTURAL_ESCALATION_CURRENT_TREE = SATISFIED
TRADING_CAPABILITY = ABSENT
REAL_MONEY_PATH = ABSENT
REAL_PROVIDER_SESSION = NOT_EXECUTED
SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_ACCEPTANCE = NO
```

## Evidence adjudication

| Gate area | Result | Basis |
|---|---|---|
| Foundation integrity | PASS | Frozen Foundation artifacts remain unchanged. |
| Functional Observer core | PASS_CURRENT_SCOPE | Passive Observer core is integrated. |
| 41 RQMs | CONDITIONAL | 39 have direct/fixture evidence; RQM-018 and RQM-036 await the official Security Diff Scan. |
| NEG-CAP-01..10 | PASS_CURRENT_TREE | Structural and runtime negative-capability evidence remains green through the provider/harness integrations. |
| Instrument discovery/resolution | PASS_FIXTURE_SCOPE | Causal point-in-time discovery is integrated; controlled real provider evidence pending. |
| DD-60 provider decision | PASS_DECISION | BTG Solutions Data Services selected and materialized by ADR-0023. |
| DD-43 credential policy | PASS_POLICY | API key is an external read-only runtime secret; no trading credential is authorized. |
| Provider adapter | PASS_IMPLEMENTATION | PR #34 integrated the narrow read-only boundary after exact-head CI/provider/upstream PASS. |
| Capture harness | PASS_IMPLEMENTATION | PR #35 integrated the bounded WIN/realtime/trades harness after adversarial discovery-remediation and exact-head CI/upstream PASS. |
| AC-05 real subscription | FAIL_OPEN | No authenticated real provider session has been executed. |
| DD-68 laboratory profile | PASS_DECISION | WIN; exact contract confirmed point-in-time; `trades` over `realtime`; no initial candles; no automatic fallback/rollover. |
| Real laboratory evidence | FAIL_OPEN | No real API-key authentication/discovery/subscription/raw trade capture has been executed. |
| Official Security Diff Scan | FAIL_OPEN | Not executed; history secret scan and other structural/runtime checks are not relabeled as this official scan. |

## Integrated laboratory policy

```text
DD_68 = RESOLVED
INSTRUMENT_FAMILY = WIN
CONCRETE_CONTRACT = EXPLICIT_CANDIDATE_PLUS_PROVIDER_CONFIRMATION_POINT_IN_TIME
AUTO_FALLBACK = FORBIDDEN
AUTO_ROLLOVER = FORBIDDEN
STREAM_TYPE = realtime
DATA_GRANULARITY = trades
DATA_SUBTYPE = derivatives
INITIAL_CANDLES = NO
VENDOR_AUTO_RECONNECT = NO
```

Immediately before a real subscription, BTG Data Services discovery must confirm the exact WIN candidate selected for the session. The exact symbol is then fixed in that run/capture context. If the discovery response is absent, ambiguous, malformed, error-bearing or does not confirm the candidate, the capture MUST NOT subscribe.

No specific expiry becomes a permanent default. A symbol used for one session does not silently determine the next session.

The integrated harness recognizes only bounded discovery response shapes; arbitrary request echoes or nested string lists cannot authorize subscription. This fail-closed behavior was added after adversarial review of PR #35 and is regression-tested.

## Review treatment

The project owner explicitly authorized the same coordinating agent to perform adversarial review and proceed for PRs #34 and #35. These reviews are **not claimed as independent**. The authorization does not waive any immutable Foundation condition, real-provider evidence, final-tree verification or Security Diff Scan requirement.

## Current adjudication

```text
SPRINT1_INTERNAL_OBSERVER_CORE = COMPLETE_CURRENT_SCOPE
SPRINT1_PROVIDER_DECISION = COMPLETE
SPRINT1_DD68_DECISION = COMPLETE
SPRINT1_PROVIDER_IMPLEMENTATION = INTEGRATED
SPRINT1_CAPTURE_HARNESS = INTEGRATED
SPRINT1_REAL_CAPTURE_GATE = OPEN
SPRINT1_SECURITY_GATE = OPEN
SPRINT1_ACCEPTANCE = NO
PROMOTION_TO_SPRINT_2 = NO
```

## Mandatory remaining sequence

1. Provision a read-only BTG Data Services API key through an authorized external runtime/secret mechanism; never commit or paste it into chat.
2. Select one explicit concrete WIN candidate for the controlled session; no automatic ranking, nearest-expiry substitution, fallback or rollover.
3. Execute the integrated read-only harness on the reviewed Sprint 1 code revision.
4. Persist one causal RunId covering authentication/session start, discovery evidence, explicit exact-symbol confirmation, subscription, raw realtime trades and close.
5. Require at least one confirmed `trade` event for the exact selected symbol; ACK/control/non-trade messages do not satisfy success.
6. Adjudicate provider liveness/disconnect and, if restart is tested, use a new explicit auditable session rather than vendor auto-reconnect.
7. Reconcile the real-provider evidence into RQM/XC status without upgrading fixture-only claims beyond the evidence.
8. Re-run full CI, boundary and NEG-CAP checks on the exact final Sprint 1 tree after final evidence/documentation changes.
9. Execute the official Security Diff Scan on the exact final Sprint 1 diff/tree, or use only a separately explicit governance waiver if one is authorized.
10. Adjudicate all 11 exit criteria conjunctively.
11. Promote to Sprint 2 only if formal Sprint 1 PASS is granted.

## Explicit prohibitions remain in force

No open, implemented or passed gate in this document authorizes Strategy, ML production wiring, Paper execution, Risk authorization, broker order APIs, trading credentials, ledger mutation, economic commitment or real-money operation.
