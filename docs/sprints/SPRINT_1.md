# Sprint 1 — Market Observer

## Estado de abertura

```text
SPRINT_1_STATUS = OPEN
CURRENT_GATE = S1_A_IMPLEMENTATION
PR_5 = MERGED
ISSUE_1 = COMPLETED
PRE_CODE_RECONCILIATION = COMPLETE
S1_A_AUTHORIZED = YES
FIRST_FUNCTIONAL_CODE = AUTHORIZED
```

O PR #5 foi integrado em `dabce69d92054b77cad72809669d4340c211c328` e a Issue #1 foi fechada como concluída. O mandato humano de execução autônoma de 2026-09-13 autoriza a primeira implementação funcional do Sprint 1 (`PRE_CODE_RECONCILIATION = COMPLETE`; `S1_A_AUTHORIZED = YES`; `FIRST_FUNCTIONAL_CODE = AUTHORIZED`), sob o contrato 0F-E integral e os gates de promoção.

## Objetivo

Implementar, conforme autorização humana vigente, um **Market Observer** estritamente:

```text
READ_ONLY_BY_CONSTRUCTION
STRUCTURAL_ESCALATION
```

O escopo positivo e os critérios de aceitação são governados integralmente pelo Contrato de Entrada canônico `docs/foundation/0F-E_sprint1_entry_contract.md`. O artefato `docs/foundation/0F-F_foundation_final_gate.md` é preservado como snapshot histórico da adjudicação final da Fundação.

## Autoridade e rastreabilidade

O Sprint 1 deve ser conduzido em conformidade cumulativa com:

- 0F-B — registro canônico de 124 decisões deferidas; para navegação portátil das fontes de proveniência, usar [0F-B — Portable Provenance Navigation](../foundation/0F-B_provenance_navigation.md), sem alterar o snapshot canônico;
- 0F-C — 41 RQMs, 27 HQIs aplicáveis ao Sprint 1 e 7 QPIs aplicáveis;
- 0F-D — 20 Negative Capabilities e 10 obrigações de testes negativos;
- 0F-E — 118 cláusulas `S1-EC-001` a `S1-EC-118`;
- 0F-F — snapshot histórico da adjudicação da Fundação.

A cardinalidade de **28 Decision Gate Clauses** do 0F-E não é equivalente à cardinalidade de **26 decisões `MAY_DECIDE_DURING_SPRINT_1`** do 0F-B. Esses universos permanecem distintos.

## Gate pré-código concluído e implementação

O PR #5 concluiu o gate documental; a Issue #1 está fechada. Seu escopo histórico permanece documental. O mandato humano subsequente autoriza agora código, testes e configuração seguros do Observer. Esta autorização não declara S1-A implementado nem Sprint 1 aceito.

Implementação começa por modelos de domínio, contratos provider-agnostic e providers de teste. Risk, replay formal, ML e Paper de sprints futuros ficam em branches SPECULATIVE separadas e não podem entrar na baseline S1. As 118 cláusulas S1-EC, 41 RQMs e 10 obrigações NEG-CAP continuam integrais. O primeiro PR funcional exige Security Diff Scan do diff exato conforme Issue #1.

Consulte [PROGRAM_EXECUTION](../program/PROGRAM_EXECUTION.md) para DAG, evidências, branches, PRs e próximos nós prontos.

## Disciplina de decisões deferidas

As decisões deferidas permanecem governadas pelo 0F-B e pelo 0F-E. Em particular:

```text
TOTAL_NORMALIZED_DECISIONS = 124
MAY_DECIDE_DURING_SPRINT_1 = 26
MAY_DEFER_BEYOND_SPRINT_1 = 50
MUST_REMAIN_UNDECIDED_NOW = 48
```

Este documento não seleciona nem congela antecipadamente provider, vendor, SDK, MT5, ticker, instrumento definitivo, timeframe, resolução definitiva, storage, database, schema físico, cloud, thresholds quantitativos finais, broker, Paper, Live, ML ou Strategy.
