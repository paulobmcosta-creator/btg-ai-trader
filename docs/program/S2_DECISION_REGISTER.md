# Sprint 2 Decision Register

This register activates only decisions whose first material dependency can occur in Sprint 2. Historical Foundation decision IDs remain unchanged.

## Active decisions

| ID | Decision | Sprint 2 adjudication | Trigger / boundary |
|---|---|---|---|
| DD-05 | Schema migration/upcasting | CONDITIONAL — no upcast in first replay kernel; if a second schema version is consumed, stop and materialize an explicit compatibility/upcast contract before code | First cross-schema replay |
| DD-15 | RunInputBoundary | DECIDED FOR S2 — immutable replay input manifest containing provider, capture_scope, ordered event/artifact identities, hashes when available, code revision, config identity, temporal semantics and replay run identity | First replay schedule |
| DD-27 | Operational snapshots | DEFERRED — replay cursor state may be explicit in memory, but durable operational snapshots require a separate decision before persistence | First durable replay checkpoint |
| DD-28 | Retention/archival | DEFERRED — source evidence remains governed by existing preservation rules; no deletion/TTL policy introduced in first increment | First managed dataset retention feature |
| DD-77 | Historical data source/vendor | DEFERRED FOR EXTERNAL VENDOR — first increment consumes existing Observer evidence or controlled fixtures only | First external historical-data ingestion |
| DD-78 | Historical sampling/resolution | DEFERRED — first kernel preserves supplied event granularity; no resampling policy | First canonical resampling/aggregation feature |
| DD-80 | Missing-data treatment | DECIDED FOR CANONICAL NORMALIZATION — preserve missingness/UNKNOWN; no silent imputation or discard. Any analytical imputation must be a later explicit derived transformation | First normalization path |
| DD-81 | Continuous-series stitching/adjustment | DEFERRED AND FORBIDDEN IN FIRST INCREMENT — no automatic futures stitching or back-adjustment | First continuous-series feature |
| DD-82 | Research dataset physical format | DEFERRED — first replay kernel is in-memory over existing envelopes. Must be decided before first canonical persisted research dataset | First dataset persistence feature |
| DD-83 | Dataset hashing/versioning | PARTIALLY DECIDED — content identities/hashes must be preserved when available; the concrete registry/versioning technology remains deferred until persisted datasets exist | First persisted dataset/version registry |

## Sprint 2 local implementation decisions

These local decisions are valid for the first functional replay increment and do not renumber Foundation DDs.

### S2-D01 — causal lane
One replay schedule is one explicit `(provider_id, capture_scope)` lane. Multiple instruments are allowed in the same lane; unrelated lanes are not globally ordered without an explicit later merge contract.

### S2-D02 — causal availability axis
Known `knowledge_time` is the visibility boundary. `event_time` is preserved as source evidence but cannot be used to reveal future knowledge.

### S2-D03 — ordering
Caller/source order is preserved. Knowledge-time regressions fail closed. Equal knowledge times preserve supplied order. The replay kernel does not sort by `event_time` or synthesize order.

### S2-D04 — cutoff semantics
`advance_to(knowledge_cutoff)` is inclusive and monotonic. A backward cutoff raises an error without advancing state.

### S2-D05 — virtual pacing
Replay speed is an exact positive rational. Logical pacing is derived from knowledge-time deltas with exact arithmetic; the first kernel does not sleep or depend on wall-clock scheduling.

### S2-D06 — deterministic equivalence
For Sprint 2 replay, determinism means the same accepted logical input boundary, code revision and configuration produce the same ordered logical output identities and pacing values. Byte-for-byte equivalence of future persisted dataset encodings is not claimed until DD-82/83 are fully materialized.

### S2-D07 — source immutability
Replay never mutates source evidence. Processing receipts, manifests and lineage are separate artifacts.

### S2-D08 — no economic interpretation
Replay completion, pacing, gaps or anomalies do not imply P&L, fill, slippage, cost, signal, risk or trading readiness.

## Explicitly still undecided

No Sprint 2 entry decision selects a cloud provider, broker execution platform, Risk/Strategy engine, order type, Paper/Live mechanism, ML framework, economic cost model, slippage model, fill model or production infrastructure.