# S1-B — Registry and capability contract decisions

- Date: 2026-09-13.
- State: DECISIONS_RECORDED_BEFORE_FIRST_MATERIAL_DEPENDENCY.
- Base: `5158dc3375fd9ed0a311dd745a981fadf2ea643a`, corrected S1-A models.
- Authority: autonomous remote mandate, bounded S1-B implementation authorized by coordination.
- Scope: passive in-memory registry and typed provider capability contracts. No concrete provider, network, persistence, execution, strategy or replay runtime.
- Promotion: draft stacked PR; not Sprint 1 acceptance. Formal Security Diff Scan and complete NEG-CAP verification remain separate pending gates.

## Decisions before code

| DD | Decision and first dependency | Evidence |
|---|---|---|
| DD-33 | Stdlib immutable ProviderCapabilities with three-valued CapabilitySupport: SUPPORTED, UNSUPPORTED, UNKNOWN. Minimum catalog: tick observation, candle observation, source sequence. Timestamp resolution and historical fidelity are explicit, scoped declarations or UNKNOWN. A metadata-only provider Protocol exposes its descriptor; no optional market operations are forced into a universal interface. | Type/constructor tests, fixture-only Protocol implementation, explicit unknown/rejection cases. |
| DD-58 | Immutable in-memory InstrumentRegistry holding mapping evidence. Resolution consumes exact provider/scope/symbol, effective instant and knowledge cutoff; it never reads a clock or chooses a global/latest symbol. | Scoped and causal mapping tests, interval boundaries, ambiguity and many-to-one tests. |

Both are `MAY_DECIDE_DURING_SPRINT_1`, with no mandatory ADR according to 0F-E DD-33/DD-58 rows. This concretizes existing ADR-0005/0006 semantics without changing architecture. DD-60 remains unresolved: neither a vendor nor a laboratory feed is selected. Future discovery/stream/history adapters require their own material decisions, including DD-60 when triggered.

## Registry semantics

An InstrumentMapping carries ProviderInstrumentRef, TradableInstrumentId, InstrumentFamilyId, validity `[valid_from, valid_until)`, `known_at` and a safe opaque evidence reference. `valid_until=None` means explicitly open-ended validity, not unknown. Unknown validity/knowledge is rejected from this resolvable catalog; such raw evidence belongs in the future quarantine/provenance path and must not be assigned artificial times. All instants must be explicit UTC as in S1-A.

Queries first exclude evidence known after `knowledge_cutoff`, then filter the scoped reference and validity at `valid_at`. A later-known mapping is not usable merely because it applies retrospectively. No automatic latest-wins, revision matching or retroactive correction policy is implemented.

Resolution returns NOT_FOUND if no admissible record matches, RESOLVED if all matches agree on the concrete instrument and family, or AMBIGUOUS if they conflict. Only RESOLVED exposes an instrument/family; ambiguity cannot select the first result. NOT_FOUND means absence from this catalog at these boundaries, not market nonexistence or lack of trading. Matching evidence remains visible for audit. A single instrument may have multiple provider references: no global bijection or reverse-map uniqueness is imposed.

Registry construction copies a finite caller-supplied iterable to a tuple. New snapshots do not mutate existing records. This increment has no persistence, canonical registry version identity, historical corrections, rollover selection policy or production discovery claim.

## Capability semantics

A descriptor is scoped to one provider and capture context. UNKNOWN is not SUPPORTED. Source sequence support requires a non-empty sequence scope; unsupported/unknown sequence capability carries no fabricated scope. Resolution is a positive timedelta or explicit missing reason. Fidelity is one of OBSERVATION_FAITHFUL, SOURCE_SEQUENCE_FAITHFUL, EVENT_TIME_ONLY or UNKNOWN; source-sequence-faithful requires declared support. These are declarations, not verified empirical guarantees.

ProviderMetadata is a Protocol with only `describe_capabilities()`. This partial metadata contract does not promise subscriptions, historical access, authentication, readiness or execution. Optional operations will have specialized contracts when material. A static test fixture implements only metadata discovery and is not a production feed. No capability is named or interpreted as permission to trade.

## Verification and limits

- Reuse the S1-A identity and UTC validators without modifying their models.
- Exercise UTC rejection, zero-length/inverted validity and explicit unknown failures.
- Test inclusive start, exclusive end, open-ended validity and exact knowledge-cutoff equality.
- Test provider/scope isolation, symbol reuse, many-to-one mappings, late-known evidence, no-match and conflicting mappings.
- Test copied immutable snapshots and preservation of mapping evidence.
- Test unsupported/unknown capabilities, nonpositive resolution and source-sequence scope consistency.
- Run inherited six remote checks on the exact final head; do not reuse an older SHA's results.

Traceability: ADR-0005/0006/0015; 0F-E §17.2, S1-EC-054/063/089/090; RQM-020/028/040 and declaration-only RQM-024; B-HQI-16/25/26, QPI-02/05/11/12. Tests do not validate a real feed, source truth, executable liquidity, instrument choice, registry completeness, full provenance or the complete Sprint 1 exit contract.
