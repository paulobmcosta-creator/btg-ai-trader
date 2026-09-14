# Program Execution — BTG AI Trader

## Current remote checkpoint

```text
AUTHORITATIVE_STATE = GITHUB_REMOTE
REPOSITORY = paulobmcosta-creator/btg-ai-trader
SPRINT_BRANCH = sprint/1-market-observer
CURRENT_INTEGRATED_BASELINE = 4fb5807f985d06ef8673a28e689b815a08763940
ACTIVE_PROVIDER_PR = #34
ACTIVE_PROVIDER_BRANCH = s1/20-btg-dataservices-adapter
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

PR #34 implements the smallest read-only provider boundary. It remains draft and unmerged until current-head remote CI executes successfully. No API key is stored in GitHub; the adapter accepts an external runtime credential source only.

Automatic vendor reconnect is disabled fail-closed. Recovery after disconnect requires a new explicit/auditable session.

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
INITIAL_CANDLES = NO
```

Before every real capture, provider discovery must confirm the exact WIN contract that will be fixed for that run/capture context. If resolution is absent, ambiguous or invalid, capture does not start. No automatic rollover, ranking or silent contract substitution is allowed.

The first real laboratory consumes the real-time trade stream. Candle streams are outside this first capture profile and cannot silently replace the approved input.

See `docs/program/workstreams/S1-DD68-FIRST-LAB.md`.

## Current infrastructure blocker

Recent GitHub Actions attempts for PR #34 have been failing before any job step starts (`steps=null`, no usable job logs). This is recorded as an execution-infrastructure blocker, not converted to PASS and not bypassed by merging.

## Remaining sequence

```text
1. Restore successful current-head remote CI for PR #34.
2. Re-run provider-specific verification, full Python CI and pinned upstream verification.
3. Obtain/reconfirm independent review on the exact green head.
4. Merge PR #34 only after those checks pass.
5. Provision read-only BTG Data Services API key outside repository/chat.
6. Execute controlled real read-only discovery/capture using the DD-68 profile: WIN, exact point-in-time contract, trades/realtime.
7. Collect provider evidence for authentication, discovery, subscription, observation, heartbeat/disconnect, explicit restart and raw capture.
8. Update exact-final-tree RQM/XC evidence.
9. Execute official Security Diff Scan when its interface is available, or apply only an explicitly authorized governance treatment.
10. Re-adjudicate all 11 Sprint 1 exit criteria conjunctively.
```

No step above authorizes financial execution, trading credentials or real money.
