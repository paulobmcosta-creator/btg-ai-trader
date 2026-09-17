# Sprint 4 Entry Contract — Statistical Baselines

## Authority and baseline

```text
SPRINT_3_FINAL_VERDICT = PASS
SPRINT_3_ACCEPTED_FUNCTIONAL_MERGE = 6333b8f431d43be9c40f3222fbbe17cf06509033
SPRINT_4_REQUIRED_BASE_SHA = 922adee625029c0cbd6c665f8906e7fd99cf71cb
CANONICAL_SPRINT_4_BRANCH = sprint/4-statistical-baselines
WORK_BRANCH = s4/00-full-statistical-baselines
ISSUE = #73
FINANCIAL_AUTHORITY = ABSENT
REAL_MONEY = FORBIDDEN
PAPER_TRADING = FORBIDDEN
LIVE_TRADING = FORBIDDEN
STRATEGY_OPERATIONAL_PATH = FORBIDDEN
RISK_OPERATIONAL_PATH = FORBIDDEN
ADDITIONAL_RECURRING_COST = ZERO
NEW_RUNTIME_DEPENDENCIES = 0
```

This contract governs Sprint 4 — Statistical Baselines. It is derived from the accepted and formally closed Sprint 3 state (`922adee625029c0cbd6c665f8906e7fd99cf71cb`), the frozen Foundation, `AGENTS.md`, the living Master Plan, Quantitative Protocols 0E-A, 0E-B, 0E-C, 0E-E, and 0E-H, and ADRs 0004, 0008, 0017, and 0021.

## 1. Mission and Classification

Sprint 4 delivers a research layer capable of constructing, fitting, and evaluating **simple deterministic statistical baselines under causal temporal validation**, with strict out-of-sample (OOS) protection.

Sprint 4 is formally classified as:
```text
SPRINT_4_CLASS = DETERMINISTIC_STATISTICAL_BASELINE_AND_TEMPORAL_VALIDATION_KERNEL
ML_ENGINE = ABSENT
FEATURE_STORE = ABSENT
MODEL_REGISTRY = ABSENT
PRODUCTION_STRATEGY = ABSENT
SIGNAL_ENGINE = ABSENT
RISK_ENGINE = ABSENT
PAPER_TRADER = ABSENT
LIVE_TRADER = ABSENT
PROMOTION_ENGINE = ABSENT
```

## 2. Epistemological and Temporal Foundation

### 2.1 OOS as an Epistemological Relation
In accordance with Protocol 0E-C:
```text
OOS != "arquivo de teste"
OOS = relação entre evidência e histórico de desenvolvimento do candidato
```
Data functions are strictly distinguished:
1. **Development Domain:** General research and exploration.
2. **Training / Fit Domain:** Partition causally admissible for parameter estimation.
3. **Validation / Selection Domain:** Partition used for model selection, threshold tuning, or calibration fit (formally part of development).
4. **Protected Evaluation Domain:** Blind evaluation partition. Must not participate in fit, tuning, feature selection, or winner selection.

Any material adaptation based on protected evaluation evidence produces a `NEW_CANDIDATE_VERSION`. Prior evidence cannot be presented as protected OOS for the modified candidate.

### 2.2 Temporal Sample Contract (`StatisticalSample`)
A supervised sample is defined with explicit knowledge times:
- `sample_id`: Unique deterministic identifier.
- `feature_knowledge_time`: Time when inputs/reference values became known.
- `target_knowledge_time`: Time when target/label became causally available.
- `reference_value`: Known reference observation at prediction time.
- `target_value`: Ground truth outcome.
- `target_semantics`: Target classification (`CONTINUOUS`, `BINARY_PROBABILITY`, `CATEGORICAL`).
- `information_interval`: Information interval `[feature_time, target_time]`.
- `source_lineage`: Traceable provenance string.

**Central Invariant:** A sample's target may only enter training/fit if:
```text
target_knowledge_time <= training_knowledge_cutoff
```
No future label access is permitted. File position is never a proxy for temporal causality.

## 3. Evaluation Boundaries & Walk-Forward

### 3.1 Boundaries & Folds
Evaluation boundaries (`EvaluationBoundary`) define explicit, immutable intervals with clear inclusive/exclusive semantics.
Each `TemporalFold` specifies:
- `development_boundary`
- `training_boundary`
- `validation_boundary` (optional)
- `protected_evaluation_boundary`
- `knowledge_cutoff`
- `purge_interval`
- `embargo_interval`
- `window_policy` (`EXPANDING` or `ROLLING`)
- `fold_id`

### 3.2 Purging and Embargo
- **Purging:** Samples whose information horizon crosses the evaluation boundary (`target_knowledge_time > eval_start`) are removed from training. If information horizon is unknown when required, the evaluation fails closed.
- **Embargo:** An explicit non-negative duration or step count immediately following training to eliminate residual serial autocorrelation. Zero embargo is valid only as an explicit, tracked configuration.

### 3.3 Prohibition of Random Shuffling
Random k-fold splitting (`shuffle=True`, `random_split`, `random_k_fold`) is strictly forbidden for prospective confirmatory validation.

## 4. Deterministic Baseline Catalog

The kernel provides simple, deterministic baselines with zero look-ahead bias:
1. `ConstantBaseline`: Emits a fixed configured value.
2. `PersistenceBaseline` / `LastObservedValueBaseline`: Emits the reference value known at prediction time.
3. `HistoricalMeanBaseline`: Exact Decimal mean of causally admissible historical targets (`target_knowledge_time <= cutoff`).
4. `HistoricalMedianBaseline`: Exact Decimal median of causally admissible historical targets.
5. `HistoricalPriorProbabilityBaseline`: Base rate / positive class prevalence of causally admissible targets.
6. `MajorityClassBaseline`: Most frequent class among causally admissible targets (deterministic tie-breaking).
7. `LastKnownClassBaseline`: Most recent target class known at or before prediction time.

**Cold Start Policy:** When history is insufficient, baselines emit explicit `is_cold_start = True` with `None` / `INDETERMINATE`. Silent imputation is prohibited.

**RNG Policy:** `RANDOM_BASELINE = NOT_REQUIRED_BY_DEFAULT`. No PRNG or stochastic sources are included in the baseline kernel (`RNG = NOT_TRIGGERED`).

## 5. Metrics and Diagnostics

### 5.1 Deterministic Metrics
Metrics are scoped by target semantics:
- **Continuous:** MAE, MSE, RMSE, Mean Bias, Sample Count.
- **Binary Probability:** Brier Score, Base Rate, Sample Count.
- **Categorical:** Accuracy, Class Prevalence, Confusion Counts.

Financial and economic metrics (Sharpe, Sortino, VaR, Drawdown) belong to Sprint 3 and are strictly segregated from statistical prediction metrics.

### 5.2 Calibration Diagnostics
`CalibrationReport` produces deterministic binned calibration diagnostics:
- Bin boundaries, bin counts, mean predicted probability per bin, observed frequency per bin, and overall Brier score.
- Empty bin policy is explicit.
- Learned calibration models (Platt scaling, isotonic regression) are excluded from the kernel baseline.

### 5.3 Fold Distribution & Stability
Results are reported per-fold and aggregated:
- Per-fold metric vector, worst fold, best fold, dispersion (range, standard deviation).
- Aggregation supports `EQUAL_FOLD` and `SAMPLE_WEIGHTED` weighting policies.
- Stability diagnostics report factual dispersion without fabricating arbitrary universal pass/fail thresholds (preserving DD-91).

## 6. Baseline Comparison and Protected Test Invariant

- **Parity Requirement:** Two candidates can only be compared if they share identical target semantics, sample population, evaluation boundaries, fold plan, protected interval, and metric semantics. Mismatched comparisons fail closed as `INVALID` / `NOT_COMPARABLE`.
- **Protected Test Winner Selection Invariant:** Protected evaluation results cannot be consumed by automated winner selection. Automated selection helpers must fail closed if applied to `PROTECTED_TEST` results.

## 7. Provenance and Determinism

- `StatisticalEvaluationInputBoundary`: Immutable record binding dataset digest, candidate identity, walk-forward plan, purging policy, embargo policy, metric configuration, calibration configuration, code revision, and environment signature.
- `StatisticalEvaluationManifest`: Cryptographically binds input boundary, per-fold results, aggregate results, search family, and generates a root SHA-256 manifest hash.
- Repeated identical runs yield identical results byte-for-byte.

## 8. Negative Capabilities (S4-NC-01..25)

```text
S4-NC-01  broker API absent
S4-NC-02  account API absent
S4-NC-03  order submission impossible
S4-NC-04  order modification impossible
S4-NC-05  order cancellation impossible
S4-NC-06  real-money authority absent
S4-NC-07  Paper path absent
S4-NC-08  Live path absent
S4-NC-09  Risk operational path absent
S4-NC-10  Strategy operational path absent
S4-NC-11  Signal operational path absent
S4-NC-12  canonical FinancialLedger mutation absent
S4-NC-13  external financial side effect absent
S4-NC-14  ML Engine absent
S4-NC-15  model registry absent
S4-NC-16  hyperparameter search engine absent
S4-NC-17  random temporal shuffle validation forbidden
S4-NC-18  protected-test candidate selection forbidden
S4-NC-19  future-label leakage forbidden
S4-NC-20  silent missing-data imputation forbidden
S4-NC-21  silent OOS reuse after adaptation forbidden
S4-NC-22  statistical significance claim without method forbidden
S4-NC-23  automatic promotion from S4 forbidden
S4-NC-24  network-dependent evaluation absent
S4-NC-25  paid external service absent
```

## 9. Acceptance Criteria (S4-AC-01..30)

- **S4-AC-01:** Exact Sprint 3 lineage and Entry Gate valid.
- **S4-AC-02:** Evaluation roles Development/Fit/Validation/Protected are explicit.
- **S4-AC-03:** Protected evaluation data cannot enter fit or selection.
- **S4-AC-04:** Label availability / target knowledge is causally enforced.
- **S4-AC-05:** Walk-forward ordering is strictly causal.
- **S4-AC-06:** Rolling and expanding modes are deterministic and explicit.
- **S4-AC-07:** Purging correctly removes overlapping-information samples.
- **S4-AC-08:** Embargo semantics are explicit and tested.
- **S4-AC-09:** No random-shuffle validation path can masquerade as OOS.
- **S4-AC-10:** Deterministic simple baseline catalog exists.
- **S4-AC-11:** Baselines never consume future labels.
- **S4-AC-12:** Cold-start/missingness is fail-closed or explicit.
- **S4-AC-13:** Continuous baseline metrics are deterministic and tested.
- **S4-AC-14:** Probability calibration diagnostics are deterministic and tested.
- **S4-AC-15:** Per-fold distributions remain visible.
- **S4-AC-16:** Fold aggregation weighting is explicit.
- **S4-AC-17:** Stability diagnostics do not fabricate universal pass/fail thresholds.
- **S4-AC-18:** Comparisons reject incompatible evaluation populations/boundaries.
- **S4-AC-19:** Protected-test result cannot be used to choose a winner.
- **S4-AC-20:** Candidate identity is version-specific and deterministic.
- **S4-AC-21:** Evaluation provenance binds material inputs/config/results.
- **S4-AC-22:** Search-family history is preserved.
- **S4-AC-23:** Repeated identical runs reproduce all scientific identities/results.
- **S4-AC-24:** No ML Engine or operational Strategy/Risk path exists.
- **S4-AC-25:** No financial authority or external side effect exists.
- **S4-AC-26:** No new recurring cost exists (`ADDITIONAL_RECURRING_COST = ZERO`, `NEW_RUNTIME_DEPENDENCIES = 0`).
- **S4-AC-27:** All applicable S1/S2/S3 regressions remain green.
- **S4-AC-28:** Capability matrix, code, tests and final acceptance agree.
- **S4-AC-29:** No Foundation artifact is silently rewritten.
- **S4-AC-30:** Sprint 5 remains unauthorized.
