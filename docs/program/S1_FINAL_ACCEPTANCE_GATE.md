# Sprint 1 — Final Acceptance Gate Checkpoint

## Gate purpose

This living checkpoint records whether the current Sprint 1 baseline may be declared a formal PASS under immutable 0F-E. It does not rewrite 0F-B, 0F-E or 0F-F.

## Current state

```text
FOUNDATION = FORMALLY_CLOSED
SPRINT_1 = OPEN
INTEGRATED_IMPLEMENTATION_BASELINE = b763ad20b857c016fecd4ca004c6d0e191df1435
ACTIVE_PROVIDER_TRANSITION = s1/23-zero-cost-cedro-provider
ZERO_ADDITIONAL_COST = REQUIRED
DD_60 = REDECIDED_CEDRO_MARKET_DATA_FREE_TRIAL
ADR_0024 = ACCEPTED_ON_TRANSITION_BRANCH
BTG_PROVIDER = NON_CANONICAL_REFERENCE_IMPLEMENTATION
CEDRO_PROVIDER_ADAPTER = NOT_IMPLEMENTED
READ_ONLY_BY_CONSTRUCTION_LAST_INTEGRATED_TREE = SATISFIED
STRUCTURAL_ESCALATION_LAST_INTEGRATED_TREE = SATISFIED
TRADING_CAPABILITY = ABSENT
REAL_MONEY_PATH = ABSENT
REAL_PROVIDER_SESSION = NOT_EXECUTED
SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_ACCEPTANCE = NO
```

## Evidence adjudication

| Gate area | Result | Basis |
|---|---|---|
| Foundation integrity | PASS | Frozen Foundation artifacts remain unchanged |
| Functional Observer core | PASS_CURRENT_SCOPE | Passive Observer core integrated |
| 41 RQMs | CONDITIONAL | 39 direct/fixture; RQM-018 and RQM-036 await official Security Diff Scan |
| NEG-CAP-01..10 | PASS_LAST_INTEGRATED_TREE | Must be rerun after Cedro implementation |
| Instrument discovery/resolution | PASS_FIXTURE_SCOPE | Point-in-time semantics integrated; Cedro real confirmation pending |
| DD-60 provider decision | PASS_DECISION_TRANSITION | Cedro Market Data free trial selected by ADR-0024 for zero-cost real qualification |
| DD-43 credential policy | PASS_POLICY | Cedro Market Data credentials only; no Trading/broker credential |
| BTG provider artifacts | HISTORICAL_REFERENCE | Prior adapter/harness remain auditable but are not canonical qualification evidence |
| Cedro provider adapter | FAIL_OPEN | Not implemented yet |
| Cedro real subscription | FAIL_OPEN | No Cedro trial/session executed |
| DD-68 laboratory profile | PASS_DECISION | WIN; exact provider confirmation; realtime trades; no fallback/rollover/candles |
| Real laboratory evidence | FAIL_OPEN | No real Cedro authentication/discovery/subscription/trade capture yet |
| Official Security Diff Scan | FAIL_OPEN | Not executed; other checks are not relabeled as official scan |

## Why the contract is not weakened

B3 public D-1/historical data and brapi no-token WIN/WDO futures endpoints are zero-cost, but are not realtime subscription feeds. They therefore remain research/replay sources and cannot satisfy AC-05/AC-07.

Cedro was selected because its public documentation advertises a seven-day free Market Data trial with B3/BM&F streaming, realtime/delay data and executed trades, while stating that its Market Data API cannot send orders.

## Laboratory policy after ADR-0024

```text
PROVIDER = Cedro Market Data free trial
PROJECT_COST = R$ 0
INSTRUMENT_FAMILY = WIN
CONCRETE_CONTRACT = EXPLICIT_CANDIDATE_PLUS_PROVIDER_CONFIRMATION_POINT_IN_TIME
STREAM_TYPE = realtime
DATA_TYPE = trades
AUTO_FALLBACK = FORBIDDEN
AUTO_ROLLOVER = FORBIDDEN
INITIAL_CANDLES = NO
TRADING_API = FORBIDDEN
BROKER_ACCOUNT = FORBIDDEN
```

The trial must not be started until the adapter and offline CI are ready, because the publicly advertised trial window is seven days.

## Cedro security boundary

Only Cedro **Market Data** authentication/observation is allowed. `/SignIn` market-data credentials and its transient `JSESSIONID` may be used solely inside the runtime session.

The following are structural gate failures if introduced:

- API Trading;
- `/services/negotiation/*`;
- `brokerServiceLogin`;
- trading `user-identifier`;
- broker/financial account identifiers;
- order send/edit/cancel;
- custody, financial, guarantee or account-control APIs.

## Current adjudication

```text
SPRINT1_INTERNAL_OBSERVER_CORE = COMPLETE_CURRENT_SCOPE
SPRINT1_PROVIDER_DECISION = REDECIDED_ZERO_COST
SPRINT1_DD68_DECISION = COMPLETE
SPRINT1_CEDRO_IMPLEMENTATION = OPEN
SPRINT1_REAL_CAPTURE_GATE = OPEN
SPRINT1_SECURITY_GATE = OPEN
SPRINT1_ACCEPTANCE = NO
PROMOTION_TO_SPRINT_2 = NO
```

## Mandatory remaining sequence

1. Integrate ADR-0024 and provider-transition cleanup after exact-head CI/review.
2. Implement the narrow Cedro Market Data adapter against an injected fake client first; no trial credential yet.
3. Add explicit NEG-CAP tests excluding Cedro Trading/negotiation/account surfaces.
4. Obtain/verify the exact streaming protocol/documentation needed for realtime BM&F trades.
5. Only when adapter/test/runner are green, request the Cedro seven-day free trial.
6. Provision Cedro Market Data credentials through a dedicated protected GitHub Environment outside repository/chat.
7. Execute one controlled `WIN` realtime-trades session; require provider confirmation of the exact candidate before subscription.
8. Fail closed if the free trial supplies only delay/EOD, lacks BM&F trades, or cannot causally confirm the exact symbol.
9. Reconcile real-provider evidence into RQM/XC without upgrading fixture-only claims beyond evidence.
10. Re-run full CI, boundary and NEG-CAP on the exact final Sprint 1 tree.
11. Execute the official Security Diff Scan on the exact final Sprint 1 tree, or only use a separately explicit governance treatment if authorized.
12. Adjudicate all 11 exit criteria conjunctively.
13. Promote to Sprint 2 only after formal Sprint 1 PASS.

## Explicit prohibitions remain in force

No open, implemented or passed gate authorizes Strategy, ML production wiring, Paper execution, Risk authorization, broker order APIs, trading credentials, financial account access, ledger mutation, economic commitment or real-money operation.
