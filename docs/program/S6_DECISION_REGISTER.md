# Sprint 6 Decision Register — Scenario Engine

This register adjudicates decisions whose first material dependency occurs at the Sprint 6 Scenario Engine boundary. Foundation IDs from `docs/foundation/0F-B_deferred_decision_register.md` are preserved exactly and are not renumbered.

## 1. Foundation decisions activated or constrained by Sprint 6

| ID | Decision | Sprint 6 adjudication | Scope |
|---|---|---|---|
| **DD-89** | Algorithms for market-regime segmentation and detection | `TRIGGERED_AND_DESIGN_ADJUDICATED` — initial family is deterministic threshold classification over explicitly supplied causal observations. Thresholds are fixed ex ante or fit only in development and frozen before evaluation. Retrospective segmentation is `EXPLORATORY_ONLY`. | Regime detection |
| **DD-108** | Parameter grid for sensitivity and cost perturbation | `TRIGGERED_FOR_S6_SCOPE_DESIGN` — finite predeclared canonical deterministic grids; shock magnitudes remain experiment-local. | Scenario/stress grid |
| **DD-91** | Numeric stability thresholds | `CANONICAL_DEFERRED` — factual heterogeneity may be reported; no universal pass/fail threshold. | Stability |
| **DD-100** | Formal estimand for each study | `EXPERIMENT_LOCAL` — every analysis declares population/estimand, baseline and scope. | Study contract |
| **DD-101** | Primary/secondary evaluation metrics | `EXPERIMENT_LOCAL_PREDECLARED` — metrics and directions are fixed in the ScenarioDispositionPolicy before evaluated evidence is inspected. | Metrics |
| **DD-102** | Statistical significance levels and confidence intervals | `NOT_TRIGGERED_AND_DEFERRED` — initial S6 remains deterministic/descriptive. | Inference |
| **DD-103** | Inferential methodology | `NOT_TRIGGERED_AND_DEFERRED` — no new frequentist, Bayesian or bootstrap inference engine. | Inference |
| **DD-104** | Temporal bootstrap block length | `NOT_TRIGGERED_AND_DEFERRED` — bootstrap is outside initial S6. | Resampling |
| **DD-105** | Multiplicity-control methods | `DEFERRED_WITH_MANDATORY_SEARCH_HISTORY` — complete search history and protected-evidence consumption are mandatory; formal FWER/FDR methods remain deferred. | Multiplicity |
| **DD-107** | Tail-risk operational thresholds | `NOT_TRIGGERED_AND_DEFERRED_TO_S7` — S6 may calculate governed descriptive tail metrics only from ObservedSeries; no operational limits. | Risk |
| **DD-110** | Minimum calibration/discrimination thresholds | `NOT_TRIGGERED` — model promotion remains outside S6. | ML |
| **DD-111** | Strategy activation thresholds and sizing | `NOT_TRIGGERED_AND_DEFERRED` — Strategy/sizing remain absent. | Strategy/Risk |
| **DD-113** | Quantitative model-drift / strategy-decay criteria | `NOT_TRIGGERED_AND_DEFERRED` — regime analysis is not a drift daemon. | Monitoring |
| **DD-13 / DD-14** | RNG and seed governance | `NOT_TRIGGERED_BY_INITIAL_S6_SCOPE` — initial S6 has no Monte Carlo/bootstrap/random scenario generation. | RNG |

## 2. Sprint 6 local decisions

### S6-D-01 — Research-only scenario authority
Scenario artifacts are research evidence only and cannot create trading, risk or financial authority.

### S6-D-02 — Causal and retrospective regime semantics are distinct
A regime supporting a causal claim must be point-in-time. Retrospective segmentation remains `EXPLORATORY_ONLY` for that evidence lineage.

### S6-D-03 — Canonical initial regime algorithm
Initial regime classification is deterministic thresholding over explicitly supplied causal observations. Adaptive clustering and indicator engineering are outside initial S6.

### S6-D-04 — Development-only fitting of learned thresholds
Any data-estimated threshold is fit only in the declared development domain and frozen before evaluation.

### S6-D-05 — Post-hoc regimes cannot repair prior evidence
A favorable regime discovered after protected/adverse results creates a new hypothesis and cannot reinterpret the prior result as confirmatory.

### S6-D-06 — Stress is not probability
Synthetic scenarios carry no event probability by default.

### S6-D-07 — Finite predeclared scenario grid
Scenario families are finite, canonically ordered, predeclared and fully retained in history.

### S6-D-08 — Structural consistency
Multi-variable stresses must satisfy declared structural/economic consistency constraints.

### S6-D-09 — UNKNOWN remains UNKNOWN
Unknown timing/path/fill/data states cannot be replaced with favorable assumptions.

### S6-D-10 — Deterministic initial engine
Initial S6 has no RNG. Monte Carlo/bootstrap/stochastic generation require future adjudication.

### S6-D-11 — Empirical distributions remain empirical
Empirical distributions originate only from `ObservedSeries`, never from deliberately selected synthetic scenario grids.

### S6-D-12 — Tail metrics are descriptive
Governed tail/downside metrics do not create operational Risk limits.

### S6-D-13 — Upstream evidence is immutable
S6 consumes immutable references/snapshots and does not rewrite upstream scientific roots.

### S6-D-14 — Search history is evidence
All materially considered regime/scenario definitions and policies remain identifiable.

### S6-D-15 — Content-addressed provenance
Scenario definitions, regime definitions, input boundaries, grids, policies, results and manifests require deterministic identities/digests.

### S6-D-16 — Zero additional recurring cost
No paid scenario/risk service is introduced.

### S6-D-17 — ScenarioInputBoundary is mandatory
Every S6 run is rooted in an immutable fail-closed boundary binding source kind, source identity/digest, lineage, a canonical evaluation role for every analysis, protected boundary when role is `PROTECTED_TEST`, role provenance, numeric policy, code revisions and canonical boundary digest. Existing upstream role must match exactly; otherwise the enclosing S6 experiment contract assigns the role before analysis.

### S6-D-18 — Protected-evidence semantics are inherited
S6 must preserve S4/S5 `EvaluationRole`, `EvaluationHistory` and protected-boundary semantics where applicable. `ScenarioResearchHistory` complements rather than replaces them. Any artifact adapted using protected evidence is `PROTECTED_INFORMED` and cannot use the same protected boundary as independent confirmation.

### S6-D-19 — Model evidence crosses a neutral snapshot boundary
Initial S6 core does not import `btg_ai_trader.ml_engine` at runtime and does not load fitted estimator state. Model evidence is consumed as immutable neutral facts/digests.

### S6-D-20 — ScenarioOutcomeSet != ObservedDistributionSummary
Synthetic scenario outcomes may be compared descriptively but cannot be interpreted as empirical frequencies, probabilities, VaR/ES samples or probability-of-loss samples.

### S6-D-21 — RegimeUseMode is explicit
Every regime-conditioned result is `CAUSAL_STRATIFICATION`, `STRATEGY_BOUND` or `RETROSPECTIVE_EXPLORATORY`. `STRATEGY_BOUND` requires upstream proof of actual regime consumption by the evaluated strategy/candidate.

### S6-D-22 — ScenarioDispositionPolicy is predeclared and uses canonical 0E-F disposition vocabulary
Final dispositions are `FAVORABLE`, `UNFAVORABLE`, `CONDITIONAL`, `INCONCLUSIVE` or `INVALID`. Robustness labels are a separate descriptive characterization. Experiment-local tolerances are `PREDECLARED` or `DEVELOPMENT_FIT`; development-fit tolerances are frozen before validation/protected evidence. Hard invalidity is non-compensatory and missing required evidence yields `INCONCLUSIVE`.

### S6-D-23 — Sprint 3 owns execution economics
S6 orchestrates Sprint 3 for fees/slippage/latency/spread assumption stresses and may not duplicate fill, accounting or P&L logic.

### S6-D-24 — Action/replay identity is preserved during initial economic stress
Initial S6 cannot create/delete/reorder/mutate actions or market events. Only declared supported EconomicAssumptions fields may change.

### S6-D-25 — ObservedSeries governs path/tail semantics
Tail/path analysis requires explicit population, observation unit, value unit, ordering, source digest and timestamps when duration metrics are claimed. Drawdown ratios require a valid positive denominator/capital convention.

### S6-D-26 — TailMetricPolicy is predeclared
Empirical tail metrics require predeclared tail level, sign convention, order-statistic/interpolation rule, minimum total/tail sample requirements and numeric policy. Insufficient evidence is unavailable/`INCONCLUSIVE`.

### S6-D-27 — No model adaptation inside Scenario Engine
Initial S6 cannot retrain models, perform feature selection/ablation, tune hyperparameters or select a candidate.

### S6-D-28 — Functional package quality gate is 100% statement and branch coverage
Any future `scenario_engine` package must reach 100% statement and 100% branch coverage before closure, plus full repository regression, strict typing, lint, compile, dependency and exact-head CI gates.

### S6-D-29 — Core package forbids dangerous side-effect surfaces
Initial S6 core has no broker/account/order API, network client, subprocess, dynamic eval/exec, unsafe pickle/joblib deserialization or untrusted dynamic import.

### S6-D-30 — Gate evidence reconciles to final canonical Entry Gate head
The historical merge SHA is `d74e632f...`; the final canonical Entry Gate head before this remediation is `616849f8...`, validated by runs `35474371811` and `35474371852`. Future state documents must distinguish these facts.

## 3. Decisions explicitly not made by this remediation

This remediation does not decide universal regime thresholds/windows, universal scenario shock magnitudes, scenario probabilities, universal VaR/ES tail levels, universal minimum sample sizes, Strategy activation thresholds, position sizing, Risk Engine limits, Paper/Live thresholds, inferential methodology, or production drift policy.

It also does not authorize functional Sprint 6 implementation.
