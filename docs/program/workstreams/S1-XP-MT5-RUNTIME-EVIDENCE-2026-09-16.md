# Sprint 1 — XP/MetaTrader 5 runtime qualification evidence — 2026-09-16

## Purpose

This record preserves the sanitized engineering evidence for the first successful qualifying passive realtime session against the XP-supplied MetaTrader 5 path selected by ADR-0026.

It is an evidence record, not a normative rewrite and not a Sprint 1 approval record. Raw discovery/tick/candle files and the evidence-session directory remain outside Git.

## Session identity

```text
DATE = 2026-09-16
PROVIDER = xp-mt5
INSTRUMENT_FAMILY = WIN
INSTRUMENT = WINV26
TIMEFRAME = PERIOD_M1
CAPTURE_SCOPE = s1-xp-capture-a12
CODE_REVISION = e622658922ff38e49e1112a48d91eecb2d43a522
GIT_WORKTREE_AT_CAPTURE = CLEAN
CAPTURE_DURATION_SECONDS = 120
BRIDGE_FINAL_STATE = IDLE
```

The exact reviewed indicator source was recompiled before this session with:

```text
COMPILER_ERRORS = 0
COMPILER_WARNINGS = 0
```

The successful launcher result was:

```text
CAPTURE_ACTIVE: s1-xp-capture-a12
CAPTURE_COMPLETED: s1-xp-capture-a12
CODE_REVISION: e622658922ff38e49e1112a48d91eecb2d43a522
EVIDENCE_SESSION: C:\BTG_AI_TRADER_EVIDENCE\rico-mt5-s1-first-lab-2df9a547-378f-45b0-95cd-941c56a50cec
```

## Sanitized raw-transport inventory

Raw transport files remain outside Git. Their byte counts, record counts and SHA-256 fingerprints are preserved here so the local evidence can be verified without publishing the payloads.

| File | Records | Bytes | SHA-256 |
|---|---:|---:|---|
| `candles.ndjson` | 2 | 538 | `979A14ED3E0F0B759F5FACA6E7BC6007C4D44A31C89A97F5640005A00A00C7BB` |
| `discovery.ndjson` | 18 | 2,011 | `75212A9370AF54942DA20171983FF547208CE781CE4FEA4AEE6FC8D8AFE88D3A` |
| `ticks.ndjson` | 8,005 | 1,517,016 | `9380F4FD2FE1F188A3CF38CB482A944F0038DFA700FDD8B40018080ACE09DD65` |

The 18 discovery records correspond to one complete snapshot envelope with 16 preserved `WIN*` candidates. The qualifying session explicitly confirmed `WINV26`; no automatic contract selection, ranking, rollover or fallback was used.

## Harness-success semantics

`scripts/rico_mt5_first_lab_capture.py` returns success only after the controlled session establishes all of the following within the configured bounds:

- a complete discovery snapshot with the exact explicit instrument present;
- provider/symbol consistency for consumed market observations;
- contiguous tick bridge sequence from one;
- at least two realtime tick frames;
- contiguous candle bridge sequence from one;
- at least one candle explicitly marked `finality = FINAL` with a positive interval;
- preserved local monotonic ingress-to-validated-availability evidence;
- heartbeat/staleness evidence with a continuously `READY` health path;
- technical evidence persistence under the exact code revision, run manifest/config hash and provider capture context.

The successful evidence summary records:

```text
real_money = false
trading_capability = false
metatrader_control_api = false
```

Trusted Python remains file-only and does not import `MetaTrader5` or expose account, position or order APIs.

## Supporting engineering checks

Immediately before the realtime session, the dedicated offline harness test file executed locally with:

```text
5 passed
```

That offline result is supporting engineering evidence only. It is not relabeled as realtime evidence.

A prior passive diagnostic namespace, `s1-xp-capture-a11`, confirmed that the corrected `FILE_COMMON` control path enters `ACTIVE`, creates the expected transport files, and returns to `IDLE`. It is nonqualifying and remains separate from `a12`.

## Evidence adjudication at this checkpoint

The successful `a12` session supplies real-provider engineering evidence for the previously open runtime portions of:

- AC-01 / AC-02 point-in-time discovery and explicit provider-symbol mapping;
- AC-05 read-only realtime market-data access;
- AC-07 tick and finalized-candle observation;
- AC-08 heartbeat/liveness within the controlled-session policy;
- AC-09 local monotonic observable latency within its explicitly limited clock scope;
- AC-12 capture context/provenance;
- AC-13 technical evidence persistence.

This record does not by itself grant `SPRINT1_PROVIDER_QUALIFIED = YES` or `SPRINT1_ACCEPTANCE = YES`. The project gate still requires post-reconciliation exact-final-tree CI/NEG-CAP verification and the official Security Diff Scan, followed by conjunctive adjudication of all 11 Sprint 1 exit criteria.

## Security boundary preserved

```text
ORDER_SUBMISSION = IMPOSSIBLE
ORDER_MODIFICATION = IMPOSSIBLE
ORDER_CANCELLATION = IMPOSSIBLE
REAL_MONEY_PATH = ABSENT
PAPER_PATH = ABSENT
LIVE_TRADING_PATH = ABSENT
ECONOMIC_COMMITMENT = IMPOSSIBLE
```

No credential, account number, position, balance or other identifying broker/account payload is versioned in this record.