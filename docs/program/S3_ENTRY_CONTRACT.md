# Sprint 3 Entry Contract — Deterministic Economic Backtesting

## Authority and baseline

```text
SPRINT_2_FINAL_VERDICT = PASS
SPRINT_2_ACCEPTED_HEAD = ba6c0c41988fc9fefbdff13b0daedf96301dd74c
SPRINT_3_CANONICAL_BRANCH = sprint/3-deterministic-economic-backtesting
ENTRY_MATERIALIZATION_BRANCH = s3/00-full-deterministic-economic-backtesting
FINANCIAL_AUTHORITY = ABSENT
REAL_MONEY = FORBIDDEN
PAPER_TRADING = FORBIDDEN
LIVE_TRADING = FORBIDDEN
ADDITIONAL_RECURRING_COST = ZERO
NEW_RUNTIME_DEPENDENCIES = 0
```

This contract governs Sprint 3 — Deterministic Economic Backtesting. It is derived from the accepted and formally closed Sprint 2 state (`ba6c0c41988fc9fefbdff13b0daedf96301dd74c`), the frozen Foundation, `AGENTS.md`, the living Master Plan, Protocol 0E-D, Protocol 0E-E, and ADRs 0004, 0008, 0014, 0016, 0017, 0021, and 0022.

Historical PR #9, PR #37, and branch `s3/01-causal-replay-kernel` are research inputs only. They are not canonical implementation and must not be merged wholesale into the Sprint 3 baseline.

## 1. Mission

Sprint 3 builds a **Deterministic Economic Backtesting Layer** over the causal market replay platform accepted in Sprint 2. It simulates economic execution, costs, slippage, latency, simulated positions, gross/net P&L, descriptive metrics, and provenance without connecting to brokers, placing live/paper orders, mutating the future canonical `FinancialLedger`, or executing machine learning models.

Sprint 3 is explicitly classified as:
```text
BACKTEST_CLASS = DETERMINISTIC_EXECUTION_ECONOMICS_KERNEL
FULL_END_TO_END_STRATEGY_BACKTEST = NOT_YET_AVAILABLE
STRATEGY_PROMOTION_CLAIMS = FORBIDDEN
```

## 2. Authorized positive capability set

| ID | Capability | Status at entry | Scope / Definition |
|---|---|---|---|
| S3-AC-01 | Explicit deterministic backtest input boundary | REQUIRED | Immutable manifest binding replay input boundary, action sequence, economic assumptions, fee schedules, slippage policies, latency policies, code revision, and config hash. |
| S3-AC-02 | Causal economic replay derived from accepted S2 semantics | REQUIRED | Replay execution driven strictly by S2 `CausalMarketReplaySchedule` / `CausalMarketReplayCursor` advancing by `knowledge_cutoff`. |
| S3-AC-03 | Explicit decision / order-ready / market-arrival / execution timing | REQUIRED | Temporal ordering: `knowledge_cutoff <= decision_time <= order_ready_time <= market_arrival_time <= execution_opportunity_time`. Zero backward time. |
| S3-AC-04 | Side-aware executable price semantics | REQUIRED | Aggressive BUY consumes Ask; aggressive SELL consumes Bid. Mid-price execution forbidden without explicit passive pre-positioning evidence. |
| S3-AC-05 | Explicit deterministic spread treatment | REQUIRED | Deterministic spread calculation; missing or non-positive spreads fail-closed as `INDETERMINATE` or `NO_FILL`. |
| S3-AC-06 | Explicit configurable fee/cost model | REQUIRED | Configurable schedules supporting per-unit fees, fixed per-order fees, and basis-point fees with currency and multiplier scoping. |
| S3-AC-07 | Explicit deterministic adverse slippage model | REQUIRED | Slippage is adverse by construction: BUY pays higher, SELL receives lower. Zero slippage only when explicitly configured. No RNG in baseline. |
| S3-AC-08 | Explicit deterministic latency model | REQUIRED | Non-negative decision-to-ready and transit-to-market latencies expressed in virtual logical microseconds without wall-clock dependence. |
| S3-AC-09 | Fill / no-fill / indeterminate semantics | REQUIRED | Explicit outcome categorization: `FILL`, `NO_FILL`, `INDETERMINATE`, `REJECTED`. |
| S3-AC-10 | Simulated economic position accounting | REQUIRED | Isolated backtest position state tracking quantity, weighted average cost basis, and realized P&L. Zero mutation of canonical `FinancialLedger`. |
| S3-AC-11 | Gross / net P&L with explicit economic units | REQUIRED | Exact Decimal arithmetic for gross P&L, explicit fees, and net P&L. Explicit currency and contract multiplier metadata. |
| S3-AC-12 | Cost attribution without double counting | REQUIRED | Spread and slippage are reflected in simulated fill prices; explicit fees are deducted. Diagnostic cost burden is tracked without double-deduction. |
| S3-AC-13 | Descriptive economic metrics | REQUIRED | Deterministic descriptive statistics (turnover, hit rate, average win/loss, profit factor, max drawdown). Promotional claims (Sharpe/Sortino/VaR) forbidden. |
| S3-AC-14 | Future-data leakage protection | REQUIRED | Provenance and tests verifying that perturbing or adding events after the decision cutoff does not alter prior execution or accounting. |
| S3-AC-15 | Deterministic repeated execution | REQUIRED | Same inputs + same assumptions + same code = byte/value identical economic results. |
| S3-AC-16 | Assumption sensitivity / cost stress | REQUIRED | Deterministic sensitivity sweeps asserting monotonicity: worsening fees or slippage cannot improve economic outcomes. |
| S3-AC-17 | Lineage tracking | REQUIRED | Lineage binding: `market_event -> research_action -> simulated_fill -> economic_result`. |
| S3-AC-18 | Explicit end-of-window position policy | REQUIRED | Default `KEEP_OPEN`. Forced liquidation without an explicit market event and rule is prohibited. |
| S3-AC-19 | Explicit handling of unavailable execution evidence | REQUIRED | Stale, missing, or incomplete market data yields `INDETERMINATE` or `NO_FILL` instead of synthetic execution. |
| S3-AC-20 | Final Gate B reconciliation | REQUIRED | Formal reconciliation against Gate B requirements (determinism, leakage absence, costs modeled, reproducible replay). |
| S3-AC-21 | Small-lot assumption | REQUIRED | Explicit parameter declaring small order assumption; liquidity limits documented. |
| S3-AC-22 | Order types beyond MARKET | DEFERRED | Limit and stop orders deferred; unsupported in baseline kernel. |
| S3-AC-23 | Order book queue priority / depth fill | DEFERRED | Queue position and depth fills unsupported by available market evidence; deferred. |
| S3-AC-24 | Market impact model | DEFERRED | Unbounded linear impact models rejected; impact models deferred until depth data available. |
| S3-AC-25 | Candle intrabar trajectory execution | DEFERRED | Intrabar path ambiguity treated as `INDETERMINATE` or deferred to tick-level data. |

## 3. Negative capabilities

```text
S3-NC-01 Broker order/account API = ABSENT
S3-NC-02 Order submission / modification / cancellation = IMPOSSIBLE
S3-NC-03 Paper trading operational path = ABSENT
S3-NC-04 Live trading operational path = ABSENT
S3-NC-05 Real-money authority = ABSENT
S3-NC-06 Strategy operational engine / decision path = ABSENT
S3-NC-07 Signal operational engine / generator path = ABSENT
S3-NC-08 Risk operational engine / authorization path = ABSENT
S3-NC-09 Canonical FinancialLedger mutation = ABSENT
S3-NC-10 External network side effects (requests/httpx/aiohttp/socket) = ABSENT
S3-NC-11 Wall-clock-driven causality (sleep/now/time.time) = ABSENT
S3-NC-12 Paid external services / dependencies = ABSENT
S3-NC-13 Predictive ML operational wiring = ABSENT
S3-NC-14 Silent missing data imputation = FORBIDDEN
S3-NC-15 Future data leakage / lookahead = FORBIDDEN
S3-NC-16 Favorable unknown / ambiguous resolution = FORBIDDEN
S3-NC-17 Mid-price aggressive fill by default = FORBIDDEN
S3-NC-18 Same-close execution without causal proof = FORBIDDEN
S3-NC-19 Tick volume as accessible liquidity = FORBIDDEN
S3-NC-20 Unbounded linear capacity assumption = FORBIDDEN
S3-NC-21 Random number generator / stochastic execution in baseline = NOT_TRIGGERED / ABSENT
```

## 4. Operational rules and zero-cost constraints

1. **Zero Recurring Cost:** `ADDITIONAL_RECURRING_COST = ZERO`. All simulations and tests use synthetic fixtures or existing S1/S2 data.
2. **Zero New Runtime Dependencies:** `NEW_RUNTIME_DEPENDENCIES = 0`. Uses Python standard library (`decimal`, `fractions`, `dataclasses`, `datetime`, `uuid`, `enum`, `math`, `typing`).
3. **Exact Arithmetic:** Financial valuations and P&L use Python `Decimal` to avoid floating-point rounding drifts.
4. **Boundary Scanner:** `scripts/check_s3_boundary.py` must pass on all code under `src/btg_ai_trader/backtesting`.
