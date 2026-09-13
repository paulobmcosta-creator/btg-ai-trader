# S1 — Monotonic transit-latency evidence

- Status: implementation detail selected for closing RQM-023 / AC-09 in the deterministic S1 boundary.
- Scope: passive measurement only; no provider selection, network clock, wall-clock inference or execution authority.
- Authority: current Sprint 1 mandate and 0F-E RQM-023 / AC-09.

## Decision

Transit/ingestion latency evidence is represented from two explicit readings of the **same caller-declared monotonic clock scope**:

1. `ingress_ns`: monotonic reading captured by the adapter/owner at ingress;
2. `available_ns`: later reading at the internal observation boundary;
3. `latency_ns = available_ns - ingress_ns`.

The library never converts event timestamps or wall-clock UTC into monotonic time. It never reads a clock implicitly. Backwards readings fail closed. Clock scope is explicit and validated. The evidence is an immutable typed value and has no operational side effect.

For the S1 fixture boundary, integration tests pair this measurement with an actual `FixtureObserver` advance using the same explicit monotonic sample. A future real provider must supply its own ingress reading from the same monotonic scope; this decision does not select DD-60 or DD-54 concurrency.

## Limits

- This is transit/ingestion latency evidence, not exchange latency, broker latency, order latency or network one-way latency.
- It does not infer source-side timing from `event_time`.
- It does not authorize a real provider, credential, thread model, order path or economic action.
- Any distributed/multi-host clock comparison requires a successor decision.
