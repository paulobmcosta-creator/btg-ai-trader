# S8-STRATEGY-REMEDIATION — Operational Strategy / TradeIntent

```text
SPRINT = 8
WORK_MODE = PREAUTH_BLOCKER_REMEDIATION_ONLY
ISSUE = #95
UPSTREAM_ENTRY_GATE_PR = #94
UPSTREAM_ENTRY_GATE_HEAD = 7fce78b02d03cc8140bc021217a0230776cc53ff
CANONICAL_BRANCH = sprint/8-paper-trader
UPSTREAM_WORK_BRANCH = s8/00-entry-gate
WORK_BRANCH = s8/01-strategy-remediation

S8-B01_REMEDIATION = AUTHORIZED
S8-B01_REMEDIATION_AUTHORIZATION_DATE = 2026-10-04
S8-B01_REMEDIATION_CANDIDATE = IMPLEMENTED_PENDING_EXACT_HEAD_CI_AND_INDEPENDENT_REVIEW
S8-B02 = OPEN

S8_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
PAPER_CONFIRMATORY_RUN = NOT_AUTHORIZED
LIVE_TRADING = NO
REAL_MONEY = NO
BROKER_ORDER_SIDE_EFFECT = FORBIDDEN
CANONICAL_FINANCIAL_LEDGER_MUTATION = FORBIDDEN
MERGE = FORBIDDEN_WITHOUT_HUMAN_AUTHORIZATION
```

## 1. Purpose

Remediate only S8-B01 by materializing the upstream operational Strategy path required by ADR 0016 and Protocol 0E-F. This work is deliberately separate from Paper Trader functionality and from S8-B02 candidate promotion.

The implemented path is:

```text
DecisionOpportunity / admitted upstream evidence
        ↓
CandidateStrategy
        ↓
deterministic ordered StrategyRule policy
        ↓
StrategyDecision
   ├── NO_TRADE
   └── PROPOSE_TRADE
            ↓
       TradeIntent
            ↓
   one-way risk_adapter
            ↓
       RiskProposal
            ↓
 existing S7 Risk Engine
```

## 2. Runtime contracts

### CandidateStrategy

`CandidateStrategy` is an immutable, version-specific policy identity. Its digest binds:

- strategy name and version;
- code revision;
- one concrete `TradableInstrumentId`;
- portfolio identity;
- upstream input-spec digest;
- maximum admitted evidence age;
- the complete ordered rule set and every economic objective.

The infrastructure selects no favorable thresholds and creates no canonical candidate by itself. Thresholds, priorities, sizing and directions are candidate-owned configuration and therefore become part of candidate identity.

### DecisionOpportunity

`DecisionOpportunity` is the causal Strategy input boundary. It binds:

- concrete instrument and portfolio;
- `event_time <= knowledge_time <= decision_time`;
- exact upstream input-spec digest;
- immutable finite Decimal signal mapping;
- explicit evidence quality;
- source provenance digest.

It is not a Signal generator and does not synthesize market evidence.

### StrategyDecision

Every evaluated opportunity produces an explicit engine-issued `StrategyDecision`:

- `NO_TRADE`; or
- `PROPOSE_TRADE`.

`NO_TRADE` remains a first-class auditable result. Instrument, portfolio, input-spec, evidence-quality, staleness and required-signal failures fail closed to `NO_TRADE`.

### EconomicObjective and TradeIntent

A matched rule carries one immutable `EconomicObjective` with:

- one of the four S7-compatible economic directions;
- positive requested quantity and explicit unit;
- positive requested exposure and explicit unit.

Only an engine-issued `PROPOSE_TRADE` decision may produce an engine-issued `TradeIntent`. The intent binds the candidate digest, opportunity digest, decision digest, concrete instrument, portfolio, economic objective, creation time and source digest.

### Risk adapter

`to_risk_proposal()` is the only Strategy-to-Risk adapter in this workstream. It:

- accepts only an engine-issued `TradeIntent`;
- maps the four economic directions explicitly to the canonical S7 enum;
- preserves quantity, exposure, units, instrument, portfolio and decision time;
- sets `RiskProposal.source_digest = TradeIntent.intent_digest`;
- creates no `RiskDecision`, `RiskAuthorization` or execution authority.

## 3. Determinism and fail-closed semantics

The runtime uses no randomness, wall-clock reads, network, broker API, filesystem I/O or dynamic code loading. Identical immutable candidate/opportunity inputs produce identical decision/intent/result digests.

Rules are canonicalized by unique integer priority. The first matching rule is deterministic. Missing required signals do not fall through to a potentially favorable lower-information path; they produce `NO_TRADE`.

Evidence at exactly the configured maximum age remains admissible; evidence older than the predeclared maximum produces `NO_TRADE`.

## 4. Explicit non-goals

This workstream does not implement or authorize:

- a specific empirically favorable Strategy candidate;
- `PAPER_ELIGIBLE` adjudication or candidate freeze;
- `AuthorizationAllocation`;
- `OrderIntent`, `OrderPlan`, `ExecutionOrder` or any execution command;
- Paper fills, paper account state, P&L or Paper evidence;
- broker/account/order connectivity;
- canonical `FinancialLedger` mutation;
- Live Trading or real money.

Accordingly, successful S8-B01 remediation leaves S8-B02 open and leaves functional Paper prohibited.

## 5. Acceptance evidence required

The remediation candidate must pass, at one exact PR head:

- full repository regression;
- 100% statement and branch coverage for `btg_ai_trader.strategy`;
- Ruff;
- strict mypy;
- compileall;
- dependency check;
- Foundation integrity;
- S1–S7 capability-boundary checks;
- dedicated S8 Strategy boundary scanner;
- exact authorized-file-surface check;
- pinned upstream engineering;
- independent Codex review with no blocking findings.

## 6. Authorized file surface

Only the following may change relative to `7fce78b02d03cc8140bc021217a0230776cc53ff`:

- `src/btg_ai_trader/strategy/**`;
- `tests/strategy/**`;
- `scripts/check_s8_strategy_boundary.py`;
- the minimal S1 verifier compatibility update that adds `strategy` to the already-existing post-S1 root exclusions;
- the NEG-CAP-10 test correction so it verifies modules loaded *by S1 execution*, rather than modules imported earlier by unrelated future-sprint tests;
- `.github/workflows/s8-strategy-remediation-ci.yml`;
- S8 governance/workstream documentation and living checkpoint documents.

No dependency, Foundation, protocol or historical ADR change is authorized.

## 7. Current stop condition

```text
S8-B01_REMEDIATION_CANDIDATE = IMPLEMENTED_PENDING_EXACT_HEAD_CI_AND_INDEPENDENT_REVIEW
S8-B01_CANONICAL_CLOSURE = NO
S8-B02 = OPEN
PROMOTION_TO_S8_FUNCTIONAL_IMPLEMENTATION = NO
S8_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
PAPER_CONFIRMATORY_RUN = NOT_AUTHORIZED
MERGE = FORBIDDEN_WITHOUT_HUMAN_AUTHORIZATION
```


## 8. Historical S1 compatibility clarification

The original S1 boundary verifier already excludes post-S1 package roots (Replay through Risk) before comparing the frozen S1 source inventory. Adding the explicitly authorized `src/btg_ai_trader/strategy` root to that same exclusion list preserves, rather than relaxes, the S1 inventory pins.

Likewise, NEG-CAP-10 is clarified to compare `sys.modules` immediately before and after S1 execution. Its invariant is that executing S1 must not load future financial modules; unrelated test-collection/import order must not cause a false positive merely because a later-sprint module legitimately exists.
