# ADR 0006 — MarketDataProvider, entrega e backpressure

- **Status:** Aceita
- **Data:** 2026-08-18

## Contexto

Fontes de mercado oferecem capacidades e garantias distintas, e atrasos podem tornar decisões inseguras.

## Problema

Evitar uma abstração fictícia de provider e suposições de entrega exatamente uma vez.

## Alternativas consideradas

- Interface única obrigatória: métodos sem significado para muitos providers.
- Exactly-once: impraticável sob timeout e restart.
- Capacidades declaradas, at-least-once e filas limitadas: explícito e recuperável.

## Decisão

O contrato futuro será baseado em capacidades declaradas (ticks, trades, quotes, candles, book, histórico, timestamps, sequência). Adaptadores traduzem dados externos em eventos normalizados e preservam proveniência de raw, normalizado e normalização quando necessária. O desenho assume entrega potencialmente duplicada: deduplicação e idempotência são obrigatórias. Filas críticas são conceitualmente finitas; backlog e staleness são observáveis e estado de mercado obsoleto bloqueia novas exposições.

## Invariantes

- Dados raw não entram diretamente no Signal Engine.
- Não há fila ilimitada nem descarte silencioso.
- Exactly-once não é premissa arquitetural.

## Consequências positivas

Evita abstrações falsas e degradação silenciosa sob carga.

## Consequências negativas / trade-offs

Exige política de deduplicação, métricas e degradação por capacidade.

## Condições para reabrir a decisão

Garantias contratuais superiores de fonte específica podem complementar, sem remover idempotência.

## Relação com outros ADRs

Usa envelope/tempo dos ADRs 0003–0004 e aciona fail-safe do ADR 0011.
