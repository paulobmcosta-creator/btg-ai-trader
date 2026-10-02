# Sprint 8 — Decision Register

## 1. Governing sources

This register applies Protocol 0E-G, ADR 0016, ADR 0018, ADR 0019, ADR 0020, ADR 0022, the frozen 0F-B deferred-decision register, and the formally closed Sprint 7 boundary.

Historical ADRs and the 0F-B snapshot are not rewritten. This document records Sprint 8 adjudication only.

## 2. Root entry blockers

| ID | Finding | State | Consequence |
|---|---|---|---|
| **S8-B01** | Operational Signal/Strategy → `StrategyDecision` → `TradeIntent` path is absent from the canonical source tree | OPEN | Confirmatory Paper cannot exercise the exact real decision chain required by 0E-G |
| **S8-B02** | No exact candidate has canonical `PAPER_ELIGIBLE` adjudication plus candidate freeze | OPEN | Confirmatory Paper start is forbidden |

## 3. Sprint 8 local decisions

### S8-D-01 — Paper is prospective and non-funded
Paper consumes contemporaneous market evidence and real internal decisions, but S8 has no real broker/account/order side effect and no real-money authority.

### S8-D-02 — Paper does not own Strategy
Paper infrastructure may consume an exact Strategy/TradeIntent lineage but may not synthesize an embedded strategy to compensate for an absent upstream operational Strategy path.

### S8-D-03 — Exact candidate identity is mandatory
A confirmatory Paper run may start only for a specifically versioned candidate that has a canonical `PAPER_ELIGIBLE` adjudication and frozen quantitatively material configuration.

### S8-D-04 — Risk is mandatory and non-bypassable
All proposed economic changes in the canonical Paper path pass through the S7 Risk Engine. Paper cannot disable, weaken or substitute Risk to increase trade count.

### S8-D-05 — AuthorizationAllocation becomes materially triggered in S8
A future S8 consumer of `RiskAuthorization` must revalidate current authorization/state/policy/time and atomically prevent aggregate allocation from exceeding remaining capacity. The physical locking mechanism must be resolved before functional implementation.

### S8-D-06 — Paper accounting is explicitly fictional
S8 uses an isolated Paper accounting/projection surface. It does not mutate the future canonical `FinancialLedger` and cannot be interpreted as external account truth.

### S8-D-07 — Reuse before reimplementation
Where applicable, the future Paper execution/accounting design should reuse validated Sprint 3 deterministic economic semantics rather than silently create a second incompatible cost/fill/P&L model. Exact reuse boundaries require functional design review.

### S8-D-08 — Paper policy parameters are candidate-specific and predeclared
No universal number of trading days, opportunities, discrepancy tolerance, latency tolerance, slippage tolerance or emergency-stop threshold is invented at this Entry Gate. Required values must be fixed before confirmatory Paper begins for the exact candidate and claim.

### S8-D-09 — Material adaptation consumes Paper independence
A material candidate/strategy/execution-policy change informed by Paper evidence closes the current confirmatory partition and starts a new lineage after applicable upstream revalidation.

### S8-D-10 — Paper discrepancies are evidence
Material discrepancies against ex-ante Backtest expectations are append-only evidence. They are not edited away or retroactively calibrated inside the same confirmatory partition.

### S8-D-11 — Paper success does not imply Live readiness
Paper PASS, when it eventually exists, satisfies only the Paper evidence stage. It does not establish recovery, broker connectivity, operational readiness or live authorization.

### S8-D-12 — PaperGateAssessment is mandatory
A confirmatory Paper period closes only through an explicit, provenance-bound `PaperGateAssessment`.

## 4. Deferred-decision adjudication

| DD | Topic | Sprint 8 adjudication | Gate consequence |
|---|---|---|---|
| **DD-06** | Concrete order types / TIF | `TRIGGERED_PENDING_EXACT_CANDIDATE_EXECUTION_SPEC` | Must be explicit before functional Paper can exercise order planning |
| **DD-07** | Physical locking / concurrent risk-capacity reservation | `TRIGGERED_MUST_RESOLVE_BEFORE_FUNCTIONAL_AUTHORIZATION` | First downstream capacity consumer is S8 |
| **DD-08** | Idempotency keys for intents/executions | `TRIGGERED_MUST_RESOLVE_BEFORE_FUNCTIONAL_AUTHORIZATION` | Paper retries/evidence must not duplicate logical effects |
| **DD-11** | Cancel/replace protocol | `CONDITIONAL_ON_CANDIDATE_ORDER_LIFECYCLE` | Must be predeclared if candidate/order plan requires it |
| **DD-23** | WAL | `NOT_TRIGGERED_AS_REAL_ECONOMIC_SAFETY_GATE` | S8 has no external economic commitment; Paper evidence durability remains required |
| **DD-24** | fsync/flush persist-before-act | `NOT_TRIGGERED_AS_REAL_ECONOMIC_SAFETY_GATE` | No real external commitment in S8 |
| **DD-44** | Canonical Ledger accounting model | `NOT_USED_FOR_PAPER_CANONICAL_FINANCIAL_RECOGNITION` | Paper accounting remains isolated/fictional |
| **DD-45** | Canonical chart of accounts | `NOT_TRIGGERED_BY_NONFUNDED_PAPER` | No canonical financial ledger in S8 |
| **DD-46** | Cost-basis methodology | `PAPER_METHOD_MUST_BE_EXPLICIT_AND_COMPARABLE_TO_VALIDATED_BACKTEST_SEMANTICS` | Candidate-specific Paper accounting contract required |
| **DD-47** | P&L / valuation methodology | `PAPER_METHOD_MUST_BE_EXPLICIT_AND_PROVENANCE_BOUND` | Required for Backtest↔Paper comparison, without claiming real account truth |
| **DD-48** | Physical settlement | `NOT_TRIGGERED_NO_REAL_SETTLEMENT` | S8 is non-funded |
| **DD-49** | FX conversion | `CONDITIONAL_ON_CANDIDATE_CURRENCY_SCOPE` | Silent conversion forbidden |
| **DD-50** | Broker margin / buying power | `NO_BROKER_TRUTH_IN_S8` | Fictional constraints, if used, must be explicitly labeled simulation |
| **DD-51** | Netting | `PENDING_EXACT_CANDIDATE_AND_PAPER_POSITION_CONTRACT` | Cannot be finalized before candidate freeze |
| **DD-52** | Broker account topology | `NOT_TRIGGERED_NONFUNDED_PAPER` | Use internal Paper portfolio identity only |
| **DD-53** | Physical canonical Ledger persistence/query | `NOT_TRIGGERED_FOR_CANONICAL_FINANCIAL_LEDGER` | Separate Paper evidence/accounting storage only |
| **DD-64** | Aggregate exposure reservation tracking | `TRIGGERED_MUST_RESOLVE_WITH_AUTHORIZATION_ALLOCATION` | Must prevent risk-capacity double-spend |
| **DD-113** | Model drift / strategy decay criteria | `TRIGGERED_CANDIDATE_SPECIFIC_PENDING_S8_B02` | Must be predeclared if material to Paper claim |
| **DD-115** | Minimum Paper duration / opportunities | `TRIGGERED_CANDIDATE_SPECIFIC_PREDECLARATION_REQUIRED` | No universal number at gate |
| **DD-116** | Backtest↔Paper discrepancy tolerance | `TRIGGERED_CANDIDATE_SPECIFIC_PREDECLARATION_REQUIRED` | Must be set ex ante |
| **DD-117** | Paper latency / slippage tolerances | `TRIGGERED_CANDIDATE_SPECIFIC_PREDECLARATION_REQUIRED` | Must be set ex ante |
| **DD-118** | Promotion expiry | `DEFER_TO_S11_PER_0F_B` | No premature production-promotion policy |
| **DD-119** | Emergency/stopping criteria in Paper | `TRIGGERED_CANDIDATE_SPECIFIC_PREDECLARATION_REQUIRED` | Safety stop dominates sample sufficiency |
| **DD-120** | Physical Paper audit/report format | `IMPLEMENTATION_DETAIL_BEFORE_CONFIRMATORY_RUN` | Semantic `PaperGateAssessment` is mandatory; physical format remains open |

## 5. Current conclusion

```text
S8_ENTRY_GATE_CANDIDATE = CHANGES_REQUIRED
ROOT_BLOCKERS = S8-B01,S8-B02
OPEN_S8_ENTRY_GATE_BLOCKERS = 2
PROMOTION_TO_S8_FUNCTIONAL_IMPLEMENTATION = NO
```
