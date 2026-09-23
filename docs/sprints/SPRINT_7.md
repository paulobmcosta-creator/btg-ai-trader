# Sprint 7 — Risk Engine

```text
SPRINT_7_STATUS = ENTRY_GATE_CANONICAL
SPRINT_7_LIFECYCLE = AWAITING_FUNCTIONAL_AUTHORIZATION
SPRINT_7_CANONICAL_BRANCH = sprint/7-risk-engine
SPRINT_7_ENTRY_GATE_WORK_BRANCH = s7/00-entry-gate
SPRINT_7_ENTRY_GATE_ISSUE = #86
SPRINT_7_REQUIRED_BASE_SHA = 58e870925e9a1bf4ccbc0f796610d6297bcc57e2

S7_ENTRY_GATE = PASS
S7_ENTRY_GATE_CANONICAL = PASS
S7_ENTRY_GATE_PR = #87
S7_ENTRY_GATE_PR_HEAD = 0aac73fca2e291e7355f683ceda25fdcb3650d2e
S7_ENTRY_GATE_INDEPENDENT_REVIEW = PASS
S7_ENTRY_GATE_REVIEW_ID = 5295358543
S7_ENTRY_GATE_MERGE_SHA = 8d475abd8751d0042d06840012604de140e18d21
S7_ENTRY_GATE_POST_MERGE_CI_RUN = 35909666368
S7_ENTRY_GATE_POST_MERGE_UPSTREAM_RUN = 35909666371
OPEN_S7_ENTRY_GATE_BLOCKERS = 0
SPRINT_7_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
S7_ENTRY_GATE_MERGE = COMPLETED_BY_EXPLICIT_HUMAN_AUTHORIZATION

PAPER_TRADING = NO
LIVE_TRADING = NO
REAL_MONEY = NO
```

## Purpose

Sprint 7 is the independent Risk Engine stage. Its future authorized implementation will own deterministic risk veto and bounded authorization semantics before Paper Trading can exist.

Core conceptual chain:

```text
immutable proposal evidence
        |
        v
RiskEvaluationBoundary
        |
        v
RISK ENGINE
   /          \
REJECT       PERMIT
               |
               v
       RiskAuthorization
               |
        [NO EXECUTION IN S7]
```

Risk does not create Strategy proposals and does not send orders.

## Entry Gate scope

This gate materializes:

- authority and input/state/policy boundaries;
- exposure/capacity semantics;
- daily-loss/drawdown/tail-risk policy boundaries;
- circuit-breaker/fail-safe semantics;
- triggered/deferred DD reconciliation;
- positive and negative capability matrix;
- entry-gate CI;
- exact-head/pinned-upstream evidence;
- independent review.

The Entry Gate is canonical PASS. No functional Risk Engine code or tests are authorized by this gate.

## Current boundary

```text
RISK_DECISION = FUTURE_FUNCTIONAL_SCOPE_AFTER_EXPLICIT_AUTHORIZATION
RISK_AUTHORIZATION = FUTURE_FUNCTIONAL_SCOPE_AFTER_EXPLICIT_AUTHORIZATION

ORDER_INTENT = FORBIDDEN
EXECUTION_ORDER = FORBIDDEN
BROKER_SIDE_EFFECT = FORBIDDEN
FINANCIAL_LEDGER_MUTATION = FORBIDDEN
PAPER = FORBIDDEN
LIVE = FORBIDDEN
REAL_MONEY = FORBIDDEN
```
