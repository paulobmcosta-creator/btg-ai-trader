# Sprint 1 — RQM and Exit-Criteria Evidence Status

This is a **current evidence snapshot**, not a normative rewrite and not a Sprint 1 approval record. The immutable authority remains [`0F-E`](../foundation/0F-E_sprint1_entry_contract.md), blob `b04901dcc5612d3d418a6603a3a51a8e6e18ae08`.

## Current integrated baseline

```text
SPRINT_BRANCH = sprint/1-market-observer
INTEGRATED_BASELINE = 0c59a19956f43651778441e48d30299e4df72c30
PR_34_PROVIDER = MERGED @ d1d865d32f88b7420cfd0555823240d793131c19
PR_35_CAPTURE_HARNESS = MERGED @ 0c59a19956f43651778441e48d30299e4df72c30
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
SPRINT_1_LIFECYCLE = OPEN
S1_A_AUTHORIZED = YES
OBSERVER_COMPOSITION = INTEGRATED
PROPERTY_MUTATION = INTEGRATED
NEG_CAP_STRUCTURAL = INTEGRATED
NEG_CAP_RUNTIME_01_TO_10 = INTEGRATED
DD_60_INITIAL_REAL_PROVIDER = ACCEPTED_BTG_SOLUTIONS_DATA_SERVICES
DD_68_FIRST_LAB = RESOLVED_WIN_TRADES_REALTIME
AC_05_PROVIDER_ADAPTER = INTEGRATED_READ_ONLY
CONTROLLED_CAPTURE_HARNESS = INTEGRATED_READ_ONLY
REAL_PROVIDER_SESSION = NOT_EXECUTED
SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_ACCEPTANCE = NOT_GRANTED
REAL_MONEY_PATH = ABSENT
TRADING_CAPABILITY = ABSENT
```

The integrated baseline is no longer provider-agnostic: it now contains the selected BTG Data Services read-only boundary and the controlled first-lab harness. Real provider qualification is still pending because no authenticated market-data session has been executed.

## Principal integrated evidence

| Requirement | Evidence | Integrated result |
|---|---|---|
| RQM-023 / AC-09 | PR #28 | Runtime latency boundary emits Observer step plus monotonic elapsed/transit evidence; merged as `035113c5c6ab58237b304304c3c884b3625bbed2` |
| RQM-015 | PR #29 | Cross-process RunId uniqueness/restart evidence; merged as `138352088a6d8929663163d410cbc526584219cf` |
| RQM-034 | PR #30 | Passive Observer transition persisted with before/after health and AuditJournal reference; merged as `3e424b5516cd1d1391489825b290f3a02143d917` |
| RQM-039 / B-HQI-08 | PR #31 | Temporal lineage lower bounds and UNKNOWN propagation; merged as `2263d0e654609d8abff6dd86d1edcbe5b181ed95` |
| RQM-040 / AC-01 | PR #32 | Point-in-time discovery over immutable registry snapshots; merged as `cf3f184fd46d3482f24f8ac2b0a4f7bacbe3b035` |
| Provider/governance reconciliation | PR #33 | Pre-provider gate baseline `4fb5807f985d06ef8673a28e689b815a08763940` |
| Selected real-provider boundary | PR #34 | BTG Data Services read-only adapter integrated as `d1d865d32f88b7420cfd0555823240d793131c19` after exact-head CI/provider/upstream PASS |
| Controlled first-lab harness | PR #35 | WIN/realtime/trades harness integrated as `0c59a19956f43651778441e48d30299e4df72c30` after discovery fail-closed remediation and exact-head CI/upstream PASS |

## Status vocabulary

- `SATISFIED`: evidence directly matches the required behavior.
- `SATISFIED_FIXTURE_SCOPE`: semantics are demonstrated on deterministic Sprint 1 fixture/runtime evidence; it does not claim a qualified real provider session.
- `BLOCKED_SECURITY_SCAN`: implementation and bounded structural/runtime evidence exist, but the contract still requires official Security Diff Scan evidence.
- `PENDING_REAL_PROVIDER_EVIDENCE`: implementation is integrated but no authenticated real market-data session has been qualified.

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
| RQM-015 | SATISFIED | Fresh RunId identity is demonstrated across independent process starts; restart relations do not rewrite prior identity. |
| RQM-016 | SATISFIED | Typed RunRelation continuity is represented explicitly. |
| RQM-017 | SATISFIED_FIXTURE_SCOPE | CaptureContext/RunManifest bind run, code revision, provider and canonical config hash. Real-session use remains pending. |
| RQM-018 | BLOCKED_SECURITY_SCAN | Boundary/config/possible-secret heuristics and runtime credential tripwires pass; official Security Diff Scan remains absent. |
| RQM-019 | SATISFIED | Lineage graph is acyclic and rejects identity/hash rewrites. |
| RQM-020 | SATISFIED | Family, concrete instrument and provider reference are separate typed identities. |
| RQM-021 | SATISFIED | Market-data observations terminate in passive evidence only; no execution authority exists. |
| RQM-022 | SATISFIED_FIXTURE_SCOPE | Heartbeat/staleness policies and conservative readiness degradation are integrated; real provider behavior pending. |
| RQM-023 | SATISFIED_FIXTURE_SCOPE | Runtime emits explicit monotonic elapsed/transit latency evidence. |
| RQM-024 | SATISFIED_FIXTURE_SCOPE | Provider capability semantics are explicit and the BTG adapter declares its selected read-only observation capability; real-session fidelity evidence remains pending. |
| RQM-025 | SATISFIED | Invalid/corrupt/oversize frames produce structured quarantine evidence preserving raw bytes. |
| RQM-026 | SATISFIED_FIXTURE_SCOPE | Lateness is explicit and never silently reorders arrival. |
| RQM-027 | SATISFIED | Finite FIFO/backpressure evidence proves no silent overwrite/drop in the bounded owner model. |
| RQM-028 | SATISFIED_FIXTURE_SCOPE | Capability-based provider contract and selected BTG read-only boundary are integrated; real-session qualification remains pending. |
| RQM-029 | SATISFIED_FIXTURE_SCOPE | Evidence files are immutable per identity and conflicting overwrite is rejected. |
| RQM-030 | SATISFIED | EvidenceArchive and AuditJournal are separate technical roots/APIs. |
| RQM-031 | SATISFIED_FIXTURE_SCOPE | Corrections append new evidence instead of rewriting canonical records. |
| RQM-032 | SATISFIED | RuntimePhase, SafetyPosture and ReadinessStatus remain separate typed states. |
| RQM-033 | SATISFIED | Liveness cannot override stale/blocked readiness. |
| RQM-034 | SATISFIED_FIXTURE_SCOPE | Operational health transition is durably observable in EvidenceArchive and linked from AuditJournal. |
| RQM-035 | SATISFIED | Structural inventory, AST boundary and runtime NEG-CAP demonstrate no strategy/order/execution/economic authority. |
| RQM-036 | BLOCKED_SECURITY_SCAN | Integrated tree has no order/account/execution SDK path or trading-credential consumption; official Security Diff Scan remains absent. |
| RQM-037 | SATISFIED | Nontrivial observed market data terminates in technical evidence/queue decisions only. |
| RQM-038 | SATISFIED | Candle interval/finalization/knowledge availability are distinct; first real lab is explicitly `trades/realtime`, not candles. |
| RQM-039 | SATISFIED | Derived technical artifacts cannot claim temporal availability earlier or more certain than ancestors. |
| RQM-040 | SATISFIED_FIXTURE_SCOPE | Causal point-in-time discovery returns admissible mappings without ranking/rollover; the integrated BTG harness additionally fails closed on ambiguous discovery shapes. |
| RQM-041 | SATISFIED_FIXTURE_SCOPE | Run/config/input/raw hashes and deterministic reprocessing provide capture traceability; real provider evidence remains pending. |

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
| AC-01 Instrument Discovery & Resolution | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE; controlled real provider discovery pending |
| AC-02 Provider Symbol / Reference Mapping | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE; DD-68 fixes WIN point-in-time policy |
| AC-03 Provider Capability Discovery | REQUIRED_CORE | IMPLEMENTED_INTEGRATED; real provider evidence pending |
| AC-04 Read-Only Provider Authentication | REQUIRED_IF_TRIGGERED | PENDING_REAL_PROVIDER_EVIDENCE — DD-43 policy and integrated boundary exist; no real API-key session executed |
| AC-05 Read-Only Market-Data Subscription | REQUIRED_CORE | IMPLEMENTED_INTEGRATED / PENDING_REAL_PROVIDER_EVIDENCE |
| AC-06 Historical Request | PERMITTED_OPTIONAL | NOT_TRIGGERED_CONDITIONAL |
| AC-07 Tick & Candle Observation | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE; DD-68 first real lab selects `trades/realtime` |
| AC-08 Heartbeat & Liveness | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE; real provider disconnect/restart evidence pending |
| AC-09 Observable Latency Measurement | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-10 Quality / Admission | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE |
| AC-11 Invalid Event Quarantine | REQUIRED_CORE | SATISFIED |
| AC-12 Capture Context & Provenance | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE; real run pending |
| AC-13 Technical Evidence Persistence | REQUIRED_CORE | SATISFIED_FIXTURE_SCOPE; integrated harness uses canonical store |
| AC-14 Telemetry / Dedup / Backpressure | REQUIRED_CORE | SATISFIED |

## Decision-gate status

DD-60 is resolved and integrated: **BTG Solutions Data Services**, materialized by ADR-0023. DD-43 is triggered with an external-secret/read-only policy; no trading credential is authorized.

DD-68 is fully resolved:

```text
INSTRUMENT_FAMILY = WIN
CONCRETE_CONTRACT = RESOLVE_AND_CONFIRM_POINT_IN_TIME
STREAM_TYPE = realtime
DATA_GRANULARITY = trades
INITIAL_CANDLES = NO
AUTO_FALLBACK = NO
AUTO_ROLLOVER = NO
```

The exact WIN candidate must be explicitly chosen for the controlled session, confirmed by provider discovery and fixed before subscription. The integrated harness never invents a replacement contract.

## 11 Exit Criteria

| XC | Status | Evidence / blocker |
|---|---|---|
| XC-01 Required capabilities | PARTIAL | Provider adapter and capture harness are integrated; real authenticated provider evidence is still absent. |
| XC-02 Decision gates | SATISFIED | DD-60/DD-68 resolved; DD-43 policy defined and integrated. |
| XC-03 All 41 RQMs | PARTIAL | 39 have direct/fixture evidence; RQM-018 and RQM-036 await official Security Diff Scan. |
| XC-04 HQI/QPI evidence | PARTIAL | Technical causal evidence is present; final real-provider/security evidence is incomplete. |
| XC-05 NEG-CAP-01..10 | SATISFIED | Structural/runtime obligations remain green through the integrated provider/harness increments. |
| XC-06 READ_ONLY_BY_CONSTRUCTION | SATISFIED_CURRENT_TREE | Integrated provider boundary and harness expose observation only; no financial capability exists. |
| XC-07 STRUCTURAL_ESCALATION | SATISFIED_CURRENT_TREE | Execution cannot be activated by config, environment or credential swap. |
| XC-08 Zero trading credentials / ledger mutation | PARTIAL | No trading credential or ledger path exists; official Security Diff Scan and final exact-tree evidence remain outstanding. |
| XC-09 Strict code / typing / lint | SATISFIED_INTEGRATION_EVIDENCE | PR #34 and #35 exact heads passed remote tests/lint/mypy/compile/dependency/Foundation/boundary checks before merge. Final gate rerun still required after final evidence tree is fixed. |
| XC-10 RunManifest / CaptureContext | SATISFIED_FIXTURE_SCOPE | Integrated harness uses canonical run/context/config/code evidence; real WIN session pending. |
| XC-11 No Sprint-2+ escape | SATISFIED_CURRENT_TREE | Paper/Risk/strategy/formal replay/execution remain outside the Sprint 1 runtime graph. |

## Remaining blockers before formal Sprint 1 PASS

```text
B1 = REAL_PROVIDER_SESSION: provision external read-only API key and execute controlled WIN trades/realtime discovery/confirmation/subscription/capture
B2 = REAL_PROVIDER_EVIDENCE: adjudicate authentication, raw discovery, exact-symbol confirmation, trade observation and disconnect/close/restart evidence
B3 = EXACT_FINAL_TREE_EVIDENCE: rerun CI/RQM/NEG-CAP after the final evidence/documentation tree is fixed
B4 = SECURITY_DIFF_SCAN: execute official scan for the exact final Sprint 1 diff/tree, or apply only a separately explicit governance treatment
```

DD-60/DD-68, provider integration, capture-harness integration and runner allocation are no longer blockers. None of the remaining blockers authorizes a real-money account, trading credential, order API, Paper engine, Risk engine or economic path.
