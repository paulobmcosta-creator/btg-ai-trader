# S1-D — Bounded FIFO and passive health composition

- Date: 2026-09-13.
- State: DECISIONS_RECORDED_BEFORE_FIRST_MATERIAL_DEPENDENCY.
- Base: corrected health `e7337b57ba02b6342db3cb36beac938969dea074`.
- Authority: coordinator accepted the bounded experimental slice before implementation.
- Architectural choice: [ADR 0023](../../adr/0023-bounded-in-memory-observer-transport.md).

## Decisions before code

| DD | Decision | Limit |
|---|---|---|
| DD-22 | Immutable stdlib tuple FIFO, synchronous explicit state transitions, no external transport. | ADR 0023 records the architectural choice; no provider or wire format. |
| DD-59 | Required positive integer capacity, explicit BACKPRESSURE receipt retaining offered item, cumulative counters, no eviction. | Backpressure slice only; deduplication RQM-007 remains pending. |
| DD-36/DD-37 | Queue pressure is separate evidence; during RUNNING it requests DEGRADED through existing health policy, and existing latching remains. | No new lifecycle, timeout threshold or recovery authority. |

DD-54 is not triggered: this code does not implement a concurrent I/O edge. DD-57 remains unselected: accepted arrival order is preserved with no reorder window or late-event classification. DD-62 quarantine is separate future work; this typed channel accepts validated envelopes only and does not handle malformed raw transport payloads. DD-02 serialization is not triggered. DD-79 statistical outlier policies remain outside this slice.

## Contracts and claims

ObservationQueue is an immutable value with bounded items and conservation counters. offer/take return immutable results, never mutate previous state. Scope and capacity are explicit. A single synchronous owner must pass returned state forward; this is not an atomic multithread queue. A result is technical evidence only, not processing admission, durable acknowledgement or economic authority.

The health composition records queue snapshot, pressure flag and the original HealthAssessment. It preserves the existing health evaluator's monotonic continuity, missing values and posture latch. Queue evidence supplied as predecessor must satisfy public snapshot invariants, same scope/capacity and monotonic accepted/dequeued/rejected counts. Current full depth or recorded rejection signals pressure. No default capacity or production tuning is claimed.

RQM-027 receives deterministic bounded-buffer/property-style/load fixture evidence only. RQM-032..034 receive passive composition/transition evidence. RQM-007 dedup, RQM-025 quarantine, RQM-026 late annotation and provider-linked RQM-022/023 are not completed. Full NEG-CAP suite and Security Diff Scan remain pending.

## Verification required

Reject bool/float/zero/negative capacity, malformed queue storage and non-envelope items. Saturate, retry, drain and check FIFO and conservation across long deterministic command sequences with capacity bounds. Show rejected identity/payload unchanged and no mutation of prior snapshots. Verify live health plus pressure is NOT_READY, pressure cannot weaken an existing SAFE_HALT/EMERGENCY_STOP, and draining does not automatically unlatch. Preserve UNKNOWN samples and reject incompatible queue predecessors. Execute all six remote CI checks on the final HEAD before independent review.

## Next admission/quarantine increment

Design a bounded classifier over immutable raw evidence references plus normalized envelope/identity, with explicit accepted/duplicate/late/quarantined outcomes. Scope dedup by canonical identity; conflicting same-key payloads must preserve evidence and quarantine rather than overwrite. Tie durable acceptance to a verified append receipt from technical storage when integrated. Select DD-57/DD-62 and the dedup portion of DD-59 before code; no physical quarantine or durable dedup claim exists in this FIFO slice.
