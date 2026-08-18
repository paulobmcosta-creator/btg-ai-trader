# ADR 0012 — Eventos inválidos e erros críticos

- **Status:** Aceita
- **Data:** 2026-08-18

## Contexto

Dados inválidos e exceções podem contaminar decisões ou ocultar falhas financeiras.

## Problema

Definir reação proporcional, auditável e sem correção silenciosa.

## Alternativas consideradas

- Corrigir/descartar silenciosamente: perde evidência e pode mascarar corrupção.
- Falhar todo processo para qualquer erro: indisponibilidade desproporcional.
- Taxonomia, quarantine e escalonamento: mantém evidência e segurança.

## Decisão

Eventos inválidos terão taxonomia e tratamento proporcional: rejeição, quarantine, registro de qualidade, degradação ou bloqueio de novas exposições conforme criticidade. Dados não serão corrigidos silenciosamente. Erros críticos têm classificação semântica e contexto causal; `catch-all-and-continue` é proibido em componentes financeiros críticos. Valores e políticas concretas são posteriores.

## Invariantes

- Todo tratamento preserva causa e evidência suficiente.
- Eventos tardios obedecem ADR 0004, não são invisíveis.
- Incerteza que comprometa decisão financeira aciona fail-safe.

## Consequências positivas

Permite medir qualidade, investigar falhas e evitar continuidade insegura.

## Consequências negativas / trade-offs

Requer classificação e canais de quarantine futuros.

## Condições para reabrir a decisão

Nova categoria de erro ou exigência regulatória, documentada sem reduzir rastreabilidade.

## Relação com outros ADRs

Complementa tempo (0004), provider (0006), fail-safe (0011) e observabilidade (0013).
