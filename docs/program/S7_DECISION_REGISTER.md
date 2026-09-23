# Sprint 7 Decision Register — Risk Engine

Foundation IDs from `docs/foundation/0F-B_deferred_decision_register.md` are preserved exactly.

## 1. Foundation decisions activated or constrained at the S7 boundary

| ID | Decision | Sprint 7 adjudication | Gate consequence |
|---|---|---|---|
| **DD-07** | Physical locking / concurrent risk-capacity reservation | `SEMANTIC_RESERVATION_TRIGGERED_PHYSICAL_LOCKING_DEFERRED_TO_S8` | S7 defines capacity/reservation semantics; no I/O locking in Entry Gate or initial pure core. |
| **DD-27** | Physical format of operational-state snapshots | `NOT_TRIGGERED_NO_DURABLE_S7_CHECKPOINT` | S7 may use immutable in-memory RiskStateSnapshot values; no durable checkpoint/storage format is introduced. |
| **DD-34** | Automation vs human intervention for operational authorities | `CONSTRAINED_NOT_TRIGGERED_FOR_PRODUCTION_AUTOMATION` | S7 fixes human confirmation for restrictive unlatch only; broader production automation remains S9. |
| **DD-37** | Safety transition thresholds / degradation policies | `RISK_SPECIFIC_POLICY_LOCAL` | Risk thresholds are explicit policy; no hidden global runtime transition automation. |
| **DD-38** | Human confirmation to unlatch restrictive posture | `TRIGGERED_REQUIRED` | Restrictive risk latch requires explicit human confirmation to unlatch. |
| **DD-39** | Physical process watchdog / emergency kill switch | `NOT_TRIGGERED_DEFER_TO_S9` | S7 circuit breaker is a logical authorization gate, not a process watchdog or external kill switch. |
| **DD-64** | Aggregate exposure reservation/tracking model | `TRIGGERED_AND_DESIGN_ADJUDICATED` | Distinguish current, committed/potential, reserved capacity and worst-case exposure. |
| **DD-107** | Tail-risk operational cutoffs (VaR/ES) | `TRIGGERED_POLICY_LOCAL_PREDECLARED` | No universal project constant; each RiskPolicyBundle declares tail level and limit with governed empirical evidence. |
| **DD-121** | Quantitative exposure and maximum daily-loss limits | `TRIGGERED_POLICY_LOCAL_PREDECLARED` | Limits require explicit scope, currency/unit, session/timezone and hard/advisory semantics. |

## 2. S7-owner decisions intentionally not triggered by the initial Risk core

| ID | Decision | S7 gate state | Reason |
|---|---|---|---|
| **DD-06** | Concrete order types / TIF | `DEFER_TO_S8` | No OrderIntent/ExecutionOrder in S7. |
| **DD-08** | Execution/intent idempotency-key scheme | `DEFER_TO_S8` | No execution side effect. |
| **DD-11** | Cancel/replace protocol | `DEFER_TO_S8` | No order management. |
| **DD-23** | WAL for pre-action durability | `DEFER_TO_S8` | No economic side effect. |
| **DD-24** | fsync/flush persistence-before-act | `DEFER_TO_S8` | No economic side effect. |
| **DD-44** | Physical Ledger accounting model | `DEFER_TO_S8` | S7 does not mutate FinancialLedger. |
| **DD-45** | Chart of accounts | `DEFER_TO_S8` | No Ledger postings. |
| **DD-46** | Cost-basis methodology | `DEFER_TO_S8` | Risk consumes explicit qualified facts, not accounting implementation. |
| **DD-47** | Intraday P&L / valuation methodology | `DEFER_PHYSICAL_METHOD_TO_S8` | S7 requires provenance/semantics for supplied P&L facts but does not create the financial projection engine. |
| **DD-48** | Settlement rules | `DEFER_TO_S8` | No settlement composition. |
| **DD-49** | FX conversion | `DEFER_TO_S8` | Initial S7 does not silently convert currencies. |
| **DD-50** | Broker margin / buying power | `DEFER_TO_S8` | No broker/account integration. |
| **DD-51** | Position netting | `DEFER_TO_S8` | No execution/account position engine. |
| **DD-53** | Physical Ledger persistence/query | `DEFER_TO_S8` | FinancialLedger mutation is forbidden. |

## 3. Sprint 7 local decisions

### S7-D-01 — Risk is independent veto authority
Risk may reject or constrain a submitted proposal. It may not create a proposal, StrategyDecision, TradeIntent, OrderIntent or ExecutionOrder.

### S7-D-02 — Canonical decision vocabulary
`RiskDecision = REJECT | PERMIT`. Historical APPROVE_WITH_LIMITS semantics are represented by PERMIT plus a distinct bounded RiskAuthorization.

### S7-D-03 — PERMIT and authorization are distinct
A PERMIT that can enable future commitment requires explicit immutable RiskAuthorization. REJECT never creates authorization.

### S7-D-04 — RiskEvaluationBoundary is mandatory
Every evaluation binds immutable proposal/subject identity, risk-state snapshot, policy, as-of time, quality and code revision.

### S7-D-05 — RiskStateSnapshot preserves semantic separation
Current position exposure, committed potential exposure, risk-capacity reservations and worst-case exposure remain distinct.

### S7-D-06 — Risk may only tighten
RiskAuthorization never exceeds the upstream proposal. Risk cannot reverse direction or create new economic exposure.

### S7-D-07 — Authorization validity is fail-closed
Authorization expires by explicit time/state/policy validity; stale or mismatched evidence invalidates it.

### S7-D-08 — Operational limits are policy, not hidden code constants
Exposure, daily loss, drawdown, tail and concentration limits are explicit versioned policy with units and applicability.

### S7-D-09 — Hard-limit breaches are non-compensatory
No favorable metric offsets a hard risk-policy breach.

### S7-D-10 — UNKNOWN remains UNKNOWN
Missing/stale/incomplete critical risk state cannot be treated as zero or favorable.

### S7-D-11 — Daily-loss boundaries are explicit
Currency, P&L source, inclusion semantics, session/trading-day boundary, timezone and reset rule are mandatory.

### S7-D-12 — Drawdown boundaries are explicit
Peak/current value, denominator convention, source identity, ordering and freshness must be valid before a drawdown limit is used.

### S7-D-13 — Tail-risk evidence remains governed
VaR/ES operational use requires governed empirical evidence with sufficient sample/tail support and predeclared policy.

### S7-D-14 — Synthetic stress is not empirical probability
ScenarioOutcomeSet may trigger deterministic stress veto but cannot be a probability/VaR/ES sample.

### S7-D-15 — Capacity reservation is not market exposure
RiskCapacityReservation consumes risk budget but is not PositionExposure.

### S7-D-16 — Authorization is not a capacity reservation
RiskAuthorization alone consumes no capacity reservation. A future AuthorizationAllocation must revalidate authorization and then reserve capacity against the current state before OrderIntent can exist. Physical concurrent allocation locking is deferred to the first downstream execution-capable composition.

### S7-D-17 — Restrictive circuit states latch
A hard risk circuit may block new authorizations until an explicit governed unlatch event.

### S7-D-18 — Human confirmation is required to unlatch
Initial restrictive unlatch requires explicit human confirmation. No automatic time-only unlatch.

### S7-D-19 — SAFE_HALT is not an economic action
SAFE_HALT blocks new commitments but does not auto-flatten, auto-cancel or call a broker.

### S7-D-20 — Risk does not own Strategy merit
Downstream Risk vetoes cannot be credited as upstream Strategy quality.

### S7-D-21 — Risk does not invent financial facts
Risk consumes provenance-bound risk facts; it does not implement FinancialLedger, fill recognition, P&L accounting or broker truth.

### S7-D-22 — No policy tuning inside runtime Risk
Risk Engine does not tune limits from the same runtime outcomes it judges.

### S7-D-23 — Deterministic initial core
Identical immutable state + policy + proposal yields identical decision/authorization. Initial S7 has no RNG.

### S7-D-24 — Content-addressed provenance
Boundary, policy, risk state, decision, authorization and circuit-state artifacts require deterministic identities/digests.

### S7-D-25 — No side-effect surface
Initial core has no network, broker/account/order API, subprocess, unsafe deserialization, dynamic eval/exec or FinancialLedger mutation.

### S7-D-26 — Zero recurring cost / no new mandatory runtime dependency
The initial Risk Engine must remain dependency-light and introduce no paid service.

### S7-D-27 — Future S7 package quality gate is 100% statement and branch coverage
Closure requires dedicated adversarial tests, full regression S1–S6, strict typing, lint, compile, dependency and exact-head gates.

### S7-D-28 — Paper/Live promotion is separate
S7 closure cannot authorize Sprint 8 Paper Trading automatically.

## 4. Explicitly unresolved by this Entry Gate

The gate does not choose universal monetary loss limits, universal exposure limits, universal drawdown percentages, universal VaR/ES levels, broker margin rules, strategy sizing rules, execution order types or production kill-switch wiring.

Those values/mechanisms require the first material policy/deployment context and separate authorization.
