# Sprint 1 — Rico/MetaTrader 5 first runtime qualification

## Purpose

This runbook governs the first **read-only** real-provider session for the Rico-supplied MetaTrader 5 path selected by ADR-0025. It converts the already integrated offline bridge, symbol-discovery surface and local evidence harness into a controlled operator procedure for collecting evidence against Sprint 1 AC-01, AC-02, AC-05 and AC-07.

It does **not** authorize trading, Paper execution, strategy execution, order APIs, account mutation, financial ledger mutation or any economic commitment.

```text
REAL_PROVIDER_SESSION = NOT_EXECUTED
SPRINT1_PROVIDER_QUALIFIED = NO
SPRINT1_ACCEPTANCE = NO
PROMOTION_TO_SPRINT_2 = NO
```

Those states remain unchanged until a future evidence review explicitly adjudicates them.

## External operational facts used by this runbook

The following vendor/platform facts are operational inputs, not substitutes for repository acceptance evidence:

1. Rico currently describes MetaTrader as optional and free of platform charge for clients: <https://www.rico.com.vc/plataformas/metatrader/>.
2. MetaTrader 5 documents two account-access modes. Investor authorization permits account/price observation but does not permit trading: <https://www.metatrader5.com/pt/terminal/help/startworking/authorization>.
3. MetaTrader 5 documents creation/change of an investor password under platform settings: <https://www.metatrader5.com/pt/terminal/help/startworking/settings>.
4. MQL5 `FILE_COMMON` places shared files under the terminal common data folder, in `Terminal/Common/Files`: <https://www.mql5.com/en/docs/files/fileopen>.

These statements must be rechecked if provider terms or platform behavior change. A marketing statement that the platform is free does not by itself prove that the concrete account has the required realtime WIN entitlement without a minimum-trade condition.

## Canonical safety boundary

The only approved runtime topology is:

```text
Rico / MT5 server
  -> MetaTrader 5 desktop terminal
     -> Investor / read-only authorization
     -> custom indicator: tools/mt5/RicoMarketDataBridge.mq5
        -> append-only FILE_COMMON observations
           -> scripts/rico_mt5_first_lab_capture.py
              -> trusted Python read-only bridge/discovery readers
                 -> TechnicalEvidenceStore / later adjudication
```

The following remain prohibited throughout the session:

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

If establishing an investor password requires entering the master password in the MetaTrader GUI, that action occurs **locally and interactively only**. The value must never be copied into the project, shell, GitHub, evidence files or chat.

For the first qualification session, do not enable automatic password saving. Credential persistence by the terminal is outside the project evidence boundary and is unnecessary for this gate.

## Required preconditions

All conditions below are mandatory before the runtime session begins.

1. The operator is on an exact reviewed 40-character Git SHA from `sprint/1-market-observer`; the working tree is clean.
2. The exact tree contains the integrated `RicoMarketDataBridge.mq5`, `RicoMt5BridgeReader`, `RicoMt5DiscoveryReader` and `scripts/rico_mt5_first_lab_capture.py` implementations.
3. Exact-final-tree CI and negative-capability verification are green for the selected revision.
4. MetaTrader 5 has been activated/contracted through the concrete Rico account with **R$0 additional recurring platform charge** confirmed for that account state.
5. No real-money trade, minimum number of contracts or other financial operation is required merely to preserve the entitlement used by this qualification. If such an operation is required, stop and classify the Rico path as incompatible with the current zero-cost/no-economic-action constraint.
6. The terminal is obtained through the Rico/official MetaTrader route, not an arbitrary third-party binary.
7. Investor/read-only authorization exists for the concrete account. If the broker/server does not provide a usable investor mode, stop.
8. The session is conducted while the target WIN market-data stream is expected to be live; delayed or historical-only availability cannot satisfy AC-05/AC-07 realtime evidence.
9. A local, non-repository evidence root exists and is writable. It must not contain credentials or account secrets.
10. The operator understands that discovery candidates are evidence, not an instruction to trade or an automatic front-contract decision.

## Phase 0 — establish zero-cost entitlement evidence

Before logging into the terminal for qualification, preserve non-secret evidence showing the concrete account/platform state. Evidence should establish, as far as the Rico interface permits:

- MetaTrader 5 is contracted/available for the account;
- the platform charge shown for the account is R$0;
- no minimum real-money operation is stated as necessary to keep the platform/feed entitlement used by this session;
- the account is connected to the expected Rico server.

Acceptable evidence can include a sanitized screenshot or locally saved provider page/statement. Redact or omit account number, CPF, e-mail, QR codes, passwords, tokens and unrelated portfolio information.

If the concrete account terms contradict the zero-cost constraint, **do not continue**.

## Phase 1 — establish investor/read-only authorization locally

Use the MetaTrader desktop GUI only.

1. If needed, create/change an **investor (read-only) password** through the terminal's account/password settings. Any master password required for that UI action remains local and is never recorded by this project.
2. Disconnect the trading account session if necessary, then authenticate using the account login, the **investor password**, and the exact Rico server.
3. Leave automatic password saving disabled for the first qualification.
4. Verify that the terminal identifies the connection as investor/read-only or otherwise exposes trading as disabled.
5. Preserve only non-secret evidence of that state. A screenshot may show the read-only/investor state, but must redact account identifiers and unrelated financial information.
6. Do **not** prove read-only status by attempting to submit, modify or cancel an order. The Sprint 1 boundary prohibits creating the execution path merely to test that it fails.

If the terminal appears to grant normal trading authority under the credentials intended for investor mode, stop immediately and do not attach the bridge.

## Phase 2 — compile the reviewed custom indicator

Use only the reviewed source from the exact checked-out repository revision:

```text
tools/mt5/RicoMarketDataBridge.mq5
```

The bridge must remain a **custom indicator**. Do not convert it to an Expert Advisor or script.

Compile it in MetaEditor and reject the session if the source requires edits to compile. A locally modified bridge is a different artifact and cannot qualify the reviewed tree.

Record, outside the repository:

```text
CODE_REVISION = <exact 40-character Git SHA>
BRIDGE_SOURCE = tools/mt5/RicoMarketDataBridge.mq5
COMPILATION = PASS | FAIL
COMPILER_ERRORS = <count>
COMPILER_WARNINGS = <count>
```

`COMPILATION = FAIL` blocks the real session.

## Phase 3 — create unique file namespaces

Every qualification attempt receives a unique ASCII session label, for example:

```text
s1-rico-20260914T190000Z-a1
```

The example is a shape only, not a fixed session identifier.

Use unique indicator input file names so no previous observation can contaminate a new attempt:

```text
TickBridgeFile      = btg_ai_trader\<SESSION>\ticks.ndjson
CandleBridgeFile    = btg_ai_trader\<SESSION>\candles.ndjson
DiscoveryBridgeFile = btg_ai_trader\<SESSION>\discovery.ndjson
DiscoveryPrefix     = WIN
```

Because the bridge uses `FILE_COMMON`, the physical files are under the MetaTrader common data path, beneath:

```text
Terminal\Common\Files\btg_ai_trader\<SESSION>\
```

Do not guess the absolute Windows profile path. Locate the terminal common data directory through MetaTrader/MQL5 terminal information when needed.

Never reuse a session directory after a failed or completed attempt. The bridge and Python readers assume append-only continuity.

For the **qualifying capture namespace**, the harness requires the three transport files to be absent or empty when the harness starts. The `--output-root` must already exist as a local directory outside the repository. Do not pre-populate the qualifying transport files with discovery or market data from an earlier attachment.

## Phase 4 — passive WIN symbol discovery

The first attachment is a **discovery phase**, not qualifying tick/candle evidence.

1. Attach the reviewed indicator to one chart while still under investor authorization.
2. Use the unique discovery namespace from Phase 3 and `DiscoveryPrefix = WIN`.
3. The indicator enumerates the server symbol list without programmatically adding symbols to Market Watch.
4. Detach the indicator after a complete discovery snapshot has been emitted.
5. Preserve `discovery.ndjson` byte-for-byte.
6. Parse it with the integrated `RicoMt5DiscoveryReader`.

A valid snapshot must satisfy all parser invariants and report:

```text
prefix_errors = 0
enumeration_errors = 0
enumeration_complete = true
```

All successfully classified `WIN*` candidates are preserved. The software must not rank them, select a front contract or infer expiry from the symbol name.

Tick/candle files produced incidentally during this discovery attachment are **not** qualifying AC-07 evidence and must not be relabeled as such.

### Discovery fail-closed conditions

Stop if:

- no complete discovery snapshot is available;
- `prefix_errors > 0`;
- `enumeration_errors > 0`;
- snapshot accounting fails;
- duplicate provider symbols appear;
- no plausible WIN candidates are returned;
- the evidence requires guessing which contract is current.

## Phase 5 — explicit point-in-time WIN mapping

AC-02 requires more than a `WIN` prefix. Before qualifying capture:

1. Review the complete provider candidate set from Phase 4.
2. Establish the **current concrete WIN contract** using authoritative point-in-time contract evidence, such as B3 instrument/expiry information and the terminal's own non-secret contract details.
3. Confirm that the exact concrete provider symbol exists in the discovery snapshot from the same qualification context.
4. Record the mapping decision explicitly; do not make it a permanent default.

Required evidence shape:

```text
INSTRUMENT_FAMILY = WIN
PROVIDER = rico-mt5
CAPTURE_SCOPE = <session-specific scope>
PROVIDER_SYMBOL = <exact discovered concrete symbol>
MAPPING_STATUS = EXPLICITLY_CONFIRMED | AMBIGUOUS | NOT_FOUND
MAPPING_EVIDENCE = <non-secret evidence references>
```

Only `EXPLICITLY_CONFIRMED` may proceed. `AMBIGUOUS` and `NOT_FOUND` are fail-closed.

No automatic nearest-expiry, highest-volume or first-list-item rule is authorized here.

## Phase 6 — controlled realtime tick/candle capture with the evidence harness

After the exact concrete symbol has been explicitly confirmed, use a **new capture namespace**. The harness must be running **before** the indicator writes qualifying discovery/tick/candle bytes so it can record local monotonic ingress-to-validated-availability evidence and session health.

### Phase 6A — prepare explicit harness inputs

Before execution, record all harness inputs as session-specific qualification inputs. They are evidence for this run, not universal production defaults.

The integrated CLI requires:

```text
--instrument
--capture-scope
--code-revision
--discovery-file
--tick-file
--candle-file
--output-root
--clock-scope
--discovery-timeout-seconds
--capture-seconds
--poll-interval-ms
--heartbeat-timeout-ms
--market-staleness-ms
```

The integrated harness enforces these bounds:

```text
discovery_timeout_seconds = > 0 and <= 30
capture_seconds = 60..300
poll_interval_ms = 10..1000
heartbeat_timeout_ms > poll_interval_ms
market_staleness_ms > poll_interval_ms
```

The heartbeat and market-staleness values must be explicitly chosen and recorded for the session. Fixture values or permissive values chosen merely to obtain a PASS must **not** be promoted into runtime policy. If later evidence shows the thresholds are inappropriate, the evidence must be adjudicated accordingly rather than rewriting the session after the fact.

A PowerShell command template is:

```powershell
python scripts/rico_mt5_first_lab_capture.py `
  --instrument <EXACT_WIN_SYMBOL> `
  --capture-scope <SESSION_SPECIFIC_SCOPE> `
  --code-revision <EXACT_40_CHARACTER_GIT_SHA> `
  --discovery-file "<COMMON_FILES>\btg_ai_trader\<CAPTURE_SESSION>\discovery.ndjson" `
  --tick-file "<COMMON_FILES>\btg_ai_trader\<CAPTURE_SESSION>\ticks.ndjson" `
  --candle-file "<COMMON_FILES>\btg_ai_trader\<CAPTURE_SESSION>\candles.ndjson" `
  --output-root "<LOCAL_NON_REPOSITORY_EVIDENCE_ROOT>" `
  --clock-scope <LOCAL_MONOTONIC_CLOCK_SCOPE> `
  --discovery-timeout-seconds <SESSION_VALUE> `
  --capture-seconds <SESSION_VALUE> `
  --poll-interval-ms <SESSION_VALUE> `
  --heartbeat-timeout-ms <SESSION_VALUE> `
  --market-staleness-ms <SESSION_VALUE>
```

The placeholders above are deliberately not defaults. Replace them only with values established for the concrete session. No credential, account number, password or token is accepted by the harness CLI.

### Phase 6B — execute capture in causal order

1. Confirm the qualifying capture transport files are absent or empty and all three resolve to the same explicit capture-session directory.
2. Start `scripts/rico_mt5_first_lab_capture.py` from the exact reviewed repository revision.
3. Open/select the chart for the exact confirmed provider symbol interactively in the terminal. This operator UI action is not delegated to Python and does not authorize trading.
4. For the first lab profile, use a short chart interval appropriate for observing at least one completed candle; the chosen interval must be recorded as session evidence and is **not** a universal runtime default.
5. Attach a fresh instance of the reviewed custom indicator using the exact **capture** namespace passed to the harness. Do not reuse the discovery-phase namespace.
6. The capture-phase discovery snapshot must complete before evidence is treated as qualifying market capture.
7. Allow the bridge to observe realtime ticks and at least one genuine bar transition so that a finalized candle can be emitted.
8. Detach the indicator to close/flush the files cleanly after the bounded capture interval.
9. Allow the harness to terminate normally and record the resulting local evidence-session directory.
10. Preserve `ticks.ndjson`, `candles.ndjson` and `discovery.ndjson` byte-for-byte before any later manual transformation.

The harness fails closed on discovery ambiguity/incompleteness, provider/symbol mismatch, non-contiguous bridge sequence, stale/nonfresh transport at session start, health degradation, bounded-buffer overflow or insufficient qualifying observations. A successful run requires at least two tick frames and at least one explicitly finalized candle.

The first `OnCalculate` state does not fabricate a historical finalized candle. A qualifying candle must result from a bar transition observed while the bridge is attached.

The harness latency record is **local monotonic ingress-to-validated-availability evidence**. It must not be relabeled as exchange-to-terminal, broker-network or end-to-end market latency.

## Phase 7 — bridge and evidence review

The raw files and harness output are provider evidence inputs, not automatically accepted observations.

Review must establish at minimum:

- discovery snapshot is complete and internally consistent;
- exact provider symbol equals the explicitly confirmed concrete WIN contract;
- tick records are present and belong to the exact symbol;
- tick timestamps advance in a manner consistent with live observations;
- at least one finalized candle is present for the exact symbol;
- candle interval/finality fields are structurally valid;
- tick/candle duplicates or malformed records are not silently discarded;
- bridge sequences are contiguous from one for the qualifying session;
- file continuity was not broken by truncation/replacement;
- the harness session records exact code revision, config hash, provider identity, RunId, health samples and local monotonic timing evidence;
- trusted Python path still contains no `MetaTrader5`, account, position or order API;
- no master/trading credential entered the repository, shell arguments, evidence payloads or chat.

The runtime review must determine whether the captured observations and harness health/timing records are sufficient to establish the Sprint 1 timestamp, heartbeat/staleness, provenance and latency requirements. Harness success is necessary engineering evidence but does not by itself adjudicate AC-05, AC-07 or the final acceptance gate.

## Evidence that must remain outside Git

Do not commit real-session raw data or screenshots merely because they are non-secret. The first session should be reviewed locally before any curated artifact is considered for version control.

Keep outside Git:

- investor password;
- master password;
- account login/number when identifying;
- CPF/e-mail/phone/QR codes;
- screenshots containing portfolio/positions/balance or account identifiers;
- raw session files until reviewed for sensitive content;
- harness evidence-session output until reviewed for sensitive content;
- any terminal log containing identifying account metadata.

Version control should receive only deliberately curated, non-secret conclusions/evidence references approved after review.

## Qualification matrix

A real session may support provider qualification only when each row has direct evidence:

| Gate | Required evidence | Failure disposition |
|---|---|---|
| Zero recurring cost | Concrete account/platform state shows no additional recurring MT5 charge | Reject provider path |
| No minimum economic action | Entitlement does not require a trade/contract minimum | Reject provider path |
| Investor boundary | Investor/read-only authorization established without order test | Stop/reject if unavailable |
| AC-01 discovery | Complete WIN candidate snapshot with zero discovery errors | Fail closed |
| AC-02 mapping | Explicit point-in-time concrete WIN mapping | Fail closed if ambiguous |
| AC-05 realtime | Real provider stream produces live observations for exact symbol | Fail closed |
| AC-07 ticks | Raw realtime ticks for exact symbol | Fail closed |
| AC-07 candles | At least one genuinely finalized candle from observed transition | Fail closed |
| Provenance | Exact code SHA, session scope, config hash, RunId and provider identity preserved | Fail closed |
| Heartbeat/staleness | Harness/runtime evidence supports liveness/staleness adjudication | Fail closed |
| Latency | Local timing evidence exists and is not overstated beyond its clock scope | Fail closed |
| Negative capability | No trading/account/order surface entered trusted runtime | Fail Sprint 1 |

No single row compensates for another. Qualification is conjunctive.

## Post-session repository actions

After a real session, do not immediately mark Issue #45 complete. First:

1. review and sanitize all raw and harness-generated evidence;
2. map the evidence explicitly to AC-01/02/03/05/07 and relevant RQMs;
3. adjudicate heartbeat/staleness, provenance and latency claims within their actual evidence scope;
4. rerun exact-final-tree CI and negative-capability checks after any curated evidence/documentation changes;
5. execute the official Security Diff Scan when the supported action is available;
6. update the provider-qualification issue only with claims directly supported by reviewed evidence;
7. adjudicate the Sprint 1 final acceptance gate conjunctively.

A successful Rico/MT5 observation session is **necessary evidence**, not automatic Sprint 1 PASS.
