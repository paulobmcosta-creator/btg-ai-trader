# Program Execution — BTG AI Trader

## Current remote checkpoint

```text
AUTHORITATIVE_STATE = GITHUB_REMOTE
REPOSITORY = paulobmcosta-creator/btg-ai-trader
SPRINT_BRANCH = sprint/1-market-observer
INTEGRATED_IMPLEMENTATION_BASELINE = b763ad20b857c016fecd4ca004c6d0e191df1435
ACTIVE_PROVIDER_TRANSITION = s1/23-zero-cost-cedro-provider
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
SPRINT_1_LIFECYCLE = OPEN
S1_A_AUTHORIZED = YES
SPRINT1_ACCEPTANCE = NOT_GRANTED
ZERO_ADDITIONAL_COST = REQUIRED
DD_60 = REOPENED_AND_REDECIDED_FOR_ZERO_COST
TARGET_REAL_PROVIDER = CEDRO_MARKET_DATA_FREE_TRIAL
BTG_PROVIDER = NON_CANONICAL_REFERENCE_IMPLEMENTATION
REAL_PROVIDER_SESSION = NOT_EXECUTED
SECURITY_DIFF_SCAN = NOT_EXECUTED
REAL_MONEY = NO
LIVE_TRADING = NO
TRADING_CREDENTIALS = NO
TRADING_CAPABILITY = ABSENT
```

Historical execution detail remains in Git history and prior PRs. This living file records only the state required to resume safely.

## Preserved authorities

The frozen Foundation artifacts remain unchanged: `0F-B`, `0F-E`, `0F-F`, and quantitative `TRACEABILITY.md`.

The zero-cost constraint does **not** weaken 0F-E. In particular:

- AC-05 still requires read-only market-data subscription/streaming;
- AC-07 still requires realtime tick/candle observation capability;
- delayed/EOD/historical data cannot be relabeled as realtime qualification evidence.

## Provider transition

ADR-0024 supersedes ADR-0023 **only for the real Sprint 1 provider qualification**.

```text
OLD_QUALIFICATION_PROVIDER = BTG Solutions Data Services
OLD_STATUS = NON_CANONICAL_REFERENCE_IMPLEMENTATION
NEW_QUALIFICATION_PROVIDER = Cedro Market Data
ACCESS = FREE_TRIAL
PUBLICLY_ADVERTISED_TRIAL = 7 days
MARKET = B3 / BM&F
TARGET_TRANSPORT = streaming WebSocket or Socket
TARGET_DATA = realtime trades
PROJECT_COST = R$ 0
```

The Cedro public documentation states that its Market Data product offers B3/BM&F streaming, realtime or delayed data, and executed trades; it also states that the Market Data API itself cannot send buy/sell orders. Authentication for Market Data uses a Cedro user/password session and `JSESSIONID` cookie. Trading APIs are separate and remain forbidden.

Official/provider sources recorded by ADR-0024 include Cedro Market Data/WebSocket/reference documentation, B3 Market Data FAQ and brapi futures documentation.

## Why B3 historical / brapi are not the S1 realtime provider

The B3 permits D-1/end-of-day/historical data to be distributed without Market Data fees, and brapi exposes WIN/WDO test access without token. These are useful for zero-cost research after qualification, but they do not satisfy the frozen AC-05/AC-07 realtime streaming obligation.

They may be used later for replay/research only with explicit fidelity declarations.

## BTG artifacts after supersession

PR #34/#35 and their BTG adapter/harness history remain auditable and are not rewritten. The BTG-specific real-lab workflow is retired from the active tree during this transition so that no stale BTG credential path remains operationally triggerable as the canonical lab.

No BTG API key should be purchased or provisioned for Sprint 1 closure.

## Cedro credential boundary

DD-43 remains triggered, now for Cedro Market Data credentials.

Allowed authentication surface:

```text
Cedro Market Data /SignIn
market-data username/password supplied only from external secret storage
JSESSIONID held only in process/session memory
```

Forbidden surface:

```text
/services/negotiation/*
API Trading
brokerServiceLogin
user-identifier for broker/trading
broker account number
order send/edit/cancel
financial/account/custody/guarantee APIs
```

No Cedro credential, session cookie or password may be committed, pasted into chat, persisted in EvidenceArchive/AuditJournal or emitted to logs.

## DD-68 laboratory profile

DD-68 remains unchanged:

```text
INSTRUMENT_FAMILY = WIN
CONCRETE_CONTRACT = EXPLICIT_CANDIDATE_PLUS_PROVIDER_CONFIRMATION_POINT_IN_TIME
STREAM_TYPE = realtime
DATA_TYPE = trades
AUTO_FALLBACK = FORBIDDEN
AUTO_ROLLOVER = FORBIDDEN
INITIAL_CANDLES = NO
```

`WINV26` remains the current September/2026 candidate, but it may be subscribed only after the selected Cedro session confirms its availability.

## Evidence state

```text
RQM_TOTAL = 41
RQM_SATISFIED_OR_FIXTURE_SCOPE = 39
RQM_BLOCKED_SECURITY_SCAN = 2  # RQM-018, RQM-036
NEG_CAP_01_TO_10 = SATISFIED_ON_LAST_INTEGRATED_TREE
READ_ONLY_BY_CONSTRUCTION = SATISFIED_ON_LAST_INTEGRATED_TREE
STRUCTURAL_ESCALATION = SATISFIED_ON_LAST_INTEGRATED_TREE
CEDRO_ADAPTER = NOT_IMPLEMENTED
CEDRO_REAL_SESSION = NOT_EXECUTED
SECURITY_DIFF_SCAN = NOT_EXECUTED
```

The 39/2 classification is evidence bookkeeping, not formal Sprint 1 PASS. Provider-specific claims must be revalidated for Cedro before acceptance.

## Remaining Sprint 1 sequence

```text
1. Integrate ADR-0024/provider-transition documentation after CI/review.
2. Implement a narrow Cedro Market Data adapter with fake-client tests first; no trial credential yet.
3. Prove NEG-CAP against Cedro Trading/negotiation/account surfaces.
4. Only after adapter CI is green, request the Cedro 7-day free Market Data trial so the time window is not wasted.
5. Store Cedro market-data credentials in a dedicated protected GitHub Environment outside repository/chat.
6. Execute one controlled WIN realtime-trades session; fail closed if realtime BM&F trades or exact-symbol confirmation are unavailable.
7. Reconcile real-provider evidence into RQM/XC.
8. Re-run exact-final-tree CI and NEG-CAP.
9. Execute the official Security Diff Scan on the exact final Sprint 1 tree, or only use a separately explicit governance treatment if authorized.
10. Adjudicate all 11 Sprint 1 exit criteria conjunctively.
11. Promote to Sprint 2 only after formal Sprint 1 PASS.
```

No step above authorizes financial execution, broker/trading credentials, order APIs, Paper execution, Risk authorization, ledger mutation or real money.
