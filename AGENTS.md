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
SPRINT_2_STATUS = CLOSURE_CANDIDATE
SPRINT_2_LIFECYCLE = PROPOSED_CLOSED
S2_ENTRY_GATE = PASS
S2_A = ACCEPTED
S2_B = ACCEPTED
S2_C = PROPOSED
PROPOSED_SPRINT_2_FINAL_VERDICT = PASS
PROPOSED_SPRINT_2_LIFECYCLE = FORMALLY_CLOSED
PROMOTION_TO_SPRINT_3_GATE = YES
```

O Sprint 2 tratou exclusivamente de **Data Platform & Causal Market Replay** dentro de `docs/program/S2_ENTRY_CONTRACT.md`, `S2_DECISION_REGISTER.md`, `S2_CAPABILITY_MATRIX.md` e dos gates correspondentes. Os incrementos funcionais S2-A (Causal Replay Core) e S2-B (Lossless Normalization & Data Quality) foram formalmente aceitos. O gate final S2-C consolidou a reconciliação formal conjuntiva em `docs/program/S2_FINAL_ACCEPTANCE.md`.

Não há autorização para negociação automática, envio de ordens, Paper, Risk operacional, Strategy operacional, execução financeira, backtesting econômico ou uso de dinheiro real.

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
- No Sprint 2, não implementar backtesting econômico, custos, slippage, P&L ou queue-fill econômico; esses itens pertencem ao Sprint 3 ou posterior conforme gate aplicável.
- No primeiro incremento funcional do Sprint 2, não ampliar o escopo além do causal replay core autorizado no handoff do Antigravity.

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
- O Sprint 2 deve manter ordenação causal, knowledge cutoffs explícitos e provenance reproduzível no replay.
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
- No Sprint 2, toda mudança funcional deve passar `Sprint 2 Python CI`, inclusive `s2-boundary`, além da verificação upstream aplicável.
- PRs #9 e #37 são referências históricas de pesquisa; não fazer merge/cherry-pick integral deles para a baseline canônica.

## Definição de pronto

Uma mudança só está pronta quando escopo, testes, documentação, implicações de segurança e pendências estão claros. Para componentes críticos, evidências auditáveis são obrigatórias. Um sprint só fecha por gate formal conjuntivo quando todos os critérios aplicáveis estiverem satisfeitos.

## Mandato de execução remota — 2026-09-13, reconciliado em 2026-09-16

O GitHub remoto é a superfície operacional e a fonte do estado implementado. O checkout físico do usuário não é a baseline canônica. Branches, commits e PRs remotos estão autorizados dentro dos gates vigentes.

Integração em branches canônicas de sprint/staging exige testes, typing, lint, checks de integridade, segurança/capacidades negativas aplicáveis, dependências satisfeitas e nenhum finding bloqueante. Promoção global para `main` não é automática.

O Sprint 1 preservou `READ_ONLY_BY_CONSTRUCTION` e `STRUCTURAL_ESCALATION`; o Sprint 2 herda essas barreiras e todas as negative financial capabilities. Dinheiro real, credenciais de negociação, ordens de broker e ativação financeira permanecem proibidos.

No Sprint 2, os incrementos funcionais S2-A e S2-B foram implementados pelo Antigravity em branches filhas com CI completo e integrados à baseline canônica. A tarefa S2-C consolidou a reconciliação formal de fechamento sem alteração de código funcional. Qualquer transição para o Sprint 3 exige aprovação independente, merge e a materialização formal do gate de entrada do Sprint 3.

Arquitetura e dry-run de sprints futuros podem avançar isoladamente como pesquisa, mas promoção ou ativação exige gate próprio. Decisões in-sprint são registradas antes da primeira dependência material; mudanças arquiteturais materiais seguem ADR. A Issue #6 preserva a errata histórica do 0F-F e `TRACEABILITY.md` continua autoridade canônica das QPIs.

O checkpoint vivo é [PROGRAM_EXECUTION.md](docs/program/PROGRAM_EXECUTION.md).