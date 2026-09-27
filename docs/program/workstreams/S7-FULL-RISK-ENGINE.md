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
