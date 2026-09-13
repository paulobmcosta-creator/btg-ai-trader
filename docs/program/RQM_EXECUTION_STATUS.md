# Sprint 1 — RQM and Exit-Criteria Evidence Status

This is a **current evidence snapshot**, not a normative rewrite and not a Sprint 1 approval record.
The immutable authority remains [`0F-E`](../foundation/0F-E_sprint1_entry_contract.md), blob
`b04901dcc5612d3d418a6603a3a51a8e6e18ae08`.

## Audited canonical baseline

```text
SPRINT_BRANCH = sprint/1-market-observer
AUDITED_BASELINE = 5255ba5b35217275bab67dcc3c9a4bb03e479153
OBSERVER_COMPOSITION = INTEGRATED
PROPERTY_MUTATION = INTEGRATED
NEG_CAP_STRUCTURAL = INTEGRATED
NEG_CAP_RUNTIME_01_TO_10 = INTEGRATED
SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_ACCEPTANCE = NOT_GRANTED
```

The baseline includes the passive `FixtureObserver` composition, generated-property/mutation tests,
and structural + runtime negative-capability verification. No real provider, broker account, trading
credential, Paper engine, Risk engine or financial execution path is present.

### Principal remote evidence

| Evidence | Exact revision / run | Result |
|---|---|---|
| Observer composition | PR #27 head `87c8f92275e0db82dce026c6d15e37b7d94d7a65`; merge `64c419f5565cd5f222538ed7f79fcaaffb14476c` | reviewed; CI + upstream verification green |
| Property/mutation campaign | PR #26 head `650c073e66ba89088845b773f70455cf71235888`; merge `5c47dbe1f183cf4f87329803858fd1aebcc99207` | remote CI green; 36 generated cases; bounded 10/10 mutant detection campaign |
| NEG-CAP integrated evidence | PR #25 head `b822003d07ec7b3316bc9071c01f974d4a37e2d6`; merge `5255ba5b35217275bab67dcc3c9a4bb03e479153` | structural + runtime layers green on combined ancestry |
| Runtime NEG-CAP execution | `06038b3ab9ad10dd90f735592e859747594d24ae`, run `34789456375` | 434 tests passed, aggregate branch-inclusive coverage 95% |
| Final combined NEG-CAP ancestry | `b822003d07ec7b3316bc9071c01f974d4a37e2d6`, run `34789559956` | SUCCESS |
| Foundation integrity | merged PR #13 | frozen artifacts and normalized contract counters preserved |

`Security Diff Scan` is deliberately excluded from the PASS evidence above. The official available
scan interface required a Git-local target and could not be executed under the remote-only mandate.
No substitute is silently labeled as the official scan.

## Status vocabulary

- `SATISFIED`: evidence directly matches the required behavior for the implemented S1 scope.
- `SATISFIED_FIXTURE_SCOPE`: the normative behavior is demonstrated with the deterministic S1 fixture
  composition; this does not claim a real provider or production environment.
- `PARTIAL`: meaningful implementation/evidence exists, but at least one required semantic is not yet
  fully demonstrated.
- `BLOCKED_SECURITY_SCAN`: implementation and bounded static/runtime evidence exist, but the contract
  also calls for security-scan evidence that has not been executed.
- `NOT_TRIGGERED_CONDITIONAL`: a conditional capability/decision has not been activated by the chosen
  implementation path.

## 41 RQMs

| RQM | Status | Current evidence / remaining limit |
|---|---|---|
| RQM-001 | SATISFIED | Domain/envelope + composition preserve distinct `event_time`, `ingestion_time`, and `knowledge_time`; temporal regressions cover causal inversions. |
| RQM-002 | SATISFIED | Critical timestamps are timezone-aware UTC and naive timestamps fail closed. B3 calendar/session conversion has not been triggered as a filtering capability. |
| RQM-003 | SATISFIED | `MissingReason.UNKNOWN` is preserved through models, admission and composition; no optimistic synthesis. |
| RQM-004 | SATISFIED | Decimal zero and missingness are distinct and round-trip through fixture admission. |
| RQM-005 | SATISFIED_FIXTURE_SCOPE | Fixture/domain tests distinguish volume zero from missing data/source exhaustion. |
| RQM-006 | SATISFIED | Unknown ordering remains unknown; no synthetic source sequence/order is manufactured. |
| RQM-007 | SATISFIED | Bounded canonical EventId dedup is implemented, property-tested and integrated; duplicates do not become admitted FIFO events. |
| RQM-008 | SATISFIED | Versioned EventEnvelope metadata is validated and integrated with capture evidence. |
| RQM-009 | SATISFIED | `source_sequence` requires explicit `sequence_scope`; invalid combinations fail closed. |
| RQM-010 | SATISFIED_FIXTURE_SCOPE | `fixture-json-v1` / envelope versions are explicit; unknown versions/schema shapes are rejected without fallback. |
| RQM-011 | SATISFIED | Exogenous fixture observations do not receive synthetic correlation/causation identifiers. |
| RQM-012 | SATISFIED_FIXTURE_SCOPE | Run/input identity and provenance records are immutable; integrated manifest/config/code-pin evidence is persisted. |
| RQM-013 | SATISFIED | Canonical code/hash references reject mutable/abbreviated aliases in provenance tests. |
| RQM-014 | SATISFIED_FIXTURE_SCOPE | Exact raw bytes are archived before decode/admission; quarantine/filter decisions reference preserved evidence rather than erasing raw input. |
| RQM-015 | PARTIAL | RunId types and restart relations exist, but automatic uniqueness across independent OS process restarts is not proven; runtime currently receives RunId from the caller. |
| RQM-016 | SATISFIED | Typed `RunRelation` continuity is represented without rewriting prior run identity. |
| RQM-017 | SATISFIED_FIXTURE_SCOPE | CaptureContext/RunManifest bind run, code revision, provider and canonical config hash; CI fixtures expose sanitized SHA/config/manifest evidence. |
| RQM-018 | BLOCKED_SECURITY_SCAN | Scoped boundary/possible-secret heuristics and runtime synthetic-credential tests pass; official Security Diff Scan remains NOT_EXECUTED. |
| RQM-019 | SATISFIED | Lineage graph is acyclic and property/regression tested; cycles fail closed. |
| RQM-020 | SATISFIED | `InstrumentFamilyId`, `TradableInstrumentId` and scoped `ProviderInstrumentRef` are separate typed identities with point-in-time mapping. |
| RQM-021 | SATISFIED | Runtime NEG-CAP proves observed market data yields passive observation/evidence only and no execution authority. |
| RQM-022 | SATISFIED_FIXTURE_SCOPE | Explicit heartbeat/staleness policies, monotonic samples and conservative readiness degradation are integrated and tested. |
| RQM-023 | PARTIAL | Monotonic elapsed/age measurement exists, but a concrete end-to-end ingestion/transit latency metric is not yet produced by the integrated Observer. |
| RQM-024 | SATISFIED_FIXTURE_SCOPE | ProviderCapabilities explicitly declares FidelityMode/resolution/UNKNOWN semantics; no stronger source claim is synthesized. |
| RQM-025 | SATISFIED | Invalid/corrupt/oversize fixture frames produce structured quarantine receipts preserving exact raw evidence; following valid input remains processable. |
| RQM-026 | SATISFIED_FIXTURE_SCOPE | Late classification is explicit and does not reorder arrival; incompatible/unknown temporal comparisons remain `UNKNOWN`. |
| RQM-027 | SATISFIED | Finite immutable FIFO, observable backpressure and conservation/load/property tests prove no silent overwrite/drop in the bounded fixture owner model. |
| RQM-028 | SATISFIED_FIXTURE_SCOPE | Market-data provider contract is capability-based and fixture provider exposes only read-only metadata/read operations. Real provider qualification is separate. |
| RQM-029 | SATISFIED_FIXTURE_SCOPE | Evidence storage publishes immutable per-identity files, preserves bytes/hash and rejects overwrite/conflicting identity. |
| RQM-030 | SATISFIED | EvidenceArchive and AuditJournal are separate typed roots/APIs and remain isolated from financial schemas. |
| RQM-031 | SATISFIED_FIXTURE_SCOPE | Corrections require a new record/relation; existing canonical record is never replaced or deleted by the adapter. |
| RQM-032 | SATISFIED | RuntimePhase, SafetyPosture and ReadinessStatus are distinct enums and composition preserves the separation. |
| RQM-033 | SATISFIED | Liveness is evaluated independently from readiness; live heartbeat cannot override stale/blocked posture. |
| RQM-034 | PARTIAL | Health transitions and observation/decision sidecars are observable; a complete durable audit history for every operational transition, including post-storage-fault state, is not yet proven. |
| RQM-035 | SATISFIED | Integrated structural inventory + AST boundary + runtime NEG-CAP demonstrate no strategy/order/execution/economic-authority capability in the S1 graph. |
| RQM-036 | BLOCKED_SECURITY_SCAN | Current tree has zero runtime dependency on execution SDKs and no trading-credential consumption; official security-scan evidence required by the contract is still absent. |
| RQM-037 | SATISFIED | Nontrivial market-data fixtures terminate in technical evidence/queue decisions; financial tripwires remain untouched. |
| RQM-038 | SATISFIED | Candle interval/finalization/knowledge availability are distinct and future availability is rejected before consumption. |
| RQM-039 | PARTIAL | Causal frontier checks prevent known future availability in the Observer, but a general derived-data pipeline proving inheritance of ancestral temporal restrictions does not yet exist. |
| RQM-040 | PARTIAL | Scoped point-in-time provider-reference resolution is implemented; provider-driven instrument discovery of a real futures universe has not been implemented. |
| RQM-041 | SATISFIED_FIXTURE_SCOPE | Integrated run/config/input/raw hashes and fixture reprocessing provide capture traceability on the deterministic Observer graph. |

### RQM summary

```text
SATISFIED / SATISFIED_FIXTURE_SCOPE = 34
PARTIAL = 5   # RQM-015, 023, 034, 039, 040
BLOCKED_SECURITY_SCAN = 2  # RQM-018, 036
TOTAL = 41
```

The count above is an evidence classification, not a formal gate result.

## Required-core capability view

The 0F-E rule `ALLOWED != REQUIRED` remains controlling. Current status of the 14 positive capabilities:

| Capability | Class | State |
|---|---|---|
| AC-01 Instrument Discovery & Resolution | REQUIRED_CORE | PARTIAL — point-in-time resolution exists; real/provider-driven discovery remains absent |
| AC-02 Provider Symbol / Reference Mapping | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-03 Provider Capability Discovery | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-04 Read-Only Provider Authentication | REQUIRED_IF_TRIGGERED | NOT_TRIGGERED_CONDITIONAL — fixture provider requires no authentication |
| AC-05 Read-Only Market-Data Subscription | REQUIRED_CORE | PARTIAL — deterministic finite read-only fixture source exists; real streaming/subscription boundary not yet implemented |
| AC-06 Historical Request | PERMITTED_OPTIONAL | NOT_TRIGGERED_CONDITIONAL |
| AC-07 Tick & Candle Observation | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-08 Heartbeat & Liveness | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-09 Observable Latency Measurement | REQUIRED_CORE | PARTIAL — monotonic health age exists; explicit transit/ingestion latency metric still missing |
| AC-10 Quality / Admission | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-11 Invalid Event Quarantine | REQUIRED_CORE | SATISFIED |
| AC-12 Capture Context & Provenance | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-13 Technical Evidence Persistence | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-14 Telemetry / Dedup / Backpressure | REQUIRED_CORE | SATISFIED |

## Decision-gate status

Material decisions already used by the implementation were recorded before their dependent code in the
workstream history/ADRs, including ID/schema/numeric types, provider capabilities, registry, runtime
health states, RunManifest/CaptureContext, filesystem evidence storage, bounded in-memory transport,
dedup/late policy, quarantine/admission and synchronous composition.

Conditional decisions not activated by the current design remain legitimately unselected where their
trigger has not occurred (for example DB storage, authenticated feed credentials, B3 session calendar,
advanced gap/outlier filters and MT5 end-to-end compatibility).

**Open interpretation / promotion blocker:** `DD-60` (initial real Market Data provider) remains
UNDECIDED. The deliverable contract explicitly requires a base provider + deterministic mock/fixture,
which exists, while AC-05 is phrased as REQUIRED_CORE read-only subscription/streaming and DD-60 is
marked mandatory in the decision table with a trigger tied to a real adapter. Do not silently resolve
this tension by declaring MT5 canonical. Sprint 1 acceptance requires either:

1. implementing/qualifying a real read-only provider and resolving DD-60 before that dependency; or
2. an explicit coordination interpretation that the deterministic provider/fixture satisfies the S1
   acceptance boundary and defers real-provider admission to a later gate.

`DD-61` remains conditional on selecting MT5. The import-only MT5 spike does not trigger provider
admission and does not prove the eleven dual-use conditions.

## 11 Exit Criteria

| XC | Status | Evidence / blocker |
|---|---|---|
| XC-01 Required capabilities | PARTIAL | AC-01 discovery, AC-05 streaming/subscription and AC-09 explicit latency remain incomplete/ambiguous. |
| XC-02 Decision gates | PARTIAL | Most material DDs were resolved before dependency; DD-60 acceptance interpretation/provider choice remains open. |
| XC-03 All 41 RQMs | PARTIAL | Five RQMs remain partial and two retain the Security-scan blocker. |
| XC-04 27 HQIs / 7 QPIs | PARTIAL | QPI principles are preserved in current evidence, but HQIs mapped to incomplete RQM-023/039/040 cannot yet be claimed fully satisfied. |
| XC-05 NEG-CAP-01..10 | SATISFIED | All ten runtime obligations execute green alongside the structural boundary suite on combined ancestry. |
| XC-06 READ_ONLY_BY_CONSTRUCTION | SATISFIED_CURRENT_TREE | Pinned inventory + AST/import/config boundary and runtime tripwires prove the current S1 graph passive. Not the official Security Diff Scan. |
| XC-07 STRUCTURAL_ESCALATION | SATISFIED_CURRENT_TREE | Config/env/dependency injection cannot activate execution in the current graph; adding such capability requires code/inventory change. |
| XC-08 Zero trading credentials / ledger mutation | PARTIAL | Runtime and current-tree evidence is green, but full official security/credential audit evidence is not available remotely. |
| XC-09 Strict code / typing / lint | SATISFIED | Current integrated evidence runs Ruff, mypy, compile, dependencies and diff checks green. |
| XC-10 RunManifest / CaptureContext | SATISFIED_FIXTURE_SCOPE | Integrated fixture execution emits and validates manifest/context/config/code evidence. |
| XC-11 No Sprint-2+ escape | SATISFIED_CURRENT_TREE | Structural inventory excludes Paper/Risk/strategy/formal replay/execution from the S1 runtime graph. |

## Remaining blockers before a formal Sprint 1 PASS

```text
B1 = explicit ingestion/transit latency evidence (RQM-023 / AC-09)
B2 = complete operational-transition audit evidence (RQM-034)
B3 = derived-data temporal inheritance evidence or justified S1 non-applicability (RQM-039)
B4 = provider-driven instrument discovery / AC-01 completion (RQM-040)
B5 = resolve DD-60 / AC-05 real-provider-versus-fixture acceptance interpretation
B6 = official Security Diff Scan or explicit human waiver accepted as a governance exception
B7 = cross-process RunId restart uniqueness evidence or clarified responsibility boundary (RQM-015)
```

No item above authorizes a real account, trading credential, order API, Paper engine or economic path.
