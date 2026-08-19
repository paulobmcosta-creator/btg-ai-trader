# ADR 0017 — Refinamento de determinismo, input boundaries e aleatoriedade

- **Status:** Aceita
- **Data:** 2026-08-19
- **Refina:** ADR 0008 — Perfis operacionais, replay e determinismo

## Contexto

O ADR 0008 fixou perfis de composição e determinismo de Backtest sob mesmas entradas, configuração, código, estado inicial e seeds. O Sprint 0D refinou a provenance necessária para sustentar claims fortes de determinismo e reprodução.

## Decisão / refinamento

- Uma seed explícita é requisito mínimo quando houver aleatoriedade, mas não constitui provenance universalmente suficiente.
- Quando materialmente relevante, o contexto de aleatoriedade deve preservar generator/version, initialization/seed semantics, stream identities/partitioning e demais limitações capazes de alterar a sequência consumida.
- Claims fortes de determinismo exigem `RunInputBoundary` suficientemente definido para identificar os inputs/cortes efetivamente usados; nomes de dataset ou datas vagas não são suficientes.
- Determinismo, replayability, auditability e reproducibility permanecem conceitos distintos. Uma execução pode ser auditável sem ser plenamente reproduzível.
- Perfis REPLAY, BACKTEST, PAPER e LIVE continuam sendo composição de providers/clock/execution/persistence/accounting, sem branches de domínio por modo.

## Invariantes

- Seed isolada não autoriza claim de determinismo quando generator/stream semantics materiais são desconhecidos.
- Inputs efetivos devem ser rastreáveis; Manifest declarado não substitui processing/lineage provenance.
- Conhecimento posterior ao `knowledge_cutoff` não pode contaminar replay/backtest histórico.

## Consequências

Claims de determinismo passam a ser verificáveis sem impor tecnologia de experiment tracking ou RNG específico.

## Decisões deliberadamente adiadas

Permanecem adiados: RNG concreto, algoritmo de seed, formato do RunInputBoundary, equivalência numérica/byte-a-byte, artifact registry, Git/MLflow e ambiente físico de execução.

## Relação com outros ADRs

Refina ADR 0008 e complementa ADRs 0004, 0015 e 0021.
