# 0F-B — Deferred Decisions, Ownership & Stage Triage (Revisão Final)

**Sprint 0F — Gate do Sprint 0 / Foundation Cross-Gate**  
**Bloco:** 0F-B — Deferred Decisions, Ownership & Stage Triage  
**Baseline Audited Commit:** `2b786ad6727e3bb9cdce07cbf084ff59e24926ca`  
**Data da Avaliação:** 2026-08-23  
**Status da Revisão:** READ-ONLY ANALYSIS — nenhum arquivo do repositório foi alterado, nenhum código implementado e nenhuma decisão técnica antecipada  
**Status de Fechamento:** `PROPOSED_0F-B_RESULT = PASS_WITH_PRE_SPRINT1_ACTIONS` | `0F-B_APPROVAL = PENDING_COORDINATION_REVIEW`  

---

## 1. Enquadramento Epistemológico e Princípios de Triagem

```text
UNDECIDED              ≠  BLOCKING
DELIBERATELY_DEFERRED  ≠  INCOMPLETE / DEFICIENT
IMPLEMENTATION_DETAIL  ≠  NORMATIVE_DECISION
FUTURE_POLICY          ≠  CURRENT_REQUIREMENT
```

A existência de decisões não concretizadas no Sprint 0 **não constitui defeito**. A baseline dos Sprints 0A a 0E foi arquitetada deliberadamente para estabelecer contratos lógicos e semânticos formais (ADRs 0001–0022 e Protocolos Quantitativos 0E-A a 0E-H), mantendo desacopladas as escolhas de tecnologias físicas, bibliotecas, brokers, fornecedores e parâmetros numéricos empíricos.

### Critérios Restritivos de Bloqueio para o Sprint 1
O Sprint 1 (Market Observer) é **estritamente read-only**:
- ✅ **Permitido:** descobrir/correlacionar instrumentos, receber/observar dados de mercado, normalizar observações, registrar proveniência, medir heartbeat e latência observável, produzir e persistir evidência de qualidade, permitir auditoria.
- ⛔ **Proibido:** estratégias, sinais econômicos, TradeIntent, RiskAuthorization, OrderIntent, ExecutionOrder, conexão de execução a corretoras, ordens, dinheiro real, ML operacional, paper trading.

Uma decisão é classificada como `MUST_DECIDE_BEFORE_SPRINT_1` **apenas se** for estritamente impossível escrever o primeiro Market Observer correto, seguro e não arbitrário sem fixar formalmente essa decisão antes do início do sprint.

---

## 2. Inventário de Itens Brutos Deferidos na Fonte (Source Deferment Inventory)

Abaixo está o levantamento exaustivo de todos os 141 itens brutos extraídos das seções normativas de adiamento e dos limites de escopo do projeto:
- `## Decisões deliberadamente adiadas` dos [ADR-0015](file:///c:/Projetos/btg-ai-trader/docs/adr/0015-refinement-event-envelope-processing-context-and-versioning.md) a [ADR-0022](file:///c:/Projetos/btg-ai-trader/docs/adr/0022-refinement-ledger-financial-projections-and-exposure.md);
- `## Policy / Experiment Parameters (Decisões Deliberadamente Adiada)` dos protocolos [0E-A](file:///c:/Projetos/btg-ai-trader/docs/protocols/quantitative/0E-A-experimental-semantics.md) a [0E-G](file:///c:/Projetos/btg-ai-trader/docs/protocols/quantitative/0E-G-promotion-paper-rejection.md);
- Decisões deixadas em aberto nos [ADR-0001](file:///c:/Projetos/btg-ai-trader/docs/adr/0001-safe-structural-bootstrap.md) a [ADR-0014](file:///c:/Projetos/btg-ai-trader/docs/adr/0014-position-portfolio-ledger-and-exposure-ownership.md), [Plano Mestre](file:///c:/Projetos/btg-ai-trader/docs/BTG_AI_TRADER_MASTER_PLAN.md), [SAFETY.md](file:///c:/Projetos/btg-ai-trader/docs/protocols/SAFETY.md) e [config/README.md](file:///c:/Projetos/btg-ai-trader/config/README.md).

| # | SOURCE | SOURCE_SECTION | RAW_DEFERRED_ITEM | NORMALIZED_DECISION_ID |
|:---|:---|:---|:---|:---|
| 1 | ADR-0015 | ## Decisões deliberadamente adiadas | representação física de IDs | DD-01 |
| 2 | ADR-0015 | ## Decisões deliberadamente adiadas | formato de serialização | DD-02 |
| 3 | ADR-0015 | ## Decisões deliberadamente adiadas | schema framework | DD-03 |
| 4 | ADR-0015 | ## Decisões deliberadamente adiadas | algoritmo de versionamento | DD-04 |
| 5 | ADR-0015 | ## Decisões deliberadamente adiadas | storage | DD-20, DD-21 |
| 6 | ADR-0015 | ## Decisões deliberadamente adiadas | mensageria | DD-22 |
| 7 | ADR-0015 | ## Decisões deliberadamente adiadas | mecanismo físico de migração/upcast | DD-05 |
| 8 | ADR-0016 | ## Decisões deliberadamente adiadas | tipos concretos de ordem | DD-06 |
| 9 | ADR-0016 | ## Decisões deliberadamente adiadas | time-in-force | DD-06 |
| 10 | ADR-0016 | ## Decisões deliberadamente adiadas | mecanismo físico de reserva/locking | DD-07 |
| 11 | ADR-0016 | ## Decisões deliberadamente adiadas | formato de idempotency key | DD-08 |
| 12 | ADR-0016 | ## Decisões deliberadamente adiadas | broker/provider (execution) | DD-09 |
| 13 | ADR-0016 | ## Decisões deliberadamente adiadas | MT5 (execution) | DD-10 |
| 14 | ADR-0016 | ## Decisões deliberadamente adiadas | cancel/replace concreto | DD-11 |
| 15 | ADR-0016 | ## Decisões deliberadamente adiadas | retry timing | DD-12 |
| 16 | ADR-0016 | ## Decisões deliberadamente adiadas | implementação de persistência | DD-20, DD-26 |
| 17 | ADR-0017 | ## Decisões deliberadamente adiadas | RNG concreto | DD-13 |
| 18 | ADR-0017 | ## Decisões deliberadamente adiadas | algoritmo de seed | DD-14 |
| 19 | ADR-0017 | ## Decisões deliberadamente adiadas | formato do RunInputBoundary | DD-15 |
| 20 | ADR-0017 | ## Decisões deliberadamente adiadas | equivalência numérica/byte-a-byte | DD-16 |
| 21 | ADR-0017 | ## Decisões deliberadamente adiadas | artifact registry | DD-17 |
| 22 | ADR-0017 | ## Decisões deliberadamente adiadas | Git/MLflow | DD-18 |
| 23 | ADR-0017 | ## Decisões deliberadamente adiadas | ambiente físico de execução | DD-19 |
| 24 | ADR-0018 | ## Decisões deliberadamente adiadas | banco | DD-20 |
| 25 | ADR-0018 | ## Decisões deliberadamente adiadas | SQL/NoSQL | DD-20 |
| 26 | ADR-0018 | ## Decisões deliberadamente adiadas | filesystem/object storage | DD-21 |
| 27 | ADR-0018 | ## Decisões deliberadamente adiadas | Kafka | DD-22 |
| 28 | ADR-0018 | ## Decisões deliberadamente adiadas | WAL | DD-23 |
| 29 | ADR-0018 | ## Decisões deliberadamente adiadas | fsync | DD-24 |
| 30 | ADR-0018 | ## Decisões deliberadamente adiadas | replication/quorum | DD-25 |
| 31 | ADR-0018 | ## Decisões deliberadamente adiadas | transaction mechanism | DD-26 |
| 32 | ADR-0018 | ## Decisões deliberadamente adiadas | serialization | DD-02 |
| 33 | ADR-0018 | ## Decisões deliberadamente adiadas | snapshot format | DD-27 |
| 34 | ADR-0018 | ## Decisões deliberadamente adiadas | TTL/retention | DD-28 |
| 35 | ADR-0018 | ## Decisões deliberadamente adiadas | cloud provider | DD-29 |
| 36 | ADR-0019 | ## Decisões deliberadamente adiadas | algoritmo de matching | DD-30 |
| 37 | ADR-0019 | ## Decisões deliberadamente adiadas | thresholds de freshness | DD-31 |
| 38 | ADR-0019 | ## Decisões deliberadamente adiadas | número/timing de rounds | DD-32 |
| 39 | ADR-0019 | ## Decisões deliberadamente adiadas | provider capabilities concretas | DD-33 |
| 40 | ADR-0019 | ## Decisões deliberadamente adiadas | natureza humana/automática de determinadas authorities | DD-34 |
| 41 | ADR-0019 | ## Decisões deliberadamente adiadas | mecanismos físicos de recovery | DD-35 |
| 42 | ADR-0020 | ## Decisões deliberadamente adiadas | catálogo físico de enums | DD-36 |
| 43 | ADR-0020 | ## Decisões deliberadamente adiadas | thresholds de transition policy | DD-37 |
| 44 | ADR-0020 | ## Decisões deliberadamente adiadas | necessidade concreta de confirmação humana para unlatch | DD-38 |
| 45 | ADR-0020 | ## Decisões deliberadamente adiadas | implementação de watchdog/kill switch | DD-39 |
| 46 | ADR-0021 | ## Decisões deliberadamente adiadas | formato físico de manifest | DD-40 |
| 47 | ADR-0021 | ## Decisões deliberadamente adiadas | Git/hash/SemVer como representação universal | DD-41 |
| 48 | ADR-0021 | ## Decisões deliberadamente adiadas | artifact registry | DD-17 |
| 49 | ADR-0021 | ## Decisões deliberadamente adiadas | MLflow | DD-18 |
| 50 | ADR-0021 | ## Decisões deliberadamente adiadas | storage | DD-20, DD-21 |
| 51 | ADR-0021 | ## Decisões deliberadamente adiadas | serialization | DD-02 |
| 52 | ADR-0021 | ## Decisões deliberadamente adiadas | environment packaging | DD-42 |
| 53 | ADR-0021 | ## Decisões deliberadamente adiadas | mecanismo de secret references | DD-43 |
| 54 | ADR-0022 | ## Decisões deliberadamente adiadas | double-entry clássico | DD-44 |
| 55 | ADR-0022 | ## Decisões deliberadamente adiadas | chart of accounts | DD-45 |
| 56 | ADR-0022 | ## Decisões deliberadamente adiadas | cost basis | DD-46 |
| 57 | ADR-0022 | ## Decisões deliberadamente adiadas | FIFO/média | DD-46 |
| 58 | ADR-0022 | ## Decisões deliberadamente adiadas | methodology de P&L/valuation | DD-47 |
| 59 | ADR-0022 | ## Decisões deliberadamente adiadas | settlement rules concretas | DD-48 |
| 60 | ADR-0022 | ## Decisões deliberadamente adiadas | FX | DD-49 |
| 61 | ADR-0022 | ## Decisões deliberadamente adiadas | margin/buying power | DD-50 |
| 62 | ADR-0022 | ## Decisões deliberadamente adiadas | netting | DD-51 |
| 63 | ADR-0022 | ## Decisões deliberadamente adiadas | broker account topology | DD-52 |
| 64 | ADR-0022 | ## Decisões deliberadamente adiadas | mecanismo físico de ledger | DD-53 |
| 65 | ADR-0001 | ## Consequências | escolhas de stack técnica abertas | DD-03, DD-20 |
| 66 | ADR-0002 | ## Decisão | concorrência nas bordas de I/O | DD-54 |
| 67 | ADR-0002 | ## Invariantes | separação física futura em processos/serviços | DD-55 |
| 68 | ADR-0004 | ## Decisão | calendário versionado B3 e regras America/Sao_Paulo | DD-56 |
| 69 | ADR-0004 | ## Consequências | janelas de tolerância e reordenação temporal | DD-57 |
| 70 | ADR-0005 | ## Consequências | registry e resolução concreta de instrumentos | DD-58 |
| 71 | ADR-0006 | ## Decisão | contrato futuro baseado em capacidades declaradas | DD-33 |
| 72 | ADR-0006 | ## Consequências | política de deduplicação e degradação | DD-59 |
| 73 | ADR-0008 | ## Decisão | adaptadores reais e reconciliação para LIVE | DD-09, DD-30 |
| 74 | ADR-0008 | ## Consequências | composição e simuladores para perfis operacionais | DD-99 |
| 75 | ADR-0011 | ## Decisão | detalhamento de estados operacionais | DD-36 |
| 76 | ADR-0011 | ## Decisão | autorização de flatten/cancelamento em SAFE_HALT | DD-38 |
| 77 | ADR-0012 | ## Consequências | classificação e canais de quarantine | DD-62 |
| 78 | ADR-0013 | ## Decisão | vinculação de artefatos de decisão (strategy/model version) | DD-63 |
| 79 | ADR-0014 | ## Consequências | modelagem de reservas de exposição | DD-64 |
| 80 | 0E-A | ## 5. Policy / Experiment Parameters | Definição do ativo concreto e timeframe | DD-68 |
| 81 | 0E-A | ## 5. Policy / Experiment Parameters | Especificação de targets, labels e horizontes de previsão/decisão | DD-69 |
| 82 | 0E-A | ## 5. Policy / Experiment Parameters | Lista concreta de features e hiperparâmetros | DD-70 |
| 83 | 0E-A | ## 5. Policy / Experiment Parameters | Escolha de arquiteturas de modelos e algoritmos de ML | DD-71 |
| 84 | 0E-A | ## 5. Policy / Experiment Parameters | Escolha de comparadores e benchmarks específicos | DD-73 |
| 85 | 0E-A | ## 5. Policy / Experiment Parameters | Modelagem numérica exata de custos e fricções | DD-74 |
| 86 | 0E-A | ## 5. Policy / Experiment Parameters | Métricas estatísticas específicas e seus thresholds | DD-75 |
| 87 | 0E-A | ## 5. Policy / Experiment Parameters | Número de folds, seeds e cenários de robustez | DD-76 |
| 88 | 0E-B | ## 8. Policy / Experiment Parameters | Escolha de fornecedores e fontes de dados | DD-77 |
| 89 | 0E-B | ## 8. Policy / Experiment Parameters | Frequências de amostragem e resoluções temporais concretas | DD-78 |
| 90 | 0E-B | ## 8. Policy / Experiment Parameters | Regras numéricas específicas de tolerância a gaps e outliers | DD-79 |
| 91 | 0E-B | ## 8. Policy / Experiment Parameters | Estratégia concreta de imputação ou descarte de dados faltantes | DD-80 |
| 92 | 0E-B | ## 8. Policy / Experiment Parameters | Algoritmos específicos de construção e emenda de séries contínuas | DD-81 |
| 93 | 0E-B | ## 8. Policy / Experiment Parameters | Implementação física de armazenamento (Parquet, SQL, DuckDB, etc.) | DD-82 |
| 94 | 0E-B | ## 8. Policy / Experiment Parameters | Tecnologia de versionamento de datasets e hashing | DD-83 |
| 95 | 0E-C | ## 7. Policy / Experiment Parameters | Datas e intervalos exatos de divisão entre treino, validação e teste protegido | DD-84 |
| 96 | 0E-C | ## 7. Policy / Experiment Parameters | Proporções e tamanhos das janelas de amostragem | DD-85 |
| 97 | 0E-C | ## 7. Policy / Experiment Parameters | Número exato de dobras (folds) no walk-forward | DD-86 |
| 98 | 0E-C | ## 7. Policy / Experiment Parameters | Método de purging e horizonte de purging | DD-87 |
| 99 | 0E-C | ## 7. Policy / Experiment Parameters | Método de embargo e duração de embargo | DD-88 |
| 100 | 0E-C | ## 7. Policy / Experiment Parameters | Definição algorítmica específica de regimes de volatilidade ou tendência | DD-89 |
| 101 | 0E-C | ## 7. Policy / Experiment Parameters | Lista e seleção de baselines e benchmarks específicos | DD-90 |
| 102 | 0E-C | ## 7. Policy / Experiment Parameters | Thresholds numéricos de estabilidade entre folds | DD-91 |
| 103 | 0E-D | ## 7. Policy / Experiment Parameters | Resolução temporal dos dados de simulação (ticks, trades, candles) | DD-92 |
| 104 | 0E-D | ## 7. Policy / Experiment Parameters | Tabela exata de taxas e emolumentos por contrato | DD-93 |
| 105 | 0E-D | ## 7. Policy / Experiment Parameters | Modelo matemático específico de slippage | DD-94 |
| 106 | 0E-D | ## 7. Policy / Experiment Parameters | Modelo numérico de latência em milissegundos | DD-95 |
| 107 | 0E-D | ## 7. Policy / Experiment Parameters | Algoritmo de prioridade de fila em ordens de livro | DD-96 |
| 108 | 0E-D | ## 7. Policy / Experiment Parameters | Função de impacto de mercado para grandes volumes | DD-97 |
| 109 | 0E-D | ## 7. Policy / Experiment Parameters | Regra de liquidação de posições no encerramento da sessão intradiária | DD-98 |
| 110 | 0E-D | ## 7. Policy / Experiment Parameters | Escolha da biblioteca ou framework físico de backtesting | DD-99 |
| 111 | 0E-E | ## 9. Policy / Experiment Parameters | Definição formal do estimand de cada estudo | DD-100 |
| 112 | 0E-E | ## 9. Policy / Experiment Parameters | Lista de métricas primárias e secundárias do experimento | DD-101 |
| 113 | 0E-E | ## 9. Policy / Experiment Parameters | Níveis de significância estatística (alpha) e intervalos de confiança | DD-102 |
| 114 | 0E-E | ## 9. Policy / Experiment Parameters | Escolha da metodologia inferencial (frequentista, bayesiana, bootstrap) | DD-103 |
| 115 | 0E-E | ## 9. Policy / Experiment Parameters | Comprimento dos blocos em bootstrap temporal | DD-104 |
| 116 | 0E-E | ## 9. Policy / Experiment Parameters | Métodos específicos de controle de multiplicidade | DD-105 |
| 117 | 0E-E | ## 9. Policy / Experiment Parameters | Thresholds numéricos mínimos de Sharpe, Sortino, Calmar e Expectancy | DD-106 |
| 118 | 0E-E | ## 9. Policy / Experiment Parameters | Níveis de corte para VaR e Expected Shortfall | DD-107 |
| 119 | 0E-E | ## 9. Policy / Experiment Parameters | Grade de parâmetros para testes de sensibilidade e perturbação de custos | DD-108 |
| 120 | 0E-F | ## 9. Policy / Experiment Parameters | Lista específica de métricas preditivas por família de modelo | DD-109 |
| 121 | 0E-F | ## 9. Policy / Experiment Parameters | Thresholds numéricos mínimos de calibração (Brier) e discriminação (AUC) | DD-110 |
| 122 | 0E-F | ## 9. Policy / Experiment Parameters | Limiares exatos de decisão e confiança da estratégia | DD-111 |
| 123 | 0E-F | ## 9. Policy / Experiment Parameters | Regras de penalização de complexidade algorítmica | DD-112 |
| 124 | 0E-F | ## 9. Policy / Experiment Parameters | Critérios quantitativos para detecção de model drift e strategy decay | DD-113 |
| 125 | 0E-F | ## 9. Policy / Experiment Parameters | Formato físico de armazenamento e metadados de Model Cards | DD-114 |
| 126 | 0E-G | ## 8. Policy / Experiment Parameters | Número mínimo exigido de pregões e oportunidades em Paper Trading | DD-115 |
| 127 | 0E-G | ## 8. Policy / Experiment Parameters | Limiares quantitativos de tolerância a discrepâncias Backtest vs Paper | DD-116 |
| 128 | 0E-G | ## 8. Policy / Experiment Parameters | Tolerâncias máximas aceitáveis para slippage e latência em Paper | DD-117 |
| 129 | 0E-G | ## 8. Policy / Experiment Parameters | Prazos de validade temporal e critérios de vigência de status de promoção | DD-118 |
| 130 | 0E-G | ## 8. Policy / Experiment Parameters | Critérios quantitativos para parada de emergência em Paper | DD-119 |
| 131 | 0E-G | ## 8. Policy / Experiment Parameters | Formato físico de relatórios de auditoria e telas de acompanhamento | DD-120 |
| 132 | MASTER_PLAN / ADR-0006 / SPRINT_0.md | L110 / L22 / L32 | Provedor de Market Data read-only inicial (MT5 API vs direct vendor) | DD-60 |
| 133 | MASTER_PLAN | L598 | Repositório remoto não é requisito prévio para avançar arquitetura | DD-66 |
| 134 | MASTER_PLAN / 0E-H | L779-785 / L56 | Limites diários de perda e dimensionamento real de lotes | DD-121 |
| 135 | MASTER_PLAN | L801-807 | Dashboard e interface de monitoramento operacional | DD-122 |
| 136 | MASTER_PLAN | 4.2 (L126-136) | Automação de trading por cliques na interface do BTG Trader | DD-123 |
| 137 | MASTER_PLAN | 4.2 (L126-136) | HFT de microssegundos | DD-124 |
| 138 | config/README.md | L12 | Formato e mecanismo de validação de configuração | DD-65 |
| 139 | SPRINT_0.md / MASTER_PLAN | L20-24 / L698 | Validação de compatibilidade Python 3.12 vs MetaTrader 5 | DD-61 |
| 140 | MASTER_PLAN | L238 | Representação numérica de preços, volumes e quantidades | DD-67 |
| 141 | README.md / 0E-H | L48-49 / L56 | Seleção de biblioteca ou framework físico de Machine Learning | DD-72 |

Total de itens brutos mapeados na fonte: **141**  
Total de decisões normalizadas resultantes: **124** (`DD-01` a `DD-124`)  
Decisões normalizadas sem fonte mapeada (`NORMALIZED_DECISIONS_WITHOUT_SOURCE`): **0**

---

## 3. Registro de Decisões Deferidas Normalizadas (Deferred Decision Register)

> [!NOTE]
> Convenção das Dimensões Independentes:
> - **EPISTEMIC_CLASS:** `DELIBERATELY_DEFERRED` | `IMPLEMENTATION_DETAIL` | `FUTURE_POLICY` | `OUT_OF_SCOPE` | `UNDECIDED_AND_BLOCKING`
> - **TIMING_CLASS:** `MUST_DECIDE_BEFORE_SPRINT_1` | `MAY_DECIDE_DURING_SPRINT_1` | `MAY_DEFER_BEYOND_SPRINT_1` | `MUST_REMAIN_UNDECIDED_NOW`
> - **OWNER_STAGE_SOURCE:** `EXPLICIT_IN_BASELINE` | `DERIVED_FROM_ROADMAP` | `ASSIGNED_BY_0F_B`

---

### Tabela Consolidada de Decisões Normalizadas (DD-01 a DD-124)

| ID | DECISÃO NORMALIZADA | EPISTEMIC_CLASS | TIMING_CLASS | DECISION_OWNER_STAGE | OWNER_STAGE_SOURCE | EARLIEST_STAGE | LATEST_STAGE | SPRINT_1_APPLICABILITY |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **DD-01** | Representação física de IDs (UUID, ULID, int, str) | `DELIBERATELY_DEFERRED` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_1` | A decisão concreta pode ser tomada durante o Sprint 1, antes da primeira capability que dependa materialmente dela. |
| **DD-02** | Formato de serialização de eventos e mensagens | `DELIBERATELY_DEFERRED` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_2` | A decisão concreta pode ser tomada durante o Sprint 1 para persistência/transmissão de evidências observadas. |
| **DD-03** | Framework de schema e validação de tipos de dados de domínio | `IMPLEMENTATION_DETAIL` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_1` | A decisão concreta pode ser tomada durante o Sprint 1 na modelagem das estruturas de dados. |
| **DD-04** | Algoritmo e política de versionamento de schemas de eventos | `DELIBERATELY_DEFERRED` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_2` | A decisão concreta pode ser tomada durante o Sprint 1 para versionamento do envelope. |
| **DD-05** | Mecanismo físico de schema migration e upcasting de eventos históricos | `DELIBERATELY_DEFERRED` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_2_MARKET_DATA_PLATFORM` | `DERIVED_FROM_ROADMAP` | `SPRINT_2` | `SPRINT_3` | Não aplicável no Sprint 1 (apenas schema inicial v1). |
| **DD-06** | Catálogo de tipos concretos de ordens e time-in-force | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_8` | Não aplicável no Sprint 1 (read-only; sem ordens). |
| **DD-07** | Mecanismo físico de locking e reserva concorrente de capacidade de risco | `DELIBERATELY_DEFERRED` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_8` | Não aplicável no Sprint 1 (sem alocação de risco). |
| **DD-08** | Formato e geração de idempotency keys para execuções e intents | `IMPLEMENTATION_DETAIL` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_8` | Não aplicável no Sprint 1 (sem intents de execução). |
| **DD-09** | Seleção de broker e plataforma de execução para ordens | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_9_CLOUD_TRADING_NODE` | `DERIVED_FROM_ROADMAP` | `SPRINT_8` | `SPRINT_9` | Proibido nesta fase (sem execução). |
| **DD-10** | Integração com MetaTrader 5 para envio e gestão de ordens de execução | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_9_CLOUD_TRADING_NODE` | `DERIVED_FROM_ROADMAP` | `SPRINT_8` | `SPRINT_9` | Proibido nesta fase (sem envio de ordens). |
| **DD-11** | Protocolo concreto de cancel/replace e reconciliação de modificações de ordem | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_8` | Não aplicável no Sprint 1 (sem gestão de ordens). |
| **DD-12** | Políticas e timing de retry com backoff para falhas de comunicação com broker | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_9_CLOUD_TRADING_NODE` | `DERIVED_FROM_ROADMAP` | `SPRINT_8` | `SPRINT_9` | Não aplicável no Sprint 1 (sem canal de execução). |
| **DD-13** | Algoritmo concreto de Random Number Generator (RNG) para simulação | `DELIBERATELY_DEFERRED` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_3_BACKTESTING_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_3` | Não aplicável no Sprint 1 (observação determinística). |
| **DD-14** | Algoritmo de inicialização, derivação e particionamento de seeds | `DELIBERATELY_DEFERRED` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_3_BACKTESTING_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_3` | Não aplicável no Sprint 1. |
| **DD-15** | Formato físico e representação do RunInputBoundary | `DELIBERATELY_DEFERRED` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_3_BACKTESTING_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_2` | `SPRINT_3` | Não aplicável no Sprint 1 (relevante para replay/backtest). |
| **DD-16** | Critérios de equivalência numérica vs byte-level para determinismo e replay | `DELIBERATELY_DEFERRED` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_3_BACKTESTING_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_3` | Não aplicável no Sprint 1. |
| **DD-17** | Tecnologia e infraestrutura de Artifact Registry | `IMPLEMENTATION_DETAIL` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_5_ML_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_2` | `SPRINT_5` | Não aplicável no Sprint 1. |
| **DD-18** | Ferramenta de tracking de experimentos e linhagem de runs | `IMPLEMENTATION_DETAIL` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_5_ML_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_5` | Não aplicável no Sprint 1 (sem treino de modelos). |
| **DD-19** | Especificação do ambiente físico de execução determinística (OS, containers) | `IMPLEMENTATION_DETAIL` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_3_BACKTESTING_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_9` | A execução no Sprint 1 ocorre no ambiente de desenvolvimento local normatizado no Sprint 0B. |
| **DD-20** | Tecnologia de banco de dados para os planos de persistência (SQL vs NoSQL) | `DELIBERATELY_DEFERRED` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_2` | A decisão concreta pode ser tomada durante o Sprint 1, antes da primeira capability que dependa materialmente dela. |
| **DD-21** | Tecnologia de filesystem e object storage para EvidenceArchive | `DELIBERATELY_DEFERRED` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_2` | A decisão concreta sobre o arquivamento raw pode ser tomada durante o Sprint 1. |
| **DD-22** | Tecnologia de transporte e mensageria interna | `DELIBERATELY_DEFERRED` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_9` | A decisão concreta sobre o mecanismo de transporte interno pode ser tomada durante o Sprint 1. |
| **DD-23** | Implementação de Write-Ahead Log (WAL) para durabilidade pré-ação | `DELIBERATELY_DEFERRED` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_8` | Não aplicável no Sprint 1 (sem side effects econômicos). |
| **DD-24** | Política e mecanismo de fsync/flush síncrono para persist-before-act | `DELIBERATELY_DEFERRED` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_8` | Não aplicável no Sprint 1 (sem compromissos econômicos). |
| **DD-25** | Mecanismo de replicação e quórum para persistência crítica | `DELIBERATELY_DEFERRED` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_9_CLOUD_TRADING_NODE` | `DERIVED_FROM_ROADMAP` | `SPRINT_9` | `SPRINT_9` | Não aplicável no Sprint 1 (execução local mononó). |
| **DD-26** | Mecanismo físico de transação e atomicidade local | `IMPLEMENTATION_DETAIL` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_2` | A decisão concreta pode ser tomada durante o Sprint 1 para gravação atômica de evidências. |
| **DD-27** | Formato físico de snapshots de estado operacional | `IMPLEMENTATION_DETAIL` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_2_MARKET_DATA_PLATFORM` | `DERIVED_FROM_ROADMAP` | `SPRINT_2` | `SPRINT_7` | Não aplicável no Sprint 1. |
| **DD-28** | Política de retenção temporal (TTL), expiração e arquivamento de dados | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_2_MARKET_DATA_PLATFORM` | `DERIVED_FROM_ROADMAP` | `SPRINT_2` | `SPRINT_9` | Não aplicável no Sprint 1. |
| **DD-29** | Seleção de provedor de nuvem (AWS, Azure, GCP) e arquitetura de VM | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_9_CLOUD_TRADING_NODE` | `DERIVED_FROM_ROADMAP` | `SPRINT_9` | `SPRINT_9` | Proibido deploy de infraestrutura produtiva nesta fase. |
| **DD-30** | Algoritmo de matching de ordens e fills para reconciliação | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_9_CLOUD_TRADING_NODE` | `DERIVED_FROM_ROADMAP` | `SPRINT_8` | `SPRINT_9` | Não aplicável no Sprint 1 (sem preenchimentos). |
| **DD-31** | Limiares numéricos de freshness e defasagem temporal para reconciliação | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_9_CLOUD_TRADING_NODE` | `DERIVED_FROM_ROADMAP` | `SPRINT_2` | `SPRINT_9` | Não aplicável no Sprint 1. |
| **DD-32** | Protocolo de rodadas de reconciliação (frequência, timing, rounds máximos) | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_9_CLOUD_TRADING_NODE` | `DERIVED_FROM_ROADMAP` | `SPRINT_8` | `SPRINT_9` | Não aplicável no Sprint 1 (sem reconciliação de ordens). |
| **DD-33** | Catálogo formal de capacidades declaradas de provedores de dados | `DELIBERATELY_DEFERRED` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_1` | Diretamente aplicável à instanciação do Observer no Sprint 1. |
| **DD-34** | Política de automação vs intervenção humana para autoridades operacionais | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_9_CLOUD_TRADING_NODE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_9` | Não aplicável no Sprint 1. |
| **DD-35** | Mecanismos físicos de recuperação de estado (crash recovery handlers) | `DELIBERATELY_DEFERRED` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_9_CLOUD_TRADING_NODE` | `DERIVED_FROM_ROADMAP` | `SPRINT_2` | `SPRINT_9` | O Sprint 1 requer apenas reconexão de stream; recovery complexo é posterior. |
| **DD-36** | Catálogo físico de enums para RuntimePhase e SafetyPosture | `IMPLEMENTATION_DETAIL` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_2` | A decisão concreta pode ser tomada durante o Sprint 1 para estados do Observer. |
| **DD-37** | Limiares de transição de segurança e políticas de degradação | `FUTURE_POLICY` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_7` | Aplicável para alertas de desconexão e degradação de captura no Sprint 1. |
| **DD-38** | Requisito de confirmação humana para unlatch de posturas restritivas | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_9` | Não aplicável no Sprint 1 (sem posturas latched de negociação). |
| **DD-39** | Implementação física de watchdog de processo e kill switch de emergência | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_9_CLOUD_TRADING_NODE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_9` | Não aplicável no Sprint 1 (read-only não requer kill switch financeiro). |
| **DD-40** | Formato físico e schema de serialização do RunManifest | `IMPLEMENTATION_DETAIL` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_1` | A decisão concreta pode ser tomada durante o Sprint 1 para registrar a execução do Observer. |
| **DD-41** | Representação canônica universal de versões (Git commit vs hash vs SemVer) | `IMPLEMENTATION_DETAIL` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_1` | Aplicável na proveniência das observações de mercado capturadas. |
| **DD-42** | Tecnologia de empacotamento de ambiente reproduzível (venv vs Docker vs Nix) | `IMPLEMENTATION_DETAIL` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_3_BACKTESTING_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_9` | A decisão concreta sobre empacotamento avançado pode ser tomada em sprint posterior. |
| **DD-43** | Mecanismo de resolução e gerenciamento de referências a credenciais/segredos | `DELIBERATELY_DEFERRED` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_1` | A decisão concreta pode ser tomada durante o Sprint 1 caso o provider exija autenticação. |
| **DD-44** | Modelo contábil do Ledger (partidas dobradas clássicas vs transações atômicas) | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_8` | Não aplicável no Sprint 1 (sem lançamentos financeiros). |
| **DD-45** | Plano de contas (chart of accounts) formal do Ledger | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_8` | Não aplicável no Sprint 1. |
| **DD-46** | Metodologia de cost basis (custo médio ponderado vs FIFO) | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_8` | Não aplicável no Sprint 1. |
| **DD-47** | Metodologia de P&L e Valuation intradiário (Mark-to-Market) | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_8` | Não aplicável no Sprint 1. |
| **DD-48** | Regras de liquidação financeira física (D+0, D+1, D+2) | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_8` | Não aplicável no Sprint 1. |
| **DD-49** | Mecanismo de conversão cambial (FX) e multi-moeda | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_8` | Não aplicável no Sprint 1 (mercado BRL/B3 exclusivamente). |
| **DD-50** | Metodologia e cálculo de margem de garantia e buying power intradiário | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_8` | Não aplicável no Sprint 1. |
| **DD-51** | Regras e mecanismos de netting de posições intradiárias | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_8` | Não aplicável no Sprint 1. |
| **DD-52** | Topologia de contas de custódia e subcontas de corretora | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_8_PAPER_TRADER` | `DERIVED_FROM_ROADMAP` | `SPRINT_8` | `SPRINT_9` | Não aplicável no Sprint 1. |
| **DD-53** | Mecanismo físico de persistência e consulta do Ledger | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_8` | Não aplicável no Sprint 1. |
| **DD-54** | Mecanismo de concorrência nas bordas de I/O (threads vs asyncio vs subprocess) | `IMPLEMENTATION_DETAIL` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_1` | Diretamente aplicável à captura de dados no Sprint 1. |
| **DD-55** | Separação física multi-processo vs monólito modular | `DELIBERATELY_DEFERRED` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_9_CLOUD_TRADING_NODE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_9` | O padrão monólito modular vigente é mantido até evidência contrária. |
| **DD-56** | Implementação concreta de calendário de negociação B3 e feriados | `DELIBERATELY_DEFERRED` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_2` | A decisão concreta pode ser tomada durante o Sprint 1 para delimitar horários de sessão. |
| **DD-57** | Janelas operacionais de tolerância para reordenação de eventos temporais | `FUTURE_POLICY` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_2` | Aplicável na ordenação de ticks e candles recebidos no Sprint 1. |
| **DD-58** | Implementação de Instrument Registry e mapeamento de símbolos | `DELIBERATELY_DEFERRED` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_1` | Diretamente aplicável à descoberta e correlação de símbolos no Sprint 1. |
| **DD-59** | Políticas concretas de deduplicação e backpressure de market data | `IMPLEMENTATION_DETAIL` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_1` | Diretamente aplicável ao fluxo de ingestão do Observer no Sprint 1. |
| **DD-60** | Provedor de Market Data read-only inicial (MT5 API vs direct vendor) | `DELIBERATELY_DEFERRED` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_1` | Decisão central de adaptação do Sprint 1 (estritamente read-only). |
| **DD-61** | Validação técnica de compatibilidade de Python 3.12 com API MetaTrader 5 | `DELIBERATELY_DEFERRED` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_1` | Condicional à escolha do MT5 como feed de mercado no Sprint 1. |
| **DD-62** | Canais físicos de quarantine e classificação de eventos inválidos | `IMPLEMENTATION_DETAIL` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_2` | Aplicável na detecção e isolamento de ticks corrompidos no Sprint 1. |
| **DD-63** | Esquema concreto de propagação e vinculação de metadados de decisão | `IMPLEMENTATION_DETAIL` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_5` | Não aplicável no Sprint 1. |
| **DD-64** | Modelo algorítmico de reserva e tracking de exposição agregada | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_8` | Não aplicável no Sprint 1. |
| **DD-65** | Formato de arquivo e validação de configuração não-sensível | `IMPLEMENTATION_DETAIL` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_1` | A decisão concreta pode ser tomada durante o Sprint 1 para parametrização do Observer. |
| **DD-66** | Infraestrutura e hosting de repositório Git remoto (GitHub/GitLab) | `IMPLEMENTATION_DETAIL` | `MAY_DEFER_BEYOND_SPRINT_1` | `CROSS_CUTTING_ADR` | `ASSIGNED_BY_0F_B` | `SPRINT_1` | `SPRINT_9` | Repositório local autônomo é suficiente para a baseline e Sprint 1. |
| **DD-67** | Representação numérica de preços, volumes e quantidades financeiras | `DELIBERATELY_DEFERRED` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_1` | Diretamente aplicável à modelagem de dados numéricos observados. |
| **DD-68** | Seleção do instrumento e resolução do primeiro laboratório experimental | `FUTURE_POLICY` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_1` | Configuração do primeiro ativo/timeframe observado no Sprint 1. |
| **DD-69** | Especificação de targets, labels e horizontes temporais de previsão | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_5_ML_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_5` | Não aplicável no Sprint 1. |
| **DD-70** | Definição do catálogo de features e espaço de hiperparâmetros | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_5_ML_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_5` | Não aplicável no Sprint 1. |
| **DD-71** | Escolha de arquiteturas de modelos e algoritmos de Machine Learning | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_5_ML_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_5` | Não aplicável no Sprint 1 (pesquisa preditiva futura). |
| **DD-72** | Seleção de biblioteca ou framework físico de Machine Learning | `IMPLEMENTATION_DETAIL` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_5_ML_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_5` | Não aplicável no Sprint 1 (sem dependências de ML). |
| **DD-73** | Seleção de modelos de baseline e benchmarks de comparação | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-74** | Modelagem paramétrica de custos de transação e fricções | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_3_BACKTESTING_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_3` | Não aplicável no Sprint 1. |
| **DD-75** | Definição de métricas de validação de hipótese e níveis de significância | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-76** | Parametrização de folds, seeds e grade de robustez para hipóteses | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-77** | Seleção de fontes e vendors de dados históricos de mercado | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_2_MARKET_DATA_PLATFORM` | `DERIVED_FROM_ROADMAP` | `SPRINT_2` | `SPRINT_2` | O Sprint 1 foca em observação e captura em tempo real. |
| **DD-78** | Resoluções e frequências de amostragem de datasets históricos | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_2_MARKET_DATA_PLATFORM` | `DERIVED_FROM_ROADMAP` | `SPRINT_2` | `SPRINT_2` | Não aplicável no Sprint 1. |
| **DD-79** | Limiares numéricos de tolerância a gaps e detecção de outliers | `FUTURE_POLICY` | `MAY_DECIDE_DURING_SPRINT_1` | `SPRINT_1_MARKET_OBSERVER` | `DERIVED_FROM_ROADMAP` | `SPRINT_1` | `SPRINT_2` | Aplicável para emissão de evidência de qualidade no Sprint 1. |
| **DD-80** | Estratégia e algoritmo de tratamento de dados faltantes (imputação/descarte) | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_2_MARKET_DATA_PLATFORM` | `DERIVED_FROM_ROADMAP` | `SPRINT_2` | `SPRINT_2` | O Sprint 1 registra gaps como UNKNOWN sem imputação. |
| **DD-81** | Algoritmos de emenda e ajuste de séries históricas contínuas | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_2_MARKET_DATA_PLATFORM` | `DERIVED_FROM_ROADMAP` | `SPRINT_2` | `SPRINT_2` | Não aplicável no Sprint 1. |
| **DD-82** | Formato físico de persistência de datasets de pesquisa (Parquet/DuckDB) | `IMPLEMENTATION_DETAIL` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_2_MARKET_DATA_PLATFORM` | `DERIVED_FROM_ROADMAP` | `SPRINT_2` | `SPRINT_2` | Não aplicável no Sprint 1. |
| **DD-83** | Tecnologia de hashing e versionamento de datasets (DVC/content-hash) | `IMPLEMENTATION_DETAIL` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_2_MARKET_DATA_PLATFORM` | `DERIVED_FROM_ROADMAP` | `SPRINT_2` | `SPRINT_2` | Não aplicável no Sprint 1. |
| **DD-84** | Datas e intervalos de particionamento temporal OOS (treino/val/teste) | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-85** | Configuração de janelas de treino/teste (expanding vs rolling) | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-86** | Número de splits e folds em validação walk-forward | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-87** | Método e horizonte temporal de purging em validação cruzada | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-88** | Método e duração de embargo para independência temporal | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-89** | Algoritmos de segmentação e detecção de regimes de mercado | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_6_SCENARIO_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_6` | Não aplicável no Sprint 1. |
| **DD-90** | Catálogo de baselines de referência para validação OOS | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-91** | Limiares numéricos de estabilidade de desempenho entre folds | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-92** | Resolução temporal de simulação de backtest (ticks vs trades vs candles) | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_3_BACKTESTING_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_3` | Não aplicável no Sprint 1. |
| **DD-93** | Tabela de taxas de negociação, registro e emolumentos B3 | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_3_BACKTESTING_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_3` | Não aplicável no Sprint 1. |
| **DD-94** | Modelo matemático de estimativa de slippage na simulação | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_3_BACKTESTING_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_3` | Não aplicável no Sprint 1. |
| **DD-95** | Modelo de latência de transmissão e processamento em simulação | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_3_BACKTESTING_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_3` | Não aplicável no Sprint 1. |
| **DD-96** | Algoritmo de simulação de prioridade de fila de ordens no book | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_3_BACKTESTING_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_3` | Não aplicável no Sprint 1. |
| **DD-97** | Função de impacto de mercado para simulação de grandes volumes | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_3_BACKTESTING_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_3` | Não aplicável no Sprint 1. |
| **DD-98** | Regras de liquidação mandatória de posições no fim do pregão simulado | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_3_BACKTESTING_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_3` | Não aplicável no Sprint 1. |
| **DD-99** | Biblioteca ou engine físico de simulação causal de backtest | `IMPLEMENTATION_DETAIL` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_3_BACKTESTING_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_3` | Não aplicável no Sprint 1 (desenvolvimento no Sprint 3). |
| **DD-100** | Especificação de estimands formais em testes de hipótese estatística | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-101** | Seleção de métricas primárias e secundárias do EvaluationVector | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-102** | Níveis de significância estatística (alpha) e intervalos de confiança | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-103** | Escolha de metodologia de inferência estatística (bootstrap vs bayesiano) | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-104** | Tamanho de blocos para bootstrap em séries temporais dependentes | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-105** | Métodos de controle de multiplicidade (Bonferroni, Holm, FDR, White RC) | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-106** | Limiares mínimos de métricas ajustadas ao risco para promoção (Sharpe) | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_11_PRE_PRODUCTION_AUDIT` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_11` | Não aplicável no Sprint 1. |
| **DD-107** | Parâmetros de corte para métricas de risco de cauda (VaR e ES 95%/99%) | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_7` | Não aplicável no Sprint 1. |
| **DD-108** | Grade de parâmetros para testes de sensibilidade e perturbação de custos | `FUTURE_POLICY` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_3` | `SPRINT_4` | Não aplicável no Sprint 1. |
| **DD-109** | Catálogo de métricas preditivas por arquitetura de modelo de ML | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_5_ML_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_5` | `SPRINT_5` | Não aplicável no Sprint 1. |
| **DD-110** | Limiares mínimos de calibração (Brier) e discriminação (AUC) | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_5_ML_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_5` | `SPRINT_5` | Não aplicável no Sprint 1. |
| **DD-111** | Limiares de ativação de sinais e regras de dimensionamento de estratégia | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_4_STATISTICAL_BASELINES` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_5` | Não aplicável no Sprint 1. |
| **DD-112** | Critérios formais de penalização de complexidade algorítmica | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_5_ML_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_4` | `SPRINT_5` | Não aplicável no Sprint 1. |
| **DD-113** | Critérios quantitativos de detecção de model drift e strategy decay | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_5_ML_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_5` | `SPRINT_8` | Não aplicável no Sprint 1. |
| **DD-114** | Formato físico e schema de armazenamento de Model Cards | `IMPLEMENTATION_DETAIL` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_5_ML_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_5` | `SPRINT_5` | Não aplicável no Sprint 1. |
| **DD-115** | Requisitos de duração mínima e número de trades para Paper Trading | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_8_PAPER_TRADER` | `DERIVED_FROM_ROADMAP` | `SPRINT_8` | `SPRINT_8` | Não aplicável no Sprint 1. |
| **DD-116** | Limiares de tolerância a discrepâncias estatísticas Backtest vs Paper | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_8_PAPER_TRADER` | `DERIVED_FROM_ROADMAP` | `SPRINT_8` | `SPRINT_8` | Não aplicável no Sprint 1. |
| **DD-117** | Tolerâncias máximas aceitáveis de latência e slippage em Paper Trading | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_8_PAPER_TRADER` | `DERIVED_FROM_ROADMAP` | `SPRINT_8` | `SPRINT_8` | Não aplicável no Sprint 1. |
| **DD-118** | Prazos de validade temporal e políticas de expiração de promoção | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_11_PRE_PRODUCTION_AUDIT` | `DERIVED_FROM_ROADMAP` | `SPRINT_8` | `SPRINT_11` | Não aplicável no Sprint 1. |
| **DD-119** | Critérios de parada de emergência e interrupção em Paper Trading | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_8_PAPER_TRADER` | `DERIVED_FROM_ROADMAP` | `SPRINT_8` | `SPRINT_8` | Não aplicável no Sprint 1. |
| **DD-120** | Formato físico de relatórios de auditoria e monitoramento de Paper Trading | `IMPLEMENTATION_DETAIL` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_8_PAPER_TRADER` | `DERIVED_FROM_ROADMAP` | `SPRINT_8` | `SPRINT_8` | Não aplicável no Sprint 1. |
| **DD-121** | Limites quantitativos de exposição e perda máxima diária (daily loss) | `FUTURE_POLICY` | `MUST_REMAIN_UNDECIDED_NOW` | `SPRINT_7_RISK_ENGINE` | `DERIVED_FROM_ROADMAP` | `SPRINT_7` | `SPRINT_8` | Não aplicável no Sprint 1 (sem risco econômico). |
| **DD-122** | Framework e tecnologia de dashboard operacional intradiário | `IMPLEMENTATION_DETAIL` | `MAY_DEFER_BEYOND_SPRINT_1` | `SPRINT_10_DASHBOARD` | `DERIVED_FROM_ROADMAP` | `SPRINT_8` | `SPRINT_10` | Não aplicável no Sprint 1. |
| **DD-123** | Automação de trading por cliques na interface do BTG Trader | `OUT_OF_SCOPE` | `MUST_REMAIN_UNDECIDED_NOW` | `NONE` | `ASSIGNED_BY_0F_B` | `NONE` | `NONE` | Fora de escopo (Plano Mestre 4.2: 'automação de trading por cliques na interface do BTG Trader'). |
| **DD-124** | HFT de microssegundos | `OUT_OF_SCOPE` | `MUST_REMAIN_UNDECIDED_NOW` | `NONE` | `ASSIGNED_BY_0F_B` | `NONE` | `NONE` | Fora de escopo (Plano Mestre 4.2: 'HFT de microssegundos'). |

---

## 4. Análise de Falsas Dependências e Desacoplamento do Sprint 1

| Falsa Dependência Identificada | Análise Técnica e Desacoplamento | Veredito |
|:---|:---|:---|
| *"Não há banco de dados escolhido"* | A decisão concreta sobre o mecanismo físico de persistência inicial pode ser tomada durante o Sprint 1, antes da primeira capability que dependa materialmente dela, observando a separação lógica de planos (ADR-0018). O banco de dados de produção pertence ao Sprint 2. | **FALSA DEPENDÊNCIA** — Não bloqueia |
| *"Não há ticker/ativo congelado"* | O Observer implementa discovery de instrumentos e configuração de subscription por parâmetro. O ativo é detalhe de configuração runtime (ADR-0005). | **FALSA DEPENDÊNCIA** — Não bloqueia |
| *"Não há provedor pré-escolhido"* | A interface `MarketDataProvider` é baseada em capacidades declaradas (ADR-0006). A escolha concreta do adapter (ex.: MT5 read-only vs vendor) pode ser tomada durante o Sprint 1 via ADR de implementação. | **FALSA DEPENDÊNCIA PRÉVIA** — Não bloqueia abertura |
| *"Não há formato de serialização definido"* | O formato de serialização de eventos (DD-02) é encapsulado pelo envelope e pode ser resolvido durante a implementação do Sprint 1. | **FALSA DEPENDÊNCIA** — Não bloqueia |
| *"Não há calendário B3 codificado"* | A decisão concreta sobre a implementação de calendário pode ser tomada durante o Sprint 1 para parametrização do Observer, evoluindo no Sprint 2. | **FALSA DEPENDÊNCIA** — Não bloqueia |
| *"Não há bibliotecas de ML"* | O Sprint 1 é estritamente read-only e não consome modelos de ML. Bibliotecas de ML pertencem ao Sprint 5. | **FALSA DEPENDÊNCIA TOTAL** — Irrelevante |
| *"Não há limites de risco diário"* | O Sprint 1 não aloca capital e não executa ordens. O Risk Engine pertence ao Sprint 7. | **FALSA DEPENDÊNCIA TOTAL** — Irrelevante |

---

## 5. Achados e Ações Prévias ao Sprint 1 (Findings)

### Achados Documentais de 0F-B:
1. **F-01 — Referência obsoleta a "Sprint 0" em config/README.md:**  
   - **Localização:** [`config/README.md`](file:///c:/Projetos/btg-ai-trader/config/README.md) L12 ("O formato e o mecanismo de validação serão escolhidos no Sprint 0").
   - **Diagnóstico:** O Sprint 0 (0A–0E) fechou sem instanciar schemas físicos de configuração. A frase deve ser atualizada para referenciar o sprint de implementação correspondente (Sprint 1), evitando falso compromisso não cumprido.
   - **Classificação:** `PRE_SPRINT1_ACTION` (não bloqueante).

2. **F-02 — Referência em README.md a escolha de bibliotecas no Sprint 0:**  
   - **Localização:** [`README.md`](file:///c:/Projetos/btg-ai-trader/README.md) L48–49.
   - **Diagnóstico:** Já identificado no bloco 0F-A como **A-F02**. Mantido em tracking unificado.

---

## 6. Governança de Owners e Stages (Provenance)

- **Total de Decisões Normalizadas:** 124
- **OWNER_STAGE_EXPLICIT_IN_SOURCE_ITEM:** 0 (a baseline histórica registrou apenas que permaneciam adiadas sem designar owner/stage nominais)
- **OWNER_STAGE_DERIVED_FROM_BASELINE_ROADMAP:** 121 (derivadas formalmente das responsabilidades e escopos dos Sprints 1 a 12 e Gates A a G do Plano Mestre)
- **OWNER_STAGE_ASSIGNED_BY_0F_B:** 3 (DD-66 Git remoto e DD-123/DD-124 Out of Scope atribuídos como governança pelo gate 0F-B)
- **OWNER_STAGE_UNRESOLVED:** 0 (todas as 124 decisões possuem estágio e responsável de resolução definidos)

---

## 7. Reconciliação Aritmética e Totais Consolidados

### A. Verificação de Soma por EPISTEMIC_CLASS:
- `UNDECIDED_AND_BLOCKING`: **0**
- `DELIBERATELY_DEFERRED`: **24**
- `IMPLEMENTATION_DETAIL`: **24**
- `FUTURE_POLICY`: **74**
- `OUT_OF_SCOPE`: **2**
- **Soma das Classes Epistemológicas:** 0 + 24 + 24 + 74 + 2 = **124** ✅

### B. Verificação de Soma por TIMING_CLASS:
- `MUST_DECIDE_BEFORE_SPRINT_1`: **0**
- `MAY_DECIDE_DURING_SPRINT_1`: **26**
- `MAY_DEFER_BEYOND_SPRINT_1`: **50**
- `MUST_REMAIN_UNDECIDED_NOW`: **48**
- **Soma das Classes Temporais:** 0 + 26 + 50 + 48 = **124** ✅

### C. Verificação de Soma por OWNER_STAGE_SOURCE:
- `OWNER_STAGE_EXPLICIT_IN_SOURCE_ITEM`: **0**
- `OWNER_STAGE_DERIVED_FROM_BASELINE_ROADMAP`: **121**
- `OWNER_STAGE_ASSIGNED_BY_0F_B`: **3**
- **Soma das Fontes de Governança:** 0 + 121 + 3 = **124** ✅

### D. Consistência Cruzada e Integridade Relacional:
- Cada uma das 124 decisões normalizadas possui **exatamente uma** classe epistemológica, **exatamente uma** classe temporal e **exatamente uma** fonte de governança.
- Todos os 141 itens brutos das seções de deferimento estão 100% cobertos (`SOURCE_ITEMS_UNCOVERED = 0`).
- Nenhuma decisão normalizada sem fonte mapeada (`NORMALIZED_DECISIONS_WITHOUT_SOURCE = 0`).
- Nenhuma decisão não classificada (`UNCLASSIFIED_DECISIONS = 0`).
- Nenhuma decisão com estágio não resolvido (`OWNER_STAGE_UNRESOLVED = 0`).

---

## 8. Relatório do Quality Check Automático

```text
============================================================
0F-B AUTOMATED QUALITY CHECK REPORT
============================================================
TOTAL_SOURCE_DEFERRED_ITEMS                 = 141
TOTAL_NORMALIZED_DECISIONS                  = 124

-- EPISTEMIC CLASSIFICATION --
UNDECIDED_AND_BLOCKING                      = 0
DELIBERATELY_DEFERRED                       = 24
IMPLEMENTATION_DETAIL                       = 24
FUTURE_POLICY                               = 74
OUT_OF_SCOPE                                = 2
SUM_EPISTEMIC_CLASS                         = 124  [MATCH]

-- TIMING CLASSIFICATION --
MUST_DECIDE_BEFORE_SPRINT_1                 = 0
MAY_DECIDE_DURING_SPRINT_1                  = 26
MAY_DEFER_BEYOND_SPRINT_1                   = 50
MUST_REMAIN_UNDECIDED_NOW                   = 48
SUM_TIMING_CLASS                            = 124  [MATCH]

-- GOVERNANCE & PROVENANCE --
OWNER_STAGE_EXPLICIT_IN_SOURCE_ITEM         = 0
OWNER_STAGE_DERIVED_FROM_BASELINE_ROADMAP   = 121
OWNER_STAGE_ASSIGNED_BY_0F_B                = 3
OWNER_STAGE_UNRESOLVED                      = 0
SUM_OWNER_STAGE_SOURCE                      = 124  [MATCH]

-- INTEGRITY & COVERAGE --
SOURCE_ITEMS_UNCOVERED                      = 0    [PASS]
NORMALIZED_DECISIONS_WITHOUT_SOURCE         = 0    [PASS]
UNCLASSIFIED_DECISIONS                      = 0    [PASS]
HARD_BLOCKERS                               = 0    [PASS]
PRE_SPRINT1_ACTIONS_NEW                     = 1    [TRACKED]

REOPEN_0C                                   = NO
REOPEN_0D                                   = NO
REOPEN_0E                                   = NO
============================================================
```

---

## 9. Veredito Proposto do Bloco 0F-B

```text
PROPOSED_0F-B_RESULT = PASS_WITH_PRE_SPRINT1_ACTIONS

0F-B_APPROVAL = PENDING_COORDINATION_REVIEW
0F-C = NOT_STARTED
SPRINT_1 = NOT_STARTED
```
