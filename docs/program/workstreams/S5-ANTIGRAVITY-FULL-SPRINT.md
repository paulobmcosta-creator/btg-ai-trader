# S5-ANTIGRAVITY-FULL-SPRINT — Full Sprint 5 Autonomous Execution Packet

```text
SPRINT = 5
WORK_MODE = LARGE_BATCH_AUTONOMOUS
IMPLEMENTATION_TOOL = ANTIGRAVITY
ISSUE = #77
CANONICAL_BRANCH = sprint/5-ml-engine
WORK_BRANCH = s5/00-full-ml-engine
CANONICAL_BASE_SHA = 560dd83cdfdd50084ae277083d9f8732e5296356
HUMAN_CHECKPOINTS_DURING_IMPLEMENTATION = NONE
INDEPENDENT_AUDIT = AFTER_FULL_SPRINT_CANDIDATE
MERGE = FORBIDDEN
ADDITIONAL_RECURRING_COST = ZERO
NEW_MANDATORY_RUNTIME_DEPENDENCIES = 0
```

## 1. Execution Sequence

The full sprint execution proceeds across structured phases in a single autonomous work batch:

1. **Phase 1: Entry Gate, Contracts & Governance Materialization**
   - Materialize `docs/program/S5_ENTRY_CONTRACT.md`, `docs/program/S5_DECISION_REGISTER.md`, `docs/program/S5_CAPABILITY_MATRIX.md`, `docs/sprints/SPRINT_5.md`, `docs/program/workstreams/S5-ANTIGRAVITY-FULL-SPRINT.md`, and `docs/program/S5_ENTRY_GATE.md`.
   - Reconcile `pyproject.toml` with `[project.optional-dependencies] ml = [...]`.
   - Update `POST_S1_ROOTS` in `scripts/check_s1_boundary.py` to include `src/btg_ai_trader/ml_engine`.
   - Update living docs: `AGENTS.md`, `docs/program/PROGRAM_EXECUTION.md`, `docs/BTG_AI_TRADER_MASTER_PLAN.md`.
   - Validate Entry Gate preconditions: PASS.

2. **Phase 2: Domain, Causal Feature Pipeline & Target Contract**
   - Implement `btg_ai_trader.ml_engine.domain`: `TargetContract`, `FeatureType`, `MissingnessPolicy`, `UnknownCategoryPolicy`, `PredictiveCandidate`, `ModelEvaluationDisposition`.
   - Implement `btg_ai_trader.ml_engine.features`: `FeatureSpec`, `FeatureSchema`, `FeaturePipelineSpec`, `FittedFeaturePipeline`.
   - Ensure strict train-only fitting, deterministic column ordering, and explicit missingness/unknown policies.

3. **Phase 3: Machine Learning Candidate Models**
   - Implement `btg_ai_trader.ml_engine.models`:
     - Binary: `LogisticRegressionCandidate`, `RandomForestClassifierCandidate`, `GradientBoostingClassifierCandidate`.
     - Continuous: `RidgeRegressionCandidate`, `RandomForestRegressorCandidate`, `GradientBoostingRegressorCandidate`.
   - Enforce common interface, parameter validation, and canonical state digest extraction (`model_state_digest`) without unsafe pickling.

4. **Phase 4: Determinism, RNG Context, Thread Control & Numeric Policy**
   - Implement `RNGContext` with explicit algorithm, seed, stream semantics, and library version.
   - Enforce single-thread execution via `threadpoolctl` and `n_jobs=1`.
   - Enforce prohibition of `BEST_SEED` selection.
   - Exact Decimal canonical quantization of floating-point predictions and metrics via `NumericPolicy`.

5. **Phase 5: Training Input Boundary, Provenance & Training Manifest**
   - Implement `btg_ai_trader.ml_engine.provenance`: `ModelTrainingInputBoundary`, `ModelTrainingManifest`, `EnvironmentFingerprint`, `MLExperimentManifest`.
   - Bind dataset digest, lineage digest, candidate spec, hyperparameters, RNG context, cutoff, code revision, and SHA-256 root digest.

6. **Phase 6: Finite Candidate Search & Search History**
   - Implement `btg_ai_trader.ml_engine.selection`: `ModelSearchSpace`, `ModelSearchHistory`, `ModelSelectionPolicy`.
   - Maintain append-only search history preserving all candidates, configurations, seeds, and fit failures (full denominator of search).
   - Selection restricted strictly to `VALIDATION_SELECTION`.

7. **Phase 7: Metrics, Evaluation Engine, Baseline Parity & Protected Test**
   - Implement `btg_ai_trader.ml_engine.metrics`: continuous (MAE, MSE, RMSE, Mean Bias, R²), binary (Brier Score, Log Loss, ROC-AUC), calibration (ECE, MCE).
   - Implement `btg_ai_trader.ml_engine.evaluation`: `ModelEvaluationEngine`, `BaselineComparisonResult`, `FeatureAblationSpec`, `AblationResult`.
   - Controlled parity comparison with Sprint 4 baselines (`HistoricalPriorProbabilityBaseline`, `HistoricalMeanBaseline`, `HistoricalMedianBaseline`).
   - Protected test isolation: consuming protected evidence marks boundary consumed; reuse raises `ProtectedEvidenceReuseError`.

8. **Phase 8: Research Model Registry & Deterministic Model Card**
   - Implement `btg_ai_trader.ml_engine.registry`: `ResearchModelRegistry`, `ModelRecord`. Immutable, content-addressed, append-only, zero production serving, zero mutable aliases.
   - Implement `btg_ai_trader.ml_engine.model_card`: `ModelCard`, `ModelCardFactory`. Deterministic JSON serialization, explicit `EVALUATION_SCOPE = MODEL`, explicit non-assessment declarations.

9. **Phase 9: Comprehensive Test Suite & Boundary Checkers**
   - Implement unit, integration, metamorphic, and adversarial tests for 100% statement and branch coverage of `src/btg_ai_trader/ml_engine/`.
   - Implement `scripts/check_s5_boundary.py` (AST boundary scanner) and `scripts/verify_s5_acceptance_symbols.py` (acceptance symbol verifier).
   - Implement tests for boundary checkers (`tests/test_s5_boundary.py`, `tests/test_s5_acceptance_symbols.py`).
   - Run 20+ and 100 repeated determinism tests.

10. **Phase 10: Final Acceptance, PR Creation & Closure Candidate Report**
    - Materialize `docs/program/S5_FINAL_ACCEPTANCE.md`.
    - Update living docs to reflect `CLOSURE_CANDIDATE`.
    - Push commits to `origin/s5/00-full-ml-engine`.
    - Open Pull Request against `sprint/5-ml-engine`.
    - Verify exact-head CI clearance (Sprint 5 Python CI + upstream verification).
    - Deliver final factual consolidated execution report and STOP for independent audit.
