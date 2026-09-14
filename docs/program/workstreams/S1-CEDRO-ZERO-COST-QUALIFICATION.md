# Sprint 1 — Cedro zero-cost realtime qualification workstream

## Objective

Close the real-provider qualification requirement of Sprint 1 without financial expenditure and without weakening the frozen `0F-E` realtime subscription obligations.

## Selected provider

```text
PROVIDER = Cedro Market Data
ACCESS_MODE = free trial
PUBLIC_TRIAL_WINDOW = 7 days
TARGET_MARKET = B3 / BM&F
TARGET_INSTRUMENT_FAMILY = WIN
TARGET_TRANSPORT = streaming WebSocket or Socket
TARGET_EVENT = executed trades
TARGET_TIME_PROFILE = realtime
PROJECT_COST = R$ 0
```

Public Cedro material reviewed on 2026-09-14 states that:

- Market Data can be tested free for seven days;
- WebSocket/Socket deliver B3 streaming;
- Market Data is available realtime or delayed;
- BM&F/futures and executed trades are covered;
- the Market Data API itself does not send buy/sell orders;
- Market Data authentication uses `/SignIn` with user/password and a session cookie (`JSESSIONID`).

## Timing rule

**Do not request the trial yet.**

The seven-day window starts only after the adapter, offline fake-client tests, NEG-CAP tests and runner are ready. Starting the trial earlier would consume the only zero-cost realtime window while implementation is incomplete.

## Technical phases

### Phase 1 — offline provider boundary

Implement a narrow Cedro adapter against an injected client boundary. Offline tests must prove:

- no network is required for unit tests;
- no credential value is stored by the adapter;
- only Market Data lifecycle/discovery/subscription methods are exposed;
- raw incoming payload is preserved before domain decoding;
- exact WIN candidate is confirmed before subscription;
- subscription is `trades/realtime` only for the first lab;
- ambiguous discovery fails closed;
- disconnect/restart is explicit and auditable;
- no order/account/financial method is reachable.

### Phase 2 — protocol binding

Bind the narrow adapter to the exact Cedro streaming protocol after the trial documentation/credentials are issued.

The binding must not import or call Cedro Trading surfaces. Public documentation already establishes the prohibited namespace examples; trial-specific docs must be inspected before first network execution.

### Phase 3 — protected laboratory

Create a dedicated GitHub Environment only after offline CI is green. Expected secret classes:

```text
CEDRO_LAB_MARKETDATA_USERNAME
CEDRO_LAB_MARKETDATA_PASSWORD
CEDRO_LAB_EVIDENCE_PASSPHRASE
```

Names may be adjusted once the final protocol binding is known, but broker account/trading secrets are forbidden.

### Phase 4 — real qualification

Execute exactly one bounded causal session:

```text
market-data authentication
-> provider capability/discovery evidence
-> exact WIN candidate confirmation
-> realtime trades subscription
-> at least one exact-symbol trade
-> unsubscribe/close
-> immutable technical evidence
```

If the free trial only exposes delayed/EOD data, lacks BM&F trades or cannot confirm the exact symbol, the run fails and DD-60 reopens. No silent downgrade is allowed.

## Zero-cost post-qualification sources

After realtime qualification, the project may use B3 D-1/historical data and suitable public/no-token WIN/WDO endpoints for research/replay where fidelity is explicitly declared.

Those sources do not replace the realtime qualification evidence.

## Negative capability invariant

```text
CEDRO_TRADING_API = FORBIDDEN
NEGOTIATION_ENDPOINTS = FORBIDDEN
BROKER_LOGIN = FORBIDDEN
BROKER_ACCOUNT = FORBIDDEN
ORDER_SEND_EDIT_CANCEL = FORBIDDEN
FINANCIAL_ACCOUNT_DATA = FORBIDDEN
GUARANTEE_ALLOCATION = FORBIDDEN
PAPER_PATH = ABSENT
LIVE_PATH = ABSENT
REAL_MONEY_AUTHORITY = ABSENT
```
