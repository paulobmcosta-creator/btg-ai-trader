# S8-ENTRY-GATE — Paper Trader Governance Packet

```text
SPRINT = 8
WORK_MODE = ENTRY_GATE_ONLY
ISSUE = #93
CANONICAL_BRANCH = sprint/8-paper-trader
WORK_BRANCH = s8/00-entry-gate
CANONICAL_PREDECESSOR_BRANCH_HEAD = 1226aea13bc8a99303b8c008883fd36068247829
S7_FUNCTIONAL_CANONICAL_HEAD = e379e9b34a8b607e86165bd3336d23fcd9406259

ENTRY_GATE_VERDICT = CHANGES_REQUIRED
ROOT_BLOCKERS = S8-B01,S8-B02
FUNCTIONAL_IMPLEMENTATION = FORBIDDEN
PAPER_CONFIRMATORY_RUN = FORBIDDEN
NEW_RUNTIME_DEPENDENCIES = FORBIDDEN
MERGE = NOT_AUTHORIZED
```

## 1. Authorized tasks

1. Materialize the S8 Entry Contract, Decision Register, Capability Matrix, sprint document and checkpoint.
2. Bind Protocol 0E-G and the relevant ADR chain without rewriting historical snapshots.
3. Adjudicate or explicitly bound S8-triggered deferred decisions.
4. Record objective predecessor gaps as blockers rather than invent missing capabilities.
5. Add S8 Entry Gate CI and extend pinned-upstream triggers.
6. Open a PR from `s8/00-entry-gate` to `sprint/8-paper-trader`.
7. Obtain exact-head CI and pinned-upstream evidence.
8. Request independent review.
9. Stop before merge without explicit human authorization.

## 2. Forbidden tasks

- adding a functional Paper Trader package;
- adding functional S8 tests;
- embedding or inventing Strategy/Signal behavior inside Paper;
- declaring any candidate PAPER_ELIGIBLE without the required 0E-G evidence;
- creating a real broker/account/order adapter;
- transmitting, altering or cancelling real orders;
- bypassing or weakening Risk;
- mutating canonical FinancialLedger;
- Live Trading;
- real money;
- paid recurring services;
- merging without explicit human authorization.

## 3. Gate success semantics

This Entry Gate is intentionally a `CHANGES_REQUIRED` candidate.

CI PASS means the governance packet accurately captures the blocked state and preserves all negative capabilities. CI PASS does **not** mean functional S8 is authorized.

Promotion requires separate remediation of S8-B01 and S8-B02, subsequent independent review, and explicit human authorization.
