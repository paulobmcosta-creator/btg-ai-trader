# Protocolo 0E-A — Semântica Experimental e Hipótese Quantitativa

- **Status:** Fechado tecnicamente no Sprint 0E
- **Data da baseline:** 2026-08-20
- **Consome:** ADR-0001 a ADR-0022 (especialmente ADR-0007, ADR-0013, ADR-0016 e ADR-0021)
- **Subordinado a:** QPI-01, QPI-02, QPI-03, QPI-04, QPI-08, QPI-09, QPI-10, QPI-12, QPI-13

---

## 1. Finalidade e Escopo

O objetivo do Protocolo 0E-A é formalizar a ontologia do processo de pesquisa quantitativa, garantindo que toda investigação parta de hipóteses falsificáveis, rastreáveis e epistemologicamente honestas.

A cadeia de pesquisa científica quantitativa segue o fluxo:

```text
Research Question
        ↓
QuantitativeHypothesis
        ↓
ExperimentalDesign
        ↓
Experiment
        ↓
1..N Runs
        ↓
Evidence Artifacts
        ↓
Hypothesis Assessment
```

Esta cadeia epistemológica governa o método de pesquisa e **não substitui** a cadeia operacional em runtime (`Signal → StrategyDecision → Risk → Execution`).

---

## 2. Conceitos Semânticos Centrais

### 2.1. QuantitativeHypothesis
Afirmação quantitativamente avaliável, temporalmente situada e potencialmente falsificável acerca de uma relação preditiva, decisória ou econômica. Sua interpretação depende estritamente de um *information set* admissível, um domínio de aplicação, um *outcome* definido e uma regra previamente identificável para distinguir evidência favorável, desfavorável ou inconclusiva.

Uma hipótese **não é**:
- Uma ideia vaga de mercado;
- Uma `Strategy` ou um `Model`;
- Um conjunto de hiperparâmetros ajustados;
- Um `Run` de computador ou um backtest;
- Uma conclusão formulada retrospectivamente após observar dados.

Estrutura semântica mínima:
- Identidade e versão da hipótese;
- Intenção de pesquisa (*Research Intent*);
- Domínio e sujeito de aplicação (*Subject / Domain*);
- Contexto de observação e decisão;
- Especificação do *information set* admissível;
- Semântica de *outcome* e horizonte de avaliação;
- Requisitos de comparador e benchmark;
- Relação ou direção esperada;
- Interpretação econômica líquida (quando aplicável);
- Regra prévia de falsificação e avaliação;
- Escopo experimental e linhagem (*provenance/lineage*).

### 2.2. Falsificabilidade e Versionamento
Toda hipótese confirmatória deve admitir antecipadamente três desfechos:
1. **Evidência favorável**;
2. **Evidência desfavorável**;
3. **Evidência inconclusiva**.

É estritamente proibido reescrever uma hipótese retrospectivamente após a observação dos dados para transformar um resultado desfavorável em sucesso aparente. Alterações de premissas geram uma nova versão da hipótese (`Hypothesis v2`), mantendo o histórico da versão anterior.

### 2.3. Distinção de Escopos de Hipótese
- **Predictive / Estimative Claim:** Afirmação sobre propriedades estatísticas ou probabilísticas de um estimador ou modelo preditivo.
- **Decision-Policy Claim:** Afirmação sobre o comportamento de uma política decisória que mapeia informação em `StrategyDecision` (`NO_TRADE` vs `PROPOSE_TRADE`).
- **Economic Claim:** Afirmação sobre o resultado econômico líquido de uma estratégia sob fricções reais e incerteza.

> **Regra fundamental:** Capacidade preditiva não implica valor econômico.

### 2.4. Relação Experiment vs Run
- **Experiment:** Investigação epistemicamente delimitada de uma ou mais hipóteses sob um desenho experimental identificável.
- **Run:** Execução computacional concreta e delimitada (identificada por `RunId`, conforme ADR-0021) que materializa parte ou a totalidade de um experimento.

Um experimento pode conter múltiplos `Runs` (ex.: treinamento, avaliação OOS, variação de seeds, testes de robustez), mas mantém sua identidade experimental agregadora.

### 2.5. Pesquisa Exploratória versus Confirmatória
- **Exploratory Intent:** Busca livre de padrões, geração de atributos, comparação de formulações e levantamento de novas hipóteses. Não serve como confirmação independente.
- **Confirmatory Intent:** Avaliação rigorosa de uma hipótese pré-especificada contra dados que preservam independência epistemológica.

### 2.6. DecisionOpportunity e First-Class NO_TRADE
- **DecisionOpportunity:** Contexto temporal e informacional legítimo no qual uma estratégia tem a oportunidade de produzir uma `StrategyDecision`.
- `NO_TRADE` é um resultado decisório explícito e de primeira classe, não uma ausência de dado ou falha do sistema.
- Eventos de mercado, oportunidades de decisão, ordens, trades e observações estatísticas são grandezas com cardinalidades e significados distintos.

### 2.7. CandidateModel versus CandidateStrategy
- **CandidateModel:** Componente analítico que processa features e produz scores, probabilidades, estimativas contínuas ou classificações de regime.
- **CandidateStrategy:** Política decisória completa que consome dados, previsões de modelos e regras operacionais para gerar `StrategyDecision`.
- Um modelo não negocia; quem propõe trades é a estratégia.

---

## 3. Protocol Requirements

1. **PR-0E-A-01:** Toda investigação quantitativa deve registrar formalmente uma `QuantitativeHypothesis` antes da execução de avaliações confirmatórias.
2. **PR-0E-A-02:** O desenho experimental deve explicitar o *Research Intent* (`EXPLORATORY` vs `CONFIRMATORY`).
3. **PR-0E-A-03:** A linhagem de pesquisa (*research lineage*) deve registrar a evolução de hipóteses e experimentos predecessores.
4. **PR-0E-A-04:** A seleção entre múltiplos candidatos e o histórico de busca devem ser registrados como parte integrante do experimento.
5. **PR-0E-A-05:** Toda claim econômica deve ser avaliada considerando custos e fricções materiais compatíveis com o domínio.

---

## 4. Hard Quantitative Invariants (A-HQI-01 a A-HQI-16)

Os seguintes invariantes são estritamente obrigatórios e não compensatórios:

| ID | Hard Quantitative Invariant | Mapeamento QPI |
|---|---|---|
| **A-HQI-01** | Hipótese confirmatória deve ser formalmente falsificável ex ante. | QPI-01 |
| **A-HQI-02** | Hipótese não pode ser redefinida retrospectivamente contra a própria evidência observada. | QPI-04, QPI-12 |
| **A-HQI-03** | Capacidade preditiva estatística não equivale a valor ou viabilidade econômica. | QPI-08, QPI-06 |
| **A-HQI-04** | Exploração prévia não pode ser retroativamente apresentada como confirmação independente. | QPI-03, QPI-04 |
| **A-HQI-05** | A evidência utilizada para descobrir um padrão não serve como confirmação independente da descoberta. | QPI-03 |
| **A-HQI-06** | `NO_TRADE` é um resultado decisório legítimo e observável, não ausência de dado. | QPI-09 |
| **A-HQI-07** | Evento de mercado, oportunidade de decisão, decisão, trade e observação estatística não são equivalentes. | QPI-08, QPI-05 |
| **A-HQI-08** | `CandidateModel` e `CandidateStrategy` são entidades conceituais distintas e não intercambiáveis. | QPI-08 |
| **A-HQI-09** | Sucesso quantitativo em pesquisa nunca cria autoridade operacional ou de trading. | QPI-13 |
| **A-HQI-10** | Resultado metodologicamente inválido (ex.: contaminação temporal) não é evidência admissível. | QPI-10 |
| **A-HQI-11** | Avaliação de evidência (*assessment*), avaliação de candidato (*evaluation*) e promoção (*promotion*) são etapas distintas. | QPI-13 |
| **A-HQI-12** | O histórico material de pesquisa, hipóteses descartadas e seleção não pode ser ocultado. | QPI-04, QPI-12 |
| **A-HQI-13** | O processo de seleção entre múltiplos modelos ou estratégias integra formalmente o experimento. | QPI-04 |
| **A-HQI-14** | Toda hipótese histórica deve ser situada em um *information set* causalmente legítimo. | QPI-02 |
| **A-HQI-15** | Status confirmatório não pode ser atribuído a posteriori a estudos exploratórios. | QPI-03, QPI-01 |
| **A-HQI-16** | Reivindicação de mérito econômico exige resultado líquido das fricções materiais aplicáveis. | QPI-06 |

---

## 5. Policy / Experiment Parameters (Decisões Deliberadamente Adiada)

Permanecem abertos e parametrizáveis por experimento:
- Definição do ativo concreto e timeframe;
- Especificação de targets, labels e horizontes de previsão/decisão;
- Lista concreta de features e hiperparâmetros;
- Escolha de arquiteturas de modelos e algoritmos de ML;
- Escolha de comparadores e benchmarks específicos;
- Modelagem numérica exata de custos e fricções;
- Métricas estatísticas específicas e seus thresholds;
- Número de folds, seeds e cenários de robustez.

---

## 6. Gates Internos do Bloco 0E-A

- **0E-A1:** Identidade e falsificabilidade da hipótese documentadas.
- **0E-A2:** Versionamento de hipótese e intenção de pesquisa claros.
- **0E-A3:** Distinção entre Experiment e Run respeitada.
- **0E-A4:** Separação entre evidência exploratória e confirmatória.
- **0E-A5:** Semântica de DecisionOpportunity e `NO_TRADE` preservada.
- **0E-A6:** Separação conceitual entre Model e Strategy.
- **0E-A7:** Coerência integral com ADRs 0001 a 0022 e ausência de claims de autoridade de trading.
