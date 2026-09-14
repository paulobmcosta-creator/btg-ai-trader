# Sprint 1 — RQM and Exit-Criteria Evidence Status

This is a **current evidence snapshot**, not a normative rewrite and not a Sprint 1 approval record.
The immutable authority remains [`0F-E`](../foundation/0F-E_sprint1_entry_contract.md), blob
`b04901dcc5612d3d418a6603a3a51a8e6e18ae08`.

## Current integrated baseline and active provider branch

```text
SPRINT_BRANCH = sprint/1-market-observer
INTEGRATED_BASELINE = 4fb5807f985d06ef8673a28e689b815a08763940
ACTIVE_PROVIDER_PR = #34
ACTIVE_PROVIDER_BRANCH = s1/20-btg-dataservices-adapter
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
SPRINT_1_LIFECYCLE = OPEN
S1_A_AUTHORIZED = YES
OBSERVER_COMPOSITION = INTEGRATED
PROPERTY_MUTATION = INTEGRATED
NEG_CAP_STRUCTURAL = INTEGRATED
NEG_CAP_RUNTIME_01_TO_10 = INTEGRATED
SECURITY_DIFF_SCAN = NOT_EXECUTED
DD_60_INITIAL_REAL_PROVIDER = ACCEPTED_BTG_SOLUTIONS_DATA_SERVICES
DD_68_FIRST_LAB = RESOLVED_WIN_TRADES_REALTIME
AC_05_PROVIDER_ADAPTER = IMPLEMENTED_IN_PR_34_NOT_INTEGRATED
REAL_PROVIDER_SESSION = NOT_EXECUTED
SPRINT1_ACCEPTANCE = NOT_GRANTED
REAL_MONEY_PATH = ABSENT
TRADING_CAPABILITY = ABSENT
```

The integrated baseline remains passive and provider-agnostic. PR #34 adds the selected BTG Solutions Data Services read-only boundary but is not part of the integrated baseline until its exact-head CI/review gate is green and the PR is merged.

## Principal integrated evidence

| Requirement | Evidence | Integrated result |
|---|---|---|
| RQM-023 / AC-09 | PR #28 | Runtime latency boundary emits the Observer step together with monotonic elapsed/transit evidence; merged as `035113c5c6ab58237b304304c3c884b3625bbed2` |
| RQM-015 | PR #29 | Independent-process RunId uniqueness/restart evidence; merged as `138352088a6d8929663163d410cbc526584219cf` |
| RQM-034 | PR #30 | Real passive `FixtureObserver` transition persisted with before/after health state and AuditJournal reference; merged as `3e424b5516cd1d1391489825b290f3a02143d917` |
| RQM-039 / B-HQI-08 | PR #31 | `TemporalLineageEvidence` enforces ancestral event/effective/knowledge lower bounds and UNKNOWN propagation; merged as `2263d0e654609d8abff6dd86d1edcbe5b181ed95` |
| RQM-040 / AC-01 | PR #32 | Point-in-time discovery over immutable registry snapshots with explicit family/provider/scope/validity/knowledge boundaries; merged as `cf3f184fd46d3482f24f8ac2b0a4f7bacbe3b035` |
| Final provider/governance reconciliation | PR #33 | DD-60 decision packet and final pre-provider gate integrated into Sprint 1 baseline `4fb5807f985d06ef8673a28e689b815a08763940` |

## Status vocabulary

- `SATISFIED`: evidence directly matches the required behavior.
- `SATISFIED_FIXTURE_SCOPE`: semantics are demonstrated on the deterministic Sprint 1 fixture/runtime graph; it does not claim a qualified real provider session.
- `BLOCKED_SECURITY_SCAN`: implementation and bounded structural/runtime evidence exist, but the contract still requires the official Security Diff Scan evidence.
- `PENDING_PROVIDER_INTEGRATION`: implementation exists in PR #34 but is not yet in the integrated baseline.
- `PENDING_REAL_PROVIDER_EVIDENCE`: design/adapter exists, but no authenticated live market-data session has been executed.

## 41 RQMs

| RQM | Status | Current evidence / limit |
|---|---|---|
| RQM-001 | SATISFIED | Event, ingestion and knowledge time remain distinct and causally validated. |
| RQM-002 | SATISFIED | Critical timestamps require explicit UTC; ambiguous/naive time fails closed. |
| RQM-003 | SATISFIED | `UNKNOWN` is preserved; no optimistic synthesis. |
| RQM-004 | SATISFIED | Numeric zero and missingness remain distinct. |
| RQM-005 | SATISFIED_FIXTURE_SCOPE | Fixture/domain evidence distinguishes zero volume, missing value and source exhaustion. |
| RQM-006 | SATISFIED | Unknown ordering is not fabricated. |
| RQM-007 | SATISFIED | Finite canonical EventId deduplication is integrated and property-tested. |
| RQM-008 | SATISFIED | Versioned EventEnvelope metadata is validated. |
| RQM-009 | SATISFIED | Source sequence requires explicit sequence scope. |
| RQM-010 | SATISFIED_FIXTURE_SCOPE | Unknown fixture/envelope versions fail closed without fallback. |
| RQM-011 | SATISFIED | Exogenous observations receive no synthetic causal identifiers. |
| RQM-012 | SATISFIED_FIXTURE_SCOPE | Immutable run/input identity and provenance are integrated. |
| RQM-013 | SATISFIED | Mutable/abbreviated code references are rejected. |
| RQM-014 | SATISFIED_FIXTURE_SCOPE | Raw bytes are preserved before decode/admission and referenced by decisions. |
| RQM-015 | SATISFIED | Cross-process evidence demonstrates fresh RunId identity across independent process starts; restart relations do not rewrite prior identity. |
| RQM-016 | SATISFIED | Typed RunRelation continuity is represented explicitly. |
| RQM-017 | SATISFIED_FIXTURE_SCOPE | CaptureContext/RunManifest bind run, code revision, provider and canonical config hash. |
| RQM-018 | BLOCKED_SECURITY_SCAN | Boundary/config/possible-secret heuristics and runtime credential tripwires pass; official Security Diff Scan remains absent. |
| RQM-019 | SATISFIED | Lineage graph is acyclic and rejects identity/hash rewrites. |
| RQM-020 | SATISFIED | Family, concrete instrument and provider reference are separate typed identities. |
| RQM-021 | SATISFIED | Market-data observations terminate in passive evidence only; no execution authority exists. |
| RQM-022 | SATISFIED_FIXTURE_SCOPE | Heartbeat/staleness policies and conservative readiness degradation are integrated. |
| RQM-023 | SATISFIED_FIXTURE_SCOPE | Observer runtime emits explicit monotonic elapsed/transit latency evidence through the typed latency boundary. |
| RQM-024 | SATISFIED_FIXTURE_SCOPE | Provider capability fidelity/resolution/UNKNOWN semantics are explicit. PR #34 extends this to the selected provider pending integration. |
| RQM-025 | SATISFIED | Invalid/corrupt/oversize frames produce structured quarantine evidence preserving raw bytes. |
| RQM-026 | SATISFIED_FIXTURE_SCOPE | Lateness is explicit and never silently reorders arrival. |
| RQM-027 | SATISFIED | Finite FIFO/backpressure evidence proves no silent overwrite/drop in the bounded owner model. |
| RQM-028 | SATISFIED_FIXTURE_SCOPE | Provider contract is capability-based and fixture surface is read-only; PR #34 adds the selected real-provider boundary pending integration and real-session qualification. |
| RQM-029 | SATISFIED_FIXTURE_SCOPE | Evidence files are immutable per identity and conflicting overwrite is rejected. |
| RQM-030 | SATISFIED | EvidenceArchive and AuditJournal are separate technical roots/APIs. |
| RQM-031 | SATISFIED_FIXTURE_SCOPE | Corrections append new evidence instead of rewriting canonical records. |
| RQM-032 | SATISFIED | RuntimePhase, SafetyPosture and ReadinessStatus remain separate typed states. |
| RQM-033 | SATISFIED | Liveness cannot override stale/blocked readiness. |
| RQM-034 | SATISFIED_FIXTURE_SCOPE | Operational health transition is durably observable in EvidenceArchive and linked from AuditJournal. |
| RQM-035 | SATISFIED | Structural inventory, AST boundary and runtime NEG-CAP demonstrate no strategy/order/execution/economic authority. |
| RQM-036 | BLOCKED_SECURITY_SCAN | Current integrated tree has no execution SDK dependency or trading-credential consumption; official Security Diff Scan remains absent. PR #34 must be re-evaluated on exact final tree. |
| RQM-037 | SATISFIED | Nontrivial observed market data terminates in technical evidence/queue decisions only. |
| RQM-038 | SATISFIED | Candle interval/finalization/knowledge availability are distinct and future availability is rejected; first real lab is explicitly trades/realtime, not candles. |
| RQM-039 | SATISFIED | Derived technical artifacts cannot claim temporal availability earlier or more certain than their ancestors. |
| RQM-040 | SATISFIED_FIXTURE_SCOPE | Causal point-in-time discovery returns all admissible mappings without ranking, rollover or implicit contract selection; DD-68 requires this before each WIN capture. |
| RQM-041 | SATISFIED_FIXTURE_SCOPE | Integrated run/config/input/raw hashes and deterministic reprocessing provide capture traceability. |

### RQM summary

```text
SATISFIED_OR_FIXTURE_SCOPE = 39
BLOCKED_SECURITY_SCAN = 2  # RQM-018, RQM-036
PARTIAL = 0
TOTAL = 41
```

This is an evidence classification, not a formal Sprint 1 PASS.

## Positive capability view

| Capability | Class | Current state |
|---|---|---|
| AC-01 Instrument Discovery & Resolution | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE; real provider discovery pending controlled session |
| AC-02 Provider Symbol / Reference Mapping | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE; DD-68 fixes WIN resolution policy |
| AC-03 Provider Capability Discovery | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE; PR #34 adds selected-provider capability surface pending integration |
| AC-04 Read-Only Provider Authentication | REQUIRED_IF_TRIGGERED | PENDING_REAL_PROVIDER_EVIDENCE — DD-43 policy and adapter boundary exist; no real API-key session executed |
| AC-05 Read-Only Market-Data Subscription | REQUIRED_CORE | PENDING_PROVIDER_INTEGRATION / PENDING_REAL_PROVIDER_EVIDENCE — PR #34 implements read-only subscription boundary; no real session yet |
| AC-06 Historical Request | PERMITTED_OPTIONAL | NOT_TRIGGERED_CONDITIONAL |
| AC-07 Tick & Candle Observation | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE; DD-68 first real lab selects trades/realtime |
| AC-08 Heartbeat & Liveness | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE; real provider disconnect/restart evidence pending |
| AC-09 Observable Latency Measurement | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-10 Quality / Admission | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-11 Invalid Event Quarantine | REQUIRED_CORE | SATISFIED |
| AC-12 Capture Context & Provenance | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-13 Technical Evidence Persistence | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-14 Telemetry / Dedup / Backpressure | REQUIRED_CORE | SATISFIED |

## Decision-gate status

`DD-60` is resolved: human coordination selected **BTG Solutions Data Services**, materialized by ADR-0023 in PR #34. DD-43 is triggered with an external-secret / memory-only policy; no trading credential is authorized.

`DD-68` is resolved for the first Sprint 1 laboratory:

```text
INSTRUMENT_FAMILY = WIN
CONCRETE_CONTRACT = RESOLVE_POINT_IN_TIME
STREAM_TYPE = realtime
DATA_GRANULARITY = trades
INITIAL_CANDLES = NO
AUTO_FALLBACK = NO
AUTO_ROLLOVER = NO
```

The exact WIN contract must be discovered/confirmed before each real capture and fixed in the run/capture context before subscription.

## 11 Exit Criteria

| XC | Status | Evidence / blocker |
|---|---|---|
| XC-01 Required capabilities | PARTIAL | AC-05 adapter exists in PR #34 but is unmerged and no real provider session has been qualified. |
| XC-02 Decision gates | SATISFIED_CURRENT_BRANCH | DD-60 and DD-68 are explicitly resolved; DD-43 policy is defined. This does not replace implementation/evidence gates. |
| XC-03 All 41 RQMs | PARTIAL | 39 have direct/fixture evidence; RQM-018 and RQM-036 await official Security Diff Scan. |
| XC-04 HQI/QPI evidence | PARTIAL | Technical causal evidence is present; final provider/security evidence is not yet complete. |
| XC-05 NEG-CAP-01..10 | SATISFIED | Structural and runtime obligations are green on the integrated passive graph; PR #34 must pass exact-head final checks before integration. |
| XC-06 READ_ONLY_BY_CONSTRUCTION | SATISFIED_CURRENT_TREE | Current integrated inventory/boundary/runtime graph is passive; PR #34 is also designed read-only but must pass final exact-head evidence. |
| XC-07 STRUCTURAL_ESCALATION | SATISFIED_CURRENT_TREE | Execution cannot be activated by config, environment or credential swap in the integrated graph. |
| XC-08 Zero trading credentials / ledger mutation | PARTIAL | Policy and branch design are read-only; official security/credential scan and exact-final-tree evidence remain outstanding. |
| XC-09 Strict code / typing / lint | PARTIAL | Integrated baseline is green; current PR #34 runners are failing before steps start and therefore do not provide valid current-head CI evidence. |
| XC-10 RunManifest / CaptureContext | SATISFIED_FIXTURE_SCOPE | Deterministic runtime emits and validates manifest/context/config/code evidence; real WIN session context pending. |
| XC-11 No Sprint-2+ escape | SATISFIED_CURRENT_TREE | Paper/Risk/strategy/formal replay/execution remain outside the S1 runtime graph. |

## Remaining blockers before formal Sprint 1 PASS

```text
B1 = PR #34: obtain valid current-head CI/review and integrate selected-provider adapter
B2 = REAL_PROVIDER_SESSION: provision external read-only API key and execute controlled WIN trades/realtime discovery/subscription/capture
B3 = EXACT_FINAL_TREE_EVIDENCE: rerun RQM/NEG-CAP/CI after provider integration and real-session evidence
B4 = SECURITY_DIFF_SCAN: execute official scan for exact final Sprint 1 diff/tree, or apply only an explicitly authorized governance treatment
```

DD-60 and DD-68 are no longer decision blockers. None of the remaining blockers authorizes a real-money account, trading credential, order API, Paper engine, Risk engine or economic path.
