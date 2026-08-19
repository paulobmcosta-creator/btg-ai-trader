# ADR 0019 — Refinamento de recovery, reconciliation boundaries e readiness

- **Status:** Aceita
- **Data:** 2026-08-19
- **Refina e substitui parcialmente:** ADR 0010 — Recovery, reconciliação e resultados desconhecidos

## Contexto

O ADR 0010 fixou recovery/reconciliation fail-closed e proibiu retry cego para outcome externo desconhecido. O Sprint 0D separou término procedural, qualidade da reconstrução, consistency cuts e readiness operacional.

## Decisão / refinamento

- `RecoverySession` representa o processo; `RecoveryAssessment` registra resultado por scope. Session encerrada não implica recovery bem-sucedido.
- Snapshot + journal só sustentam reconstrução quando continuity é demonstrável para os scopes necessários; gap/corruption/ambiguity/unknown não são convertidos em reconstrução otimista.
- `ReconciliationSession` pode conter múltiplos `ReconciliationRound`s imutáveis. Cada round possui `ReconciliationObservationBoundary` próprio com scopes, intervalo observacional, sequence/watermark quando disponível, freshness/completeness e limitações de consistência.
- `CONSISTENT` só é afirmado relativamente a boundary explícito e suficiente.
- Findings distinguem match, mismatch, unresolved, missing evidence, ambiguous matching e contradictory evidence. `ReconciliationMismatch` representa apenas divergência demonstrada.
- A cadeia corretiva é `observation → identity matching/linkage → consistency assessment → ReconciliationDecision`. Correção financeira posterior exige `FinancialCorrectionAuthority` antes de `CanonicalAdjustmentEconomicFact` e reconhecimento no Ledger.
- `OperationalControlAuthority` é distinta da authority financeira e da `RiskAuthorization`; permite apenas query/cancel/recovery/control de obrigações existentes sem criar ou ampliar commitment.
- Recovery/reconciliation suficientes apenas removem seus blockers. Disponibilidade de `CREATE_NEW_ECONOMIC_COMMITMENT` continua sendo decidida por `OperationalReadinessAssessment`.
- Restart não encerra obrigação econômica existente. Um novo Run deve reconstruir/controlar commitments herdados sem fabricar nova lineage econômica nem liberar capacidade automaticamente.

## Invariantes

- Outcome externo material `UNKNOWN` permanece committed até reconciliation suficiente.
- Missing evidence não é MATCH; unresolved não é success.
- External Position/Cash observation não sobrescreve internal state nem gera adjustment automático.
- Externally discovered obligation sem lineage interna não recebe TradeIntent/RiskAuthorization/ExecutionOrder retroativos fictícios.

## Consequências

A formulação histórica “resolver explicitamente e só então READY” fica refinada: recovery/reconciliation suficientes são pré-condições, mas não produzem readiness automaticamente.

## Decisões deliberadamente adiadas

Permanecem adiados: algoritmo de matching, thresholds de freshness, número/timing de rounds, provider capabilities concretas, natureza humana/automática de determinadas authorities e mecanismos físicos de recovery.

## Relação com outros ADRs

Refina ADR 0010 e complementa ADRs 0018, 0020, 0021 e 0022.
