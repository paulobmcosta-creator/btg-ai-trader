# Sprint 5 — Final Acceptance Reconciliation

## 1. Scope and authority

```text
REPOSITORY = paulobmcosta-creator/btg-ai-trader
SPRINT_5_CANONICAL_BRANCH = sprint/5-ml-engine
CANONICAL_BASE_SHA = 560dd83cdfdd50084ae277083d9f8732e5296356
WORK_BRANCH = s5/00-full-ml-engine
ISSUE = #77
PR = #78
SPRINT_5_CLASS = SUPERVISED_TABULAR_ML_RESEARCH_ENGINE
ADDITIONAL_RECURRING_COST = ZERO
FINANCIAL_AUTHORITY = ABSENT
BROKER_ORDER_API = ABSENT
STRATEGY_OPERATIONAL_PATH = ABSENT
RISK_OPERATIONAL_PATH = ABSENT
PAPER_TRADING = FORBIDDEN
LIVE_TRADING = FORBIDDEN
REAL_MONEY = FORBIDDEN
SPRINT_5_LIFECYCLE = CLOSURE_CANDIDATE
MERGE_STATUS = PROHIBITED_PENDING_INDEPENDENT_AUDIT
```

Sprint 5 remains a research-only machine-learning layer. It does not create an operational strategy, risk authorization, order authority, paper execution path, live execution path, or financial-ledger mutation capability.

The canonical entry-gate and decision documents remain:

- `docs/program/S5_ENTRY_CONTRACT.md`
- `docs/program/S5_DECISION_REGISTER.md`
- `docs/program/S5_CAPABILITY_MATRIX.md`
- `docs/program/S5_ENTRY_GATE.md`
- `docs/program/workstreams/S5-ANTIGRAVITY-FULL-SPRINT.md`

This reconciliation is not a merge authorization. Exact-head CI and pinned upstream evidence must be green on the current PR head at the time of independent audit.

---

## 2. Implemented research surface

The implementation is contained in `src/btg_ai_trader/ml_engine/`, with eleven Python files including package initialization.

### Domain and scientific identity

`TargetContract` binds target name, target semantics, forecast horizon and target-knowledge delay.

`RNGContext` records the scikit-learn integer `random_state` seed semantics actually supplied to stochastic estimators. Child contexts are derived deterministically from the parent context digest and a stream qualifier.

`MLCandidateSpec` binds model family, hyperparameters, target contract, feature-pipeline specification digest, RNG context when applicable, numeric policy and code revision into deterministic candidate identity.

Configuration mappings are recursively frozen before they are retained as scientific identity.

### Feature pipeline

`FeatureSpec`, `FeatureSchema`, `FeaturePipelineSpec` and `FittedFeaturePipeline` implement explicit numeric, categorical and boolean feature handling.

Missingness is governed by `MissingnessPolicy.REJECT`, `MissingnessPolicy.CONSTANT` or `MissingnessPolicy.INDICATOR`. Unknown categorical values are governed by `UnknownCategoryPolicy.REJECT` or a declared fallback category.

Learned normalization statistics and categorical vocabularies are fit from the training partition only. Non-finite numeric values are rejected.

### Governed model families

The supported research candidates are:

- `LogisticRegressionCandidate`
- `RidgeRegressionCandidate`
- `RandomForestClassifierCandidate`
- `RandomForestRegressorCandidate`
- `GradientBoostingClassifierCandidate`
- `GradientBoostingRegressorCandidate`

`create_candidate()` is the governed factory. Stochastic families require an explicit `RNGContext`; best-seed search is prohibited structurally.

`extract_model_state_digest()` binds supported learned estimator state using SHA-256 with explicit array shape, dtype/endianness and canonical byte or text representation.

### Training provenance

`EnvironmentFingerprint` records sanitized reproducibility-relevant runtime evidence including Python, NumPy, SciPy, scikit-learn, joblib, threadpoolctl, platform and threadpool signature.

`ModelTrainingInputBoundary.create_and_verify()` validates the actual ordered training samples through the Sprint 4 statistical input-boundary machinery, binds dataset and source-lineage digests, enforces target availability at the training knowledge cutoff, and binds candidate, pipeline, environment and code revision.

A directly constructed or dataclass-replaced boundary does not inherit verified status.

`ModelTrainingManifest.create()` accepts only a verified boundary and checks candidate, target, feature pipeline, environment and code-revision parity before emitting its scientific-root digest.

### Search and selection

`ModelSearchSpace` is finite, deterministically ordered and rejects duplicate candidate identities. Candidate sets that differ only by random seed are rejected, preventing best-seed cherry-picking.

`ModelSearchHistory` is append-only through its public API, bound to one search space, and exposes immutable attempt records.

`ModelSelectionPolicy.select_best()` uses one predeclared metric and direction. Eligible successful records must all be `EvaluationRole.VALIDATION_SELECTION` and share one identical validation experimental-context fingerprint. Protected-test evidence is not eligible for model selection.

`ModelComplexityDescriptor` records factual complexity descriptors only; Sprint 5 does not impose a universal complexity penalty or automatic promotion rule.

### Temporal evaluation and Sprint 4 reuse

`ModelEvaluationEngine.evaluate_candidate()` reuses `WalkForwardPlanner.partition_samples()` and the `WalkForwardPlan` purge/embargo policies from Sprint 4. It does not implement a second independent temporal splitter.

Feature-pipeline fitting and model fitting occur on the canonical training partition for each fold. Validation and protected evaluation use the corresponding canonical partitions.

Protected evaluation requires the Sprint 4 `EvaluationHistory`. Adapted descendants informed by a protected boundary are not admissible against that same protected boundary; independent protected boundaries remain separately usable.

`compare_with_baseline()` accepts a real Sprint 4 `AggregateEvaluationResult` and fails closed unless candidate and baseline evidence match on role, aggregation policy, numeric policy, target contract, fold identities, population/plan context and requested metric.

`run_ablation()` performs validation-scope feature removal experiments. It does not claim permutation importance and does not use protected evidence for feature selection.

### Metrics, cards and registry

Sprint 5 provides deterministic Brier score, log loss, ROC AUC, calibration diagnostics, and continuous MAE/MSE/RMSE/bias/R² behavior where mathematically defined.

`ModelCard` is restricted to `EvaluationScope.MODEL`. Strategy value, economic value, paper eligibility and live readiness must remain `NOT_ASSESSED`.

`ResearchModelRegistry` is an immutable research catalog keyed by content digest. `ModelRecord.from_manifest()` requires a verified training manifest and a real model-card digest. Mutable operational aliases such as `latest`, `champion` and `production` are rejected.

---

## 3. Negative-capability enforcement

The Sprint 5 AST boundary verifier is `scripts/check_s5_boundary.py`.

It prohibits, within the ML engine boundary, broker/MT5 operational APIs, order/execution authority, Strategy/Risk/Ledger operational symbols, live/paper execution capability, deep-learning frameworks, AutoML/search frameworks outside the authorized surface, network clients, process execution, wall-clock dependence in scientific code, entropy sources, and unsafe dynamic/deserialization calls including `eval()`, `exec()`, `__import__()`, `importlib.import_module()`, pickle/joblib/cloudpickle/dill loading surfaces.

The implementation therefore remains research-only and read-only with respect to financial authority.

---

## 4. Adversarial evidence

The current suite includes explicit evidence for the material audit findings:

- `test_adversarial_future_label_rejected_and_prediction_surface_has_no_target` — future target knowledge is rejected and prediction inputs expose no target.
- `test_protected_lineage_blocks_adapted_candidate_but_allows_independent_boundary` — protected evidence lineage is enforced through Sprint 4 `EvaluationHistory`.
- `test_adversarial_best_seed_is_rejected_at_search_space_construction` — candidates differing only by RNG seed cannot form a search space.
- `test_adversarial_twenty_repeated_fits_are_digest_identical` — all six governed model families reproduce identical learned-state digests across repeated same-environment fits.
- `test_adversarial_hundred_feature_pipeline_replays_are_identical` — repeated feature-pipeline fits/transforms are deterministic under identical input and environment.
- `test_adversarial_model_card_rejects_strategy_scope` — strategy-scope claims are rejected by the model-card contract.
- `tests/test_ml_engine_coverage_final.py` — exercises the remaining fail-closed branches for evaluation parity, provenance, model guards, missingness and registry identity.
- `tests/test_s5_boundary.py` — includes negative tests for prohibited dynamic loading and unsafe deserialization.
- `tests/test_s5_acceptance_symbols.py` — rejects phantom acceptance paths/classes/functions/methods/enums/tests.

---

## 5. Verified implementation evidence before documentary reconciliation

The implementation evidence head immediately preceding this documentary reconciliation was:

```text
IMPLEMENTATION_EVIDENCE_HEAD = 7b5eb613cdfa4e39cbebf8ac6dae97bb9c9ce08d
SPRINT_5_PYTHON_CI_RUN = 35386732738
PINNED_UPSTREAM_RUN = 35386727326
```

Verified results on that implementation head:

```text
FULL_REPOSITORY_TESTS = 1063 PASSED
FULL_REPOSITORY_TEST_FAILURES = 0
FULL_REPOSITORY_WARNINGS = 1

S5_COVERAGE_TESTS = 87 PASSED
S5_PACKAGE_STATEMENTS = 1452 / 1452
S5_PACKAGE_BRANCHES = 468 / 468
S5_PACKAGE_COVERAGE = 100.00%

RUFF = PASS
MYPY_STRICT = PASS (151 source files)
COMPILE = PASS
DEPENDENCIES = PASS
FOUNDATION_GATE = PASS
S1_BOUNDARY = PASS
S2_BOUNDARY = PASS
S3_BOUNDARY = PASS
S4_BOUNDARY = PASS
DIFF_GATE = PASS

PINNED_UPSTREAM_DOCS = PASS
PINNED_UPSTREAM_CI = PASS
```

On that head, the only failing S5 CI matrix job was the acceptance-symbol verifier because this document still cited six superseded test names. This reconciliation removes those stale references. The current PR head must be revalidated after this documentary commit; no prior run is treated as evidence for a later SHA.

---

## 6. Claims explicitly not made

Sprint 5 does **not** establish:

- profitable trading edge;
- economic superiority;
- statistical significance or inferential certainty;
- strategy quality;
- risk fitness;
- paper-trading eligibility;
- live-trading readiness;
- model promotion to production;
- automatic model deployment;
- broker connectivity;
- FinancialLedger authority;
- Strategy, Signal, Risk, Paper or Live operational authority.

A predictive model ranking is not an economic-strategy ranking and is not a promotion decision.

---

## 7. Closure-gate disposition

```text
SPRINT_5_ENTRY_GATE = PASS
SPRINT_5_FUNCTIONAL_SCOPE = IMPLEMENTED
SPRINT_5_NEGATIVE_CAPABILITY_BOUNDARY = ENFORCED
SPRINT_5_IMPLEMENTATION_EVIDENCE = GREEN_EXCEPT_PRE_RECONCILIATION_DOC_SYMBOL_JOB
SPRINT_5_CLOSURE_GATE = CLOSURE_CANDIDATE
INDEPENDENT_CHATGPT_REAUDIT = REQUIRED
MERGE_RECOMMENDATION = NO
MERGE_AUTHORIZED = NO
SPRINT_5_FORMALLY_CLOSED = NO
PROMOTION_TO_SPRINT_6_GATE = NO
```

The next valid action is exact-head CI/upstream verification followed by independent reauditing of PR #78. Only after an independent PASS and explicit human merge authorization may Sprint 5 be merged and formally closed.
