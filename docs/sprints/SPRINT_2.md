# Sprint 2 — Data Platform & Causal Market Replay

## Estado atual

```text
SPRINT_2_STATUS = CLOSURE_CANDIDATE
SPRINT_1_STATUS = FORMALLY_CLOSED
SPRINT_1_FINAL_VERDICT = PASS
SPRINT_1_ACCEPTED_HEAD = 57d820e256dd386624c1842c6f60b6797ba792aa
SPRINT_2_BRANCH = sprint/2-data-platform-replay
SPRINT_2_LIFECYCLE = PROPOSED_CLOSED
S2_ENTRY_GATE = PASS
S2_A = ACCEPTED (PR #65, 9faa43c3bc112c1d2e558aa3e1518371880cc518)
S2_B = ACCEPTED (PR #67, 071e004f2be8e5925b0de63db97af61cbbf37b30)
S2_C = PROPOSED
S2_C_ISSUE = #68
S2_C_PR = #70
S2_C_BRANCH = s2/03-final-acceptance-reconciliation
PROPOSED_SPRINT_2_FINAL_VERDICT = PASS
PROPOSED_SPRINT_2_LIFECYCLE = FORMALLY_CLOSED
PROMOTION_TO_SPRINT_3_GATE = YES
FINANCIAL_AUTHORITY = ABSENT
ECONOMIC_BACKTEST_AUTHORITY = ABSENT
```

O Sprint 2 parte do head formalmente aceito do Sprint 1. Nenhuma branch experimental anterior é automaticamente promovida para esta baseline.

## 1. Missão

Construir a camada de **Data Platform & Causal Market Replay** necessária para transformar evidência de mercado preservada em dados historicamente reproduzíveis e replay causal auditável, sem introduzir simulação econômica ou capacidade financeira.

O Sprint 2 preserva a semântica temporal, provenance, identidade e negative capabilities herdadas do Sprint 1.

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

O contrato operacional detalhado é `docs/program/S2_ENTRY_CONTRACT.md`, complementado por `S2_DECISION_REGISTER.md` e `S2_CAPABILITY_MATRIX.md`.

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

A abertura e o Gate de Entrada do Sprint 2 não modificam essas restrições.

## 5. Invariantes temporais mínimos

- Conhecimento posterior ao cutoff não pode alterar o estado observável de um replay anterior.
- Nenhum componente pode ordenar fatos por `event_time` de modo a fabricar conhecimento que não estava disponível.
- `UNKNOWN`/`NOT_PROVIDED` aplicáveis permanecem conservadores e não são convertidos silenciosamente em timestamps sintéticos.
- Igualdade de tempos preserva a ordenação causal original quando houver evidência de ordem.
- Regressão de `knowledge_time` em uma lane causal falha fechado, salvo contrato explícito que prove outra semântica.
- Replay repetido com os mesmos inputs, configuração e versão produz a mesma sequência lógica observável.

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

O replay não modifica os artefatos de origem para registrar processamento; receipts/lineage permanecem separados.

## 7. Relação com experimentos históricos

Os antigos PRs experimentais #9 e #37 foram encerrados como `SUPERSEDED BY FORMAL SPRINT 2`. Eles permanecem fontes históricas de pesquisa e podem ser consultados criticamente, mas:

- seus commits não são baseline canônica;
- seus resultados não são automaticamente aceitos como requisitos ou implementação do Sprint 2;
- qualquer conceito reutilizado deve ser reavaliado contra o head aceito do Sprint 1 e os contratos vigentes do Sprint 2;
- nenhuma branch experimental deve ser mesclada diretamente nesta branch apenas por existir anteriormente.

## 8. Gate de entrada funcional — PASS

O Gate de Entrada foi materializado com:

1. `docs/program/S2_ENTRY_CONTRACT.md`;
2. `docs/program/S2_DECISION_REGISTER.md`;
3. `docs/program/S2_CAPABILITY_MATRIX.md`;
4. `docs/program/S2_ENTRY_GATE.md`;
5. `docs/program/workstreams/S2-ANTIGRAVITY-HANDOFF.md`;
6. `scripts/check_s2_boundary.py`;
7. `.github/workflows/s2-python-ci.yml`;
8. verificação upstream estendida para branches S2.

A materialização funcional foi validada no head `8cfb17e3ba7b02c2eccc4d94f17dec986d6bb474` pelos runs `35130469411` (Sprint 2 Python CI) e `35130469284` (Pinned upstream engineering verification), todos verdes.

```text
S2_ENTRY_GATE = PASS
S2_FIRST_FUNCTIONAL_CODE = AUTHORIZED
```

O PR final do gate ainda deve permanecer verde em seu próprio HEAD exato antes do merge; essa revalidação é condição de integração, não reabertura do gate substantivo.

## 9. Incrementos funcionais executados e aceitos

### S2-A — Causal Replay Core (Aceito)
- **PR:** #65
- **Merge commit:** `9faa43c3bc112c1d2e558aa3e1518371880cc518`
- **Validação:** Python CI `35150432340` (8/8 PASS), Upstream `35150432259` (2/2 PASS)
- **Entregas:** `CausalMarketReplaySchedule`, `CausalMarketReplayCursor`, `CausalLane`, `ReplaySpeed`, `ReplayEmission`, `ReplayEmissionLineage`, e `ReplayInputBoundary` (DD-15). Replay monotônico por cutoff, sem wall-clock, estritamente causal.

### S2-B — Lossless Normalization & Data-Quality Evidence (Aceito)
- **PR:** #67
- **Merge commit:** `071e004f2be8e5925b0de63db97af61cbbf37b30`
- **Validação:** Python CI `35163848955` (8/8 PASS), Upstream `35163848942` (2/2 PASS)
- **Entregas:** `NormalizedMarketBatch`, `normalize_market_batch`, e `QualityFinding` (S2-AC-10). Preservação integral de fatos e missingness (DD-80), distinção entre achados bloqueantes de replay e não bloqueantes, zero imputação silenciosa.

### S2-C — Final Acceptance Reconciliation & Sprint 2 Closure Gate (Em revisão)
- **Branch:** `s2/03-final-acceptance-reconciliation`
- **Issue:** #68
- **PR:** #70
- **Artefato:** `docs/program/S2_FINAL_ACCEPTANCE.md`
- **Escopo:** Reconciliação formal conjuntiva de todas as capacidades positivas (S2-AC-01..14), negativas (S2-NC-01..16) e decisões ativas (DD-05..83). Zero código funcional novo.

## 10. Critério de não-regressão do Sprint 1

A Data Platform e o Replay consumiram contratos/evidência do Observer sem enfraquecer nenhum dos invariantes aceitos no Sprint 1. O scanner `scripts/check_s2_boundary.py` garantiu que nenhuma autoridade financeira ou acoplamento a corretoras fosse introduzido.

## 11. Próxima ação

Submeter o PR de reconciliação final e fechamento do Sprint 2 (S2-C). Após auditoria independente, aprovação de CI no HEAD exato, merge em `sprint/2-data-platform-replay` e validação pós-merge, preparar formalmente o Gate de Entrada do Sprint 3 (Deterministic Economic Backtesting). O fechamento do Sprint 2 não autoriza antecipadamente capacidades econômicas ou financeiras antes da abertura formal do gate de Sprint 3.