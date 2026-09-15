"""Passive XP/MT5 append-only file bridge; no terminal, account or execution API.

Legacy Rico-named symbols are retained temporarily as compatibility names. The active
provider identity is XP/MT5 under ADR-0026.
"""

from dataclasses import dataclass
from pathlib import Path

from btg_ai_trader.observer.identity import ProviderInstrumentRef
from btg_ai_trader.observer.provider import (
    CapabilitySupport,
    FidelityMode,
    ProviderCapabilities,
)
from btg_ai_trader.observer.raw_source import RawChannel, RawFrame
from btg_ai_trader.observer.values import MissingReason, require_text

XP_MT5_PROVIDER = "xp-mt5"
# Compatibility alias for legacy implementation names.
RICO_MT5_PROVIDER = XP_MT5_PROVIDER


class BridgeContinuityError(RuntimeError):
    """The append-only transport no longer preserves the reader's observed prefix."""


class BridgeRecordTooLargeError(RuntimeError):
    """A record exceeded the explicit passive transport bound."""


@dataclass(frozen=True, slots=True)
class RicoMt5BridgeSettings:
    """Local transport settings independent from any MT5 account or credential."""

    capture_scope: str
    symbol: str
    path: Path
    channel: RawChannel = RawChannel.TICK
    max_record_bytes: int = 16_384

    def __post_init__(self) -> None:
        require_text(self.capture_scope, "capture_scope")
        require_text(self.symbol, "symbol")
        if not isinstance(self.path, Path):
            raise TypeError("path must be pathlib.Path")
        if not isinstance(self.channel, RawChannel):
            raise TypeError("channel must be RawChannel")
        if type(self.max_record_bytes) is not int or self.max_record_bytes <= 0:
            raise ValueError("max_record_bytes must be an explicit positive integer")


class RicoMt5BridgeReader:
    """Read complete append-only records without importing or controlling MetaTrader 5."""

    __slots__ = ("_offset", "_reference", "_settings")

    def __init__(self, settings: RicoMt5BridgeSettings) -> None:
        if not isinstance(settings, RicoMt5BridgeSettings):
            raise TypeError("settings must be RicoMt5BridgeSettings")
        self._settings = settings
        self._reference = ProviderInstrumentRef(
            XP_MT5_PROVIDER,
            settings.capture_scope,
            settings.symbol,
        )
        self._offset = 0

    @property
    def offset(self) -> int:
        """Number of transport bytes already emitted as complete records."""
        return self._offset

    def describe_capabilities(self) -> ProviderCapabilities:
        """Declare offline bridge channels; runtime feed fidelity remains unknown."""
        return ProviderCapabilities(
            provider=XP_MT5_PROVIDER,
            capture_scope=self._settings.capture_scope,
            ticks=CapabilitySupport.SUPPORTED,
            candles=CapabilitySupport.SUPPORTED,
            source_sequence=CapabilitySupport.UNKNOWN,
            timestamp_resolution=MissingReason.UNKNOWN,
            fidelity=FidelityMode.UNKNOWN,
        )

    def poll_next(self) -> RawFrame | None:
        """Return one complete record, or None when no complete record is available yet."""
        try:
            with self._settings.path.open("rb") as source:
                source.seek(0, 2)
                size = source.tell()
                if size < self._offset:
                    raise BridgeContinuityError("bridge file shrank below consumed offset")
                if size == self._offset:
                    return None
                source.seek(self._offset)
                record = source.readline(self._settings.max_record_bytes + 2)
        except FileNotFoundError:
            if self._offset:
                raise BridgeContinuityError(
                    "bridge file disappeared after data was consumed"
                ) from None
            return None

        if not record.endswith(b"\n"):
            if len(record) > self._settings.max_record_bytes:
                raise BridgeRecordTooLargeError("bridge record exceeded max_record_bytes")
            return None
        if len(record) - 1 > self._settings.max_record_bytes:
            raise BridgeRecordTooLargeError("bridge record exceeded max_record_bytes")

        self._offset += len(record)
        return RawFrame(record, self._reference, self._settings.channel)
