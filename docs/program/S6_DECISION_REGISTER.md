# Sprint 6 Decision Register — Scenario Engine

This register adjudicates decisions whose first material dependency occurs at the Sprint 6 Scenario Engine boundary. Foundation IDs from `docs/foundation/0F-B_deferred_decision_register.md` are preserved exactly.

## 1. Foundation decisions activated or constrained by Sprint 6

| ID | Decision | Sprint 6 Entry-Gate Adjudication | Scope |
|---|---|---|---|
| **DD-89** | Algorithms for market-regime segmentation and detection | `TRIGGERED_AND_DESIGN_ADJUDICATED` — initial S6 family is deterministic causal threshold classification. Definitions declare features, windows and thresholds explicitly. Thresholds are fixed ex ante or fitted only in the development domain and frozen before evaluation. Retrospective segmentation remains `EXPLORATORY_ONLY`. | Regime detection |
| **DD-108** | Parameter grid for sensitivity and cost perturbation | `TRIGGERED_FOR_S6_SCOPE_DESIGN_ONLY` — finite, predeclared, canonically ordered deterministic scenario grids. Shock magnitudes remain experiment-local. | Scenario/stress grid |
| **DD-91** | Numeric stability thresholds | `CANONICAL_DEFERRED` — factual regime/scenario heterogeneity may be reported, but no universal pass/fail threshold is introduced. | Stability |
| **DD-100** | Formal estimand for each study | `EXPERIMENT_LOCAL` — each S6 analysis declares its question, population, baseline and regime/scenario scope. | Study contract |
| **DD-101** | Primary/secondary metrics | `EXPERIMENT_LOCAL` — valid metrics depend on the upstream evidence and claim; no single universal S6 metric defines merit. | Metrics |
| **DD-102** | Significance levels and confidence intervals | `NOT_TRIGGERED_AND_DEFERRED` — initial S6 remains descriptive/deterministic. | Inference |
| **DD-103** | Inferential methodology | `NOT_TRIGGERED_AND_DEFERRED` — no new frequentist, Bayesian or bootstrap engine. | Inference |
| **DD-104** | Temporal bootstrap block length | `NOT_TRIGGERED_AND_DEFERRED` — bootstrap is outside initial S6. | Resampling |
| **DD-105** | Multiplicity control | `CANONICAL_DEFERRED_WITH_SEARCH_HISTORY` — scenario/regime search history is mandatory, but formal FWER/FDR corrections remain deferred. | Search evidence |
| **DD-107** | Tail-risk operational thresholds | `NOT_TRIGGERED_AND_DEFERRED_TO_S7` — S6 may calculate descriptive tail/downside metrics, not operational limits. | Risk |
| **DD-110** | Calibration/discrimination thresholds | `NOT_TRIGGERED` — model promotion thresholds remain outside S6. | ML thresholds |
| **DD-111** | Strategy activation thresholds and sizing | `NOT_TRIGGERED_AND_DEFERRED` — Strategy and sizing remain absent. | Strategy/Risk |
| **DD-113** | Model drift / strategy decay criteria | `NOT_TRIGGERED_AND_DEFERRED` — regime-conditioned analysis is not a drift-monitoring daemon. | Monitoring |
| **DD-13 / DD-14** | RNG and seed governance | `NOT_TRIGGERED_BY_INITIAL_S6_SCOPE` — initial S6 excludes Monte Carlo, bootstrap and random scenario generation. | RNG |

## 2. Sprint 6 local decisions

### S6-D-01 — Research-only authority
Scenario artifacts are research evidence only and cannot create trading, risk or financial authority.

### S6-D-02 — Causal and retrospective regime semantics are distinct
A regime supporting a causal claim must be point-in-time. Retrospective segmentation is permanently tagged `EXPLORATORY_ONLY` for that evidence lineage.

### S6-D-03 — Canonical initial regime algorithm
The initial family is deterministic threshold classification. Features, windows and thresholds are explicit parts of regime identity. Adaptive clustering is outside initial S6.

### S6-D-04 — Development-only fitting of learned thresholds
Any threshold estimated from data is fit only in the declared development domain and frozen before evaluation.

### S6-D-05 — Post-hoc regimes cannot repair prior evidence
A favorable regime discovered after seeing protected/adverse results creates a new hypothesis; it cannot reinterpret the old result as confirmatory.

### S6-D-06 — Stress is not probability
Synthetic scenarios carry no event probability by default. Severity and probability are separate concepts.

### S6-D-07 — Finite predeclared scenario grid
The considered scenario family is finite, canonically ordered and preserved as evidence. Adaptive search on protected evidence is prohibited.

### S6-D-08 — Structural consistency
Multi-variable stresses must preserve declared economic/structural consistency constraints.

### S6-D-09 — UNKNOWN remains UNKNOWN
Unknown timing, path, fill or data states cannot be replaced with favorable assumptions. Worst-case, expected-case and `UNKNOWN` remain distinct.

### S6-D-10 — Deterministic initial engine
No RNG is required or allowed in initial S6. Monte Carlo, bootstrap and stochastic scenario generation require later explicit adjudication.

### S6-D-11 — Empirical distributions remain empirical
Empirical quantiles/frequencies describe the supplied sample or scenario results; they are not silently promoted to population probabilities.

### S6-D-12 — Tail metrics are descriptive
VaR, Expected Shortfall, downside and drawdown may describe valid evidence; they do not create Risk limits.

### S6-D-13 — Upstream evidence is immutable
S6 consumes references to upstream artifacts and does not rewrite them or fabricate a trading path absent from them.

### S6-D-14 — Search history is evidence
Every materially considered regime/scenario definition belongs to the experiment history. Unfavorable cases cannot be silently dropped.

### S6-D-15 — Content-addressed provenance
Any future implementation must assign deterministic identities/digests to regime definitions, scenario definitions, grids, evaluations and manifests.

### S6-D-16 — Zero additional recurring cost
Initial S6 introduces no commercial scenario/risk service or mandatory paid dependency.

## 3. Decisions not made by this gate

This gate does not decide universal volatility/trend windows, universal shock magnitudes, scenario probabilities, operational VaR/ES limits, Strategy thresholds, sizing, Risk limits, Paper/Live thresholds, inferential methodology, or production drift policy.
