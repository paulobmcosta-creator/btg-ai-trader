# Sprint 1 — DD-68 First Laboratory Decision

## Status

```text
DD_68 = RESOLVED
INSTRUMENT_FAMILY = WIN
CONCRETE_CONTRACT = RESOLVE_POINT_IN_TIME
AUTO_FALLBACK = FORBIDDEN
STREAM_TYPE = REALTIME
DATA_GRANULARITY = TRADES
INITIAL_CANDLES = NO
REAL_CAPTURE = NOT_EXECUTED
```

Human coordination approved the first-laboratory policy in two steps on 2026-09-14:

1. use the `WIN` family as the first laboratory, resolving and confirming the concrete contract point-in-time in BTG Solutions Data Services before each real capture, with no silent contract substitution; and
2. use the provider's real-time `trades` stream as the initial observation granularity, without candle subscription/aggregation as the first laboratory input.

## Decision semantics

DD-68 is now fully resolved for Sprint 1:

1. **Stable laboratory subject:** the first observed instrument family is `WIN`.
2. **Point-in-time tradable contract:** the concrete future contract is not hardcoded permanently. It must be resolved from provider discovery immediately before the capture session and then explicitly fixed for that run.
3. **Observation granularity:** the first real capture consumes the `realtime` `trades` stream. No candle interval is part of the initial laboratory configuration.

A symbol such as `WINV26` may be the resolved contract for a specific session, but it is not a permanent canonical default.

`trades/realtime` is the approved first-laboratory observation mode. It does not imply that candles are forbidden forever; adding a candle stream later is a separate explicit configuration/change and must not silently alter the first-laboratory evidence model.

## Fail-closed rules

Before a real subscription starts:

- provider discovery must return the exact concrete WIN contract intended for the run;
- the selected symbol must be recorded in the run/capture evidence before subscription;
- if the intended contract is absent, ambiguous, stale, or cannot be causally resolved, capture MUST NOT start;
- no automatic rollover, ranking, nearest-expiry substitution, or fallback to another WIN contract is allowed;
- changing the concrete contract requires a new explicit capture context/run decision and must not mutate prior evidence;
- the first laboratory must use `stream_type=realtime` and `data_type=trades`;
- candle streams (`candles-*`) are outside the initial real-capture profile and cannot replace the trade stream silently;
- fixture identifiers such as `TEST-DERIV-1` never satisfy this real-laboratory decision.

## First-laboratory capture profile

```text
PROVIDER = BTG Solutions Data Services
EXCHANGE = B3
INSTRUMENT_FAMILY = WIN
CONCRETE_SYMBOL = RESOLVE_AND_CONFIRM_POINT_IN_TIME
STREAM_TYPE = realtime
DATA_TYPE = trades
DATA_SUBTYPE = derivatives
AUTO_RECONNECT = NO
AUTO_ROLLOVER = NO
AUTO_FALLBACK = NO
ECONOMIC_AUTHORITY = NONE
```

The concrete symbol selected by discovery must be fixed in the run/capture context before subscription and remain unchanged for that capture session.

## Safety boundaries

This decision authorizes observation only. It does not authorize trading, brokerage credentials, order APIs, Strategy, Paper, Risk authorization, economic commitment, or real-money operation.
