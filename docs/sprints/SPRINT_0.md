# Sprint 0 — Fundação e especificação

## Objetivo

Converter a visão inicial em arquitetura, contratos, protocolos e critérios de aceite verificáveis, preservando a ausência de capacidade de negociação.

## Etapa 0B — Ambiente de Desenvolvimento

**Estado:** concluída em 2026-08-17.

O projeto fixa Python 3.12 e fornece um extra `dev` instalável com `pytest`, `pytest-cov`,
Ruff e mypy. O backend de build e as ferramentas de desenvolvimento estão com versões
exatas para reduzir variações na instalação local. Não foram introduzidas dependências de
runtime, financeiras, de dados, ML ou integração externa.

Verificações exigidas: instalação em ambiente virtual limpo; `pytest` com cobertura; Ruff;
mypy; e `compileall`. O cache local do pytest é desabilitado para evitar que artefatos de
execução interfiram nas verificações do projeto.

### Pendência explícita

Antes de qualquer integração externa futura, validar e registrar por ADR a compatibilidade
de Python 3.12 com MetaTrader 5 e todas as dependências críticas que vierem a ser aprovadas.
Essa validação não autoriza integração, negociação ou uso de credenciais.

## Etapa 0C — Arquitetura lógica

**Estado:** ✅ APROVADO/CONCLUÍDO em 2026-08-18, após revisão documental e aprovação humana.

Foram materializadas as decisões 0C-01 a 0C-26 nos ADRs 0002–0014. A baseline fixa monólito modular orientado a eventos, envelope causal, semântica temporal e fidelidade histórica, identidade de instrumentos, fronteiras Signal/Risk/Execution, perfis operacionais, persistência, recovery, fail-safe, tratamento de eventos inválidos, ownership de posição/exposição e provenance de decisões.

Permanece proibida qualquer implementação funcional, Market Observer, integração BTG/MT5, ordem, ML, backtesting, dependência nova ou escolha de tecnologia física. Contratos e schemas pertencem exclusivamente à etapa 0D.

### Gate de encerramento 0C

- ADRs 0002–0014 presentes, aceitos e mutuamente referenciados;
- decisões 0C-01 a 0C-26 cobertas sem contradição documental;
- invariantes de veto de Risk, fail-closed, causalidade, temporalidade e ownership preservados;
- Plano Mestre e visão de arquitetura atualizados;
- nenhum código, dependência ou integração financeira adicionados;
- aprovação humana explícita registrada em 2026-08-18.

## Etapa 0D — Contratos e Modelo de Dados

**Estado:** ✅ formalmente fechado e aprovado em 2026-08-19 após o F1 final de consistência normativa/documental.

Os blocos 0D-A, 0D-B, 0D-C, 0D-D e 0D-E estão fechados e congelados. O 0D-F — Cross-contract Gate foi aprovado sem blocker arquitetural. A sincronização normativa/documental preservou os ADRs históricos e registrou os refinamentos do Sprint 0D nos ADRs 0015–0022.

O F1 final confirmou que ADRs históricos + refinements e os documentos vivos formam uma baseline normativa única, sem `CURRENT_NORM_CONFLICT`. Nenhuma implementação funcional de 0D foi iniciada e nenhuma tecnologia física foi escolhida. A sincronização normativa do 0D foi consolidada no commit local `c7e3b24` (`docs: finalize Sprint 0D normative synchronization`).

### Gate de encerramento 0D — F1

- relações de refinement 0003→0015, 0007→0016, 0008→0017, 0009→0018, 0010→0019, 0011→0020, 0013→0021 e 0014→0022 validadas;
- ADRs 0001–0022 contínuos e integralmente indexados;
- nenhum conflito normativo corrente detectado nas buscas transversais;
- links relativos e referências de refinement válidos;
- `git diff --cached --check` sem erros na árvore canônica local;
- `pytest`: 1 teste aprovado;
- Ruff: aprovado;
- mypy: aprovado;
- `compileall`: aprovado;
- `pip check`: sem requisitos quebrados;
- commit `c7e3b24` criado com 22 arquivos documentais (`652 insertions`, `158 deletions`);
- `git status` após o commit: `working tree clean`.

---

## Etapa 0E — Protocolos Quantitativos

**Estado:** ✅ Formalmente fechado e aprovado em 2026-08-22 após aprovação humana do FINAL_0E_DOC_GATE.

Os sub-blocos 0E-A a 0E-G foram tecnicamente fechados e o 0E-H — Cross-Protocol Gate foi aprovado (PASS). A especificação metodológica foi materializada em [docs/protocols/quantitative/](../protocols/quantitative/README.md) e documentada em [docs/sprints/SPRINT_0E.md](SPRINT_0E.md).

Foram formalizados 269 Hard Quantitative Invariants (HQIs) e consolidados sob 15 Invariantes Canônicos Transversais (QPI-01 a QPI-15) com rastreabilidade completa em [TRACEABILITY.md](../protocols/quantitative/TRACEABILITY.md). Foram resolvidos formalmente os achados documentais H-DOC-01 a H-DOC-06:
- **H-DOC-01:** Relação Paper × Risk esclarecida (a authority e fronteira independente de Risk existem desde 0C/0D, a capability de Risk para Paper é implementada antes do Sprint 8, e o Gate E avalia a suficiência pré-produção completa do Risk Engine);
- **H-DOC-02:** "Slippage observado" em Paper refinado como discrepância observável qualificada pela proveniência da observação;
- **H-DOC-03:** Promoção quantitativa formalizada como progressão evidenciária, nunca autoridade de trading;
- **H-DOC-04:** Predicados de aplicabilidade (*ApplicabilityPredicate*) formalizados como não transformadores de HQI em policy;
- **H-DOC-05:** Canonicalização transversal dos 269 HQIs sob QPI-01 a QPI-15 em TRACEABILITY.md;
- **H-DOC-06:** Conceitos semânticos delimitados como metodológicos, sem constituir schemas físicos de runtime prematuros.

Nenhum código funcional, dependência, ativo, timeframe, modelo ou tecnologia física foi introduzido. O Sprint 0E está formalmente fechado.

### Gate de encerramento 0E — FINAL_0E_DOC_GATE

- 269 Hard Quantitative Invariants (HQIs) e 15 QPIs integralmente auditados e canonicalizados sem semantic drift contra o dossiê canônico;
- Matriz de rastreabilidade em TRACEABILITY.md atualizada, com remoção da coluna individual de aplicabilidade e adoção da regra transversal unificada;
- Nenhum conflito normativo corrente (CURRENT_NORM_CONFLICT = NONE);
- Nenhuma alteração em ADRs, src/, tests/ ou dependências;
- Aprovação humana formal registrada em 2026-08-22;
- Status do Sprint 0E: FORMALLY CLOSED.

---

## Etapa 0F — Foundation Cross-Gate

**Estado:** ✅ Formalmente fechado e aprovado em 2026-08-25 após aprovação do Foundation Final Gate (0F-F).

Os blocos 0F-A (consistência normativa), 0F-B (triagem de 124 decisões deferidas), 0F-C (matriz canônica de 41 RQMs), 0F-D (20 Negative Capabilities) e 0F-E (Contrato de Entrada do Sprint 1 com 118 cláusulas) foram formalmente auditados e fechados sem Hard Blockers. As quatro ações documentais pré-Sprint 1 (A-F01, A-F02, A-F03 e B-F01) foram materializadas e fechadas.

Com isso, toda a fase de Fundação (Sprint 0, etapas 0A a 0F) está formalmente concluída e aprovada.

## Próximo marco

- O lifecycle do **Sprint 1 — Market Observer** está `OPEN`; o PR #5 foi integrado e a Issue #1 concluída (`PRE_CODE_RECONCILIATION = COMPLETE`).
- A primeira implementação funcional está autorizada (`S1_A_AUTHORIZED = YES`) pelo mandato humano de 2026-09-13, sob cumprimento integral do 0F-E. O [checkpoint vivo](../program/PROGRAM_EXECUTION.md) distingue autorização, implementação e promoção.

## Fora de escopo

Estratégias operacionais concretas, modelos em produção, integração BTG/MT5, coleta ao vivo, ordens, dinheiro real, cloud, produção e deploy.

## Critérios de aceite

- baseline arquitetural, ADRs e protocolos quantitativos revisados;
- riscos, limites não escolhidos e decisões deliberadamente adiadas visíveis;
- protocolos iniciais com evidências exigidas e rastreabilidade total;
- ferramentas de qualidade escolhidas e executáveis;
- nenhum segredo ou capacidade de execução financeira no repositório.
