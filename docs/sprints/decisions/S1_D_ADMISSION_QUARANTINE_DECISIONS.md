# S1-D — Strict fixture admission and quarantine decisions

- State: decisions before first dependent code, autonomous mandate 2026-09-13.
- Base: PR22 at 94c6181bb50fc7393d2b3a7b98844edca5ab4d38.
- Norms: ADR0003/0004/0006/0012/0015; 0F-E S1-EC-020/067/078/090 and DD02/62; S1-A domain decisions.
- Scope: one explicit fixture JSON decoder producing typed observation or isolated quarantine receipt. No provider admission, serializer for production sources, network, SDK, callback, financial operation, replay engine or live clock.

## DD02: fixture-json-v1

The caller must supply max_payload_bytes as an explicit positive integer (never bool). Oversized input is quarantined before UTF-8 or JSON decoding. Parser RecursionError becomes a structured JSON rejection; no payload-size default is selected. This fixture codec does not replace the separate technical-storage codec.

The UTF-8 JSON root has exactly these keys: envelope_version, schema_version, event_id, event_type, source, instrument_id, event_time, effective_time, payload, external_event_id, source_sequence, sequence_scope, correlation_id, causation_id. Both versions are integer1; booleans are not integers. Duplicate keys, missing/extra fields, invalid UTF-8/JSON, nonstandard NaN/Infinity tokens and unsupported versions are rejected. No root field can overwrite internal ingress context.

source has exactly provider/scope/symbol and must equal the RawFrame reference. event_type is TICK or CANDLE and must agree with RawChannel. event_id is fixture-supplied canonical UUID; no ID is generated. instrument_id is {uuid: canonical UUID} or an explicit missing value; this declaration does not perform registry resolution or authenticate identity.

Numeric fields use {decimal: text} with decimal lexical grammar [+-]?(0|[1-9][0-9]*)([.][0-9]+)?([eE][+-]?[0-9]+)? (full match; no whitespace, underscore, NaN or Infinity) and finite Decimal, or {missing: reason}. JSON numbers, null, booleans and whitespace/coercions are not numeric values. Missing reasons are UNKNOWN, NOT_PROVIDED or NOT_APPLICABLE and remain distinct.

Temporal values use {utc: YYYY-MM-DDTHH:MM:SS.ffffffZ} or {missing: reason}. The UTC syntax is exact; offsets and naive dates are rejected rather than converted. Candle interval endpoints require known UTC. event_time has exactly value/basis/resolution_us: value is temporal, basis is {text: nonempty text} or missing, resolution_us is positive integer microseconds or missing. effective_time and candle finalized_at/available_at are temporal. No timestamp is inferred from another axis. Model validation enforces known finality/availability and OHLC rules.

Tick payload keys: bid, ask, last, volume. Candle keys: interval_start, interval_end, finality, finalized_at, available_at, open, high, low, close, volume. finality is OPEN, FINAL or UNKNOWN. External event/sequence/correlation/causation metadata use explicit null where the existing envelope permits absence; otherwise strict text/integer/typed UUID rules apply. Source sequence and scope are paired.

IngressMetadata is supplied explicitly by the caller: UTC ingestion_time, temporal knowledge_time, and nonnegative integer ingestion_order or None. Known knowledge cannot precede ingestion. This metadata is not parsed from raw or inferred from source time; it is preserved in every receipt.

## DD62: returned quarantine channel

admit_fixture(frame, ingress, *, max_payload_bytes) returns one immutable Admitted receipt (original raw frame, ingress, validated EventEnvelope) or Quarantined receipt (same raw and ingress, stable reason enum and field path). Quarantine exposes no admitted envelope. Raw bytes, symbols and supplied event ordering remain untouched. Known malformed-input exceptions are isolated at decoding/domain boundaries; unexpected programming errors propagate. A corrupt frame does not consume or mutate the next fixture frame.

Reasons distinguish payload-size limit, UTF8, JSON, schema, domain, source mismatch and channel mismatch. Diagnostic paths do not echo payload content. The receipt is a synchronous channel to its owner, not an accumulating list or durable write. The owner must retain both admitted and quarantined receipts, including when downstream persistence or queue offer fails. Returning a receipt is not durable acknowledgment or complete RQM025.

No deduplication, lateness decision, registry lookup, evidence archive or capture RunId is fabricated. PR23 can later assess admitted envelopes; PR19 can persist receipts and original bytes in the composition. RQM025/DELIV-S1-05 are partial until that integration proves durable isolation and continuing feed handling.

## Verification

Tests cover both channels; all missing reasons; immutable corrupt/raw preservation; malformed encoding/JSON/duplicate keys; unknown/extra fields; strict versions/numbers/timestamps; source/channel mismatch; invalid OHLC/finality/knowledge; optional sequence pair rules; sequential bad then good fixture handling; and no invented identities, time or normalization. Existing S1-A/B tests and six remote checks run on the exact head. No official Security scan or full NEG-CAP gate is claimed.
