# Sprint 1 — BTG first-lab runner — historical/superseded

> **Current status (2026-09-14):** this workstream is preserved as historical evidence only. ADR-0024 superseded BTG Solutions Data Services for the real Sprint 1 qualification because the project owner requires zero additional financial cost. The active qualification target is Cedro Market Data free trial. The BTG-specific workflow was removed from the active tree so this document must not be used as an execution runbook.

## Historical purpose

This increment prepared a controlled GitHub-hosted execution path for the integrated read-only BTG Data Services first-lab harness. It did not itself execute a real session and did not add any trading/account/order capability.

The historical runner used GitHub Environment `btg-readonly-lab`, external laboratory secrets, exact-SHA execution, encrypted raw evidence and a sanitized no-price/no-raw-payload summary.

## Historical security properties

```text
PROVIDER = BTG Solutions Data Services
STATUS = NON_CANONICAL_REFERENCE_IMPLEMENTATION
REAL_SESSION = NEVER_EXECUTED
TRADING_CAPABILITY = ABSENT
REAL_MONEY_AUTHORITY = ABSENT
```

## Supersession

The active zero-cost provider decision and execution plan are now defined by:

- `docs/adr/0024-zero-cost-sprint1-qualification-provider-cedro-market-data.md`;
- `docs/program/workstreams/S1-CEDRO-ZERO-COST-QUALIFICATION.md`.

Historical PRs #34, #35 and #40 remain audit evidence for the read-only boundary, discovery hardening and secure-runner design. They are not Cedro qualification evidence and must not be relabeled as such.
