# Sprint 3 Capability Matrix — Deterministic Economic Backtesting

## Positive capabilities

| Capability ID | Name | Classification | Governing Rule / Contract | Implementation Module | Evidence / Test Mapping | Status |
|---|---|---|---|---|---|---|
| S3-AC-01 | Explicit deterministic backtest input boundary | REQUIRED | ADR-0017, DD-15, S3-AC-01 | `btg_ai_trader.backtesting.domain` | `tests/backtesting/test_backtesting_domain.py` | PASS |
| S3-AC-02 | Causal economic replay derived from accepted S2 semantics | REQUIRED | ADR-0004, ADR-0008, S3-AC-02 | `btg_ai_trader.backtesting.engine` | `tests/backtesting/test_engine.py` | PASS |
| S3-AC-03 | Explicit decision / order-ready / market-arrival / execution timing | REQUIRED | Protocol 0E-D, S3-AC-03, S3-D-06 | `btg_ai_trader.backtesting.domain`, `execution` | `tests/backtesting/test_execution.py` | PASS |
| S3-AC-04 | Side-aware executable price semantics | REQUIRED | Protocol 0E-D, S3-D-03, S3-AC-04 | `btg_ai_trader.backtesting.assumptions` | `tests/backtesting/test_assumptions.py` | PASS |
| S3-AC-05 | Explicit deterministic spread treatment | REQUIRED | Protocol 0E-D, S3-D-03, S3-D-14, S3-AC-05 | `btg_ai_trader.backtesting.assumptions` | `tests/backtesting/test_assumptions.py` | PASS |
| S3-AC-06 | Explicit configurable fee/cost model | REQUIRED | Protocol 0E-D, DD-74, DD-93 (NOT_TRIGGERED_AND_DEFERRED, REAL_HISTORICAL_B3_FEE_TABLE = NOT_PROVIDED), S3-D-08, S3-AC-06 | `btg_ai_trader.backtesting.assumptions` | `tests/backtesting/test_assumptions.py` | PASS |
| S3-AC-07 | Explicit deterministic adverse slippage model | REQUIRED | Protocol 0E-D, DD-74, DD-94, S3-D-07, S3-AC-07 | `btg_ai_trader.backtesting.assumptions` | `tests/backtesting/test_assumptions.py` | PASS |
| S3-AC-08 | Explicit deterministic latency model | REQUIRED | Protocol 0E-D, DD-95, S3-D-09, S3-AC-08 | `btg_ai_trader.backtesting.assumptions` | `tests/backtesting/test_assumptions.py` | PASS |
| S3-AC-09 | Fill / no-fill / indeterminate semantics | REQUIRED | Protocol 0E-D, S3-D-10, S3-AC-09 | `btg_ai_trader.backtesting.execution` | `tests/backtesting/test_execution.py` | PASS |
| S3-AC-10 | Simulated economic position accounting | REQUIRED | ADR-0014, ADR-0022, DD-46 (CANONICAL_DEFERRED, S3_LOCAL_SIMULATION_COST_BASIS = WACB), S3-D-11 | `btg_ai_trader.backtesting.accounting` | `tests/backtesting/test_accounting.py` | PASS |
| S3-AC-11 | Gross / net P&L with explicit economic units | REQUIRED | ADR-0022, DD-46, DD-47 (CANONICAL_DEFERRED, S3_LOCAL_SIMULATION_VALUATION_POLICY = BACKTEST_MARK_EVIDENCE), S3-D-11, S3-AC-11 | `btg_ai_trader.backtesting.accounting` | `tests/backtesting/test_accounting.py` | PASS |
| S3-AC-12 | Cost attribution without double counting | REQUIRED | Protocol 0E-D, DD-46 (CANONICAL_DEFERRED, S3_LOCAL_SIMULATION_COST_BASIS = WACB), S3-D-13, S3-D-14, S3-AC-12 | `btg_ai_trader.backtesting.accounting` | `tests/backtesting/test_accounting.py` | PASS |
| S3-AC-13 | Descriptive economic metrics | REQUIRED | Protocol 0E-D, S3-D-16, S3-AC-13 | `btg_ai_trader.backtesting.metrics` | `tests/backtesting/test_metrics.py` | PASS |
| S3-AC-14 | Future-data leakage protection | REQUIRED | Protocol 0E-A, Protocol 0E-B, S3-D-06 | `btg_ai_trader.backtesting.engine` | `tests/backtesting/test_leakage.py` | PASS |
| S3-AC-15 | Deterministic repeated execution | REQUIRED | ADR-0017, DD-16, S3-D-05, S3-AC-15 | `btg_ai_trader.backtesting.engine` | `tests/backtesting/test_determinism.py` | PASS |
| S3-AC-16 | Assumption sensitivity / cost stress | REQUIRED | Protocol 0E-D, S3-D-17 (Fee/Slippage Monotonicity & Latency Sensitivity), S3-AC-16 | `btg_ai_trader.backtesting.sensitivity` | `tests/backtesting/test_sensitivity.py` | PASS |
| S3-AC-17 | Lineage tracking | REQUIRED | ADR-0021, DD-15, S3-D-18, S3-AC-17 | `btg_ai_trader.backtesting.provenance` | `tests/backtesting/test_backtesting_provenance.py` | PASS |
| S3-AC-18 | Explicit end-of-window position policy | REQUIRED | Protocol 0E-D, DD-98 (NOT_TRIGGERED_AND_DEFERRED, S3_LOCAL_END_OF_WINDOW_POLICY = KEEP_OPEN), S3-D-15, S3-AC-18 | `btg_ai_trader.backtesting.accounting` | `tests/backtesting/test_accounting.py` | PASS |
| S3-AC-19 | Explicit handling of unavailable execution evidence | REQUIRED | Protocol 0E-D, S3-D-04, S3-AC-19 | `btg_ai_trader.backtesting.execution` | `tests/backtesting/test_execution.py` | PASS |
| S3-AC-20 | Final Gate B reconciliation | REQUIRED | Protocol 0E-H, S3-AC-20 | `docs/program/S3_FINAL_ACCEPTANCE.md` | Audit Verification | PASS |
| S3-AC-21 | Small-lot assumption | REQUIRED | Protocol 0E-D, S3-AC-21 | `btg_ai_trader.backtesting.assumptions` | `tests/backtesting/test_assumptions.py` | PASS |
| S3-AC-22 | Order types beyond MARKET | DEFERRED | Protocol 0E-D | N/A (Deferred) | `tests/backtesting/test_backtesting_domain.py` | DEFERRED |
| S3-AC-23 | Order book queue priority / depth fill | DEFERRED | Protocol 0E-D, DD-96 | N/A (Unsupported evidence) | N/A | DEFERRED |
| S3-AC-24 | Market impact model | DEFERRED | Protocol 0E-D, DD-97 | N/A (Unsupported evidence) | N/A | DEFERRED |
| S3-AC-25 | Candle intrabar trajectory execution | DEFERRED | Protocol 0E-D, DD-92 (TRIGGERED_AND_SATISFIED, BASELINE_PRECISE_EXECUTION = TICK) | `btg_ai_trader.backtesting.execution` | `tests/backtesting/test_execution.py` | DEFERRED |

## Negative capabilities

| Negative Capability ID | Name | Enforcement Mechanism | Verifier / Test | Status |
|---|---|---|---|---|
| S3-NC-01 | Broker API absent | AST import check | `scripts/check_s3_boundary.py` | VERIFIED |
| S3-NC-02 | Order submission/modification/cancel impossible | AST call check | `scripts/check_s3_boundary.py` | VERIFIED |
| S3-NC-03 | Paper trading absent | Namespace segregation | `scripts/check_s3_boundary.py` | VERIFIED |
| S3-NC-04 | Live trading absent | Namespace segregation | `scripts/check_s3_boundary.py` | VERIFIED |
| S3-NC-05 | Real money authority absent | Architectural prohibition | `scripts/check_s3_boundary.py` | VERIFIED |
| S3-NC-06 | Strategy operational path absent | AST symbol check | `scripts/check_s3_boundary.py` | VERIFIED |
| S3-NC-07 | Signal operational path absent | AST symbol check | `scripts/check_s3_boundary.py` | VERIFIED |
| S3-NC-08 | Risk operational path absent | AST symbol check | `scripts/check_s3_boundary.py` | VERIFIED |
| S3-NC-09 | Financial Ledger mutation absent | Domain segregation | `scripts/check_s3_boundary.py` | VERIFIED |
| S3-NC-10 | Network side effects absent | AST import check (`requests`, `httpx`, `aiohttp`, `socket`, `urllib.request`) | `scripts/check_s3_boundary.py` | VERIFIED |
| S3-NC-11 | Wall-clock causality absent | AST call check (`time.sleep`, `datetime.now`, `time.time`) | `scripts/check_s3_boundary.py` | VERIFIED |
| S3-NC-12 | Paid external services absent | Architectural audit | `pyproject.toml` | VERIFIED |
| S3-NC-13 | Predictive ML absent | AST import / code audit | `scripts/check_s3_boundary.py` | VERIFIED |
| S3-NC-14 | Silent missing data imputation forbidden | Strict fail-closed logic | `tests/backtesting/test_execution.py` | PASS |
| S3-NC-15 | Future data leakage forbidden | Monotonic cutoff enforcement | `tests/backtesting/test_leakage.py` | PASS |
| S3-NC-16 | Favorable unknown resolution forbidden | Conservative fail-closed | `tests/backtesting/test_execution.py` | PASS |
| S3-NC-17 | Mid-price aggressive fill forbidden | Side-aware Ask/Bid logic | `tests/backtesting/test_assumptions.py` | PASS |
| S3-NC-18 | Same-close execution without causal proof forbidden | Explicit causal latency | `tests/backtesting/test_execution.py` | PASS |
| S3-NC-19 | Tick volume as accessible liquidity forbidden | Small-lot assumption | `tests/backtesting/test_assumptions.py` | PASS |
| S3-NC-20 | Unbounded linear capacity assumption forbidden | Small-lot assumption | `tests/backtesting/test_assumptions.py` | PASS |
| S3-NC-21 | Random number generator in baseline absent | AST call check (`random.*`, `uuid.uuid4`, `secrets.*`, `os.urandom`) | `scripts/check_s3_boundary.py` | VERIFIED |
