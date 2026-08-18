# BTG AI Trader — Plano Mestre Vivo

**Documento de referência principal do projeto**  
**Status:** ativo e evolutivo  
**Última consolidação:** 2026-08-18  
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

```text
MARKET / DATA SOURCE
        |
        v
MARKET ADAPTER
        |
        v
DATA ENGINE
        |
        v
NORMALIZED MARKET EVENTS
        |
        +--------------------> RECORDER / STORAGE
        |
        +--------------------> MONITORING
        |
        v
FEATURE ENGINE
        |
        v
MARKET STATE
        |
        +-----------> REGIME ENGINE
        |
        +-----------> SIGNAL ENGINE
                           |
                           v
                       TradeIntent
                           |
                           v
                       RISK ENGINE
                      /           \
                  REJECT         APPROVE
                    |               |
                 NO_TRADE       OrderIntent
                                    |
                                    v
                            EXECUTION ENGINE
                                    |
                                    v
                              BROKER ADAPTER
                                    |
                                    v
                                BTG / B3
```

## 5.1. Invariante central

A cadeia permitida deverá seguir:

```text
ML / Signal
    |
    v
TradeIntent
    |
    v
Risk Engine
    |
    v
OrderIntent
    |
    v
Execution Engine
    |
    v
Broker Adapter
```

É arquiteturalmente proibido:

```text
ML Model -> Broker
Signal Engine -> order_send()
```

---

# 6. Conceitos arquiteturais a formalizar no Sprint 0C

## 6.1. TradeIntent

Representa uma intenção econômica, por exemplo:

```text
instrument_family: WIN
direction: LONG
confidence: 0.74
expected_horizon: 5m
expected_return: ...
expected_downside: ...
```

Não constitui uma ordem.

## 6.2. OrderIntent

Somente pode surgir após avaliação do Risk Engine.

Exemplo conceitual:

```text
tradable_instrument: WINQ26
side: BUY
quantity: 1
order_type: ...
```

Ainda assim, somente o Execution Engine poderá convertê-lo em instrução para a infraestrutura da corretora.

## 6.3. Quatro modos

O núcleo deverá ser reutilizável entre:

```text
REPLAY
BACKTEST
PAPER
LIVE
```

A estratégia deve, tanto quanto tecnicamente possível, receber interfaces equivalentes de dados e decisão nos diferentes modos.

O Signal Engine não deve depender de saber se está em `BACKTEST` ou `LIVE`.

## 6.4. Semântica temporal

Deverão existir, quando aplicável:

- `event_time`: momento do evento no mercado;
- `ingestion_time`: momento de chegada ao sistema;
- `processing_time`: momento de processamento.

Direção preliminar:

- tempo interno em UTC;
- conversão explícita para `America/Sao_Paulo` onde calendário/regras da B3 exigirem;
- evitar `naive datetime`.

## 6.5. Instrumentos

Separar:

```text
InstrumentFamily: WIN
TradableInstrument: WINQ26
```

Rollover deverá ser explícito e auditável.

## 6.6. Recuperação de estado

Em reinicialização:

```text
BOOT
  |
  v
carregar estado persistido
  |
  v
consultar fonte externa quando disponível
  |
  v
reconciliar posições/ordens
  |
  v
detectar divergências
  |
  v
FAIL SAFE
  |
  v
liberar operação somente após consistência
```

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
Baseline arquitetural                 ✅ ADR-0002 a ADR-0014 VIGENTE
0D — Contratos e modelo de dados       ← PRÓXIMA ETAPA OFICIAL
0E — Protocolos quantitativos
0F — Gate do Sprint 0
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

Ainda não foram escolhidos schema, interfaces Python, armazenamento físico, tecnologia de mensageria, calendário concreto, tolerâncias, mecanismo de reserva ou integração externa. Esses itens pertencem a 0D ou sprints posteriores. O Sprint 0C está formalmente concluído e aprovado; 0D — Contratos e Modelo de Dados é a próxima etapa oficial.

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

- número mínimo de pregões;
- comportamento compatível com backtest;
- slippage observado;
- estabilidade operacional;
- nenhum erro crítico.

## Gate E — Risk Engine

- veto testado;
- circuit breakers;
- daily loss;
- position limits;
- kill switch;
- fail-safe.

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

---

# 23. Próxima ação oficial

**Iniciar, mediante tarefa autorizada, o Sprint 0D — Contratos e Modelo de Dados.**

Antes de qualquer nova implementação funcional:

1. preservar os ADRs 0002–0014 como baseline arquitetural vigente;
2. definir o escopo e os critérios de aceite do 0D;
3. materializar contratos e modelo de dados somente em tarefa autorizada;
4. manter qualquer capacidade financeira real desabilitada.

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
