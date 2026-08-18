# ADR 0003 — Envelope de eventos, causalidade e ordenação

- **Status:** Aceita
- **Data:** 2026-08-18

## Contexto

Eventos de mercado e operacionais precisam de identidade, proveniência e ordenação auditáveis.

## Problema

Separar metadados estáveis do payload e evitar inferências falsas sobre ordem global.

## Alternativas consideradas

- Payload sem envelope: perde evolução e rastreabilidade uniforme.
- Um timestamp como ordenação total: incorreto para eventos simultâneos ou tardios.
- Envelope versionado com causalidade e ordem contextual: preserva evidência.

## Decisão

Todo evento relevante terá envelope canônico versionado, conceitualmente com `event_id`, tipo, versão de schema, origem, identificador externo quando houver, instrumento, `event_time`, `ingestion_time`, sequência da fonte com seu escopo, `correlation_id`, `causation_id` e payload. Não existe um único `processing_time` do evento: tempos de processamento pertencem a receipts/telemetria por componente.

A ordenação não será deduzida apenas de `event_time`. Sequência nativa só vale no escopo documentado (`provider`, conexão, stream, canal, instrumento ou outro); ela nunca é global por presunção. Onde houver, preserva-se a ordem registrada de ingestão; o desempate é determinístico por identidade interna.

## Invariantes

- `source_sequence` sem `sequence_scope` não tem semântica suficiente.
- Streams independentes não são ordenados numericamente como uma sequência global.
- Correlação e causalidade não são substituídas por timestamps.

## Consequências positivas

Permite evolução compatível, deduplicação, reconstrução causal e replay honesto.

## Consequências negativas / trade-offs

Exige metadados adicionais e documentação da fonte.

## Condições para reabrir a decisão

Necessidade comprovada de novos metadados obrigatórios ou incompatibilidade de schema, com migração explícita.

## Relação com outros ADRs

Complementa ADR 0004; suporta 0006, 0009, 0010 e 0013.
