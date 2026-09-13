"""Strict fixture decoding and isolated quarantine regressions."""

import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest

from btg_ai_trader.observer.admission import (
    Admitted,
    IngressMetadata,
    Quarantined,
    RejectionReason,
    admit_fixture,
)
from btg_ai_trader.observer.identity import ProviderInstrumentRef
from btg_ai_trader.observer.market import Candle, CandleFinality, Tick
from btg_ai_trader.observer.provider import (
    CapabilitySupport,
    FidelityMode,
    ProviderCapabilities,
)
from btg_ai_trader.observer.raw_source import FixtureMarketDataSource, RawChannel, RawFrame
from btg_ai_trader.observer.values import MissingReason

STAMP = "2026-09-13T12:00:00.000000Z"
UUID = "11111111-1111-4111-8111-111111111111"
LIMIT = 65536


def ingress() -> IngressMetadata:
    return IngressMetadata(datetime(2026, 9, 13, 12, 1, tzinfo=UTC), MissingReason.UNKNOWN, 7)


def document(channel: RawChannel = RawChannel.TICK) -> dict[str, Any]:
    result: dict[str, Any] = {
        "envelope_version": 1, "schema_version": 1, "event_id": UUID,
        "event_type": channel.value,
        "source": {"provider": "fixture", "scope": "capture-A", "symbol": "RaW"},
        "instrument_id": {"missing": "UNKNOWN"},
        "event_time": {
            "value": {"utc": STAMP}, "basis": {"text": "source"},
            "resolution_us": 1,
        },
        "effective_time": {"missing": "NOT_APPLICABLE"},
        "payload": {
            "bid": {"decimal": "10.00"}, "ask": {"decimal": "11"},
            "last": {"missing": "NOT_PROVIDED"}, "volume": {"decimal": "0"},
        },
        "external_event_id": None, "source_sequence": None, "sequence_scope": None,
        "correlation_id": None, "causation_id": None,
    }
    if channel is RawChannel.CANDLE:
        result["payload"] = {
            "interval_start": {"utc": "2026-09-13T11:59:00.000000Z"},
            "interval_end": {"utc": STAMP}, "finality": "FINAL",
            "finalized_at": {"utc": STAMP}, "available_at": {"utc": STAMP},
            "open": {"decimal": "10"}, "high": {"decimal": "12"},
            "low": {"decimal": "9"}, "close": {"decimal": "11"},
            "volume": {"missing": "UNKNOWN"},
        }
    return result


def raw(data: dict[str, Any], channel: RawChannel = RawChannel.TICK) -> RawFrame:
    return RawFrame(
        json.dumps(data).encode("utf-8"),
        ProviderInstrumentRef("fixture", "capture-A", "RaW"), channel,
    )


def decode(data: dict[str, Any], channel: RawChannel = RawChannel.TICK) -> Admitted | Quarantined:
    return admit_fixture(raw(data, channel), ingress(), max_payload_bytes=LIMIT)


@pytest.mark.parametrize("channel", list(RawChannel))
def test_admission_preserves_exact_frame_context_identity_and_domain(channel: RawChannel) -> None:
    frame = raw(document(channel), channel)
    context = ingress()
    result = admit_fixture(frame, context, max_payload_bytes=len(frame.payload))
    assert isinstance(result, Admitted)
    assert result.raw is frame
    assert result.ingress is context
    assert result.envelope.event_id.value == UUID
    assert result.envelope.source is not frame.reference
    assert result.envelope.source == frame.reference
    assert result.envelope.times.ingestion_time is context.ingestion_time
    assert result.envelope.times.knowledge_time is MissingReason.UNKNOWN
    assert result.envelope.ingestion_order == 7
    assert result.envelope.instrument_id is MissingReason.UNKNOWN
    if channel is RawChannel.TICK:
        assert isinstance(result.envelope.payload, Tick)
        assert result.envelope.payload.bid == Decimal("10.00")
        assert result.envelope.payload.bid.as_tuple().exponent == -2
        assert result.envelope.payload.last is MissingReason.NOT_PROVIDED
    else:
        assert isinstance(result.envelope.payload, Candle)
        assert result.envelope.payload.finality is CandleFinality.FINAL
        assert result.envelope.payload.volume is MissingReason.UNKNOWN
    with pytest.raises(FrozenInstanceError):
        result.raw = frame  # type: ignore[misc]


@pytest.mark.parametrize("reason", list(MissingReason))
def test_missingness_is_explicit_and_never_inferred(reason: MissingReason) -> None:
    data = document()
    missing = {"missing": reason.value}
    data["payload"] = {key: missing for key in ("bid", "ask", "last", "volume")}
    data["instrument_id"] = missing
    data["effective_time"] = missing
    data["event_time"] = {"value": missing, "basis": missing, "resolution_us": missing}
    result = decode(data)
    assert isinstance(result, Admitted)
    assert isinstance(result.envelope.payload, Tick)
    assert result.envelope.payload.bid is reason
    assert result.envelope.instrument_id is reason
    assert result.envelope.times.event_time.value is reason
    assert result.envelope.times.event_time.basis is reason
    assert result.envelope.times.event_time.resolution is reason
    assert result.envelope.times.effective_time is reason


def test_explicit_ids_sequence_and_candle_unknown_are_preserved() -> None:
    data = document(RawChannel.CANDLE)
    data.update(instrument_id={"uuid": UUID}, correlation_id=UUID, causation_id=UUID,
                external_event_id="external-01", source_sequence=0, sequence_scope="stream")
    data["payload"].update(finality="UNKNOWN", finalized_at={"missing": "UNKNOWN"},
                           available_at={"missing": "UNKNOWN"})
    result = decode(data, RawChannel.CANDLE)
    assert isinstance(result, Admitted)
    assert result.envelope.source_sequence == 0
    assert result.envelope.sequence_scope == "stream"
    assert result.envelope.correlation_id is not None
    assert result.envelope.causation_id is not None
    assert isinstance(result.envelope.payload, Candle)
    assert result.envelope.payload.finality is CandleFinality.UNKNOWN


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        (b"\xff\x00", RejectionReason.UTF8),
        (b"{", RejectionReason.JSON),
        (b"", RejectionReason.JSON),
        (b'{"duplicate": 1, "duplicate": 2}', RejectionReason.JSON),
        (b'{"payload": {"a": 1, "a": 2}}', RejectionReason.JSON),
        (b"NaN", RejectionReason.JSON),
        (b"Infinity", RejectionReason.JSON),
        (b"-Infinity", RejectionReason.JSON),
        (b"null", RejectionReason.SCHEMA),
        (b"[]", RejectionReason.SCHEMA),
        (b"[" * 10000 + b"]" * 10000, RejectionReason.JSON),
    ],
)
def test_corruption_is_structured_and_exact_raw_is_retained(
    payload: bytes, reason: RejectionReason
) -> None:
    frame = replace(raw(document()), payload=payload)
    context = ingress()
    result = admit_fixture(frame, context, max_payload_bytes=LIMIT)
    assert isinstance(result, Quarantined)
    assert result.raw is frame
    assert result.ingress is context
    assert result.raw.payload is payload
    assert result.reason is reason
    assert result.field == "$"


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, None])
def test_limit_must_be_explicit_positive_integer(limit: Any) -> None:
    with pytest.raises(ValueError, match="max_payload_bytes"):
        admit_fixture(raw(document()), ingress(), max_payload_bytes=limit)


def test_size_limit_precedes_utf8_parsing_and_never_drops_bytes() -> None:
    frame = replace(raw(document()), payload=b"\xff\xff")
    result = admit_fixture(frame, ingress(), max_payload_bytes=1)
    assert isinstance(result, Quarantined)
    assert result.reason is RejectionReason.PAYLOAD_TOO_LARGE
    assert result.raw is frame


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("schema_version",), True), (("schema_version",), 2),
        (("envelope_version",), 1.0), (("event_id",), "not-a-uuid"),
        (("event_type",), "ORDER"), (("source", "symbol"), "OTHER"),
        (("source", "scope"), "OTHER"), (("source", "provider"), "OTHER"),
        (("payload", "bid"), 10), (("payload", "bid"), None),
        (("payload", "bid"), {"decimal": 10}),
        (("payload", "volume"), {"decimal": "-1"}),
        (("payload", "bid"), {"decimal": "12"}),
        (("payload", "last"), {"missing": "ABSENT"}),
        (("instrument_id",), {"uuid": "invalid"}),
        (("event_time", "basis"), None),
        (("event_time", "resolution_us"), True),
        (("event_time", "resolution_us"), 0),
        (("event_time", "resolution_us"), 10**100),
        (("event_time", "value"), {"utc": "2026-09-13T12:00:00"}),
        (("event_time", "value"), {"utc": "2026-09-13T12:00:00.000000+00:00"}),
        (("event_time", "value"), {"utc": "2026-02-31T12:00:00.000000Z"}),
        (("source_sequence",), True), (("source_sequence",), -1),
        (("source_sequence",), 1), (("sequence_scope",), "orphan"),
        (("correlation_id",), "invalid"), (("causation_id",), 1),
        (("external_event_id",), " "),
    ],
)
def test_bad_fields_cannot_be_admitted(path: tuple[str, ...], value: Any) -> None:
    data = document()
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    result = decode(data)
    assert isinstance(result, Quarantined)
    assert result.field.startswith("$")


@pytest.mark.parametrize("text", [" 1", "1 ", "1_0", "NaN", "Infinity", "01", ".", "", "1e"])
def test_decimal_grammar_rejects_coercion(text: str) -> None:
    data = document()
    data["payload"]["bid"] = {"decimal": text}
    result = decode(data)
    assert isinstance(result, Quarantined)
    assert result.reason is RejectionReason.SCHEMA
    assert result.field == "$.payload.bid"


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("high", {"decimal": "8"}),
        ("interval_start", {"missing": "UNKNOWN"}),
        ("interval_end", {"utc": "2026-09-13T11:58:00.000000Z"}),
        ("finality", "INVALID"),
        ("available_at", {"utc": "2026-09-13T11:59:59.000000Z"}),
        ("finalized_at", {"utc": "2026-09-13T11:59:59.000000Z"}),
    ],
)
def test_invalid_candle_is_isolated(key: str, value: Any) -> None:
    data = document(RawChannel.CANDLE)
    data["payload"][key] = value
    assert isinstance(decode(data, RawChannel.CANDLE), Quarantined)


def test_exact_schema_prevents_missing_extra_or_internal_overrides() -> None:
    base = document()
    cases = []
    for field in base:
        item = deepcopy(base)
        del item[field]
        cases.append(item)
    for field in ("ingestion_time", "knowledge_time", "ingestion_order", "unknown-secret-text"):
        cases.append({**base, field: "not included in diagnostic"})
    for item in cases:
        result = decode(item)
        assert isinstance(result, Quarantined)
        assert result.reason is RejectionReason.SCHEMA
        assert result.field == "$"


def test_source_and_channel_mismatch_have_distinct_reasons() -> None:
    data = document()
    data["source"]["symbol"] = "another"
    mismatch = decode(data)
    assert isinstance(mismatch, Quarantined)
    assert mismatch.reason is RejectionReason.SOURCE_MISMATCH
    result = admit_fixture(raw(document(), RawChannel.CANDLE), ingress(), max_payload_bytes=LIMIT)
    assert isinstance(result, Quarantined)
    assert result.reason is RejectionReason.CHANNEL_MISMATCH


def test_invalid_ingress_is_a_caller_error_not_silently_rewritten() -> None:
    context = ingress()
    with pytest.raises(ValueError):
        replace(context, ingestion_time=context.ingestion_time.replace(tzinfo=None))
    with pytest.raises(ValueError):
        replace(context, knowledge_time=context.ingestion_time - timedelta(microseconds=1))
    with pytest.raises(ValueError):
        replace(context, ingestion_order=True)
    invalid: Any = None
    with pytest.raises(TypeError):
        admit_fixture(invalid, context, max_payload_bytes=LIMIT)
    with pytest.raises(TypeError):
        admit_fixture(raw(document()), invalid, max_payload_bytes=LIMIT)


def test_bad_frame_then_good_frame_continue_without_catch_all_or_mutation() -> None:
    bad = replace(raw(document()), payload=b"\xff")
    good = raw(document())
    descriptor = ProviderCapabilities(
        "fixture", "capture-A", CapabilitySupport.SUPPORTED, CapabilitySupport.SUPPORTED,
        CapabilitySupport.UNKNOWN, MissingReason.UNKNOWN, FidelityMode.UNKNOWN,
    )
    source = FixtureMarketDataSource(descriptor, [bad, good])
    first = source.read_next()
    assert first is bad
    result = admit_fixture(first, ingress(), max_payload_bytes=LIMIT)
    assert isinstance(result, Quarantined)
    assert result.raw is bad
    second = source.read_next()
    assert second is good
    accepted = admit_fixture(second, ingress(), max_payload_bytes=LIMIT)
    assert isinstance(accepted, Admitted)
    assert accepted.raw is good
    assert source.read_next() is None
