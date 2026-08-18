# ADR 0011 — Fail-safe e estados operacionais

- **Status:** Aceita
- **Data:** 2026-08-18

## Contexto

Incerteza de dados, estado ou dependência não pode permitir aumento de exposição.

## Problema

Definir uma degradação segura sem tratar parada de processo como controle financeiro suficiente.

## Alternativas consideradas

- Continuar com dados/estado incertos: inseguro.
- Parar o processo: não resolve exposição ou realidade externa.
- Estados explícitos e fail-closed: comportamento auditável e proporcional.

## Decisão

Usar estados operacionais explícitos, incluindo estados de inicialização, degradação, `SAFE_HALT` e `READY` a serem detalhados em 0D. Falha ou incerteza relevante bloqueia novas exposições. `SAFE_HALT` não implica automaticamente flatten, cancelamento ou ação externa; tais efeitos exigem decisão e autorização futura específicas. Staleness, backpressure, inconsistência e falha crítica podem acionar degradação.

## Invariantes

- Falha segura é fechada para aumento de exposição.
- Transições de estado são observáveis e auditáveis.
- Nenhum estado autoriza operação real nesta fase.

## Consequências positivas

Evita decisões com premissas operacionais inválidas.

## Consequências negativas / trade-offs

Pode aumentar indisponibilidade e requer critérios objetivos de transição.

## Condições para reabrir a decisão

Evidência de que um novo estado preserva ou melhora a segurança e auditabilidade.

## Relação com outros ADRs

Recebe sinais de 0006, 0010 e 0012; é observado por 0013.
