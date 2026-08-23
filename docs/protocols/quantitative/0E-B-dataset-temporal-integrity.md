# Protocolo 0E-B — Dados, RunInputBoundary e Integridade Temporal

- **Status:** Fechado tecnicamente no Sprint 0E
- **Data da baseline:** 2026-08-20
- **Consome:** ADR-0003, ADR-0004, ADR-0005, ADR-0006, ADR-0015, ADR-0017, ADR-0018, ADR-0021
- **Subordinado a:** QPI-01, QPI-02, QPI-03, QPI-04, QPI-10, QPI-11, QPI-12

---

## 1. Finalidade e Escopo

O Protocolo 0E-B estabelece os requisitos e invariantes necessários para responder com precisão:
> *Quais informações concretas estavam disponíveis para o experimento, quais poderiam legitimamente estar disponíveis para a decisão histórica simulada e por quais transformações foram convertidas nos inputs efetivamente utilizados?*

Princípio orientador fundamental:
```text
dados existentes hoje
≠ dados historicamente existentes
≠ dados historicamente conhecidos
≠ dados admissíveis naquela decisão
≠ inputs efetivamente consumidos pelo Run
```

---

## 2. Camadas Semânticas de Dados

O tratamento de dados é estruturado nas seguintes camadas conceituais:

1. **Source / Evidence Artifact:** Evidência bruta recebida ou preservada de fontes externas ou locais.
2. **Dataset Specification:** Regra descritiva e declarativa da população de dados pretendida.
3. **Dataset Materialization:** Materialização concreta e imutável da especificação em determinado estado de conhecimento.
4. **Input Slice:** Subconjunto temporal, instrumental ou estrutural destinado a processamento.
5. **RunInputBoundary:** Fronteira contratual dos inputs, versões e cortes efetivamente disponíveis e consumidos por um `Run` computacional.

---

## 3. Integridade Temporal e Point-in-Time Correctness

### 3.1. Conjunto de Informação Admissível \(I(t)\)
Para cada oportunidade de decisão no instante \(t\), o conjunto de informação admissível \(I(t)\) contém apenas os dados cuja disponibilidade histórica e todas as transformações precedentes respeitam o *knowledge cutoff* \(t\).

Não basta verificar que `event_time(x) <= t`. É obrigatório que o fato já fosse conhecido e acessível no sistema em \(t\).

### 3.2. Múltiplos Eixos Temporais
Devem ser distinguidos conforme o domínio:
- `event_time`: instante de ocorrência no mercado/provedor;
- `effective_time`: instante em que o fato passa a ter efeito econômico/normativo;
- `knowledge_time` / `availability_time`: instante em que a informação se tornou acessível ao sistema;
- `ingestion_time`: instante de chegada física ao pipeline;
- `capture_context` e `processing_context`: metadados de proveniência por componente e Run.

### 3.3. UNKNOWN Permanece UNKNOWN
A ausência de registro explícito de `availability_time` não autoriza a invenção de que `availability_time = event_time` ou o fechamento arbitrário de barras. Na dúvida temporal, a incerteza deve ser registrada como limitação metodológica.

### 3.4. Fidelidade Histórica
Distingue-se evidência capturada ao vivo (*captured-live*) de dados históricos fornecidos por vendors (*vendor-historical*), registrando as limitações de granularidade e ordenação.

---

## 4. Prevenção de Look-Ahead Bias e Data Leakage

### 4.1. Definição de Look-Ahead Bias
Ocorre quando qualquer decisão, cálculo de atributo, agregação, transformação, filtro ou seleção utiliza, direta ou indiretamente, informação cujo conhecimento admissível ocorre após o *cutoff* temporal correspondente.

### 4.2. Tipologia Canônica de Leakage
- **Direct Feature Leakage:** Atributo que incorpora diretamente valores futuros da série ou do target.
- **Transform Leakage:** Transformações ajustadas (*fit*) com dados do futuro (ex.: `StandardScaler`, `MinMaxScaler`, PCA, quantis ou imputadores ajustados sobre todo o histórico).
- **Aggregation Leakage:** Médias móveis, agregações ou janelas centradas que utilizam observações posteriores ao ponto de cálculo.
- **Window Leakage:** Utilização de dados incompletos ou fechamentos de barras antes de sua finalização formal (*candle finality*).
- **Label Overlap Contamination:** Sobreposição temporal de horizontes de rótulos que contamina features de períodos adjacentes.
- **Reference-Data Leakage:** Tabelas de referência, calendários, dividendos ou ajustes corporativos conhecidos a posteriori aplicados retroativamente sem histórico *as-known*.
- **Revision Leakage:** Uso de valores revisados de séries econômicas ou dados fundamentais antes da data em que a revisão foi efetivamente publicada.
- **Selection Leakage:** Seleção prévia de instrumentos (ex.: os mais líquidos do dia) ou atributos com base em desempenho verificado no final da amostra.

---

## 5. Especificidades de Mercado e Tratamento de Séries

1. **Ciclo de Vida do Candle:** Distinguir estritamente intervalo do candle (`start_time` a `end_time`), momento de finalização (`candle_finality`) e disponibilidade para consumo (`candle_availability`).
2. **Missingness e Gaps:** `UNKNOWN`, `NOT_PROVIDED`, `NOT_APPLICABLE` e ausência de negociação são conceitualmente distintos de zero (`0.0`). Interpolação ou *forward-fill* são decisões explícitas de modelagem, não propriedades intrínsecas dos dados.
3. **Viés de Sobrevivência (Survivorship Bias):** Universos históricos devem ser reconstruídos em base *point-in-time* (*as-known*), incluindo ativos que deixaram de ser negociados.
4. **Rollover de Contratos Futuros:** A regra de transição entre vencimentos deve ser causal e reproduzível no tempo histórico da decisão.
5. **Séries Analíticas Contínuas:** Séries contínuas sintéticas são instrumentos de pesquisa e não representam preços executáveis de um contrato negociável real.
6. **Revisões e Correções:** Correções em dados brutos geram novas materializações de datasets e novos `Runs`, preservando o registro do que foi consumido em execuções passadas.

---

## 6. Protocol Requirements

1. **PR-0E-B-01:** Todo `Run` experimental deve definir um `RunInputBoundary` imutável, identificando datasets, versões, cortes e limitações de fidelidade.
2. **PR-0E-B-02:** Todo pré-processamento ajustável (*fitted*) deve ser calibrado estritamente dentro do conjunto de desenvolvimento e aplicado causalmente.
3. **PR-0E-B-03:** A linhagem de dados (*data lineage*) deve registrar transformações, exclusões e regras de imputação aplicadas.
4. **PR-0E-B-04:** Devem ser executados testes conceituais de integridade temporal (ex.: teste de contaminação de candle, teste de vazamento de scaler).

---

## 7. Hard Quantitative Invariants (B-HQI-01 a B-HQI-29)

| ID | Hard Quantitative Invariant | Mapeamento QPI |
|---|---|---|
| **B-HQI-01** | Dataset nominal declarado não equivale automaticamente ao input efetivo consumido pelo Run. | QPI-01, QPI-12 |
| **B-HQI-02** | O input declarado no manifesto não substitui a proveniência real de processamento quando material. | QPI-12 |
| **B-HQI-03** | `event_time` não equivale a `knowledge_time` (tempo de disponibilidade). | QPI-02 |
| **B-HQI-04** | `effective_time` não equivale a `knowledge_time`. | QPI-02 |
| **B-HQI-05** | Disponibilidade temporal desconhecida (`UNKNOWN`) não pode ser fabricada artificialmente. | QPI-11 |
| **B-HQI-06** | A existência de um dado histórico na base hoje não prova sua disponibilidade histórica na data do fato. | QPI-02, QPI-11 |
| **B-HQI-07** | Informação futura não pode alcançar o input decisório por nenhum caminho direto ou derivacional. | QPI-02, QPI-10 |
| **B-HQI-08** | Dados e atributos derivados herdam integralmente as restrições temporais de seus dados ancestrais. | QPI-02 |
| **B-HQI-09** | Informação futura de rótulos/targets não pode contaminar o conjunto de features preditivas. | QPI-02, QPI-10 |
| **B-HQI-10** | Transformações ajustadas (*fitted transforms*) possuem seus próprios knowledge cutoffs e não podem ver o futuro. | QPI-02, QPI-03 |
| **B-HQI-11** | Intervalo do candle, finalização do candle e disponibilidade para decisão permanecem distintos. | QPI-02 |
| **B-HQI-12** | Dados ausentes, desconhecidos ou não aplicáveis não equivalem a zero (`0.0`). | QPI-11 |
| **B-HQI-13** | Imputação de dados é decisão metodológica explícita, não correção neutra de dados. | QPI-04, QPI-12 |
| **B-HQI-14** | Ausência de registro na base de dados não equivale a ausência observada de negociação no mercado. | QPI-11, QPI-05 |
| **B-HQI-15** | A reconstituição do universo histórico deve prevenir viés de sobrevivência (*survivorship bias*). | QPI-01 |
| **B-HQI-16** | A seleção histórica de instrumentos e regras de rollover deve ser causal e point-in-time. | QPI-02 |
| **B-HQI-17** | Séries sintéticas/contínuas analíticas não constituem preços negociáveis executáveis. | QPI-05, QPI-08 |
| **B-HQI-18** | Correção posterior de dados históricos não apaga o histórico do que foi conhecido no passado. | QPI-02, QPI-12 |
| **B-HQI-19** | A identidade do input histórico efetivamente utilizado em um Run é imutável. | QPI-12 |
| **B-HQI-20** | Aliases mutáveis (`latest`, `current`) não constituem identidade estável de versão de dataset. | QPI-12 |
| **B-HQI-21** | Exclusões e filtros materiais de dados integram obrigatoriamente a proveniência do estudo. | QPI-04, QPI-12 |
| **B-HQI-22** | A limpeza e filtragem de dados não podem depender do resultado econômico posterior verificado. | QPI-02, QPI-04 |
| **B-HQI-23** | Features preditoras e labels de target possuem domínios temporais e de conhecimento distintos. | QPI-02 |
| **B-HQI-24** | Cruzamentos e junções temporais (*temporal joins*) devem respeitar a semântica de efetividade e conhecimento. | QPI-02 |
| **B-HQI-25** | Timestamps críticos exigem interpretação temporal não ambígua e fuso horário explícito. | QPI-02, QPI-11 |
| **B-HQI-26** | Sequência ou ordenação temporal desconhecida não pode ser inventada em benefício do modelo. | QPI-11 |
| **B-HQI-27** | Entrega duplicada de eventos de mercado não equivale a múltiplos fatos econômicos reais. | QPI-05 |
| **B-HQI-28** | Curadoria ou limpeza de dados não elimina a linhagem da evidência bruta original. | QPI-12 |
| **B-HQI-29** | A força de qualquer claim experimental não pode exceder a fidelidade e proveniência dos dados consumidos. | QPI-01 |

---

## 8. Policy / Experiment Parameters (Decisões Deliberadamente Adiada)

Permanecem abertos e parametrizáveis por experimento:
- Escolha de fornecedores e fontes de dados;
- Frequências de amostragem e resoluções temporais concretas;
- Regras numéricas específicas de tolerância a gaps e outliers;
- Estratégia concreta de imputação ou descarte de dados faltantes;
- Algoritmos específicos de construção e emenda de séries contínuas;
- Implementação física de armazenamento (Parquet, SQL, DuckDB, etc.);
- Tecnologia de versionamento de datasets e hashing.

---

## 9. Gates Internos do Bloco 0E-B

- **0E-B1:** Camadas semânticas de dados identificáveis.
- **0E-B2:** `RunInputBoundary` definido e rastreável.
- **0E-B3:** Semântica temporal e eixos temporais respeitados.
- **0E-B4:** Correção *point-in-time* assegurada.
- **0E-B5:** Prevenção formal de *look-ahead* e *leakage*.
- **0E-B6:** Tratamento de viés de sobrevivência e revisões.
- **0E-B7:** Distinção entre instrumentos concretos e séries contínuas.
- **0E-B8:** Tratamento transparente de dados faltantes e gaps.
- **0E-B9:** Rastreabilidade e imutabilidade de proveniência.
- **0E-B10:** Conformidade integral com ADRs 0003, 0004, 0005, 0015, 0017, 0018 e 0021.
