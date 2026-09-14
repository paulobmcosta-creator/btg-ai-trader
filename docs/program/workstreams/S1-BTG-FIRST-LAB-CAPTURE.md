# Sprint 1 — BTG Data Services controlled first-lab capture

## Purpose

This runbook prepares the first **read-only** real Market Observer evidence session after DD-60 and DD-68. It does not authorize trading, a brokerage account, order APIs, Paper execution, Risk authorization or economic commitment.

## Canonical profile

```text
PROVIDER = BTG Solutions Data Services
INSTRUMENT_FAMILY = WIN
CONCRETE_CONTRACT = explicit operator candidate + provider confirmation point-in-time
STREAM_TYPE = realtime
DATA_TYPE = trades
DATA_SUBTYPE = derivatives
FEED = A
AUTO_RECONNECT = NO
AUTO_ROLLOVER = NO
AUTO_FALLBACK = NO
INITIAL_CANDLES = NO
ECONOMIC_AUTHORITY = NONE
```

The concrete WIN symbol is never a permanent default. It is an explicit candidate for one controlled session and must appear in provider discovery evidence before any subscription is sent.

## Required preconditions

All of the following are mandatory before a real session:

1. PR #34 is integrated only after current-head remote CI and review are valid.
2. The capture harness is reviewed and integrated on top of that provider boundary.
3. The exact code revision to be executed is a full reviewed 40-character Git SHA.
4. An existing controlled output directory is chosen for technical evidence.
5. A BTG Solutions Data Services API key is provisioned by an authorized runtime mechanism under `BTG_DATASERVICES_API_KEY`.
6. The API key value is never committed, pasted into documentation, stored in config, emitted to logs, inserted into CaptureContext/RunManifest, or supplied in chat.
7. The intended concrete WIN candidate is explicitly chosen for that session; no automatic nearest-expiry logic is allowed.

## Execution lifecycle

`scripts/btg_first_lab_capture.py` implements one causal read-only session with one RunId:

```text
connect with no preselected instrument
  -> available_to_subscribe
  -> preserve discovery/control payloads in EvidenceArchive/AuditJournal
  -> verify exact candidate appears in provider discovery evidence
  -> STOP if not confirmed
  -> persist explicit point-in-time confirmation evidence
  -> subscribe_confirmed(exact_candidate)
  -> receive realtime provider messages
  -> count success only for JSON event=trade with symbol=exact_candidate
  -> preserve other post-subscription messages as technical evidence only
  -> unsubscribe
  -> close
  -> require at least one confirmed trade frame
  -> persist canonical capture summary as technical evidence
```

There is no reconnect between discovery and subscription. The same connection that produced the point-in-time discovery evidence is the connection that receives the explicit subscription after confirmation. This removes a time-of-check/time-of-use gap between two separate provider sessions.

The provider settings contain no ticker. The concrete symbol enters the provider reference only after `subscribe_confirmed()`.

## Provider discovery semantics

The official BTG client exposes `available_to_subscribe()` as a separate WebSocket request and allows the client to start with an empty instrument list. The public client documentation does not define a stable response schema for the discovery payload.

Therefore the laboratory must preserve the raw discovery response and treat automated confirmation as a bounded helper, not as permission to invent a symbol. The exact requested WIN symbol must be present in the returned JSON evidence and the resulting evidence must be reviewed after the run. Ambiguous, malformed or absent evidence is fail-closed.

## Invocation contract

The harness requires these explicit arguments:

- `--instrument`: concrete WIN contract candidate to be confirmed by provider discovery;
- `--capture-scope`: bounded logical scope for the session;
- `--code-revision`: exact reviewed 40-character Git SHA;
- `--output-root`: pre-existing controlled directory;
- `--discovery-seconds`: greater than zero and at most 30 seconds;
- `--capture-seconds`: greater than zero and at most 300 seconds.

The API key is **not** a command-line argument. It must exist only in the authorized process environment under `BTG_DATASERVICES_API_KEY`.

A representative invocation shape is:

```text
python scripts/btg_first_lab_capture.py \
  --instrument <EXACT_WIN_CONTRACT_CANDIDATE> \
  --capture-scope first-lab \
  --code-revision <EXACT_REVIEWED_40_CHAR_GIT_SHA> \
  --output-root <PREEXISTING_CONTROLLED_DIRECTORY> \
  --discovery-seconds 10 \
  --capture-seconds 60
```

The placeholders above are documentation tokens, not repository defaults and not configuration values. The operator must substitute the exact session-specific values outside versioned configuration.

## Evidence layout

Each invocation creates one unique session directory containing only canonical technical evidence roots:

```text
btg-s1-first-lab-<uuid>/
  archive/
  journal/
```

There is no loose `session-summary.json`. The session plan, discovery response, explicit confirmation, post-subscription provider messages, qualifying trade events and final capture summary are persisted through the existing `TechnicalEvidenceStore` model.

The credential value is never included in those records. The config hash covers only the non-secret capture profile.

## Fail-closed conditions

The capture MUST stop or refuse to start when any of the following occurs:

- API key is absent from the authorized runtime environment;
- requested symbol is not a concrete uppercase WIN contract matching the bounded format;
- provider discovery does not contain the exact requested symbol;
- provider reports an error during discovery;
- subscription is attempted before the adapter has issued discovery;
- subscription is attempted twice;
- automatic reconnect is requested;
- provider reports an error during capture;
- only ACK/control/non-trade messages arrive after subscription;
- no `trade` event for the exact confirmed symbol is observed;
- output root is missing or traverses a symlink;
- code revision is not a canonical full SHA.

No failed session is reinterpreted as successful evidence.

## Evidence required after the first real session

A successful laboratory session is evidence for provider qualification only when review confirms, at minimum:

- API-key authentication succeeded without secret persistence;
- one RunId covers the causal sequence from discovery through close;
- discovery evidence contains the exact selected WIN contract;
- explicit confirmation evidence precedes subscription;
- no subscription occurred before discovery/confirmation;
- market evidence is `realtime / trades / derivatives` only;
- at least one raw `trade` event for the exact confirmed symbol was persisted;
- ACK/control/non-trade messages did not satisfy the success condition;
- disconnect/close behavior is observable;
- no trading/account/order capability appears in the runtime graph;
- all exact-final-tree CI/RQM/NEG-CAP checks are rerun;
- the official Security Diff Scan is executed when its supported interface is available, unless governance explicitly authorizes a different treatment.

A successful capture does **not** itself grant Sprint 1 acceptance; the 11 Exit Criteria remain conjunctive.
