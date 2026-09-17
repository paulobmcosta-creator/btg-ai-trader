# Sprint 3 — Deterministic Economic Backtesting

## Estado atual

```text
SPRINT_3_STATUS = OPEN
SPRINT_2_STATUS = FORMALLY_CLOSED
SPRINT_2_FINAL_VERDICT = PASS
SPRINT_2_CANONICAL_HEAD = ba6c0c41988fc9fefbdff13b0daedf96301dd74c
SPRINT_3_CANONICAL_BRANCH = sprint/3-deterministic-economic-backtesting
WORK_BRANCH = s3/00-full-deterministic-economic-backtesting
SPRINT_3_LIFECYCLE = OPEN
S3_ENTRY_GATE = PASS
FINANCIAL_AUTHORITY = ABSENT
REAL_MONEY_AUTHORITY = ABSENT
PAPER_AUTHORITY = ABSENT
LIVE_AUTHORITY = ABSENT
STRATEGY_OPERATIONAL_PATH = ABSENT
RISK_OPERATIONAL_PATH = ABSENT
CANONICAL_FINANCIAL_LEDGER_MUTATION = ABSENT
ADDITIONAL_RECURRING_COST = ZERO
NEW_RUNTIME_DEPENDENCIES = 0
```

O Sprint 3 parte estritamente do head formalmente aceito e fechado do Sprint 2 (`ba6c0c41988fc9fefbdff13b0daedf96301dd74c`). A branch experimental histórica `s3/01-causal-replay-kernel` não é baseline e permanece exclusivamente para consulta de pesquisa.

## 1. Missão

Construir a camada de **simulação econômica determinística** sobre a plataforma causal de mercado aceita no Sprint 2.

O Sprint 3 implementa:
- modelagem de tempo de execução explícito (knowledge cutoff <= decision time <= order-ready time <= simulated market-arrival time <= execution opportunity time);
- semântica de preço executável sensível ao lado do mercado (BUY consome Ask, SELL consome Bid; mid-price proibido como default agressivo);
- tratamento determinístico explícito de spread e detecção de dados incompletos/stale (fail-closed);
- modelo configurável de taxas/emolumentos/corretagem em unidades econômicas explícitas;
- modelo de slippage determinístico estritamente adverso (favorable slippage proibido; zero slippage somente quando explicitamente configurado; sem RNG no baseline);
- modelo de latência determinístico não negativo (computação e trânsito em microssegundos lógicos virtuais);
- semântica estrita de desfechos: `FILL`, `NO_FILL`, `INDETERMINATE`, `REJECTED`;
- contabilidade de posição simulada (domínio isolado de backtest; nunca muta o `FinancialLedger` canônico futuro);
- cálculo de P&L realizado bruto e líquido, sem dupla contagem de custos (spread e slippage embutidos nos preços simulados; taxas deduzidas);
- métricas econômicas descritivas determinísticas (sem claims estatísticas ou promocionais como Sharpe/Sortino/p-values antes dos sprints devidos);
- proteção comprovada contra vazamento de dados futuros (invariância a eventos posteriores ao cutoff, rejeição de regressões temporais);
- rastreabilidade e proveniência causal completa (`market_event -> research_action -> simulated_fill -> economic_result`);
- invariantes de sensibilidade e teste de estresse de custos (piorar premissas não pode melhorar resultado financeiro).

## 2. Fronteira e classificação do kernel

O Sprint 3 é classificado rigorosamente como:

```text
BACKTEST_CLASS = DETERMINISTIC_EXECUTION_ECONOMICS_KERNEL
FULL_END_TO_END_STRATEGY_BACKTEST = NOT_YET_AVAILABLE
STRATEGY_PROMOTION_CLAIMS = FORBIDDEN
```

O kernel consome ações imutáveis de pesquisa (`BacktestAction`), que:
- **NÃO SÃO** `StrategyDecision`;
- **NÃO SÃO** `TradeIntent`;
- **NÃO SÃO** `RiskDecision` ou `RiskAuthorization`;
- **NÃO SÃO** `OrderIntent`, `OrderPlan` ou `ExecutionOrder`;
- **NÃO SÃO** ordens de broker ou chamadas de execução.

Esses conceitos pertencem a estágios posteriores do roadmap e não são simulados precocemente apenas para simular completude arquitetural.

## 3. Negative capabilities preservadas

```text
BROKER_API = ABSENT
ACCOUNT_API = ABSENT
ORDER_SUBMISSION = IMPOSSIBLE
ORDER_MODIFICATION = IMPOSSIBLE
ORDER_CANCELLATION = IMPOSSIBLE
PAPER_PATH = ABSENT
LIVE_PATH = ABSENT
REAL_MONEY_AUTHORITY = ABSENT
STRATEGY_OPERATIONAL_PATH = ABSENT
SIGNAL_OPERATIONAL_PATH = ABSENT
RISK_OPERATIONAL_PATH = ABSENT
CANONICAL_FINANCIAL_LEDGER_MUTATION = ABSENT
EXTERNAL_NETWORK_SIDE_EFFECT = ABSENT
WALL_CLOCK_CAUSALITY = ABSENT
PAID_EXTERNAL_SERVICE = ABSENT
PREDICTIVE_ML = ABSENT
SILENT_MISSING_DATA_IMPUTATION = FORBIDDEN
FUTURE_DATA_LEAKAGE = FORBIDDEN
FAVORABLE_UNKNOWN_RESOLUTION = FORBIDDEN
MID_PRICE_AGGRESSIVE_FILL_BY_DEFAULT = FORBIDDEN
SAME_CLOSE_EXECUTION_WITHOUT_CAUSAL_PROOF = FORBIDDEN
TICK_VOLUME_AS_ACCESSIBLE_LIQUIDITY = FORBIDDEN
UNBOUNDED_LINEAR_CAPACITY_ASSUMPTION = FORBIDDEN
RNG_IN_BASELINE = NOT_TRIGGERED_AND_ABSENT
```

## 4. Documentos normativos do Sprint 3

1. `docs/program/S3_ENTRY_CONTRACT.md`
2. `docs/program/S3_DECISION_REGISTER.md`
3. `docs/program/S3_CAPABILITY_MATRIX.md`
4. `docs/program/S3_ENTRY_GATE.md`
5. `docs/program/S3_FINAL_ACCEPTANCE.md` (conclusão do sprint)
6. `docs/program/workstreams/S3-ANTIGRAVITY-FULL-SPRINT.md`
7. `scripts/check_s3_boundary.py`
8. `.github/workflows/s3-python-ci.yml`
