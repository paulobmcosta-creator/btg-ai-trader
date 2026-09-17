# Sprint 3 Decision Register

This register activates and formalizes decisions whose first material dependency occurs in Sprint 3. Historical Foundation decision IDs remain unchanged.

## Active Foundation decisions

| ID | Decision | Sprint 3 adjudication | Trigger / boundary |
|---|---|---|---|
| DD-15 | RunInputBoundary / BacktestInputBoundary | DECIDED FOR S3 — immutable boundary capturing replay input boundary, ordered research actions, economic assumptions identity/hash, instrument economics, fee schedules, slippage policies, latency policies, code revision, and config hash. | First backtest run |
| DD-22 | Financial recognition and ledger isolation | DECIDED FOR S3 — simulated backtest accounting is strictly segregated in `BacktestPositionState` / `BacktestEconomicState`. The canonical `FinancialLedger` from ADR-0014/0022 is never mutated or instantiated. | First simulated position/P&L |
| DD-79 | Execution price semantics | DECIDED FOR S3 — aggressive market orders consume Ask for BUY and Bid for SELL. Mid-price execution is forbidden by default. Same-close execution without causal proof is rejected. | First simulated fill |
| DD-80 | Missing-data treatment in execution | DECIDED FOR S3 — missing, stale, or incomplete market quotes cannot be silently imputed; they fail-closed producing `INDETERMINATE` or `NO_FILL`. | First market-data fill evaluation |
| DD-84 | Backtest kernel classification | DECIDED FOR S3 — classified as `DETERMINISTIC_EXECUTION_ECONOMICS_KERNEL`. No operational Strategy or Risk Engine claims are permitted. | Sprint 3 entry |
| DD-85 | Research execution action contract | DECIDED FOR S3 — input actions are immutable `BacktestAction` instances with explicit decision cutoff, decision time, order-ready time, instrument ID, side, and quantity. They are not broker orders or strategy decisions. | Backtest action domain |
| DD-86 | Spread model | DECIDED FOR S3 — deterministic side-aware pricing. Spread is `Ask - Bid`. If spread <= 0 or missing, fill outcome is `INDETERMINATE`. | Spread calculation |
| DD-87 | Slippage model | DECIDED FOR S3 — adverse deterministic slippage: `slippage_price >= raw_price` for BUY, `slippage_price <= raw_price` for SELL. Models: `ZERO_SLIPPAGE`, `FIXED_POINTS`, `FIXED_BPS`. Favorable slippage is forbidden. RNG is absent/not triggered in baseline. | Slippage modeling |
| DD-88 | Fee/cost model | DECIDED FOR S3 — explicit configurable fee schedules: `FeeSchedule(fixed_per_order, per_unit, bps_rate, currency)`. No claim of real historical B3 tables without explicit evidence; tests use synthetic schedules. | Fee accounting |
| DD-89 | Latency model | DECIDED FOR S3 — deterministic non-negative latency in virtual microseconds: `decision_latency_us` and `transit_latency_us`. Wall-clock `sleep()` or `datetime.now()` is forbidden. | Execution timing |
| DD-90 | Fill outcome semantics | DECIDED FOR S3 — four distinct categories: `FILL` (executable price found and constraints met), `NO_FILL` (valid market state but execution criteria unmet), `INDETERMINATE` (missing, stale, or ambiguous market data), `REJECTED` (invalid action inputs or temporal violations). | Execution outcomes |
| DD-91 | Position accounting and cost basis | DECIDED FOR S3 — moving weighted average cost basis using exact `Decimal` arithmetic. Cost basis updates on position-increasing fills; realized P&L recognized on position-reducing fills. Gross P&L, fees, and Net P&L tracked separately. No double-counting of spread/slippage. | Position & P&L |
| DD-92 | End-of-window position policy | DECIDED FOR S3 — default policy is `KEEP_OPEN`. End of backtest window does not trigger forced liquidation unless an explicit policy and valid market event are provided. | Window termination |
| DD-93 | Descriptive economic metrics | DECIDED FOR S3 — descriptive statistics only: gross P&L, net P&L, total fees, spread burden, slippage burden, turnover, fill count, no-fill count, indeterminate count, win rate, profit factor, expectancy, max drawdown. Promotional inferential statistics (Sharpe, Sortino, VaR, p-values) are deferred. | Backtest metrics |
| DD-94 | Sensitivity and monotonicity invariants | DECIDED FOR S3 — deterministic parameter perturbation tests. Invariant: increasing adverse slippage or increasing fees cannot improve net economic outcomes, all else equal. | Robustness & sensitivity |

## Deferred decisions

The following decisions remain deferred to subsequent sprints:
- Limit / stop order fill models with order book queue priority;
- Partial fill models based on market depth;
- Market impact functions for large orders;
- Predictive ML models and automated parameter optimization;
- Integration with broker APIs (MetaTrader 5, BTG DataServices, etc.);
- Live / paper trading orchestration;
- Canonical production `FinancialLedger` database persistence.
