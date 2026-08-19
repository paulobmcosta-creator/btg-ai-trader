# ADR 0020 — Refinamento de RuntimePhase, SafetyPosture e Readiness

- **Status:** Aceita
- **Data:** 2026-08-19
- **Refina:** ADR 0011 — Fail-safe e estados operacionais

## Contexto

O ADR 0011 deliberadamente deixou os estados operacionais para detalhamento em 0D, preservando fail-closed e `SAFE_HALT` sem auto-flatten. O Sprint 0D separou três dimensões que não devem compartilhar um enum monolítico.

## Decisão / refinamento

- `RuntimePhase` representa a fase operacional, com semânticas como STARTING, RECOVERING, RECONCILING, RUNNING, STOPPING e STOPPED quando aplicáveis.
- `SafetyPosture` representa a postura de contenção, com semânticas como NORMAL, DEGRADED, SAFE_HALT e EMERGENCY_STOP quando aplicáveis.
- `OperationalReadinessAssessment` é separado de ambos e avalia capabilities específicas, incluindo criação de novo commitment versus control/reconciliation de obrigações existentes.
- Combinações como `RECONCILING + SAFE_HALT` são válidas. `RUNNING` não implica readiness para novo commitment.
- `DEGRADED` não possui permission matrix universal; capability availability depende de assessment/policy explícitos.
- `SAFE_HALT` é fail-closed para novos commitments, mas não implica auto-flatten, cancelamento automático ou outra ação econômica.
- Transições para postura mais restritiva podem ser policy-driven. Saída de postura latched exige prerequisites de recovery/reconciliation/integridade/readiness e authority explícita; mera normalização da métrica disparadora é insuficiente.

## Invariantes

- `RuntimePhase ≠ SafetyPosture ≠ OperationalReadinessAssessment`.
- Liveness não implica readiness.
- RECOVERING/RECONCILING e SAFE_HALT bloqueiam novos commitments conforme os hard invariants vigentes.
- SafetyPosture restringe; não cria authority financeira.

## Consequências

A noção histórica de `READY` passa a ser expressa por readiness capability-based, sem apagar o princípio de que recovery/reconciliation precedem qualquer possível reativação segura.

## Decisões deliberadamente adiadas

Permanecem adiados: catálogo físico de enums, thresholds de transition policy, necessidade concreta de confirmação humana para unlatch e implementação de watchdog/kill switch.

## Relação com outros ADRs

Refina ADR 0011 e complementa ADRs 0019 e 0021.
