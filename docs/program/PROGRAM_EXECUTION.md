# Program Execution — BTG AI Trader

## Current remote checkpoint

```text
AUTHORITATIVE_STATE = GITHUB_REMOTE
REPOSITORY = paulobmcosta-creator/btg-ai-trader
SPRINT_BRANCH = sprint/1-market-observer
CURRENT_INTEGRATED_BASELINE = 4fb5807f985d06ef8673a28e689b815a08763940
ACTIVE_PROVIDER_PR = #34
ACTIVE_PROVIDER_BRANCH = s1/20-btg-dataservices-adapter
ACTIVE_CAPTURE_PR = #35
ACTIVE_CAPTURE_BRANCH = s1/21-btg-controlled-capture-harness
ACTIONS_BLOCKER_ISSUE = #36
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
SPRINT_1_LIFECYCLE = OPEN
S1_A_AUTHORIZED = YES
SPRINT1_ACCEPTANCE = NOT_GRANTED
REAL_MONEY = NO
LIVE_TRADING = NO
TRADING_CREDENTIALS = NO
TRADING_CAPABILITY = ABSENT
```

Historical execution detail remains available through Git history and prior PRs. This living file records only the state needed to resume safely.

## Preserved authorities

The historical/canonical Foundation artifacts remain unchanged:

- `docs/foundation/0F-B_deferred_decision_register.md`;
- `docs/foundation/0F-E_sprint1_entry_contract.md`;
- `docs/foundation/0F-F_foundation_final_gate.md`;
- `docs/protocols/quantitative/TRACEABILITY.md` remains the canonical QPI authority.

## Integrated Sprint 1 core

The integrated baseline already contains the passive Market Observer core: raw evidence, admission/quarantine, normalized observation envelope, point-in-time registry discovery, dedup, bounded FIFO/backpressure, health/liveness/readiness, latency evidence, provenance, technical persistence and AuditJournal/lineage.

It contains no StrategyDecision, TradeIntent, RiskAuthorization, OrderIntent, OrderPlan, ExecutionOrder, Paper execution, broker execution, ledger mutation or real-money authority.

## RQM / negative-capability state

```text
RQM_TOTAL = 41
RQM_SATISFIED_OR_FIXTURE_SCOPE = 39
RQM_PARTIAL = 0
RQM_BLOCKED_SECURITY_SCAN = 2  # RQM-018, RQM-036
NEG_CAP_01_TO_10 = SATISFIED
READ_ONLY_BY_CONSTRUCTION_CURRENT_TREE = SATISFIED
STRUCTURAL_ESCALATION_CURRENT_TREE = SATISFIED
SECURITY_DIFF_SCAN = NOT_EXECUTED
```

## Provider gate — DD-60 / DD-43 / AC-05

Human coordination approved:

```text
DD_60 = ACCEPTED
PROVIDER = BTG Solutions Data Services
ADR = ADR-0023
DD_43 = TRIGGERED
```

PR #34 implements the smallest read-only provider boundary. Current design requirements include:

```text
connect
-> provider discovery request
-> external point-in-time contract confirmation
-> subscribe_confirmed(exact_symbol)
-> raw observation
```

The adapter settings do not contain a preselected ticker. `subscribe_confirmed()` is impossible until the adapter has successfully issued `available_to_subscribe()`. Pre-subscription messages are control/discovery evidence, not instrument-labelled Market Data `RawFrame`s. Automatic vendor reconnect is disabled fail-closed. Intentional local close is distinguished from unexpected disconnect so a normal shutdown does not become a false provider failure.

PR #34 remains draft and unmerged until current-head remote CI actually executes successfully. No API key is stored in GitHub; the adapter accepts an external runtime credential source only.

## DD-68 — first laboratory

Human coordination fully resolved the first laboratory:

```text
DD_68 = RESOLVED
INSTRUMENT_FAMILY = WIN
CONCRETE_CONTRACT = RESOLVE_POINT_IN_TIME
AUTO_FALLBACK = FORBIDDEN
AUTO_ROLLOVER = FORBIDDEN
STREAM_TYPE = realtime
DATA_GRANULARITY = trades
DATA_SUBTYPE = derivatives
INITIAL_CANDLES = NO
```

Before every real capture, provider discovery must confirm the exact WIN contract that will be fixed for that run/capture context. If resolution is absent, ambiguous or invalid, capture does not start. No automatic rollover, ranking or silent contract substitution is allowed.

The first real laboratory consumes the real-time trade stream. Candle streams are outside this first capture profile and cannot silently replace the approved input.

See `docs/program/workstreams/S1-DD68-FIRST-LAB.md`.

## Controlled capture harness — PR #35

PR #35 is a stacked draft on PR #34 and prepares the first real read-only laboratory without executing it. Its effective delta is intentionally limited to four files: runbook, scripts policy, harness and offline tests.

The harness executes one causal read-only provider session with one RunId:

```text
connect with no preselected ticker
-> available_to_subscribe
-> persist raw discovery/control evidence
-> exact WIN confirmation
-> persist explicit confirmation evidence
-> subscribe_confirmed(exact_symbol)
-> observe realtime provider messages
-> require at least one trade for exact_symbol
-> unsubscribe
-> close
-> persist canonical summary
```

This same-session design removes a time-of-check/time-of-use gap that existed in an earlier draft using separate discovery/capture connections.

The harness:

- obtains the Data Services API key only from `BTG_DATASERVICES_API_KEY` in the authorized process environment;
- never receives the API key as a CLI/config argument and never persists or hashes its value;
- starts the vendor client with an empty instrument list;
- persists discovery/control payloads using the existing EvidenceArchive/AuditJournal model;
- requires the exact operator-supplied WIN contract to be present in provider discovery evidence before subscription;
- persists an explicit confirmation artifact before `subscribe_confirmed(exact_symbol)`;
- counts only JSON `trade` events whose `symbol` equals the confirmed contract as successful market observations;
- preserves post-subscription non-trade messages but does not count them as market-data success;
- fails closed if discovery does not confirm the candidate or if zero confirmed trade frames arrive;
- has offline fake-provider tests proving single-session causality and that a synthetic credential is absent from persisted artifacts;
- has not used any real API key or network session.

The S1 boundary inventory remains intentionally scoped to the importable runtime/configuration surface. The harness does not become canonical runtime merely by existing under `scripts/`. Ruff, mypy and compileall cover `scripts`, while dedicated harness tests cover its credential/evidence lifecycle. The official Security Diff Scan remains a separate mandatory final gate unless human governance explicitly changes that requirement.

PR #35 must not be integrated before #34. It is kept reanchored on the current #34 head while stacked. After #34 integrates into `sprint/1-market-observer`, #35 must be retargeted to that integrated baseline and its four-file effective delta reconfirmed before promotion.

## Current infrastructure blocker — Issue #36

GitHub Actions is currently failing before runner steps start on both #34 and #35:

```text
job.status = completed
job.conclusion = failure
job.steps = null / []
job.logs_url = null
check_run.output.annotations_count = 1
```

Representative affected runs are recorded in Issue #36. The current connector can observe the annotation count but cannot access the annotations endpoint, so no unverified root-cause label is assigned.

This state means:

```text
REMOTE_CI = NOT_EXECUTED_VALIDLY
PR_34_MERGE = BLOCKED
PR_35_MERGE = BLOCKED
```

It is not converted to PASS and is not bypassed by local-only evidence.

## Review state

```text
PR_34_EXACT_HEAD_STRUCTURAL_REVIEW = REQUIRED_AFTER_LAST_CHANGES
PR_34_INDEPENDENT_REVIEW = PENDING
PR_35_EXACT_HEAD_STRUCTURAL_REVIEW = REQUIRED
PR_35_INDEPENDENT_REVIEW = PENDING
```

Self/author structural review may document findings but does not satisfy the independent-review requirement.

## Remaining sequence

```text
1. Restore valid GitHub Actions runner execution (Issue #36).
2. Run Remote Python CI, BTG provider verification and pinned upstream verification on PR #34 exact HEAD.
3. Obtain independent review on that exact green HEAD.
4. Merge PR #34 only after all mandatory checks pass.
5. Retarget PR #35 to the integrated sprint baseline and reconfirm its effective four-file delta.
6. Run full exact-head CI and independent review for PR #35; integrate only if green.
7. Provision read-only BTG Data Services API key outside repository/chat.
8. Execute the controlled laboratory: WIN family, exact point-in-time contract, realtime trades.
9. Collect provider evidence for authentication, discovery, confirmation-before-subscription, observation and disconnect/close.
10. If restart is tested, create a new explicit run/session; never rely on vendor auto-reconnect.
11. Update exact-final-tree RQM/XC and NEG-CAP evidence.
12. Execute official Security Diff Scan when its supported interface is available, or apply only an explicitly authorized governance treatment.
13. Re-adjudicate all 11 Sprint 1 exit criteria conjunctively.
```

No step above authorizes financial execution, trading credentials or real money.
