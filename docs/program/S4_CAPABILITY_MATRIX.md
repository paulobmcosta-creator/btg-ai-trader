# Sprint 4 Capability Matrix — Statistical Baselines

## Positive capabilities

| Capability ID | Name | Classification | Governing Rule / Contract | Implementation Module | Evidence / Test Mapping | Status |
|---|---|---|---|---|---|---|
| S4-AC-01 | Exact Sprint 3 lineage and Entry Gate valid | REQUIRED | Protocol 0E-H, S4-AC-01 | `docs/program/S4_ENTRY_GATE.md` | Verification against canonical base SHA | REQUIRED |
| S4-AC-02 | Evaluation roles Development/Fit/Validation/Protected explicit | REQUIRED | Protocol 0E-C, C-HQI-02, C-HQI-03 | `btg_ai_trader.statistical_baselines.domain` | `tests/test_statistical_baselines_domain.py` | REQUIRED |
| S4-AC-03 | Protected evaluation data cannot enter fit or selection | REQUIRED | Protocol 0E-C, C-HQI-26, S4-D-01 | `btg_ai_trader.statistical_baselines.evaluation` | `tests/test_statistical_baselines_evaluation.py` | REQUIRED |
| S4-AC-04 | Label availability / target knowledge causally enforced | REQUIRED | Protocol 0E-B, Protocol 0E-C, S4-D-02 | `btg_ai_trader.statistical_baselines.domain`, `baselines` | `tests/test_statistical_baselines_leakage.py` | REQUIRED |
| S4-AC-05 | Walk-forward ordering strictly causal | REQUIRED | Protocol 0E-C, PR-0E-C-02, C-HQI-07 | `btg_ai_trader.statistical_baselines.splits` | `tests/test_statistical_baselines_splits.py` | REQUIRED |
| S4-AC-06 | Rolling and expanding modes deterministic and explicit | REQUIRED | Protocol 0E-C, DD-85 | `btg_ai_trader.statistical_baselines.splits` | `tests/test_statistical_baselines_splits.py` | REQUIRED |
| S4-AC-07 | Purging correctly removes overlapping-information samples | REQUIRED | Protocol 0E-C, DD-87, C-HQI-10 | `btg_ai_trader.statistical_baselines.splits` | `tests/test_statistical_baselines_splits.py` | REQUIRED |
| S4-AC-08 | Embargo semantics explicit and tested | REQUIRED | Protocol 0E-C, DD-88 | `btg_ai_trader.statistical_baselines.splits` | `tests/test_statistical_baselines_splits.py` | REQUIRED |
| S4-AC-09 | No random-shuffle validation path can masquerade as OOS | REQUIRED | Protocol 0E-C, C-HQI-08, S4-D-04 | `btg_ai_trader.statistical_baselines.splits` | `tests/test_statistical_baselines_splits.py` | REQUIRED |
| S4-AC-10 | Deterministic simple baseline catalog exists | REQUIRED | Protocol 0E-C, DD-73, DD-90 | `btg_ai_trader.statistical_baselines.baselines` | `tests/test_statistical_baselines_catalog.py` | REQUIRED |
| S4-AC-11 | Baselines never consume future labels | REQUIRED | Protocol 0E-A, Protocol 0E-B, S4-D-02 | `btg_ai_trader.statistical_baselines.baselines` | `tests/test_statistical_baselines_leakage.py` | REQUIRED |
| S4-AC-12 | Cold-start/missingness is fail-closed or explicit | REQUIRED | Protocol 0E-C, S4-D-05 | `btg_ai_trader.statistical_baselines.baselines` | `tests/test_statistical_baselines_catalog.py` | REQUIRED |
| S4-AC-13 | Continuous baseline metrics are deterministic and tested | REQUIRED | Protocol 0E-E, DD-75, S4-D-07 | `btg_ai_trader.statistical_baselines.metrics` | `tests/test_statistical_baselines_metrics.py` | REQUIRED |
| S4-AC-14 | Probability calibration diagnostics are deterministic and tested | REQUIRED | Protocol 0E-C, C-HQI-22, S4-D-09 | `btg_ai_trader.statistical_baselines.calibration` | `tests/test_statistical_baselines_calibration.py` | REQUIRED |
| S4-AC-15 | Per-fold distributions remain visible | REQUIRED | Protocol 0E-C, C-HQI-24, S4-D-10 | `btg_ai_trader.statistical_baselines.evaluation` | `tests/test_statistical_baselines_evaluation.py` | REQUIRED |
| S4-AC-16 | Fold aggregation weighting is explicit | REQUIRED | Protocol 0E-C, S4-AC-16 | `btg_ai_trader.statistical_baselines.evaluation` | `tests/test_statistical_baselines_evaluation.py` | REQUIRED |
| S4-AC-17 | Stability diagnostics do not fabricate universal pass/fail thresholds | REQUIRED | Protocol 0E-C, DD-91 | `btg_ai_trader.statistical_baselines.evaluation` | `tests/test_statistical_baselines_evaluation.py` | REQUIRED |
| S4-AC-18 | Comparisons reject incompatible evaluation populations/boundaries | REQUIRED | Protocol 0E-C, C-HQI-20, S4-D-11 | `btg_ai_trader.statistical_baselines.comparison` | `tests/test_statistical_baselines_comparison.py` | REQUIRED |
| S4-AC-19 | Protected-test result cannot be used to choose a winner | REQUIRED | Protocol 0E-C, C-HQI-26, S4-D-12 | `btg_ai_trader.statistical_baselines.comparison` | `tests/test_statistical_baselines_comparison.py` | REQUIRED |
| S4-AC-20 | Candidate identity is version-specific and deterministic | REQUIRED | Protocol 0E-A, C-HQI-06, S4-D-13 | `btg_ai_trader.statistical_baselines.domain` | `tests/test_statistical_baselines_domain.py` | REQUIRED |
| S4-AC-21 | Evaluation provenance binds material inputs/config/results | REQUIRED | ADR-0021, DD-15, S4-D-14 | `btg_ai_trader.statistical_baselines.provenance` | `tests/test_statistical_baselines_provenance.py` | REQUIRED |
| S4-AC-22 | Search-family history is preserved | REQUIRED | Protocol 0E-C, S4-D-13 | `btg_ai_trader.statistical_baselines.comparison` | `tests/test_statistical_baselines_comparison.py` | REQUIRED |
| S4-AC-23 | Repeated identical runs reproduce all scientific identities/results | REQUIRED | ADR-0017, DD-16, S4-D-06 | `btg_ai_trader.statistical_baselines.evaluation` | `tests/test_statistical_baselines_determinism.py` | REQUIRED |
| S4-AC-24 | No ML Engine or operational Strategy/Risk path exists | REQUIRED | AGENTS.md, DD-71 | `scripts/check_s4_boundary.py` | `tests/test_s4_boundary.py` | REQUIRED |
| S4-AC-25 | No financial authority or external side effect exists | REQUIRED | AGENTS.md, S4-NC-01..13 | `scripts/check_s4_boundary.py` | `tests/test_s4_boundary.py` | REQUIRED |
| S4-AC-26 | No new recurring cost exists | REQUIRED | AGENTS.md | `pyproject.toml` | Environment inspection | REQUIRED |
| S4-AC-27 | All applicable S1/S2/S3 regressions remain green | REQUIRED | Protocol 0E-H | Test suite | `tests/` full test run | REQUIRED |
| S4-AC-28 | Capability matrix, code, tests and final acceptance agree | REQUIRED | Protocol 0E-H | Repository audit | `docs/program/S4_FINAL_ACCEPTANCE.md` | REQUIRED |
| S4-AC-29 | No Foundation artifact is silently rewritten | REQUIRED | AGENTS.md | `scripts/check_foundation_contract.py` | `tests/test_foundation_contract.py` | REQUIRED |
| S4-AC-30 | Sprint 5 remains unauthorized | REQUIRED | Master Plan | Governance check | Final Acceptance audit | REQUIRED |

## Negative capabilities

| Negative Capability ID | Name | Enforcement Mechanism | Verifier / Test | Status |
|---|---|---|---|---|
| S4-NC-01 | Broker API absent | AST import check | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-02 | Account API absent | AST symbol check | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-03 | Order submission impossible | AST call check | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-04 | Order modification impossible | AST call check | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-05 | Order cancellation impossible | AST call check | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-06 | Real-money authority absent | Architectural prohibition | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-07 | Paper path absent | Namespace segregation | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-08 | Live path absent | Namespace segregation | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-09 | Risk operational path absent | AST symbol check | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-10 | Strategy operational path absent | AST symbol check | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-11 | Signal operational path absent | AST symbol check | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-12 | Canonical FinancialLedger mutation absent | Domain segregation | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-13 | External financial side effect absent | AST import check (`requests`, `httpx`, `aiohttp`, `socket`, `urllib.request`) | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-14 | ML Engine absent | AST import check (`sklearn`, `xgboost`, `lightgbm`, `tensorflow`, `torch`, `keras`) | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-15 | Model registry absent | Namespace segregation | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-16 | Hyperparameter search engine absent | Namespace segregation | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-17 | Random temporal shuffle validation forbidden | AST & domain check (`random.shuffle`, `sklearn.model_selection`) | `scripts/check_s4_boundary.py`, `tests/test_statistical_baselines_splits.py` | REQUIRED |
| S4-NC-18 | Protected-test candidate selection forbidden | Domain invariant | `tests/test_statistical_baselines_comparison.py` | REQUIRED |
| S4-NC-19 | Future-label leakage forbidden | Causal knowledge cutoff check | `tests/test_statistical_baselines_leakage.py` | REQUIRED |
| S4-NC-20 | Silent missing-data imputation forbidden | Cold start / fail-closed logic | `tests/test_statistical_baselines_catalog.py` | REQUIRED |
| S4-NC-21 | Silent OOS reuse after adaptation forbidden | Versioned candidate identity | `tests/test_statistical_baselines_domain.py` | REQUIRED |
| S4-NC-22 | Statistical significance claim without method forbidden | Descriptive reporting only | `tests/test_statistical_baselines_evaluation.py` | REQUIRED |
| S4-NC-23 | Automatic promotion from S4 forbidden | Governance invariant | `docs/program/S4_FINAL_ACCEPTANCE.md` | REQUIRED |
| S4-NC-24 | Network-dependent evaluation absent | Offline deterministic evaluation | `scripts/check_s4_boundary.py` | REQUIRED |
| S4-NC-25 | Paid external service absent | Dependency audit | `pyproject.toml` | REQUIRED |
