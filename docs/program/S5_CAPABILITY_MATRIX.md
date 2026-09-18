# Sprint 5 Capability Matrix — ML Engine

## Positive Capabilities (S5-AC-01 to S5-AC-42)

| Capability ID | Name | Classification | Governing Rule / Contract | Implementation Module | Evidence / Test Mapping | Status |
|---|---|---|---|---|---|---|
| **S5-AC-01** | S5 Entry Gate materialized and valid | REQUIRED | Protocol 0E-H, S5 Entry Contract | `docs/program/S5_ENTRY_GATE.md` | Verification against canonical base SHA | PASS |
| **S5-AC-02** | S5 Decision Register adjudicated | REQUIRED | Foundation 0F-B, S5 Decision Register | `docs/program/S5_DECISION_REGISTER.md` | Adjudication audit table | PASS |
| **S5-AC-03** | Feature-safe input contract | REQUIRED | Protocol 0E-B, Protocol 0E-C | `btg_ai_trader.ml_engine.domain` | `tests/test_ml_engine_features.py` | PASS |
| **S5-AC-04** | Immutable FeatureSchema | REQUIRED | Protocol 0E-A, DD-70 | `btg_ai_trader.ml_engine.features` | `tests/test_ml_engine_features.py` | PASS |
| **S5-AC-05** | Deterministic feature ordering | REQUIRED | ADR-0017, DD-16, DD-70 | `btg_ai_trader.ml_engine.features` | `tests/test_ml_engine_features.py` | PASS |
| **S5-AC-06** | Explicit missingness policy | REQUIRED | Protocol 0E-C, DD-70, S5-D-05 | `btg_ai_trader.ml_engine.features` | `tests/test_ml_engine_features.py` | PASS |
| **S5-AC-07** | Explicit unknown-category policy | REQUIRED | Protocol 0E-C, DD-70, S5-D-05 | `btg_ai_trader.ml_engine.features` | `tests/test_ml_engine_features.py` | PASS |
| **S5-AC-08** | Train-only feature pipeline fitting | REQUIRED | Protocol 0E-C, C-HQI-09, S5-D-02 | `btg_ai_trader.ml_engine.features` | `tests/test_ml_engine_evaluation.py` | PASS |
| **S5-AC-09** | Fitted feature pipeline digest | REQUIRED | ADR-0021, DD-41 | `btg_ai_trader.ml_engine.features` | `tests/test_ml_engine_features.py` | PASS |
| **S5-AC-10** | Explicit TargetContract | REQUIRED | Protocol 0E-A, DD-69, S5-D-06 | `btg_ai_trader.ml_engine.domain` | `tests/test_ml_engine_domain.py` | PASS |
| **S5-AC-11** | ML candidate identity | REQUIRED | Protocol 0E-A, DD-41, DD-63 | `btg_ai_trader.ml_engine.domain` | `tests/test_ml_engine_domain.py` | PASS |
| **S5-AC-12** | Stochastic RNG identity | REQUIRED | ADR-0017, DD-13, DD-14 | `btg_ai_trader.ml_engine.domain` | `tests/test_ml_engine_adversarial.py` | PASS |
| **S5-AC-13** | Deterministic library/environment fingerprint | REQUIRED | ADR-0021, DD-42 | `btg_ai_trader.ml_engine.provenance` | `tests/test_ml_engine_provenance.py` | PASS |
| **S5-AC-14** | Verified training input boundary | REQUIRED | ADR-0017, ADR-0021, DD-15 | `btg_ai_trader.ml_engine.provenance` | `tests/test_ml_engine_provenance.py` | PASS |
| **S5-AC-15** | Logistic Regression candidate | REQUIRED | Protocol 0E-A, DD-71 | `btg_ai_trader.ml_engine.models` | `tests/test_ml_engine_models.py` | PASS |
| **S5-AC-16** | Ridge Regression candidate | REQUIRED | Protocol 0E-A, DD-71 | `btg_ai_trader.ml_engine.models` | `tests/test_ml_engine_models.py` | PASS |
| **S5-AC-17** | Random Forest Classifier candidate | REQUIRED | Protocol 0E-A, DD-71 | `btg_ai_trader.ml_engine.models` | `tests/test_ml_engine_models.py` | PASS |
| **S5-AC-18** | Random Forest Regressor candidate | REQUIRED | Protocol 0E-A, DD-71 | `btg_ai_trader.ml_engine.models` | `tests/test_ml_engine_models.py` | PASS |
| **S5-AC-19** | Gradient Boosting Classifier candidate | REQUIRED | Protocol 0E-A, DD-71 | `btg_ai_trader.ml_engine.models` | `tests/test_ml_engine_models.py` | PASS |
| **S5-AC-20** | Gradient Boosting Regressor candidate | REQUIRED | Protocol 0E-A, DD-71 | `btg_ai_trader.ml_engine.models` | `tests/test_ml_engine_models.py` | PASS |
| **S5-AC-21** | Canonical prediction conversion | REQUIRED | ADR-0017, DD-16, S5-D-17 | `btg_ai_trader.ml_engine.models` | `tests/test_ml_engine_models.py` | PASS |
| **S5-AC-22** | Model-state digest extraction | REQUIRED | ADR-0021, DD-41, S5-D-08 | `btg_ai_trader.ml_engine.models` | `tests/test_ml_engine_models.py` | PASS |
| **S5-AC-23** | ModelTrainingManifest | REQUIRED | ADR-0021, DD-15 | `btg_ai_trader.ml_engine.provenance` | `tests/test_ml_engine_provenance.py` | PASS |
| **S5-AC-24** | Finite explicit ModelSearchSpace | REQUIRED | Protocol 0E-C, DD-70, S5-D-11 | `btg_ai_trader.ml_engine.selection` | `tests/test_ml_engine_selection.py` | PASS |
| **S5-AC-25** | Append-only ModelSearchHistory | REQUIRED | Protocol 0E-E, DD-105, S5-D-11 | `btg_ai_trader.ml_engine.selection` | `tests/test_ml_engine_selection.py` | PASS |
| **S5-AC-26** | Validation-only ModelSelection | REQUIRED | Protocol 0E-C, C-HQI-26, S5-D-12 | `btg_ai_trader.ml_engine.selection` | `tests/test_ml_engine_selection.py` | PASS |
| **S5-AC-27** | Protected-test integration | REQUIRED | Protocol 0E-C, C-HQI-03 | `btg_ai_trader.ml_engine.evaluation` | `tests/test_ml_engine_evaluation.py` | PASS |
| **S5-AC-28** | Protected evidence lineage enforcement | REQUIRED | Protocol 0E-C, S5-D-13 | `btg_ai_trader.ml_engine.evaluation` + Sprint 4 `EvaluationHistory` | `tests/test_ml_engine_evaluation.py` | PASS |
| **S5-AC-29** | Baseline parity comparison | REQUIRED | Protocol 0E-C, Protocol 0E-F, DD-73 | `btg_ai_trader.ml_engine.evaluation` | `tests/test_ml_engine_evaluation.py` | PASS |
| **S5-AC-30** | Classification metrics (Brier, LogLoss, ROC-AUC) | REQUIRED | Protocol 0E-F, DD-109 | `btg_ai_trader.ml_engine.metrics` | `tests/test_ml_engine_metrics.py` | PASS |
| **S5-AC-31** | Regression metrics (MAE, MSE, RMSE, Mean Bias, R²) | REQUIRED | Protocol 0E-F, DD-109 | `btg_ai_trader.ml_engine.metrics` | `tests/test_ml_engine_metrics.py` | PASS |
| **S5-AC-32** | Calibration diagnostics | REQUIRED | Protocol 0E-C, C-HQI-22 | `btg_ai_trader.ml_engine.metrics` | `tests/test_ml_engine_metrics.py` | PASS |
| **S5-AC-33** | Feature ablation support | REQUIRED | Protocol 0E-F, PR-0E-F-04 | `btg_ai_trader.ml_engine.evaluation` | `tests/test_ml_engine_evaluation.py` | PASS |
| **S5-AC-34** | ModelEvaluation disposition | REQUIRED | Protocol 0E-F | `btg_ai_trader.ml_engine.evaluation` | `tests/test_ml_engine_evaluation.py` | PASS |
| **S5-AC-35** | ResearchModelRegistry | REQUIRED | ADR-0021, DD-17, S5-D-15 | `btg_ai_trader.ml_engine.registry` | `tests/test_ml_engine_registry.py` | PASS |
| **S5-AC-36** | Immutable ModelRecord | REQUIRED | ADR-0021, DD-17, S5-D-15 | `btg_ai_trader.ml_engine.registry` | `tests/test_ml_engine_registry.py` | PASS |
| **S5-AC-37** | Deterministic ModelCard | REQUIRED | DD-114, S5-D-16 | `btg_ai_trader.ml_engine.model_card` | `tests/test_ml_engine_model_card.py` | PASS |
| **S5-AC-38** | ML scientific provenance / manifest | REQUIRED | ADR-0021, DD-15 | `btg_ai_trader.ml_engine.provenance` | `tests/test_ml_engine_provenance.py` | PASS |
| **S5-AC-39** | Exact code-revision binding | REQUIRED | ADR-0021 | `btg_ai_trader.ml_engine.provenance` | `tests/test_ml_engine_provenance.py` | PASS |
| **S5-AC-40** | Deterministic repeated-run evidence | REQUIRED | ADR-0017, DD-16 | `btg_ai_trader.ml_engine.evaluation` | `tests/test_ml_engine_adversarial.py` | PASS |
| **S5-AC-41** | Data-snooping & search-family provenance | REQUIRED | Protocol 0E-E, DD-105 | `btg_ai_trader.ml_engine.selection` | `tests/test_ml_engine_selection.py` | PASS |
| **S5-AC-42** | Zero-additional-recurring-cost dependency profile | REQUIRED | AGENTS.md, DD-72, S5-D-18 | `pyproject.toml` | Environment inspection | PASS |

---

## Negative Capabilities (S5-NC-01 to S5-NC-35)

| Negative Capability ID | Name | Enforcement Mechanism | Verifier / Test | Status |
|---|---|---|---|---|
| **S5-NC-01** | No Strategy operational path | AST symbol & import check | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-02** | No StrategyDecision generation | AST symbol & instantiation check | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-03** | No TradeIntent generation | AST symbol & instantiation check | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-04** | No Risk operational path | AST symbol & import check | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-05** | No RiskDecision generation | AST symbol & instantiation check | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-06** | No RiskAuthorization generation | AST symbol & instantiation check | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-07** | No OrderIntent | AST symbol & instantiation check | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-08** | No OrderPlan | AST symbol & instantiation check | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-09** | No ExecutionOrder | AST symbol & instantiation check | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-10** | No broker account API | AST import & call check | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-11** | No broker order API | AST import & call check | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-12** | No order_send | AST call & name check | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-13** | No order modify / cancel | AST call & name check | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-14** | No Paper Trading | Namespace & symbol segregation | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-15** | No Live Trading | Namespace & symbol segregation | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-16** | No real money | Architectural prohibition | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-17** | No FinancialLedger mutation | Domain boundary check | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-18** | No external economic commitment | Network & execution prohibition | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-19** | No model serving endpoint | AST import check (`fastapi`, `flask`, `uvicorn`, `aiohttp.web`) | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-20** | No production deployment | Namespace segregation | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-21** | No production model alias | Registry invariant (`latest`, `champion`, `production` forbidden) | `tests/test_ml_engine_registry.py` | VERIFIED |
| **S5-NC-22** | No MLflow / W&B / cloud ML service | AST import check (`mlflow`, `wandb`, `boto3`, `google.cloud`) | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-23** | No paid ML dependency / service | Dependency inventory inspection | `pyproject.toml` | VERIFIED |
| **S5-NC-24** | No AutoML | Search space validation | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-25** | No adaptive protected-test search | Domain evaluation role check | `tests/test_ml_engine_evaluation.py` | VERIFIED |
| **S5-NC-26** | No best-seed selection | Selection policy check | `tests/test_ml_engine_selection.py` | VERIFIED |
| **S5-NC-27** | No protected-test feature fitting | Causal leakage check | `tests/test_ml_engine_evaluation.py` | VERIFIED |
| **S5-NC-28** | No protected-test hyperparameter selection | Causal leakage check | `tests/test_ml_engine_selection.py` | VERIFIED |
| **S5-NC-29** | No future-label predictor surface | PredictionInput interface enforcement | `tests/test_ml_engine_evaluation.py` | VERIFIED |
| **S5-NC-30** | No arbitrary estimator import | Allowlist check (`eval`, `exec`, dynamic `importlib`) | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-31** | No unsafe pickle/joblib artifact loading | AST call check (`pickle.loads`, `joblib.load`) | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-32** | No neural network / deep learning requirement | Framework boundary check (`torch`, `tensorflow`, `keras`) | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-33** | No Reinforcement Learning (RL) | AST symbol check (`gym`, `gymnasium`, `stable_baselines3`) | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-34** | No Scenario Engine implementation | Scope boundary check | `scripts/check_s5_boundary.py` | VERIFIED |
| **S5-NC-35** | No automatic PAPER_ELIGIBLE promotion | ModelCard & disposition validation | `tests/test_ml_engine_model_card.py` | VERIFIED |
