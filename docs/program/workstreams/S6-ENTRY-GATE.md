# S6-ENTRY-GATE — Scenario Engine Governance Packet

```text
SPRINT = 6
WORK_MODE = ENTRY_GATE_ONLY
ISSUE = #79
CANONICAL_BRANCH = sprint/6-scenario-engine
WORK_BRANCH = s6/00-entry-gate
CANONICAL_BASE_SHA = 9956f3a15d1fa2f87b347d436a26d684d50ba857

FUNCTIONAL_IMPLEMENTATION = FORBIDDEN
SRC_SCENARIO_ENGINE = MUST_NOT_EXIST_IN_THIS_PR
TEST_SCENARIO_ENGINE = MUST_NOT_EXIST_IN_THIS_PR
NEW_RUNTIME_DEPENDENCIES = FORBIDDEN
MERGE = FORBIDDEN_WITHOUT_HUMAN_AUTHORIZATION
```

## 1. Authorized tasks

1. Materialize the S6 entry contract, decision register, capability matrix, sprint document and entry-gate checkpoint.
2. Update living program documents to reflect an S6 Entry Gate candidate.
3. Extend pinned-upstream workflow triggers to S6 gate branches.
4. Add an entry-gate-only CI workflow that verifies:
   - frozen Foundation;
   - required S6 documents;
   - no `src/` or `tests/` functional changes;
   - no dependency changes;
   - clean `git diff --check`.
5. Open a PR from `s6/00-entry-gate` to `sprint/6-scenario-engine`.
6. Obtain exact-head CI and pinned-upstream evidence.
7. Perform independent review.
8. Stop before merge unless human authorization is explicit.

## 2. Forbidden tasks

- Creating `src/btg_ai_trader/scenario_engine/`.
- Adding functional Scenario Engine tests.
- Adding runtime dependencies.
- Implementing regime classifiers, scenario evaluators, stress engines or distribution engines.
- Implementing Strategy, Risk, Paper, Live or broker-order capabilities.
- Merging without explicit human authorization.

## 3. Gate success condition

The gate may be adjudicated as a PASS candidate if the Sprint 5 predecessor is exact and green, DD-89 and related boundaries are adjudicated, negative capabilities are explicit, entry-gate CI and pinned-upstream verification pass, and independent review finds no blocker.

A PASS gate still does not authorize functional implementation.
