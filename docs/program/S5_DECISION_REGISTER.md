# Sprint 5 Decision Register — ML Engine

This register formalizes architectural and quantitative decisions whose first material dependency occurs in Sprint 5. Foundation decision IDs from `docs/foundation/0F-B_deferred_decision_register.md` are strictly preserved without renumbering.

---

## 1. Active Foundation Decisions Adjudicated in Sprint 5

| ID | Decision | Sprint 5 Adjudication Status | Decision / Adjudication Details | Scope / Boundary |
|---|---|---|---|---|
| **DD-13** | Algoritmo concreto de RNG para simulação | `TRIGGERED_AND_SATISFIED` | Explicit `RNGContext` binding RNG algorithm provider (`PCG64`, `MT19937` or standard integer seed for scikit-learn `random_state`), explicit integer seed, stream semantics, and library version. Stochastic estimators (`RandomForest`, `GradientBoosting`) require a non-null explicit integer seed in `RNGContext`. | Stochastic ML estimators |
| **DD-14** | Algoritmo de inicialização, derivação e particionamento de seeds | `TRIGGERED_AND_SATISFIED` | Seeds are predeclared in candidate specifications and content-hashed into candidate identities. Selecting or cherry-picking the "best seed" as a performance hyperparameter is strictly prohibited (`S5-NC-26`). Multiple seeds for robustness must be evaluated and reported as an ensemble/replicate group across a predeclared seed set. | Seed governance & robustness |
| **DD-16** | Critérios de determinismo e replay / equivalência numérica | `TRIGGERED_AND_SATISFIED` | Within an identical `EnvironmentFingerprint`, repeated fits of identical candidates on identical training boundaries with identical seeds yield identical model state digests, predictions, and evaluation metrics. Predictions and probabilities are converted to Decimal via `NumericPolicy` (exact canonical quantization) before entering evaluation manifests. | Numerical determinism |
| **DD-17** | Artifact registry | `TRIGGERED_AND_SATISFIED` | Implemented as `ResearchModelRegistry` (in-memory / local semantic registry). Records are immutable, content-addressed, append-only `ModelRecord` instances. Production serving, deployment authority, and mutable aliases (`latest`, `champion`, `production`) are strictly forbidden. | Research model registry |
| **DD-18** | Git / MLflow | `TRIGGERED_AND_SATISFIED` | Research registry uses local cryptographic hashing and Git commit binding (`code_revision`). External SaaS platforms (MLflow, Weights & Biases, SageMaker, Vertex AI, Azure ML) are forbidden. Zero recurring monetary cost. | Experiment tracking & registry |
| **DD-19** | Ambiente físico / paralelismo | `TRIGGERED_AND_SATISFIED` | CPU-only local execution. Multi-threaded race conditions are eliminated via `threadpoolctl` thread limitation and explicit estimator configuration (`n_jobs=1`). Multiprocessing candidate search and distributed GPU execution are excluded from this sprint. | Concurrency & execution |
| **DD-41** | Representação de versões | `TRIGGERED_AND_SATISFIED` | Content-addressed SHA-256 digests represent immutable identities of datasets, candidate specifications, fitted pipelines, trained model states, manifests, model cards, and records. Semantic versioning complements content digests without mutable pointer semantics. | Versioning & content-addressing |
| **DD-42** | Environment packaging | `TRIGGERED_AND_SATISFIED` | Factual `EnvironmentFingerprint` capturing runtime environment: Python version, scikit-learn version, NumPy version, SciPy version, joblib version, threadpoolctl version, and platform OS family. Does not claim universal container portability. | Environment provenance |
| **DD-63** | Vinculação de model/version metadata | `TRIGGERED_AND_SATISFIED` | `ModelRecord` deterministically binds `candidate_id`, `model_state_digest`, `training_input_boundary_digest`, `feature_pipeline_digest`, `target_contract_digest`, `rng_context`, `environment_fingerprint`, `training_manifest_digest`, `evaluation_refs`, `model_card_digest`, and `code_revision`. | Model artifact metadata |
| **DD-69** | Targets, labels e horizontes de previsão/decisão | `TRIGGERED_AND_SATISFIED` | Materialized as explicit, immutable `TargetContract` specifying `target_semantics` (`BINARY_PROBABILITY`, `CONTINUOUS`), target name, forecast/label horizon, knowledge availability semantics, and contract digest. No universal financial target is hardcoded. | Target specification contract |
| **DD-70** | Lista concreta de features e hiperparâmetros | `TRIGGERED_AND_SATISFIED` | Materialized as `FeatureSchema`, `FeatureSpec`, `FeaturePipelineSpec`, and finite explicit `ModelSearchSpace`. AutoML, infinite continuous search, and adaptive Bayesian optimization are forbidden. Feature ordering is deterministic; missingness and unknown categories require explicit policies. | Feature platform & search space |
| **DD-71** | Escolha de arquiteturas de modelos e algoritmos de ML | `TRIGGERED_AND_SATISFIED` | Supported catalog consists of 6 standard algorithms: `LogisticRegressionCandidate`, `RandomForestClassifierCandidate`, `GradientBoostingClassifierCandidate` (binary), and `RidgeRegressionCandidate`, `RandomForestRegressorCandidate`, `GradientBoostingRegressorCandidate` (continuous). Deep learning, neural networks, transformers, RL, XGBoost, and LightGBM are deferred. | ML candidate catalog |
| **DD-72** | ML library / framework | `TRIGGERED_AND_SATISFIED` | Resolved and pinned to `scikit-learn==1.9.1` (with `numpy==2.5.3`, `scipy==1.18.1`, `joblib==1.6.0`, `threadpoolctl==3.7.0`). Zero recurring cost, compatible with Python 3.12, declared under `[project.optional-dependencies] ml`. | ML runtime dependencies |
| **DD-105** | Métodos específicos de controle de multiplicidade | `TRIGGERED_AND_SATISFIED` | Materialized as append-only `ModelSearchHistory` capturing the full denominator of candidate exploration: candidate specs, hyperparameter sets, feature subsets, seeds, fit attempts, failures, and validation results. Unverified statistical significance claims without formal correction are marked `INCONCLUSIVE` / `NOT_ASSESSED`. | Multiplicity & search history |
| **DD-109** | Métricas preditivas por família | `TRIGGERED_AND_SATISFIED` | Explicit metric taxonomy: Binary Probability: Brier Score, Log Loss (with explicit clipping), ROC-AUC (deterministic tie handling), Calibration ECE/MCE. Continuous: MAE, MSE, RMSE, Mean Bias, optional R². Accuracy is prohibited as a sovereign promotion metric. | Evaluation metrics |
| **DD-110** | Thresholds de calibração / discriminação | `TRIGGERED_AND_SATISFIED` | No hardcoded universal thresholds (e.g. AUC >= 0.60). Thresholds are declared in experiment-local policy. In the absence of predeclared thresholds, evaluation evidence remains descriptive/comparative without automatic promotional claims. | Decision thresholds |
| **DD-112** | Regras de penalização de complexidade algorítmica | `TRIGGERED_AND_SATISFIED` | Materialized as `ModelComplexityDescriptor` reporting factual complexity: family, feature count, parameter count, tree count, tree depth. Predeclared complexity handling in selection policy; no arbitrary universal penalty formulas. | Complexity quantification |
| **DD-113** | Model drift / strategy decay | `CANONICAL_DEFERRED` | Prospective runtime drift monitoring daemon and live alerting are deferred. Reference distribution contracts and factual `DriftAssessment` interfaces are supported for future baseline tracking. | Drift assessment interface |
| **DD-114** | Model Card storage / schema | `TRIGGERED_AND_SATISFIED` | Materialized as `ModelCard` with deterministic canonical JSON serialization, content-addressed digest, explicit `EVALUATION_SCOPE = EvaluationScope.MODEL`, and explicit non-assessment declarations for strategy, economic value, paper eligibility, and live execution. | Model Card schema |

---

## 2. Deferred Decisions Formally NOT TRIGGERED in Sprint 5

The following decisions remain unactivated because their operational boundaries belong to future sprints:

| ID | Decision | Status | Rationale |
|---|---|---|---|
| **DD-89** | Definição algorítmica de regimes de mercado | `NOT_TRIGGERED_AND_DEFERRED` | Belongs to Sprint 6 (Scenario Engine). No functional regime switching in S5. |
| **DD-107** | Risk-tail operational thresholds | `NOT_TRIGGERED_AND_DEFERRED` | Belongs to Sprint 7 (Risk Engine). S5 evaluates predictive models without financial risk limits. |
| **DD-111** | Strategy decision thresholds & position sizing | `NOT_TRIGGERED_AND_DEFERRED` | Belongs to Strategy Engine & Sprint 7. S5 does not generate trade signals or sizing. |
| **DD-115..120** | Paper Trading architecture and execution | `NOT_TRIGGERED_AND_DEFERRED` | Belongs to Sprint 8 (Paper Trader). No paper execution in S5. |
| **DD-121** | Risk Engine limits and circuit breakers | `NOT_TRIGGERED_AND_DEFERRED` | Belongs to Sprint 7 (Risk Engine). |
| **DD-123** | GUI trading automation | `NOT_TRIGGERED_AND_DEFERRED` | Out of scope for research ML engine. |
| **DD-124** | High Frequency Trading (HFT) infrastructure | `NOT_TRIGGERED_AND_DEFERRED` | Explicitly non-goal of project. |

---

## 3. Sprint 5 Local Implementation Decisions (S5-D-01 to S5-D-18)

These decisions govern the internal architecture of `src/btg_ai_trader/ml_engine/`:

### S5-D-01 — Epistemological separation of ModelEvaluation and StrategyEvaluation
In strict adherence to Quantitative Protocol 0E-F and QPI-08, `ModelEvaluation` evaluates predictive merit (`EvaluationScope.MODEL`). It does not evaluate strategy rules, economic P&L, risk controls, or trade decisions. A favorable model evaluation never implies `PAPER_ELIGIBLE` or execution readiness.

### S5-D-02 — Train-only feature pipeline fitting
Learned preprocessing state (scalers, encoders, imputation constants, category vocabularies) must be computed exclusively from the training domain (`EvaluationRole.TRAINING_FIT`). Fitting or adapting pipelines on validation or protected-test domains raises `CausalLeakageError`.

### S5-D-03 — Causal prediction input surface
The predictive model interface consumes only `PredictionInput` or features extracted from it. Sample targets (`target_value`), label timestamps (`target_knowledge_time`), and audit metadata are structurally quarantined and inaccessible to the predictor.

### S5-D-04 — Deterministic feature ordering
Feature matrices ($X$) are constructed following an explicit, lexicographically stable feature schema order. Dict iteration, set ordering, hash randomization, or filesystem differences cannot alter column positioning.

### S5-D-05 — Explicit missingness and unknown category policies
Missing feature values must be handled via explicit policies: `REJECT`, `CONSTANT`, or `INDICATOR`. Silent mean imputation or zero fills are forbidden. Unknown categories encountered during inference must follow declared policies: `REJECT` or `DECLARED_FALLBACK`.

### S5-D-06 — Immutable TargetContract
Every training and evaluation run requires an explicit `TargetContract` defining target semantics, horizon, label semantics, and digest. Silent or implicit financial targets are prohibited.

### S5-D-07 — Verified ModelTrainingInputBoundary
Model training requires a deeply frozen, content-addressed `ModelTrainingInputBoundary` binding ordered sample IDs, dataset digest, candidate specification, hyperparameters, RNG context, feature schema, cutoff, numeric policy, and code revision. Mutating a boundary invalidates its verification status.

### S5-D-08 — Canonical model state digest
Trained models produce a deterministic SHA-256 `model_state_digest` extracted from learned parameters (coefficients, intercepts, tree structures, splits, thresholds) canonicalized as ordered bytes. Executable pickling is forbidden as an identity mechanism.

### S5-D-09 — Stochastic RNGContext & prohibition of best-seed selection
Stochastic estimators require an explicit integer seed wrapped in `RNGContext`. Searching across seeds to select the best-performing seed is prohibited as a selection policy (`S5-NC-26`).

### S5-D-10 — Single-thread deterministic execution
To ensure reproducibility across execution environments, estimators run with `n_jobs=1` and threadpools are capped via `threadpoolctl`. Multiprocessing candidate search is forbidden.

### S5-D-11 — Finite explicit search space & append-only history
Hyperparameter exploration uses a predeclared, finite `ModelSearchSpace`. All attempted candidates, configurations, feature sets, fit results, and failures are recorded in append-only `ModelSearchHistory`. Failed fits are never dropped from the denominator.

### S5-D-12 — Validation-only candidate selection
Model selection occurs strictly on `EvaluationRole.VALIDATION_SELECTION`. Selection over `EvaluationRole.PROTECTED_TEST` raises `ValueError`.

### S5-D-13 — Protected evidence consumption enforcement
Protected test evidence is strictly confirmatory. If protected test results inform any candidate adaptation, the protected boundary is marked consumed; reusing consumed protected evidence raises `ProtectedEvidenceReuseError`.

### S5-D-14 — Strict baseline parity comparison
ML candidates must be compared against Sprint 4 baselines under identical populations, boundaries, folds, targets, and metric definitions. Comparisons violating parity fail closed with `ParityViolationError`.

### S5-D-15 — Research-only model registry
`ResearchModelRegistry` stores immutable `ModelRecord` entries in memory/local storage. No REST serving endpoints, no model deployment, and no mutable production pointers (`champion`, `latest`) exist.

### S5-D-16 — Canonical ModelCard
`ModelCard` serializes to deterministic JSON and declares `EVALUATION_SCOPE = MODEL`, with explicit `NOT_ASSESSED` values for strategy, economic value, paper eligibility, and live readiness.

### S5-D-17 — Exact Decimal canonicalization via NumericPolicy
All float predictions, probabilities, and evaluation metrics are converted to Python `Decimal` with explicit rounding via `NumericPolicy` before entering manifests and model cards, preventing cross-architecture float drift.

### S5-D-18 — Zero additional recurring cost
The ML Engine utilizes `scikit-learn` and its pinned open-source dependencies (`numpy`, `scipy`, `joblib`, `threadpoolctl`). No paid APIs, SaaS trackers, or cloud subscriptions are introduced (`ADDITIONAL_RECURRING_COST = ZERO`).
