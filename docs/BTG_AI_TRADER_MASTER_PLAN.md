# BTG AI Trader — Plano Mestre Vivo

**Documento de referência principal do projeto**
**Status:** ativo e evolutivo
**Última consolidação:** 2026-08-20
**Repositório local:** `C:\Projetos\btg-ai-trader`
**Projeto ChatGPT:** `BTG AI Trader`

---

## 1. Finalidade deste documento

Este arquivo é a referência transversal do projeto **BTG AI Trader**. Ele existe para evitar perda de contexto entre Chat, Codex, Work, branches, sprints, revisões e futuras mudanças de arquitetura.

Ele deve:

1. registrar o objetivo e os limites do projeto;
2. preservar decisões arquiteturais de alto nível;
3. registrar o estado atual do desenvolvimento;
4. definir a sequência de sprints e gates;
5. orientar o uso de Chat, Codex e Work;
6. impedir que decisões críticas fiquem apenas no histórico de conversas;
7. ser atualizado quando uma decisão relevante for alterada;
8. apontar para ADRs, protocolos e documentos especializados quando o detalhe ultrapassar o escopo deste plano mestre.

Este documento **não substitui** `AGENTS.md`, ADRs, protocolos, testes, documentação de arquitetura nem Model Cards. Ele funciona como mapa geral e fonte de continuidade.

---

# 2. Visão do produto

Desenvolver um sistema privado de **trading quantitativo intradiário**, inicialmente voltado a operações de curtíssimo prazo em instrumentos líquidos da B3 e conectado futuramente à conta do usuário no BTG por infraestrutura oficialmente suportada, com **MetaTrader 5 como candidato inicial de ponte de mercado/execução**.

O sistema deverá combinar:

- dados de mercado em tempo real;
- engenharia de atributos;
- identificação de regime de mercado;
- modelos estatísticos e de machine learning;
- avaliação probabilística de cenários;
- geração de sinais;
- dimensionamento de posição;
- gestão independente de risco;
- execução auditável;
- paper trading;
- backtesting/replay;
- monitoramento;
- reconciliação após falhas;
- operação em nuvem no estágio apropriado.

O foco inicial é **trading intradiário em horizonte de minutos**, e não alocação de carteira de médio/longo prazo.

---

# 3. Princípios não negociáveis

## 3.1. Segurança e preservação de capital

1. Preservação de capital tem precedência sobre maximização de retorno.
2. O sistema deve admitir `NO_TRADE` como resultado plenamente válido.
3. O **Risk Engine** deverá possuir poder absoluto de veto.
4. Nenhum modelo, Signal Engine ou componente de ML poderá enviar ordens diretamente.
5. Nenhum sistema poderá operar dinheiro real antes de gates formais de validação.
6. Deve existir fail-safe, watchdog e kill switch.
7. Em caso de incerteza operacional, a preferência é bloquear novas operações.

## 3.2. Integridade científica e quantitativa

1. Nenhum modelo pode ser promovido apenas por desempenho in-sample.
2. É obrigatória prevenção de:
   - look-ahead bias;
   - data leakage;
   - survivorship bias;
   - overfitting;
   - seleção retrospectiva oportunista.
3. Validação temporal fora da amostra é obrigatória.
4. Backtests devem incorporar, quando aplicável:
   - spread;
   - slippage;
   - taxas;
   - emolumentos;
   - liquidez;
   - latência;
   - limitações operacionais.
5. Accuracy não será métrica central isolada.
6. Métricas econômicas e de risco terão precedência sobre taxa bruta de acerto.

## 3.3. Engenharia e auditabilidade

1. Toda decisão relevante deve poder ser reconstruída.
2. Sinais, decisões, ordens, falhas e mudanças de modelo deverão ser auditáveis.
3. Mudanças arquiteturais importantes exigem ADR.
4. Componentes financeiros críticos devem possuir testes.
5. Credenciais e segredos nunca devem ser versionados.
6. Pesquisa, treinamento, backtesting, paper e produção devem permanecer logicamente separados.

---

# 4. Escopo inicial

## 4.1. Incluído

- B3.
- Trading intradiário.
- Horizonte prioritário de segundos a minutos, com ênfase inicial em candles/ticks de curta duração.
- Instrumentos líquidos.
- Primeiro laboratório provável: família WIN.
- Evolução posterior possível para WDO, ações e ETFs líquidos.
- Python como linguagem principal de pesquisa e backend.
- MetaTrader 5 como candidato inicial para integração com BTG.
- Infraestrutura local para desenvolvimento.
- Windows VM em nuvem para o futuro Trading Node.
- Modelos estatísticos e ML supervisionado como primeira linha.
- Paper trading antes de qualquer produção.
- Dashboard de monitoramento em etapa futura.

## 4.2. Fora do escopo inicial

- administração profissional de patrimônio de terceiros;
- venda do sistema como serviço financeiro;
- HFT de microssegundos;
- opções como primeiro mercado;
- alavancagem real na fase inicial;
- venda descoberta real na fase inicial;
- Reinforcement Learning como primeiro modelo produtivo;
- execução real antes dos gates;
- automação por cliques na interface do BTG Trader;
- dependência de um computador pessoal ligado durante produção.

---

# 5. Arquitetura-alvo de alto nível

A cadeia abaixo sintetiza a baseline lógica de 0C refinada pelos contratos congelados do Sprint 0D. Ela não constitui implementação nem autorização de operação real.

```text
MARKET / DATA SOURCE
        |
        v
RAW / CAPTURE EVIDENCE
        |
        v
QUALITY / ADMISSION
        |
        v
NORMALIZED MARKET EVENTS
        |
        +--------------------> EVIDENCE ARCHIVE / AUDIT
        |
        +--------------------> MONITORING
        |
        v
FEATURE / ANALYTICAL PIPELINE
        |
        v
SIGNAL ENGINE
        |
        v
StrategyDecision
   /            \
NO_TRADE     PROPOSE_TRADE
                  |
                  v
        InstrumentResolution?
                  |
                  v
             TradeIntent
                  |
                  v
             RISK ENGINE
            /           \
         REJECT        PERMIT
                         |
                         v
               RiskAuthorization
                         |
                         v
              AuthorizationAllocation
                         |
                         v
                  OrderIntent
                         |
                         v
                    OrderPlan
                         |
                         v
                ExecutionOrder(s)
                         |
                         v
                  EXECUTION ENGINE
                         |
                         v
                   EXTERNAL WORLD
```

## 5.1. Invariantes centrais

- `NO_TRADE` é resultado explícito de `StrategyDecision` e é distinto de `RiskDecision.REJECT`, `SAFE_HALT` e falha operacional.
- Todo `TradeIntent` apresentado ao Risk referencia um `TradableInstrument` concreto; `AnalyticalSeries` não chega a Risk/Execution como instrumento negociável.
- `RiskDecision` julga (`REJECT | PERMIT`); `RiskAuthorization` concede authority normativa limitada.
- Nenhum novo economic commitment pode contornar `RiskAuthorization` válida e `AuthorizationAllocation` suficiente.
- Somente Execution pode solicitar efeito externo e somente após satisfazer as authorities e os persistence gates aplicáveis.
- Nenhum modelo, Signal Engine ou Strategy possui authority para enviar ordem.

É arquiteturalmente proibido:

```text
ML Model -> Broker
Signal Engine -> order_send()
StrategyDecision -> Execution
RiskDecision -> external side effect
```

---

# 6. Baseline contratual consolidada até o Sprint 0D

## 6.1. StrategyDecision, TradeIntent e Risk

A estratégia materializa `StrategyDecision` com resultado semanticamente equivalente a `NO_TRADE` ou `PROPOSE_TRADE`. A ausência acidental de `TradeIntent` não é usada como substituto de `NO_TRADE`.

Quando a proposta ainda referencia subject não executável, `InstrumentResolutionDecision` resolve explicitamente para `TradableInstrument`. Todo `TradeIntent` apresentado ao Risk referencia instrumento concreto e contém `EconomicObjective` com semântica e unidade explícitas.

Exemplo conceitual:

```text
tradable_instrument: WINQ26
economic_objective:
    basis: EXPOSURE_DELTA
    direction: LONG
    magnitude: 1
    unit: CONTRACT
expected_horizon: ...
expected_return: ...
expected_downside: ...
```

Os nomes físicos, tipos Python e representação numérica permanecem deliberadamente não escolhidos.

`RiskDecision` possui semanticamente `REJECT | PERMIT`. `PERMIT` que possa habilitar efeito econômico downstream exige `RiskAuthorization`; antes de `OrderIntent`, uma `AuthorizationAllocation` reserva capacidade. O planejamento segue `OrderIntent → OrderPlan → ExecutionOrder`.

## 6.2. Commitment e execução

Criar `ExecutionAttempt` não constitui commitment por si só. Commitment ocorre na primeira fronteira após a qual o sistema já não consegue garantir ausência de side effect externo decorrente da tentativa. Outcome externo `UNKNOWN` permanece committed e exige reconciliation suficiente; timeout não autoriza blind retry.

Expiração de TradeIntent/authorization/allocation bloqueia novos commitments, mas não apaga obrigações já externalizadas.

## 6.3. Execution facts e reconhecimento financeiro

Mensagens externas podem normalizar em `OrderLifecycleObservation` e `FillObservation`. `FillObservation` não possui efeito financeiro direto.

A cadeia financeira é:

```text
FillObservation
→ identity / dedup / matching
→ canonical Fill
→ EconomicRecognitionIdentity
→ LedgerTransaction
→ 1..N LedgerPostings
→ Position / Cash / Valuation / P&L / Exposure projections
```

O mesmo fato econômico não pode produzir reconhecimento duplicado em restart ou reprocessing. Observações externas de Position/Cash não sobrescrevem as projeções internas e não geram automaticamente Fill ou Ledger adjustment.

## 6.4. Perfis operacionais

O núcleo é reutilizável por composição entre:

```text
REPLAY
BACKTEST
PAPER
LIVE
```

Os profiles variam providers, clock, execution/persistence/accounting counterparts, sem criar branches de domínio por modo. O Signal Engine não depende de saber se está em `BACKTEST` ou `LIVE`.

## 6.5. Semântica temporal e conhecimento

Quando aplicável, distinguem-se:

- `event_time`: tempo sustentado pela fonte externa, com basis/resolution quando disponível;
- `ingestion_time`: chegada efetiva ao sistema;
- effective/economic time e knowledge/recognition cutoffs conforme o domínio;
- tempos de processamento registrados por `ProcessingReceipt`/telemetria por componente, não como `processing_time` universal do evento.

Direção vigente:

- tempo interno absoluto em UTC quando aplicável;
- conversão explícita para `America/Sao_Paulo` onde calendário/regras de mercado exigirem;
- evitar `naive datetime`;
- conhecimento posterior ao cutoff não pode reescrever decisão histórica.

## 6.6. Instrumentos

Separar:

```text
InstrumentFamily: WIN
TradableInstrument: WINQ26
```

Rollover e selection são explícitos, versionados e auditáveis. Analytical series permanecem não executáveis.

## 6.7. Recovery, reconciliation e readiness

Recovery e reconciliation são processos distintos e scope-specific. Snapshot + journal só podem sustentar reconstrução quando continuity é demonstrável. Reconciliation afirma consistency apenas em relação a `ReconciliationObservationBoundary` explícito. Matching/lineage precede correction.

Recovery/reconciliation suficientes apenas removem seus blockers; não produzem `READY` automaticamente. `OperationalReadinessAssessment` avalia capabilities específicas.

## 6.8. Runtime e segurança

São semanticamente distintos:

```text
RuntimePhase
≠ SafetyPosture
≠ OperationalReadinessAssessment
```

`SAFE_HALT` é fail-closed para novos commitments, mas não implica auto-flatten. Liveness não equivale a readiness. Saída de postura latched exige prerequisites e authority explícitos.

## 6.9. Runs e provenance

`RunId` identifica uma execução computacional concreta. Restart cria novo `RunId`; continuidade é registrada por `RunRelation` tipada, como `RESUMES_FROM`. Run não é OperationalSession nem Experiment.

Fatos externos não exigem `run_id` intrínseco. `CaptureContext` registra o contexto de captura e pode referenciar o Run capturador; `ProcessingReceipt` registra processamento de um artifact em um Run/componente sem mutá-lo; `ArtifactLineageRecord` representa derivação separadamente.

Run boundary não é economic obligation boundary: obrigações committed antes de crash sobrevivem ao Run e precisam ser reconstruídas/controladas/reconciliadas no Run posterior.

## 6.10. Persistence

Persistência lógica separa `EvidenceArchive`, `AuditJournal` e snapshots. AuditJournal não é Ledger; snapshot é projeção derivada e nunca substitui/corrige journal.

Para novo side effect capaz de criar/ampliar economic commitment, os critical records exigidos pela policy devem satisfazer os `DurabilityRequirement`s antes do dispatch externo. Esse persist-before-act não pressupõe transação ACID distribuída com broker/venue.

---

# 7. Machine Learning — orientação inicial

## 7.1. Não iniciar pelo modelo mais complexo

Sequência preferencial:

1. baseline aleatório;
2. regressão logística;
3. Random Forest;
4. Gradient Boosting;
5. XGBoost/LightGBM;
6. modelos temporais mais complexos apenas se houver ganho robusto;
7. RL somente como linha experimental futura.

## 7.2. Possíveis famílias de modelos

- direção;
- magnitude do retorno;
- adverse excursion;
- regime;
- meta-model para avaliar confiabilidade dos sinais;
- volatilidade;
- cenário.

## 7.3. Meta-labeling

Um sinal primário poderá ser filtrado por um segundo modelo:

```text
Signal Model -> LONG
Meta Model   -> confiança insuficiente
Resultado    -> NO_TRADE
```

---

# 8. Features candidatas futuras

Nenhuma destas features está aprovada como obrigatória; são linhas de investigação.

## 8.1. Preço

- retorno 30s/1m/5m/15m;
- momentum;
- aceleração;
- distância da VWAP;
- breakout;
- máxima/mínima intraday;
- gaps.

## 8.2. Volume

- volume absoluto;
- volume relativo ao horário;
- delta;
- volume acumulado;
- volume por faixa de preço.

## 8.3. Volatilidade

- realized volatility;
- ATR intraday;
- range;
- compressão/expansão.

## 8.4. Microestrutura

- bid;
- ask;
- spread;
- profundidade;
- imbalance;
- agressões compradoras/vendedoras;
- mudanças no book.

Exemplo conceitual de Order Book Imbalance:

```text
OBI = (Q_bid - Q_ask) / (Q_bid + Q_ask)
```

---

# 9. Avaliação de cenários e risco

O projeto deverá evoluir para avaliação probabilística, não apenas decisão binária.

Métricas candidatas:

- expected return;
- expected downside;
- Value at Risk;
- Expected Shortfall;
- drawdown;
- Sharpe;
- Sortino;
- Calmar;
- profit factor;
- expectancy;
- probabilidade de perda;
- probabilidade de ruína;
- slippage efetivo;
- latência efetiva.

Objetivo conceitual:

```text
maximizar retorno ajustado ao risco
```

e não maximizar simplesmente retorno bruto.

---

# 10. Infraestrutura

## 10.1. Desenvolvimento

Projeto local:

```text
C:\Projetos\btg-ai-trader
```

Estrutura atual:

```text
btg-ai-trader/
├── .gitignore
├── .python-version
├── AGENTS.md
├── README.md
├── pyproject.toml
├── config/
├── docs/
├── scripts/
├── src/
└── tests/
```

## 10.2. Produção futura

Direção preliminar:

```text
CLOUD
 |
 +-- Trading Node Windows
 |    +-- MetaTrader 5 / BTG
 |    +-- Execution Engine
 |    +-- Risk Engine
 |    +-- Watchdog
 |
 +-- AI / Research Node
 |    +-- treinamento
 |    +-- backtesting
 |    +-- otimização
 |    +-- Model Registry
 |
 +-- Database
 |
 +-- Dashboard / Telemetria
```

Treinamento pesado não deverá competir por recursos com a camada crítica de execução.

---

# 11. Estratégia de uso do ChatGPT, Codex e Work

## 11.1. Chat

Usar para:

- arquitetura;
- discussão conceitual;
- diagnóstico;
- metodologia quantitativa;
- análise de risco;
- avaliação de resultados;
- decisões;
- revisão crítica.

Política:

```text
Instant -> rotina
Medium  -> engenharia e análise normal
High    -> arquitetura, risco, metodologia e decisões críticas
```

## 11.2. Codex

Usar para:

- implementar;
- editar;
- testar;
- refatorar;
- executar comandos;
- criar arquivos;
- manter Git.

Política econômica:

```text
Luna  -> tarefas determinísticas, mecânicas e bem especificadas
Terra -> implementação cotidiana e mudanças multiarquivo
Sol   -> bugs difíceis, código crítico, arquitetura ambígua ou auditoria técnica
```

## 11.3. Work

Usar excepcionalmente.

Adequado para:

- integração transversal de muitos artefatos;
- auditoria de grandes marcos;
- consolidação de arquitetura/documentação;
- tarefas realmente multi-etapa e agentivas.

Princípio:

```text
Chat  -> abundante
Codex -> cirúrgico
Work  -> excepcional
```

---

# 12. Fonte de verdade

A hierarquia deverá ser:

```text
1. Código e testes do repositório
2. ADRs e protocolos versionados
3. AGENTS.md
4. Este Plano Mestre
5. Conversas do ChatGPT
```

Conversas são espaços de raciocínio, não devem ser a única fonte de decisões permanentes.

---

# 13. Git e GitHub

## 13.1. Estado atual

- Git local inicializado.
- Branch local: `main`.
- Baseline 0A/0B preparada para versionamento.
- Autor Git configurado localmente.
- Commit de sincronização normativa do Sprint 0D: `c7e3b24` — `docs: finalize Sprint 0D normative synchronization`.
- Após esse commit, a árvore canônica local foi verificada com `git status` limpo.
- Repositório remoto ainda não é requisito para avançar a arquitetura.

## 13.2. Política futura

- GitHub privado;
- branches por feature/experimento quando necessário;
- nenhuma credencial versionada;
- commits pequenos e semanticamente coerentes;
- evitar misturar arquitetura, dependências e implementação não relacionada no mesmo commit.

---

# 14. Estado atual do Sprint 0

```text
SPRINT 0 — FUNDAÇÃO

0A — Bootstrap estrutural              ✅ CONCLUÍDO/APROVADO
0B — Ambiente de desenvolvimento       ✅ CONCLUÍDO/APROVADO
Baseline Git                           ✅ CONFIGURADA/VALIDADA
0C — Arquitetura lógica                ✅ CONCLUÍDO/APROVADO
Baseline arquitetural                 ✅ ADR-0002 a ADR-0014 + refinamentos 0015–0022
0D-A a 0D-E                           ✅ FECHADOS/CONGELADOS
0D-F — Cross-contract Gate            ✅ APROVADO
Sincronização normativa 0D            ✅ CONCLUÍDA — ADRs 0015–0022
F1 final de consistência documental   ✅ APROVADO
Commit de sincronização 0D            ✅ `c7e3b24`
Sprint 0D                             ✅ FORMALMENTE FECHADO/APROVADO
0E-A a 0E-G                           ✅ FECHADOS/CONGELADOS
0E-H — Cross-Protocol Gate            ✅ APROVADO (PASS)
Sincronização documental 0E           ✅ CONCLUÍDA
Gate final de consistência documental ⏳ PENDENTE
Sprint 0E                             🟠 NÃO FECHADO FORMALMENTE AINDA
0F — Gate do Sprint 0                 ⏳ NÃO INICIADO
```

---

# 15. Resultado da etapa 0A

Criados:

```text
.gitignore
AGENTS.md
README.md
pyproject.toml
config/
docs/
scripts/
src/
tests/
```

Decisões registradas:

- Risk Engine independente;
- `NO_TRADE` válido;
- pesquisa e execução separadas;
- prevenção de leakage;
- validação fora da amostra;
- paper trading obrigatório;
- ADRs para decisões relevantes;
- nenhuma integração financeira nesta fase.

---

# 16. Resultado da etapa 0B

## Dependências de desenvolvimento

```text
pytest==8.3.5
pytest-cov==6.0.0
ruff==0.11.0
mypy==1.15.0
hatchling==1.27.0
```

Nenhuma dependência financeira ou de trading adicionada.

## Verificações aprovadas

```text
pip check       ✅
pytest          ✅
coverage        ✅ 100% do pacote estrutural atual
Ruff            ✅
mypy            ✅
compileall      ✅
git diff check  ✅
segredos        ✅ nenhum padrão identificado
BTG/MT5         ✅ inexistentes
ordens          ✅ inexistentes
```

Observação: a cobertura de 100% ainda não é uma métrica substantiva, pois o pacote possui apenas estrutura mínima.

## Pendências

- validar Python 3.12 contra MetaTrader 5 e futuras dependências críticas antes de congelá-lo definitivamente;
- validar instalação em um Python 3.12 Windows padrão completamente isolado;
- formalizar a decisão em ADR no momento apropriado.

---

# 17. Sprint 0C — Arquitetura lógica

A baseline lógica foi fechada e materializada nos ADRs 0002–0014. Ela adota monólito modular orientado a eventos; envelope versionado com causalidade e ordenação contextual; UTC, relógio monotônico e fidelidade histórica declarada; identidade de instrumentos separada de referências de provider; rollover explícito; contratos de MarketDataProvider baseados em capacidades; intents e fronteiras independentes entre Signal, Risk e Execution; perfis de composição para Replay/Backtest/Paper/Live; determinismo de Backtest; persistência em archive, journal e snapshots; recovery/reconciliation fail-closed; estados de fail-safe; tratamento auditável de eventos inválidos; observabilidade, provenance e `run_id`; e ownership explícito de Ledger, Position/Portfolio e exposição.

As 26 decisões permanecem identificáveis individualmente: 0C-01 arquitetura modular; 0C-02 envelope e causalidade; 0C-03 semântica temporal; 0C-04 ordenação contextual e fidelidade; 0C-05 desordem limitada; 0C-06 identidades de instrumento; 0C-07 rollover; 0C-08 resolução de instrumento antes de Risk; 0C-09 Signal informacional; 0C-10 TradeIntent imutável; 0C-11 RiskDecision; 0C-12 Order Planning; 0C-13 expiração de autorização; 0C-14 provider por capacidades; 0C-15 at-least-once/idempotência; 0C-16 backpressure; 0C-17 perfis de composição; 0C-18 determinismo; 0C-19 três planos de persistência; 0C-20 recovery antes de READY; 0C-21 reconciliação para resultado desconhecido; 0C-22 fail-safe explícito; 0C-23 eventos inválidos; 0C-24 erros críticos; 0C-25 ownership de posição/exposição; e 0C-26 provenance e `run_id`.

Na conclusão histórica do 0C ainda não haviam sido escolhidos schema, interfaces Python, armazenamento físico, tecnologia de mensageria, calendário concreto, tolerâncias, mecanismo de reserva ou integração externa. O Sprint 0C permanece formalmente concluído e aprovado. Posteriormente, o Sprint 0D refinou semanticamente a baseline por meio dos ADRs 0015–0022, sem escolher tecnologia física, e foi formalmente fechado em 2026-08-19 após aprovação do F1 final de consistência normativa/documental.

---

# 18. Roadmap macro

## Sprint 0 — Fundação

- estrutura;
- ambiente;
- arquitetura;
- contratos;
- protocolos;
- gates.

## Sprint 1 — Market Observer

Somente leitura.

Objetivo:

- conectar futuramente a uma fonte de mercado;
- descobrir símbolos;
- receber ticks;
- receber candles;
- registrar dados;
- medir heartbeat e latência;
- nenhuma ordem.

## Sprint 2 — Market Data Platform

- normalização;
- armazenamento;
- qualidade;
- proveniência;
- replay.

## Sprint 3 — Backtesting Engine

- replay determinístico;
- custos;
- spread;
- slippage;
- métricas;
- testes de leakage.

## Sprint 4 — Statistical Baselines

- estratégias e modelos simples;
- benchmarks;
- calibração;
- out-of-sample.

## Sprint 5 — ML Engine

- feature pipeline;
- model registry;
- treino/validação;
- comparação de modelos.

## Sprint 6 — Scenario Engine

- regimes;
- cenários;
- stress;
- distribuição de resultados.

## Sprint 7 — Risk Engine

- limites;
- sizing;
- circuit breakers;
- veto;
- drawdown;
- daily loss;
- fail-safe.

## Sprint 8 — Paper Trader

- mercado real;
- decisões reais;
- dinheiro fictício;
- registro completo.

## Sprint 9 — Cloud Trading Node

- Windows VM;
- watchdog;
- reconciliação;
- observabilidade;
- segurança operacional.

## Sprint 10 — Dashboard

- status;
- posições;
- P&L;
- risco;
- pause;
- kill switch;
- alertas.

## Sprint 11 — Auditoria pré-produção

- segurança;
- estatística;
- performance;
- recovery;
- risco;
- compliance operacional.

## Sprint 12 — Produção mínima controlada

Somente se todos os gates forem cumpridos.

---

# 19. Gates de evolução

## Gate A — Dados

- timestamps válidos;
- ausência de gaps inexplicados;
- reconexão validada;
- proveniência registrada;
- qualidade mensurada.

## Gate B — Backtester

- determinismo;
- ausência de leakage;
- custos modelados;
- replay reproduzível;
- testes automatizados.

## Gate C — Modelo

- validação fora da amostra;
- walk-forward;
- benchmark;
- calibração;
- estabilidade;
- custos líquidos.

## Gate D — Paper

- número mínimo de pregões e oportunidades de decisão;
- comportamento e distribuição estatística compatíveis com o backtest;
- discrepância de execução observável no perfil Paper com proveniência declarada (refinando "slippage observado");
- estabilidade operacional e ausência de erros críticos;
- decisões prospectivas não financiadas (non-funded) sem equivalência automática a Live.

## Gate E — Risk Engine

- avaliação da suficiência pré-produção completa do Risk Engine (a authority e a fronteira independente de Risk existem na baseline desde 0C/0D, a capability necessária ao Paper deve ser implementada antes do Sprint 8, e o Gate E audita a suficiência final pré-produção);
- veto testado e poder de veto independente;
- circuit breakers e limites de perda diária (daily loss);
- position limits e limites de exposição da carteira;
- kill switch e fail-safe integrados.

## Gate F — Recovery

- restart;
- reconciliação;
- ordens pendentes;
- estado divergente;
- falha de rede;
- falha de dados.

## Gate G — Produção

Somente após revisão formal e aprovação explícita.

---

# 20. Políticas proibitivas até novo gate

Até autorização expressa:

```text
PROIBIDO:
- order_send() produtivo
- dinheiro real
- habilitar negociação automática
- armazenar chave ou senha no Git
- conectar modelo diretamente ao broker
- implementar lógica que contorne o Risk Engine
- ativar alavancagem real
- promover modelo sem validação
```

---

# 21. Política de atualização deste Plano Mestre

Este arquivo é **vivo**.

Atualizar quando ocorrer:

- mudança de escopo;
- nova decisão arquitetural relevante;
- aprovação ou rejeição de tecnologia;
- encerramento de sprint;
- mudança de gate;
- alteração da infraestrutura-alvo;
- descoberta que invalide premissa anterior;
- entrada de nova classe de ativo;
- mudança significativa na estratégia de uso de Chat/Codex/Work.

## 21.1. Como atualizar

Preferência:

1. registrar decisão específica em ADR/protocolo;
2. atualizar este Plano Mestre com a síntese;
3. atualizar status/roadmap;
4. registrar no changelog do repositório;
5. fazer commit.

## 21.2. Nunca fazer

- apagar silenciosamente uma decisão anterior relevante;
- reescrever histórico para parecer que a decisão atual sempre existiu;
- alterar gate sem justificativa;
- promover hipótese experimental a regra permanente sem evidência.

---

# 22. Registro de mudanças do Plano Mestre

## 2026-08-17 — versão inicial consolidada

Consolidação do planejamento realizado até o fim das etapas 0A e 0B.

Inclui:

- visão do produto;
- arquitetura preliminar;
- política de risco;
- estratégia quantitativa;
- infraestrutura;
- estratégia Chat/Codex/Work;
- estado do desenvolvimento;
- roadmap;
- gates;
- próximos passos.

## 2026-08-18 — baseline documental do Sprint 0C

Criados ADRs 0002–0014 para materializar as decisões 0C-01 a 0C-26. A arquitetura lógica está documentada e aguarda gate final de consistência e aprovação humana antes de abrir 0D. Nenhum código funcional, dependência, integração de mercado/corretora ou capacidade de negociação foi adicionada.

## 2026-08-18 — fechamento formal do Sprint 0C

Após revisão da baseline documental e aprovação humana, o Sprint 0C — Arquitetura Lógica foi marcado como concluído e aprovado. Os ADRs 0002–0014 constituem a baseline arquitetural vigente. A próxima etapa oficial é o Sprint 0D — Contratos e Modelo de Dados; nenhuma implementação de 0D foi iniciada.

## 2026-08-19 — sincronização normativa/documental do Sprint 0D

Os blocos 0D-A a 0D-E foram fechados e congelados, e o 0D-F — Cross-contract Gate foi tecnicamente aprovado sem blocker arquitetural. A auditoria textual integral dos ADRs 0002–0014 identificou deltas normativos específicos, documentados de forma append-only nos ADRs 0015–0022, preservando as decisões históricas de 0C.

A sincronização atualiza também AGENTS.md, o índice de ADRs, a visão de arquitetura, este Plano Mestre e o documento do Sprint 0. Nenhum código funcional, integração financeira, capacidade de negociação ou tecnologia física foi introduzido. O Sprint 0D permanece ainda não formalmente fechado: falta rerodar exclusivamente o gate F1 de consistência entre ADRs e documentação. O Sprint 0E não foi iniciado.

## 2026-08-19 — fechamento formal do Sprint 0D

O F1 final de consistência normativa/documental foi executado sobre a baseline sincronizada e aprovado sem `CURRENT_NORM_CONFLICT`. Foram confirmadas as relações de refinement 0003→0015, 0007→0016, 0008→0017, 0009→0018, 0010→0019, 0011→0020, 0013→0021 e 0014→0022; ADRs 0001–0022 permanecem contínuos e indexados; documentos vivos estão coerentes com a norma vigente; nenhuma decisão física nova ou capacidade financeira foi introduzida.

Com isso, o Sprint 0D — Contratos e Modelo de Dados é formalmente marcado como concluído e aprovado. A sincronização normativa foi consolidada no commit local `c7e3b24` (`docs: finalize Sprint 0D normative synchronization`). Na árvore canônica local, `pytest`, Ruff, mypy, `compileall`, `pip check` e `git diff --cached --check` passaram; após o commit, `git status` confirmou `working tree clean`. O Sprint 0E permanece não iniciado.

## 2026-08-20 — sincronização normativa/documental do Sprint 0E

Os sub-blocos 0E-A a 0E-G foram tecnicamente fechados e o 0E-H — Cross-Protocol Gate foi aprovado (PASS). A especificação metodológica foi materializada em `docs/protocols/quantitative/` (0E-A a 0E-H) e documentada em `docs/sprints/SPRINT_0E.md`.

Foram formalizados 269 Hard Quantitative Invariants (HQIs) e consolidados sob 15 Invariantes Canônicos Transversais (QPI-01 a QPI-15) com rastreabilidade completa em `TRACEABILITY.md`. Foram resolvidos formalmente os achados documentais H-DOC-01 a H-DOC-06:
- H-DOC-01: Relação Paper × Risk esclarecida (a authority de Risk existe desde 0C/0D, a capability necessária ao Paper é implementada antes do Sprint 8 e o Gate E avalia a suficiência pré-produção completa do Risk Engine);
- H-DOC-02: "Slippage observado" em Paper refinado como discrepância observável qualificada pela proveniência da observação;
- H-DOC-03: Promoção quantitativa formalizada como progressão evidenciária, nunca autoridade de trading;
- H-DOC-04: Predicados de aplicabilidade (ApplicabilityPredicate) formalizados como não transformadores de HQI em policy;
- H-DOC-05: Canonicalização transversal dos 269 HQIs sob QPI-01 a QPI-15 em TRACEABILITY.md;
- H-DOC-06: Conceitos semânticos delimitados como metodológicos, sem constituir schemas físicos de runtime prematuros.

Nenhum código funcional, dependência, ativo, timeframe, modelo ou tecnologia física foi introduzido. O Sprint 0E permanece ainda não formalmente fechado, com o gate final de consistência documental pendente. O Sprint 0F permanece não iniciado.

## 2026-08-22 — fechamento formal do Sprint 0E

O gate final de consistência documental (`FINAL_0E_DOC_GATE`) foi executado e aprovado com sucesso (`PASS`) após a canonicalização estrita dos 269 HQIs e 15 QPIs contra o dossiê canônico. Foi removida a coluna individual de aplicabilidade em `TRACEABILITY.md`, preservando a regra transversal de que aplicabilidade não converte Hard Invariant em policy. A aprovação humana formal para o encerramento do Sprint 0E foi concedida em 2026-08-22.

Com isso, o Sprint 0E — Protocolos Quantitativos está formalmente concluído e aprovado. A baseline normativa é composta pelos ADRs 0001–0022 e pelos protocolos quantitativos 0E-A a 0E-H. O Sprint 0F permanece como próximo passo oficial (não iniciado).

---

# 23. Próxima ação oficial

**Sprint 0F — Gate do Sprint 0 (NEXT OFFICIAL STEP / NOT STARTED).**

O Sprint 0E está formalmente concluído e aprovado. Até a abertura explícita do Sprint 0F:

1. tratar ADRs 0001–0022 e os Protocolos Quantitativos 0E-A a 0E-H como baseline normativa vigente e congelada;
2. manter qualquer capacidade financeira real estritamente desabilitada;
3. não implementar integração BTG/MT5, execução, ordens ou dinheiro real;
4. manter as decisões físicas e numéricas deliberadamente adiadas fora da baseline até etapa apropriada;
5. o Sprint 0F é o próximo marco formal do projeto e permanece não iniciado.

---

# 24. Regra de continuidade

Em qualquer novo Chat, Work ou tarefa Codex relacionada ao projeto, este documento pode ser usado como ponto de partida.

Prompt mínimo sugerido:

```text
Leia primeiro AGENTS.md e docs/BTG_AI_TRADER_MASTER_PLAN.md.
Considere esses documentos como contexto normativo e de continuidade.
Não contradiga decisões já aprovadas sem explicitar a divergência e propor atualização formal por ADR.
```

Este arquivo deve permanecer no repositório e evoluir junto com o projeto.
