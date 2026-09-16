# Sprint 2 Entry Contract — Data Platform & Causal Market Replay

## Authority and baseline

```text
SPRINT_1_FINAL_VERDICT = PASS
SPRINT_1_ACCEPTED_HEAD = 57d820e256dd386624c1842c6f60b6797ba792aa
SPRINT_2_CANONICAL_BRANCH = sprint/2-data-platform-replay
ENTRY_MATERIALIZATION_BRANCH = s2/00-entry-contract-materialization
FINANCIAL_AUTHORITY = ABSENT
REAL_MONEY = FORBIDDEN
```

This contract governs the first functional increment of Sprint 2. It is derived from the accepted Sprint 1 state, the frozen Foundation, `AGENTS.md`, the living Master Plan and the Sprint 2 scope record. It does not rewrite frozen Foundation artifacts.

Historical PRs #9 and #37 are research inputs only. They are not canonical implementation and must not be merged wholesale into the Sprint 2 baseline.

## 1. Mission

Sprint 2 builds a **Data Platform & Causal Market Replay** layer that can consume immutable market-data evidence, preserve historical knowledge boundaries and reproduce a causal sequence deterministically.

Sprint 2 is not an economic backtester and has no financial authority.

## 2. Authorized positive capability set

The following capabilities are allowed in Sprint 2, subject to this contract and recorded decisions:

| ID | Capability | Status at entry |
|---|---|---|
| S2-AC-01 | Dataset / capture input-boundary validation | REQUIRED |
| S2-AC-02 | Lossless normalization preserving source facts and explicit missingness | REQUIRED |
| S2-AC-03 | Provider/capture-scope causal lane partitioning | REQUIRED |
| S2-AC-04 | Immutable causal replay schedule | REQUIRED |
| S2-AC-05 | Explicit inclusive knowledge-cutoff advancement | REQUIRED |
| S2-AC-06 | Controllable virtual clock with monotonic advancement | REQUIRED |
| S2-AC-07 | Exact logical replay-speed representation without wall-clock dependence | REQUIRED |
| S2-AC-08 | Replay input provenance / manifest | REQUIRED |
| S2-AC-09 | Replay run identity and lineage from input evidence to outputs | REQUIRED |
| S2-AC-10 | Data-quality evidence and fail-closed anomaly reporting | REQUIRED |
| S2-AC-11 | Schema compatibility / upcast mechanism | REQUIRED_IF_TRIGGERED |
| S2-AC-12 | Deterministic repeated replay of identical logical inputs | REQUIRED |
| S2-AC-13 | Dataset persistence format | REQUIRED_IF_TRIGGERED |
| S2-AC-14 | Historical external-source ingestion | REQUIRED_IF_TRIGGERED |

## 3. Negative capabilities

The following capabilities are prohibited throughout Sprint 2 unless a later formal sprint gate changes authority:

```text
S2-NC-01 Strategy operational path = ABSENT
S2-NC-02 Signal-to-trade operational path = ABSENT
S2-NC-03 Risk authorization path = ABSENT
S2-NC-04 Paper execution = ABSENT
S2-NC-05 Live execution = ABSENT
S2-NC-06 Broker order/account API = ABSENT
S2-NC-07 Financial Ledger mutation = ABSENT
S2-NC-08 P&L / economic backtest = ABSENT
S2-NC-09 Spread/fee/slippage/queue-fill economic model = ABSENT
S2-NC-10 Predictive ML operational wiring = ABSENT
S2-NC-11 Real-money authority = ABSENT
S2-NC-12 Mutation of source evidence = ABSENT
S2-NC-13 Fabricated event/knowledge time = ABSENT
S2-NC-14 Cross-lane global ordering without explicit evidence = ABSENT
S2-NC-15 Silent imputation of missing market facts = ABSENT
S2-NC-16 Wall-clock-driven causal semantics = ABSENT
```

## 4. Canonical temporal semantics

The replay boundary is causal, not merely chronological.

1. `knowledge_time` controls whether information may be visible at a replay cutoff.
2. `event_time` remains source/event evidence and must never be used to reveal knowledge earlier than the recorded knowledge boundary.
3. Equal `knowledge_time` values preserve existing causal order evidence; they do not authorize arbitrary sorting.
4. Unknown or missing temporal evidence is not replaced by another axis.
5. Backward movement of the virtual clock or cutoff fails closed.
6. A replay repeated from the same logical inputs, configuration and code version must yield the same ordered logical output identities.

## 5. Dataset and lane boundary

The first functional Sprint 2 increment uses one explicit causal lane identified by:

```text
(provider_id, capture_scope)
```

Multiple instruments may exist inside one lane when they were observed under the same capture scope. Data from unrelated provider/capture scopes must not be assigned a synthetic global order.

The input boundary must preserve at least:

- immutable input artifact identities;
- provider and capture scope;
- source hashes or equivalent content identities when available;
- code revision;
- configuration identity/hash;
- ordered input event identities;
- explicit temporal evidence;
- replay run identity;
- lineage from input to replay output.

## 6. Decisions inherited versus newly activated

Sprint 1 decisions that are already materialized are inherited and are not silently reopened. In particular, existing domain identity, temporal fields, provenance conventions, technical persistence semantics and negative financial boundaries remain authoritative.

The following Foundation decisions become relevant to Sprint 2 and are governed by `docs/program/S2_DECISION_REGISTER.md`:

```text
DD-05 schema migration / upcasting
DD-15 RunInputBoundary
DD-27 operational snapshot format
DD-28 retention / archival policy
DD-77 historical data source/vendor
DD-78 historical sampling/resolution
DD-80 missing-data treatment
DD-81 continuous-series adjustment/stitching
DD-82 research dataset physical format
DD-83 dataset hashing/versioning
```

Decisions whose first material dependency is later than the current increment remain deferred.

## 7. First functional increment authorized after this gate

After this entry materialization is merged and green, the first Antigravity implementation increment may create a pure replay kernel with the following maximum scope:

- immutable schedule over existing `EventEnvelope` values;
- one explicit `(provider_id, capture_scope)` lane;
- known `knowledge_time` required for replay scheduling;
- caller/source causal order preserved;
- duplicate identity and knowledge-time regression rejected;
- inclusive monotonic `advance_to(knowledge_cutoff)`;
- exact positive rational replay speed;
- no `sleep()`, wall-clock scheduling, network/provider I/O or credentials;
- no economic or financial artifacts.

This increment should reuse concepts from PR #37 only after re-deriving them against the accepted Sprint 1 types. It must be implemented anew on a child branch of the canonical Sprint 2 branch.

## 8. CI and boundary gate

Before first functional code is accepted, Sprint 2 must have its own CI and boundary checks. The Sprint 1 boundary scanner is not reused as the Sprint 2 capability model because it intentionally rejects replay capability.

Required Sprint 2 CI jobs:

```text
tests
lint
types
compile
dependencies
foundation
s2-boundary
diff
```

The S2 boundary check must permit causal data/replay modules while rejecting financial execution, Strategy/Risk/Paper/Live paths, broker order/account APIs, real-money authority, silent temporal fabrication and prohibited economic-backtest constructs.

## 9. Entry acceptance criteria

The Sprint 2 functional gate is PASS only when all conditions below hold:

```text
S2-EG-01 Sprint 1 accepted baseline preserved
S2-EG-02 Frozen Foundation unchanged
S2-EG-03 Decision register materialized
S2-EG-04 Positive/negative capability matrix materialized
S2-EG-05 Temporal/lane/replay semantics explicit
S2-EG-06 Sprint 2 boundary scanner exists and passes
S2-EG-07 Sprint 2 CI exists and passes on exact entry-gate head
S2-EG-08 Antigravity handoff is constrained to this contract
S2-EG-09 Historical PRs #9/#37 remain research-only inputs
S2-EG-10 No financial or economic-backtest capability introduced
```

Only after `S2-EG-01..10 = PASS` may `S2_FIRST_FUNCTIONAL_CODE` be changed to `AUTHORIZED`.

## 10. Failure semantics

Any ambiguity involving temporal truth, data provenance, causal order, scope identity or prohibited financial capability must stop implementation and produce a documented decision or finding. The system must not repair uncertainty by inventing order, timestamps, missing values or economic semantics.