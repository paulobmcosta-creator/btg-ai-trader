# Sprint 4 Decision Register

This register activates and formalizes decisions whose first material dependency occurs in Sprint 4. Historical Foundation decision IDs from `docs/foundation/0F-B_deferred_decision_register.md` remain unchanged and are strictly preserved without renumbering.

## Active Foundation decisions

| ID | Decision | Sprint 4 adjudication | Trigger / boundary |
|---|---|---|---|
| DD-13 | Algoritmo concreto de RNG para simulação | `NOT_TRIGGERED_AND_DEFERRED` — Baselines in Sprint 4 are strictly deterministic without stochastic or pseudo-random generation. RNG is absent and forbidden in baseline kernel. | Statistical baseline catalog |
| DD-14 | Algoritmo de inicialização, derivação e particionamento de seeds | `NOT_TRIGGERED_AND_DEFERRED` — Deterministic run identities derived from content hashes (SHA-256) without PRNG seeds. Seed derivation remains deferred. | Deterministic evaluation runs |
| DD-15 | Formato físico e representação do RunInputBoundary | `TRIGGERED_AND_SATISFIED` — Materialized as `StatisticalEvaluationInputBoundary` binding dataset identity, candidate identity, walk-forward plan, purging/embargo policies, metric/calibration configs, code revision, and environment signature. | Statistical evaluation runner |
| DD-16 | Critérios de determinismo e replay | `TRIGGERED_AND_SATISFIED` — Strict value and manifest reproducibility across repeated identical runs; AST scanner excludes stochastic entropy sources (`random`, `uuid4`, `secrets`, `os.urandom`). Exact `Decimal` arithmetic for metrics. | Statistical determinism |
| DD-68 | Definição do ativo concreto e timeframe | `CANONICAL_DEFERRED`, `S4_LOCAL_ASSET_SPECIFICATION = EXPERIMENT_LOCAL` — Target asset and timeframe are parameterized per evaluation plan. No universal asset is frozen globally in Sprint 4. | Evaluation plan configuration |
| DD-69 | Especificação de targets, labels e horizontes de previsão/decisão | `TRIGGERED_AND_SATISFIED` — Materialized as `StatisticalTargetSemantics` (`CONTINUOUS`, `BINARY_PROBABILITY`, `CATEGORICAL`) with explicit `feature_knowledge_time` and `target_knowledge_time`. Canonical production targets remain deferred. | Sample domain contract |
| DD-70 | Lista concreta de features e hiperparâmetros | `NOT_TRIGGERED_AND_DEFERRED` — Feature engineering platforms, feature registries, and ML feature catalogs are deferred to Sprint 5. | Feature platform |
| DD-71 | Escolha de arquiteturas de modelos e algoritmos de ML | `NOT_TRIGGERED_AND_DEFERRED` — ML models (Random Forest, GBDT, XGBoost, Neural Networks) and logistic regression pipelines belong to Sprint 5. | Machine learning models |
| DD-73 | Escolha de comparadores e benchmarks específicos | `TRIGGERED_AND_SATISFIED` — Materialized as `StatisticalBaseline` catalog and `Comparator` contract enforcing strict experimental parity. | Model comparison kernel |
| DD-75 | Métricas estatísticas específicas e seus thresholds | `PARTIALLY_TRIGGERED` — Core deterministic metrics implemented: MAE, MSE, RMSE, Mean Bias (continuous); Brier score, Base Rate (probability); Accuracy, Class Prevalence, Confusion Counts (categorical). Universal promotional thresholds remain deferred. | Metric computation |
| DD-76 | Número de folds, seeds e cenários de robustez | `PARTIALLY_TRIGGERED` — Walk-forward plan specifies exact folds per run. PRNG seeds are untriggered (no RNG). Universal fold count remains deferred. | Walk-forward plan |
| DD-84 | Datas e intervalos exatos de divisão entre treino, validação e teste protegido | `CANONICAL_DEFERRED`, `S4_PARTITION_POLICY = EXPERIMENT_LOCAL` — Boundary intervals are explicitly declared in immutable `EvaluationBoundary` instances per evaluation plan. No global calendar dates frozen. | Evaluation boundaries |
| DD-85 | Proporções e tamanhos das janelas de amostragem | `TRIGGERED_AND_SATISFIED` — Both `EXPANDING` and `ROLLING` window policies are supported and explicitly configured in `WalkForwardPlan`. | Window policy |
| DD-86 | Número exato de dobras (folds) no walk-forward | `CANONICAL_DEFERRED`, `S4_FOLD_COUNT = EXPERIMENT_LOCAL` — Fold count is explicitly declared per plan (`len(plan.folds)`). Universal project-wide fold count remains deferred. | Walk-forward configuration |
| DD-87 | Método de purging e horizonte de purging | `TRIGGERED_AND_SATISFIED` — Configurable information-horizon purging removes samples whose label availability crosses evaluation boundaries (`target_knowledge_time > eval_start`). | Overlapping label handling |
| DD-88 | Método de embargo e duração de embargo | `TRIGGERED_AND_SATISFIED` — Configurable temporal embargo offsets evaluation or excludes post-training intervals to prevent serial autocorrelation. Zero embargo is valid only when explicitly declared. | Post-training separation |
| DD-89 | Definição algorítmica específica de regimes de volatilidade ou tendência | `NOT_TRIGGERED_AND_DEFERRED` — Market regime segmentation is deferred beyond Sprint 4. No post-hoc regime masking. | Regime segmentation |
| DD-90 | Lista e seleção de baselines e benchmarks específicos | `TRIGGERED_AND_SATISFIED` — Catalog of 7 deterministic baselines (`ConstantBaseline`, `PersistenceBaseline`, `HistoricalMeanBaseline`, `HistoricalMedianBaseline`, `HistoricalPriorProbabilityBaseline`, `MajorityClassBaseline`, `LastKnownClassBaseline`). | Baseline catalog |
| DD-91 | Thresholds numéricos de estabilidade entre folds | `PARTIALLY_TRIGGERED` — Factual stability diagnostics (worst fold, dispersion, range, sign consistency) implemented. Universal pass/fail stability thresholds remain deferred. | Fold stability analysis |

## Sprint 4 local implementation decisions

These local decisions govern Sprint 4 implementation and do not renumber Foundation DDs.

### S4-D-01 — Epistemological separation of data functions
In alignment with Protocol 0E-C, data roles are strictly partitioned into `Development`, `Training/Fit`, `Validation/Selection`, and `Protected Evaluation`. Protected test evidence cannot be used for parameter tuning, threshold optimization, or winner selection.

### S4-D-02 — Causal label availability enforcement
A sample's label may only be consumed in model fitting if `sample.target_knowledge_time <= training_knowledge_cutoff`. Look-ahead access raises `CausalLeakageError`.

### S4-D-03 — Immutable evaluation boundaries
Evaluation boundaries (`EvaluationBoundary`, `TemporalFold`, `WalkForwardPlan`) are frozen, immutable dataclasses with explicit inclusive/exclusive endpoint semantics.

### S4-D-04 — Prohibition of random cross-validation
Random shuffle cross-validation (`shuffle=True`, `random_split`) is prohibited for prospective confirmatory validation. Walk-forward analysis must be strictly chronological.

### S4-D-05 — Fail-closed missingness and cold start
If historical samples are insufficient (`count < min_samples`), baselines emit explicit `is_cold_start = True` with `None` output. Silent imputation is forbidden.

### S4-D-06 — Zero PRNG in baseline catalog
All Sprint 4 baselines are deterministic. No pseudo-random number generator, seed derivation, or stochastic execution is permitted.

### S4-D-07 — Exact Decimal precision for statistical metrics
Metrics and probabilities use Python `Decimal` with explicit rounding to guarantee cross-platform numerical stability and exact reproducibility.

### S4-D-08 — Segregation of economic and statistical metrics
Statistical metrics assess predictive accuracy. Financial metrics (Sharpe, Sortino, P&L, drawdown) belong to Sprint 3 and must not be conflated with baseline prediction metrics.

### S4-D-09 — Descriptive probability calibration diagnostics
`CalibrationReport` provides binned reliability diagnostics (observed frequency vs mean predicted probability) and Brier score. Learned ML calibrators are excluded.

### S4-D-10 — Factual fold distribution reporting
Per-fold results are reported as empirical vectors without fabricating unverified confidence intervals or p-values.

### S4-D-11 — Strict parity for model comparison
Candidates can only be compared when evaluated against identical populations, boundaries, folds, targets, and metric semantics. Mismatched comparisons fail closed as `INVALID`.

### S4-D-12 — Structural protection against protected test winner selection
Automated selection helpers reject results with role `PROTECTED_TEST`, raising `ProtectedTestSelectionViolationError`.

### S4-D-13 — Search family multiplicity tracking
The evaluation manifest records all candidates, baselines, and configurations evaluated within a `SearchFamily` to maintain scientific provenance.

### S4-D-14 — Cryptographic evaluation provenance
`StatisticalEvaluationManifest` binds the input boundary, per-fold evaluations, aggregate results, and code revision to produce a canonical SHA-256 root digest.
