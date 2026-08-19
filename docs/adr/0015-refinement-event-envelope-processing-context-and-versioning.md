# ADR 0015 — Refinamento do envelope, contexto de processamento e versionamento

- **Status:** Aceita
- **Data:** 2026-08-19
- **Refina:** ADR 0003 — Envelope de eventos, causalidade e ordenação

## Contexto

O ADR 0003 fixou envelope versionado, causalidade e ordenação contextual. O Sprint 0D refinou quais metadados são intrínsecos ao fato externo, quais são condicionais e como processamento posterior e evolução de schema são registrados sem fabricar contexto inexistente.

## Decisão / refinamento

A decisão histórica do ADR 0003 permanece válida, com os seguintes refinamentos normativos:

- `correlation_id`, `causation_id` e `event_time` são campos condicionais. Fatos exógenos independentes não recebem correlação ou causalidade fabricadas apenas para preencher o envelope.
- Quando `event_time` existir, sua semântica inclui `event_time_basis` e `event_time_resolution` compatíveis com a evidência da fonte. Resolução ou precisão inexistentes não são fabricadas.
- `run_id` não é metadado universal de fatos externos. Fatos externos/históricos preservam identidade própria; o contexto do Run que os capturou ou processou é registrado por provenance, conforme ADR 0021.
- Um fato externo pode referenciar `CaptureContext`; processamento posterior em um ou mais Runs é registrado por `ProcessingReceipt`, sem mutar o fato original.
- `source_sequence` permanece interpretável somente dentro de `sequence_scope` explícito; não existe sequência global por presunção.
- Versão de envelope e versão de payload/schema podem evoluir de forma explícita e independente quando aplicável. Versão desconhecida ou incompatível não é reinterpretada silenciosamente como a versão corrente.

## Invariantes

- Ausência legítima de `correlation_id`, `causation_id` ou `event_time` não autoriza preencher valor sintético.
- `event_time` isolado não define ordem observada global.
- `run_id` de captura/processamento não se torna identidade do fato externo.
- Compatibilidade de schema deve ser declarada; incompatibilidade exige tratamento explícito, nunca fallback silencioso para `current`.

## Consequências

O envelope continua uniforme sem transformar metadados contextuais em requisitos artificiais. Replay, recovery e provenance podem relacionar fatos históricos a múltiplos Runs preservando sua identidade original.

## Decisões deliberadamente adiadas

Permanecem fora deste ADR: representação física de IDs, formato de serialização, schema framework, algoritmo de versionamento, storage, mensageria e mecanismo físico de migração/upcast.

## Relação com outros ADRs

Refina ADR 0003 e complementa ADRs 0004, 0006, 0008 e 0021.
