# 0F-B — Portable Provenance Navigation

Este arquivo é um **companion de navegação não normativo** para `0F-B_deferred_decision_register.md`.

O registro canônico 0F-B permanece preservado byte-a-byte no blob Git:

```text
819397f0a3fe322ef199d053b2ccbe9a6fdb5747
```

Os links `file:///c:/Projetos/btg-ai-trader/...` existentes no snapshot canônico são artefatos do ambiente Windows em que o documento foi produzido e **não devem ser reescritos dentro do 0F-B**, pois isso destruiria a prova de byte-identidade exigida pelo gate de materialização. Para navegação portátil no GitHub, Linux ou outros checkouts, use os links repository-relative abaixo.

Este companion não altera nenhuma decisão, contador, classificação, ownership, stage ou deadline do 0F-B; ele apenas fornece uma rota portátil para as fontes já citadas pelo registro canônico.

## ADRs 0001–0014

- [ADR-0001 — Safe Structural Bootstrap](../adr/0001-safe-structural-bootstrap.md)
- [ADR-0002 — Event-Driven Modular Monolith](../adr/0002-event-driven-modular-monolith.md)
- [ADR-0003 — Event Envelope, Causality and Ordering](../adr/0003-event-envelope-causality-and-ordering.md)
- [ADR-0004 — Temporal Semantics and Historical Fidelity](../adr/0004-temporal-semantics-and-historical-fidelity.md)
- [ADR-0005 — Instrument Identity, Lifecycle and Rollover](../adr/0005-instrument-identity-lifecycle-and-rollover.md)
- [ADR-0006 — Market Data Provider Delivery and Backpressure](../adr/0006-market-data-provider-delivery-and-backpressure.md)
- [ADR-0007 — Signal, Risk, Execution and Intents](../adr/0007-signal-risk-execution-and-intents.md)
- [ADR-0008 — Operating Profiles, Replay and Determinism](../adr/0008-operating-profiles-replay-and-determinism.md)
- [ADR-0009 — Persistence, Audit Journal and Snapshots](../adr/0009-persistence-audit-journal-and-snapshots.md)
- [ADR-0010 — Recovery, Reconciliation and Unknown Outcomes](../adr/0010-recovery-reconciliation-and-unknown-outcomes.md)
- [ADR-0011 — Fail-Safe Operational States](../adr/0011-fail-safe-operational-states.md)
- [ADR-0012 — Invalid Events and Critical Errors](../adr/0012-invalid-events-and-critical-errors.md)
- [ADR-0013 — Observability, Decision Provenance and Traceability](../adr/0013-observability-decision-provenance-and-traceability.md)
- [ADR-0014 — Position, Portfolio, Ledger and Exposure Ownership](../adr/0014-position-portfolio-ledger-and-exposure-ownership.md)

## Refinement ADRs 0015–0022

- [ADR-0015 — Event Envelope, Processing Context and Versioning](../adr/0015-refinement-event-envelope-processing-context-and-versioning.md)
- [ADR-0016 — Strategy, Risk Authorization and Execution Chain](../adr/0016-refinement-strategy-risk-authorization-and-execution-chain.md)
- [ADR-0017 — Determinism, Input Boundaries and Randomness](../adr/0017-refinement-determinism-input-boundaries-and-randomness.md)
- [ADR-0018 — Persistence, Durability and Persist-Before-Act](../adr/0018-refinement-persistence-durability-and-persist-before-act.md)
- [ADR-0019 — Recovery, Reconciliation Boundaries and Readiness](../adr/0019-refinement-recovery-reconciliation-boundaries-and-readiness.md)
- [ADR-0020 — Runtime Phase, Safety Posture and Readiness](../adr/0020-refinement-runtime-phase-safety-posture-and-readiness.md)
- [ADR-0021 — Provenance, Runs, Capture and Lineage](../adr/0021-refinement-provenance-runs-capture-and-lineage.md)
- [ADR-0022 — Ledger, Financial Projections and Exposure](../adr/0022-refinement-ledger-financial-projections-and-exposure.md)

## Protocolos quantitativos 0E-A–0E-H

- [0E-A — Experimental Semantics](../protocols/quantitative/0E-A-experimental-semantics.md)
- [0E-B — Dataset and Temporal Integrity](../protocols/quantitative/0E-B-dataset-temporal-integrity.md)
- [0E-C — Validation, OOS and Baselines](../protocols/quantitative/0E-C-validation-oos-baselines.md)
- [0E-D — Backtest and Market Simulation](../protocols/quantitative/0E-D-backtest-market-simulation.md)
- [0E-E — Statistical and Economic Validation](../protocols/quantitative/0E-E-statistical-economic-validation.md)
- [0E-F — Strategy and Model Evaluation](../protocols/quantitative/0E-F-strategy-model-evaluation.md)
- [0E-G — Promotion, Paper and Rejection](../protocols/quantitative/0E-G-promotion-paper-rejection.md)
- [0E-H — Cross-Protocol Gate](../protocols/quantitative/0E-H-cross-protocol-gate.md)

## Demais fontes citadas pelo inventário

- [README.md da raiz](../../README.md)
- [Plano Mestre](../BTG_AI_TRADER_MASTER_PLAN.md)
- [SPRINT_0.md](../sprints/SPRINT_0.md)
- [SAFETY.md](../protocols/SAFETY.md)
- [config/README.md](../../config/README.md)

## Regra de autoridade

Em caso de qualquer divergência entre este companion e o registro canônico, **prevalece o conteúdo do `0F-B_deferred_decision_register.md` no blob `819397f0a3fe322ef199d053b2ccbe9a6fdb5747`**. Este arquivo existe exclusivamente para navegação portátil de proveniência.