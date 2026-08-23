# Matriz de Rastreabilidade Transversal — HQI ↔ QPI

- **Status:** Consolidado e auditado no Sprint 0E
- **Data:** 2026-08-20
- **Total de Hard Quantitative Invariants (HQIs):** 269
- **Total de Quantitative Protocol Invariants (QPIs):** 15

---

## 1. Visão Geral da Rastreabilidade

Este documento formaliza a rastreabilidade completa entre os **269 Hard Quantitative Invariants (HQIs)** estabelecidos nos protocolos 0E-A a 0E-G e os **15 Invariantes Canônicos Transversais (QPI-01 a QPI-15)** definidos no Bloco 0E-H.

Essa estrutura assegura que:
1. Nenhum HQI aprovado tenha sido eliminado ou tenha sua semântica enfraquecida;
2. Os 15 princípios canônicos sirvam como referência de alto nível para auditorias e revisões arquiteturais;
3. Toda claim científica, preditiva ou econômica possa ser rastreada diretamente até os invariantes metodológicos específicos que a governam.

---

## 2. Resumo da Distribuição: QPI ↔ HQI

| QPI | Descrição Canônica | HQIs Primários | HQIs Secundários | Total HQIs Únicos | Sub-blocos Cobertos |
|---|---|---|---|---|---|
| **QPI-01** | CLAIM STRENGTH ≤ EVIDENCE STRENGTH | 57 | 21 | 78 | 0E-A, 0E-B, 0E-C, 0E-D, 0E-E, 0E-F, 0E-G |
| **QPI-02** | KNOWLEDGE MUST BE CAUSAL | 25 | 2 | 27 | 0E-A, 0E-B, 0E-C, 0E-D |
| **QPI-03** | ADAPTATION CONSUMES INDEPENDENCE | 17 | 7 | 24 | 0E-A, 0E-B, 0E-C, 0E-D, 0E-E, 0E-F, 0E-G |
| **QPI-04** | SEARCH HISTORY IS PART OF THE EVIDENCE | 21 | 10 | 31 | 0E-A, 0E-B, 0E-C, 0E-D, 0E-E, 0E-F, 0E-G |
| **QPI-05** | OBSERVED MARKET ≠ EXECUTABLE MARKET | 15 | 8 | 23 | 0E-A, 0E-B, 0E-D, 0E-E, 0E-F, 0E-G |
| **QPI-06** | ECONOMIC CLAIMS ARE NET AND RISK-AWARE | 27 | 20 | 47 | 0E-A, 0E-C, 0E-D, 0E-E, 0E-F |
| **QPI-07** | NO SINGLE METRIC DEFINES MERIT | 18 | 9 | 27 | 0E-C, 0E-E, 0E-F, 0E-G |
| **QPI-08** | MODEL ≠ STRATEGY ≠ COMPOSED SYSTEM | 22 | 3 | 25 | 0E-A, 0E-B, 0E-C, 0E-D, 0E-F, 0E-G |
| **QPI-09** | NO_TRADE IS A FIRST-CLASS DECISION | 4 | 1 | 5 | 0E-A, 0E-E, 0E-F, 0E-G |
| **QPI-10** | HARD INVALIDITY IS NON-COMPENSATORY | 9 | 14 | 23 | 0E-A, 0E-B, 0E-C, 0E-D, 0E-E, 0E-F, 0E-G |
| **QPI-11** | UNKNOWN MUST REMAIN UNKNOWN | 11 | 11 | 22 | 0E-B, 0E-D, 0E-E, 0E-F, 0E-G |
| **QPI-12** | VERSION AND PROVENANCE ARE IMMUTABLE HISTORICALLY | 17 | 12 | 29 | 0E-A, 0E-B, 0E-C, 0E-D, 0E-E, 0E-F, 0E-G |
| **QPI-13** | EVALUATION ≠ PROMOTION ≠ AUTHORITY | 11 | 10 | 21 | 0E-A, 0E-C, 0E-D, 0E-E, 0E-F, 0E-G |
| **QPI-14** | PAPER IS PROSPECTIVE, NON-FUNDED EVIDENCE | 9 | 12 | 21 | 0E-G |
| **QPI-15** | GATES ARE FAIL-CLOSED AND CONJUNCTIVE | 6 | 8 | 14 | 0E-F, 0E-G |

---

## 3. Matriz Completa de Rastreabilidade (269 HQIs)

### 3.1. Bloco 0E-A — Semântica Experimental e Hipótese Quantitativa (16 HQIs)

| ID | Invariante | QPI Primário | QPI Secundário | ApplicabilityPredicate |
|---|---|---|---|---|
| **A-HQI-01** | Hipótese confirmatória deve ser formalmente falsificável ex ante. | QPI-01 | — | Sempre aplicável a estudos confirmatórios |
| **A-HQI-02** | Hipótese não pode ser redefinida retrospectivamente contra a própria evidência observada. | QPI-04 | QPI-12 | Sempre aplicável |
| **A-HQI-03** | Capacidade preditiva estatística não equivale a valor ou viabilidade econômica. | QPI-08 | QPI-06 | Sempre aplicável |
| **A-HQI-04** | Exploração prévia não pode ser retroativamente apresentada como confirmação independente. | QPI-03 | QPI-04 | Sempre aplicável |
| **A-HQI-05** | A evidência utilizada para descobrir um padrão não serve como confirmação independente da descoberta. | QPI-03 | — | Sempre aplicável |
| **A-HQI-06** | `NO_TRADE` é um resultado decisório legítimo e observável, não ausência de dado. | QPI-09 | — | Sempre aplicável a estratégias |
| **A-HQI-07** | Evento de mercado, oportunidade de decisão, decisão, trade e observação estatística não são equivalentes. | QPI-08 | QPI-05 | Sempre aplicável |
| **A-HQI-08** | `CandidateModel` e `CandidateStrategy` são entidades conceituais distintas e não intercambiáveis. | QPI-08 | — | Sempre aplicável |
| **A-HQI-09** | Sucesso quantitativo em pesquisa nunca cria autoridade operacional ou de trading. | QPI-13 | — | Sempre aplicável |
| **A-HQI-10** | Resultado metodologicamente inválido (ex.: contaminação temporal) é nulo e inadmissível. | QPI-10 | — | Sempre aplicável |
| **A-HQI-11** | Avaliação de evidência (*assessment*), avaliação de candidato (*evaluation*) e promoção (*promotion*) são etapas distintas. | QPI-13 | — | Sempre aplicável |
| **A-HQI-12** | O histórico material de pesquisa, hipóteses descartadas e seleção não pode ser ocultado. | QPI-04 | QPI-12 | Quando houver histórico de busca prévio |
| **A-HQI-13** | O processo de seleção entre múltiplos modelos ou estratégias integra formalmente o experimento. | QPI-04 | — | Quando houver seleção entre alternativas |
| **A-HQI-14** | Toda hipótese histórica deve ser situada em um *information set* causalmente legítimo. | QPI-02 | — | Sempre aplicável |
| **A-HQI-15** | Status confirmatório não pode ser atribuído a posteriori a estudos exploratórios. | QPI-03 | QPI-01 | Sempre aplicável |
| **A-HQI-16** | Reivindicação de mérito econômico exige resultado líquido das fricções materiais aplicáveis. | QPI-06 | — | Quando houver claim econômica |

---

### 3.2. Bloco 0E-B — Dados, RunInputBoundary e Integridade Temporal (29 HQIs)

| ID | Invariante | QPI Primário | QPI Secundário | ApplicabilityPredicate |
|---|---|---|---|---|
| **B-HQI-01** | Dataset nominal declarado não equivale automaticamente ao input efetivo consumido pelo Run. | QPI-01 | QPI-12 | Sempre aplicável |
| **B-HQI-02** | O input declarado no manifesto não substitui a proveniência real de processamento quando material. | QPI-12 | — | Quando material |
| **B-HQI-03** | `event_time` não equivale a `knowledge_time` (tempo de disponibilidade). | QPI-02 | — | Sempre aplicável |
| **B-HQI-04** | `effective_time` não equivale a `knowledge_time`. | QPI-02 | — | Sempre aplicável |
| **B-HQI-05** | Disponibilidade temporal desconhecida (`UNKNOWN`) não pode ser fabricada artificialmente. | QPI-11 | — | Quando availability for desconhecida |
| **B-HQI-06** | A existência de um dado histórico na base hoje não prova sua disponibilidade histórica na data do fato. | QPI-02 | QPI-11 | Sempre aplicável a dados históricos |
| **B-HQI-07** | Informação futura não pode alcançar o input decisório por nenhum caminho direto ou derivacional. | QPI-02 | QPI-10 | Sempre aplicável |
| **B-HQI-08** | Dados e atributos derivados herdam integralmente as restrições temporais de seus dados ancestrais. | QPI-02 | — | Sempre aplicável a pipelines derivados |
| **B-HQI-09** | Informação futura de rótulos/targets não pode contaminar o conjunto de features preditivas. | QPI-02 | QPI-10 | Sempre aplicável a ML supervisionado |
| **B-HQI-10** | Transformações ajustadas (*fitted transforms*) possuem seus próprios knowledge cutoffs e não podem ver o futuro. | QPI-02 | QPI-03 | Quando houver transformações ajustáveis |
| **B-HQI-11** | Intervalo do candle, finalização do candle e disponibilidade para decisão permanecem distintos. | QPI-02 | — | Quando o dado for em formato candle |
| **B-HQI-12** | Dados ausentes, desconhecidos ou não aplicáveis não equivalem a zero (`0.0`). | QPI-11 | — | Quando houver dados faltantes |
| **B-HQI-13** | Imputação de dados é decisão metodológica explícita, não correção neutra de dados. | QPI-04 | QPI-12 | Quando houver imputação |
| **B-HQI-14** | Ausência de registro na base de dados não equivale a ausência observada de negociação no mercado. | QPI-11 | QPI-05 | Quando houver gaps na base |
| **B-HQI-15** | A reconstituição do universo histórico deve prevenir viés de sobrevivência (*survivorship bias*). | QPI-01 | — | Quando o universo for dinâmico |
| **B-HQI-16** | A seleção histórica de instrumentos e regras de rollover deve ser causal e point-in-time. | QPI-02 | — | Quando envolver contratos futuros |
| **B-HQI-17** | Séries sintéticas/contínuas analíticas não constituem preços negociáveis executáveis. | QPI-05 | QPI-08 | Quando usar séries contínuas |
| **B-HQI-18** | Correção posterior de dados históricos não apaga o histórico do que foi conhecido no passado. | QPI-02 | QPI-12 | Quando houver revisões de dados |
| **B-HQI-19** | A identidade do input histórico efetivamente utilizado em um Run é imutável. | QPI-12 | — | Sempre aplicável |
| **B-HQI-20** | Aliases mutáveis (`latest`, `current`) não constituem identidade estável de versão de dataset. | QPI-12 | — | Sempre aplicável |
| **B-HQI-21** | Exclusões e filtros materiais de dados integram obrigatoriamente a proveniência do estudo. | QPI-04 | QPI-12 | Quando houver filtros de admissão |
| **B-HQI-22** | A limpeza e filtragem de dados não podem depender do resultado econômico posterior verificado. | QPI-02 | QPI-04 | Sempre aplicável |
| **B-HQI-23** | Features preditoras e labels de target possuem domínios temporais e de conhecimento distintos. | QPI-02 | — | Sempre aplicável a ML |
| **B-HQI-24** | Cruzamentos e junções temporais (*temporal joins*) devem respeitar a semântica de efetividade e conhecimento. | QPI-02 | — | Quando houver fusão de fontes |
| **B-HQI-25** | Timestamps críticos exigem interpretação temporal não ambígua e fuso horário explícito. | QPI-02 | QPI-11 | Sempre aplicável |
| **B-HQI-26** | Sequência ou ordenação temporal desconhecida não pode ser inventada em benefício do modelo. | QPI-11 | — | Quando a ordem for desconhecida |
| **B-HQI-27** | Entrega duplicada de eventos de mercado não equivale a múltiplos fatos econômicos reais. | QPI-05 | — | Sempre aplicável |
| **B-HQI-28** | Curadoria ou limpeza de dados não elimina a linhagem da evidência bruta original. | QPI-12 | — | Sempre aplicável |
| **B-HQI-29** | A força de qualquer claim experimental não pode exceder a fidelidade e proveniência dos dados consumidos. | QPI-01 | — | Sempre aplicável |

---

### 3.3. Bloco 0E-C — Desenho de Validação, Out-of-Sample e Baselines (32 HQIs)

| ID | Invariante | QPI Primário | QPI Secundário | ApplicabilityPredicate |
|---|---|---|---|---|
| **C-HQI-01** | OOS é uma relação causal e epistemológica relativa ao candidato e sua linhagem de desenvolvimento. | QPI-03 | QPI-01 | Sempre aplicável |
| **C-HQI-02** | Dados utilizados para selecionar entre candidatos integram o conjunto de desenvolvimento (*validation/selection*). | QPI-03 | QPI-04 | Quando houver seleção de candidatos |
| **C-HQI-03** | As funções de ajuste/seleção e julgamento protegido devem ser rigorosamente separáveis. | QPI-03 | QPI-02 | Sempre aplicável a testes confirmatórios |
| **C-HQI-04** | A promoção para etapas prospectivas exige evidência temporalmente protegida e independente. | QPI-01 | QPI-13 | Sempre aplicável a promoções |
| **C-HQI-05** | Evidência consumida por adaptação ou ajuste não continua "não vista" (*unseen*). | QPI-03 | — | Sempre aplicável |
| **C-HQI-06** | Qualquer adaptação material gera um novo sujeito de avaliação com histórico próprio. | QPI-12 | QPI-03 | Quando houver alteração material |
| **C-HQI-07** | A validação confirmatória promocional deve preservar integralmente a causalidade temporal. | QPI-02 | — | Sempre aplicável a séries temporais |
| **C-HQI-08** | Embaralhamento aleatório (*random shuffle*) isolado não substitui validação temporal prospectiva. | QPI-02 | QPI-01 | Sempre aplicável |
| **C-HQI-09** | Cada fold de uma análise walk-forward possui seu próprio *knowledge boundary* estrito. | QPI-02 | — | Quando usar walk-forward |
| **C-HQI-10** | Rótulos com horizontes sobrepostos não podem cruzar partições protegidas sem controle metodológico adequado (purging, embargo, separação equivalente ou outro método justificável). | QPI-02 | QPI-10 | Quando houver overlapping labels |
| **C-HQI-11** | A separação temporal entre treino e teste deve acompanhar a dependência informacional real dos dados. | QPI-02 | — | Sempre aplicável |
| **C-HQI-12** | O ajuste fino de hiperparâmetros (*tuning*) deve ocorrer estritamente dentro do limite de desenvolvimento. | QPI-03 | — | Quando houver tuning |
| **C-HQI-13** | Toda escolha adaptativa material (features, janelas, thresholds) conta como seleção e consome graus de liberdade. | QPI-04 | QPI-03 | Sempre aplicável |
| **C-HQI-14** | Regras de parada antecipada adaptativas (*early stopping*) integram o processo de busca e seleção. | QPI-04 | — | Quando usar early stopping |
| **C-HQI-15** | Regime de mercado descoberto *post-hoc* gera nova hipótese exploratória e não pode justificar falha passada. | QPI-04 | QPI-02 | Quando houver segmentação por regime |
| **C-HQI-16** | O regime de mercado utilizado em tempo de decisão deve ser mensurável de forma puramente causal. | QPI-02 | — | Quando a estratégia consumir regime |
| **C-HQI-17** | A população de dados avaliada no teste deve corresponder ao escopo formal da claim pretendida. | QPI-01 | — | Sempre aplicável |
| **C-HQI-18** | Obter retorno superior a zero não constitui por si só evidência de benchmarking suficiente. | QPI-06 | QPI-07 | Sempre aplicável a claims econômicas |
| **C-HQI-19** | O benchmark de comparação não pode ser selecionado retrospectivamente em função do resultado. | QPI-04 | — | Sempre aplicável |
| **C-HQI-20** | A comparação com baselines e concorrentes exige condições experimentais estritamente comparáveis. | QPI-01 | — | Sempre aplicável |
| **C-HQI-21** | Complexidade arquitetural adicional não confere mérito por si só sem ganho incremental demonstrado. | QPI-01 | QPI-07 | Quando houver alternativas mais simples |
| **C-HQI-22** | O ajuste de modelos de calibração de probabilidades integra o conjunto de desenvolvimento. | QPI-03 | — | Quando calibrar probabilidades |
| **C-HQI-23** | A robustez temporal da estratégia não pode depender do resultado de uma única janela temporal favorável. | QPI-07 | QPI-01 | Sempre aplicável |
| **C-HQI-24** | A agregação de resultados entre múltiplos folds não pode ocultar heterogeneidade ou colapso temporal grave. | QPI-07 | — | Quando usar validação particionada |
| **C-HQI-25** | A validade OOS de um modelo não implica automaticamente a validade OOS da estratégia que o utiliza. | QPI-08 | — | Sempre aplicável a sistemas compostos |
| **C-HQI-26** | A partição protegida de avaliação jamais pode ser utilizada para escolher o candidato vencedor. | QPI-03 | QPI-10 | Sempre aplicável a testes protegidos |
| **C-HQI-27** | O próprio desenho de validação possui linhagem e deve ser registrado ex ante. | QPI-12 | QPI-04 | Sempre aplicável |
| **C-HQI-28** | Evidência OOS/protegida é necessária, mas não suficiente, para sustentar claims promocionais de generalização/viabilidade econômica. | QPI-01 | QPI-06 | Sempre aplicável |
| **C-HQI-29** | O desenho de validação também pode sofrer sobreajuste (*overfit*) se repetidamente modificado. | QPI-03 | QPI-04 | Quando o desenho for alterado |
| **C-HQI-30** | A avaliação protegida exige que todos os hiperparâmetros e regras estejam materialmente fixados ex ante. | QPI-03 | QPI-12 | Sempre aplicável a testes protegidos |
| **C-HQI-31** | Alteração ou reparo material no candidato após a observação do teste protegido exige nova avaliação sob evidência temporalmente protegida e independente. | QPI-03 | QPI-10 | Quando houver correção pós-teste |
| **C-HQI-32** | O escopo de generalização reivindicado não pode exceder o escopo dos dados efetivamente avaliados. | QPI-01 | — | Sempre aplicável |

---

### 3.4. Bloco 0E-D — Backtest e Simulação de Mercado (41 HQIs)

| ID | Invariante | QPI Primário | QPI Secundário | ApplicabilityPredicate |
|---|---|---|---|---|
| **D-HQI-01** | Retorno futuro de um sinal analítico não equivale a backtest de estratégia executável. | QPI-05 | QPI-08 | Sempre aplicável a estudos de sinais |
| **D-HQI-02** | A força probatória de um backtest depende de sua semântica de simulação, não de sua nomenclatura. | QPI-01 | — | Sempre aplicável |
| **D-HQI-03** | O backtest econômico não pode contornar a cadeia de decisão, autorização de risco e execução. | QPI-08 | — | Sempre aplicável a backtests |
| **D-HQI-04** | Ordem rejeitada pelo Risk Engine (`REJECT`) não pode produzir trade simulado ou resultado financeiro. | QPI-08 | QPI-10 | Quando o Risk rejeitar intenções |
| **D-HQI-05** | Desempenho positivo em backtest não demonstra por si só prontidão operacional (*readiness*). | QPI-01 | QPI-13 | Sempre aplicável |
| **D-HQI-06** | A execução simulada de uma ordem não pode preceder a chegada da informação ou o tempo de decisão. | QPI-02 | — | Sempre aplicável |
| **D-HQI-07** | O preço no momento da decisão não é o preço de preenchimento garantido da ordem. | QPI-05 | — | Sempre aplicável |
| **D-HQI-08** | Preço observado em negócios históricos não garante acessibilidade para a estratégia. | QPI-05 | — | Sempre aplicável |
| **D-HQI-09** | Execução no preço médio (*mid-price*) para ordens agressoras exige justificativa explícita. | QPI-05 | QPI-06 | Quando assumir fill no mid |
| **D-HQI-10** | O custo do spread de compra e venda não pode ser ignorado na simulação. | QPI-06 | — | Quando o spread for material |
| **D-HQI-11** | Custos e taxas operacionais materiais devem ser explicitamente deduzidos do P&L. | QPI-06 | — | Sempre aplicável a claims econômicas |
| **D-HQI-12** | Tabelas de taxas e emolumentos devem respeitar a vigência histórica do período simulado. | QPI-02 | QPI-06 | Sempre aplicável |
| **D-HQI-13** | A fidelidade na modelagem de latência deve ser proporcional à sensibilidade temporal da estratégia. | QPI-06 | — | Quando a estratégia for sensível a latência |
| **D-HQI-14** | Latência assumida em simulação não equivale a latência real observada em ambiente de produção. | QPI-05 | QPI-11 | Sempre aplicável |
| **D-HQI-15** | O modelo de slippage utilizado deve ser compatível com a força da claim econômica pretendida. | QPI-06 | QPI-01 | Sempre aplicável |
| **D-HQI-16** | Incerteza na execução e no preenchimento não pode adotar por padrão o cenário mais favorável. | QPI-11 | QPI-06 | Quando houver incerteza de fill |
| **D-HQI-17** | Volume total negociado no mercado não representa liquidez acessível para a nossa ordem. | QPI-05 | — | Sempre aplicável |
| **D-HQI-18** | A liquidez disponível depende do lado do book, do estado de mercado e do momento temporal. | QPI-05 | — | Quando a ordem consumir liquidez |
| **D-HQI-19** | A performance de uma estratégia não escala linearmente com o tamanho do lote por presunção. | QPI-06 | — | Quando avaliar capacidade de lote |
| **D-HQI-20** | Impacto de mercado nulo é uma premissa de modelagem e não um fato universal. | QPI-06 | QPI-05 | Quando lotes forem materiais |
| **D-HQI-21** | Não preenchimento de ordem (*no-fill*) é um resultado legítimo e esperado da simulação. | QPI-05 | — | Quando usar ordens passivas ou limitadas |
| **D-HQI-22** | O risco de preenchimento parcial (*partial fill*) não pode ser convertido em preenchimento total artificial. | QPI-05 | QPI-11 | Quando a liquidez for limitada |
| **D-HQI-23** | O toque no preço limite (*price touch*) não garante o preenchimento de ordens passivas. | QPI-05 | — | Quando usar ordens passivas |
| **D-HQI-24** | Trajetória intrabar materialmente desconhecida deve permanecer desconhecida e receber tratamento explícito que não favoreça sistematicamente a Strategy. | QPI-11 | — | Quando usar dados em barras OHLC |
| **D-HQI-25** | As categorias `UNKNOWN`, pior caso e caso esperado permanecem semanticamente distintas. | QPI-11 | — | Sempre aplicável |
| **D-HQI-26** | A simulação de mercado deve avançar estritamente de forma causal com o relógio do simulador. | QPI-02 | — | Sempre aplicável |
| **D-HQI-27** | Estados do ciclo de vida de ordens materialmente relevantes à Strategy ou à claim de execução devem ser representados. | QPI-05 | — | Quando a estratégia depender de lifecycle |
| **D-HQI-28** | Reivindicações de execução precisa não podem exceder a resolução e granularidade dos dados. | QPI-01 | QPI-05 | Sempre aplicável |
| **D-HQI-29** | A fidelidade da simulação de mercado é multidimensional (tempo, preço, spread, latência, custos). | QPI-01 | — | Sempre aplicável |
| **D-HQI-30** | Todas as premissas e modelos de simulação integram obrigatoriamente a proveniência do Run. | QPI-12 | — | Sempre aplicável |
| **D-HQI-31** | Simulação estocástica exige rastreabilidade completa de geradores e sementes aleatórias (*seeds*). | QPI-12 | — | Quando a simulação for estocástica |
| **D-HQI-32** | Calibração retrospectiva de modelos de execução com base no resultado deve ser declarada como tal. | QPI-03 | QPI-04 | Quando calibrar simulação ex post |
| **D-HQI-33** | Sinais, decisões ou intenções de ordem não geram P&L diretamente sem preenchimento simulado. | QPI-08 | QPI-05 | Sempre aplicável |
| **D-HQI-34** | O término arbitrário da janela de teste não cria liquidação forçada de posições sem regra de mercado. | QPI-05 | — | Sempre aplicável |
| **D-HQI-35** | A fronteira de uma partição ou fold de dados não constitui evento de negociação real no mercado. | QPI-02 | — | Sempre aplicável |
| **D-HQI-36** | A incerteza da simulação de execução não pode ser convertida em certeza matemática artificial. | QPI-11 | — | Sempre aplicável |
| **D-HQI-37** | Estado de mercado desatualizado (*stale*) ou incompleto impede a presunção de execução normal. | QPI-05 | QPI-11 | Quando o book estiver desatualizado |
| **D-HQI-38** | As premissas de execução não podem favorecer o candidato em relação ao comparador ou benchmark. | QPI-01 | QPI-04 | Sempre aplicável |
| **D-HQI-39** | A seleção retrospectiva de modelos de custo mais favoráveis (*assumption shopping*) integra a busca. | QPI-04 | — | Quando testar múltiplos modelos de custo |
| **D-HQI-40** | Premissas materiais de execução devem ser perturbáveis para análise de sensibilidade, integrando a robustez quando pertinente à claim. | QPI-06 | QPI-01 | Quando houver incerteza de parâmetros |
| **D-HQI-41** | A omissão de qualquer fricção de mercado exige justificativa de imaterialidade ou limitação explícita. | QPI-06 | — | Quando omitir custos específicos |

---

### 3.5. Bloco 0E-E — Validação Estatística e Econômica (55 HQIs)

| ID | Invariante | QPI Primário | QPI Secundário | ApplicabilityPredicate |
|---|---|---|---|---|
| **E-HQI-01** | Significância estatística, relevância econômica e mérito para promoção são conclusões distintas. | QPI-01 | QPI-06, QPI-13 | Sempre aplicável |
| **E-HQI-02** | Toda métrica calculada deve responder a um estimand e população formalmente definidos. | QPI-01 | — | Sempre aplicável |
| **E-HQI-03** | Métricas econômicas exigem unidade, denominador e moeda explicitamente declarados. | QPI-06 | — | Sempre aplicável a métricas financeiras |
| **E-HQI-04** | O tamanho amostral nominal (\(N\)) não equivale à quantidade de informação estatística independente. | QPI-01 | — | Sempre aplicável |
| **E-HQI-05** | Dependência temporal material e autocorrelação devem ser incorporadas na quantificação de incerteza. | QPI-01 | QPI-06 | Quando houver autocorrelação serial |
| **E-HQI-06** | A sobreposição de janelas de retorno reduz a informação efetiva mesmo na ausência de leakage. | QPI-01 | — | Quando houver horizontes sobrepostos |
| **E-HQI-07** | Estimativa pontual isolada é insuficiente para sustentar claims estatísticas ou econômicas fortes. | QPI-01 | QPI-06 | Sempre aplicável a claims confirmatórias |
| **E-HQI-08** | A interpretação verbal da incerteza deve corresponder rigorosamente ao método estatístico utilizado. | QPI-01 | — | Sempre aplicável |
| **E-HQI-09** | A distribuição normal de retornos não pode ser assumida por conveniência analítica. | QPI-01 | QPI-06 | Quando retornos exibirem caudas pesadas |
| **E-HQI-10** | A média de retornos não caracteriza por si só toda a estrutura e risco da distribuição. | QPI-07 | QPI-06 | Sempre aplicável |
| **E-HQI-11** | Nenhuma métrica única isolada representa a qualidade total de uma estratégia. | QPI-07 | — | Sempre aplicável |
| **E-HQI-12** | A taxa de acerto (*hit rate*) não possui primazia econômica independente sobre o resultado líquido. | QPI-07 | QPI-06 | Sempre aplicável |
| **E-HQI-13** | O cálculo de expectativa matemática (*expectancy*) exige definição clara da variável e população base. | QPI-06 | — | Quando reportar expectancy |
| **E-HQI-14** | O fator de lucro (*profit factor*) exige análise da distribuição para prevenir distorção por outliers. | QPI-07 | QPI-06 | Quando reportar profit factor |
| **E-HQI-15** | O índice de Sharpe exige especificação completa de taxa livre de risco, frequência e autocorrelação. | QPI-07 | QPI-01 | Quando reportar Sharpe |
| **E-HQI-16** | Fórmulas de anualização de volatilidade e retornos não criam informação empírica nova. | QPI-01 | — | Quando anualizar métricas |
| **E-HQI-17** | Métricas dependentes de trajetória (*path-dependent*) exigem contexto temporal e histórico. | QPI-06 | QPI-07 | Sempre aplicável |
| **E-HQI-18** | O drawdown máximo isolado é insuficiente para caracterizar a severidade e duração de perdas. | QPI-07 | QPI-06 | Quando avaliar risco de drawdown |
| **E-HQI-19** | Métricas de quantil simples (ex.: VaR) não caracterizam sozinhas a severidade da cauda extrema. | QPI-06 | QPI-07 | Quando avaliar caudas |
| **E-HQI-20** | Métricas de cauda não podem aparentar precisão estatística superior aos dados disponíveis na cauda. | QPI-01 | QPI-11 | Sempre aplicável a estimativas de cauda |
| **E-HQI-21** | O cálculo de probabilidade de perda exige definição estrita do evento de perda e do horizonte. | QPI-06 | — | Quando reportar probabilidade de perda |
| **E-HQI-22** | A probabilidade de ruína é condicional às políticas de dimensionamento, capital e alavancagem. | QPI-06 | — | Quando avaliar ruína |
| **E-HQI-23** | Métricas econômicas promocionais devem refletir as fricções materiais aplicáveis à claim e à forma de execução avaliada. | QPI-06 | — | Sempre aplicável a promoções |
| **E-HQI-24** | A detecção de um efeito estatístico não nulo não equivale a um efeito economicamente material. | QPI-06 | QPI-01 | Sempre aplicável |
| **E-HQI-25** | Claim de superioridade ou valor incremental exige evidência controlada contra comparadores. | QPI-01 | QPI-04 | Quando reivindicar superioridade |
| **E-HQI-26** | A agregação de resultados entre folds e janelas temporais exige semântica explícita de ponderação. | QPI-01 | — | Quando agregar folds |
| **E-HQI-27** | A agregação de métricas não pode ocultar colapsos ou heterogeneidades temporais materiais. | QPI-07 | — | Sempre aplicável |
| **E-HQI-28** | Robustez metodológica não significa invariância numérica estrita diante de perturbações. | QPI-01 | — | Sempre aplicável |
| **E-HQI-29** | Quedas abruptas de desempenho em parâmetros vizinhos (*parameter cliffs*) indicam fragilidade. | QPI-01 | QPI-06 | Quando houver sensibilidade paramétrica |
| **E-HQI-30** | A sensibilidade do resultado a variações adversas de custos deve permanecer explicitamente visível. | QPI-06 | — | Sempre aplicável |
| **E-HQI-31** | A concentração de retornos em regimes específicos deve coincidir com o escopo formal da claim. | QPI-01 | — | Quando houver dependência de regime |
| **E-HQI-32** | A multiplicidade do processo de busca e seleção altera a interpretação da significância do vencedor. | QPI-04 | QPI-03 | Quando houver busca ampla |
| **E-HQI-33** | O viés de *data snooping* afeta a validade inferencial mesmo na ausência de testes de hipótese formais. | QPI-04 | — | Sempre aplicável |
| **E-HQI-34** | A família material de hipóteses e modelos testados durante a pesquisa deve permanecer identificável. | QPI-04 | QPI-12 | Sempre aplicável |
| **E-HQI-35** | O valor-p (*p-value*) não constitui um score direto de qualidade ou autorização de promoção. | QPI-07 | QPI-01 | Quando reportar p-values |
| **E-HQI-36** | Precisão estatística insuficiente em relação à claim gera desfecho `INCONCLUSIVE`, não aprovação. | QPI-11 | QPI-01 | Quando a incerteza for ampla |
| **E-HQI-37** | Resultados negativos e hipóteses rejeitadas no mesmo programa de pesquisa integram a linhagem. | QPI-04 | QPI-12 | Quando houver tentativas prévias |
| **E-HQI-38** | Cenários de teste de robustez não podem ser selecionados retrospectivamente por conveniência. | QPI-04 | QPI-01 | Sempre aplicável a testes de estresse |
| **E-HQI-39** | Cenários de estresse constituem testes de vulnerabilidade estrutural e não previsões probabilísticas. | QPI-06 | — | Quando realizar estresse |
| **E-HQI-40** | Eventos reais de cauda extrema observados nos dados não podem ser descartados como outliers para inflar métricas. | QPI-06 | QPI-10 | Sempre aplicável |
| **E-HQI-41** | Índices ajustados ao risco (*risk-adjusted ratios*) não substituem a análise de perdas em valores absolutos. | QPI-06 | QPI-07 | Sempre aplicável |
| **E-HQI-42** | O cálculo de métricas agregadas não pode apagar a taxa de seletividade e decisões `NO_TRADE`. | QPI-09 | QPI-07 | Sempre aplicável a estratégias |
| **E-HQI-43** | A interpretação do desempenho financeiro pode exigir contextualização da exposição e capital alocado. | QPI-06 | — | Quando avaliar retorno sobre capital |
| **E-HQI-44** | Incerteza e limitações do modelo de simulação de execução não podem ser ocultadas por precisão estatística. | QPI-01 | QPI-05 | Sempre aplicável |
| **E-HQI-45** | A escolha da melhor semente aleatória (*best seed*) em simulações estocásticas constitui seleção e viés. | QPI-04 | QPI-03 | Quando houver variação estocástica |
| **E-HQI-46** | Determinismo computacional de um backtest não equivale a certeza empírica de generalização futura. | QPI-01 | — | Sempre aplicável |
| **E-HQI-47** | Complexidade arquitetural adicional exige demonstração de ganho incremental estatístico e econômico. | QPI-01 | QPI-07 | Quando houver alternativas simples |
| **E-HQI-48** | A troca oportunista da métrica de avaliação em função do resultado (*metric shopping*) constitui seleção enviesada. | QPI-04 | QPI-07 | Sempre aplicável |
| **E-HQI-49** | Ser o melhor candidato dentro de um espaço de busca massivo não prova viabilidade absoluta fora da amostra. | QPI-04 | QPI-01 | Sempre aplicável |
| **E-HQI-50** | O teste de robustez deve ser genuinamente capaz de falsificar a hipótese sob condições adversas. | QPI-01 | — | Sempre aplicável |
| **E-HQI-51** | Cenários de estresse devem manter consistência econômica e estrutural interna entre as variáveis. | QPI-06 | — | Quando desenhar cenários de estresse |
| **E-HQI-52** | Métricas conflitantes no vetor de avaliação exigem síntese e julgamento explícitos, sem pesos arbitrários. | QPI-07 | — | Sempre aplicável |
| **E-HQI-53** | O veredito `INCONCLUSIVE` é uma disposição científica legítima diante de evidência ambígua. | QPI-11 | QPI-01 | Sempre aplicável |
| **E-HQI-54** | Sofisticação estatística ou técnicas avançadas de bootstrap não corrigem invalidade metodológica prévia. | QPI-10 | QPI-01 | Sempre aplicável |
| **E-HQI-55** | A força inferencial final não pode superar a fraqueza de etapas upstream de integridade ou simulação. | QPI-01 | QPI-10 | Sempre aplicável |

---

### 3.6. Bloco 0E-F — Avaliação de Modelos e Estratégias (46 HQIs)

| ID | Invariante | QPI Primário | QPI Secundário | ApplicabilityPredicate |
|---|---|---|---|---|
| **F-HQI-01** | O mérito de um modelo preditivo não equivale ao mérito da estratégia que o consome. | QPI-08 | — | Sempre aplicável |
| **F-HQI-02** | O ranking preditivo entre modelos não corresponde necessariamente ao ranking econômico das estratégias. | QPI-08 | QPI-06 | Quando comparar múltiplos modelos |
| **F-HQI-03** | O escopo de avaliação (*EvaluationScope*) deve ser explicitamente declarado. | QPI-08 | QPI-01 | Sempre aplicável |
| **F-HQI-04** | Ações de controle ou veto do Risk Engine não são creditadas como mérito da estratégia. | QPI-08 | — | Quando houver atuação do Risk |
| **F-HQI-05** | A atribuição de falha de desempenho a um componente específico exige evidência demonstrável. | QPI-01 | QPI-11 | Quando diagnosticar falhas |
| **F-HQI-06** | A métrica do modelo deve ser compatível com a natureza e o estimand de sua saída. | QPI-01 | — | Sempre aplicável a modelos |
| **F-HQI-07** | A taxa de acerto isolada não define a utilidade econômica de um modelo para a estratégia. | QPI-07 | QPI-06 | Sempre aplicável |
| **F-HQI-08** | Capacidade de discriminação e calibração de probabilidades são dimensões distintas de avaliação. | QPI-07 | — | Quando usar modelos probabilísticos |
| **F-HQI-09** | A utilidade prática de um modelo é estritamente dependente da política de decisão da estratégia. | QPI-08 | — | Sempre aplicável |
| **F-HQI-10** | A reivindicação de contribuição de um modelo exige evidência incremental controlada contra baselines. | QPI-01 | QPI-04 | Quando reivindicar ganho por modelo |
| **F-HQI-11** | O crédito atribuído a uma feature ou submodelo exige demonstração de contribuição separável. | QPI-01 | — | Quando usar ablação |
| **F-HQI-12** | Complexidade algorítmica adicional exige demonstração de valor econômico incremental. | QPI-01 | QPI-07 | Quando houver modelos complexos |
| **F-HQI-13** | A proporção e o momento de decisões `NO_TRADE` integram a avaliação da estratégia. | QPI-09 | — | Sempre aplicável |
| **F-HQI-14** | Falsos positivos e falsos negativos possuem custos assimétricos determinados pela estratégia. | QPI-06 | QPI-08 | Sempre aplicável |
| **F-HQI-15** | O threshold de decisão operacional não é uma propriedade matemática intrínseca do modelo. | QPI-08 | — | Sempre aplicável |
| **F-HQI-16** | O ranking entre candidatos pode sofrer inversão em função da composição com o sistema de execução. | QPI-08 | — | Quando avaliar sistemas compostos |
| **F-HQI-17** | Desempenho global positivo não pode mascarar falhas graves em regimes operacionais materiais. | QPI-07 | — | Sempre aplicável |
| **F-HQI-18** | A robustez estatística de um modelo não garante a robustez econômica da estratégia. | QPI-08 | QPI-06 | Sempre aplicável |
| **F-HQI-19** | A avaliação de uma estratégia é estritamente específica à sua versão imutável e parâmetros testados. | QPI-12 | — | Sempre aplicável |
| **F-HQI-20** | A materialidade de uma alteração no código ou configuração é definida por seu impacto no comportamento. | QPI-12 | — | Quando houver alterações |
| **F-HQI-21** | A comparação e o ranking entre modelos concorrentes devem considerar a incerteza estatística. | QPI-01 | — | Quando ranquear modelos |
| **F-HQI-22** | A reivindicação de mérito incremental de uma estratégia exige comparação com benchmarks controlados. | QPI-01 | QPI-04 | Sempre aplicável |
| **F-HQI-23** | Um modelo com avaliação favorável pode coexistir legitimamente com uma estratégia desfavorável. | QPI-08 | QPI-06 | Sempre aplicável |
| **F-HQI-24** | A avaliação holística de candidatos não exige nem autoriza a criação de scores compensatórios universais. | QPI-07 | QPI-10 | Sempre aplicável |
| **F-HQI-25** | A conformidade com regras metodológicas é requisito de admissibilidade e não crédito de desempenho. | QPI-10 | QPI-01 | Sempre aplicável |
| **F-HQI-26** | A constatação de invalidade metodológica por violação de invariante rígido é não compensatória. | QPI-10 | — | Sempre aplicável |
| **F-HQI-27** | Lacunas materiais de evidência delimitam o alcance das conclusões da avaliação. | QPI-01 | QPI-11 | Quando houver dados incompletos |
| **F-HQI-28** | O status de componente não avaliado (`NOT_EVALUATED`) não equivale a componente aceitável. | QPI-11 | — | Sempre aplicável |
| **F-HQI-29** | As diferentes dimensões do vetor de avaliação não podem ser agregadas por votação simples de maioria. | QPI-07 | QPI-10 | Sempre aplicável |
| **F-HQI-30** | Risco de cauda ou perdas extremas inaceitáveis dominam e anulam métricas de retorno positivo. | QPI-06 | QPI-10 | Sempre aplicável |
| **F-HQI-31** | A existência do Risk Engine não dispensa a estratégia de possuir avaliação de risco prudente. | QPI-08 | QPI-06 | Sempre aplicável |
| **F-HQI-32** | Comparações entre Strategies devem controlar ou explicitar diferenças materiais de policies downstream capazes de determinar o resultado. | QPI-01 | — | Quando comparar estratégias |
| **F-HQI-33** | Degradação estatística do modelo (*model drift*) e perda de edge da estratégia (*decay*) são fenômenos distintos. | QPI-08 | — | Sempre aplicável |
| **F-HQI-34** | Queda pontual no retorno não implica necessariamente perda estrutural do edge se a frequência de oportunidades mudou. | QPI-01 | QPI-09 | Quando analisar quebras de regime |
| **F-HQI-35** | A avaliação do candidato preserva integralmente o histórico de busca e a multiplicidade explorada. | QPI-04 | — | Sempre aplicável |
| **F-HQI-36** | A sensibilidade a variações no modelo de execução integra a qualidade intrínseca da estratégia. | QPI-06 | QPI-05 | Sempre aplicável |
| **F-HQI-37** | Retornos financeiros similares não implicam equivalência de qualidade e risco entre estratégias. | QPI-07 | QPI-06 | Sempre aplicável |
| **F-HQI-38** | As conclusões da avaliação não podem extrapolar os limites da claim formalmente testada. | QPI-01 | — | Sempre aplicável |
| **F-HQI-39** | O protocolo admite conclusões condicionais ou limitadas a regimes de mercado específicos. | QPI-01 | — | Quando a validade for condicional |
| **F-HQI-40** | A constatação de resultado desfavorável na avaliação não autoriza o ajuste automático de parâmetros no mesmo teste. | QPI-03 | QPI-10 | Sempre aplicável |
| **F-HQI-41** | Avaliação técnica favorável da estratégia não constitui autorização para início de Paper Trading. | QPI-13 | — | Sempre aplicável |
| **F-HQI-42** | Scores e rankings de pesquisa auxiliam a priorização mas não substituem os gates normativos de promoção. | QPI-13 | QPI-15 | Sempre aplicável |
| **F-HQI-43** | A atribuição comparativa de superioridade a um componente exige que diferenças materiais capazes de explicar o resultado estejam suficientemente controladas ou explicitamente reconhecidas. | QPI-01 | — | Quando realizar comparações |
| **F-HQI-44** | A documentação técnica do modelo (*Model Card*) não substitui a validação econômica da estratégia. | QPI-08 | — | Sempre aplicável |
| **F-HQI-45** | O uso de Machine Learning não é obrigatório nem confere privilégio metodológico sobre regras determinísticas. | QPI-01 | — | Sempre aplicável |
| **F-HQI-46** | Limitações metodológicas identificadas integram obrigatoriamente a conclusão formal da avaliação. | QPI-01 | QPI-11 | Sempre aplicável |

---

### 3.7. Bloco 0E-G — Promoção, Paper Trading e Rejeição (50 HQIs)

| ID | Invariante | QPI Primário | QPI Secundário | ApplicabilityPredicate |
|---|---|---|---|---|
| **G-HQI-01** | Promoção quantitativa entre etapas de pesquisa nunca cria autoridade operacional ou econômica de trading. | QPI-13 | — | Sempre aplicável |
| **G-HQI-02** | Avaliação técnica favorável da estratégia não promove o candidato automaticamente. | QPI-13 | QPI-15 | Sempre aplicável |
| **G-HQI-03** | Todo status de aprovação deve identificar explicitamente o gate normativo específico ao qual se refere. | QPI-13 | QPI-15 | Sempre aplicável |
| **G-HQI-04** | As disposições `INVALID`, `REJECTED` e `INCONCLUSIVE` permanecem conceitualmente distintas. | QPI-10 | QPI-11 | Sempre aplicável |
| **G-HQI-05** | Evidência metodologicamente inválida não pode sustentar nenhuma decisão de promoção. | QPI-10 | QPI-01 | Sempre aplicável |
| **G-HQI-06** | Valor explicativo para pesquisa científica (*RESEARCH_ONLY*) não equivale a elegibilidade para promoção. | QPI-01 | QPI-13 | Sempre aplicável |
| **G-HQI-07** | A elegibilidade para Paper Trading exige atendimento cumulativo de todas as classes materiais obrigatórias. | QPI-15 | QPI-01 | Sempre aplicável a Paper |
| **G-HQI-08** | Bloqueadores rígidos de promoção (*hard blockers*) são estritamente não compensatórios. | QPI-10 | QPI-15 | Sempre aplicável |
| **G-HQI-09** | O status de promoção é específico à versão/configuração avaliada e não se transfere automaticamente para versões materialmente modificadas. | QPI-12 | — | Sempre aplicável |
| **G-HQI-10** | O Paper confirmatório exige que o candidato e o desenho materialmente relevantes estejam pré-resolvidos e versionados antes da observação dos resultados. | QPI-12 | QPI-03 | Sempre aplicável a Paper |
| **G-HQI-11** | Qualquer alteração material durante o período de Paper Trading cria uma nova fronteira de evidência. | QPI-12 | QPI-03 | Quando houver alteração em Paper |
| **G-HQI-12** | O Paper Trading opera com decisões prospectivas reais do sistema sem risco de capital real (*non-funded*). | QPI-14 | — | Sempre aplicável a Paper |
| **G-HQI-13** | O Paper Trading deve executar a estratégia candidata exata, sendo proibido o uso de substitutas favoráveis. | QPI-14 | QPI-12 | Sempre aplicável a Paper |
| **G-HQI-14** | A validade empírica de Paper Trading é restrita ao que o ambiente é capaz de observar contemporaneamente. | QPI-14 | QPI-01 | Sempre aplicável a Paper |
| **G-HQI-15** | A execução em Paper Trading não equivale por presunção à execução em ambiente de produção real (*Live*). | QPI-14 | QPI-05 | Sempre aplicável |
| **G-HQI-16** | A compatibilidade entre Backtest e Paper Trading é de natureza estrutural e distribucional. | QPI-01 | QPI-14 | Sempre aplicável a Paper |
| **G-HQI-17** | Discrepâncias materiais observadas em Paper Trading permanecem registradas como evidência empírica. | QPI-14 | QPI-12 | Quando houver discrepâncias |
| **G-HQI-18** | A adaptação ou ajuste da estratégia motivada por dados de Paper Trading consome a independência desses dados. | QPI-03 | QPI-14 | Quando alterar estratégia após Paper |
| **G-HQI-19** | A suficiência de Paper Trading não é definida unicamente por dias de calendário, mas por volume informacional. | QPI-01 | QPI-14 | Sempre aplicável a Paper |
| **G-HQI-20** | O Paper Trading avalia todas as decisões geradas, inclusive a taxa e oportunidade de decisões `NO_TRADE`. | QPI-09 | QPI-14 | Sempre aplicável a Paper |
| **G-HQI-21** | A ocorrência de erro crítico não resolvido durante o Paper Trading bloqueia a progressão do candidato. | QPI-10 | QPI-15 | Quando ocorrer erro crítico |
| **G-HQI-22** | O impacto de falhas e erros operacionais deve ser avaliado no escopo específico em que ocorreram. | QPI-01 | — | Quando houver falhas operacionais |
| **G-HQI-23** | Estabilidade operacional em Paper Trading não equivale a prontidão operacional (*readiness*) para Live. | QPI-14 | QPI-13 | Sempre aplicável |
| **G-HQI-24** | O Paper Trading não pode contornar ou desabilitar verificações de risco para inflar o volume de trades. | QPI-08 | QPI-14 | Sempre aplicável a Paper |
| **G-HQI-25** | Análises contrafactuais em Paper Trading são ferramentas exploratórias e não substituem o comportamento canônico. | QPI-14 | QPI-01 | Quando usar contrafactuais |
| **G-HQI-26** | Toda decisão de promoção deve registrar sua proveniência, evidências e responsáveis de forma auditável. | QPI-12 | QPI-13 | Sempre aplicável a decisões de promoção |
| **G-HQI-27** | As políticas e regras de aprovação de gates possuem identidade de versão e vigência temporal. | QPI-12 | QPI-15 | Sempre aplicável |
| **G-HQI-28** | O status de elegibilidade de um candidato não é perpétuo e deve poder ser revalidado ou revogado quando versão, premissas, domínio, políticas ou outras condições materiais mudarem. | QPI-13 | — | Sempre aplicável |
| **G-HQI-29** | Novas evidências materiais desfavoráveis podem suspender ou revogar o status de elegibilidade. | QPI-13 | QPI-15 | Quando surgirem novos dados |
| **G-HQI-30** | A rejeição formal de um candidato não apaga seu histórico de desenvolvimento e linhagem de pesquisa. | QPI-04 | QPI-12 | Quando houver rejeição |
| **G-HQI-31** | Falhas repetidas de candidatos de uma mesma família permanecem registradas para controle de multiplicidade. | QPI-04 | — | Sempre aplicável |
| **G-HQI-32** | A operação em ambiente real (*Live*) exige a superação formal de todas as classes de bloqueadores aplicáveis. | QPI-15 | QPI-13 | Sempre aplicável a Live |
| **G-HQI-33** | Os gates de evolução do sistema são independentes e estritamente conjuntivos. | QPI-15 | — | Sempre aplicável |
| **G-HQI-34** | O Paper Trading deve confrontar os resultados observados contra as expectativas ex ante do backtest. | QPI-14 | QPI-01 | Sempre aplicável a Paper |
| **G-HQI-35** | Mudança estrutural no regime de mercado (*domain shift*) pode limitar a validade da evidência de Paper. | QPI-01 | QPI-14 | Quando houver quebra de regime |
| **G-HQI-36** | Regras de interrupção (*stopping rules*) de Paper Trading devem ser pré-especificadas no desenho do teste. | QPI-14 | — | Sempre aplicável a Paper |
| **G-HQI-37** | A interrupção de Paper Trading por motivos de segurança operacional prevalece sobre a suficiência amostral. | QPI-15 | QPI-14 | Quando houver risco operacional |
| **G-HQI-38** | Resultado financeiro positivo em Paper Trading, isoladamente, não é suficiente para satisfazer o Paper Gate. | QPI-07 | QPI-14 | Sempre aplicável a Paper |
| **G-HQI-39** | O Paper Trading gera novos artefatos de evidência de forma append-only, sem reescrever o histórico. | QPI-12 | QPI-14 | Sempre aplicável |
| **G-HQI-40** | O diagnóstico de falha em Paper Trading exige demonstração empírica baseada em dados e logs. | QPI-01 | QPI-14 | Quando houver falha em Paper |
| **G-HQI-41** | Candidato materialmente modificado em resposta a uma falha de Paper deve retornar aos gates quantitativos aplicáveis à mudança antes de reivindicar nova progressão. | QPI-03 | QPI-10 | Quando modificar estratégia |
| **G-HQI-42** | A aprovação humana em comitê não tem poder para validar evidência quantitativamente contaminada. | QPI-10 | QPI-13 | Sempre aplicável |
| **G-HQI-43** | Suposta urgência comercial ou de mercado não autoriza o bypass ou flexibilização de gates normativos. | QPI-15 | QPI-10 | Sempre aplicável |
| **G-HQI-44** | O estado de promoção é plenamente revogável a qualquer momento diante de novas evidências. | QPI-13 | QPI-15 | Sempre aplicável |
| **G-HQI-45** | Estar elegível para uma etapa não equivale a ter iniciado ou concluído a referida etapa. | QPI-13 | QPI-11 | Sempre aplicável |
| **G-HQI-46** | O sucesso na execução operacional de Paper Trading não comprova o mérito quantitativo da estratégia. | QPI-08 | QPI-14 | Sempre aplicável a Paper |
| **G-HQI-47** | A observação de baixo risco em Paper Trading não substitui a necessidade dos controles do Risk Engine. | QPI-08 | QPI-14 | Sempre aplicável a Paper |
| **G-HQI-48** | Gates posteriores adicionam requisitos de segurança e não atenuam exigências não cumpridas em gates prévios. | QPI-15 | — | Sempre aplicável |
| **G-HQI-49** | Candidatos derivados de uma estratégia herdam sua linhagem de pesquisa, mas não seu status de promoção. | QPI-12 | QPI-13 | Quando derivar novas versões |
| **G-HQI-50** | O escopo de promoção não pode exceder as configurações, instrumentos e condições efetivamente testadas. | QPI-01 | QPI-13 | Sempre aplicável a promoções |
