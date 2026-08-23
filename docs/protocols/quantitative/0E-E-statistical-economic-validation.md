# Protocolo 0E-E — Validação Estatística e Econômica

- **Status:** Fechado tecnicamente no Sprint 0E
- **Data da baseline:** 2026-08-20
- **Consome:** ADR-0004, ADR-0008, ADR-0013, ADR-0017, ADR-0021
- **Subordinado a:** QPI-01, QPI-03, QPI-04, QPI-06, QPI-07, QPI-08, QPI-09, QPI-10, QPI-11, QPI-12, QPI-13

---

## 1. Finalidade e Escopo

O Protocolo 0E-E estabelece o framework inferencial, estatístico e de avaliação de risco para determinar a validade de resultados quantitativos, respondendo à pergunta:
> *Dado um conjunto metodologicamente admissível de resultados econômicos simulados, quanta evidência estatística e empírica existe de que o desempenho observado não é fruto de mero acaso, dependência temporal, seleção oportunista, data snooping, regime transitório ou fragilidade a pequenas perturbações?*

Princípio orientador fundamental:
```text
ESTATISTICAMENTE DISCERNÍVEL
≠ ECONOMICAMENTE RELEVANTE
≠ MERITÓRIO DE PROMOÇÃO
```

---

## 2. Estimands, Unidades e Dependência Estatística

### 2.1. O Conceito de Estimand
Toda análise estatística deve responder a um estimand formalmente definido antes do cálculo de métricas:
```text
Research Question → Estimand → Estimator / Metric
```
O estimand define a quantidade populacional, econômica ou probabilística que o experimento pretende inferir sobre o domínio da hipótese.

### 2.2. Tamanho Amostral Nominal versus Informação Efetiva
- O número de trades ou barras simuladas (\(N\)) não equivale à quantidade de informação estatística independente;
- Operações financeiras intradiárias sofrem frequentemente de forte autocorrelação serial, agrupamento temporal (*clustering*) e sobreposição de horizontes;
- Métodos inferenciais devem incorporar a dependência temporal na quantificação de incerteza (ex.: através de bootstrap em blocos, HAC ou modelos de dependência).

### 2.3. Estimativas Pontuais e Incerteza
Nenhuma claim relevante para fins de promoção pode se basear exclusivamente em estimativas pontuais (médias ou razões). É obrigatório caracterizar a incerteza amostral e estrutural através de intervalos de confiança, distribuições empíricas ou intervalos de credibilidade.

A distribuição gaussiana não pode ser assumida por conveniência quando os retornos de cauda apresentarem curtose e assimetria materiais.

---

## 3. Famílias de Métricas e Interpretação

Nenhuma métrica isolada define a qualidade total de uma estratégia. A avaliação exige uma visão vetorial e multidimensional dividida em cinco famílias:

1. **A — Magnitude Econômica:** Resultado financeiro líquido acumulado, retorno esperado por trade/oportunidade, expectativa matemática (*expectancy*), média e mediana de retornos.
2. **B — Risco de Cauda e Downside:** Avaliação apropriada do risco de cauda e downside quando material à claim (ex.: semivariância negativa / downside deviation, Value at Risk / VaR, Expected Shortfall / ES / CVaR, quantis inferiores da distribuição, probabilidade de perda e perdas máximas condicionadas), constituindo opções metodológicas sujeitas à policy do experimento e não um conjunto métrico universal obrigatório.
3. **C — Risco de Trajetória (*Path Risk*):** Drawdown máximo, duração do drawdown, tempo de recuperação (*time underwater*), assimetria de perdas sequenciais.
4. **D — Relações Ajustadas ao Risco:** Sharpe-like, Sortino-like e Calmar-like ratios com convenções de frequência e annualization explicitamente declaradas e compatíveis com a semântica temporal dos retornos, além de tratamento explícito de autocorrelação.
5. **E — Diagnósticos de Operação:** Fator de lucro (*profit factor*), taxa de acerto (*hit rate*), razão ganho/perda (*payoff ratio*), turnover, custo relativo de fricções (*cost burden*), frequência de operações, taxa de `NO_TRADE` e slippage realizado.

### 3.1. Rejeição da Primazia da Taxa de Acerto (Accuracy / Hit Rate)
A taxa de acerto é uma métrica descritiva sem primazia econômica isolada: uma estratégia com 90% de taxa de acerto pode ser economicamente inviável se suas perdas médias excederem drasticamente os ganhos, ou se sofrer de risco de cauda catastrófico.

### 3.2. Expectancy e Profit Factor
- **Expectancy:** Exige definição clara da unidade econômica (pontos, moeda, percentual) e da população considerada (por barra, por trade ou por oportunidade de decisão).
- **Profit Factor:** Exige contexto distributivo e análise de concentração para verificar se o resultado não foi gerado por um único evento extremo atípico (*one lucky trade*).

### 3.3. Sharpe Ratio e Anualização
O cálculo do Sharpe Ratio deve explicitar o ativo livre de risco utilizado como referência, a base temporal dos retornos e o tratamento de dependência serial. A mera multiplicação por fatores de anualização (\(\sqrt{252}\)) não cria informação nova e distorce a significância estatística em séries autocorrelacionadas.

---

## 4. Testes de Múltiplas Hipóteses e Data Snooping

### 4.1. O Problema da Multiplicidade
A busca de estratégias lucrativas envolve a testagem de múltiplos modelos, combinações de parâmetros, subconjuntos de features e regras de saída. Quanto maior o espaço de busca explorado, maior a probabilidade de encontrar estratégias com métricas favoráveis puramente por acaso.

### 4.2. Tratamento de Data Snooping
- O viés de *data snooping* existe mesmo quando não são calculados p-values formais;
- A interpretação do candidato vencedor deve preservar a história material da família de busca (*search family*);
- Métodos de controle de taxa de falso descobrimento (FDR/FWER) ou penalizações baseadas no tamanho do espaço de busca devem ser considerados em avaliações confirmatórias;
- A melhor semente aleatória (*best seed*) ou o melhor fold em validação cruzada não representam estimativas neutras da performance esperada.

---

## 5. Análise de Robustez e Estresse

### 5.1. Definição de Robustez
Persistência qualitativa e economicamente relevante do desempenho sob perturbações plausíveis no ambiente de teste que não alterem a premissa central da estratégia.

### 5.2. Dimensões de Fragilidade e Robustez
As dimensões de fragilidade e robustez devem ser avaliadas quando materialmente aplicáveis à claim e ao escopo do experimento:
1. **Sensibilidade a Parâmetros (*Parameter Sensitivity / Cliffs*):** Avaliação de estabilidade na vizinhança de parâmetros materiais quando a claim reivindicar robustez paramétrica; degradações abruptas (*cliffs*) devem ser incorporadas à decisão.
2. **Sensibilidade a Custos (*Cost Stress*):** Avaliação do impacto de deterioração de spread, slippage e taxas quando a viabilidade econômica líquida for reivindicada.
3. **Robustez a Regimes (*Regime Robustness*):** Avaliação da sensibilidade a diferentes regimes de mercado quando a claim abranger múltiplos ambientes macroeconômicos ou de volatilidade.
4. **Cenários Adversariais (*Adversarial Scenarios / Stress*):** Testes de estresse estruturados para verificar os limites de falsificação sob condições adversas relevantes à hipótese.

---

## 6. Precedência Metodológica e Inconclusividade

A síntese da evidência obedece à seguinte ordem de precedência estrita:
```text
1. Validade Epistemológica (ausência de leakage e look-ahead)
        ↓
2. Validade Econômica e de Execução (fidelidade de simulação e fricções)
        ↓
3. Interpretação Estatística e Incerteza (amostragem, dependência, caudas)
        ↓
4. Síntese do Candidato (robustez, complexidade, baselines)
        ↓
5. Decisão de Promoção / Elegibilidade
```

> **Regra do Elo Mais Fraco:** A força final da claim científica é limitada pelo elo mais fraco da cadeia de validação:
\[
Strength_{claim} \le \min(DataIntegrity, ValidationIntegrity, SimulationFidelity, StatisticalEvidence)
\]

Estatística sofisticada ou p-values baixos jamais reparam dados contaminados ou simulações irrealistas.

---

## 7. Protocol Requirements

1. **PR-0E-E-01:** Toda claim quantitativa deve registrar formalmente seu estimand e métricas primárias e secundárias correspondentes.
2. **PR-0E-E-02:** A análise de desempenho deve reportar intervalos de incerteza ou distribuições empíricas para as métricas centrais.
3. **PR-0E-E-03:** A avaliação econômica para fins promocionais deve ser realizada em base líquida das fricções materiais aplicáveis à claim e à forma de execução avaliada (incluindo custos, taxas, spread e slippage quando materialmente pertinentes).
4. **PR-0E-E-04:** O histórico de busca e a multiplicidade de testes devem ser registrados na documentação de avaliação.
5. **PR-0E-E-05:** Devem ser executadas avaliações apropriadas de risco de cauda e sensibilidade quando materiais à claim (testes de estresse de custos, sensibilidade de parâmetros); VaR, Expected Shortfall, quantis inferiores e outras medidas de cauda permanecem opções metodológicas sujeitas à policy do experimento.

---

## 8. Hard Quantitative Invariants (E-HQI-01 a E-HQI-55)

| ID | Hard Quantitative Invariant | Mapeamento QPI |
|---|---|---|
| **E-HQI-01** | Significância estatística, relevância econômica e mérito para promoção são conclusões distintas. | QPI-01, QPI-06, QPI-13 |
| **E-HQI-02** | Toda métrica calculada deve responder a um estimand e população formalmente definidos. | QPI-01 |
| **E-HQI-03** | Métricas econômicas exigem unidade, denominador e moeda explicitamente declarados. | QPI-06 |
| **E-HQI-04** | O tamanho amostral nominal (\(N\)) não equivale à quantidade de informação estatística independente. | QPI-01 |
| **E-HQI-05** | Dependência temporal material e autocorrelação devem ser incorporadas na quantificação de incerteza. | QPI-01, QPI-06 |
| **E-HQI-06** | A sobreposição de janelas de retorno reduz a informação efetiva mesmo na ausência de leakage. | QPI-01 |
| **E-HQI-07** | Estimativa pontual isolada é insuficiente para sustentar claims estatísticas ou econômicas fortes. | QPI-01, QPI-06 |
| **E-HQI-08** | A interpretação verbal da incerteza deve corresponder rigorosamente ao método estatístico utilizado. | QPI-01 |
| **E-HQI-09** | A distribuição normal de retornos não pode ser assumida por conveniência analítica. | QPI-01, QPI-06 |
| **E-HQI-10** | A média de retornos não caracteriza por si só toda a estrutura e risco da distribuição. | QPI-07, QPI-06 |
| **E-HQI-11** | Nenhuma métrica única isolada representa a qualidade total de uma estratégia. | QPI-07 |
| **E-HQI-12** | A taxa de acerto (*hit rate*) não possui primazia econômica independente sobre o resultado líquido. | QPI-07, QPI-06 |
| **E-HQI-13** | O cálculo de expectativa matemática (*expectancy*) exige definição clara da variável e população base. | QPI-06 |
| **E-HQI-14** | O fator de lucro (*profit factor*) exige análise da distribuição para prevenir distorção por outliers. | QPI-07, QPI-06 |
| **E-HQI-15** | O índice de Sharpe exige especificação completa de taxa livre de risco, frequência e autocorrelação. | QPI-07, QPI-01 |
| **E-HQI-16** | Fórmulas de anualização de volatilidade e retornos não criam informação empírica nova. | QPI-01 |
| **E-HQI-17** | Métricas dependentes de trajetória (*path-dependent*) exigem contexto temporal e histórico. | QPI-06, QPI-07 |
| **E-HQI-18** | O drawdown máximo isolado pode ser insuficiente para caracterizar a severidade e duração de perdas. | QPI-07, QPI-06 |
| **E-HQI-19** | Métricas de quantil simples (ex.: VaR) não caracterizam sozinhas a severidade da cauda extrema. | QPI-06, QPI-07 |
| **E-HQI-20** | Métricas de cauda não podem aparentar precisão estatística superior aos dados disponíveis na cauda. | QPI-01, QPI-11 |
| **E-HQI-21** | O cálculo de probabilidade de perda exige definição estrita do evento de perda e do horizonte. | QPI-06 |
| **E-HQI-22** | A probabilidade de ruína é condicional às políticas de dimensionamento, capital e alavancagem. | QPI-06 |
| **E-HQI-23** | Métricas econômicas promocionais devem refletir as fricções materiais aplicáveis à claim e à forma de execução avaliada. | QPI-06 |
| **E-HQI-24** | A detecção de um efeito estatístico não nulo não equivale a um efeito economicamente material. | QPI-06, QPI-01 |
| **E-HQI-25** | Claim de superioridade ou valor incremental exige evidência controlada contra comparadores. | QPI-01, QPI-04 |
| **E-HQI-26** | A agregação de resultados entre folds e janelas temporais exige semântica explícita de ponderação. | QPI-01 |
| **E-HQI-27** | A agregação de métricas não pode ocultar colapsos ou heterogeneidades temporais materiais. | QPI-07 |
| **E-HQI-28** | Robustez metodológica não significa invariância numérica estrita diante de perturbações. | QPI-01 |
| **E-HQI-29** | Quedas abruptas de desempenho em parâmetros vizinhos (*parameter cliffs*) indicam fragilidade. | QPI-01, QPI-06 |
| **E-HQI-30** | A sensibilidade do resultado a variações adversas de custos deve permanecer explicitamente visível. | QPI-06 |
| **E-HQI-31** | A concentração de retornos em regimes específicos deve coincidir com o escopo formal da claim. | QPI-01 |
| **E-HQI-32** | A multiplicidade do processo de busca e seleção altera a interpretação da significância do vencedor. | QPI-04, QPI-03 |
| **E-HQI-33** | O viés de *data snooping* afeta a validade inferencial mesmo na ausência de testes de hipótese formais. | QPI-04 |
| **E-HQI-34** | A família material de hipóteses e modelos testados durante a pesquisa deve permanecer identificável. | QPI-04, QPI-12 |
| **E-HQI-35** | O valor-p (*p-value*) não constitui um score direto de qualidade ou autorização de promoção. | QPI-07, QPI-01 |
| **E-HQI-36** | Precisão estatística insuficiente em relação à claim gera desfecho `INCONCLUSIVE`, não aprovação. | QPI-11, QPI-01 |
| **E-HQI-37** | Resultados negativos e hipóteses rejeitadas no mesmo programa de pesquisa integram a linhagem. | QPI-04, QPI-12 |
| **E-HQI-38** | Cenários de teste de robustez não podem ser selecionados retrospectivamente por conveniência. | QPI-04, QPI-01 |
| **E-HQI-39** | Cenários de estresse constituem testes de vulnerabilidade estrutural e não previsões probabilísticas. | QPI-06 |
| **E-HQI-40** | Eventos reais de cauda extrema observados nos dados não podem ser descartados como outliers para inflar métricas. | QPI-06, QPI-10 |
| **E-HQI-41** | Índices ajustados ao risco (*risk-adjusted ratios*) não substituem a análise de perdas em valores absolutos. | QPI-06, QPI-07 |
| **E-HQI-42** | O cálculo de métricas agregadas não pode apagar a taxa de seletividade e decisões `NO_TRADE`. | QPI-09, QPI-07 |
| **E-HQI-43** | A interpretação do desempenho financeiro pode exigir contextualização da exposição e capital alocado. | QPI-06 |
| **E-HQI-44** | Incerteza e limitações do modelo de simulação de execução não podem ser ocultadas por precisão estatística. | QPI-01, QPI-05 |
| **E-HQI-45** | A escolha da melhor semente aleatória (*best seed*) em simulações estocásticas constitui seleção e viés. | QPI-04, QPI-03 |
| **E-HQI-46** | Determinismo computacional de um backtest não equivale a certeza empírica de generalização futura. | QPI-01 |
| **E-HQI-47** | Complexidade arquitetural material exige justificativa e evidência incremental quando pertinente à claim. | QPI-01, QPI-07 |
| **E-HQI-48** | A troca oportunista da métrica de avaliação em função do resultado (*metric shopping*) constitui seleção enviesada. | QPI-04, QPI-07 |
| **E-HQI-49** | Ser o melhor candidato dentro de um espaço de busca massivo não prova viabilidade absoluta fora da amostra. | QPI-04, QPI-01 |
| **E-HQI-50** | O teste de robustez deve ser genuinamente capaz de falsificar a hipótese sob condições adversas. | QPI-01 |
| **E-HQI-51** | Cenários de estresse devem manter consistência econômica e estrutural interna entre as variáveis. | QPI-06 |
| **E-HQI-52** | Métricas conflitantes no vetor de avaliação exigem síntese e julgamento explícitos, sem pesos arbitrários. | QPI-07 |
| **E-HQI-53** | O veredito `INCONCLUSIVE` é uma disposição científica legítima diante de evidência ambígua. | QPI-11, QPI-01 |
| **E-HQI-54** | Sofisticação estatística ou técnicas avançadas de bootstrap não corrigem invalidade metodológica prévia. | QPI-10, QPI-01 |
| **E-HQI-55** | A força inferencial final não pode superar a fraqueza de etapas upstream de integridade ou simulação. | QPI-01, QPI-10 |

---

## 9. Policy / Experiment Parameters (Decisões Deliberadamente Adiada)

Permanecem abertos e parametrizáveis por experimento:
- Definição formal do estimand de cada estudo;
- Lista de métricas primárias e secundárias do experimento;
- Níveis de significância estatística (\(\alpha\)) e intervalos de confiança (95%, 99%);
- Escolha da metodologia inferencial (frequentista, bayesiana, bootstrap estacionário);
- Comprimento dos blocos em bootstrap temporal;
- Métodos específicos de controle de multiplicidade (Bonferroni, Holm, Benjamini-Hochberg, White's Reality Check);
- Thresholds numéricos mínimos de Sharpe, Sortino, Calmar e Expectancy;
- Níveis de corte para VaR e Expected Shortfall (ex.: 95%, 99%);
- Grade de parâmetros para testes de sensibilidade e perturbação de custos.

---

## 10. Gates Internos do Bloco 0E-E

- **0E-E1:** Estimand e unidades econômicas formalmente especificados.
- **0E-E2:** Tratamento de dependência serial e cálculo de informação efetiva.
- **0E-E3:** Caracterização explícita de incerteza estatística.
- **0E-E4:** Cobertura vetorial das cinco famílias de métricas.
- **0E-E5:** Avaliação de risco de cauda, downside e trajetórias.
- **0E-E6:** Ponderação consistente na agregação de folds.
- **0E-E7:** Registro da multiplicidade de testes e prevenção de snooping.
- **0E-E8:** Análise de robustez e estabilidade paramétrica.
- **0E-E9:** Testes de estresse de custos e execução.
- **0E-E10:** Disposições claras de evidência (Favorable, Unfavorable, Inconclusive, Invalid).
- **0E-E11:** Conformidade cruzada com 0E-A, 0E-B, 0E-C e 0E-D.
- **0E-E12:** Conformidade integral com ADRs 0004, 0008, 0013, 0017 e 0021.
