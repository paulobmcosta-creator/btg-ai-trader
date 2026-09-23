# Sprint 7 Capability Matrix — Risk Engine

## 1. Entry Gate capabilities

| ID | Capability | Required evidence | Candidate state |
|---|---|---|---|
| **S7-EG-AC-01** | Exact formally closed Sprint 6 predecessor | canonical head `58e870925e9a1bf4ccbc0f796610d6297bcc57e2` | PASS |
| **S7-EG-AC-02** | Sprint 6 final verdict PASS / blockers zero | S6 canonical governance | PASS |
| **S7-EG-AC-03** | S7 issue and isolated branches | Issue #86; `sprint/7-risk-engine`; `s7/00-entry-gate` | PASS |
| **S7-EG-AC-04** | ADR 0016 authority chain preserved | RiskDecision / RiskAuthorization separation | PASS |
| **S7-EG-AC-05** | ADR 0022 exposure semantics preserved | current/committed/reservation/worst-case separation | PASS |
| **S7-EG-AC-06** | SAFE_HALT no-auto-flatten invariant preserved | ADR 0020 | PASS |
| **S7-EG-AC-07** | DD-38 adjudicated | human-confirmed unlatch | PASS |
| **S7-EG-AC-08** | DD-64 adjudicated | aggregate exposure/reservation semantics | PASS |
| **S7-EG-AC-09** | DD-107 adjudicated | policy-local predeclared tail limits | PASS |
| **S7-EG-AC-10** | DD-121 adjudicated | policy-local exposure/daily-loss limits | PASS |
| **S7-EG-AC-11** | S8/S9-dependent mechanisms remain deferred | DD-27/DD-34/DD-39 and S7-owner deferred decisions | PASS |
| **S7-EG-AC-12** | No functional Risk code/tests | exact diff vs S6 head | PASS |
| **S7-EG-AC-13** | No dependency change | exact diff vs S6 head | PASS |
| **S7-EG-AC-14** | Frozen Foundation | post-merge Entry Gate CI `35909666368` | PASS |
| **S7-EG-AC-15** | Pinned upstream | post-merge run `35909666371` | PASS |
| **S7-EG-AC-16** | Independent review | review `5295358543` on PR head `0aac73fc...` | PASS |

## 2. Functional positive capabilities required after a future explicit authorization

| ID | Required capability | Governing source | Entry status |
|---|---|---|---|
| **S7-AC-01** | Immutable RiskEvaluationBoundary | S7-D-04 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-02** | Immutable RiskStateSnapshot | ADR 0022; S7-D-05 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-03** | Immutable/versioned RiskPolicyBundle | S7-D-08 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-04** | RiskDecision.REJECT / PERMIT only | ADR 0016; S7-D-02 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-05** | Distinct immutable RiskAuthorization | ADR 0016; S7-D-03 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-06** | Authorization cannot exceed proposal | S7-D-06 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-07** | Authorization validity/expiry bound to state/policy/time | ADR 0007/0016; S7-D-07 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-08** | Explicit reasons/metrics/policy provenance | ADR 0016 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-09** | Current position exposure | ADR 0022 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-10** | Committed potential exposure | ADR 0022 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-11** | RiskCapacityReservation semantics | ADR 0022; DD-64 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-12** | Worst-case exposure evaluation | ADR 0022; DD-64 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-13** | Explicit unit/currency dimensional validation | S7-D-05/08 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-14** | UNKNOWN/STALE/INCOMPLETE fail-closed | ADR 0022; S7-D-10 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-15** | Predeclared exposure limit policies | DD-121 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-16** | Predeclared daily-loss policies | DD-121; S7-D-11 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-17** | Explicit daily-loss session/timezone/reset semantics | S7-D-11 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-18** | Predeclared drawdown policies | S7-D-12 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-19** | Drawdown denominator/peak validity | S7-D-12 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-20** | Governed empirical tail-risk policy | DD-107; S7-D-13 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-21** | Synthetic-vs-empirical tail separation | S7-D-14 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-22** | Hard-limit non-compensation | S7-D-09 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-23** | Risk-only maximum sizing envelope | S7-D-06 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-24** | Restrictive circuit-breaker latch | S7-D-17 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-25** | Human-confirmed unlatch | DD-38; S7-D-18 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-26** | SAFE_HALT blocks new commitment only | ADR 0020; S7-D-19 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-27** | Deterministic repeated-run equivalence | S7-D-23 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-28** | Content-addressed provenance | S7-D-24 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-29** | No runtime policy tuning | S7-D-22 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-30** | No Strategy merit attribution from Risk veto | 0E-F F-HQI-04; S7-D-20 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-31** | Dedicated S7 boundary/security verifier | S7-D-25 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-32** | Adversarial authority-chain tests | ADR 0016 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-33** | Adversarial stale/unknown-state tests | ADR 0022 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-34** | Adversarial limits/circuit-breaker tests | DD-38/DD-121 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-35** | S7 package 100% statement coverage | S7-D-27 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-36** | S7 package 100% branch coverage | S7-D-27 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-37** | Full S1–S6 regression | program governance | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-38** | Exact-head CI and pinned upstream | program governance | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-39** | Zero additional recurring cost | project constraint | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-40** | No new mandatory runtime dependency | S7-D-26 | REQUIRED_AFTER_AUTHORIZATION |
| **S7-AC-41** | RiskAuthorization alone does not reserve capacity; downstream allocation revalidates current capacity | ADR 0016; S7-D-16 | REQUIRED_AFTER_AUTHORIZATION |

## 3. Negative capabilities that must remain absent

| ID | Prohibited capability | Required state |
|---|---|---|
| **S7-NC-01** | Strategy/Signal proposal generation | ABSENT |
| **S7-NC-02** | Risk creating or mutating TradeIntent | ABSENT |
| **S7-NC-03** | Risk expanding proposal size/exposure | ABSENT |
| **S7-NC-04** | REJECT creating RiskAuthorization | ABSENT |
| **S7-NC-05** | PERMIT treated as RiskAuthorization | ABSENT |
| **S7-NC-06** | RiskAuthorization treated as AuthorizationAllocation | ABSENT |
| **S7-NC-07** | OrderIntent / OrderPlan / ExecutionOrder | ABSENT |
| **S7-NC-08** | Broker/account/order API | ABSENT |
| **S7-NC-09** | Paper Trading | ABSENT |
| **S7-NC-10** | Live Trading | ABSENT |
| **S7-NC-11** | Real-money authority | ABSENT |
| **S7-NC-12** | FinancialLedger mutation | ABSENT |
| **S7-NC-13** | Fill/accounting/P&L engine | ABSENT |
| **S7-NC-14** | Broker margin/buying-power fabrication | ABSENT |
| **S7-NC-15** | Silent FX conversion | ABSENT |
| **S7-NC-16** | UNKNOWN/STALE/INCOMPLETE converted to zero/favorable | ABSENT |
| **S7-NC-17** | Hidden/unversioned risk limits | ABSENT |
| **S7-NC-18** | Compensating a hard breach with another metric | ABSENT |
| **S7-NC-19** | Synthetic scenario outcomes used as empirical VaR/ES | ABSENT |
| **S7-NC-20** | Auto-flatten from SAFE_HALT/circuit breaker | ABSENT |
| **S7-NC-21** | Auto-cancel from SAFE_HALT/circuit breaker | ABSENT |
| **S7-NC-22** | Automatic unlatch of restrictive risk state | ABSENT |
| **S7-NC-23** | Physical execution-facing capacity locking in initial core | ABSENT |
| **S7-NC-24** | Network client in core Risk Engine | ABSENT |
| **S7-NC-25** | Subprocess spawning in core Risk Engine | ABSENT |
| **S7-NC-26** | Unsafe deserialization/dynamic eval/exec | ABSENT |
| **S7-NC-27** | RNG-dependent risk decision | ABSENT |
| **S7-NC-28** | Model retraining / Strategy selection | ABSENT |
| **S7-NC-29** | Paid external risk service | ABSENT |
| **S7-NC-30** | Functional S7 implementation before explicit authorization | ABSENT |
| **S7-NC-31** | RiskAuthorization treated as capacity reservation / consumed without AuthorizationAllocation | ABSENT |


## 4. Canonical Entry Gate closure

```text
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

S7_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
PROMOTION_TO_S7_FUNCTIONAL_IMPLEMENTATION = NO
```
