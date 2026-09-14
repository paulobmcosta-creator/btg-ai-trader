# Sprint 1 — RQM and Exit-Criteria Evidence Status

This is a **current evidence snapshot**, not a normative rewrite and not a Sprint 1 approval record.
The immutable authority remains [`0F-E`](../foundation/0F-E_sprint1_entry_contract.md), blob
`b04901dcc5612d3d418a6603a3a51a8e6e18ae08`.

## Current integrated baseline

```text
SPRINT_BRANCH = sprint/1-market-observer
INTEGRATED_BASELINE = cf3f184fd46d3482f24f8ac2b0a4f7bacbe3b035
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
SPRINT_1_LIFECYCLE = OPEN
S1_A_AUTHORIZED = YES
OBSERVER_COMPOSITION = INTEGRATED
PROPERTY_MUTATION = INTEGRATED
NEG_CAP_STRUCTURAL = INTEGRATED
NEG_CAP_RUNTIME_01_TO_10 = INTEGRATED
SECURITY_DIFF_SCAN = NOT_EXECUTED
DD_60_INITIAL_REAL_PROVIDER = UNDECIDED
AC_05_REAL_SUBSCRIPTION = NOT_IMPLEMENTED
SPRINT1_ACCEPTANCE = NOT_GRANTED
REAL_MONEY_PATH = ABSENT
TRADING_CAPABILITY = ABSENT
```

The current baseline remains passive and provider-agnostic. It includes deterministic fixture observation,
causal instrument discovery/resolution, explicit latency evidence, cross-process RunId evidence,
persisted operational-transition evidence and derived temporal-inheritance enforcement. It does not
contain a real provider adapter, trading credential, Paper engine, Risk engine or financial execution path.

## Principal evidence added after the previous snapshot

| Requirement | Evidence | Integrated result |
|---|---|---|
| RQM-023 / AC-09 | PR #28 | Runtime latency boundary emits the Observer step together with monotonic elapsed/transit evidence; merged as `035113c5c6ab58237b304304c3c884b3625bbed2` |
| RQM-015 | PR #29 | Independent-process RunId uniqueness/restart evidence; merged as `138352088a6d8929663163d410cbc526584219cf` |
| RQM-034 | PR #30 | Real passive `FixtureObserver` transition persisted with before/after health state and AuditJournal reference; merged as `3e424b5516cd1d1391489825b290f3a02143d917` |
| RQM-039 / B-HQI-08 | PR #31 | `TemporalLineageEvidence` enforces ancestral event/effective/knowledge lower bounds and UNKNOWN propagation; merged as `2263d0e654609d8abff6dd86d1edcbe5b181ed95` |
| RQM-040 / AC-01 | PR #32 | Point-in-time discovery over immutable registry snapshots with explicit family/provider/scope/validity/knowledge boundaries; merged as `cf3f184fd46d3482f24f8ac2b0a4f7bacbe3b035` |

PR #32 final-head verification included 491 tests plus Ruff, mypy, compile, dependency validation,
Foundation integrity, diff validation, the scoped NEG-CAP boundary and pinned upstream engineering
verification, all green before merge.

## Status vocabulary

- `SATISFIED`: evidence directly matches the required behavior.
- `SATISFIED_FIXTURE_SCOPE`: the required semantics are demonstrated on the deterministic Sprint 1
  fixture/runtime graph; it does not claim a qualified real provider.
- `BLOCKED_SECURITY_SCAN`: implementation and bounded structural/runtime evidence exist, but the
  contract still requires the official Security Diff Scan evidence.
- `NOT_TRIGGERED_CONDITIONAL`: a conditional capability was not activated by the chosen path.

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
| RQM-024 | SATISFIED_FIXTURE_SCOPE | Provider capability fidelity/resolution/UNKNOWN semantics are explicit. |
| RQM-025 | SATISFIED | Invalid/corrupt/oversize frames produce structured quarantine evidence preserving raw bytes. |
| RQM-026 | SATISFIED_FIXTURE_SCOPE | Lateness is explicit and never silently reorders arrival. |
| RQM-027 | SATISFIED | Finite FIFO/backpressure evidence proves no silent overwrite/drop in the bounded owner model. |
| RQM-028 | SATISFIED_FIXTURE_SCOPE | Provider contract is capability-based and fixture surface is read-only; real-provider qualification remains a separate gate. |
| RQM-029 | SATISFIED_FIXTURE_SCOPE | Evidence files are immutable per identity and conflicting overwrite is rejected. |
| RQM-030 | SATISFIED | EvidenceArchive and AuditJournal are separate technical roots/APIs. |
| RQM-031 | SATISFIED_FIXTURE_SCOPE | Corrections append new evidence instead of rewriting canonical records. |
| RQM-032 | SATISFIED | RuntimePhase, SafetyPosture and ReadinessStatus remain separate typed states. |
| RQM-033 | SATISFIED | Liveness cannot override stale/blocked readiness. |
| RQM-034 | SATISFIED_FIXTURE_SCOPE | Operational health transition is durably observable in EvidenceArchive and linked from AuditJournal. |
| RQM-035 | SATISFIED | Structural inventory, AST boundary and runtime NEG-CAP demonstrate no strategy/order/execution/economic authority. |
| RQM-036 | BLOCKED_SECURITY_SCAN | Current tree has no execution SDK dependency or trading-credential consumption; official Security Diff Scan remains absent. |
| RQM-037 | SATISFIED | Nontrivial observed market data terminates in technical evidence/queue decisions only. |
| RQM-038 | SATISFIED | Candle interval/finalization/knowledge availability are distinct and future availability is rejected. |
| RQM-039 | SATISFIED | Derived technical artifacts cannot claim temporal availability earlier or more certain than their ancestors. |
| RQM-040 | SATISFIED_FIXTURE_SCOPE | Causal point-in-time discovery returns all admissible mappings without ranking, rollover or implicit contract selection. |
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
| AC-01 Instrument Discovery & Resolution | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-02 Provider Symbol / Reference Mapping | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-03 Provider Capability Discovery | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-04 Read-Only Provider Authentication | REQUIRED_IF_TRIGGERED | NOT_TRIGGERED_CONDITIONAL — no real provider selected |
| AC-05 Read-Only Market-Data Subscription | REQUIRED_CORE | **OPEN** — fixture source does not substitute for qualification of the mandatory initial real provider |
| AC-06 Historical Request | PERMITTED_OPTIONAL | NOT_TRIGGERED_CONDITIONAL |
| AC-07 Tick & Candle Observation | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-08 Heartbeat & Liveness | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-09 Observable Latency Measurement | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-10 Quality / Admission | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-11 Invalid Event Quarantine | REQUIRED_CORE | SATISFIED |
| AC-12 Capture Context & Provenance | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-13 Technical Evidence Persistence | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-14 Telemetry / Dedup / Backpressure | REQUIRED_CORE | SATISFIED |

## Decision-gate status

`DD-60` remains `UNDECIDED`. Under 0F-E it is `Mandatory For All = YES`, requires an ADR and must be
resolved before implementation of the concrete real-provider adapter. The deterministic fixture and
provider-agnostic contracts deliberately do not select DD-60.

If DD-60 selects MetaTrader 5, DD-61 is triggered and the existing import-only spike is insufficient:
connection, observation calls, reconnect/liveness behavior and all eleven dual-use admissibility
conditions must be demonstrated without introducing trading authority.

`DD-68` (first laboratory instrument) must also be resolved before the first real capture session. It
must not be inferred from fixture symbols or historical project preferences.

## 11 Exit Criteria

| XC | Status | Evidence / blocker |
|---|---|---|
| XC-01 Required capabilities | PARTIAL | AC-05 real read-only subscription remains open pending DD-60. |
| XC-02 Decision gates | PARTIAL | DD-60 remains mandatory and undecided; DD-68 follows before first real capture. |
| XC-03 All 41 RQMs | PARTIAL | 39 have direct/fixture evidence; RQM-018 and RQM-036 await official Security Diff Scan. |
| XC-04 HQI/QPI evidence | PARTIAL | Technical causal evidence is present; final security/provider admission evidence is not yet complete. |
| XC-05 NEG-CAP-01..10 | SATISFIED | Structural and runtime obligations are green on the integrated passive graph. |
| XC-06 READ_ONLY_BY_CONSTRUCTION | SATISFIED_CURRENT_TREE | Current inventory/boundary/runtime graph is passive; this is not a substitute for the official scan. |
| XC-07 STRUCTURAL_ESCALATION | SATISFIED_CURRENT_TREE | Execution cannot be activated by config, environment or credential swap in the current graph. |
| XC-08 Zero trading credentials / ledger mutation | PARTIAL | Current-tree evidence is green; official security/credential scan evidence remains outstanding. |
| XC-09 Strict code / typing / lint | SATISFIED | Latest integrated functional PRs passed remote tests, Ruff, mypy, compile, deps and diff checks. |
| XC-10 RunManifest / CaptureContext | SATISFIED_FIXTURE_SCOPE | Deterministic runtime emits and validates manifest/context/config/code evidence. |
| XC-11 No Sprint-2+ escape | SATISFIED_CURRENT_TREE | Paper/Risk/strategy/formal replay/execution remain outside the S1 runtime graph. |

## Remaining blockers before formal Sprint 1 PASS

```text
B1 = DD-60: select and document the initial real Market Data provider by ADR
B2 = AC-05: implement and qualify the selected provider's strictly read-only subscription/streaming adapter
B3 = DD-68: declare the first real laboratory instrument before the first capture session
B4 = official Security Diff Scan for the exact final Sprint 1 diff / tree
```

B1-B3 are one provider-admission sequence. B4 is independent security evidence. None of these items
authorizes a real-money account, trading credential, order API, Paper engine, Risk engine or economic path.
