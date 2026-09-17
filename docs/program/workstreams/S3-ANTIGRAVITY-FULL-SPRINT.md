# S3-ANTIGRAVITY-FULL-SPRINT — Full Sprint 3 Autonomous Execution Packet

```text
SPRINT = 3
WORK_MODE = LARGE_BATCH
IMPLEMENTATION_TOOL = ANTIGRAVITY
ISSUE = #71
CANONICAL_BRANCH = sprint/3-deterministic-economic-backtesting
WORK_BRANCH = s3/00-full-deterministic-economic-backtesting
CANONICAL_BASE_SHA = ba6c0c41988fc9fefbdff13b0daedf96301dd74c
HUMAN_CHECKPOINTS_DURING_IMPLEMENTATION = NONE
INDEPENDENT_AUDIT = AFTER_FULL_SPRINT_CANDIDATE
MERGE = FORBIDDEN
ADDITIONAL_RECURRING_COST = ZERO
NEW_RUNTIME_DEPENDENCIES = 0
```

## 1. Execution Sequence

The full sprint execution proceeds across six structured internal commit phases:

1. **Phase 1: Entry Gate & Governance Materialization**
   - Materialize S3 entry contracts, decision register, capability matrix, entry gate, boundary checker `scripts/check_s3_boundary.py`, test suite `tests/test_s3_boundary.py`, CI workflow `.github/workflows/s3-python-ci.yml`, and update upstream verification triggers.
   - Reconcile Sprint 2 living documents to `FORMALLY_CLOSED`.

2. **Phase 2: Backtesting Domain & Core Engine**
   - Implement `btg_ai_trader.backtesting.domain`: `BacktestAction`, `OrderStyle`, `Side`, `ExecutionOutcome`, `SimulatedFill`, `InstrumentEconomics`, `BacktestInputBoundary`.
   - Implement `btg_ai_trader.backtesting.execution`: Temporal matching, causal latency advance, fill logic.

3. **Phase 3: Execution Assumptions (Spread, Fees, Slippage, Latency, Fills)**
   - Implement `btg_ai_trader.backtesting.assumptions`:
     - `SpreadModel`: Side-aware pricing (Ask for BUY, Bid for SELL), spread validation.
     - `FeeSchedule`: Configurable per-unit, fixed, and basis-point fees.
     - `AdverseSlippageModel`: Purely deterministic adverse slippage (fixed points, fixed bps, zero slippage). Zero RNG.
     - `LatencyModel`: Deterministic virtual microsecond delays.
     - `ExecutionPolicy`: Small-lot assumption, fail-closed handling of missing/stale quotes, candle intrabar ambiguity handling.

4. **Phase 4: Simulated Accounting, P&L & Descriptive Metrics**
   - Implement `btg_ai_trader.backtesting.accounting`:
     - `BacktestPositionState`: Quantity tracking, moving weighted average cost basis, zero canonical FinancialLedger mutation.
     - `BacktestPnL`: Gross realized P&L, explicit fees, net realized P&L, diagnostic spread burden, diagnostic slippage burden.
     - `EndOfWindowPolicy`: Default `KEEP_OPEN`.
   - Implement `btg_ai_trader.backtesting.metrics`:
     - Descriptive statistics: gross P&L, net P&L, fees, turnover, fill count/rate, no-fill/indeterminate counts, win rate, profit factor, expectancy, max drawdown.

5. **Phase 5: Provenance, Sensitivity & Hardening**
   - Implement `btg_ai_trader.backtesting.provenance`: Full lineage `market_event -> research_action -> simulated_fill -> economic_result`, `BacktestRunManifest`.
   - Implement `btg_ai_trader.backtesting.sensitivity`: Deterministic cost/assumption stress testing with monotonicity assertions.
   - Implement `btg_ai_trader.backtesting.engine`: Unified `DeterministicEconomicBacktester` orchestrating replay, actions, execution, accounting, metrics, provenance.
   - Comprehensive test suite for determinism, leakage invariance, property tests, and 100% line/branch coverage.

6. **Phase 6: Final Reconciliation & S3 Closure Gate Candidate**
   - Materialize `docs/program/S3_FINAL_ACCEPTANCE.md`.
   - Update living docs (`AGENTS.md`, `docs/program/PROGRAM_EXECUTION.md`, `docs/BTG_AI_TRADER_MASTER_PLAN.md`).
   - Open single PR against `sprint/3-deterministic-economic-backtesting`.
   - Validate remote CI runs on exact PR commit.
