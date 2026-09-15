# Sprint 1 — XP/MetaTrader 5 first runtime qualification

## Purpose

This runbook governs the first **qualifying read-only realtime session** for the XP-supplied MetaTrader 5 path selected by ADR-0026 and tracked in Issue #54.

It preserves the Sprint 1 passive Market Observer boundary. It does **not** authorize trading, Paper execution, strategy execution, order APIs, account mutation, financial ledger mutation or any economic commitment.

```text
PROVIDER = xp-mt5
REAL_QUALIFYING_PROVIDER_SESSION = NOT_EXECUTED
SPRINT1_PROVIDER_QUALIFIED = NO
SPRINT1_ACCEPTANCE = NO
PROMOTION_TO_SPRINT_2 = NO
```

## Preliminary evidence already obtained

The following occurred on 14/09/2026 before this provider-reconciliation changeset and is preserved only as **pre-qualification evidence**:

- successful authentication to the XP MT5 environment;
- Investor/read-only password established and used locally, without credential disclosure;
- then-reviewed `tools/mt5/RicoMarketDataBridge.mq5` compiled with `0 errors, 0 warnings`;
- passive `WIN*` discovery completed against the XP server;
- discovery reported 57.414 total server symbols, 16 `WIN*` matches, 16 emitted candidates, zero custom exclusions, zero prefix errors and zero enumeration errors;
- `WINV26` was present and identified as the preliminary point-in-time target contract.

This evidence does **not** satisfy AC-05 or AC-07, does not establish the account's concrete zero-cost entitlement and does not qualify XP. The raw preliminary file remains outside Git.

Because this changeset changes provider provenance from `rico-mt5` to `xp-mt5`, the custom indicator must be recompiled from the exact post-reconciliation revision before the qualifying capture.

## Canonical safety boundary

```text
XP / MT5 server
  -> MetaTrader 5 desktop terminal
     -> Investor / read-only authorization
     -> custom indicator: tools/mt5/RicoMarketDataBridge.mq5
        -> ProviderId = xp-mt5
        -> append-only FILE_COMMON observations
           -> scripts/rico_mt5_first_lab_capture.py
              -> trusted Python read-only bridge/discovery readers
                 -> TechnicalEvidenceStore / later adjudication
```

`RicoMarketDataBridge.mq5`, `rico_mt5_bridge.py`, the `RicoMt5*` class names and `scripts/rico_mt5_first_lab_capture.py` are retained temporarily as **legacy compatibility names**. They do not define provider provenance. The active provider identity is `xp-mt5`.

The following remain prohibited:

```text
MASTER_PASSWORD_IN_REPOSITORY = NO
MASTER_PASSWORD_IN_CHAT = NO
MASTER_PASSWORD_IN_COMMAND_LINE = NO
MASTER_PASSWORD_IN_ENVIRONMENT = NO
INVESTOR_PASSWORD_IN_REPOSITORY = NO
INVESTOR_PASSWORD_IN_CHAT = NO
TRUSTED_PYTHON_IMPORTS_METATRADER5 = NO
PYTHON_ACCOUNT_API = ABSENT
PYTHON_POSITION_API = ABSENT
PYTHON_ORDER_API = ABSENT
EXPERT_ADVISOR_FOR_BRIDGE = NO
SCRIPT_FOR_BRIDGE = NO
ORDER_SUBMISSION_TEST = PROHIBITED
PAPER_ORDER_TEST = PROHIBITED
REAL_MONEY_OPERATION = PROHIBITED
AUTO_ROLLOVER = NO
AUTO_CONTRACT_SELECTION = NO
```

If a master password is required locally to create/change an Investor password, it may be entered only in the MT5 GUI. It must never enter Git, chat, shell arguments, environment variables or evidence files.

## Required preconditions

Before the qualifying session:

1. checkout is on an exact reviewed 40-character SHA from `sprint/1-market-observer` and the working tree is clean;
2. exact-final-tree CI/negative-capability checks for that revision are green;
3. `tools/mt5/RicoMarketDataBridge.mq5` is copied without edits and compiled again with zero errors and zero warnings;
4. concrete XP account evidence shows the MT5/platform/feed entitlement used here has **R$0 additional recurring cost**;
5. the same entitlement does not require any minimum real-money trade, RLP, minimum brokerage spend or equivalent economic action merely to remain available;
6. Investor/read-only authorization is active locally;
7. the session occurs while the target WIN feed is expected to be live;
8. a writable evidence root exists outside the repository and contains no credential/account secret;
9. transport files for the qualifying namespace are absent or empty when the harness starts.

If items 4 or 5 cannot be demonstrated, stop. Do not trade merely to preserve platform/feed access.

## Phase 0 — zero-cost entitlement

Preserve non-secret account-level evidence showing, as far as the XP interface permits:

- MetaTrader 5 is available/contracted;
- platform/feed charge used for the session is R$0 additional recurring cost;
- no minimum real-money operation is required to retain that entitlement.

Public XP documentation supports provider selection but does not replace this account-level evidence.

Redact account number, CPF, e-mail, balances, positions, passwords, QR codes and tokens.

## Phase 1 — Investor/read-only

Use only the MT5 GUI.

1. Authenticate to the exact XP production server using the Investor password.
2. Do not enable automatic password saving for this first qualification unless separately justified.
3. Preserve only sanitized, non-secret evidence of the read-only state.
4. Never attempt to submit/modify/cancel an order to prove read-only status.

If trading authority appears to be available under the intended Investor credentials, stop before attaching the bridge.

## Phase 2 — compile exact reviewed indicator

Use only:

```text
tools/mt5/RicoMarketDataBridge.mq5
```

The file name is legacy compatibility. The program must remain a **custom indicator**, not an Expert Advisor or script.

Required result:

```text
PROVIDER_ID_DEFAULT = xp-mt5
COMPILATION = PASS
COMPILER_ERRORS = 0
COMPILER_WARNINGS = 0
```

Any source edit required locally invalidates the reviewed artifact for qualification.

## Phase 3 — discovery and explicit WIN mapping

Discovery is separate from qualifying tick/candle capture.

Use a unique discovery namespace, for example:

```text
s1-xp-discovery-a2
```

Indicator inputs:

```text
ProviderId          = xp-mt5
TickBridgeFile      = btg_ai_trader\s1-xp-discovery-a2\ticks.ndjson
CandleBridgeFile    = btg_ai_trader\s1-xp-discovery-a2\candles.ndjson
DiscoveryBridgeFile = btg_ai_trader\s1-xp-discovery-a2\discovery.ndjson
DiscoveryPrefix     = WIN
```

Attach under Investor authorization, allow one complete snapshot, then detach. Preserve `discovery.ndjson` byte-for-byte outside Git.

A valid snapshot requires:

```text
prefix_errors = 0
enumeration_errors = 0
enumeration_complete = true
```

All candidates must be preserved. The software must not choose the first symbol, nearest expiry, highest volume or an alias such as `WIN$` automatically.

### Point-in-time target

The preliminary session identified `WINV26`. Before the qualifying capture, re-confirm and preserve non-secret point-in-time evidence that the exact current contract is still:

```text
INSTRUMENT_FAMILY = WIN
PROVIDER = xp-mt5
PROVIDER_SYMBOL = WINV26
MAPPING_STATUS = EXPLICITLY_CONFIRMED
```

If the contract changes or the mapping becomes ambiguous, stop and re-adjudicate it. No automatic rollover is authorized.

Incidental tick/candle bytes emitted during discovery are not qualifying AC-07 evidence.

## Phase 4 — fresh qualifying namespace

Create a new session namespace, for example:

```text
s1-xp-capture-a1
```

All three transport files must share that directory and be absent or empty before the harness starts:

```text
<COMMON_FILES>\btg_ai_trader\s1-xp-capture-a1\discovery.ndjson
<COMMON_FILES>\btg_ai_trader\s1-xp-capture-a1\ticks.ndjson
<COMMON_FILES>\btg_ai_trader\s1-xp-capture-a1\candles.ndjson
```

Never reuse a failed/completed capture namespace.

## Phase 5 — start harness before indicator

The legacy-named harness remains the active file-only evidence harness:

```text
scripts/rico_mt5_first_lab_capture.py
```

It must start **before** the indicator emits qualifying bytes. It does not connect to MT5, receive credentials or expose account/order APIs.

The integrated bounds remain:

```text
discovery_timeout_seconds = > 0 and <= 30
capture_seconds = 60..300
poll_interval_ms = 10..1000
heartbeat_timeout_ms > poll_interval_ms
market_staleness_ms > poll_interval_ms
```

One controlled initial-session command is:

```powershell
python scripts\rico_mt5_first_lab_capture.py `
  --instrument WINV26 `
  --capture-scope s1-xp-capture-a1 `
  --code-revision <EXACT_40_CHARACTER_GIT_SHA> `
  --discovery-file "<COMMON_FILES>\btg_ai_trader\s1-xp-capture-a1\discovery.ndjson" `
  --tick-file "<COMMON_FILES>\btg_ai_trader\s1-xp-capture-a1\ticks.ndjson" `
  --candle-file "<COMMON_FILES>\btg_ai_trader\s1-xp-capture-a1\candles.ndjson" `
  --output-root "C:\BTG_AI_TRADER_EVIDENCE" `
  --clock-scope windows-local-monotonic `
  --discovery-timeout-seconds 30 `
  --capture-seconds 120 `
  --poll-interval-ms 100 `
  --heartbeat-timeout-ms 2000 `
  --market-staleness-ms 5000
```

These numeric values are **session parameters**, not permanent runtime policy. If evidence shows they are inappropriate, adjudicate the evidence rather than rewriting the run after the fact.

No credential, account number, password or token belongs in the CLI.

## Phase 6 — qualifying realtime capture

After the harness is waiting:

1. open the exact `WINV26` chart interactively in MT5;
2. use M1 for this controlled first capture so at least one real bar transition can be observed inside the bounded window; this is a session choice, not universal policy;
3. attach the freshly compiled custom indicator with exactly:

```text
ProviderId          = xp-mt5
TickBridgeFile      = btg_ai_trader\s1-xp-capture-a1\ticks.ndjson
CandleBridgeFile    = btg_ai_trader\s1-xp-capture-a1\candles.ndjson
DiscoveryBridgeFile = btg_ai_trader\s1-xp-capture-a1\discovery.ndjson
DiscoveryPrefix     = WIN
```

4. allow realtime observation long enough for genuine tick flow and at least one bar transition;
5. detach the indicator after the bounded capture interval so files flush cleanly;
6. let the harness terminate normally;
7. preserve discovery/tick/candle raw files and harness evidence byte-for-byte outside Git.

A successful engineering run requires at least two tick frames and at least one candle with `finality = FINAL`. The first `OnCalculate` must not fabricate a historical finalized candle; the candle must arise from an observed transition while attached.

The harness latency measure is **local monotonic ingress-to-validated-availability** only. It must never be relabeled as exchange-to-terminal, network or end-to-end market latency.

## Phase 7 — evidence review

Before any acceptance claim, review must establish:

- discovery snapshot complete and internally consistent;
- exact provider identity is `xp-mt5`;
- exact symbol equals the explicitly confirmed concrete WIN contract;
- genuine realtime tick flow is present;
- at least one genuine finalized candle is present;
- tick/candle sequences are contiguous from one;
- no transport truncation/replacement occurred;
- exact code revision, config hash, RunId and CaptureContext are present;
- heartbeat/staleness and local monotonic latency evidence are interpretable within their scope;
- Python still contains no `MetaTrader5`, account, position or order API;
- no credential entered Git, shell arguments, evidence payloads or chat.

Harness success is necessary engineering evidence but is not automatic AC-05/AC-07 or Sprint 1 PASS.

## Evidence kept outside Git

Keep outside Git until deliberately sanitized and curated:

- master/investor passwords;
- account login/number and identifying account metadata;
- CPF/e-mail/phone/QR codes;
- balance/portfolio/positions;
- raw discovery/tick/candle files;
- raw screenshots;
- harness evidence-session directory.

## Post-session sequence

After the qualifying session:

1. review/sanitize evidence;
2. map evidence explicitly to AC-01/02/03/04/05/07/08/09/12/13 and relevant RQMs;
3. update Issue #54 only with supported claims;
4. reconcile living checkpoints without upgrading unsupported evidence;
5. rerun exact-final-tree tests, lint, typing, compile, Foundation and NEG-CAP checks;
6. execute the official Security Diff Scan on the exact final Sprint 1 tree;
7. adjudicate all 11 Sprint 1 exit criteria conjunctively;
8. promote to Sprint 2 only after formal Sprint 1 PASS.

No step authorizes financial execution.