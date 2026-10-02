# S7-FULL-RISK-ENGINE — Functional implementation workstream

```text
SPRINT = 7
ISSUE = #88
CANONICAL_BRANCH = sprint/7-risk-engine
WORK_BRANCH = s7/01-full-risk-engine
CANONICAL_BASE_SHA = bef92694314d5a5555a3e38abc588b42561411b3
FUNCTIONAL_AUTHORIZATION_DATE = 2026-09-26

FUNCTIONAL_IMPLEMENTATION = AUTHORIZED
MERGE = FORBIDDEN_WITHOUT_SEPARATE_HUMAN_AUTHORIZATION

STRATEGY_OPERATIONAL_PATH = ABSENT
ORDER_EXECUTION_PATH = ABSENT
BROKER_ACCOUNT_OR_ORDER_API = FORBIDDEN
FINANCIAL_LEDGER_MUTATION = FORBIDDEN
PAPER_TRADING = NO
LIVE_TRADING = NO
REAL_MONEY = NO
```

## Authorized implementation

Implement the canonical S7 Risk Engine as a deterministic, side-effect-free decision layer:

- immutable `RiskProposal` evidence;
- immutable `RiskStateSnapshot`;
- immutable/versioned `RiskPolicyBundle`;
- verified `RiskEvaluationBoundary`;
- `RiskDecision.REJECT | PERMIT`;
- engine-issued immutable bounded `RiskAuthorization`;
- exposure/capacity evaluation;
- daily-loss/drawdown/tail limits;
- hard-limit non-compensation;
- UNKNOWN/STALE/INCOMPLETE fail-closed;
- circuit latch with human-confirmed unlatch;
- deterministic provenance/digests;
- authorization validity checks;
- S7 boundary/security checker;
- dedicated adversarial tests and 100% package statement/branch coverage.

## Strict exclusions

This workstream must not create:

- StrategyDecision or TradeIntent generation;
- AuthorizationAllocation consumption/locking;
- OrderIntent, OrderPlan or ExecutionOrder;
- broker/account/order side effects;
- FinancialLedger mutation;
- Paper or Live Trading;
- real-money capability;
- auto-flatten or auto-cancel;
- production watchdog/kill switch;
- network clients, subprocess, dynamic eval/exec or unsafe deserialization;
- model retraining or strategy selection;
- new mandatory runtime dependencies or paid services.

## Acceptance boundary

```text
S7_DEDICATED_TESTS = PASS
S7_PACKAGE_STATEMENT_COVERAGE = 100%
S7_PACKAGE_BRANCH_COVERAGE = 100%
FULL_REGRESSION_S1_TO_S6 = PASS
S7_BOUNDARY_VERIFIER = PASS
FOUNDATION_INTEGRITY = PASS
RUFF = PASS
MYPY_STRICT = PASS
COMPILE = PASS
DEPENDENCY_AUDIT = PASS
DIFF_CHECK = PASS
PINNED_UPSTREAM = PASS
EXACT_HEAD_CI = PASS
INDEPENDENT_REAUDIT = PASS
OPEN_BLOCKERS = 0
```

A passing candidate is not merge authority. Merge requires a new explicit human authorization.


## Exact-head functional candidate validation

```text
S7_FUNCTIONAL_VALIDATED_CODE_HEAD = c1e33bd3615e311f259d59055349596667978dec
S7_FUNCTIONAL_PYTHON_CI_RUN = 36939849626
S7_FUNCTIONAL_ENTRY_GATE_CI_RUN = 36939849827
S7_FUNCTIONAL_PINNED_UPSTREAM_RUN = 36939849524
S7_FUNCTIONAL_FULL_REGRESSION = 1127_PASS
S7_FUNCTIONAL_PACKAGE_STATEMENT_COVERAGE = 100%
S7_FUNCTIONAL_PACKAGE_BRANCH_COVERAGE = 100%
S7_FUNCTIONAL_CANDIDATE = PASS_CANDIDATE
OPEN_FUNCTIONAL_CANDIDATE_BLOCKERS = 0

MERGE = FORBIDDEN_WITHOUT_SEPARATE_HUMAN_AUTHORIZATION
SPRINT_8 = NOT_AUTHORIZED
PAPER_TRADING = NO
LIVE_TRADING = NO
REAL_MONEY = NO
```

The next boundary is exact-head PR validation and independent re-audit. No merge is authorized by this candidate state.
