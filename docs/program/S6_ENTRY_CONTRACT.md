# Sprint 6 Entry Contract — Scenario Engine

## Authority and canonical baseline

```text
SPRINT_5_STATUS = FORMALLY_CLOSED
SPRINT_5_FINAL_VERDICT = PASS
SPRINT_5_FINAL_CANONICAL_HEAD = 9956f3a15d1fa2f87b347d436a26d684d50ba857

SPRINT_6_ENTRY_GATE = PASS
SPRINT_6_ENTRY_GATE_CANONICAL = PASS
SPRINT_6_ENTRY_GATE_MERGE_SHA = d74e632f47fafab9f441574acbacb3ae7f1a7a72
SPRINT_6_ENTRY_GATE_FINAL_CANONICAL_HEAD = 616849f8e77ecf3624b2b9362c1ef42c7fb9bcc1
SPRINT_6_ENTRY_GATE_FINAL_CI_RUN = 35474371811
SPRINT_6_ENTRY_GATE_FINAL_UPSTREAM_RUN = 35474371852

PREAUTH_REMEDIATION_ISSUE = #81
PREAUTH_REMEDIATION_BRANCH = s6/01-preauth-remediation
PREAUTH_REMEDIATION_PR = #82
S6_PREAUTH_REMEDIATION_MERGE_SHA = 7df047b25633527e505b3e4772c0a0c43e1ab10c
S6_PREAUTH_POST_MERGE_ENTRY_GATE_CI_RUN = 35759318235
S6_PREAUTH_POST_MERGE_UPSTREAM_RUN = 35759318238
S6_PREAUTH_REMEDIATION_CANONICAL = PASS

SPRINT_6_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
PROMOTION_TO_S6_FUNCTIONAL_IMPLEMENTATION = NO

FINANCIAL_AUTHORITY = ABSENT
STRATEGY_OPERATIONAL_PATH = FORBIDDEN
RISK_OPERATIONAL_PATH = FORBIDDEN
PAPER_TRADING = FORBIDDEN
LIVE_TRADING = FORBIDDEN
REAL_MONEY = FORBIDDEN
BROKER_ORDER_API = FORBIDDEN
FINANCIAL_LEDGER_MUTATION = FORBIDDEN
ADDITIONAL_RECURRING_COST = ZERO
```

This contract defines the only admissible functional boundary for a future Sprint 6 implementation. The present remediation does not itself authorize that implementation.

---

## 1. Mission

Sprint 6 is a research-only analytical layer for evaluating how already-admissible upstream evidence behaves across explicitly defined market regimes and deterministic adverse scenarios.

```text
SPRINT_6_CLASS = RESEARCH_SCENARIO_REGIME_AND_ROBUSTNESS_ENGINE

SCENARIO_ENGINE_MAY = ANALYZE_AND_ORCHESTRATE_RESEARCH_EVIDENCE
SCENARIO_ENGINE_MAY_NOT = CREATE_FINANCIAL_AUTHORITY

CAUSAL_REGIME_ANALYSIS = FUTURE_IN_SCOPE_AFTER_AUTHORIZATION
RETROSPECTIVE_REGIME_ANALYSIS = EXPLORATORY_ONLY
DETERMINISTIC_SCENARIOS = FUTURE_IN_SCOPE_AFTER_AUTHORIZATION
STRESS_TESTING = FUTURE_IN_SCOPE_AFTER_AUTHORIZATION
OBSERVED_DISTRIBUTION_SUMMARY = FUTURE_IN_SCOPE_AFTER_AUTHORIZATION

MONTE_CARLO_ENGINE = OUT_OF_INITIAL_S6_SCOPE
BOOTSTRAP_INFERENCE = OUT_OF_INITIAL_S6_SCOPE
STOCHASTIC_SCENARIO_GENERATION = OUT_OF_INITIAL_S6_SCOPE
ADAPTIVE_CLUSTERING = OUT_OF_INITIAL_S6_SCOPE
MODEL_RETRAINING = OUT_OF_INITIAL_S6_SCOPE
STRATEGY_GENERATION = OUT_OF_INITIAL_S6_SCOPE
```

---

## 2. Canonical input boundary

A future Scenario Engine must fail closed unless every analysis is rooted in one immutable `ScenarioInputBoundary`.

### 2.1 Required ScenarioInputBoundary semantics

The boundary must bind at minimum:

- `source_kind`;
- immutable upstream artifact identity;
- upstream artifact content/scientific-root digest;
- `source_lineage_digest`;
- canonical `evaluation_role` for every S6 analysis;
- `protected_boundary_id` whenever `evaluation_role == PROTECTED_TEST`;
- `role_provenance`, distinguishing a role inherited from upstream from a role assigned by the enclosing S6 experiment contract;
- numeric-policy identity/digest;
- source code revision;
- Scenario Engine code revision;
- ordered input identity where ordering is material;
- canonical `boundary_digest`.

No mutable alias such as `latest`, `champion`, `production` or an unversioned filename is sufficient provenance.

The boundary must be constructed by a validated factory that recomputes all supported digests and fails closed on identity mismatch. Caller-supplied digest text is not trusted merely because it is syntactically valid.

If an upstream artifact already carries an `EvaluationRole`, the S6 role must match it exactly. If the upstream artifact does not carry a role (for example a Sprint 3 backtest artifact), the enclosing S6 experiment contract must assign the role explicitly before analysis. Role may never be inferred from filename, date range, directory name or favorable/adverse outcome.

### 2.2 Admissible upstream evidence families

Initial S6 may consume only explicitly typed, immutable evidence snapshots rooted in one of these families:

1. **Backtest evidence**
   - Sprint 3 `BacktestRunManifest` whose `verify_integrity()` succeeds, plus its immutable identity and hashes;
   - referenced immutable `BacktestResult`/economic evidence when required by the analysis;
   - causal replay boundary identity;
   - action-sequence identity;
   - assumptions identity;
   - instrument economics identity.

2. **Statistical evaluation evidence**
   - Sprint 4 verified `StatisticalEvaluationInputBoundary` (`is_verified == True`) and evaluation-manifest identity;
   - `EvaluationRole`;
   - dataset, source-lineage and plan digests;
   - aggregate/fold metrics only under the original evaluation context.

3. **Model evaluation evidence**
   - a neutral immutable verified `ModelEvidenceSnapshot` containing only research evidence required by S6;
   - candidate/model identity;
   - `EvaluationScope.MODEL`;
   - `EvaluationRole`;
   - dataset, plan, target-contract and experimental-context digests;
   - metrics/disposition as upstream facts;
   - source training/evaluation manifest identities where available;
   - when a `ModelTrainingManifest` is supplied, it must be verified and identity-consistent with the snapshot.

4. **Observed series evidence**
   - immutable `ObservedSeries` described in section 7.

### 2.3 Optional-ML dependency firewall

The core Scenario Engine must not require the optional ML stack merely to consume model-evaluation evidence.

```text
scenario_engine core -> MUST_NOT_IMPORT btg_ai_trader.ml_engine at runtime
scenario_engine core -> MUST_NOT_LOAD estimator objects
scenario_engine core -> MUST_NOT_DESERIALIZE joblib/pickle model state
```

A neutral evidence snapshot may be produced at an upstream adapter boundary. Its factory must verify source identities/context before issuing the snapshot, and the snapshot must carry a non-transferable verification state or equivalent fail-closed construction invariant. It contains immutable facts/digests, not a fitted estimator or executable model object.

### 2.4 Upstream evidence is immutable

S6 may not rewrite upstream manifests, candidate identities, protected-boundary identities, action histories, replay boundaries or source-lineage records.

---

## 3. Protected evidence and adaptation history

Sprint 6 inherits Sprint 4/Sprint 5 epistemological protection. A scenario/regime analysis must preserve the distinction between development/selection evidence and protected evidence.

### 3.1 Canonical roles

Every S6 analysis declares a canonical `EvaluationRole`. When an upstream artifact already carries a role, S6 preserves it exactly. When it does not, the S6 experiment contract assigns the role explicitly before any result is inspected. In particular:

```text
PROTECTED_TEST remains PROTECTED_TEST
PROTECTED_TEST -> MUST_NOT_BECOME development evidence implicitly
UNLABELED_BACKTEST -> MUST_BE_ROLE_BOUND_BEFORE_ANALYSIS
```

`ScenarioResearchHistory` complements rather than weakens the existing S4/S5 protected-evidence semantics. Where the existing `EvaluationHistory` abstraction applies to the candidate lineage, S6 must preserve/check that history as well as its scenario-specific history; a parallel scenario history cannot be used to bypass an existing protected-evidence consumption record.

### 3.2 ScenarioResearchHistory

A future implementation must maintain an immutable or append-only research history containing:

- all materially considered `RegimeDefinition` identities;
- all materially considered `ScenarioSpec` identities;
- all `ScenarioGrid` identities;
- analysis attempts and dispositions;
- protected-evidence observations;
- adaptations informed by protected evidence;
- parent/derived definition lineage.

### 3.3 Protected-boundary consumption rule

If a protected result from boundary `B` informs any material change to a regime definition, scenario definition, scenario grid, disposition policy or metric policy, the derived artifact is `PROTECTED_INFORMED`.

A `PROTECTED_INFORMED` artifact:

- may be retained as exploratory research;
- may not be evaluated on the same protected boundary `B` as independent confirmatory evidence;
- requires a new independent protected boundary for any later confirmatory claim.

This rule is non-compensatory.

### 3.4 No protected search

Protected evidence cannot be used to:

- choose the favorable regime;
- choose the favorable scenario;
- choose the favorable shock magnitude;
- choose the favorable tail level;
- choose the favorable metric;
- tune a robustness-disposition rule.

---

## 4. Regime semantics

### 4.1 RegimeDefinitionMode

Every `RegimeDefinition` must declare one mode:

- `PREDECLARED`;
- `DEVELOPMENT_FIT`;
- `RETROSPECTIVE_EXPLORATORY`.

`DEVELOPMENT_FIT` thresholds/windows are estimated only from the declared development domain and frozen before evaluation.

`RETROSPECTIVE_EXPLORATORY` may not support a confirmatory claim in the same evidence lineage.

### 4.2 Initial regime family

The initial canonical family is deterministic threshold classification over explicitly supplied causal observations. Sprint 6 does not initially own indicator engineering, adaptive clustering or latent-state estimation.

A regime observation must carry:

- observation identity;
- observation/event time when meaningful;
- `knowledge_time`;
- declared variables and units;
- source-lineage digest;
- explicit missing/unknown state.

No future information may enter the classification.

### 4.3 RegimeUseMode

Every regime-conditioned result must declare one of:

1. `CAUSAL_STRATIFICATION`
   - the regime assignment itself was point-in-time admissible;
   - the evaluated candidate/strategy is not claimed to have consumed the regime;
   - the result is a conditional analysis only.

2. `STRATEGY_BOUND`
   - upstream provenance proves that the evaluated strategy/candidate actually consumed that exact regime definition at decision time;
   - merely being able to calculate the regime causally is insufficient.

3. `RETROSPECTIVE_EXPLORATORY`
   - segmentation was identified or materially changed after observing outcomes;
   - exploratory only.

Sprint 6 may not manufacture `STRATEGY_BOUND` status. If upstream evidence does not prove regime consumption, the strongest admissible status is `CAUSAL_STRATIFICATION`.

---

## 5. Scenario and stress semantics

### 5.1 Stress scenario != probability forecast

```text
STRESS_SCENARIO != FORECAST
SCENARIO_WEIGHT != PROBABILITY
SCENARIO_COUNT != EMPIRICAL_FREQUENCY
SCENARIO_OUTCOME_SET != OBSERVED_DISTRIBUTION
```

Synthetic scenario definitions carry no event probability by default.

### 5.2 ScenarioSpec

Each deterministic `ScenarioSpec` must bind:

- immutable scenario identity;
- baseline evidence reference;
- finite typed shocks;
- shock targets and units;
- structural/economic consistency constraints;
- predeclaration status;
- research-history reference;
- code revision;
- scenario digest.

### 5.3 ScenarioGrid

A `ScenarioGrid` must be:

- finite;
- canonically ordered;
- predeclared before inspecting evaluated evidence for scenario selection;
- fully preserved in research history;
- non-adaptive on protected evidence.

Unfavorable scenarios cannot be silently dropped.

---

## 6. Economic and execution stress must delegate to Sprint 3

Sprint 6 is not a second backtester.

### 6.1 Permitted orchestration

When stress modifies assumptions already modeled by Sprint 3, S6 must delegate execution economics to the existing deterministic backtesting kernel.

Initial permissible assumption-stress dimensions are limited to those already represented by the Sprint 3 model and explicitly declared by the scenario, such as:

- fees;
- adverse slippage;
- latency;
- spread/execution assumptions where supported by the existing Sprint 3 contracts.

Existing Sprint 3 sensitivity helpers should be reused when their semantics exactly match the requested stress.

### 6.2 Preserved upstream identities

Unless separately adjudicated in a future change, a Sprint 6 economic stress must preserve:

- the exact ordered `BacktestAction` sequence and action identities;
- causal replay boundary;
- market event sequence;
- instrument identity/economics;
- end-of-window semantics;
- all non-shocked assumptions.

Only the declared assumption field(s) may differ.

### 6.3 Mandatory manifest lineage

Every stressed economic run must retain:

- baseline `BacktestRunManifest` reference;
- stressed `BacktestRunManifest`;
- baseline/stressed assumptions hashes;
- unchanged action/replay identities;
- scenario digest;
- code revision.

### 6.4 Explicit prohibitions

Scenario Engine must not:

- create, delete, reorder or mutate `BacktestAction` objects;
- create StrategyDecision or TradeIntent objects;
- synthesize favorable fills;
- reimplement P&L/accounting/fill logic;
- alter replay market events;
- convert unknown/indeterminate execution outcomes into favorable fills.

---

## 7. Observed series, distributions, tail and path semantics

### 7.1 ObservedSeries

An `ObservedSeries` is the only initial S6 source eligible for empirical-distribution/tail summaries.

It must bind:

- series identity;
- population/estimand description;
- observation unit (trade, opportunity, period, return, P&L amount, etc.);
- value unit/currency/scale;
- ordered values;
- immutable observation identities;
- timestamps when temporal-duration metrics are requested;
- source artifact/boundary digest;
- missing/unknown policy;
- series digest.

### 7.2 ScenarioOutcomeSet is not ObservedSeries

A finite set of outputs generated from deliberately selected synthetic stress scenarios is a `ScenarioOutcomeSet`.

It may be summarized across scenarios descriptively, but:

- it is not an empirical sample from the market;
- scenario counts are not event frequencies;
- scenario weights are not probabilities;
- it cannot be fed into empirical VaR/ES/probability-of-loss calculations.

### 7.3 TailMetricPolicy

Any empirical quantile/VaR/Expected-Shortfall-like metric must have a predeclared `TailMetricPolicy` containing at least:

- loss direction/sign convention;
- tail level;
- interpolation/order-statistic convention;
- minimum tail-observation requirement;
- minimum total sample requirement;
- missing-value policy;
- numeric policy.

The output must expose:

- total effective sample count;
- tail observation count;
- empirical resolution;
- policy identity/digest.

If the predeclared sample/tail sufficiency rule is not met, the metric is unavailable or the corresponding claim is `INCONCLUSIVE`; precision may not be fabricated.

### 7.4 Path metrics

- drawdown amount requires an ordered value/equity series;
- drawdown ratio requires an explicit valid positive denominator/capital convention;
- drawdown duration, recovery time and time-underwater require a causally ordered timestamped series;
- the current Sprint 3 `realized_equity_curve` alone does not prove elapsed-time duration because it has no intrinsic timestamps;
- missing time/capital semantics remain `UNKNOWN`/unavailable.

---

## 8. Scenario disposition policy

Scenario dispositions must be derived under a predeclared immutable `ScenarioDispositionPolicy`, never improvised after result inspection.

Final research dispositions reuse the canonical 0E-F vocabulary:

- `FAVORABLE`;
- `UNFAVORABLE`;
- `CONDITIONAL`;
- `INCONCLUSIVE`;
- `INVALID`.

Robustness is a separate descriptive characterization, not a replacement disposition. A governed result may additionally report a `RobustnessCharacterization` such as `ROBUST_WITHIN_DECLARED_SCOPE`, `FRAGILE` or `MIXED`, but that label cannot override the canonical final disposition.

The policy must bind:

- declared evaluation scope;
- required evidence dimensions;
- applicable metrics and directions;
- experiment-local tolerances/conditions;
- treatment of missing/unknown metrics;
- treatment of conflicting metrics;
- tail/path sufficiency requirements when applicable;
- policy digest;
- definition mode for any experiment-local tolerances (`PREDECLARED` or `DEVELOPMENT_FIT`).

Any `DEVELOPMENT_FIT` tolerance is derived only from the declared development domain and frozen before validation/protected evaluation. No universal compensatory score is allowed. A hard-invalidity condition yields `INVALID` regardless of favorable values elsewhere. Insufficient required evidence yields `INCONCLUSIVE`, not robustness.

No disposition grants Strategy, Risk, Paper or Live authority.

---

## 9. Initial Scenario Engine package boundary

A future implementation is restricted to a pure research package such as `src/btg_ai_trader/scenario_engine/`.

The core package must not:

- retrain or fit ML models;
- select ML candidates or hyperparameters;
- perform feature selection/ablation;
- deserialize estimator/model state;
- generate trading actions;
- implement Strategy or Risk logic;
- call broker/account/order APIs;
- perform Paper/Live execution;
- mutate FinancialLedger;
- use network clients;
- spawn subprocesses;
- use dynamic `eval`/`exec`;
- perform unsafe pickle/joblib deserialization;
- dynamically import untrusted modules;
- create additional recurring cost.

The core should remain deterministic and side-effect-minimal.

---

## 10. Functional engineering acceptance contract

A later authorized functional implementation cannot close until all applicable gates below pass on the exact reviewed head:

```text
S6_PACKAGE_STATEMENT_COVERAGE = 100%
S6_PACKAGE_BRANCH_COVERAGE = 100%

S6_DEDICATED_TESTS = PASS
FULL_REGRESSION_S1_TO_S5 = PASS
S6_BOUNDARY_VERIFIER = PASS
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

Required adversarial tests include at minimum:

- causal vs post-hoc regime separation;
- `CAUSAL_STRATIFICATION` vs `STRATEGY_BOUND`;
- protected-evidence consumption and same-boundary reuse rejection;
- scenario predeclaration;
- synthetic scenario outcomes rejected as empirical probability/tail input;
- unknown-preservation;
- Sprint 3 action/replay identity preservation under stress;
- invalid path/tail metrics when timestamp/capital/sample semantics are insufficient;
- deterministic repeated-run equivalence;
- forbidden dynamic/deserialization/network/subprocess surfaces.

---

## 11. Explicitly excluded from initial Sprint 6

- Strategy or Signal operational logic.
- Trade activation thresholds or sizing.
- Risk limits, vetoes, RiskDecision or RiskAuthorization.
- Paper or Live trading.
- Broker/order capabilities.
- FinancialLedger mutation or real money.
- Automatic promotion.
- Monte Carlo.
- Bootstrap/new inferential engines.
- Stochastic scenario generation.
- Adaptive clustering/latent-state models.
- Model retraining/selection/feature engineering.
- Synthetic scenario probabilities.
- VaR/ES over `ScenarioOutcomeSet`.
- Time-underwater/recovery duration without timestamped observed evidence.
- Paid external scenario/risk platforms.

---

## 12. Authorization boundary

This remediation only strengthens the contract.

```text
S6_ENTRY_GATE = PASS
S6_PREAUTH_CONTRACT_REMEDIATION = PASS
S6_PREAUTH_REAUDIT = PASS
S6_PREAUTH_REMEDIATION_CANONICAL = PASS
S6_PREAUTH_REMEDIATION_MERGE_SHA = 7df047b25633527e505b3e4772c0a0c43e1ab10c
S6_PREAUTH_POST_MERGE_ENTRY_GATE_CI_RUN = 35759318235
S6_PREAUTH_POST_MERGE_UPSTREAM_RUN = 35759318238
OPEN_PREAUTH_BLOCKERS = 0
SPRINT_6_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
```

PR #82 was merged by explicit human authorization and the remediation is now canonical PASS. Functional implementation remains separately NOT_AUTHORIZED and requires a distinct explicit human authorization.
