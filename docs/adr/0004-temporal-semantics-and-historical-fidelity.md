# ADR 0004 — Semântica temporal e fidelidade histórica

- **Status:** Aceita
- **Data:** 2026-08-18

## Contexto

Tempo e ordem observada podem introduzir look-ahead bias e tornar resultados irreprodutíveis.

## Problema

Definir tempo absoluto, duração, sessões, eventos tardios e limites de fidelidade de dados históricos.

## Alternativas consideradas

- Datas locais/naive e ordenação por timestamp: ambíguas e frágeis.
- Reordenar ilimitadamente ou corrigir o passado: altera decisões tomadas.
- UTC explícito, relógio monotônico e desordem limitada: preserva causalidade.

## Decisão

Timestamps absolutos são UTC timezone-aware; duração e latência usam relógio monotônico. `event_time` é o tempo externo, `ingestion_time` a chegada efetiva e processamento é medido por componente. A sessão de negociação será derivada futuramente por calendário versionado e regras explícitas de `America/Sao_Paulo`.

Em Paper/Live, a reordenação só é permitida dentro de janela operacional explícita; evento tardio é arquivado, marcado e contabilizado, nunca reescreve decisão passada. Captura própria pode preservar `ingestion_order`; dados históricos que só tragam `event_time` ou sequência da fonte não podem inventar ordem histórica de ingestão. Replay deve declarar-se observation-faithful, source-sequence-faithful ou event-time-only e suas limitações.

## Invariantes

- `datetime` naive é proibido.
- Importação atual não é ingestion histórico.
- Fidelidade histórica insuficiente é limitação registrada, não precisão fabricada.

## Consequências positivas

Reduz leakage temporal e torna latência e replay interpretáveis.

## Consequências negativas / trade-offs

Calendário, clocks e qualidade temporal acrescentam complexidade futura.

## Condições para reabrir a decisão

Evidência de requisito temporal não atendido, sem remover a auditabilidade ou a declaração de fidelidade.

## Relação com outros ADRs

Refina ADR 0003 e fundamenta ADRs 0006 e 0008.
