"""Bounded fixture JSON admission; receipts preserve original raw evidence."""

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import cast

from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.identity import (
    CorrelationId,
    EventId,
    ProviderInstrumentRef,
    TradableInstrumentId,
)
from btg_ai_trader.observer.market import Candle, CandleFinality, Tick
from btg_ai_trader.observer.raw_source import RawFrame
from btg_ai_trader.observer.temporal import (
    EventTime,
    ObservationTimes,
    TemporalValue,
    require_temporal,
    require_utc,
)
from btg_ai_trader.observer.values import MissingReason, NumericValue, require_text


class RejectionReason(Enum):
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    UTF8 = "UTF8"
    JSON = "JSON"
    SCHEMA = "SCHEMA"
    DOMAIN = "DOMAIN"
    SOURCE_MISMATCH = "SOURCE_MISMATCH"
    CHANNEL_MISMATCH = "CHANNEL_MISMATCH"


@dataclass(frozen=True, slots=True)
class IngressMetadata:
    ingestion_time: datetime
    knowledge_time: TemporalValue
    ingestion_order: int | None

    def __post_init__(self) -> None:
        require_utc(self.ingestion_time, "ingestion_time")
        require_temporal(self.knowledge_time, "knowledge_time")
        if (
            isinstance(self.knowledge_time, datetime)
            and self.knowledge_time < self.ingestion_time
        ):
            raise ValueError("internal knowledge must not precede ingestion")
        if self.ingestion_order is not None and (
            type(self.ingestion_order) is not int or self.ingestion_order < 0
        ):
            raise ValueError("ingestion_order must be nonnegative integer or None")


@dataclass(frozen=True, slots=True)
class Admitted:
    raw: RawFrame
    ingress: IngressMetadata
    envelope: EventEnvelope


@dataclass(frozen=True, slots=True)
class Quarantined:
    raw: RawFrame
    ingress: IngressMetadata
    reason: RejectionReason
    field: str


class _DecodeError(ValueError):
    def __init__(self, field: str, reason: RejectionReason = RejectionReason.SCHEMA) -> None:
        super().__init__(field)
        self.field = field
        self.reason = reason


_ROOT_KEYS = {
    "envelope_version", "schema_version", "event_id", "event_type", "source",
    "instrument_id", "event_time", "effective_time", "payload", "external_event_id",
    "source_sequence", "sequence_scope", "correlation_id", "causation_id",
}
_DECIMAL = re.compile(r"[+-]?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?")
_UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z")


def _object(value: object, keys: set[str], field: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise _DecodeError(field)
    return cast(dict[str, object], value)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise _DecodeError(field)
    try:
        require_text(value, field)
    except ValueError:
        raise _DecodeError(field) from None
    return value


def _missing(value: object, field: str) -> MissingReason | None:
    if isinstance(value, dict) and set(value) == {"missing"}:
        text = _text(value["missing"], field)
        try:
            return MissingReason(text)
        except ValueError:
            raise _DecodeError(field) from None
    return None


def _number(value: object, field: str) -> NumericValue:
    missing = _missing(value, field)
    if missing is not None:
        return missing
    data = _object(value, {"decimal"}, field)
    text = _text(data["decimal"], field)
    if _DECIMAL.fullmatch(text) is None:
        raise _DecodeError(field)
    try:
        number = Decimal(text)
    except InvalidOperation:
        raise _DecodeError(field) from None
    if not number.is_finite():
        raise _DecodeError(field)
    return number


def _known_time(value: object, field: str) -> datetime:
    data = _object(value, {"utc"}, field)
    text = _text(data["utc"], field)
    if _UTC.fullmatch(text) is None:
        raise _DecodeError(field)
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
    except ValueError:
        raise _DecodeError(field) from None


def _time(value: object, field: str) -> TemporalValue:
    missing = _missing(value, field)
    return missing if missing is not None else _known_time(value, field)


def _event_time(value: object) -> EventTime:
    data = _object(value, {"value", "basis", "resolution_us"}, "$.event_time")
    missing_basis = _missing(data["basis"], "$.event_time.basis")
    basis: str | MissingReason
    if missing_basis is not None:
        basis = missing_basis
    else:
        tagged = _object(data["basis"], {"text"}, "$.event_time.basis")
        basis = _text(tagged["text"], "$.event_time.basis")
    missing_resolution = _missing(data["resolution_us"], "$.event_time.resolution_us")
    resolution: timedelta | MissingReason
    if missing_resolution is not None:
        resolution = missing_resolution
    else:
        value_us = data["resolution_us"]
        if type(value_us) is not int or value_us <= 0:
            raise _DecodeError("$.event_time.resolution_us")
        try:
            resolution = timedelta(microseconds=value_us)
        except OverflowError:
            raise _DecodeError("$.event_time.resolution_us") from None
    return EventTime(_time(data["value"], "$.event_time.value"), basis, resolution)


def _optional_text(value: object, field: str) -> str | None:
    return None if value is None else _text(value, field)


def _optional_counter(value: object, field: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value < 0:
        raise _DecodeError(field)
    return value


def _payload(value: object, event_type: EventType) -> Tick | Candle:
    if event_type is EventType.TICK:
        data = _object(value, {"bid", "ask", "last", "volume"}, "$.payload")
        return Tick(*(_number(data[key], f"$.payload.{key}") for key in (
            "bid", "ask", "last", "volume"
        )))
    data = _object(value, {
        "interval_start", "interval_end", "finality", "finalized_at", "available_at",
        "open", "high", "low", "close", "volume",
    }, "$.payload")
    finality_text = _text(data["finality"], "$.payload.finality")
    try:
        finality = CandleFinality(finality_text)
    except ValueError:
        raise _DecodeError("$.payload.finality") from None
    return Candle(
        _known_time(data["interval_start"], "$.payload.interval_start"),
        _known_time(data["interval_end"], "$.payload.interval_end"),
        finality,
        _time(data["finalized_at"], "$.payload.finalized_at"),
        _time(data["available_at"], "$.payload.available_at"),
        *(_number(data[key], f"$.payload.{key}") for key in (
            "open", "high", "low", "close", "volume"
        )),
    )


def _envelope(value: object, frame: RawFrame, ingress: IngressMetadata) -> EventEnvelope:
    data = _object(value, _ROOT_KEYS, "$")
    for key in ("envelope_version", "schema_version"):
        if type(data[key]) is not int or data[key] != 1:
            raise _DecodeError(f"$.{key}")
    source_data = _object(data["source"], {"provider", "scope", "symbol"}, "$.source")
    source = ProviderInstrumentRef(*(
        _text(source_data[key], f"$.source.{key}") for key in ("provider", "scope", "symbol")
    ))
    if source != frame.reference:
        raise _DecodeError("$.source", RejectionReason.SOURCE_MISMATCH)
    event_text = _text(data["event_type"], "$.event_type")
    try:
        event_type = EventType(event_text)
    except ValueError:
        raise _DecodeError("$.event_type") from None
    if event_type.value != frame.channel.value:
        raise _DecodeError("$.event_type", RejectionReason.CHANNEL_MISMATCH)
    instrument_missing = _missing(data["instrument_id"], "$.instrument_id")
    instrument: TradableInstrumentId | MissingReason
    if instrument_missing is not None:
        instrument = instrument_missing
    else:
        tagged = _object(data["instrument_id"], {"uuid"}, "$.instrument_id")
        instrument = TradableInstrumentId(_text(tagged["uuid"], "$.instrument_id"))
    correlation = _optional_text(data["correlation_id"], "$.correlation_id")
    causation = _optional_text(data["causation_id"], "$.causation_id")
    return EventEnvelope(
        event_id=EventId(_text(data["event_id"], "$.event_id")),
        event_type=event_type,
        source=source,
        instrument_id=instrument,
        times=ObservationTimes(
            _event_time(data["event_time"]), ingress.ingestion_time,
            ingress.knowledge_time, _time(data["effective_time"], "$.effective_time"),
        ),
        payload=_payload(data["payload"], event_type),
        external_event_id=_optional_text(data["external_event_id"], "$.external_event_id"),
        source_sequence=_optional_counter(data["source_sequence"], "$.source_sequence"),
        sequence_scope=_optional_text(data["sequence_scope"], "$.sequence_scope"),
        ingestion_order=ingress.ingestion_order,
        correlation_id=None if correlation is None else CorrelationId(correlation),
        causation_id=None if causation is None else EventId(causation),
    )


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DecodeError("$", RejectionReason.JSON)
        result[key] = value
    return result


def _invalid_constant(value: str) -> object:
    raise _DecodeError("$", RejectionReason.JSON)


def admit_fixture(
    frame: RawFrame, ingress: IngressMetadata, *, max_payload_bytes: int
) -> Admitted | Quarantined:
    """Decode one fixture; return evidence instead of swallowing unrelated failures."""
    if not isinstance(frame, RawFrame) or not isinstance(ingress, IngressMetadata):
        raise TypeError("typed raw frame and ingress metadata required")
    if type(max_payload_bytes) is not int or max_payload_bytes <= 0:
        raise ValueError("max_payload_bytes must be an explicit positive integer")
    if len(frame.payload) > max_payload_bytes:
        return Quarantined(frame, ingress, RejectionReason.PAYLOAD_TOO_LARGE, "$")
    try:
        text = frame.payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return Quarantined(frame, ingress, RejectionReason.UTF8, "$")
    try:
        value: object = json.loads(
            text, object_pairs_hook=_unique_object, parse_constant=_invalid_constant
        )
    except _DecodeError as error:
        return Quarantined(frame, ingress, error.reason, error.field)
    except (ValueError, RecursionError):
        return Quarantined(frame, ingress, RejectionReason.JSON, "$")
    try:
        envelope = _envelope(value, frame, ingress)
    except _DecodeError as error:
        return Quarantined(frame, ingress, error.reason, error.field)
    except ValueError:
        return Quarantined(frame, ingress, RejectionReason.DOMAIN, "$")
    return Admitted(frame, ingress, envelope)
