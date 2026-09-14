# Sprint 1 — Final Acceptance Gate Checkpoint

## Gate purpose

This living checkpoint records whether the current Sprint 1 baseline may be declared a formal PASS under immutable 0F-E. It does not rewrite 0F-B, 0F-E or 0F-F.

## Current state

```text
FOUNDATION = FORMALLY_CLOSED
SPRINT_1 = OPEN
CURRENT_INTEGRATED_BASELINE = 4fb5807f985d06ef8673a28e689b815a08763940
PROVIDER_PR = #34 DRAFT / NOT_MERGED
READ_ONLY_BY_CONSTRUCTION_CURRENT_TREE = SATISFIED
STRUCTURAL_ESCALATION_CURRENT_TREE = SATISFIED
TRADING_CAPABILITY = ABSENT
REAL_MONEY_PATH = ABSENT
SPRINT1_ACCEPTANCE = NO
```

## Evidence adjudication

| Gate area | Result | Basis |
|---|---|---|
| Foundation integrity | PASS | Frozen Foundation artifacts remain unchanged. |
| Functional Observer core | PASS_CURRENT_SCOPE | Passive Observer core is integrated. |
| 41 RQMs | CONDITIONAL | 39 have direct/fixture evidence; RQM-018 and RQM-036 await the official Security Diff Scan. |
| NEG-CAP-01..10 | PASS | Structural and runtime negative-capability evidence exists for the integrated passive graph. |
| Instrument discovery/resolution | PASS_FIXTURE_SCOPE | Causal point-in-time discovery is integrated. |
| DD-60 provider decision | PASS_DECISION | Human coordination selected BTG Solutions Data Services; ADR-0023 materializes the choice. |
| DD-43 credential policy | PASS_POLICY | API key is external runtime secret only; no trading credential is authorized. |
| Provider adapter | PENDING_INTEGRATION | PR #34 implements a narrow read-only boundary but remains unmerged pending current-head CI. |
| AC-05 real subscription | FAIL_OPEN | No real authenticated provider session/capture has been executed. |
| DD-68 laboratory profile | PASS_DECISION | WIN family; concrete contract resolved/confirmed point-in-time; `trades` over `realtime`; no initial candles; no automatic fallback/rollover. |
| Real laboratory evidence | FAIL_OPEN | No API key/session/discovery/subscription/raw capture has been executed. |
| Official Security Diff Scan | FAIL_OPEN | Not executed; other structural/runtime evidence is not relabeled as the official scan. |

## DD-68 policy now in force

```text
DD_68 = RESOLVED
INSTRUMENT_FAMILY = WIN
CONCRETE_CONTRACT = RESOLVE_POINT_IN_TIME
AUTO_FALLBACK = FORBIDDEN
AUTO_ROLLOVER = FORBIDDEN
STREAM_TYPE = realtime
DATA_GRANULARITY = trades
INITIAL_CANDLES = NO
```

Immediately before a real capture, BTG Data Services discovery must confirm the exact WIN contract selected for the run. That exact symbol is fixed in the run/capture context before subscription. If resolution is missing, ambiguous or invalid, capture MUST NOT start.

No specific expiry becomes a permanent default. A symbol used for one session does not silently determine the next session.

The first laboratory uses the real-time trades stream. Candle subscription/aggregation is outside the initial capture profile and cannot silently replace the approved input.

## Current adjudication

```text
SPRINT1_INTERNAL_OBSERVER_CORE = COMPLETE_CURRENT_SCOPE
SPRINT1_PROVIDER_DECISION = COMPLETE
SPRINT1_DD68_DECISION = COMPLETE
SPRINT1_PROVIDER_IMPLEMENTATION = PENDING_PR_34
SPRINT1_REAL_CAPTURE_GATE = OPEN
SPRINT1_SECURITY_GATE = OPEN
SPRINT1_ACCEPTANCE = NO
PROMOTION_TO_SPRINT_2 = NO
```

## Mandatory remaining sequence

1. Obtain successful current-head CI for PR #34 and integrate only after exact-head review/checks are green.
2. Provision a read-only BTG Data Services API key outside the repository and outside chat.
3. Start a controlled read-only session.
4. Run provider discovery, resolve/confirm the exact WIN contract point-in-time and persist the decision in the run/capture context.
5. Subscribe only to that confirmed instrument using `trades` + `realtime`; no automatic fallback, rollover or initial candle stream.
6. Collect real evidence for authentication, discovery, observation, heartbeat/disconnect, explicit restart and raw capture.
7. Re-run full CI, RQM and NEG-CAP evidence on the exact final tree.
8. Execute the official Security Diff Scan on the exact final Sprint 1 diff/tree, or only use a waiver if explicitly authorized by governance.
9. Adjudicate all 11 exit criteria conjunctively.

## Explicit prohibitions remain in force

No open or passed gate in this document authorizes Strategy, ML production wiring, Paper execution, Risk authorization, broker order APIs, trading credentials, ledger mutation, economic commitment or real-money operation.
