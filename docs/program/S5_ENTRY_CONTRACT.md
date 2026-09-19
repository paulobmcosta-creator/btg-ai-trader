# Sprint 5 Entry Contract — ML Engine

## Authority and baseline

```text
SPRINT_4_FINAL_VERDICT = PASS
SPRINT_4_ACCEPTED_FUNCTIONAL_MERGE = 0786ace3e6a83ecb23a508af860f43a2fd5d64e8
SPRINT_5_REQUIRED_BASE_SHA = 560dd83cdfdd50084ae277083d9f8732e5296356
CANONICAL_SPRINT_5_BRANCH = sprint/5-ml-engine
WORK_BRANCH = s5/00-full-ml-engine
ISSUE = #77
FINANCIAL_AUTHORITY = ABSENT
REAL_MONEY = FORBIDDEN
PAPER_TRADING = FORBIDDEN
LIVE_TRADING = FORBIDDEN
STRATEGY_OPERATIONAL_PATH = FORBIDDEN
RISK_OPERATIONAL_PATH = FORBIDDEN
BROKER_ORDER_API = FORBIDDEN
ADDITIONAL_RECURRING_COST = ZERO
NEW_MANDATORY_RUNTIME_DEPENDENCIES = 0
```

This contract governs Sprint 5 — **ML Engine**. It is derived from the accepted and formally closed Sprint 4 state (`560dd83cdfdd50084ae277083d9f8732e5296356`), the frozen Foundation, `AGENTS.md`, the living Master Plan, Quantitative Protocols 0E-A, 0E-B, 0E-C, 0E-E, 0E-F, 0E-G, and 0E-H, and ADRs 0004, 0008, 0017, and 0021.

---

## 1. Mission and Classification

Sprint 5 constructs a **Research Machine Learning Engine** designed to answer a single quantitative question:

```text
Dadas features causalmente admissíveis e um target explícito,
um candidato de Machine Learning apresenta evidência preditiva
válida e comparável aos baselines sob separação temporal?
```

The output of Sprint 5 is strictly:
```text
prediction / probability / score
+
model evaluation evidence
+
provenance
+
model card
+
research registry record
```

Sprint 5 is formally classified as:
```text
SPRINT_5_CLASS = RESEARCH_ML_ENGINE_AND_PREDICTIVE_CANDIDATE_EVALUATION
STRATEGY_ENGINE = ABSENT
RISK_ENGINE = ABSENT
SCENARIO_ENGINE_FUNCTIONAL = ABSENT
PAPER_TRADER = ABSENT
LIVE_TRADER = ABSENT
BROKER_EXECUTION = ABSENT
ORDER_APIS = ABSENT
REAL_MONEY = ABSENT
FINANCIAL_LEDGER_MUTATION = ABSENT
MODEL_SERVING_ENDPOINT = ABSENT
PRODUCTION_DEPLOYMENT = ABSENT
AUTO_ML = ABSENT
REINFORCEMENT_LEARNING = ABSENT
NEURAL_NETWORKS = ABSENT
EXTERNAL_PAID_ML_PLATFORMS = ABSENT
```

---

## 2. Fundamental Epistemological Separation (Protocol 0E-F)

In strict accordance with Quantitative Protocol 0E-F:
```text
ModelEvaluation != StrategyEvaluation
EvaluationScope = EvaluationScope.MODEL
```

A favorable model evaluation:
- Does NOT imply a favorable strategy.
- Does NOT imply economic merit or positive trading P&L.
- Does NOT grant `PAPER_ELIGIBLE` status.
- Does NOT grant paper trading authorization.
- Does NOT grant financial execution authority.

Decision thresholds, position sizing, risk rules, and order generation belong to future stages (Sprint 7: Risk Engine; Sprint 8: Paper Trader; Strategy Engine). Sprint 5 models produce predictive scores, probabilities, and evaluation evidence only.

---

## 3. Scope Specification

### Included in Scope
1. **Causal Feature Pipeline:**
   - Strictly consumes `PredictionInput` or causal equivalents derived from `StatisticalSample`.
   - Never exposes `target_value`, `target_knowledge_time`, `audit_metadata`, or future labels to the predictor.
   - `FeatureSchema` defining name, feature type (`NUMERIC`, `CATEGORICAL`, `BOOLEAN`), missingness policy, and unknown-category policy.
   - Deterministic feature column ordering independent of dict insertion, hash randomization, or filesystem order.
   - Explicit missingness policies (`REJECT`, `CONSTANT`, `INDICATOR`); silent imputation is strictly forbidden.
   - Explicit unknown category policies (`REJECT`, `DECLARED_FALLBACK`); silent fallback without provenance is forbidden.
   - `FittedFeaturePipeline` derived exclusively from the training domain, carrying a content-addressed scientific digest.
2. **Explicit Target Contract:**
   - `TargetContract` binding `target_semantics` (`BINARY_PROBABILITY`, `CONTINUOUS`), target definition, forecast horizon, knowledge availability semantics, and contract digest.
   - No hardcoded universal financial target.
3. **Deterministic Predictive Candidate Catalog:**
   - Binary probability / classification:
     - `LogisticRegressionCandidate`
     - `RandomForestClassifierCandidate`
     - `GradientBoostingClassifierCandidate`
   - Continuous regression:
     - `RidgeRegressionCandidate`
     - `RandomForestRegressorCandidate`
     - `GradientBoostingRegressorCandidate`
   - Strict adherence to common `PredictiveCandidate` protocol.
   - Explicit allowlist of families; no dynamic estimator imports (`eval`, `exec`, arbitrary module loaders).
4. **Reproducibility, RNG & Determinism:**
   - Explicit `RNGContext` binding algorithm (`PCG64` / `MT19937` / integer seed), seed value, stream semantics, and library version for stochastic candidates (`RandomForest`, `GradientBoosting`).
   - Single-thread execution (`threadpoolctl`, `n_jobs=1`) to eliminate multi-threaded nondeterminism.
   - Prohibition of `BEST_SEED` selection: seeds cannot be treated as performance hyperparameters.
   - Exact numerical equivalence policy: stable Decimal conversion of float outputs via `NumericPolicy`.
5. **Model Training Input Boundary & Manifest:**
   - `ModelTrainingInputBoundary` binding ordered training samples, dataset digest, lineage digest, target contract, feature schema, fit boundary, cutoff, candidate spec, hyperparameters, RNG context, numeric policy, framework versions, and code revision.
   - `model_state_digest` extracting canonical learned state (coefficients, intercepts, tree structures) without relying on executable pickling.
   - `ModelTrainingManifest` capturing complete scientific training lineage with SHA-256 root digest.
6. **Finite Candidate Search & Search History:**
   - Explicit, finite, predeclared `ModelSearchSpace` with canonical ordering.
   - Append-only `ModelSearchHistory` preserving all attempted candidates, hyperparameter combinations, feature subsets, seeds, fit results, and failures (denominator of search is fully preserved).
7. **Validation-Only Selection & Protected Test Integration:**
   - `ModelSelectionPolicy` operating strictly on `EvaluationRole.VALIDATION_SELECTION`.
   - Protected test (`EvaluationRole.PROTECTED_TEST`) never participates in fitting, feature engineering, feature selection, hyperparameter selection, or candidate ranking.
   - Integration with Sprint 4 `EvaluationHistory`: reusing consumed protected evidence raises `ProtectedEvidenceReuseError`.
8. **Baseline Parity Comparison:**
   - Controlled comparison against Sprint 4 baselines (`HistoricalPriorProbabilityBaseline`, `HistoricalMeanBaseline`, `HistoricalMedianBaseline`) under strict experimental parity (identical populations, folds, targets, metrics, numeric policies).
9. **Metrics, Calibration & Ablation:**
   - Binary: Brier Score, Log Loss (explicit clipping), ROC-AUC (deterministic tie handling), Calibration ECE/MCE.
   - Continuous: MAE, MSE, RMSE, Mean Bias, optional R².
   - `FeatureAblationSpec` and `AblationResult` supporting incremental value verification.
   - Formal `ModelEvaluationDisposition` (`FAVORABLE`, `UNFAVORABLE`, `INCONCLUSIVE`, `INVALID`, `CONDITIONAL`).
10. **Research Model Registry & Model Card:**
    - `ResearchModelRegistry` providing append-only, content-addressed, immutable `ModelRecord` instances. Zero production serving, zero mutable aliases (`latest`, `champion`, `production`).
    - `ModelCard` with deterministic canonical serialization, explicit `EVALUATION_SCOPE = MODEL`, and explicit non-assessment declarations for strategy, economic value, paper eligibility, and live readiness.
11. **Scientific Provenance:**
    - Exact Git code revision binding.
    - Factual `EnvironmentFingerprint` (Python, scikit-learn, numpy, scipy, joblib, threadpoolctl).
12. **Zero Additional Cost:**
    - `ADDITIONAL_RECURRING_COST = ZERO`.
    - Purely open-source, locally executable Python stack (`scikit-learn==1.9.1`).

### Out of Scope (Absolute Prohibitions)
- Strategy operational logic, trading decisions, signal generation.
- Risk management engine, risk limits, risk veto, position sizing.
- Scenario Engine, regime switches, stress engine runtime.
- Broker connections, order placement, order modification/cancellation.
- Calls to `order_send`, `order_check`, or equivalent trading primitives.
- Real money, account balance mutation, `FinancialLedger` mutation.
- Paper trading, live execution, execution simulations with economic P&L.
- Model serving servers, REST inference microservices, cloud deployments.
- Mutable production alias pointers (`champion`, `latest`, `production`).
- Third-party experiment tracking platforms (MLflow, Weights & Biases, SageMaker, Vertex AI).
- Paid cloud APIs, commercial data feeds, or subscription services.
- AutoML, genetic algorithms, Bayesian optimization search engines.
- Neural networks, deep learning frameworks (PyTorch, TensorFlow, Keras), transformers, Reinforcement Learning.
- Unsafe executable deserialization (`pickle.loads`, `joblib.load` on arbitrary files).

---

## 4. Acceptance Criteria & Verification Structure

Sprint 5 verification requires:
1. Materialization of all 42 Positive Capabilities (`S5-AC-01` through `S5-AC-42`).
2. Structural enforcement of all 35 Negative Capabilities (`S5-NC-01` through `S5-NC-35`).
3. Static AST boundary scanner: `scripts/check_s5_boundary.py`.
4. Acceptance symbol verifier: `scripts/verify_s5_acceptance_symbols.py`.
5. 100% statement and 100% branch test coverage of `src/btg_ai_trader/ml_engine/`.
6. Full regression of S1, S2, S3, and S4 suites.
7. Exact-head CI clearance on GitHub Actions.
