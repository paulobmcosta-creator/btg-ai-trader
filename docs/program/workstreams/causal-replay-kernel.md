# Causal replay kernel — SPECULATIVE engineering harness

- Status: SPECULATIVE; isolated S3 branch; not promoted into S1.
- Base: `183203307169f41ce40e035fe19f1d0a570e3e16`.
- Authority: remote autonomous mandate 2026-09-13; bounded independent engineering work.
- Merge boundary: review against `s1/00-post-merge-authorization` is comparison only. DO NOT MERGE into the S1 baseline.
- Scope: finite in-memory fixture scheduling and a controllable causal clock. No provider, normalization, market-event schema, financial artifacts, strategy, Paper, Ledger or production capability.

## Decisions recorded before implementation

These are experimental implementation choices confined to this harness. They neither supersede approved ADRs nor freeze canonical S1 data policy.

- DD-15 (limited): an immutable tuple of opaque fixture references, exact UTC knowledge times, one explicit ordering scope and strictly increasing positions is the harness input boundary. It is not a complete production RunInputBoundary or RunManifest. The caller must preserve immutable fixture contents externally; a reference alone does not establish actual input provenance.
- DD-16 (limited): equality means the exact same ordered sequence of references and UTC instants for identical schedule, initial clock and cutoff calls. No floating-point, economic or byte-level serialization equivalence is claimed.
- DD-13/DD-14: no RNG or seeds are used or selected.
- DD-19: Python 3.12 remains the supported baseline; remote CI evidence is required before integration. No OS/container policy is chosen.
- DD-57 and S1 ordering/deduplication remain unchanged. The scheduler validates one supplied scope; it does not merge independent streams, invent global historical order or sort by event_time.

## Contracts and boundaries

`ReplayClock` accepts a timezone-aware initial instant, normalizes to UTC, and advances only forward (equality permitted). It has no wall-clock, sleep, I/O or RNG dependency.

`FixtureScheduleEntry` holds only non-empty fixture reference and ordering scope, non-negative integer position (bool is invalid), and known timezone-aware knowledge time. UNKNOWN is rejected, not replaced with event_time or zero. Input time evidence is a caller precondition; the harness cannot independently prove historical availability.

`ReplaySchedule` copies entries into a tuple and validates unique references, one scope, strictly increasing positions and nondecreasing knowledge times. Supplied order is preserved, never fabricated. Equal knowledge times are resolved only by the supplied positions. Empty schedules are valid.

`ReplayCursor.advance_to(knowledge_cutoff)` has inclusive cutoff semantics. It reveals entries whose known availability is at or before the requested cutoff and advances the clock through their availability times, then to the cutoff. A future entry remains withheld. Backward cutoffs fail without changing cursor state. The initial clock must not lie after the first item: missing historical processing is never silently fabricated. Returned entries do not imply event-time ordering, domain decisions, statistical independence, execution, economic output or promotion.

The cursor owns its clock and exposes only its current instant; callers cannot advance a shared clock behind the scheduler. There are no callbacks or payload objects. The namespace is `btg_ai_trader.research`, explicitly SPECULATIVE and not imported into an Observer.

## Verification matrix

| Invariant | Tests planned | Normative mapping |
|---|---|---|
| Naive/unknown times fail closed; aware offsets resolve to UTC | Constructor and cutoff rejection; offset equivalence | ADR-0004; B-HQI-03/05/25; QPI-02/11 |
| No future fixture is emitted before knowledge cutoff | Before/at/after cutoff and stepped playback | B-HQI-07; C-HQI-09; D-HQI-26; QPI-02 |
| No backward time or fabricated ordering | Clock and cursor rollback; mixed scope and inconsistent ordering rejection | ADR-0003/0004; B-HQI-26; QPI-11 |
| Input immutability and explicit deterministic scope | Mutable input copy, frozen records, repeated schedules | ADR-0017/0021; B-HQI-19; QPI-12 |
| Limits stay explicit | Empty fixture schedule; no payload/callback/finance imports | D-HQI-35; E-HQI-46; QPI-01 |

Tests validate computational behavior on fixtures only. They cannot prove historical knowledge-time truth, absence of leakage in unseen payloads, market-data quality, quantitative merit, OOS, full Backtester Gate B, Paper, or operational readiness. Workflow execution and exact commit results must be attached to the PR; code review alone is not execution evidence.
