# Protocolo 0E-C — Desenho de Validação, Out-of-Sample e Baselines

- **Status:** Fechado tecnicamente no Sprint 0E
- **Data da baseline:** 2026-08-20
- **Consome:** ADR-0004, ADR-0008, ADR-0017, ADR-0021
- **Subordinado a:** QPI-01, QPI-02, QPI-03, QPI-04, QPI-07, QPI-08, QPI-10, QPI-12, QPI-13

---

## 1. Finalidade e Escopo

O Protocolo 0E-C estabelece a metodologia de separação epistemológica e temporal dos dados entre a descoberta/ajuste/seleção de modelos e seu julgamento confirmatório, respondendo à pergunta:
> *Como garantir que a evidência dita "fora da amostra" (Out-of-Sample — OOS) seja genuinamente externa e independente em relação a todo o processo que produziu o candidato avaliado?*

---

## 2. OOS como Relação Epistemológica

### 2.1. Definição de Out-of-Sample (OOS)
Evidência proveniente de observações que não participaram, direta ou indiretamente, da formulação, ajuste (*fitting*), calibração, seleção ou adaptação material do candidato específico cuja claim está sendo avaliada.

OOS **não é** um rótulo estático ou propriedade intrínseca de um arquivo ou partição de datas: é uma **relação** entre um conjunto de dados e o histórico de desenvolvimento de um candidato.

### 2.2. As Quatro Funções de Dados no Processo Científico
1. **Development Domain:** Dados abertos para exploração, formulação de hipóteses, engenharia de features, identificação de regimes e definição de regras.
2. **Training / Fit Domain:** Subconjunto específico de desenvolvimento utilizado para estimar parâmetros livres de um modelo.
3. **Validation / Selection Domain:** Subconjunto de desenvolvimento utilizado para otimização de hiperparâmetros, calibração e seleção entre candidatos concorrentes (integra formalmente o desenvolvimento).
4. **Protected Evaluation Domain:** Partição estritamente reservada para julgamento final, que jamais participou de qualquer decisão que originou o candidato.

```text
+-------------------------------------------------------------+-------------------------------+
|                    DEVELOPMENT DOMAIN                       |  PROTECTED EVALUATION DOMAIN  |
|  +------------------------+-------------------------------+  |                               |
|  |   TRAINING / FIT       |    VALIDATION / SELECTION     |  |      PROTECTED OOS TEST       |
|  |   (ajuste de pesos)    |    (tuning, escolha de winner)|  |      (julgamento cego)        |
|  +------------------------+-------------------------------+  |                               |
+-------------------------------------------------------------+-------------------------------+
```

### 2.3. Consumo da Proteção Epistemológica
A proteção de um conjunto de avaliação é um recurso consumível: se o resultado no conjunto protegido for utilizado para alterar hiperparâmetros, features ou regras do candidato, aquele conjunto passa a integrar o histórico de desenvolvimento e perde sua independência para a nova versão gerada.

---

## 3. Desenho de Validação Temporal

### 3.1. Causalidade Temporal Obrigatória
A validação de estratégias intradiárias e séries temporais financeiras deve preservar a ordem cronológica estrita dos fatos. Embaralhamento aleatório (*random k-fold cross-validation*) isolado é metodologicamente inválido para validar estratégias prospectivas.

### 3.2. Walk-Forward Analysis
Sequência ordenada de avaliações em que, para cada dobra (*fold*), o candidato é ajustado e selecionado utilizando apenas a informação admissível anterior e avaliado no período imediatamente posterior.
- Modalidades permitidas: janela rolante (*rolling window*) ou janela expansiva (*expanding window*);
- Cada fold possui seu próprio *knowledge boundary* e *cutoff* independente.

### 3.3. Purging e Embargo
- **Purging:** Neutralização e remoção de observações de desenvolvimento cujo horizonte de cálculo ou rótulo (*label*) sobreponha a fronteira da partição protegida.
- **Embargo:** Intervalo de segurança temporal adicionado imediatamente após o conjunto de treinamento/validação para eliminar autocorrelação serial ou dependência de curto prazo residual.
- Purging, embargo, separação temporal equivalente ou outro método justificável permanecem possibilidades metodológicas de policy para controle de dependência informacional e sobreposição.

### 3.4. Toda Escolha Adaptativa Conta
Para fins de integridade OOS, qualquer ajuste baseado em dados consome independência, incluindo:
- Ajuste de hiperparâmetros;
- Otimização de thresholds decisórios;
- Seleção de subconjuntos de atributos (*feature selection*);
- Escolha de janelas temporais de médias ou volatilidade;
- Regras de parada antecipada (*early stopping*);
- Ponderação de modelos em *ensembles*.

---

## 4. Segmentação por Regime e Baselines

### 4.1. Regimes de Mercado
- Se um regime for utilizado pela estratégia como filtro ou entrada causal, sua detecção deve ser puramente *point-in-time* e calculada causalmente.
- Regimes identificados retrospectivamente (*post-hoc*) não podem ser utilizados para mascarar períodos de perda da estratégia histórica, gerando nova hipótese exploratória.

### 4.2. Hierarquia Canônica de Comparadores e Baselines
Nenhuma estratégia pode ser promovida com base apenas em desempenho superior a zero. Todo experimento deve confrontar o candidato com os comparadores e baselines materialmente apropriados às claims que pretende sustentar, selecionados a partir da hierarquia canônica (sem exigência de executar todos simultaneamente em qualquer escopo):
1. **Predictive Baseline:** Modelos ingênuos (ex.: persistência, média móvel simples, ruído aleatório) quando a claim for de capacidade preditiva informacional.
2. **Decision-Policy Baseline:** Políticas determinísticas simples (ex.: sempre comprar, comprar e manter, posições baseadas em regras elementares) quando a claim for de política decisória.
3. **Economic Benchmark:** Retorno ajustado a custos do ativo de referência no mesmo período temporal quando a claim for de mérito econômico.
4. **Ablation Reference:** Versão da própria estratégia com componentes críticos removidos (ex.: sem o modelo de ML, sem meta-labeling) para mensurar a contribuição marginal de cada parte.

### 4.3. Model OOS versus Strategy OOS
Um modelo de Machine Learning pode ter sido avaliado em regime estritamente OOS, mas a estratégia completa que o consome pode estar contaminada (*in-sample*) se os thresholds de decisão, regras de dimensionamento ou filtros de saída foram calibrados diretamente sobre o conjunto de avaliação.

---

## 5. Protocol Requirements

1. **PR-0E-C-01:** O desenho experimental deve explicitar os limites de *EvaluationBoundary* para cada fold ou partição de teste.
2. **PR-0E-C-02:** A validação confirmatória para fins de promoção deve utilizar estrutura temporal estritamente causal (ex.: walk-forward).
3. **PR-0E-C-03:** Em cenários com horizontes ou rótulos sobrepostos (*overlapping outcome windows*), o desenho experimental deve aplicar controle metodológico adequado (purging, embargo ou separação equivalente) para prevenir vazamento informacional entre partições protegidas.
4. **PR-0E-C-04:** A performance do candidato deve ser confrontada com comparadores e baselines previamente definidos e materialmente apropriados às claims sustentadas.
5. **PR-0E-C-05:** A estabilidade temporal e o comportamento entre diferentes regimes de mercado devem ser avaliados através de múltiplos períodos quando materialmente pertinentes à claim.

---

## 6. Hard Quantitative Invariants (C-HQI-01 a C-HQI-32)

| ID | Hard Quantitative Invariant | Mapeamento QPI |
|---|---|---|
| **C-HQI-01** | OOS é uma relação causal e epistemológica relativa ao candidato e sua linhagem de desenvolvimento. | QPI-03, QPI-01 |
| **C-HQI-02** | Dados utilizados para selecionar entre candidatos integram o conjunto de desenvolvimento (*validation/selection*). | QPI-03, QPI-04 |
| **C-HQI-03** | As funções de ajuste/seleção e julgamento protegido devem ser rigorosamente separáveis. | QPI-03, QPI-02 |
| **C-HQI-04** | A promoção para etapas prospectivas exige evidência temporalmente protegida e independente. | QPI-01, QPI-13 |
| **C-HQI-05** | Evidência consumida por adaptação ou ajuste não continua "não vista" (*unseen*). | QPI-03 |
| **C-HQI-06** | Qualquer adaptação material gera um novo sujeito de avaliação com histórico próprio. | QPI-12, QPI-03 |
| **C-HQI-07** | A validação confirmatória promocional deve preservar integralmente a causalidade temporal. | QPI-02 |
| **C-HQI-08** | Embaralhamento aleatório (*random shuffle*) isolado não substitui validação temporal prospectiva. | QPI-02, QPI-01 |
| **C-HQI-09** | Cada fold de uma análise walk-forward possui seu próprio *knowledge boundary* estrito. | QPI-02 |
| **C-HQI-10** | Rótulos com horizontes sobrepostos não podem cruzar partições protegidas sem controle metodológico adequado (purging, embargo, separação equivalente ou outro método justificável). | QPI-02, QPI-10 |
| **C-HQI-11** | A separação temporal entre treino e teste deve acompanhar a dependência informacional real dos dados. | QPI-02 |
| **C-HQI-12** | O ajuste fino de hiperparâmetros (*tuning*) deve ocorrer estritamente dentro do limite de desenvolvimento. | QPI-03 |
| **C-HQI-13** | Toda escolha adaptativa material (features, janelas, thresholds) conta como seleção e consome graus de liberdade. | QPI-04, QPI-03 |
| **C-HQI-14** | Regras de parada antecipada adaptativas (*early stopping*) integram o processo de busca e seleção. | QPI-04 |
| **C-HQI-15** | Regime de mercado descoberto *post-hoc* gera nova hipótese exploratória e não pode justificar falha passada. | QPI-04, QPI-02 |
| **C-HQI-16** | O regime de mercado utilizado em tempo de decisão deve ser mensurável de forma puramente causal. | QPI-02 |
| **C-HQI-17** | A população de dados avaliada no teste deve corresponder ao escopo formal da claim pretendida. | QPI-01 |
| **C-HQI-18** | Obter retorno superior a zero não constitui por si só evidência de benchmarking suficiente. | QPI-06, QPI-07 |
| **C-HQI-19** | O benchmark de comparação não pode ser selecionado retrospectivamente em função do resultado. | QPI-04 |
| **C-HQI-20** | A comparação com baselines e concorrentes exige condições experimentais estritamente comparáveis. | QPI-01 |
| **C-HQI-21** | Complexidade arquitetural adicional não confere mérito por si só sem ganho incremental demonstrado. | QPI-01, QPI-07 |
| **C-HQI-22** | O ajuste de modelos de calibração de probabilidades integra o conjunto de desenvolvimento. | QPI-03 |
| **C-HQI-23** | A robustez temporal da estratégia não pode depender do resultado de uma única janela temporal favorável. | QPI-07, QPI-01 |
| **C-HQI-24** | A agregação de resultados entre múltiplos folds não pode ocultar heterogeneidade ou colapso temporal grave. | QPI-07 |
| **C-HQI-25** | A validade OOS de um modelo não implica automaticamente a validade OOS da estratégia que o utiliza. | QPI-08 |
| **C-HQI-26** | A partição protegida de avaliação jamais pode ser utilizada para escolher o candidato vencedor. | QPI-03, QPI-10 |
| **C-HQI-27** | O próprio desenho de validação possui linhagem e deve ser registrado ex ante. | QPI-12, QPI-04 |
| **C-HQI-28** | Evidência OOS/protegida é necessária, mas não suficiente, para sustentar claims promocionais de generalização/viabilidade econômica. | QPI-01, QPI-06 |
| **C-HQI-29** | O desenho de validação também pode sofrer sobreajuste (*overfit*) se repetidamente modificado. | QPI-03, QPI-04 |
| **C-HQI-30** | A avaliação protegida exige que todos os hiperparâmetros e regras estejam materialmente fixados ex ante. | QPI-03, QPI-12 |
| **C-HQI-31** | Alteração ou reparo material no candidato após a observação do teste protegido exige nova avaliação sob evidência temporalmente protegida e independente. | QPI-03, QPI-10 |
| **C-HQI-32** | O escopo de generalização reivindicado não pode exceder o escopo dos dados efetivamente avaliados. | QPI-01 |

---

## 7. Policy / Experiment Parameters (Decisões Deliberadamente Adiada)

Permanecem abertos e parametrizáveis por experimento:
- Datas e intervalos exatos de divisão entre treino, validação e teste protegido;
- Proporções e tamanhos das janelas de amostragem;
- Número exato de dobras (*folds*) no walk-forward;
- Método de purging (*purge method*) e horizonte de purging (*purge horizon*);
- Método de embargo (*embargo method*) e duração de embargo (*embargo duration*);
- Definição algorítmica específica de regimes de volatilidade ou tendência;
- Lista e seleção de baselines e benchmarks específicos a serem executados em função das claims;
- Thresholds numéricos de estabilidade entre folds.

---

## 8. Gates Internos do Bloco 0E-C

- **0E-C1:** Semântica clara de Development, Fit, Selection e Protected Test.
- **0E-C2:** Independência estrita de dados protegidos OOS.
- **0E-C3:** Desenho de validação temporal causal e walk-forward.
- **0E-C4:** Controle adequado de overlap/dependência, incluindo purging, embargo ou alternativa justificável.
- **0E-C5:** Registro de seleção adaptativa e prevenção de reúso de teste.
- **0E-C6:** Causalidade na segmentação de regimes de mercado.
- **0E-C7:** Existência e paridade de baselines e benchmarks.
- **0E-C8:** Avaliação de estabilidade e calibração.
- **0E-C9:** Conformidade cruzada com 0E-A e 0E-B.
- **0E-C10:** Conformidade integral com ADRs 0004, 0008, 0017 e 0021.
