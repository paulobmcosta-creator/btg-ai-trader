# Sprint 1 — Market Observer

## Estado de abertura

```text
SPRINT_1_STATUS = OPEN
CURRENT_GATE = PRE_CODE_RECONCILIATION
ISSUE = #1
FIRST_FUNCTIONAL_CODE = NOT_YET_AUTHORIZED
```

O Sprint 1 está aberto apenas para o gate documental pré-código da Issue #1. A primeira implementação funcional permanece proibida até revisão humana e merge do PR deste gate.

## Objetivo

Implementar, após autorização do primeiro código, um **Market Observer** estritamente:

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

## Gate pré-código

O gate corrente permite exclusivamente reconciliação e materialização documental. Até seu merge:

```text
S1_A_AUTHORIZED = NO
FUNCTIONAL_IMPLEMENTATION = NOT_YET_AUTHORIZED
```

Nenhum arquivo em `src/`, `tests/`, dependência ou configuração funcional deve ser alterado por este gate.

## Disciplina de decisões deferidas

As decisões deferidas permanecem governadas pelo 0F-B e pelo 0F-E. Em particular:

```text
TOTAL_NORMALIZED_DECISIONS = 124
MAY_DECIDE_DURING_SPRINT_1 = 26
MAY_DEFER_BEYOND_SPRINT_1 = 50
MUST_REMAIN_UNDECIDED_NOW = 48
```

Este documento não seleciona nem congela antecipadamente provider, vendor, SDK, MT5, ticker, instrumento definitivo, timeframe, resolução definitiva, storage, database, schema físico, cloud, thresholds quantitativos finais, broker, Paper, Live, ML ou Strategy.
