# Architectural Decision Records

ADRs registram decisões relevantes, alternativas, consequências e estado de aprovação. Use numeração sequencial (`0001`, `0002`, ...). Uma decisão aprovada não deve ser reescrita silenciosamente; mudanças posteriores recebem novo ADR que refina ou substitui explicitamente o anterior, preservando o registro histórico original.

Estados sugeridos: `Proposta`, `Aceita`, `Rejeitada`, `Substituída`.

## Índice

- [0001 — Bootstrap estrutural seguro](0001-safe-structural-bootstrap.md)
- [0002 — Monólito modular orientado a eventos](0002-event-driven-modular-monolith.md)
- [0003 — Envelope de eventos, causalidade e ordenação](0003-event-envelope-causality-and-ordering.md) — *refinado por ADR 0015*
- [0004 — Semântica temporal e fidelidade histórica](0004-temporal-semantics-and-historical-fidelity.md)
- [0005 — Identidade, lifecycle e rollover de instrumentos](0005-instrument-identity-lifecycle-and-rollover.md)
- [0006 — MarketDataProvider, entrega e backpressure](0006-market-data-provider-delivery-and-backpressure.md)
- [0007 — Fronteira Signal, Risk, Execution e intents](0007-signal-risk-execution-and-intents.md) — *refinado por ADR 0016*
- [0008 — Perfis operacionais, replay e determinismo](0008-operating-profiles-replay-and-determinism.md) — *refinado por ADR 0017*
- [0009 — Persistência, journal de auditoria e snapshots](0009-persistence-audit-journal-and-snapshots.md) — *refinado por ADR 0018*
- [0010 — Recovery, reconciliação e resultados desconhecidos](0010-recovery-reconciliation-and-unknown-outcomes.md) — *refinado por ADR 0019*
- [0011 — Fail-safe e estados operacionais](0011-fail-safe-operational-states.md) — *refinado por ADR 0020*
- [0012 — Eventos inválidos e erros críticos](0012-invalid-events-and-critical-errors.md)
- [0013 — Observabilidade, proveniência e rastreabilidade de decisões](0013-observability-decision-provenance-and-traceability.md) — *refinado por ADR 0021*
- [0014 — Ownership de Position, Portfolio, Ledger e exposição](0014-position-portfolio-ledger-and-exposure-ownership.md) — *refinado por ADR 0022*
- [0015 — Refinamento do envelope, contexto de processamento e versionamento](0015-refinement-event-envelope-processing-context-and-versioning.md)
- [0016 — Refinamento da cadeia Strategy, Risk, autorização e Execution](0016-refinement-strategy-risk-authorization-and-execution-chain.md)
- [0017 — Refinamento de determinismo, input boundaries e aleatoriedade](0017-refinement-determinism-input-boundaries-and-randomness.md)
- [0018 — Refinamento de persistência, durabilidade e persist-before-act](0018-refinement-persistence-durability-and-persist-before-act.md)
- [0019 — Refinamento de recovery, reconciliation boundaries e readiness](0019-refinement-recovery-reconciliation-boundaries-and-readiness.md)
- [0020 — Refinamento de RuntimePhase, SafetyPosture e Readiness](0020-refinement-runtime-phase-safety-posture-and-readiness.md)
- [0021 — Refinamento de provenance, Runs, capture e lineage](0021-refinement-provenance-runs-capture-and-lineage.md)
- [0022 — Refinamento de Ledger, projeções financeiras e Exposure](0022-refinement-ledger-financial-projections-and-exposure.md)
- [0023 — Provedor inicial de Market Data: BTG Solutions Data Services](0023-initial-market-data-provider-btg-solutions-data-services.md)
