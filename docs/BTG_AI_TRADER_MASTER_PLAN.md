# BTG AI Trader — Plano Mestre Vivo

**Documento de referência transversal do projeto**
**Status:** ativo e evolutivo
**Última consolidação:** 2026-09-16
**Repositório:** `paulobmcosta-creator/btg-ai-trader`
**Visibilidade:** pública, source-visible, licença proprietária

---

## 1. Finalidade e hierarquia

Este arquivo preserva a visão transversal do projeto BTG AI Trader e deve refletir o estado vivo do programa sem reescrever silenciosamente snapshots históricos.

Hierarquia de autoridade:

```text
1. Código e testes do repositório
2. ADRs, protocolos e contratos versionados
3. AGENTS.md
4. Este Plano Mestre
5. Conversas do ChatGPT
```

Os artefatos congelados da Fundação continuam históricos e não são reescritos para acomodar decisões posteriores.

---

## 2. Visão do produto

Desenvolver um sistema privado de trading quantitativo intradiário, inicialmente voltado a instrumentos líquidos da B3, com evolução estritamente governada por gates de dados, replay, backtesting, validação quantitativa, risco, paper trading, recovery e segurança antes de qualquer capacidade financeira real.

O sistema deverá evoluir para combinar dados de mercado em tempo real, engenharia de atributos, identificação de regime, modelos estatísticos e de machine learning, avaliação probabilística, sinais, dimensionamento, gestão independente de risco, execução auditável, replay/backtesting, paper trading, monitoramento e recovery/reconciliation.

O foco inicial permanece intradiário, com horizonte de segundos a minutos. O projeto não é HFT de microssegundos e não autoriza dinheiro real nesta fase.

---

## 3. Princípios não negociáveis

### 3.1. Preservação de capital e autoridade

1. Preservação de capital precede maximização de retorno.
2. `NO_TRADE` é resultado plenamente válido.
3. O futuro Risk Engine deve possuir poder absoluto de veto.
4. Nenhum modelo ou Signal Engine poderá enviar ordens diretamente.
5. Nenhuma capacidade financeira real pode existir antes dos gates formais correspondentes.
6. Incerteza operacional implica comportamento fail-closed.

### 3.2. Integridade quantitativa

- prevenir look-ahead bias, leakage, survivorship bias e overfitting;
- exigir separação temporal e validação fora da amostra;
- incorporar custos, spread, slippage, liquidez e latência quando economicamente aplicáveis;
- evitar promoção de modelos por accuracy isolada;
- priorizar métricas econômicas e de risco.

### 3.3. Engenharia e auditabilidade

- toda decisão relevante deve ser reconstruível;
- ADRs são obrigatórios para mudanças arquiteturais materiais;
- credenciais e segredos nunca são versionados;
- pesquisa, replay, backtest, paper e produção permanecem separados por autoridade e composição;
- mudanças de estágio exigem evidência e gate explícitos.

---

## 4. Arquitetura normativa de alto nível

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
        InstrumentResolution
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

Invariantes centrais:

- `NO_TRADE` é distinto de `RiskDecision.REJECT`, `SAFE_HALT` e falha operacional;
- todo `TradeIntent` apresentado a Risk referencia instrumento concreto;
- `RiskDecision` julga, `RiskAuthorization` concede authority limitada;
- novo economic commitment exige authorization/alocação suficientes;
- somente Execution pode solicitar side effect externo;
- modelo, Signal Engine e Strategy nunca possuem authority de ordem.

Arquiteturalmente proibido:

```text
ML Model -> Broker
Signal Engine -> order_send()
StrategyDecision -> Execution
RiskDecision -> external side effect
```

---

## 5. Fundação — estado canônico

```text
SPRINT 0A — Bootstrap                         CLOSED / PASS
SPRINT 0B — Ambiente                          CLOSED / PASS
SPRINT 0C — Arquitetura lógica                CLOSED / PASS
SPRINT 0D — Contratos e modelo de dados       CLOSED / PASS
SPRINT 0E — Protocolos quantitativos          CLOSED / PASS
SPRINT 0F — Foundation Cross-Gate             CLOSED / PASS
0F-A                                           CLOSED
0F-B                                           CLOSED
0F-C — 41 RQMs                                PASS / CLOSED
0F-D — 20 NCs / 10 NEG-CAP                    PASS / CLOSED
0F-E — 118 cláusulas Sprint 1                 PASS / CLOSED
0F-F — Foundation Final Gate                  PASS / CLOSED
PRE_SPRINT1_ACTIONS                            CLOSED
```

A Fundação não autoriza trading. Ela estabelece autoridade, contratos, protocolos, negative capabilities e os gates de evolução.

---

## 6. Sprint 1 — Market Observer — FORMALLY CLOSED / PASS

### 6.1. Objetivo cumprido

O Sprint 1 implementou observação de mercado real em modo estritamente passivo:

```text
READ_ONLY_BY_CONSTRUCTION = PASS
STRUCTURAL_ESCALATION = PASS
```

### 6.2. Provider final

Histórico:

```text
ADR-0023  BTG Data Services   -> referência histórica
Cedro                         -> rejeitado como provider canônico de longo prazo
ADR-0025  Rico + MT5          -> caminho histórico superseded
ADR-0026  XP + MT5            -> provider qualificado do Sprint 1
```

### 6.3. Arquitetura efetivamente exercitada

```text
XP / MT5 server
-> MetaTrader 5 terminal
   -> Investor / read-only
   -> custom MQL5 indicator
      -> append-only FILE_COMMON
         -> trusted Python readers
            -> evidence harness
               -> provenance / health / latency / technical evidence
```

O Python confiável não importa `MetaTrader5`, não recebe account/order API e não possui authority financeira.

### 6.4. Sessão qualificadora real

Em 2026-09-16, a sessão `s1-xp-capture-a12` completou com:

```text
PROVIDER = xp-mt5
INSTRUMENT = WINV26
TIMEFRAME = PERIOD_M1
CODE_REVISION = e622658922ff38e49e1112a48d91eecb2d43a522
WORKTREE_AT_CAPTURE = CLEAN
DISCOVERY_RECORDS = 18
TICK_RECORDS = 8005
CANDLE_RECORDS = 2
BRIDGE_FINAL_STATE = IDLE
```

Payloads brutos permanecem fora do Git; fingerprints e metadados sanitizados estão versionados.

### 6.5. Engenharia final

Após o PR #59, o commit integrado `6457ae1dfec6e91034741e57c6343397f368cbc2` passou GitHub Actions run `35126543429`.

A reconciliação final `977923a4693b4b14d1ddab47a77d7bf86cb250b9` passou:

```text
Remote Python CI = PASS (35128804489)
Pinned upstream engineering verification = PASS (35128804436)
```

### 6.6. Segurança final

O Official Codex Security Diff Scan não foi executado. Por decisão humana explícita em 2026-09-16, o instrumento final de assurance do Sprint 1 é o pacote GitHub-native documentado em `docs/program/S1_GITHUB_SECURITY_ALTERNATIVE_GATE_2026-09-16.md`.

```text
OFFICIAL_CODEX_SECURITY_DIFF_SCAN = NOT_EXECUTED
GITHUB_NATIVE_SECURITY_GATE = PASS
```

A substituição altera apenas o instrumento de evidência. NEG-CAP, inspeção estática, config/segredos, integridade da Fundação e os requisitos de 0F-E permanecem integrais.

### 6.7. Veredito final

```text
RQMS = 41/41 PASS_OR_CURRENT_SCOPE
NEG_CAP_01_TO_10 = PASS
XC_01_TO_11 = PASS
OPEN_BLOCKERS = 0
SPRINT1_PROVIDER_QUALIFIED = YES
SPRINT1_ACCEPTANCE = YES
PROMOTION_TO_SPRINT_2 = YES
```

Sprint 1 — Market Observer está formalmente concluído e aprovado.

---

## 7. Negative capabilities herdadas pelo Sprint 2

```text
TRUSTED_PYTHON_IMPORTS_METATRADER5 = NO
PYTHON_ACCOUNT_API = ABSENT
PYTHON_ORDER_API = ABSENT
ORDER_SUBMISSION = IMPOSSIBLE
ORDER_MODIFICATION = IMPOSSIBLE
ORDER_CANCELLATION = IMPOSSIBLE
FINANCIAL_LEDGER_MUTATION = ABSENT
PAPER_PATH = ABSENT
LIVE_TRADING_PATH = ABSENT
REAL_MONEY_AUTHORITY = ABSENT
ECONOMIC_COMMITMENT = IMPOSSIBLE
```

A promoção ao Sprint 2 não altera essas proibições.

---

## 8. Roadmap vigente

### Sprint 2 — Data Platform & Causal Market Replay — PROPOSED CLOSED / PASS

Escopo executado e auditado:

- normalização e plataforma de dados;
- replay formal de dados históricos de mercado;
- ordenação causal;
- knowledge cutoffs explícitos;
- reprodutibilidade;
- velocidade virtual controlada;
- provenance;
- qualidade e consistência de dados.

Fora do Sprint 2:

- execução de ordens;
- Strategy operacional;
- Risk operacional;
- Paper;
- Live;
- P&L econômico;
- custos, slippage e queue-fill como simulador econômico;
- modelos preditivos operacionais.

### Sprint 3 — Deterministic Economic Backtesting

Replay econômico determinístico, custos, spread, slippage, latência econômica, métricas e testes de leakage.

### Sprint 4 — Statistical Baselines

Benchmarks, modelos simples, calibração e out-of-sample.

### Sprint 5 — ML Engine

Feature pipeline, model registry, treino/validação e comparação de modelos.

### Sprint 6 — Scenario Engine

Regimes, cenários, stress e distribuição de resultados.

### Sprint 7 — Risk Engine

Limites, sizing, circuit breakers, veto, drawdown, daily loss e fail-safe.

### Sprint 8 — Paper Trader

Mercado real, decisões reais e dinheiro fictício, com registro completo e zero dinheiro real.

### Sprint 9 — Recovery / Cloud preparation

Recovery, reconciliation, watchdog, observabilidade e segurança operacional.

### Sprint 10 — Dashboard

Status, risco, pause, kill switch e alertas.

### Sprint 11 — Auditoria pré-produção

Segurança, estatística, performance, recovery, risco e compliance operacional.

### Sprint 12 — Produção mínima controlada

Somente se todos os gates posteriores forem cumpridos e houver nova autorização humana explícita.

---

## 9. Machine Learning — orientação preservada

Sequência preferencial futura:

1. baseline aleatório;
2. regressão logística;
3. Random Forest;
4. Gradient Boosting;
5. XGBoost/LightGBM;
6. modelos temporais complexos apenas com ganho robusto;
7. RL apenas como pesquisa futura.

Meta-labeling permanece linha futura válida, sem wiring operacional antecipado.

---

## 10. Avaliação e risco

Métricas futuras candidatas incluem expected return/downside, VaR/Expected Shortfall, drawdown, Sharpe/Sortino/Calmar, profit factor, expectancy, probabilidade de perda/ruína, slippage e latência efetivos.

Objetivo conceitual: maximizar retorno ajustado ao risco, nunca retorno bruto isolado.

---

## 11. Infraestrutura e superfície operacional

A superfície operacional atual é o GitHub remoto. Checkout físico do usuário não é fonte canônica do estado do programa.

```text
btg-ai-trader/
├── .github/
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

Direção futura de produção continua separando Trading Node, Research/AI Node, storage e observabilidade; treinamento pesado nunca deve competir com componentes críticos.

---

## 12. Git/GitHub

### 12.1. Estado atual

- repositório público;
- licença proprietária source-visible;
- `main` preserva deliberadamente a baseline histórica/public-readiness e não representa automaticamente o HEAD operacional de sprint;
- branch canônica do Sprint 1: `sprint/1-market-observer`;
- branch de fechamento: `s1/30-final-acceptance-github-security`;
- Sprint 2 está autorizado a abrir a partir do head aceito do Sprint 1.

### 12.2. Segurança do repositório

O projeto possui workflows de CI, integridade da Fundação, boundary/negative-capability checks e controles de inspeção de histórico/segredos. A proteção administrativa de branches/rulesets deve ser aplicada quando a superfície GitHub permitir configuração por administrador; até lá, a ausência de ruleset não reduz os gates documentais e de CI.

### 12.3. Política

- nenhuma credencial versionada;
- commits semanticamente coerentes;
- PRs para mudanças materiais;
- branches experimentais isoladas;
- histórico não reescrito para apagar decisões;
- promoção entre sprints por gate explícito.

---

## 13. Política Chat / Codex / Work

```text
Chat  -> arquitetura, decisão, revisão e coordenação
Codex -> implementação/testes/refatoração quando disponível
Work  -> tarefas transversais excepcionais
```

O GitHub remoto é a fonte do estado implementado e deve ser preferido a contexto apenas conversacional.

---

## 14. Política de atualização

Atualizar este Plano Mestre quando houver fechamento/abertura de sprint, mudança de provider, nova decisão arquitetural material, alteração de gate, mudança de infraestrutura, nova classe de ativo ou descoberta que invalide premissa vigente.

Nunca reescrever silenciosamente ADR histórico, alterar snapshots congelados para harmonizar o presente, promover hipótese a regra sem evidência ou conceder authority financeira por implicação.

---

## 15. Changelog consolidado

### 2026-08-17 a 2026-08-25 — Fundação

Bootstrap, ambiente, arquitetura, contratos, protocolos quantitativos e Foundation Gate concluídos. Ações pré-Sprint 1 materializadas e Sprint 1 autorizado sob 0F-E.

### 2026-09-13 — execução remota do Sprint 1

GitHub consolidado como superfície operacional. Observer, provenance, health, storage, admission/quarantine, dedup/backpressure, temporal lineage, propriedades/mutação e negative-capability gates integrados.

### 2026-09-14 — providers e public-readiness

BTG Data Services, Cedro e Rico/MT5 avaliados historicamente. Repositório preparado para visibilidade pública com licença proprietária, SECURITY/NOTICE e scanner de histórico alcançável.

### 2026-09-15 — XP/MT5

ADR-0026 tornou XP/MT5 o provider vigente. Bridge read-only, discovery, portability Windows e captura automatizada foram reconciliados.

### 2026-09-16 — runtime evidence e aceitação do Sprint 1

`s1-xp-capture-a12` completou com discovery, ticks e candle finalizado. PR #59 foi integrado. O exact integrated head `6457ae1...` passou CI. A reconciliação `977923a...` também passou CI/upstream. A coordenação humana aceitou o pacote GitHub-native de segurança como substituto do Official Codex Security Diff Scan, preservando este como `NOT_EXECUTED`. Os 41 RQMs e XC-01..XC-11 foram adjudicados PASS; Sprint 1 foi formalmente aceito e Sprint 2 autorizado.

### 2026-09-16 — execução e reconciliação do Sprint 2

O Gate de Entrada do Sprint 2 foi formalizado via PR #63 (`00cc561...`). S2-A implementou o Causal Replay Core (`src/btg_ai_trader/replay/`), com schedule imutável, monotonicidade por cutoff UTC, speed racional e proveniência DD-15 (`ReplayInputBoundary`), aceito via PR #65 (`9faa43c...`). S2-B implementou a normalização sem perdas e evidência determinística de qualidade (`src/btg_ai_trader/data_platform/`), preservando `MissingReason` (DD-80) e neutralidade factual (S2-AC-10), aceito via PR #67 (`071e004...`). A tarefa S2-C consolidou a reconciliação formal conjuntiva em `docs/program/S2_FINAL_ACCEPTANCE.md` (11 ACs PASS, 3 ACs NOT_TRIGGERED, 16 NCs PASS, 0 blockers), propondo o fechamento do Sprint 2 e autorização para materializar o Gate do Sprint 3.

---

## 16. Próxima ação oficial

Aprovar e mesclar o PR de reconciliação final do Sprint 2 (S2-C) e preparar formalmente o Gate de Entrada do Sprint 3 — Deterministic Economic Backtesting.

A promoção para o Gate do Sprint 3 significa exclusivamente autorização para abrir/materializar o gate do Sprint 3, não autorizando antecipadamente execução de ordens, Strategy, Risk, Paper, Live, P&L, custos, slippage, fills ou dinheiro real.