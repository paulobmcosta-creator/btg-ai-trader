# Sprint 5 Decision Register — ML Engine

This register formalizes architectural and quantitative decisions whose first material dependency occurs in Sprint 5. Foundation decision IDs from `docs/foundation/0F-B_deferred_decision_register.md` are strictly preserved without renumbering.

---

## 1. Active Foundation Decisions Adjudicated in Sprint 5

| ID | Decision | Sprint 5 Adjudication Status | Decision / Adjudication Details | Scope / Boundary |
|---|---|---|---|---|
| **DD-13** | Algoritmo concreto de RNG para simulação | `TRIGGERED_AND_SATISFIED` | `RNGContext` materializa exclusivamente a semântica factual usada neste sprint: inteiro explícito fornecido ao `random_state` do scikit-learn (`algorithm = sklearn_random_state`), com seed, semântica de stream e versão de biblioteca. Famílias estocásticas exigem contexto RNG explícito. Não há claim de PCG64/MT19937 diretamente exercido pelo estimator. | Stochastic ML estimators |
| **DD-14** | Algoritmo de inicialização, derivação e particionamento de seeds | `TRIGGERED_AND_SATISFIED` | Seeds são predeclaradas no `MLCandidateSpec` e entram na identidade do candidato. `RNGContext.child_context()` deriva deterministicamente uma seed filha por SHA-256 do digest do contexto pai e do qualificador de stream. Espaços de busca que diferem apenas por seed são rejeitados, impedindo best-seed cherry-picking. O Sprint 5 não implementa seleção de seed por performance. | Seed governance & robustness |
| **DD-16** | Critérios de determinismo e replay / equivalência numérica | `TRIGGERED_AND_SATISFIED` | No mesmo ambiente factual (`EnvironmentFingerprint`), candidatos, fronteiras de treino, pipeline e seed idênticos produzem estado de modelo e saídas reproduzíveis nos testes repetidos. Predições numéricas são convertidas para `Decimal` sob `NumericPolicy`. Não há claim de equivalência byte-a-byte universal entre arquiteturas, BLAS distintos ou ambientes diferentes. | Numerical determinism |
| **DD-17** | Artifact registry | `TRIGGERED_AND_SATISFIED` | Implementado como `ResearchModelRegistry`, catálogo de pesquisa em memória e endereçado por digest. `ModelRecord` é imutável; não existe serving, deployment authority ou alias operacional mutável (`latest`, `champion`, `production`). Persistência física durável do registry não é claim deste sprint. | Research model registry |
| **DD-18** | Git / MLflow | `TRIGGERED_AND_SATISFIED` | A rastreabilidade S5 usa digests criptográficos locais e um campo explícito `code_revision` fornecido pelo chamador e incluído nas identidades. O engine não integra MLflow/W&B nem serviço externo de tracking. O código não valida, por si só, que `code_revision` corresponda a um commit Git existente; essa ligação é evidência de execução/CI. | Experiment tracking & registry |
| **DD-19** | Ambiente físico / paralelismo | `TRIGGERED_AND_SATISFIED` | CPU-only local execution. Multi-threaded race conditions are eliminated via `threadpoolctl` thread limitation and explicit estimator configuration (`n_jobs=1`). Multiprocessing candidate search and distributed GPU execution are excluded from this sprint. | Concurrency & execution |
| **DD-41** | Representação de versões | `TRIGGERED_AND_SATISFIED` | Content-addressed SHA-256 digests represent immutable identities of datasets, candidate specifications, fitted pipelines, trained model states, manifests, model cards, and records. Semantic versioning complements content digests without mutable pointer semantics. | Versioning & content-addressing |
| **DD-42** | Environment packaging | `TRIGGERED_AND_SATISFIED_FOR_S5_SCOPE` | O ambiente S5 é reproduzido por dependências pinadas no extra `ml` e registrado por `EnvironmentFingerprint` (Python, scikit-learn, NumPy, SciPy, joblib, threadpoolctl, plataforma e assinatura de threadpool). Não há claim de container universal nem equivalência entre ambientes diferentes. | Environment provenance |
| **DD-63** | Vinculação de model/version metadata | `TRIGGERED_AND_SATISFIED` | `ModelRecord` vincula deterministicamente `candidate_id`, `model_state_digest`, `training_input_boundary_digest`, `feature_pipeline_digest`, `target_contract_digest`, `rng_context`, `environment_fingerprint_digest`, `training_manifest_digest`, `evaluation_refs`, `model_card_digest` e `code_revision`. | Model artifact metadata |
| **DD-69** | Targets, labels e horizontes de previsão/decisão | `TRIGGERED_AND_SATISFIED` | Materialized as explicit, immutable `TargetContract` specifying `target_semantics` (`BINARY_PROBABILITY`, `CONTINUOUS`), target name, forecast/label horizon, knowledge availability semantics, and contract digest. No universal financial target is hardcoded. | Target specification contract |
| **DD-70** | Lista concreta de features e hiperparâmetros | `TRIGGERED_AND_SATISFIED` | O Sprint 5 materializa o contrato para listas **experiment-local** explícitas por `FeatureSchema`, `FeatureSpec`, `FeaturePipelineSpec` e `ModelSearchSpace` finito. Nenhuma lista universal de features/hiperparâmetros é hardcoded. AutoML e busca adaptativa não pertencem ao escopo. | Feature platform & search space |
| **DD-71** | Escolha de arquiteturas de modelos e algoritmos de ML | `TRIGGERED_AND_SATISFIED` | Supported catalog consists of 6 standard algorithms: `LogisticRegressionCandidate`, `RandomForestClassifierCandidate`, `GradientBoostingClassifierCandidate` (binary), and `RidgeRegressionCandidate`, `RandomForestRegressorCandidate`, `GradientBoostingRegressorCandidate` (continuous). Deep learning, neural networks, transformers, RL, XGBoost, and LightGBM are deferred. | ML candidate catalog |
| **DD-72** | ML library / framework | `TRIGGERED_AND_SATISFIED` | Resolved and pinned to `scikit-learn==1.9.1` (with `numpy==2.5.3`, `scipy==1.18.1`, `joblib==1.6.0`, `threadpoolctl==3.7.0`). Zero recurring cost, compatible with Python 3.12, declared under `[project.optional-dependencies] ml`. | ML runtime dependencies |
| **DD-105** | Métodos específicos de controle de multiplicidade | `CANONICAL_DEFERRED` | `ModelSearchHistory` preserva o denominador factual de tentativas (candidate spec, status, contexto de avaliação, falha e métricas), mas **não** implementa FDR/FWER, bootstrap múltiplo ou outro método inferencial de correção. Consequentemente, o Sprint 5 não produz claims de significância baseados nessa história. | Multiplicity control remains deferred |
| **DD-109** | Métricas preditivas por família | `TRIGGERED_AND_SATISFIED` | Explicit metric taxonomy: Binary Probability: Brier Score, Log Loss (with explicit clipping), ROC-AUC (deterministic tie handling), Calibration ECE/MCE. Continuous: MAE, MSE, RMSE, Mean Bias, optional R². Accuracy is prohibited as a sovereign promotion metric. | Evaluation metrics |
| **DD-110** | Thresholds de calibração / discriminação | `CANONICAL_DEFERRED` | O Sprint 5 calcula Brier, log loss, ROC-AUC e calibração, mas não fixa threshold numérico mínimo universal nem implementa promotion gate por threshold. A evidência permanece descritiva/comparativa; limiares específicos continuam decisão de experimento futuro. | Calibration/discrimination thresholds deferred |
| **DD-112** | Regras de penalização de complexidade algorítmica | `CANONICAL_DEFERRED` | `ModelComplexityDescriptor` apenas registra descritores factuais (família, features, parâmetros, árvores, profundidade). `ModelSelectionPolicy` seleciona por **uma métrica predeclarada e direção**, sem penalidade de complexidade. A regra quantitativa de penalização permanece adiada. | Complexity-penalty policy deferred |
| **DD-113** | Model drift / strategy decay | `CANONICAL_DEFERRED` | Detecção prospectiva de drift/decay, daemon de monitoramento, thresholds e alertas permanecem fora do Sprint 5. Nenhuma interface `DriftAssessment` é materializada neste sprint. | Drift/decay remains deferred |
| **DD-114** | Model Card storage / schema | `TRIGGERED_AND_SATISFIED_FOR_S5_SCOPE` | `ModelCard` materializa schema e serialização JSON determinística, digest endereçado por conteúdo, escopo `EvaluationScope.MODEL` e declarações explícitas de `NOT_ASSESSED`. O mecanismo de persistência física durável de cards permanece fora do claim S5. | Model Card schema/serialization |

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
Na orquestração `ModelEvaluationEngine`, o estado aprendido de preprocessing (normalização e vocabulários categóricos) é ajustado exclusivamente com a partição de treino devolvida por `WalkForwardPlanner.partition_samples()`. `FittedFeaturePipeline` isoladamente não recebe `EvaluationRole`; a garantia de role isolation pertence ao engine/planner e aos testes causais, não a uma exceção interna do pipeline.

### S5-D-03 — Causal prediction input surface
The predictive model interface consumes only `PredictionInput` or features extracted from it. Sample targets (`target_value`), label timestamps (`target_knowledge_time`), and audit metadata are structurally quarantined and inaccessible to the predictor.

### S5-D-04 — Deterministic feature ordering
Feature matrices ($X$) are constructed following an explicit, lexicographically stable feature schema order. Dict iteration, set ordering, hash randomization, or filesystem differences cannot alter column positioning.

### S5-D-05 — Explicit missingness and unknown category policies
Missing feature values must be handled via explicit policies: `REJECT`, `CONSTANT`, or `INDICATOR`. Silent mean imputation or zero fills are forbidden. Unknown categories encountered during inference must follow declared policies: `REJECT` or `DECLARED_FALLBACK`.

### S5-D-06 — Immutable TargetContract
Every training and evaluation run requires an explicit `TargetContract` defining target semantics, horizon, label semantics, and digest. Silent or implicit financial targets are prohibited.

### S5-D-07 — Verified ModelTrainingInputBoundary
`ModelTrainingInputBoundary.create_and_verify()` vincula IDs ordenados, dataset/source-lineage digests, target/pipeline/candidate digests, knowledge cutoff, numeric policy, environment fingerprint e code revision. Hyperparâmetros e RNG entram transitivamente pelo `candidate_spec_digest`. Construção direta ou `dataclasses.replace()` não herda o token de verificação; a imutabilidade normal é fornecida pelo dataclass frozen, sem claim de resistência a manipulação interna via `object.__setattr__`.

### S5-D-08 — Canonical model state digest
Trained models produce a deterministic SHA-256 `model_state_digest` extracted from learned parameters (coefficients, intercepts, tree structures, splits, thresholds) canonicalized as ordered bytes. Executable pickling is forbidden as an identity mechanism.

### S5-D-09 — Stochastic RNGContext & prohibition of best-seed selection
Stochastic estimators require an explicit integer seed wrapped in `RNGContext`. Searching across seeds to select the best-performing seed is prohibited as a selection policy (`S5-NC-26`).

### S5-D-10 — Single-thread deterministic execution
To ensure reproducibility across execution environments, estimators run with `n_jobs=1` and threadpools are capped via `threadpoolctl`. Multiprocessing candidate search is forbidden.

### S5-D-11 — Finite explicit search space & append-only history
Hyperparameter exploration uses a predeclared, finite `ModelSearchSpace`. `ModelSearchHistory` fornece uma API append-only que registra candidate spec, status de fit, role/contexto de avaliação, motivo de falha e métricas de validação. A identidade da feature pipeline entra pelo `MLCandidateSpec`; não há claim de armazenamento expandido da lista de features dentro de cada record. Failed fits podem ser registrados e permanecem no histórico.

### S5-D-12 — Validation-only candidate selection
Model selection occurs strictly on `EvaluationRole.VALIDATION_SELECTION`. Selection over `EvaluationRole.PROTECTED_TEST` raises `ValueError`.

### S5-D-13 — Protected evidence consumption enforcement
Protected test evidence is strictly confirmatory. If protected test results inform any candidate adaptation, the protected boundary is marked consumed; reusing consumed protected evidence raises `ProtectedEvidenceReuseError`.

### S5-D-14 — Strict baseline parity comparison
ML candidates must be compared against Sprint 4 baselines under identical populations, boundaries, folds, targets, and metric definitions. Comparisons violating parity fail closed with `ParityViolationError`.

### S5-D-15 — Research-only model registry
`ResearchModelRegistry` armazena `ModelRecord` imutável **em memória** e endereçado por digest. Não há persistência durável, REST serving, deployment ou ponteiro operacional mutável (`champion`, `latest`).

### S5-D-16 — Canonical ModelCard
`ModelCard` serializes to deterministic JSON and declares `EVALUATION_SCOPE = MODEL`, with explicit `NOT_ASSESSED` values for strategy, economic value, paper eligibility, and live readiness.

### S5-D-17 — Exact Decimal canonicalization via NumericPolicy
Predições/probabilidades provenientes do estimator são convertidas para Python `Decimal` sob `NumericPolicy`; métricas S5 também usam `Decimal`. Essa política suporta reprodutibilidade controlada no mesmo ambiente, mas não estabelece equivalência numérica universal entre arquiteturas ou bibliotecas lineares distintas.

### S5-D-18 — Zero additional recurring cost
The ML Engine utilizes `scikit-learn` and its pinned open-source dependencies (`numpy`, `scipy`, `joblib`, `threadpoolctl`). No paid APIs, SaaS trackers, or cloud subscriptions are introduced (`ADDITIONAL_RECURRING_COST = ZERO`).
