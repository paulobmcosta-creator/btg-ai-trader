# S1-D — Finite canonical deduplication and late annotation

- Date: 2026-09-13.
- State: DECISIONS_RECORDED_BEFORE_FIRST_MATERIAL_DEPENDENCY.
- Base: FIFO `673bf6b1f4230c2207a29791841f31836b92c223`.
- Authority: bounded technical design approved by coordinator before code.
- Scope: immutable fixture values and deterministic classification only.

## Decisions before code

| DD | Concrete decision | Boundary |
|---|---|---|
| DD-59 | Finite session-scoped canonical EventId table. NEW records occupy one slot; DUPLICATE and IDENTITY_CONFLICT retain the first canonical record; unknown new IDs at capacity return CAPACITY_EXHAUSTED without eviction. | No automatic provider key inference, persistence, transport admission or exactly-once claim. |
| DD-57 | Annotate LATE only when current and supplied frontier have the same exact scoped source and resolved instrument, known UTC EventTime values, and matching known basis/resolution. Equality or a later timestamp is ON_OR_AFTER_FRONTIER; insufficient comparability is UNKNOWN. | No reorder buffer, inferred frontier, automatic watermark advancement, deletion, clock read or tolerated lateness window. |

These implementation/policy DDs require no new ADR under 0F-E. ADR 0023 transport remains unchanged. DD-02 serialization/hash selection and DD-62 physical quarantine are not triggered.

## Canonical identity and equality

The key is explicit session scope plus EventId. Re-offering a fact with a newly fabricated ID is not detected as a duplicate; providers must preserve canonical fact identity when their evidence supports it. External ID or scoped source sequence remain evidence, never an automatically substituted key.

Compare typed values directly through an explicit immutable projection: event_type, source, resolved-or-missing instrument_id, EventTime, effective_time, payload, envelope/schema versions, external_event_id, source_sequence, sequence_scope, correlation_id and causation_id. Causal identity is intrinsic evidence and remains in equality. Numeric/missing semantics come from the domain records; no coercion, string serialization or hash algorithm is introduced.

Exclude ingestion_time, internal knowledge_time and ingestion_order from factual equality. These describe an observation/receipt, not a new source fact. A later receipt's different knowledge metadata does not rewrite the canonical record, establish historical availability or prove causal point-in-time retrieval. Results retain the original canonical envelope and incoming envelope separately. Enrichment or correction of compared fact fields under the same ID is IDENTITY_CONFLICT and requires a later explicit reconciliation/quarantine path; it never overwrites the first known record.

DedupState is immutable, strictly finite, with positive integer capacity (no bool) and unique canonical IDs. A single synchronous owner threads returned state forward. Old snapshots or result history retained by a caller are caller-owned memory, not hidden internal retention. Explicit state construction does not authenticate history or restart continuity.

## Late annotation

Comparison requires a concrete TradableInstrumentId on both records and exact equality of ProviderInstrumentRef, including provider, scope and symbol. Missing instrument identity, missing timestamp/basis/resolution, different basis/resolution or source/instrument mismatch returns UNKNOWN, not ON_TIME. Resolution equality establishes only this narrow comparison contract, not global clock synchronization. The frontier is explicitly supplied evidence; callers own its causal availability and selection.

LATE does not mean invalid or automatically quarantined. Arrival order, event identity and all timestamps remain intact. The result stores both input references so a later admission layer can preserve its evidence. No readiness or financial authority is conferred.

## Verification and limits

Tests must cover same-ID same-fact with different receipt metadata, changed payload/source/schema-related fact evidence, distinct IDs, capacity exhaustion, duplicate/conflict recognition at capacity, immutable original preservation, unique canonical entries, invalid capacities and non-envelope input. Deterministic long sequences verify bounded table size and no silent eviction.

Late tests require equal/newer/older known values, missing each time component, mismatched source/instrument/basis/resolution and unresolved instrument; none may mutate input or arrival order. RQM-007/RQM-026 receive fixture-level evidence only. Raw quarantine, provider normalization, durable acceptance, causal historical retrieval and full S1 acceptance remain pending. Six remote CI checks and independent review are required; Security Diff Scan remains NOT_EXECUTED.
