# Sprint 0E — Protocolos Quantitativos

- **Status:** Sincronização documental concluída / Gate final de consistência documental pendente
- **Data da consolidação técnica:** 2026-08-20
- **Baseline de entrada:** Sprint 0D formalmente fechado (`c7e3b24`) | ADR-0001 a ADR-0022
- **Próximo passo:** Execução do gate final de consistência documental e aprovação humana (0F permanece não iniciado)

---

## 1. Objetivo do Sprint 0E

O Sprint 0E especifica o sistema normativo, epistemológico e decisório pelo qual hipóteses quantitativas, estratégias e modelos de Machine Learning podem ser formulados, submetidos a evidência histórica, testados sob condições temporalmente válidas e economicamente realistas, avaliados sob incerteza, comparados com alternativas e submetidos a critérios rigorosos de promoção para Paper Trading ou rejeição.

O objetivo do Sprint 0E **não é** implementar um backtester funcional, criar estratégias lucrativas, treinar modelos ou conectar a corretoras/bolsas. O produto do Sprint 0E é a **norma metodológica de pesquisa e validação quantitativa** do projeto.

---

## 2. Decomposição em Sub-blocos (0E-A a 0E-H)

O Sprint 0E foi decomposto em oito sub-blocos especializados:

1. **[0E-A — Semântica Experimental e Hipótese Quantitativa](../protocols/quantitative/0E-A-experimental-semantics.md):** Ontologia experimental, falsificabilidade, versionamento de hipóteses, intenção de pesquisa (`EXPLORATORY` vs `CONFIRMATORY`), semântica de `DecisionOpportunity` e `NO_TRADE` de primeira classe.
2. **[0E-B — Dados, RunInputBoundary e Integridade Temporal](../protocols/quantitative/0E-B-dataset-temporal-integrity.md):** Camadas semânticas de dados, point-in-time correctness, prevenção de vazamento temporal (*look-ahead bias* e *data leakage*), ciclo de vida de candles e imutabilidade de proveniência.
3. **[0E-C — Desenho de Validação, Out-of-Sample e Baselines](../protocols/quantitative/0E-C-validation-oos-baselines.md):** Separação estrita entre desenvolvimento e partição protegida (*Protected OOS*), validação walk-forward, procedimentos de *purging* e *embargo*, baselines e comparadores.
4. **[0E-D — Backtest e Simulação de Mercado](../protocols/quantitative/0E-D-backtest-market-simulation.md):** Simulação consciente de execução, causalidade temporal da decisão ao fill, modelagem de spread, custos, latência, slippage, liquidez e incerteza intrabar.
5. **[0E-E — Validação Estatística e Econômica](../protocols/quantitative/0E-E-statistical-economic-validation.md):** Estimands, informação efetiva vs tamanho nominal, caracterização de incerteza, famílias de métricas, risco de cauda e downside (quando material, com opções como VaR/ES), controle de multiplicidade (*data snooping*) e robustez.
6. **[0E-F — Avaliação de Modelos e Estratégias](../protocols/quantitative/0E-F-strategy-model-evaluation.md):** Separação entre `ModelEvaluation` e `StrategyEvaluation`, escopos de avaliação, calibração vs discriminação, vetor multidimensional de evidência e disposições técnicas.
7. **[0E-G — Promoção, Paper Trading e Rejeição](../protocols/quantitative/0E-G-promotion-paper-rejection.md):** Máquina de estados de candidatos, dez classes de elegibilidade para Paper, protocolo de Paper Trading prospectivo (*non-funded*), compatibilidade distribucional e dez classes de bloqueadores para Live.
8. **[0E-H — Gate de Consistência Transversal](../protocols/quantitative/0E-H-cross-protocol-gate.md):** Auditoria cruzada (H1 a H8), 15 Invariantes Canônicos Transversais (QPI-01 a QPI-15) e resolução formal dos achados documentais H-DOC-01 a H-DOC-06.

A rastreabilidade dos 269 Hard Quantitative Invariants (HQIs) para os 15 QPIs está consolidada em [TRACEABILITY.md](../protocols/quantitative/TRACEABILITY.md).

---

## 3. Invariantes e Disciplina de Parâmetros

Durante todo o Sprint 0E foi rigorosamente respeitada a proibição de decisões físicas prematuras:
- **Nenhum código funcional** de simulação, trading ou dados foi implementado;
- **Nenhuma dependência** de runtime ou biblioteca física foi adicionada;
- **Nenhum ativo, timeframe, modelo ou threshold numérico final** foi congelado;
- **Nenhum caminho de contorno** para o Risk Engine, Paper Trading ou aprovação humana foi admitido.

---

## 4. Estado Atual e Próximos Passos

```text
Sprint 0E — Protocolos Quantitativos:
├── 0E-A a 0E-G: ✅ FECHADOS TECNICAMENTE
├── 0E-H Cross-Protocol Gate: ✅ APROVADO (PASS)
├── Sincronização documental: ✅ CONCLUÍDA
├── Gate final de consistência documental: ⏳ PENDENTE
└── Fechamento formal do Sprint 0E: ⏳ PENDENTE DE APROVAÇÃO HUMANA

Sprint 0F — Gate do Sprint 0: ⏳ NÃO INICIADO
```
