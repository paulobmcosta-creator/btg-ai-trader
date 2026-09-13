# S9-A — Scoped recovery continuity fixtures

- Status: SPECULATIVE; isolated future runtime contract; not for S1 promotion.
- Base: 183203307169f41ce40e035fe19f1d0a570e3e16; compare against integration/research.
- Authority: autonomous mandate 2026-09-13, independent READY runtime/recovery work.
- Norms read: ADR0010 refined by0019; ADR0020; Master Plan sections6.7–6.9; DD35.
- Decision before code: frozen stdlib dataclasses and enums describe a finite, ordered sequence of journal segment metadata for one explicit scope. Positions are nonnegative scoped journal boundaries, not event IDs, source sequence, market order or global chronology.
- DD35 (experimental and partial): an assessment of supplied continuity metadata only. No snapshot format, recovery handler, storage, retry, matching, reconciliation rounds, watchdog or authority is selected. DD27/30/31/32/34/38/39 remain deferred.

A JournalSegment covers the half-open interval [start, end) in one supplied journal scope. It carries an integrity assertion VERIFIED, UNKNOWN or CORRUPT. The assessment cannot verify bytes or authenticate this assertion; future adapters must provide trustworthy verified evidence. An empty or reverse segment is invalid.

RecoveryBoundary contains one scope, a snapshot's next position and the required target next position. Snapshot integrity is explicit. Segments must be supplied in the order claimed by that journal; the implementation never sorts them or merges scopes.

For a boundary to be METADATA_CONTIGUOUS, snapshot integrity must be VERIFIED, each segment must have VERIFIED integrity and matching scope, its start must equal the preceding boundary, and its end may not exceed the target. The final boundary must equal the target. Gaps, overlaps, wrong scopes, insufficient evidence and extra segments fail closed. A zero-length required range needs a verified snapshot and no segments.

The assessment result preserves reasons and the exact boundary. It is not a RecoverySession, proof of reconstructed state, reconciliation result, readiness, authorization, RunId or new economic commitment. Procedural completion and successful metadata assessment never emit READY.

Regression matrix: exact adjacency; empty required range; missing tail; gap; overlap; wrong scope; reordered segments; beyond-target segment; unknown/corrupt snapshot or segment; mutable input copied; malformed counters and booleans rejected; no mutation after rejection. Tests use only in-memory fixtures, no disk/network/broker/runtime controls.

Promotion requires review, CI on exact head and subsequent integration with trustworthy artifact validation and scope-specific recovery outcomes. This precursor alone does not satisfy recovery, reconciliation or production gates.
