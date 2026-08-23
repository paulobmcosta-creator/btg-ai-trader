# Protocolos Quantitativos — Sprint 0E

**Status:** Sincronização documental concluída / Gate final de consistência documental pendente  
**Baseline normativa:** ADR-0001 a ADR-0022 | Sprint 0D formalmente fechado (`c7e3b24`)  
**Data:** 2026-08-20  

---

## 1. Finalidade

Este diretório contém os protocolos epistemológicos, metodológicos e decisórios que governam a formulação de hipóteses, a integridade temporal de dados, o desenho de validação, a simulação de mercado, a validação estatística e econômica, a avaliação de modelos e estratégias, e os critérios de promoção, rejeição e paper trading do **BTG AI Trader**.

Os protocolos aqui definidos convertem os princípios do [Plano Mestre](../../BTG_AI_TRADER_MASTER_PLAN.md) e de [AGENTS.md](../../../AGENTS.md) em procedimentos formais, auditáveis e reproduzíveis, impedindo que resultados históricos favoráveis sejam confundidos com evidência suficiente de viabilidade operacional ou econômica.

---

## 2. Invariantes Canônicos Transversais (QPI-01 a QPI-15)

O Sprint 0E estabeleceu 269 Hard Quantitative Invariants (HQIs) específicos, distribuídos entre os sub-blocos 0E-A a 0E-G. Transversalmente, esses invariantes são regidos por 15 princípios canônicos inegociáveis:

1. **QPI-01 — CLAIM STRENGTH ≤ EVIDENCE STRENGTH:** Nenhuma claim científica, preditiva ou econômica pode possuir força superior à integridade temporal, experimental, econômica e estatística da evidência que a sustenta.
2. **QPI-02 — KNOWLEDGE MUST BE CAUSAL:** Informação futura ou posterior ao knowledge cutoff de uma decisão não pode alcançar o processo decisório histórico por nenhum caminho direto, derivado ou agregado.
3. **QPI-03 — ADAPTATION CONSUMES INDEPENDENCE:** Evidência utilizada para formular, calibrar, selecionar ou adaptar um candidato consome sua independência e não pode ser reutilizada como validação confirmatória da versão resultante.
4. **QPI-04 — SEARCH HISTORY IS PART OF THE EVIDENCE:** A interpretação do mérito de qualquer candidato vencedor preserva a história material de busca (hipóteses testadas, hiperparâmetros, features, regimes, métricas e variantes).
5. **QPI-05 — OBSERVED MARKET ≠ EXECUTABLE MARKET:** Preço, volume e trajetórias observados no mercado histórico não provam acessibilidade, liquidez executável, prioridade de fila ou preenchimento de ordens.
6. **QPI-06 — ECONOMIC CLAIMS ARE NET AND RISK-AWARE:** Toda claim econômica deve incorporar fricções materiais (custos, taxas, spread, slippage, latência), downside, risco de cauda, risco de trajetória e incerteza amostral/estrutural.
7. **QPI-07 — NO SINGLE METRIC DEFINES MERIT:** Nenhuma métrica isolada (Sharpe, taxa de acerto, retorno acumulado ou p-value) define a qualidade integral de um candidato.
8. **QPI-08 — MODEL ≠ STRATEGY ≠ COMPOSED SYSTEM:** Mérito preditivo de um modelo, mérito de uma política decisória (estratégia) e comportamento de um sistema composto sob risco e execução são objetos de avaliação distintos.
9. **QPI-09 — NO_TRADE IS A FIRST-CLASS DECISION:** A inação deliberada (`NO_TRADE`) é um resultado decisório legítimo, observável e prioritário em condições de incerteza, e não ausência de dado.
10. **QPI-10 — HARD INVALIDITY IS NON-COMPENSATORY:** Violação de invariante metodológico crítico (leakage, contaminação de OOS, look-ahead) anula a admissibilidade da evidência e não pode ser compensada por métricas favoráveis.
11. **QPI-11 — UNKNOWN MUST REMAIN UNKNOWN:** A ausência de evidência ou dado temporal não pode ser preenchida por suposições otimistas, timestamps fabricados, liquidez presumida ou certezas artificiais.
12. **QPI-12 — VERSION AND PROVENANCE ARE IMMUTABLE HISTORICALLY:** Qualquer alteração material em código, dados, parâmetros ou políticas gera nova identidade de versão; o passado permanece vinculado ao que foi efetivamente executado.
13. **QPI-13 — EVALUATION ≠ PROMOTION ≠ AUTHORITY:** Avaliação quantitativa favorável subsidia decisões de promoção entre etapas de pesquisa, mas nunca concede autoridade para negociar dinheiro real.
14. **QPI-14 — PAPER IS PROSPECTIVE, NON-FUNDED EVIDENCE:** Paper trading é uma avaliação prospectiva com dados contemporâneos e decisões reais do sistema, sem capital real em risco, e não equivale automaticamente a Live.
15. **QPI-15 — GATES ARE FAIL-CLOSED AND CONJUNCTIVE:** Gates de evolução são independentes, conjuntivos e fail-closed; a aprovação em um gate não substitui outro nem autoriza bypass de etapas posteriores.

A rastreabilidade completa entre todos os 269 HQIs e os 15 QPIs está documentada em [TRACEABILITY.md](TRACEABILITY.md).

---

## 3. Estrutura dos Protocolos

Os protocolos quantitativos estão organizados conforme a seguinte taxonomia:

```text
docs/protocols/quantitative/
├── README.md                                 # Visão geral e índice transversal
├── 0E-A-experimental-semantics.md            # Ontologia experimental e hipótese quantitativa
├── 0E-B-dataset-temporal-integrity.md        # Camadas de dados, RunInputBoundary e integridade temporal
├── 0E-C-validation-oos-baselines.md          # Desenho de validação, OOS e baselines
├── 0E-D-backtest-market-simulation.md        # Simulação de mercado e backtest consciente de execução
├── 0E-E-statistical-economic-validation.md   # Validação estatística e inferência econômica
├── 0E-F-strategy-model-evaluation.md         # Avaliação de modelos e estratégias
├── 0E-G-promotion-paper-rejection.md         # Promoção, paper trading e rejeição
├── 0E-H-cross-protocol-gate.md               # Auditoria transversal e gate de consistência
└── TRACEABILITY.md                           # Matriz de rastreabilidade HQI ↔ QPI
```

---

## 4. Distinção Normativa nos Protocolos

Cada protocolo distingue rigorosamente três níveis normativos:

1. **HARD QUANTITATIVE INVARIANT (HQI):** Propriedade inegociável cuja violação torna a evidência nula, inadmissível ou inválida para a claim pretendida.
2. **PROTOCOL REQUIREMENT:** Requisito procedimental obrigatório do método científico (ex.: exigir um benchmark ou caracterizar incerteza).
3. **POLICY / EXPERIMENT PARAMETER:** Escolha deliberadamente parametrizável por experimento ou política de pesquisa (ex.: tamanho de janelas, métodos específicos de bootstrap, thresholds numéricos).

### Nota sobre Aplicabilidade

A presença de predicados como "quando material" ou "quando aplicável" (**ApplicabilityPredicate**) não transforma um Hard Invariant em parâmetro de escolha: se a condição fática for verdadeira, o invariante é estritamente **HARD** e não compensatório.

---

## 5. Natureza Semântica — Ausência de Schemas Físicos Prematuros

Conceitos estabelecidos nesta especificação (como `DecisionOpportunity`, `EvaluationBoundary`, `ModelEvaluation`, `StrategyEvaluation`, `QuantitativeEvidenceAssessment` e `PaperGateAssessment`) são **conceitos semânticos e metodológicos**.

Eles **não constituem** classes Python, dataclasses, schemas de banco de dados, tópicos de mensageria ou contratos físicos de runtime automaticamente aprovados. A materialização física de estruturas de dados e código permanece restrita aos sprints de implementação correspondentes.

---

## 6. Relação com as Restrições Operacionais

Nenhum resultado, métrica ou aprovação obtida sob estes protocolos autoriza:
- Conexão a corretoras ou MetaTrader 5;
- Envio, alteração ou cancelamento de ordens reais;
- Negociação com dinheiro real;
- Bypass de etapas de Risk Engine, Recovery ou aprovação humana formal.
