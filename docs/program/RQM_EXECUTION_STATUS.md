# Sprint 1 — RQM and Exit-Criteria Evidence Status

This is a current evidence snapshot, not a normative rewrite and not a Sprint 1 approval record. Immutable authority remains `docs/foundation/0F-E_sprint1_entry_contract.md`.

## Current transition state

```text
SPRINT_BRANCH = sprint/1-market-observer
INTEGRATED_IMPLEMENTATION_BASELINE = b763ad20b857c016fecd4ca004c6d0e191df1435
ACTIVE_PROVIDER_TRANSITION = s1/23-zero-cost-cedro-provider
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
ZERO_ADDITIONAL_COST = REQUIRED
DD_60 = REDECIDED_CEDRO_MARKET_DATA_FREE_TRIAL
ADR_0024 = ACCEPTED_ON_TRANSITION_BRANCH
BTG_ADAPTER = NON_CANONICAL_REFERENCE_IMPLEMENTATION
CEDRO_ADAPTER = NOT_IMPLEMENTED
DD_68_FIRST_LAB = RESOLVED_WIN_TRADES_REALTIME
REAL_PROVIDER_SESSION = NOT_EXECUTED
SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_ACCEPTANCE = NOT_GRANTED
REAL_MONEY_PATH = ABSENT
TRADING_CAPABILITY = ABSENT
```

## Provider-selection evidence

The provider decision changed because the project owner requires zero additional financial cost.

The frozen contract was **not** relaxed. Provider research established:

| Candidate | Zero cost | B3/BM&F futures | Streaming realtime | Trades | S1 qualification result |
|---|---:|---:|---:|---:|---|
| BTG Solutions Data Services | No for the required real service | Yes | Yes | Yes | Superseded for qualification due cost constraint |
| B3 public D-1/historical | Yes | Yes | No | Historical/EOD only | Research/replay source only |
| brapi WIN/WDO no-token endpoints | Yes | Yes | No | EOD/daily | Research/test source only |
| Cedro Market Data free trial | Yes during advertised 7-day trial | Yes | Yes | Yes | **Selected for real S1 qualification** |

The Cedro public documentation also states that its Market Data API cannot send orders; Trading is a separate API family. The S1 adapter must physically exclude the Trading family.

## RQM summary

Provider transition does not erase provider-agnostic/fixture evidence already established, but selected-provider claims must be requalified against Cedro.

```text
SATISFIED_OR_FIXTURE_SCOPE = 39
BLOCKED_SECURITY_SCAN = 2  # RQM-018, RQM-036
PARTIAL = 0
TOTAL = 41
```

Material caveats:

- RQM-017/022/024/028/041 retain fixture/provider-contract evidence, but Cedro-specific real evidence is pending.
- RQM-018 and RQM-036 remain blocked by the official Security Diff Scan.
- prior BTG real-provider implementation evidence is historical/reference evidence, not Cedro qualification evidence.

## Positive capability view during transition

| Capability | Current state |
|---|---|
| AC-01 Instrument Discovery & Resolution | SATISFIED_FIXTURE_SCOPE; Cedro real confirmation pending |
| AC-02 Provider Symbol / Reference Mapping | SATISFIED_FIXTURE_SCOPE; Cedro mapping pending |
| AC-03 Provider Capability Discovery | PROVIDER_TRANSITION_PENDING |
| AC-04 Read-Only Provider Authentication | PROVIDER_TRANSITION_PENDING — Cedro Market Data credentials only |
| AC-05 Read-Only Market-Data Subscription | PROVIDER_TRANSITION_PENDING — Cedro streaming adapter not yet integrated |
| AC-06 Historical Request | PERMITTED_OPTIONAL; B3/brapi may support research after qualification |
| AC-07 Tick & Candle Observation | SATISFIED_FIXTURE_SCOPE; real Cedro `trades/realtime` pending |
| AC-08 Heartbeat & Liveness | SATISFIED_FIXTURE_SCOPE; Cedro behavior pending |
| AC-09 Observable Latency Measurement | SATISFIED_FIXTURE_SCOPE |
| AC-10 Quality / Admission | SATISFIED_FIXTURE_SCOPE |
| AC-11 Invalid Event Quarantine | SATISFIED |
| AC-12 Capture Context & Provenance | SATISFIED_FIXTURE_SCOPE; real Cedro run pending |
| AC-13 Technical Evidence Persistence | SATISFIED_FIXTURE_SCOPE |
| AC-14 Telemetry / Dedup / Backpressure | SATISFIED |

## Credential / negative-capability boundary for Cedro

Allowed:

```text
Market Data /SignIn
Cedro market-data username/password from external secret storage
JSESSIONID in transient session memory only
market-data quote/discovery/streaming surfaces
```

Explicitly forbidden:

```text
API Trading
/services/negotiation/*
brokerServiceLogin
user-identifier for trading
broker account / financial account
send/edit/cancel order
financial/custody/guarantee APIs
```

Any Cedro adapter or runner that imports, references or consumes those forbidden surfaces fails the Sprint 1 gate.

## 11 Exit Criteria

| XC | Status | Evidence / blocker |
|---|---|---|
| XC-01 Required capabilities | PARTIAL | Observer core exists; selected Cedro provider adapter/session pending |
| XC-02 Decision gates | SATISFIED_DECISION_SCOPE | DD-60 redecided to Cedro free trial; DD-68 unchanged; DD-43 constrained to market-data credentials |
| XC-03 All 41 RQMs | PARTIAL | 39 direct/fixture; RQM-018 and RQM-036 await official Security Diff Scan |
| XC-04 HQI/QPI evidence | PARTIAL | Technical causal evidence present; Cedro real-provider/security evidence incomplete |
| XC-05 NEG-CAP-01..10 | SATISFIED_LAST_INTEGRATED_TREE | Must be re-run after Cedro adapter integration |
| XC-06 READ_ONLY_BY_CONSTRUCTION | SATISFIED_LAST_INTEGRATED_TREE | Cedro implementation must preserve this invariant |
| XC-07 STRUCTURAL_ESCALATION | SATISFIED_LAST_INTEGRATED_TREE | Cedro implementation must not expose Trading API by config/credential swap |
| XC-08 Zero trading credentials / ledger mutation | PARTIAL | No trading credential/ledger path; Cedro adapter + official scan still pending |
| XC-09 Strict code / typing / lint | SATISFIED_LAST_INTEGRATED_TREE | Must rerun on Cedro exact heads/final tree |
| XC-10 RunManifest / CaptureContext | SATISFIED_FIXTURE_SCOPE | Real Cedro session pending |
| XC-11 No Sprint-2+ escape | SATISFIED_CURRENT_SCOPE | No formal replay/Paper/Risk/strategy/execution added by provider transition |

## Remaining blockers before formal Sprint 1 PASS

```text
B1 = CEDRO_ADAPTER: implement/test narrow read-only Market Data adapter without starting trial
B2 = CEDRO_TRIAL_ACCESS: request/receive free 7-day Market Data credentials only after adapter is green
B3 = REAL_PROVIDER_SESSION: execute controlled WIN realtime-trades discovery/confirmation/subscription/capture
B4 = REAL_PROVIDER_EVIDENCE: adjudicate authentication, discovery, exact-symbol confirmation, trades, liveness and close evidence
B5 = EXACT_FINAL_TREE_EVIDENCE: rerun CI/RQM/NEG-CAP after final evidence/documentation tree
B6 = SECURITY_DIFF_SCAN: execute official scan for exact final Sprint 1 tree, or apply only a separately explicit governance treatment
```

None of these blockers authorizes broker/trading credentials, an order API, Paper/Risk engine, financial account access, ledger mutation or real money.
