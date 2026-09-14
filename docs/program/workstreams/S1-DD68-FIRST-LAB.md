# Sprint 1 — DD-68 First Laboratory Decision

## Status

```text
DD_68 = PARTIALLY_RESOLVED
INSTRUMENT_FAMILY = WIN
CONCRETE_CONTRACT = RESOLVE_POINT_IN_TIME
AUTO_FALLBACK = FORBIDDEN
TIMEFRAME_OR_GRANULARITY = UNDECIDED
REAL_CAPTURE = NOT_EXECUTED
```

Human coordination approved the following policy on 2026-09-14:

> Use the WIN family as the first laboratory. Immediately before each real capture, resolve and confirm the concrete WIN contract available in BTG Solutions Data Services. Do not silently switch to another contract.

## Decision semantics

DD-68 is intentionally split into two layers:

1. **Stable laboratory subject:** the first observed instrument family is `WIN`.
2. **Point-in-time tradable contract:** the concrete future contract is not hardcoded permanently. It must be resolved from provider discovery immediately before the capture session and then explicitly fixed for that run.

This means a symbol such as `WINV26` may be the resolved contract for a specific session, but it is not a permanent canonical default.

## Fail-closed rules

Before a real subscription starts:

- provider discovery must return the exact concrete WIN contract intended for the run;
- the selected symbol must be recorded in the run/capture evidence before subscription;
- if the intended contract is absent, ambiguous, stale, or cannot be causally resolved, capture MUST NOT start;
- no automatic rollover, ranking, nearest-expiry substitution, or fallback to another WIN contract is allowed;
- changing the concrete contract requires a new explicit capture context/run decision and must not mutate prior evidence;
- fixture identifiers such as `TEST-DERIV-1` never satisfy this real-laboratory decision.

## Remaining DD-68 parameter

The original 0E-A parameter also includes concrete timeframe/granularity. Human approval in this decision resolved the instrument family and contract-resolution policy only.

Therefore:

```text
TIMEFRAME_OR_GRANULARITY = UNDECIDED
DECISION_DEADLINE = BEFORE_FIRST_REAL_CAPTURE
```

No timeframe, candle interval, or trade/tick granularity is silently promoted by adapter defaults or fixtures.

## Safety boundaries

This decision authorizes observation only. It does not authorize trading, brokerage credentials, order APIs, Strategy, Paper, Risk authorization, economic commitment, or real-money operation.
