"""S1-A semantic regression tests; fixtures are observations, never a runtime feed."""

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import cast

import pytest

from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.identity import (
    CorrelationId,
    EventId,
    InstrumentFamilyId,
    ProviderInstrumentRef,
    TradableInstrumentId,
)
from btg_ai_trader.observer.market import Candle, CandleFinality, Tick
from btg_ai_trader.observer.temporal import EventTime, ObservationTimes
from btg_ai_trader.observer.values import MissingReason, NumericValue

T0 = datetime(2026, 8, 20, 12, tzinfo=UTC)
UUID_TEXT = "8a849434-cfde-4f26-8110-6d2a211683c8"
MISSING = MissingReason.UNKNOWN


def tick() -> Tick:
    return Tick(Decimal("100.10"), Decimal("100.20"), MISSING, Decimal("0"))


def times() -> ObservationTimes:
    return ObservationTimes(
        EventTime(T0, "provider_timestamp", timedelta(milliseconds=1)),
        T0 + timedelta(seconds=2),
        T0 + timedelta(seconds=3),
        T0 + timedelta(seconds=1),
    )


def envelope() -> EventEnvelope:
    return EventEnvelope(
        EventId(UUID_TEXT),
        EventType.TICK,
        ProviderInstrumentRef("fixture", "capture-stream-a", "SYMBOL"),
        TradableInstrumentId(UUID_TEXT),
        times(),
        tick(),
    )


def candle() -> Candle:
    end = T0 + timedelta(minutes=1)
    return Candle(
        interval_start=T0,
        interval_end=end,
        finality=CandleFinality.FINAL,
        finalized_at=end + timedelta(seconds=1),
        available_at=end + timedelta(seconds=2),
        open=Decimal("100.1"),
        high=Decimal("100.3"),
        low=Decimal("100.0"),
        close=Decimal("100.2"),
        volume=MISSING,
    )


@pytest.mark.parametrize(
    "value", ["not-uuid", UUID_TEXT.upper(), UUID_TEXT.replace("-", ""), "", None, 123]
)
def test_identity_rejects_noncanonical_input(value: object) -> None:
    with pytest.raises(ValueError, match="identity"):
        EventId(cast(str, value))


def test_identity_types_and_provider_scopes_remain_distinct() -> None:
    family = InstrumentFamilyId(UUID_TEXT)
    concrete = TradableInstrumentId(UUID_TEXT)
    assert len({family, concrete, EventId(UUID_TEXT), CorrelationId(UUID_TEXT)}) == 4
    assert family.value == concrete.value == UUID_TEXT
    a = ProviderInstrumentRef("a", "stream", "SYMBOL")
    assert a != ProviderInstrumentRef("b", "stream", "SYMBOL")
    assert a != ProviderInstrumentRef("a", "other-stream", "SYMBOL")
    with pytest.raises(ValueError, match="instrument_id"):
        replace(envelope(), instrument_id=cast(TradableInstrumentId, family))


@pytest.mark.parametrize("bad", ["", " ", " trailing", "trailing ", None])
def test_provider_reference_rejects_ambiguous_text(bad: object) -> None:
    with pytest.raises(ValueError):
        ProviderInstrumentRef("fixture", cast(str, bad), "SYMBOL")


@pytest.mark.parametrize(
    "bad",
    [0.1, 0, True, "1.0", None, Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity")],
)
def test_numeric_values_reject_coercion_and_nonfinite_evidence(bad: object) -> None:
    with pytest.raises(ValueError, match="finite Decimal"):
        replace(tick(), last=cast(NumericValue, bad))


def test_decimal_precision_and_missingness_are_preserved() -> None:
    precise = Decimal("123456789012345678901234567890.123456789")
    observed = replace(tick(), last=precise)
    assert observed.last is precise
    assert observed.volume == Decimal("0")
    for reason in MissingReason:
        assert replace(observed, volume=reason).volume is reason
        assert len({reason, Decimal("0")}) == 2
    with pytest.raises(ValueError, match="negative"):
        replace(observed, volume=Decimal("-1"))
    with pytest.raises(ValueError, match="bid"):
        replace(observed, bid=Decimal("101"))


@pytest.mark.parametrize(
    "bad",
    [
        datetime(2026, 8, 20, 12),
        datetime(2026, 8, 20, 9, tzinfo=timezone(timedelta(hours=-3))),
        None,
    ],
)
def test_temporal_boundary_rejects_naive_or_nonutc_input(bad: object) -> None:
    with pytest.raises(ValueError, match="UTC"):
        replace(times(), ingestion_time=cast(datetime, bad))
    with pytest.raises(ValueError, match="UTC"):
        EventTime(cast(datetime, bad), MISSING, MISSING)


def test_temporal_axes_preserve_evidence_without_inference() -> None:
    observed = times()
    assert len(
        {
            observed.event_time.value,
            observed.ingestion_time,
            observed.knowledge_time,
            observed.effective_time,
        }
    ) == 4
    unknown = ObservationTimes(EventTime(MISSING, MISSING, MISSING), T0, MISSING)
    assert unknown.event_time.value is MISSING
    assert unknown.knowledge_time is MISSING
    # Equal instants remain legal: distinct semantics do not require unequal numbers.
    same = ObservationTimes(EventTime(T0, MISSING, MISSING), T0, T0, T0)
    assert same.knowledge_time == same.event_time.value


def test_time_precision_is_explicit_and_never_fabricated() -> None:
    observed = EventTime(T0, MISSING, MISSING)
    assert observed.basis is observed.resolution is MISSING
    with pytest.raises(ValueError, match="resolution"):
        replace(observed, resolution=timedelta(0))


@pytest.mark.parametrize("version", [0, 2, True, "1", None])
def test_envelope_rejects_unknown_versions_without_fallback(version: object) -> None:
    with pytest.raises(ValueError, match="unsupported"):
        replace(envelope(), envelope_version=cast(int, version))
    with pytest.raises(ValueError, match="unsupported"):
        replace(envelope(), schema_version=cast(int, version))


def test_exogenous_context_and_order_are_not_synthesized() -> None:
    event = envelope()
    assert event.correlation_id is None
    assert event.causation_id is None
    assert event.source_sequence is None
    assert event.sequence_scope is None
    assert event.ingestion_order is None
    assert "run_id" not in {field.name for field in fields(event)}
    with pytest.raises(ValueError, match="together"):
        replace(event, source_sequence=5)
    with pytest.raises(ValueError, match="together"):
        replace(event, sequence_scope="stream")
    first = replace(event, source_sequence=5, sequence_scope="provider/connection-a")
    second = replace(event, source_sequence=5, sequence_scope="provider/connection-b")
    assert first != second
    assert first.times == second.times == event.times


@pytest.mark.parametrize("bad", [-1, True, 1.5, "1"])
def test_sequence_and_arrival_index_are_strict(bad: object) -> None:
    with pytest.raises(ValueError, match="source_sequence"):
        replace(envelope(), source_sequence=cast(int, bad), sequence_scope="stream")
    with pytest.raises(ValueError, match="ingestion_order"):
        replace(envelope(), ingestion_order=cast(int, bad))


def test_envelope_validates_payload_type_and_identity_roles() -> None:
    with pytest.raises(ValueError, match="payload"):
        replace(envelope(), payload=candle())
    with pytest.raises(ValueError, match="payload"):
        replace(envelope(), payload=cast(Tick, {"mutable": "payload"}))
    with pytest.raises(ValueError, match="correlation_id"):
        replace(envelope(), correlation_id=cast(CorrelationId, EventId(UUID_TEXT)))
    event = replace(envelope(), correlation_id=CorrelationId(UUID_TEXT))
    assert event.correlation_id == CorrelationId(UUID_TEXT)


def test_candle_interval_finality_and_availability_are_distinct() -> None:
    observed = candle()
    assert observed.interval_end != observed.finalized_at != observed.available_at
    # An open update can be available before the interval ends, without finality.
    current = replace(
        observed,
        finality=CandleFinality.OPEN,
        finalized_at=MISSING,
        available_at=T0 + timedelta(seconds=10),
    )
    assert current.finalized_at is MISSING
    assert current.available_at != current.interval_end
    unknown = replace(observed, finality=CandleFinality.UNKNOWN, finalized_at=MISSING)
    assert unknown.finalized_at is MISSING


def test_candle_rejects_contradictory_evidence_without_repair() -> None:
    observed = candle()
    for changes in (
        {"interval_end": T0},
        {"finalized_at": T0},
        {"finality": CandleFinality.OPEN},
        {"high": Decimal("99")},
        {"low": Decimal("101")},
        {"volume": Decimal("-1")},
    ):
        with pytest.raises(ValueError):
            replace(observed, **changes)
    assert observed == candle()


def test_frozen_value_objects_preserve_original_observation() -> None:
    original = envelope()
    field_name = "source_sequence"
    with pytest.raises(FrozenInstanceError):
        setattr(original, field_name, 1)
    field_name = "volume"
    with pytest.raises(FrozenInstanceError):
        setattr(original.payload, field_name, Decimal("100"))
    corrected = replace(
        original,
        event_id=EventId("8a849434-cfde-4f26-8110-6d2a211683c9"),
        payload=replace(tick(), last=Decimal("100.15")),
    )
    assert original.payload == tick()
    assert corrected != original


def test_internal_knowledge_cannot_precede_ingestion() -> None:
    with pytest.raises(ValueError, match="knowledge_time.*ingestion_time"):
        replace(times(), knowledge_time=T0 + timedelta(seconds=1))
    observed = replace(times(), knowledge_time=times().ingestion_time)
    assert observed.knowledge_time == observed.ingestion_time
    for reason in MissingReason:
        assert replace(times(), knowledge_time=reason).knowledge_time is reason


def test_final_candle_cannot_be_available_before_interval_end() -> None:
    observed = candle()
    with pytest.raises(ValueError, match="availability.*interval end"):
        replace(
            observed,
            finalized_at=MISSING,
            available_at=observed.interval_end - timedelta(microseconds=1),
        )
    # Even without a finalization timestamp, interval end remains a known lower bound.
    boundary = replace(observed, finalized_at=MISSING, available_at=observed.interval_end)
    assert boundary.available_at == boundary.interval_end
    assert boundary.finalized_at is MISSING


def test_final_candle_cannot_be_available_before_known_finalization() -> None:
    observed = candle()
    with pytest.raises(ValueError, match="availability.*finalization"):
        replace(observed, available_at=observed.interval_end)
    boundary = replace(observed, available_at=observed.finalized_at)
    assert boundary.available_at == boundary.finalized_at
    simultaneous = replace(
        observed, finalized_at=observed.interval_end, available_at=observed.interval_end
    )
    assert simultaneous.finalized_at == simultaneous.available_at == simultaneous.interval_end


def test_final_candle_unknown_availability_is_not_inferred() -> None:
    for reason in MissingReason:
        observed = replace(candle(), available_at=reason)
        assert observed.available_at is reason
        assert observed.finalized_at == candle().finalized_at
    both_unknown = replace(candle(), finalized_at=MISSING, available_at=MISSING)
    assert both_unknown.finalized_at is MISSING
    assert both_unknown.available_at is MISSING
