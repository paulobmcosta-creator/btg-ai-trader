# Sprint 7 — Risk Engine

```text
SPRINT_7_STATUS = ENTRY_GATE_IN_PROGRESS
SPRINT_7_LIFECYCLE = ENTRY_GATE
SPRINT_7_CANONICAL_BRANCH = sprint/7-risk-engine
SPRINT_7_ENTRY_GATE_WORK_BRANCH = s7/00-entry-gate
SPRINT_7_ENTRY_GATE_ISSUE = #86
SPRINT_7_REQUIRED_BASE_SHA = 58e870925e9a1bf4ccbc0f796610d6297bcc57e2

S7_ENTRY_GATE_CANDIDATE = PASS
S7_ENTRY_GATE_CANONICAL = NO
SPRINT_7_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
S7_ENTRY_GATE_MERGE = NOT_AUTHORIZED

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

No functional Risk Engine code or tests are authorized by this gate.

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
