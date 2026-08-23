# Protocolo 0E-F — Avaliação de Modelos e Estratégias

- **Status:** Fechado tecnicamente no Sprint 0E
- **Data da baseline:** 2026-08-20
- **Consome:** ADR-0007, ADR-0013, ADR-0016, ADR-0021, ADR-0022
- **Subordinado a:** QPI-01, QPI-03, QPI-04, QPI-06, QPI-07, QPI-08, QPI-09, QPI-10, QPI-11, QPI-12, QPI-13

---

## 1. Finalidade e Escopo

O Protocolo 0E-F estabelece as diretrizes para sintetizar os vetores de evidência empírica, estatística e econômica gerados nas etapas anteriores em avaliações formais de dois objetos conceituais distintos:
1. **CandidateModel:** Avaliação do mérito preditivo, estimativo ou de classificação de um modelo isolado.
2. **CandidateStrategy:** Avaliação do mérito econômico, comportamental e de risco de uma política decisória completa.

Esta etapa realiza a **avaliação técnica** (*evaluation*) e **não decide** a promoção operacional para etapas prospectivas (objeto de 0E-G).

---

## 2. Separação Fundamental: Model versus Strategy

### 2.1. ModelEvaluation versus StrategyEvaluation
- **ModelEvaluation:** Pergunta se a saída do modelo (probabilidade, classe, estimativa contínua, regime, volatilidade) é estatisticamente precisa, bem calibrada e informacionalmente útil em relação ao seu estimand e targets.
- **StrategyEvaluation:** Pergunta se a política que transforma informações e modelos em `StrategyDecision` (`NO_TRADE` vs `PROPOSE_TRADE`) gera um perfil de comportamento economicamente justificável, robusto e compatível com os limites de risco.

### 2.2. Ranking Preditivo versus Ranking Econômico
Um modelo com métricas preditivas superiores (ex.: maior AUC-ROC, menor erro quadrático ou maior acurácia) pode gerar uma estratégia com resultado econômico inferior quando integrado a thresholds decisórios, regras de dimensionamento e custos de transação.

```text
[ Features ] → [ CandidateModel ] → [ Probability / Score ]
                                           ↓
                                    [ Decision Threshold ]
                                    [ Business Rules     ] → [ CandidateStrategy ] → [ StrategyDecision ]
                                    [ Sizing / Timing    ]                                  ↓
                                                                                     [ Risk & Execution ]
                                                                                            ↓
                                                                                     [ Economic P&L ]
```

---

## 3. Escopos de Avaliação e Atribuição de Falhas

### 3.1. Os Três Escopos de Avaliação (*EvaluationScope*)
1. **Escopo A — Componente / Modelo:** Avalia exclusivamente a transformação de atributos de entrada em saídas preditivas.
2. **Escopo B — Política Decisória da Estratégia:** Avalia a lógica que consome dados de mercado e previsões de modelos para produzir intenções de operação e decisões `NO_TRADE`.
3. **Escopo C — Comportamento Composto com Risco e Execução:** Avalia a interação do sistema completo (Estratégia + Políticas de Risco + Modelagem de Execução).

### 3.2. Atribuição Causal de Veto e Desempenho
- **Veto Downstream não gera Mérito Upstream:** Uma estratégia com lógica deficiente que apresenta baixo drawdown apenas porque o Risk Engine bloqueou 90% de suas propostas não é uma estratégia de alta qualidade.
- **Atribuição de Falhas:** O diagnóstico de desempenho insuficiente deve distinguir se a causa reside no modelo preditivo, no threshold decisório, nas regras de risco, no modelo de execução ou em condições adversas de mercado. Quando não for possível isolar o componente, o diagnóstico deve ser registrado como `UNKNOWN_ATTRIBUTION`.

---

## 4. Avaliação de Modelos Preditivos

1. **Métricas Alinhadas à Semântica de Saída:**
   - As métricas de avaliação do modelo devem ser selecionadas em função de seu estimand, tipo de saída e objetivo informacional.
   - Para modelos de probabilidades ou scores: exemplos possíveis incluem métricas de discriminação (como curvas ROC/PR e estatísticas de ordenação), calibração (como Brier score e diagramas de confiabilidade) ou perdas probabilísticas globais (como log-loss/cross-entropy), conforme a semântica do output.
   - Para modelos de estimativa contínua: exemplos possíveis incluem métricas de erro de previsão, concordância direcional e estabilidade de resíduos.
   - Para classificadores de regime ou estado: exemplos possíveis incluem persistência, acerto temporal causal e concordância com estados de referência.
2. **Discriminação versus Calibração:** Um modelo pode discriminar bem entre classes mas apresentar probabilidades mal calibradas, distorcendo o dimensionamento de posições.
3. **Threshold Decisório é Propriedade da Estratégia:** O limiar de corte de probabilidade para gerar um trade pertence à estratégia e deve ser validado conjuntamente com as regras de negócio.
4. **Machine Learning Não é Requisito Obrigatório:** Estratégias puramente baseadas em regras determinísticas (*rule-based*) são cidadãs de primeira classe e não necessitam de componentes de ML para serem válidas.

---

## 5. Vetor de Avaliação da Estratégia (EvaluationVector)

A qualidade de uma estratégia é caracterizada por um vetor multidimensional de evidências, e não por um score numérico único compensatório:

```text
StrategyEvaluation
├── Identidade e versão do candidato (código, modelo, parâmetros)
├── Escopo da avaliação (Scope A, B ou C)
├── População de DecisionOpportunities e taxa de NO_TRADE
├── Magnitude econômica (ex.: retorno líquido, expectancy, payoff)
├── Incerteza amostral e inferencial (ex.: distribuições, intervalos de confiança)
├── Risco de downside e cauda (ex.: semivariância, perdas máximas, VaR/ES quando aplicável)
├── Risco de trajetória e drawdown (ex.: drawdown máximo, duração, recovery time)
├── Evidência ajustada ao risco (ex.: razões Sharpe-like, Sortino-like com convenções declaradas)
├── Evidência comparativa contra baselines e benchmarks apropriados
├── Estabilidade temporal através de múltiplos períodos/folds
├── Robustez e sensibilidade paramétrica (ex.: análise de vizinhança, cliffs)
├── Sensibilidade a fricções de mercado, execução e capacidade (custos, slippage, latência, volume)
├── Dependência de regimes de mercado (quando material à claim)
├── Valor incremental de componentes e submodelos
├── Sobrecarga de complexidade arquitetural
├── Contexto e sobrecarga de multiplicidade (histórico de busca e seleção)
├── Completude de evidência avaliada
├── Limitações metodológicas declaradas
└── Disposição final da avaliação (Favorable, Unfavorable, Inconclusive, Invalid, Conditional)
```

---

## 6. Disposições da Avaliação

A síntese de avaliação resulta em uma das seguintes disposições técnicas:

- **`FAVORABLE`:** Evidência metodologicamente válida que sustenta favoravelmente a claim avaliada dentro de seu escopo, considerando uncertainty, comparators, risco e limitações materialmente aplicáveis.
- **`UNFAVORABLE`:** Evidência válida que demonstra insuficiência econômica, risco inaceitável ou fragilidade estrutural.
- **`INCONCLUSIVE`:** Evidência metodologicamente válida, porém com precisão estatística insuficiente ou horizonte amostral reduzido para sustentar conclusão afirmativa.
- **`INVALID`:** Evidência comprometida por falha epistemológica (vazamento temporal, violação de OOS ou erro metodológico grave). O status é estritamente não compensatório.
- **`CONDITIONAL / LIMITED`:** Evidência favorável restrita a condições, regimes ou horizontes operacionais expressamente delimitados.

---

## 7. Protocol Requirements

1. **PR-0E-F-01:** Toda avaliação deve explicitar formalmente seu *EvaluationScope* (Modelo, Estratégia ou Sistema Composto).
2. **PR-0E-F-02:** A avaliação de modelos preditivos deve utilizar métricas compatíveis com a semântica do output, incluindo discriminação, calibração ou outras dimensões quando aplicáveis.
3. **PR-0E-F-03:** A avaliação da estratégia deve analisar explicitamente o comportamento e a taxa de decisões `NO_TRADE`.
4. **PR-0E-F-04:** A claim de valor agregado por componentes complexos (ex.: modelos adicionais de ML ou features) exige evidência incremental controlada contra baselines apropriados, podendo incluir testes de ablação ou métodos comparativos equivalentes.
5. **PR-0E-F-05:** A avaliação técnica é estritamente vinculada à versão imutável do candidato avaliado (*version-specific*).

---

## 8. Hard Quantitative Invariants (F-HQI-01 a F-HQI-46)

| ID | Hard Quantitative Invariant | Mapeamento QPI |
|---|---|---|
| **F-HQI-01** | O mérito de um modelo preditivo não equivale ao mérito da estratégia que o consome. | QPI-08 |
| **F-HQI-02** | O ranking preditivo entre modelos não corresponde necessariamente ao ranking econômico das estratégias. | QPI-08, QPI-06 |
| **F-HQI-03** | O escopo de avaliação (*EvaluationScope*) deve ser explicitamente declarado. | QPI-08, QPI-01 |
| **F-HQI-04** | Ações de controle ou veto do Risk Engine não são creditadas como mérito da estratégia. | QPI-08 |
| **F-HQI-05** | A atribuição de falha de desempenho a um componente específico exige evidência demonstrável. | QPI-01, QPI-11 |
| **F-HQI-06** | A métrica do modelo deve ser compatível com a natureza e o estimand de sua saída. | QPI-01 |
| **F-HQI-07** | A taxa de acerto isolada não define a utilidade econômica de um modelo para a estratégia. | QPI-07, QPI-06 |
| **F-HQI-08** | Capacidade de discriminação e calibração de probabilidades são dimensões distintas de avaliação. | QPI-07 |
| **F-HQI-09** | A utilidade prática de um modelo é estritamente dependente da política de decisão da estratégia. | QPI-08 |
| **F-HQI-10** | A reivindicação de contribuição de um modelo exige evidência incremental controlada contra baselines. | QPI-01, QPI-04 |
| **F-HQI-11** | O crédito atribuído a uma feature ou submodelo exige demonstração de contribuição separável. | QPI-01 |
| **F-HQI-12** | Complexidade algorítmica adicional exige demonstração de valor econômico incremental. | QPI-01, QPI-07 |
| **F-HQI-13** | A proporção e o momento de decisões `NO_TRADE` integram a avaliação da estratégia. | QPI-09 |
| **F-HQI-14** | Falsos positivos e falsos negativos possuem custos assimétricos determinados pela estratégia. | QPI-06, QPI-08 |
| **F-HQI-15** | O threshold de decisão operacional não é uma propriedade matemática intrínseca do modelo. | QPI-08 |
| **F-HQI-16** | O ranking entre candidatos pode sofrer inversão em função da composição com o sistema de execução. | QPI-08 |
| **F-HQI-17** | Desempenho global positivo não pode mascarar falhas graves em regimes operacionais materiais. | QPI-07 |
| **F-HQI-18** | A robustez estatística de um modelo não garante a robustez econômica da estratégia. | QPI-08, QPI-06 |
| **F-HQI-19** | A avaliação de uma estratégia é estritamente específica à sua versão imutável e parâmetros testados. | QPI-12 |
| **F-HQI-20** | A materialidade de uma alteração no código ou configuração é definida por seu impacto no comportamento. | QPI-12 |
| **F-HQI-21** | A comparação e o ranking entre modelos concorrentes devem considerar a incerteza estatística. | QPI-01 |
| **F-HQI-22** | A reivindicação de mérito incremental de uma estratégia exige comparação com benchmarks controlados. | QPI-01, QPI-04 |
| **F-HQI-23** | Um modelo com avaliação favorável pode coexistir legitimamente com uma estratégia desfavorável. | QPI-08, QPI-06 |
| **F-HQI-24** | A avaliação holística de candidatos não exige nem autoriza a criação de scores compensatórios universais. | QPI-07, QPI-10 |
| **F-HQI-25** | A conformidade com regras metodológicas é requisito de admissibilidade e não crédito de desempenho. | QPI-10, QPI-01 |
| **F-HQI-26** | A constatação de invalidade metodológica por violação de invariante rígido é não compensatória. | QPI-10 |
| **F-HQI-27** | Lacunas materiais de evidência delimitam o alcance das conclusões da avaliação. | QPI-01, QPI-11 |
| **F-HQI-28** | O status de componente não avaliado (`NOT_EVALUATED`) não equivale a componente aceitável. | QPI-11 |
| **F-HQI-29** | As diferentes dimensões do vetor de avaliação não podem ser agregadas por votação simples de maioria. | QPI-07, QPI-10 |
| **F-HQI-30** | Risco de cauda ou perdas extremas inaceitáveis dominam e anulam métricas de retorno positivo. | QPI-06, QPI-10 |
| **F-HQI-31** | A existência do Risk Engine não dispensa a estratégia de possuir avaliação de risco prudente. | QPI-08, QPI-06 |
| **F-HQI-32** | Comparações entre Strategies devem controlar ou explicitar diferenças materiais de policies downstream capazes de determinar o resultado. | QPI-01 |
| **F-HQI-33** | Degradação estatística do modelo (*model drift*) e perda de edge da estratégia (*decay*) são fenômenos distintos. | QPI-08 |
| **F-HQI-34** | Queda pontual no retorno não implica necessariamente perda estrutural do edge se a frequência de oportunidades mudou. | QPI-01, QPI-09 |
| **F-HQI-35** | A avaliação do candidato preserva integralmente o histórico de busca e a multiplicidade explorada. | QPI-04 |
| **F-HQI-36** | A sensibilidade a variações no modelo de execução integra a qualidade intrínseca da estratégia. | QPI-06, QPI-05 |
| **F-HQI-37** | Retornos financeiros similares não implicam equivalência de qualidade e risco entre estratégias. | QPI-07, QPI-06 |
| **F-HQI-38** | As conclusões da avaliação não podem extrapolar os limites da claim formalmente testada. | QPI-01 |
| **F-HQI-39** | O protocolo admite conclusões condicionais ou limitadas a regimes de mercado específicos. | QPI-01 |
| **F-HQI-40** | A constatação de resultado desfavorável na avaliação não autoriza o ajuste automático de parâmetros no mesmo teste. | QPI-03, QPI-10 |
| **F-HQI-41** | Avaliação técnica favorável da estratégia não constitui autorização para início de Paper Trading. | QPI-13 |
| **F-HQI-42** | Scores e rankings de pesquisa auxiliam a priorização mas não substituem os gates normativos de promoção. | QPI-13, QPI-15 |
| **F-HQI-43** | A atribuição comparativa de superioridade a um componente exige que diferenças materiais capazes de explicar o resultado estejam suficientemente controladas ou explicitamente reconhecidas. | QPI-01 |
| **F-HQI-44** | A documentação técnica do modelo (*Model Card*) não substitui a validação econômica da estratégia. | QPI-08 |
| **F-HQI-45** | O uso de Machine Learning não é obrigatório nem confere privilégio metodológico sobre regras determinísticas. | QPI-01 |
| **F-HQI-46** | Limitações metodológicas identificadas integram obrigatoriamente a conclusão formal da avaliação. | QPI-01, QPI-11 |

---

## 9. Policy / Experiment Parameters (Decisões Deliberadamente Adiada)

Permanecem abertos e parametrizáveis por experimento:
- Lista específica de métricas preditivas por família de modelo;
- Thresholds numéricos mínimos de calibração (Brier Score) e discriminação (AUC);
- Limiares exatos de decisão e confiança da estratégia;
- Regras de penalização de complexidade algorítmica;
- Critérios quantitativos para detecção de *model drift* e *strategy decay*;
- Formato físico de armazenamento e metadados de *Model Cards*.

---

## 10. Gates Internos do Bloco 0E-F

- **0E-F1:** Escopo de avaliação claramente delimitado.
- **0E-F2:** Separação conceitual estrita entre Model e Strategy.
- **0E-F3:** Avaliação de discriminação e calibração para modelos preditivos.
- **0E-F4:** Avaliação da política decisória e comportamento de `NO_TRADE`.
- **0E-F5:** Evidência incremental controlada e mensuração de valor agregado (incluindo ablação quando aplicável).
- **0E-F6:** Síntese holística vetorial de risco e retorno.
- **0E-F7:** Avaliação de robustez e sensibilidade a fricções de execução.
- **0E-F8:** Diagnóstico honesto de atribuição de falhas.
- **0E-F9:** Completude de evidência e emissão de disposição formal.
- **0E-F10:** Versionamento imutável e linhagem do candidato avaliado.
- **0E-F11:** Conformidade cruzada com 0E-A a 0E-E.
- **0E-F12:** Conformidade integral com ADRs 0007, 0013, 0016, 0021 e 0022.
