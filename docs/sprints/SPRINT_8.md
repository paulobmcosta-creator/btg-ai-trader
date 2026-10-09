# Sprint 8 — Paper Trader

```text
SPRINT_8_STATUS = ENTRY_GATE_CANDIDATE_CHANGES_REQUIRED
SPRINT_8_LIFECYCLE = ENTRY_GATE
SPRINT_8_ENTRY_GATE_AUTHORIZATION_DATE = 2026-10-02
SPRINT_8_CANONICAL_BRANCH = sprint/8-paper-trader
SPRINT_8_ENTRY_GATE_WORK_BRANCH = s8/00-entry-gate
SPRINT_8_ENTRY_GATE_ISSUE = #93
SPRINT_8_REQUIRED_PREDECESSOR_BRANCH_HEAD = 1226aea13bc8a99303b8c008883fd36068247829
SPRINT_7_FUNCTIONAL_CANONICAL_HEAD = e379e9b34a8b607e86165bd3336d23fcd9406259

S8_ENTRY_GATE_CANDIDATE = CHANGES_REQUIRED
OPEN_S8_ENTRY_GATE_BLOCKERS = 2
S8-B01 = OPEN_CANONICALLY__REMEDIATION_AUTHORIZED
S8-B01_REMEDIATION_ISSUE = #95
S8-B01_REMEDIATION_WORK_BRANCH = s8/01-strategy-remediation
S8-B01_REMEDIATION_CANDIDATE = IMPLEMENTED_PENDING_EXACT_HEAD_CI_AND_INDEPENDENT_REVIEW
S8-B02 = OPEN

S8_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
PAPER_CONFIRMATORY_RUN = NOT_AUTHORIZED
LIVE_TRADING = NO
REAL_MONEY = NO
```

## Purpose

Sprint 8 is the prospective non-funded Paper Trader stage defined by Protocol 0E-G.

A future authorized implementation must exercise real internal system decisions on contemporaneous market data while remaining structurally incapable of transmitting a real order or creating real financial exposure.

## Current gate finding

The Entry Gate currently blocks functional implementation for two root reasons:

- **S8-B01:** there is no operational Signal/Strategy → `StrategyDecision` → `TradeIntent` runtime path in the canonical predecessor;
- **S8-B02:** there is no exact candidate canonically adjudicated `PAPER_ELIGIBLE` and frozen for confirmatory Paper.

Paper infrastructure must not hide either gap by inventing a strategy or selecting a favorable substitute.

## Hard boundary

```text
REAL_BROKER_ORDER = FORBIDDEN
REAL_ACCOUNT_MUTATION = FORBIDDEN
REAL_MONEY = FORBIDDEN
LIVE_TRADING = FORBIDDEN
CANONICAL_FINANCIAL_LEDGER_MUTATION = FORBIDDEN

RISK_BYPASS = FORBIDDEN
PAPER_LOCAL_STRATEGY_SUBSTITUTE = FORBIDDEN
AUTO_PROMOTION_TO_LIVE = FORBIDDEN
```

The Entry Gate itself changes no functional source code.


## S8-B01 remediation phase — 2026-10-04

A separate human authorization opened Issue #95 and `s8/01-strategy-remediation` from exact PR #94 head `7fce78b02d03cc8140bc021217a0230776cc53ff`.

This phase is pre-Paper blocker remediation only. It may materialize `CandidateStrategy`, `DecisionOpportunity`, `StrategyDecision`, `EconomicObjective`, `TradeIntent` and the one-way adapter into the existing S7 `RiskProposal`.

It cannot implement `AuthorizationAllocation`, order planning/execution, Paper accounting/fills, broker connectivity, canonical FinancialLedger mutation, Live or real money. S8-B02 remains open and independently blocking.

```text
S8-B01_REMEDIATION_CANDIDATE = IMPLEMENTED_PENDING_EXACT_HEAD_CI_AND_INDEPENDENT_REVIEW
S8-B01_CANONICAL_CLOSURE = NO
S8-B02 = OPEN
PROMOTION_TO_S8_FUNCTIONAL_IMPLEMENTATION = NO
PAPER_CONFIRMATORY_RUN = NOT_AUTHORIZED
```
