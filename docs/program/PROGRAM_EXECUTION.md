# Program Execution — BTG AI Trader

## Current remote checkpoint

```text
AUTHORITATIVE_STATE = GITHUB_REMOTE
REPOSITORY = paulobmcosta-creator/btg-ai-trader
SPRINT_BRANCH = sprint/1-market-observer
CURRENT_INTEGRATED_BASELINE = 0c59a19956f43651778441e48d30299e4df72c30
PR_34_PROVIDER = MERGED @ d1d865d32f88b7420cfd0555823240d793131c19
PR_35_CAPTURE_HARNESS = MERGED @ 0c59a19956f43651778441e48d30299e4df72c30
ACTIONS_BLOCKER_ISSUE_36 = RESOLVED_CLOSED
SPECULATIVE_S2_PR = #37 ISOLATED
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
SPRINT_1_LIFECYCLE = OPEN
S1_A_AUTHORIZED = YES
SPRINT1_ACCEPTANCE = NOT_GRANTED
REAL_PROVIDER_SESSION = NOT_EXECUTED
SECURITY_DIFF_SCAN = NOT_EXECUTED
REAL_MONEY = NO
LIVE_TRADING = NO
TRADING_CREDENTIALS = NO
TRADING_CAPABILITY = ABSENT
```

Historical execution detail remains in Git history and prior PRs. This living file records only the state required to resume safely.

## Preserved authorities

The historical/canonical Foundation artifacts remain unchanged:

- `docs/foundation/0F-B_deferred_decision_register.md`;
- `docs/foundation/0F-E_sprint1_entry_contract.md`;
- `docs/foundation/0F-F_foundation_final_gate.md`;
- `docs/protocols/quantitative/TRACEABILITY.md` remains the canonical QPI authority.

The frozen 0F-E Replay Boundary remains authoritative: Sprint 1 preserves replay inputs/evidence but does not contain formal replay; Sprint 2 owns formal causal market-data replay; Sprint 3 owns deterministic economic backtesting.

## Integrated Sprint 1 graph

The current Sprint 1 baseline contains the passive Market Observer core plus the selected read-only BTG Data Services boundary and the controlled first-lab capture harness.

```text
BTG Data Services read-only session
    -> discovery/control evidence
    -> exact point-in-time WIN confirmation
    -> subscribe_confirmed(exact_symbol)
    -> raw realtime trade observation
    -> admission / quarantine
    -> normalized passive observation
    -> bounded queue / dedup / health / latency
    -> EvidenceArchive / AuditJournal / provenance / lineage
```

It contains no StrategyDecision operational path, TradeIntent operational path, RiskAuthorization Engine, OrderIntent, OrderPlan, ExecutionOrder, Paper execution, broker execution, ledger mutation or real-money authority.

## RQM / negative-capability state

```text
RQM_TOTAL = 41
RQM_SATISFIED_OR_FIXTURE_SCOPE = 39
RQM_PARTIAL = 0
RQM_BLOCKED_SECURITY_SCAN = 2  # RQM-018, RQM-036
NEG_CAP_01_TO_10 = SATISFIED
READ_ONLY_BY_CONSTRUCTION = SATISFIED_CURRENT_INTEGRATED_TREE
STRUCTURAL_ESCALATION = SATISFIED_CURRENT_INTEGRATED_TREE
SECURITY_DIFF_SCAN = NOT_EXECUTED
```

The 39/2 classification remains an evidence classification, not a formal Sprint 1 PASS.

## Provider decision and implementation

Human coordination approved DD-60 and fully resolved DD-68:

```text
DD_60 = ACCEPTED
PROVIDER = BTG Solutions Data Services
ADR = ADR-0023
DD_43 = TRIGGERED_EXTERNAL_READ_ONLY_SECRET
DD_68 = RESOLVED
INSTRUMENT_FAMILY = WIN
CONCRETE_CONTRACT = RESOLVE_AND_CONFIRM_POINT_IN_TIME
AUTO_FALLBACK = FORBIDDEN
AUTO_ROLLOVER = FORBIDDEN
STREAM_TYPE = realtime
DATA_GRANULARITY = trades
DATA_SUBTYPE = derivatives
INITIAL_CANDLES = NO
```

PR #34 is integrated as `d1d865d32f88b7420cfd0555823240d793131c19`. Its final exact head passed Remote Python CI, BTG provider verification and pinned upstream engineering verification before merge. The adapter is strictly read-only, requires discovery before `subscribe_confirmed()`, separates pre-subscription control evidence from instrument-labelled market data, obtains credentials only through an injected runtime source, and disables vendor automatic reconnect fail-closed.

The API key remains external to the repository and must never be pasted into chat, committed, persisted, hashed into run configuration or emitted to logs.

## Controlled capture harness

PR #35 is integrated as `0c59a19956f43651778441e48d30299e4df72c30`.

The harness implements one causal read-only session / one RunId:

```text
connect with no preselected ticker
-> available_to_subscribe
-> persist discovery/control evidence
-> exact WIN confirmation
-> persist explicit confirmation evidence
-> subscribe_confirmed(exact_symbol)
-> observe realtime provider messages
-> require at least one trade for exact_symbol
-> unsubscribe
-> close
-> persist canonical summary
```

During adversarial review, an earlier discovery helper was found to accept a ticker appearing in an arbitrary nested string list. That could have converted an echo/error structure into false availability. The integrated version is fail-closed: only bounded recognized discovery shapes can authorize subscription; mixed, echoed, malformed and error-bearing payloads remain evidence only. Dedicated regression tests cover this case.

The harness also:

- reads `BTG_DATASERVICES_API_KEY` only from the authorized process environment;
- never accepts the key as a CLI/config argument;
- uses the existing EvidenceArchive/AuditJournal storage model;
- fixes the candidate symbol only after provider discovery evidence;
- counts only exact-symbol JSON `trade` events as successful market observations;
- bounds discovery and capture duration;
- rejects non-WIN candidates, missing confirmation and zero-trade captures;
- has not executed any real API-key/network session yet.

## Review adjudication

For PRs #34 and #35, the project owner explicitly instructed the same coordinating agent to perform adversarial review and proceed. The resulting reviews are **not represented as independent reviews**. The owner authorization replaces the project-local separated-reviewer rule for those integrations only; it does not waive Foundation constraints, CI, NEG-CAP, real-provider evidence or the official Security Diff Scan.

The review of #35 produced a material finding and remediation before merge, demonstrating that the review was not treated as a ceremonial approval.

## GitHub Actions infrastructure

Issue #36 is resolved and closed. After repository visibility changed to public, GitHub-hosted runners allocated normally and current workflows produced real steps/logs. The former `runner_id=0 / steps=[]` condition is no longer an active blocker.

## Speculative Sprint 2

PR #37 remains isolated future-sprint work and MUST NOT be retargeted or merged into Sprint 1. Formal causal replay remains owned by Sprint 2 under the frozen 0F-E boundary.

## Remaining Sprint 1 sequence

```text
1. Provision a BTG Data Services read-only API key through an authorized external runtime/secret mechanism; never through chat or versioned files.
2. Select an explicit concrete WIN candidate for the controlled session; no automatic ranking, fallback or rollover.
3. Execute the integrated controlled read-only laboratory on the reviewed Sprint 1 code revision.
4. Preserve authentication/discovery/confirmation/subscription/raw-trade/close evidence with one RunId.
5. If restart behavior is tested, create a new explicit auditable session; never rely on vendor automatic reconnect.
6. Reconcile real-provider evidence into RQM/XC status without overstating fixture evidence.
7. Re-run exact-final-tree CI and NEG-CAP evidence after any evidence/documentation commit that changes the final tree.
8. Execute the official Security Diff Scan for the exact final Sprint 1 diff/tree, or use only a separately explicit governance waiver if one is authorized.
9. Adjudicate all 11 Sprint 1 exit criteria conjunctively.
10. Promote to Sprint 2 only if Sprint 1 receives formal PASS.
```

No step above authorizes financial execution, broker/trading credentials, order APIs, Paper execution, Risk authorization or real money.
