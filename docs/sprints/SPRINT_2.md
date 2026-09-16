# Sprint 2 — Data Platform & Causal Market Replay

## Estado de abertura

```text
SPRINT_2_STATUS = OPEN
SPRINT_1_STATUS = FORMALLY_CLOSED
SPRINT_1_FINAL_VERDICT = PASS
SPRINT_1_ACCEPTED_HEAD = 57d820e256dd386624c1842c6f60b6797ba792aa
SPRINT_2_BRANCH = sprint/2-data-platform-replay
SPRINT_2_LIFECYCLE = OPEN
SPRINT_2_FUNCTIONAL_IMPLEMENTATION = NOT_YET_PROMOTED
FINANCIAL_AUTHORITY = ABSENT
```

O Sprint 2 é aberto a partir do head formalmente aceito do Sprint 1. Nenhuma branch experimental anterior é automaticamente promovida para esta baseline.

## 1. Missão

Construir a camada de **Data Platform & Causal Market Replay** necessária para transformar evidência de mercado preservada em dados historicamente reproduzíveis e replay causal auditável, sem introduzir simulação econômica ou capacidade financeira.

O Sprint 2 deve preservar integralmente a semântica temporal, provenance, identidade e negative capabilities herdadas do Sprint 1.

## 2. Escopo positivo autorizado

O Sprint 2 pode projetar, implementar e testar, mediante decisões registradas antes da primeira dependência material:

- normalização de dados de mercado preservando fatos e missingness explícita;
- contratos de datasets/capturas históricas e sua provenance;
- leitura e composição de evidência técnica produzida pelo Observer;
- replay formal de dados históricos de mercado;
- ordenação causal baseada em conhecimento disponível, sem look-ahead;
- `knowledge_time`/knowledge cutoffs explícitos;
- preservação de `event_time`, `ingestion_time` e demais bases temporais aplicáveis;
- relógio virtual/controlável para replay;
- avanço monotônico por cutoff;
- controle de velocidade de replay sem dependência de wall-clock para determinismo lógico;
- reprodutibilidade de uma mesma captura/configuração;
- isolamento de lanes/scopes/providers quando a causalidade assim exigir;
- detecção fail-closed de regressões temporais, identidade duplicada/conflitante e provenance incompatível;
- qualidade e consistência de dados históricos;
- evidência técnica de replay e rastreabilidade de entradas/saídas;
- testes de propriedades e determinismo apropriados ao escopo de dados/replay.

## 3. Fronteira explícita com o Sprint 3

O Sprint 2 implementa **replay causal de mercado**, não backtesting econômico.

É proibido no Sprint 2 materializar como capacidade operacional:

```text
P&L simulation
spread-cost model
tax/fee model
slippage model
queue-fill simulation
order fill simulation
economic latency model
portfolio accounting
Ledger mutation
StrategyDecision operational path
TradeIntent operational path
RiskAuthorization operational path
Paper trading
Live trading
broker order API
real-money execution
```

Custos, spread, slippage, fills simulados e métricas econômicas pertencem ao Sprint 3 ou estágio posterior formalmente autorizado.

## 4. Negative capabilities herdadas

```text
PYTHON_ORDER_API = ABSENT
BROKER_ACCOUNT_API = ABSENT
ORDER_SUBMISSION = IMPOSSIBLE
ORDER_MODIFICATION = IMPOSSIBLE
ORDER_CANCELLATION = IMPOSSIBLE
FINANCIAL_LEDGER_MUTATION = ABSENT
STRATEGY_OPERATIONAL_PATH = ABSENT
RISK_OPERATIONAL_PATH = ABSENT
PAPER_PATH = ABSENT
LIVE_TRADING_PATH = ABSENT
REAL_MONEY_AUTHORITY = ABSENT
ECONOMIC_COMMITMENT = IMPOSSIBLE
```

A abertura do Sprint 2 não modifica essas restrições.

## 5. Invariantes temporais mínimos

- Conhecimento posterior ao cutoff não pode alterar o estado observável de um replay anterior.
- Nenhum componente pode ordenar fatos por `event_time` de modo a fabricar conhecimento que não estava disponível.
- `UNKNOWN`/`NOT_PROVIDED` aplicáveis devem permanecer conservadores e não ser convertidos silenciosamente em timestamps sintéticos.
- Igualdade de tempos deve preservar a ordenação causal original quando houver evidência de ordem.
- Regressão de `knowledge_time` em uma lane causal deve falhar fechado, salvo contrato explícito que prove outra semântica.
- Replay repetido com os mesmos inputs, configuração e versão deve produzir a mesma sequência lógica observável.

## 6. Provenance e lineage

Todo replay aceito deve permitir reconstruir, no mínimo:

```text
source capture / artifact identities
provider / capture_scope
input artifact hashes
code revision
configuration identity/hash
replay run identity
knowledge cutoff semantics
ordered output identities
lineage between input evidence and replay outputs
```

O replay não pode modificar os artefatos de origem para registrar processamento; receipts/lineage devem permanecer separados.

## 7. Relação com experimentos históricos

Os antigos PRs experimentais #9 e #37 foram encerrados como `SUPERSEDED BY FORMAL SPRINT 2`. Eles permanecem fontes históricas de pesquisa e podem ser consultados criticamente, mas:

- seus commits não são baseline canônica;
- seus resultados não são automaticamente aceitos como requisitos ou implementação do Sprint 2;
- qualquer conceito reutilizado deve ser reavaliado contra o head aceito do Sprint 1 e documentado antes da nova implementação;
- nenhuma branch experimental deve ser mesclada diretamente nesta branch apenas por existir anteriormente.

## 8. Gate de entrada funcional

Antes do primeiro código funcional novo do Sprint 2, materializar e revisar:

1. escopo/contrato de entrada do Sprint 2 derivado da autoridade vigente;
2. decisões deferidas que atingem a primeira dependência material;
3. matriz de capacidades positivas e negativas do Sprint 2;
4. definição do dataset/capture boundary e replay identity;
5. definição da semântica de ordering/cutoff/virtual clock;
6. plano de testes de determinismo, temporalidade, provenance e negative capability;
7. CI/boundary apropriado ao novo escopo, sem reutilizar cegamente um scanner feito para rejeitar capacidades Sprint-2+ na árvore do Sprint 1.

```text
S2_FIRST_FUNCTIONAL_CODE = BLOCKED_UNTIL_ENTRY_MATERIALIZATION
```

## 9. Critério de não-regressão do Sprint 1

A Data Platform e o Replay podem consumir contratos/evidência do Observer, mas não podem enfraquecer os invariantes aceitos no Sprint 1. Qualquer incompatibilidade entre necessidade do Sprint 2 e contratos herdados deve parar a implementação e produzir decisão explícita, não alteração silenciosa.

## 10. Próxima ação

Materializar o **Sprint 2 Entry Contract / scope gate** e a matriz de verificação antes de promover qualquer código experimental anterior ou implementar novos componentes funcionais.