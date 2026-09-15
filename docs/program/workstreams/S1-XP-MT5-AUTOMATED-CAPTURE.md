# Sprint 1 — automated passive XP/MT5 capture overlay

## Status

This operational overlay refines the manual Phase 4–6 workflow in `S1-XP-MT5-FIRST-RUNTIME-QUALIFICATION.md`. It does not change Sprint 1 acceptance criteria, provider identity, instrument adjudication, or any Frozen Foundation artifact.

## Objective

Reduce operator error and timing races while preserving the file-only, read-only market-observation boundary.

The automation uses two local `FILE_COMMON` coordination files outside Git:

- `btg_ai_trader/capture-bridge-status.tsv` — heartbeat/status emitted by the custom indicator;
- `btg_ai_trader/capture-control.tsv` — short-lived activation record emitted by the local launcher only after the evidence harness has passed its transport preflight.

Neither file contains credentials, account identifiers, balances, positions, or financial instructions.

## Persistent custom indicator

The preferred indicator is:

```text
tools/mt5/XPMarketDataBridge.mq5
```

It is a custom indicator and remains passive. It may be attached once to the explicitly adjudicated WIN contract on M1 and left attached. While no valid control record exists it stays idle and emits only a local status heartbeat.

A valid activation record must contain:

```text
schema=1
state=ACTIVE
capture_scope=s1-xp-capture-aN
instrument=<explicit WIN contract>
provider=xp-mt5
expires_epoch=<bounded local expiry>
```

The indicator rejects malformed scopes, a mismatched symbol, a timeframe other than M1, expired activation, or pre-existing transport files. It derives the three transport paths from `capture_scope`; the operator no longer copies tick, candle, or discovery paths into indicator inputs.

## One-command launcher

After the indicator is compiled and attached once, the preferred workstation command is:

```powershell
.\scripts\xp_mt5_qualifying_capture.ps1
```

The wrapper invokes `scripts/xp_mt5_qualifying_capture.py`, which:

1. requires the canonical `sprint/1-market-observer` branch and a clean working tree;
2. obtains the exact 40-character code revision from Git;
3. discovers the MT5 `FILE_COMMON` root through `%APPDATA%`;
4. waits for a fresh `IDLE` heartbeat from `XPMarketDataBridge` on the explicit instrument and M1;
5. calculates the next unused `s1-xp-capture-aN` namespace automatically;
6. creates the fresh empty namespace;
7. starts the existing `rico_mt5_first_lab_capture.py` harness first;
8. waits until the harness has created its evidence session, proving transport preflight has passed;
9. atomically publishes the bounded activation record;
10. waits for the indicator to report `ACTIVE` for the exact namespace;
11. lets the existing bounded harness perform discovery and tick/candle qualification;
12. removes the activation record in a `finally` path so the indicator returns to `IDLE`;
13. preserves failed/completed namespaces rather than reusing them.

The operator does not need to copy capture paths or race a manual indicator confirmation against the 30-second discovery timeout.

## Safety boundary

The launcher and persistent indicator do not import or call an MT5 terminal-control Python package. They do not authenticate, inspect account state, select positions, or create a financial execution path. The only launcher-to-indicator coordination is local file activation of passive observation.

The existing prohibitions remain unchanged: no automatic contract selection, no automatic rollover, no paper or real execution, no credential transfer, and no financial commitment.

## First-time setup

The automation cannot safely choose or manipulate the MT5 chart through a terminal-control API. One local setup remains deliberately manual:

1. copy/compile the exact reviewed `XPMarketDataBridge.mq5` in MetaEditor;
2. open the explicitly adjudicated contract chart in M1;
3. attach `XPMarketDataBridge` once and leave it attached.

After that, qualifying capture attempts are launched with the single PowerShell command above. If the explicit contract changes, human mapping adjudication remains required before changing the chart/instrument.

## Evidence semantics

Automation does not upgrade evidence by itself. A launcher success remains engineering evidence that must still be reviewed against AC-05, AC-07, timestamp/provenance/health requirements, exact-final-tree checks, and the official Security Diff Scan before Sprint 1 acceptance.
