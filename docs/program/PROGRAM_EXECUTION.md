# Program Execution — BTG AI Trader

## Current remote checkpoint

```text
AUTHORITATIVE_STATE = GITHUB_REMOTE
REPOSITORY = paulobmcosta-creator/btg-ai-trader
SPRINT_BRANCH = sprint/1-market-observer
INTEGRATED_IMPLEMENTATION_BASELINE = 5a9fa177b609e56e06e7835b291beac821c8bbd6
PR_34_PROVIDER = MERGED @ d1d865d32f88b7420cfd0555823240d793131c19
PR_35_CAPTURE_HARNESS = MERGED @ 0c59a19956f43651778441e48d30299e4df72c30
PR_40_SECURE_LAB_RUNNER = MERGED @ 5a9fa177b609e56e06e7835b291beac821c8bbd6
ACTIONS_BLOCKER_ISSUE_36 = RESOLVED_CLOSED
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
SPRINT_1_LIFECYCLE = OPEN
S1_A_AUTHORIZED = YES
SPRINT1_ACCEPTANCE = NOT_GRANTED
REAL_PROVIDER_SESSION = NOT_EXECUTED
SECURITY_DIFF_SCAN = NOT_EXECUTED
BTG_LAB_ENVIRONMENT = EXTERNAL_CONFIGURATION_NOT_VERIFIED
REAL_MONEY = NO
LIVE_TRADING = NO
TRADING_CREDENTIALS = NO
TRADING_CAPABILITY = ABSENT
```

Historical execution detail remains in Git history and prior PRs. This living file records only the state required to resume safely.

## Preserved authorities

The frozen Foundation artifacts remain unchanged: `0F-B`, `0F-E`, `0F-F`, and quantitative `TRACEABILITY.md`. The 0F-E replay boundary remains authoritative: Sprint 1 is passive observation/evidence; Sprint 2 owns formal causal replay; Sprint 3 owns deterministic economic backtesting.

## Integrated Sprint 1 graph

The integrated branch now contains the passive Market Observer core, the selected BTG Data Services read-only provider boundary, the controlled first-lab capture harness, and a protected secure runner for the first real laboratory.

```text
BTG Data Services read-only session
-> discovery/control evidence
-> exact point-in-time WIN confirmation
-> subscribe_confirmed(exact_symbol)
-> realtime trades observation
-> passive admission / queue / health / latency
-> EvidenceArchive / AuditJournal / provenance / lineage
```

No StrategyDecision operational path, TradeIntent operational path, RiskAuthorization Engine, OrderIntent, OrderPlan, ExecutionOrder, Paper execution, broker execution, ledger mutation or real-money authority exists.

## Provider and laboratory policy

```text
DD_60 = ACCEPTED
PROVIDER = BTG Solutions Data Services
ADR = ADR-0023
DD_43 = TRIGGERED_EXTERNAL_READ_ONLY_SECRET
DD_68 = RESOLVED
INSTRUMENT_FAMILY = WIN
CONCRETE_CONTRACT = EXPLICIT_CANDIDATE_PLUS_PROVIDER_CONFIRMATION_POINT_IN_TIME
STREAM_TYPE = realtime
DATA_TYPE = trades
DATA_SUBTYPE = derivatives
AUTO_FALLBACK = FORBIDDEN
AUTO_ROLLOVER = FORBIDDEN
VENDOR_AUTO_RECONNECT = FORBIDDEN
INITIAL_CANDLES = NO
```

PR #34 integrated the narrow read-only adapter. PR #35 integrated the one-session/one-RunId capture harness and the fail-closed discovery remediation. PR #40 integrated the secure runner; merging it does not execute a real session.

## Secure laboratory runner

The integrated workflow `.github/workflows/btg-first-lab-secure.yml` is restricted to an explicit request on `lab/btg-s1-first-capture`, checks that the requested code revision equals the current remote Sprint 1 head, then executes the exact clean Sprint 1 revision.

The job is bound to GitHub Environment `btg-readonly-lab`. Governance requires the laboratory values to exist only as Environment secrets:

```text
BTG_LAB_DATASERVICES_API_KEY
BTG_LAB_EVIDENCE_PASSPHRASE
```

The current connector cannot inspect or mutate GitHub Environment/secrets administration. Therefore their actual remote configuration is intentionally recorded as:

```text
BTG_LAB_ENVIRONMENT = EXTERNAL_CONFIGURATION_NOT_VERIFIED
BTG_LAB_SECRETS = EXTERNAL_CONFIGURATION_NOT_VERIFIED
```

No secret value may be pasted into chat or committed. Raw market-data evidence is encrypted before artifact handling; only ciphertext, checksum and a sanitized no-price/no-raw-payload summary are exposed remotely.

## Evidence state

```text
RQM_TOTAL = 41
RQM_SATISFIED_OR_FIXTURE_SCOPE = 39
RQM_BLOCKED_SECURITY_SCAN = 2  # RQM-018, RQM-036
NEG_CAP_01_TO_10 = SATISFIED_CURRENT_TREE
READ_ONLY_BY_CONSTRUCTION = SATISFIED_CURRENT_TREE
STRUCTURAL_ESCALATION = SATISFIED_CURRENT_TREE
REAL_PROVIDER_SESSION = NOT_EXECUTED
SECURITY_DIFF_SCAN = NOT_EXECUTED
```

The official Security Diff Scan remains a distinct gate. Codex Security is installed, but its scan action is not exposed in this chat runtime; no alternative scan is relabeled as official PASS.

## Review treatment

For PRs #34, #35 and #40, the project owner explicitly authorized the same coordinating agent to perform adversarial review and proceed. These reviews are not represented as independent review. This treatment does not waive Foundation constraints, CI, NEG-CAP, real-provider evidence or the official Security Diff Scan.

## Remaining Sprint 1 sequence

```text
1. Configure the external GitHub Environment `btg-readonly-lab` with deployment protection appropriate to the laboratory branch.
2. Provision the two laboratory Environment secrets outside repository/chat.
3. Choose one explicit concrete WIN candidate; no ranking, fallback or rollover.
4. Create the dedicated laboratory request branch from the current Sprint 1 head and execute the secure runner.
5. Review the sanitized run summary and protected evidence; preserve one causal RunId from discovery through close.
6. Reconcile real-provider evidence into RQM/XC without overstating fixture evidence.
7. Re-run exact-final-tree CI and NEG-CAP after final evidence/documentation changes.
8. Execute the official Security Diff Scan for the exact final Sprint 1 diff/tree, or only use a separately explicit governance treatment if authorized.
9. Adjudicate all 11 Sprint 1 exit criteria conjunctively.
10. Promote to Sprint 2 only after formal Sprint 1 PASS.
```

No step above authorizes financial execution, broker/trading credentials, order APIs, Paper execution, Risk authorization or real money.
