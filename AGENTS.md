# BTG AI Trader — Instruções permanentes

## Propósito e prioridade

Este repositório é a fonte de verdade técnica do BTG AI Trader, um sistema quantitativo intradiário em Python. Segurança operacional, preservação de capital, integridade dos dados, auditabilidade e reprodutibilidade têm precedência sobre velocidade de entrega ou desempenho aparente.

## Estado atual

A Fundação (Sprints 0A a 0F) está formalmente concluída e aprovada. Os contratos 0D-A a 0D-E, os protocolos 0E-A a 0E-G e os artefatos congelados de 0F permanecem preservados e auditáveis.

O Sprint 1 — Market Observer foi formalmente aceito em 2026-09-16 sob o contrato 0F-E integral. A sessão qualificadora `s1-xp-capture-a12` exerceu o provider `xp-mt5` em modo passivo/read-only, e os 41 RQMs, NEG-CAP-01..10 e XC-01..XC-11 foram adjudicados como satisfeitos no gate final.

Por decisão humana explícita de 2026-09-16, o Official Codex Security Diff Scan não foi executado e permanece registrado como `NOT_EXECUTED`; o instrumento final de segurança do Sprint 1 é o pacote GitHub-native documentado em `docs/program/S1_GITHUB_SECURITY_ALTERNATIVE_GATE_2026-09-16.md`. Essa substituição altera apenas o instrumento de evidência e não dispensa requisitos substantivos de 0F-E.

```text
SPRINT1_PROVIDER_QUALIFIED = YES
SPRINT1_ACCEPTANCE = YES
PROMOTION_TO_SPRINT_2 = YES
SPRINT_2_STATUS = FORMALLY_CLOSED
SPRINT_2_LIFECYCLE = FORMALLY_CLOSED
SPRINT_2_FINAL_VERDICT = PASS
SPRINT_2_CANONICAL_HEAD = ba6c0c41988fc9fefbdff13b0daedf96301dd74c
S2_ENTRY_GATE = PASS
S2_A = ACCEPTED
S2_B = ACCEPTED
S2_C = ACCEPTED
PROMOTION_TO_SPRINT_3_GATE = YES

SPRINT_3_STATUS = FORMALLY_CLOSED
SPRINT_3_LIFECYCLE = FORMALLY_CLOSED
SPRINT_3_FINAL_VERDICT = PASS
SPRINT_3_CANONICAL_HEAD = 6333b8f431d43be9c40f3222fbbe17cf06509033
SPRINT_3_POST_MERGE_CI_RUN = 35256018204
SPRINT_3_POST_MERGE_CI = PASS
SPRINT_3_POST_MERGE_UPSTREAM_RUN = 35256018048
SPRINT_3_POST_MERGE_UPSTREAM = PASS
S3_ENTRY_GATE = PASS
S3_CANONICAL_BRANCH = sprint/3-deterministic-economic-backtesting
S3_WORK_BRANCH = s3/00-full-deterministic-economic-backtesting
MERGE_COMPLETED = YES
PROMOTION_TO_SPRINT_4_GATE = YES
SPRINT_4_STATUS = FORMALLY_CLOSED
SPRINT_4_LIFECYCLE = FORMALLY_CLOSED
SPRINT_4_FINAL_VERDICT = PASS
SPRINT_4_FUNCTIONAL_MERGE = 0786ace3e6a83ecb23a508af860f43a2fd5d64e8
SPRINT_4_POST_MERGE_CI_RUN = 35304136357
SPRINT_4_POST_MERGE_CI = PASS
SPRINT_4_POST_MERGE_UPSTREAM_RUN = 35304136369
SPRINT_4_POST_MERGE_UPSTREAM = PASS
SPRINT_4_INDEPENDENT_REAUDIT = PASS
S4_ENTRY_GATE = PASS
S4_CANONICAL_BRANCH = sprint/4-statistical-baselines
S4_WORK_BRANCH = s4/00-full-statistical-baselines
SPRINT_4_MERGE_COMPLETED = YES
PROMOTION_TO_SPRINT_5_GATE = YES
SPRINT_5_STATUS = FORMALLY_CLOSED
SPRINT_5_LIFECYCLE = FORMALLY_CLOSED
SPRINT_5_ENTRY_GATE = PASS
SPRINT_5_CANONICAL_BRANCH = sprint/5-ml-engine
SPRINT_5_WORK_BRANCH = s5/00-full-ml-engine
SPRINT_5_FUNCTIONAL_IMPLEMENTATION = COMPLETED
SPRINT_5_FINAL_ACCEPTANCE = PASS
SPRINT_5_FINAL_VERDICT = PASS
SPRINT_5_INDEPENDENT_REAUDIT = PASS
SPRINT_5_MERGE_SHA = 8b09a34ecc7c3b0b180e30ada0702d22d61d96d2
SPRINT_5_POST_MERGE_CI_RUN = 35473144900
SPRINT_5_POST_MERGE_UPSTREAM_RUN = 35473144855
PROMOTION_TO_SPRINT_6_GATE = YES
SPRINT_6_STATUS = FORMALLY_CLOSED
SPRINT_6_LIFECYCLE = FORMALLY_CLOSED
SPRINT_6_ENTRY_GATE = PASS
SPRINT_6_ENTRY_GATE_FINAL_CANONICAL_HEAD = 616849f8e77ecf3624b2b9362c1ef42c7fb9bcc1
SPRINT_6_ENTRY_GATE_FINAL_CI_RUN = 35474371811
SPRINT_6_ENTRY_GATE_FINAL_UPSTREAM_RUN = 35474371852
SPRINT_6_CANONICAL_BRANCH = sprint/6-scenario-engine
SPRINT_6_ENTRY_GATE_WORK_BRANCH = s6/00-entry-gate
SPRINT_6_PREAUTH_WORK_BRANCH = s6/01-preauth-remediation
SPRINT_6_ENTRY_GATE_ISSUE = #79
SPRINT_6_PREAUTH_REMEDIATION_ISSUE = #81
SPRINT_6_PREAUTH_REVIEW = CHANGES_REQUIRED_REMEDIATED
SPRINT_6_PREAUTH_REMEDIATION = PASS
SPRINT_6_PREAUTH_REMEDIATION_CANONICAL = PASS
SPRINT_6_PREAUTH_REMEDIATION_MERGE_SHA = 7df047b25633527e505b3e4772c0a0c43e1ab10c
SPRINT_6_PREAUTH_POST_MERGE_ENTRY_GATE_CI_RUN = 35759318235
SPRINT_6_PREAUTH_POST_MERGE_UPSTREAM_RUN = 35759318238
SPRINT_6_FUNCTIONAL_ISSUE = #83
SPRINT_6_FUNCTIONAL_WORK_BRANCH = s6/02-full-scenario-engine
SPRINT_6_FUNCTIONAL_AUTHORIZATION_DATE = 2026-09-22
SPRINT_6_FUNCTIONAL_IMPLEMENTATION = COMPLETED
SPRINT_6_FUNCTIONAL_PR = #85
SPRINT_6_FUNCTIONAL_PR_HEAD = 69b5797306027a91b5366d44c4d22f2ab1caa37f
SPRINT_6_FUNCTIONAL_INDEPENDENT_REAUDIT = PASS
SPRINT_6_FUNCTIONAL_MERGE_SHA = 0e9438590338e2a322e96306a4dd8cb43d957535
SPRINT_6_POST_MERGE_PYTHON_CI_RUN = 35898586034
SPRINT_6_POST_MERGE_ENTRY_GATE_CI_RUN = 35898586113
SPRINT_6_POST_MERGE_UPSTREAM_RUN = 35898585983
SPRINT_6_FINAL_VERDICT = PASS
OPEN_SPRINT_6_BLOCKERS = 0
PROMOTION_TO_SPRINT_7_GATE = YES
SPRINT_7_STATUS = ENTRY_GATE_CANONICAL
SPRINT_7_LIFECYCLE = AWAITING_FUNCTIONAL_AUTHORIZATION
SPRINT_7_ENTRY_GATE_ISSUE = #86
SPRINT_7_CANONICAL_BRANCH = sprint/7-risk-engine
SPRINT_7_ENTRY_GATE_WORK_BRANCH = s7/00-entry-gate
S7_ENTRY_GATE = PASS
S7_ENTRY_GATE_CANONICAL = PASS
S7_ENTRY_GATE_PR = #87
S7_ENTRY_GATE_PR_HEAD = 0aac73fca2e291e7355f683ceda25fdcb3650d2e
S7_ENTRY_GATE_INDEPENDENT_REVIEW = PASS
S7_ENTRY_GATE_REVIEW_ID = 5295358543
S7_ENTRY_GATE_MERGE_SHA = 8d475abd8751d0042d06840012604de140e18d21
S7_ENTRY_GATE_POST_MERGE_CI_RUN = 35909666368
S7_ENTRY_GATE_POST_MERGE_UPSTREAM_RUN = 35909666371
OPEN_S7_ENTRY_GATE_BLOCKERS = 0
PROMOTION_TO_S7_FUNCTIONAL_IMPLEMENTATION = NO
SPRINT_7_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
STOP_FOR_INDEPENDENT_AUDIT = NO_FORMALLY_CLOSED
```

O Sprint 2 tratou exclusivamente de **Data Platform & Causal Market Replay** dentro de `docs/program/S2_ENTRY_CONTRACT.md`, `S2_DECISION_REGISTER.md`, `S2_CAPABILITY_MATRIX.md` e dos gates correspondentes. Os incrementos funcionais S2-A (Causal Replay Core) e S2-B (Lossless Normalization & Data Quality) e o gate final S2-C foram formalmente aceitos e fechados.

O Sprint 3 — **Deterministic Economic Backtesting** — foi formalmente concluído após auditoria independente, merge do PR #72 no commit canônico `6333b8f431d43be9c40f3222fbbe17cf06509033` e validação pós-merge dos runs `35256018204` e `35256018048`.

O Sprint 4 — **Statistical Baselines** — permanece formalmente fechado. O Sprint 5 — **Supervised Machine Learning Research Engine** — também está formalmente fechado após reauditoria independente PASS, merge humano do PR #78 em `8b09a34ecc7c3b0b180e30ada0702d22d61d96d2` e validação pós-merge dos runs `35473144900` (Sprint 5 Python CI, 13/13) e `35473144855` (Pinned upstream, 2/2). O Sprint 6 Entry Gate foi aprovado e integrado pelo PR #80. O head final reconciliado do gate antes da remediação pré-autorização é `616849f8e77ecf3624b2b9362c1ef42c7fb9bcc1`, validado pelos runs `35474371811` e `35474371852`. A revisão pré-autorização classificou o contrato funcional como `CHANGES_REQUIRED`; os findings foram remediados e reaudita​dos PASS no PR #82, que foi mergeado por autorização humana e validado pós-merge. A remediação está canônica PASS, com 0 blockers substantivos. A implementação funcional research-only do Sprint 6 foi reaudita​da PASS, integrada pelo PR #85 no merge SHA `0e9438590338e2a322e96306a4dd8cb43d957535` e validada pós-merge pelos runs `35898586034`, `35898586113` e `35898585983`. O Sprint 6 está formalmente fechado. O Sprint 7 Entry Gate foi reaudita​do PASS, mergeado por autorização humana via PR #87 em `8d475abd8751d0042d06840012604de140e18d21` e validado pós-merge pelos runs `35909666368` e `35909666371`. O lifecycle está em `AWAITING_FUNCTIONAL_AUTHORIZATION`; implementação funcional do Risk Engine permanece não autorizada. Negociação automática, envio de ordens, Paper operacional, Live operacional, Risk operacional, Strategy operacional, execução financeira e uso de dinheiro real permanecem estritamente proibidos.

## Autoridade normativa e realidade implementada

- Decisões normativas aprovadas são definidas pelos artefatos normativos vigentes do projeto: ADRs, protocolos quantitativos, contratos de entrada e gates formais.
- Código, testes, configurações e estrutura física representam o estado efetivamente implementado no repositório.
- A realidade implementada não pode silenciosamente superseder a autoridade normativa; divergência constitui drift/finding a ser reconciliado explicitamente.
- ADRs históricos aprovados não são reescritos silenciosamente; mudanças normativas exigem refinement ou supersession explícito.
- Snapshots históricos aprovados não são modificados retroativamente para harmonizar o presente.
- A integração read-only de market data admitida no Sprint 1 não cria precedente para autoridade financeira em sprints posteriores.
- A promoção de um sprint não importa automaticamente capacidades de sprints futuros.
- Antigravity, ChatGPT/Codex ou qualquer outro agente de implementação está subordinado aos contratos e gates versionados do repositório; a ferramenta não é fonte de autoridade normativa.

## Restrições absolutas nesta fase

- Não conectar a corretoras ou plataformas para fins de execução financeira.
- Não transmitir, criar, alterar ou cancelar ordens.
- Não usar nem introduzir chamadas a `order_send()` em caminhos autorizados do programa.
- Não habilitar negociação automática.
- Não operar com dinheiro real.
- Não implementar Strategy operacional, Risk operacional, Paper ou machine learning operacional fora do sprint formalmente autorizado.
- Não inserir credenciais, tokens, chaves, senhas, números de conta ou outros segredos no repositório, logs, documentação ou chat.
- Não fazer deploy de infraestrutura financeira produtiva.
- Os Sprints 4 e 5 estão FORMALLY_CLOSED/PASS. O Sprint 6 possui Entry Gate e remediação pré-autorização canônicos PASS; a implementação funcional research-only foi concluída e integrada canonicamente pelo PR #85. Strategy, Risk, Paper, Live, broker-order, FinancialLedger mutation e real money permanecem não autorizados.

Qualquer mudança futura dessas restrições exige decisão humana explícita, decisão arquitetural/documental adequada e satisfação dos gates correspondentes. Ausência de proibição não equivale a autorização.

## Princípios arquiteturais

- O futuro Risk Engine deve ser independente e ter poder de veto sobre qualquer Signal/Decision Engine.
- `NO_TRADE` deve ser resultado válido e preferível quando não houver evidência suficiente.
- Pesquisa/treinamento e execução deverão ser isolados; treinamento nunca deve disputar recursos com uma camada crítica de execução.
- Componentes financeiros críticos devem ser determinísticos quando possível, testáveis, observáveis e auditáveis.
- Dados, modelos, configurações e decisões devem ter versionamento e proveniência.
- Alterações arquiteturais relevantes exigem ADR em `docs/adr/`.
- Replay causal de dados de mercado não equivale a backtesting econômico.

## Regras de dados, replay, ML e validação

- Prevenir obrigatoriamente look-ahead bias, data leakage e contaminação entre treino, validação e teste.
- Preservar `event_time`, `ingestion_time`, `knowledge_time` e demais fronteiras temporais sem síntese otimista.
- O replay canônico deve manter ordenação causal, knowledge cutoffs explícitos e provenance reproduzível.
- `knowledge_time` é a fronteira de visibilidade causal do primeiro replay; `event_time` não pode substituí-la para revelar conhecimento futuro.
- Missingness/`UNKNOWN` não pode ser silenciosamente imputada ou descartada no caminho canônico de normalização.
- Usar separação temporal e validação fora da amostra antes de promover qualquer modelo futuro.
- Modelar custos, spread, slippage, latência e liquidez apenas nos estágios econômicos autorizados.
- Backtest não é evidência suficiente de desempenho futuro.
- Exigir replay/backtest verificável e paper trading antes de qualquer discussão de produção.
- Modelos futuros devem possuir versão, dados de origem, métricas, limitações e critérios de promoção/rejeição documentados.

## Gates mínimos para produção futura

Nenhuma execução real pode ser criada até aprovação explícita, no mínimo, de: qualidade dos dados; replay/backtester; ausência de leakage; validação fora da amostra; Risk Engine; paper trading; recuperação/reconciliação; observabilidade; segurança e autorização humana final. Os critérios detalhados devem ser materializados no estágio correspondente antes da primeira dependência material.

## Práticas de engenharia

- Usar layout `src/`, tipagem, testes automatizados e mudanças pequenas/revisáveis.
- Manter configuração separada de código; apenas exemplos seguros podem ser versionados.
- Falhar de modo seguro: incerteza, dados inválidos ou dependências indisponíveis devem impedir ações financeiras e impedir inferências otimistas de qualidade/readiness.
- Registrar decisões duráveis no repositório, não apenas em conversas.
- Antes de alterar código, ler este arquivo e a documentação aplicável ao sprint.
- Não ampliar o escopo de um sprint sem aprovação.
- Revalidar o HEAD remoto antes de merge ou promoção.
- Branches experimentais de sprints futuros permanecem SPECULATIVE até promoção formal; histórico experimental não entra automaticamente na baseline canônica.
- Toda mudança funcional deve passar o CI e os boundary checks aplicáveis ao estágio, além da verificação upstream pertinente.
- PRs #9 e #37 são referências históricas de pesquisa; não fazer merge/cherry-pick integral deles para a baseline canônica.

## Definição de pronto

Uma mudança só está pronta quando escopo, testes, documentação, implicações de segurança e pendências estão claros. Para componentes críticos, evidências auditáveis são obrigatórias. Um sprint só fecha por gate formal conjuntivo quando todos os critérios aplicáveis estiverem satisfeitos.

## Mandato de execução remota — 2026-09-13, reconciliado em 2026-09-17

O GitHub remoto é a superfície operacional e a fonte do estado implementado. O checkout físico do usuário não é a baseline canônica. Branches, commits e PRs remotos estão autorizados dentro dos gates vigentes.

Integração em branches canônicas de sprint/staging exige testes, typing, lint, checks de integridade, segurança/capacidades negativas aplicáveis, dependências satisfeitas e nenhum finding bloqueante. Promoção global para `main` não é automática.

O Sprint 1 preservou `READ_ONLY_BY_CONSTRUCTION` e `STRUCTURAL_ESCALATION`; os Sprints 2 e 3 herdaram essas barreiras e todas as negative financial capabilities. Dinheiro real, credenciais de negociação, ordens de broker e ativação financeira permanecem proibidos.

Os Sprints 3, 4, 5 e 6 estão formalmente fechados. O Sprint 7 foi autorizado apenas para Entry Gate sob Issue #86, com branches `sprint/7-risk-engine` e `s7/00-entry-gate`; implementação funcional de Risk, Paper, Live, broker-order e dinheiro real permanecem não autorizados.

Arquitetura e dry-run de sprints futuros podem avançar isoladamente como pesquisa, mas promoção ou ativação exige gate próprio. Decisões in-sprint são registradas antes da primeira dependência material; mudanças arquiteturais materiais seguem ADR. A Issue #6 preserva a errata histórica do 0F-F e `TRACEABILITY.md` continua autoridade canônica das QPIs.

O checkpoint vivo é [PROGRAM_EXECUTION.md](docs/program/PROGRAM_EXECUTION.md).