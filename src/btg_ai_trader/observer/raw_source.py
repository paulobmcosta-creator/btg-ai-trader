"""Finite raw fixture source; channel declarations do not validate payloads."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from btg_ai_trader.observer.identity import ProviderInstrumentRef
from btg_ai_trader.observer.provider import (
    CapabilitySupport,
    ProviderCapabilities,
    ProviderMetadata,
)


class RawChannel(Enum):
    TICK = "TICK"
    CANDLE = "CANDLE"


@dataclass(frozen=True, slots=True)
class RawFrame:
    """Untouched source bytes and scoped routing metadata, without invented identity/time."""

    payload: bytes
    reference: ProviderInstrumentRef
    channel: RawChannel

    def __post_init__(self) -> None:
        if type(self.payload) is not bytes:
            raise TypeError("raw payload must be immutable bytes")
        if not isinstance(self.reference, ProviderInstrumentRef):
            raise TypeError("raw reference must be ProviderInstrumentRef")
        if not isinstance(self.channel, RawChannel):
            raise TypeError("raw channel must be RawChannel")


class RawMarketDataSource(ProviderMetadata, Protocol):
    """Specialized finite fixture read contract; no connection or execution operations."""

    def read_next(self) -> RawFrame | None:
        """Consume one raw frame; None denotes exhaustion, never market health."""
        ...


class FixtureMarketDataSource:
    """Single-consumer deterministic fixture; supplied order and duplicates are preserved."""

    __slots__ = ("_capabilities", "_frames", "_position")

    def __init__(
        self, capabilities: ProviderCapabilities, frames: Iterable[RawFrame]
    ) -> None:
        if not isinstance(capabilities, ProviderCapabilities):
            raise TypeError("explicit ProviderCapabilities required")
        copied = tuple(frames)
        for frame in copied:
            if not isinstance(frame, RawFrame):
                raise TypeError("fixture requires RawFrame records")
            if (
                frame.reference.provider != capabilities.provider
                or frame.reference.scope != capabilities.capture_scope
            ):
                raise ValueError("frame provider/capture scope differs from descriptor")
            support = (
                capabilities.ticks if frame.channel is RawChannel.TICK else capabilities.candles
            )
            if support is not CapabilitySupport.SUPPORTED:
                raise ValueError("frame channel requires explicitly SUPPORTED capability")
        self._capabilities = capabilities
        self._frames = copied
        self._position = 0

    def describe_capabilities(self) -> ProviderCapabilities:
        return self._capabilities

    def read_next(self) -> RawFrame | None:
        if self._position == len(self._frames):
            return None
        frame = self._frames[self._position]
        self._position += 1
        return frame
