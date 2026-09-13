# ADR 0023 — Bounded in-memory Observer transport

- **Status:** Aceita por delegação técnica do mandato autônomo, escopo experimental S1-D.
- **Data:** 2026-09-13
- **Decisão adiada:** DD-22
- **Base:** `e7337b57ba02b6342db3cb36beac938969dea074`
- **Autoridade:** recorte técnico aprovado pelo coordenador antes desta materialização; não constitui aprovação humana de Sprint 1, arquitetura financeira ou operação real.

## Contexto

ADR 0002 defines a modular event-driven monolith whose domain does not require concurrent I/O. ADR 0006 requires finite critical queues, observable backlog and no silent loss; ADR 0015 preserves event identity and temporal evidence across transport. The current slice has immutable observation envelopes and passive health evidence, without provider or persistence integration.

## Problema

Select the first internal transport mechanism under DD-22 before code depends on it, and expose saturation without overwriting accepted observations or making an exactly-once claim.

## Alternativas consideradas

- External broker: adds infrastructure, serialization and operational failure modes without current evidence of need.
- Unbounded queue or overwrite-on-full ring: violates the finite-buffer/no-silent-loss invariant.
- Mutable concurrent queue: useful at I/O edges, but selects synchronization before this slice has any concurrent producer.
- Immutable bounded FIFO state and synchronous transitions: deterministic, explicit ownership and bounded payload retention; selected for this experimental slice.

## Decisão

Use a stdlib-only immutable tuple of validated EventEnvelope records. A queue has an explicit scope and strictly positive integer capacity; bool is not capacity. Every offer returns the original item, ACCEPTED or BACKPRESSURE, and the new immutable queue state. A full queue retains its accepted items unchanged, increments a rejection counter and returns the offered item to its caller for explicit retry. Taking an item returns the oldest accepted item and the new state. Empty take is explicit.

No serializer, broker, network, worker, clock reader or runtime loop is introduced. One caller owns and threads state transitions synchronously; retaining or branching old states is a fixture capability, not shared concurrent delivery. State validation requires exact tuple storage, validated envelopes, bounded depth, nonnegative integer counters and accepted minus dequeued equals depth.

Backpressure evidence includes scope, capacity, depth, accepted/dequeued/rejected counts. Counters retain no rejected payload history. Full occupancy or a nonzero rejection count is conservative pressure evidence in this experimental queue epoch. Composition with health preserves separate lifecycle and posture; during RUNNING, pressure requests at least DEGRADED. A live/fresh feed therefore cannot make passive readiness READY under pressure. Restrictive posture remains latched across subsequent evaluations. UNKNOWN heartbeat/market evidence is never synthesized.

## Invariantes

- No silent overwrite, drop, eviction, unbounded payload buffer or automatic retry.
- FIFO follows accepted arrival order; no event_time sorting, identity replacement or synthetic source sequence.
- A BACKPRESSURE return leaves ownership with the caller; it is not durable acceptance.
- No exactly-once, persistence, cross-process delivery, authenticated history or restart guarantee.
- Composition validates same queue scope/capacity and nondecreasing counters when a predecessor is supplied; absence of predecessor is a new fixture evaluation, not recovery authorization.
- No generic mutable payload, execution callback, order capability, trading credential or financial effect.

## Consequências positivas

Finite retained payloads, deterministic transitions, explicit pressure evidence and simple integration with future admission/persistence contracts.

## Consequências negativas / trade-offs

Tuple transitions copy up to capacity references. Old immutable snapshots may be retained by callers; callers own total history retention. An in-memory rejection receipt cannot prevent a caller from ignoring it and provides no durability on process loss. Historical rejection conservatively blocks the queue epoch; no automatic recovery/reset API is supplied.

## Condições para reabrir a decisão

Measured I/O concurrency, throughput, durability or distribution requirements require an explicit successor decision before adopting workers, a broker or another transport mechanism. No change may weaken traceability or finite capacity.

## Relação com outros ADRs

Concretizes DD-22 under ADR 0002/0006/0015. Uses temporal semantics from ADR 0004 and passive containment from ADR 0011/0020. Future technical persistence is independently governed by ADR 0024; this slice does not depend on that unimplemented contract.
