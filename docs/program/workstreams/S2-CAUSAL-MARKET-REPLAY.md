# Sprint 2 — Causal market replay precursor (SPECULATIVE)

## Status and promotion boundary

```text
CLASSIFICATION = SPECULATIVE_S2
WORKSTREAM = S2-R2
BRANCH = s2/01-causal-market-replay
BASE = integration/s2-research
PROMOTION_TO_SPRINT1 = FORBIDDEN
FINANCIAL_EXECUTION = ABSENT
ECONOMIC_BACKTEST = ABSENT
STRATEGY_OR_ML = ABSENT
```

This workstream is permitted only as isolated future-sprint development. It is not evidence that Sprint 1 is complete and must never be merged into `sprint/1-market-observer`.

Normative authority is the frozen 0F-E Replay Boundary: Sprint 2 may implement formal historical **market-data replay with speed control and causal ordering**; Sprint 3 owns economic backtesting with costs, slippage, latency and queue simulation.

PR #9 (`s3/01-causal-replay-kernel`, historically named) remains an earlier generic fixture-clock precursor. This workstream does not promote that branch or reuse its historical classification. It narrows the next increment to the integrated Observer `EventEnvelope` contract now present in the Sprint 1 development baseline.

## Scope of this increment

Implement a pure, deterministic replay schedule over immutable `EventEnvelope` values.

The increment MAY:

- consume immutable Observer envelopes supplied by the caller;
- require an explicit replay/capture scope;
- require known UTC `knowledge_time` for every replayed envelope;
- preserve caller-supplied causal order rather than sort by `event_time`;
- reject order that contradicts known knowledge availability;
- expose inclusive knowledge cutoffs;
- expose deterministic virtual pacing as an exact rational transformation of knowledge-time deltas;
- return immutable replay emissions for downstream research consumers.

The increment MUST NOT:

- read wall clock or sleep;
- connect to a provider, broker or account;
- load credentials;
- submit, modify or cancel orders;
- create StrategyDecision, TradeIntent, RiskAuthorization, OrderIntent, fills or ledger records;
- model spread, fees, slippage, queue fills, execution latency or P&L;
- invoke predictive models or feature pipelines;
- infer historical truth for unknown timestamps;
- reorder events by `event_time` or invent a global order across unrelated capture scopes;
- mutate Observer envelopes.

## Experimental decisions before implementation

These choices are limited to this speculative workstream and do not supersede historical ADRs or authorize Sprint 2 promotion.

### S2R2-D01 — replay lane boundary

One schedule is one explicit `(provider, capture_scope)` lane. Multiple symbols may exist inside the same lane, but envelopes from another provider/scope are rejected. This avoids inventing a global order across independently captured streams.

### S2R2-D02 — causal availability key

Scheduling uses the envelope's `times.knowledge_time`, not `event_time`, effective time or wall clock. `MissingReason` knowledge time is rejected for formal replay scheduling rather than replaced with another axis.

### S2R2-D03 — ordering

The caller supplies the sequence. The schedule copies it immutably and requires:

- unique `EventId`s;
- known UTC knowledge times;
- nondecreasing knowledge times in supplied order.

Equal knowledge times preserve supplied order. The replay engine never sorts to repair input. If an envelope has an explicit `ingestion_order`, that value is evidence only; this increment does not use it to synthesize a cross-source order.

### S2R2-D04 — deterministic speed control

Playback rate is an exact positive rational `numerator / denominator`.

For a source knowledge-time delta measured in integer microseconds, virtual playback delay is represented exactly as a rational number of microseconds:

```text
virtual_delay_us = source_delta_us * denominator / numerator
```

No rounding, floating point, `sleep()` or real-time scheduling occurs in this increment. Examples:

- `1/1` = 1x;
- `2/1` = 2x;
- `1/2` = 0.5x.

This is a deterministic pacing contract, not a claim about operating-system timing accuracy.

### S2R2-D05 — cutoff semantics

`advance_to(knowledge_cutoff)` is inclusive and monotonic. It emits not-yet-emitted envelopes with known knowledge time `<= cutoff`, in original supplied order. Backward cutoffs fail without advancing cursor state.

The cursor is finite and single-use per schedule. Replay completion means only that every supplied envelope has been emitted; it carries no economic or promotion meaning.

## Verification contract

Tests cover at least:

- empty schedule;
- immutable copy and frozen schedule state;
- multiple symbols in one provider/capture scope;
- mixed provider/scope rejection;
- unknown knowledge-time rejection;
- knowledge-time regression rejection without sorting;
- duplicate EventId rejection;
- equal knowledge time preserving supplied order;
- inclusive before/at/after cutoffs;
- backward cutoff rejection without cursor mutation;
- exact 1x/2x/0.5x rational pacing;
- deterministic repeated construction/results;
- absence of wall-clock, network, credential, strategy, execution and financial imports/capabilities.

### Isolated research CI

`.github/workflows/s2-research-ci.yml` is scoped only to `s2/**` pushes and pull requests targeting `integration/s2-research`. It runs:

```text
tests
lint
types
compile
dependencies
diff
foundation
```

It intentionally does **not** run `scripts/check_s1_boundary.py`. That scanner inventories the canonical Sprint 1 `src/` tree and is supposed to reject replay/research capability there. Running it against a deliberately isolated future-sprint research branch would conflate two different promotion boundaries. The omission is not a waiver: before any future Sprint 2 promotion, Sprint 2 must receive its own scope/capability gate.

The research workflow has `contents: read`, pinned GitHub actions, no secrets, no provider access and no deployment permission. Passing it would establish engineering evidence for this speculative branch only; it would not satisfy Sprint 1 acceptance or a future Sprint 2 gate.

## Evidence limits

This workstream can prove only deterministic scheduling behavior over supplied immutable market envelopes. It cannot prove:

- historical correctness of caller-supplied timestamps;
- completeness of market data;
- absence of leakage in upstream data construction;
- economic realism;
- model quality;
- Sprint 2 acceptance;
- Sprint 1 acceptance;
- Paper or Live readiness.

Remote CI remains required for promotion. At the current checkpoint GitHub-hosted runner allocation is blocked under Issue #36 (`runner_id=0`, `steps=[]` across Linux and Windows diagnostics), so any current code review is not execution evidence.
