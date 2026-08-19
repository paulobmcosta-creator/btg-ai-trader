# ADR 0009 — Persistência, journal de auditoria e snapshots

- **Status:** Aceita
- **Data:** 2026-08-18
- **Refinada por:** ADR 0018 — Refinamento de persistência, durabilidade e persist-before-act

## Contexto

Dados de mercado e decisões operacionais possuem volumes, criticidade e finalidades distintas.

## Problema

Permitir auditabilidade e restart sem adotar event sourcing indiscriminado.

## Alternativas consideradas

- Um armazenamento único: mistura retenção e garantias.
- Event sourcing total: custo desproporcional.
- Três planos lógicos: adequado ao tipo de evidência.

## Decisão

Separar logicamente: market-data archive append-only para pesquisa/replay; operational/audit journal para intents, decisões, execução, erros críticos e reconciliation; e state snapshots para acelerar restauração. Snapshot é otimização; journal é evidência histórica. Decisões financeiras relevantes são append-only: correção exige novo fato, decisão ou compensação. Persistir antes de agir sempre que possível; não há transação ACID única com uma corretora futura, logo idempotência e reconciliation continuam necessárias.

## Invariantes

- Passado não é reescrito silenciosamente.
- Snapshot não substitui journal.
- Persistência não prova que efeito externo ocorreu.

## Consequências positivas

Combina recuperação eficiente, proveniência e custo proporcional.

## Consequências negativas / trade-offs

Exige consistência de referências entre planos lógicos.

## Condições para reabrir a decisão

Requisito de retenção ou auditoria que demonstre insuficiência, preservando append-only crítico.

## Relação com outros ADRs

Suporta recovery (0010), provenance (0013) e ownership financeiro (0014).
