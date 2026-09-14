# Program Execution — BTG AI Trader

## Current remote checkpoint

This is the current operational checkpoint. Historical execution detail remains available through Git
history and prior PRs; this living file intentionally records only the state needed to resume work safely.

```text
AUTHORITATIVE_STATE = GITHUB_REMOTE
REPOSITORY = paulobmcosta-creator/btg-ai-trader
SPRINT_BRANCH = sprint/1-market-observer
CURRENT_INTEGRATED_BASELINE = cf3f184fd46d3482f24f8ac2b0a4f7bacbe3b035
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
PR_5 = MERGED
ISSUE_1 = COMPLETED
ISSUE_6 = OPEN_NON_BLOCKING
PRE_CODE_RECONCILIATION = COMPLETE
SPRINT_1_LIFECYCLE = OPEN
S1_A_AUTHORIZED = YES
FIRST_FUNCTIONAL_CODE = AUTHORIZED_AND_IMPLEMENTED
SPRINT1_ACCEPTANCE = NOT_GRANTED
REAL_MONEY = NO
LIVE_TRADING = NO
TRADING_CREDENTIALS = NO
TRADING_CAPABILITY = ABSENT
```

## Preserved authorities

The following historical/canonical artifacts remain unchanged by this checkpoint:

- `docs/foundation/0F-B_deferred_decision_register.md` — blob `819397f0a3fe322ef199d053b2ccbe9a6fdb5747`;
- `docs/foundation/0F-E_sprint1_entry_contract.md` — blob `b04901dcc5612d3d418a6603a3a51a8e6e18ae08`;
- `docs/foundation/0F-F_foundation_final_gate.md` — blob `7204d409edd1239853ab2282e9a7a4411a068bba`;
- `docs/protocols/quantitative/TRACEABILITY.md` remains the canonical QPI authority;
- Issue #6 remains a non-blocking traceability erratum and does not rewrite 0F-F.

## Integrated Sprint 1 capability graph

The current baseline contains only the passive Market Observer graph:

```text
provider-agnostic source / fixture
    -> raw evidence
    -> admission + quarantine
    -> normalized observation envelope
    -> point-in-time instrument resolution/discovery
    -> dedup + finite FIFO + backpressure
    -> health / liveness / readiness
    -> monotonic latency evidence
    -> technical evidence persistence
    -> AuditJournal / provenance / lineage
```

It does **not** contain StrategyDecision, TradeIntent, RiskAuthorization, OrderIntent, OrderPlan,
ExecutionOrder, Paper execution, broker execution, ledger mutation or real-money authority.

## Integrated engineering evidence

| Area | Integrated evidence |
|---|---|
| Foundation / pre-code gate | PR #5 merge `dabce69d92054b77cad72809669d4340c211c328` |
| Domain / registry / provenance / health / storage / ingestion | integrated through the Sprint 1 branch history before Observer composition |
| NEG-CAP structural + runtime | integrated and green before composition/property campaign |
| Observer composition | integrated before the final RQM remediation sequence |
| Property + mutation campaign | generated properties plus bounded 10/10 mutant detection campaign |
| RQM-023 latency | PR #28 → `035113c5c6ab58237b304304c3c884b3625bbed2` |
| RQM-015 RunId process evidence | PR #29 → `138352088a6d8929663163d410cbc526584219cf` |
| RQM-034 transition audit | PR #30 → `3e424b5516cd1d1391489825b290f3a02143d917` |
| RQM-039 temporal inheritance | PR #31 → `2263d0e654609d8abff6dd86d1edcbe5b181ed95` |
| RQM-040 instrument discovery | PR #32 → `cf3f184fd46d3482f24f8ac2b0a4f7bacbe3b035` |

The PR #32 final head passed 491 tests plus Ruff, mypy, compile, dependency validation, Foundation
integrity, scoped NEG-CAP boundary, diff validation and pinned upstream engineering verification before
merge.

## Current Sprint 1 evidence state

See [`RQM_EXECUTION_STATUS.md`](RQM_EXECUTION_STATUS.md) for the detailed matrix.

```text
RQM_TOTAL = 41
RQM_SATISFIED_OR_FIXTURE_SCOPE = 39
RQM_PARTIAL = 0
RQM_BLOCKED_SECURITY_SCAN = 2  # RQM-018, RQM-036
NEG_CAP_01_TO_10 = SATISFIED
READ_ONLY_BY_CONSTRUCTION_CURRENT_TREE = SATISFIED
STRUCTURAL_ESCALATION_CURRENT_TREE = SATISFIED
```

The absence of `PARTIAL` RQMs does not grant Sprint 1 acceptance because required capability and
decision gates remain open.

## Open canonical gates

### G1 — DD-60 / AC-05 provider admission

0F-E makes `AC-05 Read-Only Market-Data Subscription` `REQUIRED_CORE` and marks `DD-60 Initial Market
Data Provider` mandatory for all implementations. Therefore:

```text
DD_60 = UNDECIDED
REAL_PROVIDER_ADAPTER = ABSENT
AC_05_REAL_SUBSCRIPTION = OPEN
```

A provider must be selected by explicit coordination decision and documented by ADR before its
concrete adapter is implemented. The existing fixture does not silently satisfy this gate.

If MetaTrader 5 is selected, DD-61 becomes active. The existing import-only MT5 spike proves package
installation/import compatibility only; it does not prove connection, market-data observation,
reconnect/liveness behavior or the eleven dual-use admissibility conditions.

### G2 — DD-68 first real laboratory instrument

`DD-68` must be explicitly selected before the first real capture session. Fixture symbols do not count
as that decision.

### G3 — official Security Diff Scan

The repository's structural boundary, config/possible-secret heuristics and runtime NEG-CAP tests are
green, but they are not relabeled as the official Security Diff Scan.

```text
SECURITY_DIFF_SCAN = NOT_EXECUTED
RQM_018 = BLOCKED_SECURITY_SCAN
RQM_036 = BLOCKED_SECURITY_SCAN
```

## Next execution sequence

```text
1. Prepare DD-60 provider decision packet.
2. Human coordination selects the initial provider.
3. Materialize DD-60 ADR before provider-dependent code.
4. Resolve DD-68 before the first real capture.
5. Implement the smallest strictly read-only provider adapter/subscription boundary.
6. Prove all applicable dual-use constraints and negative capabilities.
7. Run full remote CI and exact final-tree evidence suite.
8. Execute the official Security Diff Scan when its scan interface is available.
9. Reconcile the final Sprint 1 acceptance gate.
```

No step above authorizes real-money trading, trading credentials or financial execution.
