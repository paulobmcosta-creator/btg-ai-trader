# Protocolo 0E-D — Backtest e Simulação de Mercado

- **Status:** Fechado tecnicamente no Sprint 0E
- **Data da baseline:** 2026-08-20
- **Consome:** ADR-0004, ADR-0005, ADR-0006, ADR-0007, ADR-0008, ADR-0014, ADR-0016, ADR-0017, ADR-0021, ADR-0022
- **Subordinado a:** QPI-01, QPI-02, QPI-05, QPI-06, QPI-08, QPI-09, QPI-10, QPI-11, QPI-12, QPI-13

---

## 1. Finalidade e Escopo

O Protocolo 0E-D estabelece as regras e invariantes para simular o comportamento de uma estratégia de negociação sob condições economicamente realistas e com fidelidade histórica de execução, respondendo à pergunta:
> *Dado que sabemos o que poderia ser legitimamente conhecido no tempo da decisão, o que a estratégia poderia economicamente ter executado sob uma representação honesta e limitada da realidade de mercado?*

Princípio orientador fundamental:
```text
“o mercado atingiu determinado preço”
≠ “o preço estava acessível para nossa ordem”
≠ “a ordem chegou ao book a tempo”
≠ “havia liquidez suficiente naquele nível”
≠ “a ordem foi preenchida”
≠ “todo o lote foi preenchido”
≠ “o resultado financeiro líquido foi aquele”
```

---

## 2. As Três Classes de Estudo Simulado

1. **Analytical / Signal Study:** Estudo puramente estatístico da relação entre sinal informacional e retornos futuros teóricos. Não constitui backtest de estratégia.
2. **Decision-Policy Simulation:** Simulação das decisões geradas pela estratégia (`NO_TRADE` vs `PROPOSE_TRADE`) e eventuais vetos de risco, sem modelagem profunda de livro e execução.
3. **Execution-Aware Economic Backtest:** Simulação completa que preserva a cadeia arquitetural do sistema:
   ```text
   Market Events
   → Signal Engine
   → StrategyDecision
   → TradeIntent
   → RiskDecision (REJECT | PERMIT)
   → RiskAuthorization & Allocation
   → OrderIntent & OrderPlan
   → ExecutionOrder
   → Simulated Execution
   → Simulated Fills
   → Simulated Ledger & Position Projections
   ```

> **Regra fundamental:** O perfil `BACKTEST` reutiliza o mesmo núcleo de domínio que `PAPER` e `LIVE`, variando adaptadores de mercado e relógio. Não é permitido criar atalhos de domínio no backtest que contornem o Risk Engine ou o Order Planning.

---

## 3. Causalidade Temporal na Execução e Preços

### 3.1. Linha do Tempo da Simulação de Execução
A execução deve respeitar a ordem causal dos eventos:
```text
Information Available Time
→ Decision Time (término do cálculo da estratégia)
→ Order Ready Time (autorização de risco e planejamento)
→ Simulated Market Arrival Time (latência de rede e gateway)
→ Execution Opportunity Time (interação com o book/mercado)
→ Fill Time / Partial Fill / No Fill
```

### 3.2. Preço de Decisão versus Preço de Execução
- Não se pode assumir execução no mesmo preço de fechamento usado para formar a decisão. Qualquer claim excepcional de same-close execution exige evidência temporal e de acessibilidade compatível com a ordem causal informação → decisão → order-ready → market-arrival → fill. Latência apenas pequena em relação ao timeframe não é prova suficiente.
- Preços observados em negócios passados indicam apenas que terceiros negociaram determinado volume, não garantindo que nossa ordem teria preenchimento idêntico.
- Ordens a mercado que consomem liquidez devem pagar o spread (comprar no Ask, vender no Bid); execuções no Mid-price exigem justificativa formal e evidência de ordens passivas pré-posicionadas.

---

## 4. Modelagem de Fricções Econômicas

Toda claim de viabilidade econômica deve mensurar o resultado líquido:
\[
PnL_{net} = PnL_{gross} - C_{fees} - C_{spread} - C_{slippage} - C_{impact} - C_{other}
\]

1. **Custos e Taxas Operacionais:** Emolumentos da B3, taxas de registro, corretagem e impostos devem ser aplicados com suas tabelas e cronogramas historicamente vigentes.
2. **Latência de Execução:** Deve incluir atrasos de processamento, cálculo de atributos, verificação de risco e latência de rede/broker quando material.
3. **Slippage (Deslizamento):** Diferença de preço entre o envio e a execução efetiva. A incerteza de slippage não pode ser resolvida assumindo cenários favoráveis à estratégia.
4. **Liquidez, Profundidade e Capacidade:**
   - Volume negociado não equivale a liquidez disponível no book;
   - Não se pode assumir linearidade infinita de ganhos: \(PnL(q) = q \times PnL(1)\) para qualquer lote \(q\);
   - Ordens que representam fração relevante da liquidez devem modelar risco de preenchimento parcial (*partial fill*) ou impacto de mercado (*market impact*).
5. **Ambiguidade Intrabar em Dados OHLC:** Se a máxima e a mínima de uma barra atingirem simultaneamente o Stop Loss e o Take Profit e a trajetória interna for materialmente desconhecida, a incerteza deve permanecer desconhecida e receber tratamento explícito que não favoreça sistematicamente a Strategy (métodos admissíveis incluem: política conservadora, desfecho `AMBIGUOUS`/`INDETERMINATE`, consulta a dados de maior resolução ou modelo probabilístico justificado). `UNKNOWN ≠ WORST_CASE ≠ EXPECTED_CASE`.

---

## 5. Protocol Requirements

1. **PR-0E-D-01:** O backtest econômico deve simular expressamente o fluxo de autorização de risco e rejeitar trades vetados pelo Risk Engine.
2. **PR-0E-D-02:** A simulação deve avançar estritamente com o relógio do simulador, sem acesso a dados de barras futuras para decisões passadas.
3. **PR-0E-D-03:** Todas as premissas de execução (custos, slippage, latência, regras de preenchimento) integram a proveniência e o manifesto do `Run`.
4. **PR-0E-D-04:** Simulações com componentes estocásticos exigem registro de sementes aleatórias (*RNG seeds*) e geradores de números pseudoaleatórios.
5. **PR-0E-D-05:** Assumptions materiais de execução devem ser passíveis de perturbação para análise de sensibilidade e estresse; quando materialmente pertinente à claim, essa análise deve integrar a avaliação de robustez.

---

## 6. Hard Quantitative Invariants (D-HQI-01 a D-HQI-41)

| ID | Hard Quantitative Invariant | Mapeamento QPI |
|---|---|---|
| **D-HQI-01** | Retorno futuro de um sinal analítico não equivale a backtest de estratégia executável. | QPI-05, QPI-08 |
| **D-HQI-02** | A força probatória de um backtest depende de sua semântica de simulação, não de sua nomenclatura. | QPI-01 |
| **D-HQI-03** | O backtest econômico não pode contornar a cadeia de decisão, autorização de risco e execução. | QPI-08 |
| **D-HQI-04** | Ordem rejeitada pelo Risk Engine (`REJECT`) não pode produzir trade simulado ou resultado financeiro. | QPI-08, QPI-10 |
| **D-HQI-05** | Desempenho positivo em backtest não demonstra por si só prontidão operacional (*readiness*). | QPI-01, QPI-13 |
| **D-HQI-06** | A execução simulada de uma ordem não pode preceder a chegada da informação ou o tempo de decisão. | QPI-02 |
| **D-HQI-07** | O preço no momento da decisão não é o preço de preenchimento garantido da ordem. | QPI-05 |
| **D-HQI-08** | Preço observado em negócios históricos não garante acessibilidade para a estratégia. | QPI-05 |
| **D-HQI-09** | Execução no preço médio (*mid-price*) para ordens agressoras exige justificativa explícita. | QPI-05, QPI-06 |
| **D-HQI-10** | O custo do spread de compra e venda não pode ser ignorado na simulação. | QPI-06 |
| **D-HQI-11** | Custos e taxas operacionais materiais devem ser explicitamente deduzidos do P&L. | QPI-06 |
| **D-HQI-12** | Tabelas de taxas e emolumentos devem respeitar a vigência histórica do período simulado. | QPI-02, QPI-06 |
| **D-HQI-13** | A fidelidade na modelagem de latência deve ser proporcional à sensibilidade temporal da estratégia. | QPI-06 |
| **D-HQI-14** | Latência assumida em simulação não equivale a latência real observada em ambiente de produção. | QPI-05, QPI-11 |
| **D-HQI-15** | O modelo de slippage utilizado deve ser compatível com a força da claim econômica pretendida. | QPI-06, QPI-01 |
| **D-HQI-16** | Incerteza na execução e no preenchimento não pode adotar por padrão o cenário mais favorável. | QPI-11, QPI-06 |
| **D-HQI-17** | Volume total negociado no mercado não representa liquidez acessível para a nossa ordem. | QPI-05 |
| **D-HQI-18** | A liquidez disponível depende do lado do book, do estado de mercado e do momento temporal. | QPI-05 |
| **D-HQI-19** | A performance de uma estratégia não escala linearmente com o tamanho do lote por presunção. | QPI-06 |
| **D-HQI-20** | Impacto de mercado nulo é uma premissa de modelagem e não um fato universal. | QPI-06, QPI-05 |
| **D-HQI-21** | Não preenchimento de ordem (*no-fill*) é um resultado legítimo e esperado da simulação. | QPI-05 |
| **D-HQI-22** | O risco de preenchimento parcial (*partial fill*) não pode ser convertido em preenchimento total artificial. | QPI-05, QPI-11 |
| **D-HQI-23** | O toque no preço limite (*price touch*) não garante o preenchimento de ordens passivas. | QPI-05 |
| **D-HQI-24** | Trajetória intrabar materialmente desconhecida deve permanecer desconhecida e receber tratamento explícito que não favoreça sistematicamente a Strategy. | QPI-11 |
| **D-HQI-25** | As categorias `UNKNOWN`, pior caso e caso esperado permanecem semanticamente distintas. | QPI-11 |
| **D-HQI-26** | A simulação de mercado deve avançar estritamente de forma causal com o relógio do simulador. | QPI-02 |
| **D-HQI-27** | Estados do ciclo de vida de ordens materialmente relevantes à Strategy ou à claim de execução devem ser representados. | QPI-05 |
| **D-HQI-28** | Reivindicações de execução precisa não podem exceder a resolução e granularidade dos dados. | QPI-01, QPI-05 |
| **D-HQI-29** | A fidelidade da simulação de mercado é multidimensional (tempo, preço, spread, latência, custos). | QPI-01 |
| **D-HQI-30** | Todas as premissas e modelos de simulação integram obrigatoriamente a proveniência do Run. | QPI-12 |
| **D-HQI-31** | Simulação estocástica exige rastreabilidade completa de geradores e sementes aleatórias (*seeds*). | QPI-12 |
| **D-HQI-32** | Calibração retrospectiva de modelos de execução com base no resultado deve ser declarada como tal. | QPI-03, QPI-04 |
| **D-HQI-33** | Sinais, decisões ou intenções de ordem não geram P&L diretamente sem preenchimento simulado. | QPI-08, QPI-05 |
| **D-HQI-34** | O término arbitrário da janela de teste não cria liquidação forçada de posições sem regra de mercado. | QPI-05 |
| **D-HQI-35** | A fronteira de uma partição ou fold de dados não constitui evento de negociação real no mercado. | QPI-02 |
| **D-HQI-36** | A incerteza da simulação de execução não pode ser convertida em certeza matemática artificial. | QPI-11 |
| **D-HQI-37** | Estado de mercado desatualizado (*stale*) ou incompleto impede a presunção de execução normal. | QPI-05, QPI-11 |
| **D-HQI-38** | As premissas de execução não podem favorecer o candidato em relação ao comparador ou benchmark. | QPI-01, QPI-04 |
| **D-HQI-39** | A seleção retrospectiva de modelos de custo mais favoráveis (*assumption shopping*) integra a busca. | QPI-04 |
| **D-HQI-40** | Premissas materiais de execução devem ser perturbáveis para análise de sensibilidade, integrando a robustez quando pertinente à claim. | QPI-06, QPI-01 |
| **D-HQI-41** | A omissão de qualquer fricção de mercado exige justificativa de imaterialidade ou limitação explícita. | QPI-06 |

---

## 7. Policy / Experiment Parameters (Decisões Deliberadamente Adiada)

Permanecem abertos e parametrizáveis por experimento:
- Resolução temporal dos dados de simulação (ticks, trades, candles);
- Tabela exata de taxas e emolumentos por contrato;
- Modelo matemático específico de slippage (fixo, proporcional à volatilidade, baseado em volume);
- Modelo numérico de latência em milissegundos;
- Algoritmo de prioridade de fila em ordens de livro;
- Função de impacto de mercado para grandes volumes;
- Regra de liquidação de posições no encerramento da sessão intradiária;
- Escolha da biblioteca ou framework físico de backtesting.

---

## 8. Gates Internos do Bloco 0E-D

- **0E-D1:** Classe de simulação e força da claim claramente identificadas.
- **0E-D2:** Reutilização do núcleo de domínio sem desvios de modo.
- **0E-D3:** Causalidade temporal estrita da decisão à execução.
- **0E-D4:** Modelagem explícita de acessibilidade de preços e spread.
- **0E-D5:** Incorporação de custos, latência e slippage.
- **0E-D6:** Modelagem de liquidez, capacidade e impacto.
- **0E-D7:** Representação de preenchimentos parciais e não preenchimentos.
- **0E-D8:** Tratamento explícito da ambiguidade intrabar compatível com D-HQI-24/25.
- **0E-D9:** Declaração multidimensional da fidelidade da simulação.
- **0E-D10:** Reconhecimento financeiro via projeções de Ledger simulado.
- **0E-D11:** Proveniência e reprodutibilidade estocástica garantidas.
- **0E-D12:** Conformidade integral com ADRs 0004, 0006, 0007, 0008, 0014, 0016, 0017, 0021 e 0022.
