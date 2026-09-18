# S4-ANTIGRAVITY-FULL-SPRINT — Full Sprint 4 Autonomous Execution Packet

```text
SPRINT = 4
WORK_MODE = LARGE_BATCH_AUTONOMOUS
IMPLEMENTATION_TOOL = ANTIGRAVITY
ISSUE = #73
CANONICAL_BRANCH = sprint/4-statistical-baselines
WORK_BRANCH = s4/00-full-statistical-baselines
CANONICAL_BASE_SHA = 922adee625029c0cbd6c665f8906e7fd99cf71cb
HUMAN_CHECKPOINTS_DURING_IMPLEMENTATION = NONE
INDEPENDENT_AUDIT = AFTER_FULL_SPRINT_CANDIDATE
MERGE = FORBIDDEN
ADDITIONAL_RECURRING_COST = ZERO
NEW_RUNTIME_DEPENDENCIES = 0
```

## 1. Execution Sequence

The full sprint execution proceeds across structured internal commit phases:

1. **Phase 1: Entry Gate, Contracts & Governance Materialization**
   - Materialize S4 entry gate (`docs/program/S4_ENTRY_GATE.md`), entry contract (`docs/program/S4_ENTRY_CONTRACT.md`), decision register (`docs/program/S4_DECISION_REGISTER.md`), capability matrix (`docs/program/S4_CAPABILITY_MATRIX.md`), sprint doc (`docs/sprints/SPRINT_4.md`), workstream packet (`docs/program/workstreams/S4-ANTIGRAVITY-FULL-SPRINT.md`), boundary checker `scripts/check_s4_boundary.py`, test suite `tests/test_s4_boundary.py`, CI workflow `.github/workflows/s4-python-ci.yml`, and update upstream verification triggers.
   - Evaluate Entry Gate against real remote state: PASS.

2. **Phase 2: Temporal Sample Domain & Evaluation Boundaries**
   - Implement `btg_ai_trader.statistical_baselines.domain`: `TargetSemantics`, `EvaluationRole`, `StatisticalSample`, `PredictionResult`, `CandidateIdentity`.
   - Implement `btg_ai_trader.statistical_baselines.boundaries`: `EvaluationBoundary`, `TemporalFold`, `WalkForwardPlan`.

3. **Phase 3: Walk-Forward Splitting, Rolling/Expanding, Purging & Embargo**
   - Implement `btg_ai_trader.statistical_baselines.splits`: `WindowPolicy`, `PurgePolicy`, `EmbargoPolicy`, `WalkForwardPlanner`.
   - Structural prohibition and rejection of random temporal shuffling.

4. **Phase 4: Deterministic Simple Baseline Catalog**
   - Implement `btg_ai_trader.statistical_baselines.baselines`:
     - Base `StatisticalBaseline` protocol/class with causal fit boundary enforcement.
     - `ConstantBaseline`
     - `PersistenceBaseline` / `LastObservedValueBaseline`
     - `HistoricalMeanBaseline`
     - `HistoricalMedianBaseline`
     - `HistoricalPriorProbabilityBaseline`
     - `MajorityClassBaseline`
     - `LastKnownClassBaseline`
   - Explicit cold-start and missingness handling.

5. **Phase 5: Metrics, Calibration Diagnostics & Fold Distributions**
   - Implement `btg_ai_trader.statistical_baselines.metrics`: continuous (MAE, MSE, RMSE, Mean Bias), binary probability (Brier score, Base Rate), categorical (Accuracy, Class Prevalence, Confusion Counts). Exact `Decimal` arithmetic.
   - Implement `btg_ai_trader.statistical_baselines.calibration`: `CalibrationBin`, `CalibrationReport`.
   - Implement `btg_ai_trader.statistical_baselines.evaluation`: `FoldEvaluationResult`, `AggregateEvaluationResult`, `StatisticalEvaluationEngine`.
   - Fold stability diagnostics without fabricating universal pass/fail thresholds.

6. **Phase 6: Comparison, Search Family & Protected Test Invariant**
   - Implement `btg_ai_trader.statistical_baselines.comparison`: `Comparator` with strict experimental parity checking, `SearchFamily`.
   - Structural protection preventing candidate selection over `PROTECTED_TEST` results.

7. **Phase 7: Provenance, Input Boundary & Manifests**
   - Implement `btg_ai_trader.statistical_baselines.provenance`: `StatisticalEvaluationInputBoundary`, `StatisticalEvaluationManifest` with SHA-256 root digest.
   - Deterministic serialization and repeatability tests.

8. **Phase 8: Comprehensive Tests, Adversarial Leakage Tests & Boundary Verification**
   - Full test suite covering 100% statement and branch coverage of the new package and scanner.
   - Metamorphic tests for future label perturbations.
   - Run full regression suite (S1, S2, S3, S4, foundation, linters, types, compile, boundary scanners).

9. **Phase 9: Final Acceptance, PR Creation & Closure Candidate Reporting**
   - Materialize `docs/program/S4_FINAL_ACCEPTANCE.md`.
   - Update living docs (`AGENTS.md`, `docs/program/PROGRAM_EXECUTION.md`, `docs/BTG_AI_TRADER_MASTER_PLAN.md`).
   - Push commits and open single candidate PR (`head: s4/00-full-statistical-baselines`, `base: sprint/4-statistical-baselines`).
   - Verify remote CI and upstream verification runs.
   - Update Issue #73.
   - Produce final execution report.
