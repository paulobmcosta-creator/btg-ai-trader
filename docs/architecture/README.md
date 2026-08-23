# Arquitetura

## Baseline lógica do Sprint 0C refinada pelos contratos do Sprint 0D, não implementada

A baseline arquitetural continua sendo um monólito modular orientado a eventos com fronteiras explícitas de domínio e autoridade. O Sprint 0D refinou os contratos sem criar autorização operacional nem escolher tecnologia física.

A cadeia econômica autorizada é, conceitualmente:

```text
Market/Data Source
        |
        v
Raw/Capture Evidence
        |
        v
Quality / Admission
        |
        v
Normalized Market Events
        |
        v
Signal
        |
        v
StrategyDecision
   /            \
NO_TRADE     PROPOSE_TRADE
                  |
                  v
        InstrumentResolution?
                  |
                  v
             TradeIntent
                  |
                  v
             RiskDecision
            /           \
         REJECT        PERMIT
                         |
                         v
               RiskAuthorization
                         |
                         v
              AuthorizationAllocation
                         |
                         v
                  OrderIntent
                         |
                         v
                    OrderPlan
                         |
                         v
                ExecutionOrder(s)
                         |
                         v
                    Execution
```

`NO_TRADE` é resultado explícito de `StrategyDecision` e é distinto de `RiskDecision.REJECT`, falha operacional e `SAFE_HALT`. Todo `TradeIntent` que chega ao Risk referencia um `TradableInstrument` concreto. Nenhum Signal/modelo possui autoridade para criar efeito externo e nenhum novo economic commitment pode contornar `RiskAuthorization` e `AuthorizationAllocation` válidas.

A cadeia de observação e reconhecimento financeiro é separada:

```text
raw external execution evidence
        |
        v
OrderLifecycleObservation / FillObservation
        |
        v
identity / dedup / matching
        |
        v
canonical Fill
        |
        v
EconomicRecognitionIdentity
        |
        v
LedgerTransaction
        |
        v
1..N LedgerPostings
        |
        v
Position / Cash / Valuation / P&L / Exposure projections
```

`FillObservation` não produz efeito financeiro direto. Observações externas de Position/Cash não sobrescrevem estado interno e divergências seguem reconciliation explícita.

O estado operacional também é multidimensional:

```text
RuntimePhase
≠ SafetyPosture
≠ OperationalReadinessAssessment
```

`SAFE_HALT` é fail-closed para novos commitments, mas não implica auto-flatten. Readiness é capability-based; recovery/reconciliation suficientes removem blockers próprios, mas não produzem readiness automaticamente.

Restart cria novo `RunId`; continuidade é registrada por `RunRelation` tipada. Fatos externos não exigem `run_id` intrínseco e podem ser ligados a Runs por `CaptureContext` e `ProcessingReceipt`.

## Limites atuais

- Não há adaptador BTG ou MetaTrader 5.
- Não há coleta de mercado, estratégia, features, modelo, simulador ou executor funcional.
- Não há infraestrutura cloud ou produção.
- Não há autorização para ordens ou dinheiro real.
- Nenhum contrato do Sprint 0D constitui implementação.

## Estado documental

- Sprint 0C: concluído e aprovado.
- 0D-A a 0D-E: fechados e congelados.
- 0D-F — Cross-contract Gate: aprovado.
- Sincronização normativa/documental: concluída nos ADRs 0015–0022.
- F1 final de consistência normativa/documental: aprovado em 2026-08-19.
- Sprint 0D: formalmente fechado e aprovado.
- Sprint 0E: sincronização documental concluída; gate final de consistência documental pendente.
- Sprint 0F: não iniciado.

Os ADRs 0015–0022 refinam explicitamente decisões históricas dos ADRs 0003, 0007–0011 e 0013–0014 sem reescrever o histórico de 0C.

Schemas físicos, interfaces Python, tolerâncias quantitativas, calendário concreto, storage, mensageria, broker/provider, mecanismos de locking/transação e demais decisões deliberadamente adiadas permanecem fora desta sincronização.
