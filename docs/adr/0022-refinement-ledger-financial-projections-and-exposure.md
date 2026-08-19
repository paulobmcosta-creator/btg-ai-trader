# ADR 0022 — Refinamento de Ledger, projeções financeiras e Exposure

- **Status:** Aceita
- **Data:** 2026-08-19
- **Refina e substitui parcialmente:** ADR 0014 — Ownership de Position, Portfolio, Ledger e exposição

## Contexto

O ADR 0014 separou Ledger, Position/Portfolio e realidade externa. O Sprint 0D refinou a unidade de reconhecimento financeiro, separou projeções e distinguiu exposição de capacity reservada.

## Decisão / refinamento

- Ledger é a autoridade interna da história **financeira economicamente reconhecida**; história operacional/auditável pertence ao `AuditJournal` conforme ADR 0018.
- O reconhecimento financeiro segue `CanonicalEconomicFact → EconomicRecognitionIdentity → LedgerTransaction → 1..N LedgerPostings`.
- `EconomicRecognitionIdentity` é independente de `run_id`: reprocessar o mesmo fato em novo Run/restart não pode duplicar efeito financeiro.
- Corrections, reversals e busts não mutam ou apagam transactions anteriores; produzem novas transactions com lineage explícita.
- A baseline não impõe contabilidade clássica universal de dupla entrada, mas cada LedgerTransaction deve satisfazer invariantes econômicos/dimensionais declarados e seus Postings formam unidade semanticamente atômica quando requerido.
- `PositionProjection` representa principalmente quantidade econômica reconhecida por Portfolio + `TradableInstrument` + corte temporal/epistemológico.
- `CashBalanceProjection`, `ValuationProjection` e `PnLProjection` são contratos separados de Position. Cash é explicitamente currency-scoped.
- `PortfolioId` é interno/provider-neutral e distinto de `ExternalAccountRef`; não existe cardinalidade universal 1:1.
- External Position/Cash observations são evidência de realidade externa e nunca sobrescrevem automaticamente internal projections nem geram Fill/LedgerAdjustment diretamente.
- Exposure distingue `CurrentPositionExposure`, `CommittedPotentialExposure`, `RiskCapacityReservation` e `WorstCaseExposure`. Capacity `RESERVED` consome orçamento de risco, mas não é market exposure.
- Exposure/valuation dependente de input UNKNOWN/STALE/INCOMPLETE preserva essa qualidade; ausência de informação nunca é convertida em zero. Informação crítica insuficiente é fail-closed para novos commitments.

## Invariantes

- `FillObservation` não alcança Ledger diretamente; somente canonical Fill/fato econômico suficientemente identificado pode ser reconhecido.
- Mesmo fato econômico produz efeito de Ledger no máximo uma vez.
- OrderIntent, ACK, broker position observation e snapshot não alteram Position por si.
- Position, Cash, Valuation, P&L e Exposure são conceitos distintos.

## Consequências

A expressão histórica “Ledger é autoridade dos fatos financeiros/operacionais” fica substituída: Ledger é financeiro; AuditJournal é operacional/auditável. O lifecycle simplificado do ADR 0014 é refinado pelos ADRs 0016, 0019 e por este ADR.

## Decisões deliberadamente adiadas

Permanecem adiados: double-entry clássico, chart of accounts, cost basis, FIFO/média, methodology de P&L/valuation, settlement rules concretas, FX, margin/buying power, netting, broker account topology e mecanismo físico de ledger.

## Relação com outros ADRs

Refina ADR 0014 e complementa ADRs 0016, 0018, 0019 e 0021.
