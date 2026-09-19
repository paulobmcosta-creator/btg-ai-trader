# Sprint 6 Entry Contract — Scenario Engine

## Authority and baseline

```text
SPRINT_5_STATUS = FORMALLY_CLOSED
SPRINT_5_FINAL_VERDICT = PASS
SPRINT_5_FUNCTIONAL_MERGE = 8b09a34ecc7c3b0b180e30ada0702d22d61d96d2
SPRINT_5_FINAL_CANONICAL_HEAD = 9956f3a15d1fa2f87b347d436a26d684d50ba857
SPRINT_5_FINAL_HEAD_CI_RUN = 35473293690
SPRINT_5_FINAL_HEAD_UPSTREAM_RUN = 35473293704

SPRINT_6_REQUIRED_BASE_SHA = 9956f3a15d1fa2f87b347d436a26d684d50ba857
CANONICAL_SPRINT_6_BRANCH = sprint/6-scenario-engine
WORK_BRANCH = s6/00-entry-gate
ISSUE = #79

SPRINT_6_ENTRY_GATE_SCOPE = GOVERNANCE_ONLY
SPRINT_6_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
FINANCIAL_AUTHORITY = ABSENT
STRATEGY_OPERATIONAL_PATH = FORBIDDEN
RISK_OPERATIONAL_PATH = FORBIDDEN
PAPER_TRADING = FORBIDDEN
LIVE_TRADING = FORBIDDEN
REAL_MONEY = FORBIDDEN
FINANCIAL_LEDGER_MUTATION = FORBIDDEN
ADDITIONAL_RECURRING_COST = ZERO
NEW_MANDATORY_RUNTIME_DEPENDENCIES = 0
```

This contract governs only the Sprint 6 Entry Gate. It does not authorize functional Scenario Engine implementation.

## 1. Mission

Sprint 6 is a research-only analytical layer for evaluating how admissible upstream evidence behaves across explicitly defined market regimes and deterministic adverse scenarios.

```text
SPRINT_6_CLASS = RESEARCH_SCENARIO_REGIME_AND_ROBUSTNESS_ENGINE

CAUSAL_REGIME_ANALYSIS = FUTURE_IN_SCOPE_AFTER_AUTHORIZATION
RETROSPECTIVE_REGIME_ANALYSIS = EXPLORATORY_ONLY
DETERMINISTIC_SCENARIOS = FUTURE_IN_SCOPE_AFTER_AUTHORIZATION
STRESS_TESTING = FUTURE_IN_SCOPE_AFTER_AUTHORIZATION
EMPIRICAL_DISTRIBUTION_SUMMARY = FUTURE_IN_SCOPE_AFTER_AUTHORIZATION

MONTE_CARLO_ENGINE = OUT_OF_INITIAL_S6_SCOPE
BOOTSTRAP_INFERENCE = OUT_OF_INITIAL_S6_SCOPE
STOCHASTIC_SCENARIO_GENERATION = OUT_OF_INITIAL_S6_SCOPE
```

## 2. Governing separations

### 2.1 Causal regime != retrospective segmentation

Protocol 0E-C requires any regime used as a causal filter or input to be measurable point-in-time. A regime discovered retrospectively cannot be used to rescue a prior failure or be presented as contemporaneously known.

A future implementation must distinguish:
- **Causal regime:** features, windows and thresholds are available under an explicit knowledge cutoff.
- **Retrospective regime analysis:** permanently marked `EXPLORATORY_ONLY` for that evidence lineage.

### 2.2 Stress scenario != probability forecast

Protocol 0E-E treats stress scenarios as structural vulnerability tests, not probabilistic forecasts.

```text
STRESS_SCENARIO != FORECAST
SCENARIO_WEIGHT != PROBABILITY
SCENARIO_COUNT != EMPIRICAL_FREQUENCY
```

Synthetic stress scenarios carry no event probability unless a separately governed empirical/inferential method supports one. Such inference is outside the initial Sprint 6 scope.

### 2.3 Scenario analysis != Risk authority

Tail, downside, drawdown, loss quantiles, VaR or Expected Shortfall may be descriptive research outputs when supported by data. They do not establish limits, vetoes, sizing, capital allocation or RiskAuthorization.

```text
ScenarioEvaluation != RiskDecision
ScenarioEvaluation != RiskAuthorization
TailMetric != RiskLimit
```

Operational risk thresholds remain deferred to Sprint 7.

### 2.4 Distribution summary != promotion

No scenario result, regime result or single distributional metric grants Strategy, Paper or Live eligibility.

## 3. Functional scope allowed only after a later explicit authorization

A future implementation under this contract may include:

1. Immutable regime definitions with explicit features, windows, thresholds, knowledge semantics, code revision and content digest.
2. Deterministic threshold-based causal regime classification.
3. Thresholds fixed ex ante or estimated only in the development domain and frozen before evaluation.
4. Retrospective regime analysis marked `EXPLORATORY_ONLY`.
5. Regime assignments bound to causal cutoffs and explicit `UNKNOWN` when evidence is insufficient.
6. Deterministic scenario specifications with finite shocks, affected variables, baseline reference, consistency constraints, predeclaration status and provenance.
7. Finite, canonically ordered scenario grids with complete search-history preservation.
8. Stress of market regimes and upstream economic/execution assumptions only where the referenced upstream artifact supports such perturbation.
9. Internally consistent multi-variable adverse scenarios.
10. Empirical quantiles, downside summaries, observed-tail summaries and path/drawdown summaries when valid ordered economic evidence exists.
11. Regime-conditioned summaries with explicit sample counts and unknown mass.
12. Research dispositions such as `ROBUST_WITHIN_DECLARED_SCOPE`, `FRAGILE`, `CONDITIONAL`, `INCONCLUSIVE` and `INVALID`, none of which grants operational authority.
13. Deterministic provenance for definitions, grids, evaluations and manifests.
14. Identical admissible inputs/definitions/code revision producing identical outputs.
15. Zero additional recurring cost.

## 4. Explicitly excluded from the initial Sprint 6 scope

- Strategy or Signal operational logic.
- Trade activation thresholds or position sizing.
- Risk limits, vetoes, RiskDecision or RiskAuthorization.
- Paper or Live trading.
- Broker/order capabilities.
- FinancialLedger mutation or real money.
- Automatic promotion to Strategy, Paper or Live.
- Monte Carlo scenario generation.
- Bootstrap or new inferential engines.
- Random/entropy-driven scenario generation.
- Adaptive clustering used as causal confirmatory evidence.
- Post-hoc regime masking of losses or failures.
- Synthetic scenario probabilities without governed evidence.
- Conversion of `UNKNOWN` into favorable assumptions.
- Removal of real tail observations merely to improve metrics.
- Paid external scenario/risk platforms.

## 5. Future acceptance structure

Any later authorized implementation must:
1. satisfy `S6_CAPABILITY_MATRIX.md`;
2. preserve every negative capability;
3. implement a dedicated S6 boundary verifier before closure;
4. test regime causality, post-hoc separation, scenario predeclaration and stress/probability separation;
5. preserve S1-S5 regression;
6. provide exact-head CI and pinned-upstream evidence;
7. remain at zero additional recurring cost;
8. stop for independent audit before merge.

The present Entry Gate authorizes none of those implementation steps.
