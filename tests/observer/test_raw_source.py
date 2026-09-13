"""Raw fixture preservation and declared capability boundary regressions."""

from dataclasses import FrozenInstanceError, replace
from typing import Any

import pytest

from btg_ai_trader.observer.identity import ProviderInstrumentRef
from btg_ai_trader.observer.provider import (
    CapabilitySupport,
    FidelityMode,
    ProviderCapabilities,
)
from btg_ai_trader.observer.raw_source import (
    FixtureMarketDataSource,
    RawChannel,
    RawFrame,
    RawMarketDataSource,
)
from btg_ai_trader.observer.values import MissingReason


def capabilities() -> ProviderCapabilities:
    return ProviderCapabilities(
        "fixture", "capture-A", CapabilitySupport.SUPPORTED, CapabilitySupport.SUPPORTED,
        CapabilitySupport.UNKNOWN, MissingReason.UNKNOWN, FidelityMode.UNKNOWN,
    )


def frame(channel: RawChannel = RawChannel.TICK, symbol: str = "RaW") -> RawFrame:
    return RawFrame(b"\xff\x00not valid market data\r\n", ProviderInstrumentRef(
        "fixture", "capture-A", symbol
    ), channel)


def test_protocol_preserves_bytes_order_repetitions_symbols_and_exhaustion() -> None:
    first = frame()
    second = frame(RawChannel.CANDLE, "OTHER")
    descriptor = capabilities()
    inputs = [first, second, first]
    source: RawMarketDataSource = FixtureMarketDataSource(descriptor, inputs)
    inputs.clear()
    assert source.describe_capabilities() is descriptor
    assert source.read_next() is first
    assert source.read_next() is second
    assert source.read_next() is first
    assert source.read_next() is None
    assert source.read_next() is None
    assert first.payload == b"\xff\x00not valid market data\r\n"
    assert first.reference.symbol == "RaW"
    with pytest.raises(FrozenInstanceError):
        first.payload = b"changed"  # type: ignore[misc]


def test_empty_bytes_remain_raw_and_do_not_mean_exhaustion() -> None:
    empty = replace(frame(), payload=b"")
    source = FixtureMarketDataSource(capabilities(), (item for item in [empty]))
    assert source.read_next() is empty
    assert source.read_next() is None


def test_empty_fixture_does_not_require_an_unsupported_channel() -> None:
    descriptor = replace(
        capabilities(), ticks=CapabilitySupport.UNKNOWN, candles=CapabilitySupport.UNSUPPORTED
    )
    source = FixtureMarketDataSource(descriptor, [])
    assert source.describe_capabilities() is descriptor
    assert source.read_next() is None
    assert source.read_next() is None


@pytest.mark.parametrize("channel", list(RawChannel))
@pytest.mark.parametrize("support", [CapabilitySupport.UNKNOWN, CapabilitySupport.UNSUPPORTED])
def test_channel_requires_positive_capability(
    channel: RawChannel, support: CapabilitySupport
) -> None:
    descriptor = capabilities()
    if channel is RawChannel.TICK:
        descriptor = replace(descriptor, ticks=support)
    else:
        descriptor = replace(descriptor, candles=support)
    with pytest.raises(ValueError, match="SUPPORTED"):
        FixtureMarketDataSource(descriptor, [frame(channel)])


@pytest.mark.parametrize(
    "reference",
    [
        ProviderInstrumentRef("other", "capture-A", "RaW"),
        ProviderInstrumentRef("fixture", "other", "RaW"),
    ],
)
def test_scope_cannot_escape_descriptor(reference: ProviderInstrumentRef) -> None:
    with pytest.raises(ValueError, match="scope"):
        FixtureMarketDataSource(capabilities(), [replace(frame(), reference=reference)])


@pytest.mark.parametrize("payload", ["text", bytearray(b"raw"), memoryview(b"raw"), None, 12])
def test_payload_requires_actual_immutable_bytes(payload: Any) -> None:
    with pytest.raises(TypeError, match="bytes"):
        replace(frame(), payload=payload)


@pytest.mark.parametrize("channel", ["TICK", "CANDLE", None, 1])
def test_channel_label_requires_enum(channel: Any) -> None:
    with pytest.raises(TypeError, match="channel"):
        replace(frame(), channel=channel)


def test_untyped_reference_descriptor_and_late_invalid_frame_are_rejected() -> None:
    invalid: Any = "untyped"
    with pytest.raises(TypeError, match="reference"):
        replace(frame(), reference=invalid)
    with pytest.raises(TypeError, match="Capabilities"):
        FixtureMarketDataSource(invalid, [])
    items = [frame(), invalid]
    with pytest.raises(TypeError, match="RawFrame"):
        FixtureMarketDataSource(capabilities(), items)
    assert len(items) == 2


def test_instances_consume_independent_cursors_without_normalization() -> None:
    raw = frame()
    first = FixtureMarketDataSource(capabilities(), [raw])
    second = FixtureMarketDataSource(capabilities(), [raw])
    assert first.read_next() is raw
    assert first.read_next() is None
    assert second.read_next() is raw
    assert second.read_next() is None
