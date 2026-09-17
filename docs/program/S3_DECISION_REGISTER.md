# Sprint 3 Decision Register

This register activates and formalizes decisions whose first material dependency occurs in Sprint 3. Historical Foundation decision IDs from `docs/foundation/0F-B_deferred_decision_register.md` remain unchanged and are strictly preserved without renumbering.

## Active Foundation decisions

| ID | Decision | Sprint 3 adjudication | Trigger / boundary |
|---|---|---|---|
| DD-13 | Algoritmo concreto de RNG para simulação | `NOT_TRIGGERED_AND_DEFERRED` — Baseline backtest kernel is strictly deterministic without pseudo-random number generation. RNG is absent and forbidden in baseline simulation. Formal operational RNG remains deferred by Foundation. | Deterministic backtest baseline |
| DD-14 | Algoritmo de inicialização, derivação e particionamento de seeds | `NOT_TRIGGERED_AND_DEFERRED` — Deterministic execution and run derivation via SHA-256 / UUID5 hashes without PRNG seeds. Operational seed derivation remains deferred by Foundation. | Deterministic execution runs |
| DD-15 | Formato físico e representação do RunInputBoundary | `TRIGGERED_AND_SATISFIED` — Materialized as `BacktestInputBoundary` with mandatory explicit source provenance (`source_run_id`, `source_code_revision`, `source_config_hash`, `provider_id`, `capture_scope`). Fabricated fallback hashes (`'0'*64`) and dummy run IDs are strictly forbidden and rejected fail-closed. | First backtest run |
| DD-16 | Critérios de determinismo e replay | `TRIGGERED_AND_SATISFIED` — Strict byte-for-byte reproducibility across runs requiring valid replay schedule or explicit source boundary; AST-enforced exclusion of stochastic sources (`random`, `uuid4`, `secrets`, `os.urandom`, etc.) including alias imports. | Backtest boundary checker |
| DD-46 | Metodologia de cost basis (custo médio ponderado vs FIFO) | `CANONICAL_DEFERRED`, `S3_LOCAL_SIMULATION_COST_BASIS = WACB` — Moving weighted average cost basis using exact `Decimal` arithmetic for local backtest accounting (`S3-D-11`). Canonical production ledger cost basis remains deferred by Foundation. | Position accounting |
| DD-47 | Metodologia de P&L e Valuation intradiário (Mark-to-Market) | `CANONICAL_DEFERRED`, `S3_LOCAL_SIMULATION_VALUATION_POLICY = BACKTEST_MARK_EVIDENCE` — Intraday mark-to-market valuation strictly requires contemporary valid `BacktestMarkEvidence` and fails closed (`unrealized_pnl=None`, `total_net_pnl=None`) when mark quotes are absent (`S3-D-11`). Canonical production valuation remains deferred by Foundation. | Intraday MTM valuation |
| DD-74 | Modelagem paramétrica de custos de transação e fricções | `TRIGGERED_AND_SATISFIED` — Parametric modeling for simulation via explicit `InstrumentEconomics`, `FeeSchedule`, adverse deterministic slippage models, and diagnostic spread burden. | Backtest economic models |
| DD-92 | Resolução temporal de simulação de backtest (ticks vs trades vs candles) | `TRIGGERED_AND_SATISFIED`, `BASELINE_PRECISE_EXECUTION = TICK` — High-resolution tick simulation supported; candle execution path is deferred and fails closed (`INDETERMINATE` with `CANDLE_EXECUTION_PATH_UNSUPPORTED`). | Market data resolution |
| DD-93 | Tabela de taxas de negociação, registro e emolumentos B3 | `NOT_TRIGGERED_AND_DEFERRED`, `REAL_HISTORICAL_B3_FEE_TABLE = NOT_PROVIDED` — Parametric `FeeSchedule(fixed_per_order, per_unit, bps_rate, currency)` with temporal validity (`effective_from`/`effective_until`) supported under `S3-D-08`. Definitive canonical historical B3 tariff/emolument table in production remains deferred. | Transaction cost schedule |
| DD-94 | Modelo matemático de estimativa de slippage na simulação | `TRIGGERED_AND_SATISFIED` — Adverse deterministic slippage: `slippage_price >= raw_price` for BUY, `slippage_price <= raw_price` for SELL. Models: `ZERO_SLIPPAGE`, `FIXED_POINTS`, `FIXED_BPS`. Favorable slippage is strictly forbidden. | Slippage modeling |
| DD-95 | Modelo de latência de transmissão e processamento em simulação | `TRIGGERED_AND_SATISFIED` — Deterministic non-negative latency in virtual microseconds: `decision_latency_us` and `transit_latency_us`. Zero wall-clock dependencies. | Latency modeling |
| DD-96 | Algoritmo de simulação de prioridade de fila de ordens no book | `NOT_TRIGGERED_AND_DEFERRED` — Queue priority simulation models are deferred beyond Sprint 3. Small-lot assumption applies. | Order book depth modeling |
| DD-97 | Função de impacto de mercado para simulação de grandes volumes | `NOT_TRIGGERED_AND_DEFERRED` — Market impact functions for large orders are deferred beyond Sprint 3. Small-lot assumption applies. | Large volume simulation |
| DD-98 | Regras de liquidação mandatória de posições no fim do pregão simulado | `NOT_TRIGGERED_AND_DEFERRED`, `S3_LOCAL_END_OF_WINDOW_POLICY = KEEP_OPEN` — Default policy `KEEP_OPEN` supported; mandatory liquidation policy `CLOSE_AT_LAST_VALID_QUOTE` is deferred and raises `NotImplementedError`. | End-of-window policy |
| DD-99 | Biblioteca ou engine físico de simulação causal de backtest | `TRIGGERED_AND_SATISFIED` — In-house deterministic execution economics kernel materialized in `btg_ai_trader.backtesting`. | Backtest engine architecture |

## Sprint 3 local implementation decisions

These local decisions are valid for the Sprint 3 functional backtesting increment and do not renumber Foundation DDs.

### S3-D-01 — Kernel classification
The backtesting engine is strictly classified as a `DETERMINISTIC_EXECUTION_ECONOMICS_KERNEL`. It simulates order execution economics under deterministic market replay. No operational Strategy or Risk Engine capabilities are claimed or implemented.

### S3-D-02 — Research execution action contract
Input actions are immutable `BacktestAction` instances with explicit decision cutoff, decision time, order-ready time, instrument ID, side, and quantity. They are simulated actions, not broker orders or live trading intents.

### S3-D-03 — Adverse price semantics & tick rounding
Aggressive market orders consume the Ask price for BUY actions and Bid price for SELL actions. Mid-price execution is forbidden. Tick rounding is adverse: BUY prices round up (ROUND_CEILING), SELL prices round down (ROUND_FLOOR).

### S3-D-04 — Missing-data and quote timeout
Missing, stale, or incomplete market quotes cannot be silently imputed. If quote age exceeds `max_execution_evidence_wait_us`, execution fails closed with outcome `INDETERMINATE` or `NO_FILL`.

### S3-D-05 — Strict determinism and prohibition of stochasticity
Zero PRNG or stochastic entropy sources are permitted in the backtesting package. Given identical input boundary and code revision, backtesting runs produce byte-for-byte identical manifests and results.

### S3-D-06 — Causal temporal timeline
Temporal invariants strictly enforce `knowledge_cutoff <= decision_time <= order_ready_time <= market_event_time`. Look-ahead leakage is prevented by construction.

### S3-D-07 — Deterministic adverse slippage models
Supported slippage models are `ZERO_SLIPPAGE`, `FIXED_POINTS`, and `FIXED_BPS`. Favorable slippage is strictly prohibited and rejected.

### S3-D-08 — Configurable fee schedules
Fee schedules support fixed-per-order, per-unit, and basis-point rates in exact `Decimal` arithmetic, with optional temporal validity bounds (`effective_from` and `effective_until`).

### S3-D-09 — Virtual latency simulation
Latencies are modeled via non-negative virtual microsecond offsets (`decision_latency_us` and `transit_latency_us`). No wall-clock sleep or system timer calls are permitted.

### S3-D-10 — Execution outcome quartet
Fills are strictly partitioned into four mutually exclusive outcomes: `FILL`, `NO_FILL`, `INDETERMINATE`, and `REJECTED`.

### S3-D-11 — Weighted cost basis accounting
Position accounting maintains moving weighted average cost basis on position-increasing fills, and recognizes gross and net realized P&L on position-reducing fills.

### S3-D-12 — Fail-closed mark-to-market
Mark-to-market valuation strictly requires contemporary `BacktestMarkEvidence`. If no mark evidence is available in the event stream for an open position, valuation fails closed by leaving unrealized P&L as `None`.

### S3-D-13 — Non-negative slippage & fee burdens
Slippage burden and explicit fees are tracked as non-negative diagnostic cost accumulators.

### S3-D-14 — Diagnostic spread burden
Spread burden is computed diagnostically as half-spread cost for reporting purposes, without contaminating gross P&L or double-counting execution friction.

### S3-D-15 — End-of-window position policy
The default end-of-window policy is `KEEP_OPEN`, leaving positions unliquidated. The `CLOSE_AT_LAST_VALID_QUOTE` policy is deferred and raises `NotImplementedError`.

### S3-D-16 — Descriptive economic metrics
Backtest reports compute standard descriptive statistics (realized P&L, fees, win rate, profit factor, turnover, max drawdown). Promotional inferential metrics (Sharpe ratio, Sortino ratio, p-values) are deferred to Sprint 4.

### S3-D-17 — Parameter sensitivity and monotonicity invariants
Sensitivity analysis sweeps verify that increasing cost friction parameters monotonically degrades or preserves net P&L where mathematically guaranteed by model construction:
1. **Fee multiplier monotonicity**: Net realized P&L is guaranteed to monotonically decrease (or stay constant) as the fee multiplier increases, with explicit fees monotonically increasing. Non-monotonic behavior raises `ValueError`.
2. **Adverse slippage monotonicity**: Net realized P&L is guaranteed to monotonically decrease (or stay constant) as adverse slippage points increase. Non-monotonic behavior raises `ValueError`.
3. **Latency sensitivity**: Latency is modeled as a deterministic parameter sensitivity analysis (`run_latency_sensitivity_sweep`). P&L response to increased latency is not mathematically guaranteed to be monotonic across complex non-trivial tick streams (as a delayed order may arrive at different market prices or market regimes). Latency sweeps execute deterministically for impact evaluation without asserting strict monotonicity.

### S3-D-18 — Cryptographic run manifest
`BacktestRunManifest` computes a canonical SHA-256 hash binding input boundary, assumptions, code revision, environment info, and metric summaries for complete auditability.

### S3-D-19 — Segregated simulated accounting
Simulated accounting structures (`BacktestPositionState`, `BacktestEconomicState`) are completely segregated from canonical production ledger entities.

### S3-D-20 — Dual schedule and event ingestion
The backtesting engine accepts market data via either a `CausalMarketReplaySchedule` from Sprint 2 or a validated sequence of `EventEnvelope` market events.

## Explicitly deferred decisions

The following decisions remain deferred to subsequent sprints:
- Limit / stop order book queue priority models (DD-96);
- Market impact functions for large orders (DD-97);
- Mandatory end-of-window liquidation execution algorithms;
- Predictive ML models and automated parameter optimization (DD-69..72);
- Broker API integration and execution routing (DD-09..12);
- Paper and live trading orchestration;
- Canonical production `FinancialLedger` database persistence.
