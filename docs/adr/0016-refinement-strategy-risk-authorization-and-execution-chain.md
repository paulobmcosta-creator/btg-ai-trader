# ADR 0016 — Refinamento da cadeia Strategy, Risk, autorização e Execution

- **Status:** Aceita
- **Data:** 2026-08-19
- **Refina e substitui parcialmente:** ADR 0007 — Fronteira Signal, Risk, Execution e intents

## Contexto

O ADR 0007 estabeleceu a separação entre Signal, Risk e Execution e o veto independente do Risk Engine. O Sprint 0D detalhou a cadeia de decisão, autorização, alocação e compromisso econômico necessária para impedir ambiguidades de autoridade e double-spend de capacidade de risco.

## Decisão / refinamento

A separação de responsabilidades do ADR 0007 permanece válida. A cadeia normativa refinada é:

```text
Signal
→ StrategyDecision
   ├── NO_TRADE
   └── PROPOSE_TRADE
→ InstrumentResolutionDecision?
→ TradeIntent
→ RiskDecision
   ├── REJECT
   └── PERMIT
→ RiskAuthorization
→ AuthorizationAllocation
→ OrderIntent
→ OrderPlan
→ ExecutionOrder
→ EconomicExecutionCommand
→ ExecutionAttempt
→ external commitment boundary
```

- `StrategyDecision.NO_TRADE` é resultado estratégico explícito e distinto de `RiskDecision.REJECT`, `SAFE_HALT` e falha operacional.
- `InstrumentResolutionDecision` é obrigatório apenas quando há transformação real de subject abstrato para `TradableInstrument`; não se cria artifact no-op.
- Todo `TradeIntent` apresentado ao Risk referencia `TradableInstrument` concreto e contém um `EconomicObjective` com semântica, direção e unidade explícitas.
- `RiskDecision` possui semanticamente apenas `REJECT` ou `PERMIT`. O julgamento registra reasons, métricas, policy e contexto; não incorpora silenciosamente limites downstream.
- Todo `PERMIT` capaz de habilitar efeito econômico downstream exige `RiskAuthorization` explícita, imutável, temporal e limitada.
- Antes de `OrderIntent`, `AuthorizationAllocation` reserva uma parcela da capacidade da `RiskAuthorization` e conserva semanticamente capacity entre `reserved`, `committed`, `realized` e `released`.
- `OrderIntent` é broker-neutral e referencia uma única Allocation na baseline. `OrderPlan` descreve a topologia de planejamento e pode produzir uma ou mais `ExecutionOrder`s sem exceder o worst-case commitment autorizado.
- Criar `ExecutionAttempt` não constitui commitment por si só. Commitment ocorre na primeira fronteira após a qual o sistema já não consegue garantir ausência de side effect externo decorrente da tentativa.
- Outcome externo `UNKNOWN` após possível commitment permanece `committed` até reconciliation suficiente; retry cego é proibido sem garantia adequada de idempotência externa.

## Invariantes

- Signal, Strategy, TradeIntent e Risk nunca enviam ordens.
- `AnalyticalSeries` nunca chega a Risk/Execution como instrumento negociável.
- Novo commitment econômico exige `RiskAuthorization` válida e `AuthorizationAllocation` suficiente.
- `OrderIntent` sem Allocation é inválido.
- Expiração bloqueia novos commitments, mas não elimina obrigações já externalizadas.
- Control/recovery de obrigação existente não converte authority operacional em nova autorização de risco.

## Consequências

A formulação anterior `APPROVE | APPROVE_WITH_LIMITS | REJECT` fica substituída, para materialização, por `RiskDecision.REJECT | PERMIT` mais `RiskAuthorization` explícita. A formulação anterior em que Order Planning transforma diretamente autorização em `OrderIntent` fica substituída pela cadeia `RiskAuthorization → AuthorizationAllocation → OrderIntent → OrderPlan → ExecutionOrder`.

## Decisões deliberadamente adiadas

Permanecem adiados: tipos concretos de ordem, time-in-force, mecanismo físico de reserva/locking, formato de idempotency key, broker/provider, MT5, cancel/replace concreto, retry timing e implementação de persistência.

## Relação com outros ADRs

Refina ADR 0007 e depende de ADRs 0005, 0010/0019, 0011/0020, 0014/0022 e 0018.
