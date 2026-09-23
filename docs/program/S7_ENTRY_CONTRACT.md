# Sprint 7 Entry Contract — Risk Engine

## Authority and canonical baseline

```text
SPRINT_6_STATUS = FORMALLY_CLOSED
SPRINT_6_FINAL_VERDICT = PASS
SPRINT_6_FINAL_CANONICAL_HEAD = 58e870925e9a1bf4ccbc0f796610d6297bcc57e2
SPRINT_6_FUNCTIONAL_PR = #85
SPRINT_6_FUNCTIONAL_MERGE_SHA = 0e9438590338e2a322e96306a4dd8cb43d957535

SPRINT_7_ENTRY_GATE_ISSUE = #86
SPRINT_7_CANONICAL_BRANCH = sprint/7-risk-engine
SPRINT_7_ENTRY_GATE_WORK_BRANCH = s7/00-entry-gate
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

STRATEGY_OPERATIONAL_PATH = ABSENT
RISK_OPERATIONAL_PATH = FORBIDDEN_UNTIL_FUNCTIONAL_AUTHORIZATION
ORDER_EXECUTION_PATH = ABSENT
PAPER_TRADING = FORBIDDEN
LIVE_TRADING = FORBIDDEN
REAL_MONEY = FORBIDDEN
BROKER_ACCOUNT_OR_ORDER_API = FORBIDDEN
FINANCIAL_LEDGER_MUTATION = FORBIDDEN
AUTO_FLATTEN = FORBIDDEN
AUTO_CANCEL = FORBIDDEN
NEW_MANDATORY_RUNTIME_DEPENDENCY = FORBIDDEN
ADDITIONAL_RECURRING_COST = ZERO
```

A PASS Entry Gate does not authorize functional Risk Engine implementation.

---

## 1. Mission

Sprint 7 defines the independent Risk Engine boundary required before Paper Trading can exist.

The future S7 functional layer may evaluate a proposed economic change, veto it, and — only after a valid `PERMIT` decision — issue an immutable and strictly bounded `RiskAuthorization`. It may never originate a trade proposal or request an external side effect.

```text
RISK_ENGINE_ROLE = INDEPENDENT_VETO_AND_LIMIT_AUTHORITY
RISK_ENGINE_MAY_NOT = CREATE_STRATEGY_OR_EXECUTION_AUTHORITY

RiskDecision.REJECT != SAFE_HALT
RiskDecision.PERMIT != RiskAuthorization
RiskAuthorization != AuthorizationAllocation
RiskCapacityReservation != MarketExposure
RiskAuthorization != OrderIntent
SAFE_HALT != AUTO_FLATTEN
SAFE_HALT != AUTO_CANCEL
```

Risk-originated sizing means only a **maximum permitted envelope**. It is not Strategy sizing and may never expand the submitted proposal.

---

## 2. Canonical future input boundary

Any future S7 functional run must fail closed unless it is rooted in one immutable `RiskEvaluationBoundary`.

The boundary must bind at minimum:

- immutable subject/proposal identity and digest;
- concrete `TradableInstrument` identity when a financial proposal is evaluated;
- economic direction and units;
- immutable `RiskStateSnapshot` identity and digest;
- immutable `RiskPolicyBundle` identity and digest;
- `as_of_time` / knowledge cutoff;
- source-lineage identities for position, exposure, P&L/daily-loss and drawdown facts used;
- data-quality/freshness state;
- runtime safety/readiness facts consumed by Risk;
- Risk Engine code revision;
- canonical boundary digest.

Risk must not infer a proposal from a model score, Scenario Engine output or market event. The proposal is immutable upstream evidence.

### 2.1 RiskStateSnapshot

A future `RiskStateSnapshot` must keep distinct:

- current recognized position exposure;
- committed/potential exposure;
- risk-capacity reservations;
- worst-case exposure;
- relevant cash/equity/NAV facts when supplied;
- daily-loss facts and their session boundary;
- drawdown state and denominator convention;
- applicable tail-risk evidence references;
- safety/readiness state;
- explicit UNKNOWN / STALE / INCOMPLETE quality.

Absence of a value is never equivalent to zero.

### 2.2 RiskPolicyBundle

Operational limits are versioned policy, not hidden constants in code.

Every applicable policy must bind:

- policy identity/version/digest;
- scope and instrument/portfolio applicability;
- currency/unit;
- effective interval;
- threshold direction;
- hard vs advisory semantics;
- session/timezone rules where applicable;
- missing/stale behavior;
- explicit provenance.

A hard limit is non-compensatory: favorable metrics cannot offset a hard breach.

---

## 3. Decision and authorization semantics

### 3.1 RiskDecision

Canonical decision vocabulary:

```text
RiskDecision = REJECT | PERMIT
```

A decision binds:

- request/boundary identity;
- risk-state snapshot identity;
- policy identity;
- evaluated metrics/limits;
- reasons;
- decision timestamp / as-of semantics;
- deterministic decision digest.

Risk may not silently modify the upstream proposal.

### 3.2 RiskAuthorization

A `PERMIT` that could enable future economic effect requires a distinct immutable `RiskAuthorization`.

Authorization must:

- reference the exact `RiskDecision.PERMIT`;
- reference the exact proposal and risk-state snapshot;
- define the maximum allowed quantity/notional/exposure envelope using explicit units;
- never exceed the upstream proposal;
- bind validity by time, risk-state version/digest, policy version/digest, or a stricter combination;
- expire fail-closed;
- contain no broker-specific order instruction;
- contain no execution side effect.

A `REJECT` never creates an authorization.

### 3.3 Allocation boundary

`AuthorizationAllocation` is downstream of RiskAuthorization and upstream of OrderIntent under ADR 0016. Initial S7 does not create OrderIntent or ExecutionOrder.

The semantic distinction between available capacity, reserved capacity, committed capacity, realized exposure and released capacity is mandatory.

A `RiskAuthorization` **does not reserve capacity by itself**. Any future downstream consumer must create a distinct `AuthorizationAllocation` against then-current capacity before an `OrderIntent` can exist. That allocation step must revalidate authorization validity and prevent aggregate allocation from exceeding available capacity. Physical concurrent locking/reservation and allocation consumption remain deferred until the first downstream composition that can actually consume authorization.

---

## 4. Exposure and capacity

Risk evaluation must use dimensionally valid, explicit exposure components.

At minimum distinguish:

```text
CurrentPositionExposure
CommittedPotentialExposure
RiskCapacityReservation
WorstCaseExposure
```

No cross-currency or cross-unit aggregation is valid without an explicitly governed conversion/normalization rule.

Risk must not fabricate broker margin, buying power or settlement facts. If those facts are material and unavailable, the decision is fail-closed.

---

## 5. Daily loss and drawdown

### 5.1 Daily loss

A daily-loss policy must declare:

- portfolio/account scope;
- currency;
- loss sign convention;
- recognized P&L source identity;
- whether unrealized P&L is included;
- session/trading-day boundary;
- timezone/calendar;
- reset semantics;
- threshold and comparison direction.

Local midnight must not be assumed silently.

### 5.2 Drawdown

Operational drawdown policy must declare:

- equity/NAV/capital series semantics;
- current value and governed peak identity;
- positive denominator convention where a ratio is used;
- as-of time;
- quality/freshness.

UNKNOWN denominator/peak/current value is fail-closed when the metric is required.

---

## 6. Tail-risk boundary

Sprint 6 descriptive tail evidence does not automatically become an operational limit.

```text
SCENARIO_OUTCOME_SET != EMPIRICAL_DISTRIBUTION
TAIL_METRIC != RISK_LIMIT
SCENARIO_WEIGHT != PROBABILITY
```

A future S7 policy may use VaR/ES or another tail metric only when:

- the source is governed empirical/observed evidence;
- sample/tail sufficiency is valid;
- loss direction, tail level and interpolation convention are explicit;
- the operational threshold is predeclared in the RiskPolicyBundle;
- the evidence identity and policy identity are preserved.

Synthetic scenario outcomes may support deterministic stress vetoes but may not be interpreted as empirical probability or VaR/ES samples.

---

## 7. Circuit breakers and fail-safe

A future S7 circuit breaker may latch a risk-restrictive state that rejects new authorizations.

For any restrictive latched state:

- new commitments are fail-closed;
- unlatch requires explicit human confirmation;
- state transition and reason are auditable;
- it does not itself cancel orders;
- it does not itself flatten positions;
- it does not call a broker;
- it does not mutate FinancialLedger.

A Risk Engine may recommend or expose a safety-posture consequence, but it does not silently own the global runtime state machine.

---

## 8. Decisions deliberately still deferred

The Entry Gate does not prematurely decide physical mechanisms whose first material dependency remains Paper/Execution:

- durable operational snapshot/checkpoint format while no durable Risk checkpoint exists;
- automation-vs-human policy for production operational authorities beyond the S7 human-unlatch rule;
- physical process watchdog / production kill-switch implementation;
- concrete order-type / TIF catalog;
- execution idempotency-key scheme;
- cancel/replace protocol;
- WAL / fsync persistence-before-act;
- double-entry vs other physical Ledger model;
- chart of accounts;
- cost-basis methodology;
- physical settlement;
- FX conversion;
- broker margin/buying-power implementation;
- netting mechanism;
- physical FinancialLedger persistence.

Risk may consume immutable qualified facts whose production belongs downstream; it may not invent them.

---

## 9. Determinism, provenance and security

Initial functional S7, if later authorized, must be deterministic for identical immutable inputs and policies.

Core Risk Engine must not introduce:

- network clients;
- broker/account/order SDK usage;
- subprocess spawning;
- dynamic eval/exec;
- unsafe pickle/joblib deserialization;
- untrusted dynamic imports;
- wall-clock-dependent hidden policy;
- RNG-based risk decisions;
- model retraining or Strategy selection.

Every boundary, state snapshot, policy, decision, authorization and circuit-state artifact requires deterministic provenance/digest semantics.

---

## 10. Future functional acceptance contract

Before a future S7 functional closure:

```text
S7_PACKAGE_STATEMENT_COVERAGE = 100%
S7_PACKAGE_BRANCH_COVERAGE = 100%

S7_DEDICATED_TESTS = PASS
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
OPEN_BLOCKERS = 0
```

Required adversarial tests must include at least:

- REJECT cannot create authorization;
- PERMIT without a valid authorization cannot enable downstream commitment;
- authorization cannot exceed proposal;
- expired/stale authorization rejected;
- changed risk-state/policy invalidates authorization when bound;
- UNKNOWN/STALE/INCOMPLETE critical state fails closed;
- hard-limit breach non-compensatory;
- capacity reservation distinct from exposure;
- daily-loss session/reset semantics explicit;
- drawdown denominator/peak unknown fails closed;
- synthetic scenarios rejected as empirical VaR/ES samples;
- circuit breaker latch blocks new authorizations;
- unlatch requires explicit human confirmation;
- SAFE_HALT causes no auto-flatten/cancel;
- no order/broker/Ledger side effect;
- deterministic repeated-run equivalence.

---

## 11. Entry Gate boundary

This Entry Gate authorizes governance materialization only.

```text
S7_ENTRY_GATE_CANDIDATE = PASS
S7_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
S7_ENTRY_GATE_MERGE = COMPLETED_BY_EXPLICIT_HUMAN_AUTHORIZATION

PAPER_TRADING = NO
LIVE_TRADING = NO
REAL_MONEY = NO
```
