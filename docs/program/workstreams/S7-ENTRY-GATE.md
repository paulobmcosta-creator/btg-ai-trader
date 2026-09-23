# S7-ENTRY-GATE — Risk Engine Governance Packet

```text
SPRINT = 7
WORK_MODE = ENTRY_GATE_ONLY
ISSUE = #86
CANONICAL_BRANCH = sprint/7-risk-engine
WORK_BRANCH = s7/00-entry-gate
CANONICAL_BASE_SHA = 58e870925e9a1bf4ccbc0f796610d6297bcc57e2

FUNCTIONAL_IMPLEMENTATION = FORBIDDEN
SRC_RISK_ENGINE = MUST_NOT_EXIST_IN_THIS_PR
TEST_RISK_ENGINE = MUST_NOT_EXIST_IN_THIS_PR
NEW_RUNTIME_DEPENDENCIES = FORBIDDEN
MERGE = FORBIDDEN_WITHOUT_HUMAN_AUTHORIZATION
```

## 1. Authorized tasks

1. Materialize the S7 entry contract, decision register, capability matrix, sprint document and checkpoint.
2. Update living program governance to reflect the authorized S7 Entry Gate.
3. Extend pinned-upstream triggers to S7 gate branches.
4. Add S7 Entry Gate CI verifying frozen Foundation, required documents, exact S6 predecessor, no functional code/tests/dependency delta and clean diff.
5. Open a PR from `s7/00-entry-gate` to `sprint/7-risk-engine`.
6. Obtain exact-head Entry Gate CI and pinned-upstream evidence.
7. Perform independent review of the exact PR head.
8. Stop before merge without explicit human authorization.

## 2. Forbidden tasks

- creating a functional Risk Engine package;
- adding functional S7 tests;
- creating StrategyDecision/TradeIntent;
- creating OrderIntent/OrderPlan/ExecutionOrder;
- connecting broker/account/order APIs;
- mutating FinancialLedger;
- Paper or Live Trading;
- real money;
- auto-flatten or auto-cancel;
- adding paid services or mandatory runtime dependencies;
- merging without explicit human authorization.

## 3. Gate success condition

The gate may be adjudicated PASS candidate only if:

- Sprint 6 predecessor is exact, formally closed and green;
- triggered S7 decisions are adjudicated without premature S8 decisions;
- Risk authority separation and fail-closed semantics are explicit;
- negative capabilities are explicit;
- no functional/dependency delta exists;
- Entry Gate CI and pinned upstream pass;
- independent review finds zero blocking findings.

A PASS Entry Gate does not authorize functional Sprint 7 implementation.
