"""Capability metadata only; no concrete provider, connection or execution interface."""

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Protocol

from btg_ai_trader.observer.values import MissingReason, require_text


class CapabilitySupport(Enum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


class FidelityMode(Enum):
    OBSERVATION_FAITHFUL = "OBSERVATION_FAITHFUL"
    SOURCE_SEQUENCE_FAITHFUL = "SOURCE_SEQUENCE_FAITHFUL"
    EVENT_TIME_ONLY = "EVENT_TIME_ONLY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    """Scoped source declarations, not verified guarantees or permission to trade."""

    provider: str
    capture_scope: str
    ticks: CapabilitySupport
    candles: CapabilitySupport
    source_sequence: CapabilitySupport
    timestamp_resolution: timedelta | MissingReason
    fidelity: FidelityMode
    sequence_scope: str | None = None

    def __post_init__(self) -> None:
        require_text(self.provider, "provider")
        require_text(self.capture_scope, "capture_scope")
        for field in ("ticks", "candles", "source_sequence"):
            if not isinstance(getattr(self, field), CapabilitySupport):
                raise ValueError(f"{field} must declare CapabilitySupport")
        if not isinstance(self.fidelity, FidelityMode):
            raise ValueError("fidelity must declare FidelityMode")
        if not isinstance(self.timestamp_resolution, MissingReason):
            if (
                not isinstance(self.timestamp_resolution, timedelta)
                or self.timestamp_resolution <= timedelta(0)
            ):
                raise ValueError("timestamp_resolution must be positive or explicitly missing")
        if self.source_sequence is CapabilitySupport.SUPPORTED:
            if self.sequence_scope is None:
                raise ValueError("supported source sequence requires its scope")
            require_text(self.sequence_scope, "sequence_scope")
        elif self.sequence_scope is not None:
            raise ValueError("unknown or unsupported sequence must not fabricate scope")
        if (
            self.fidelity is FidelityMode.SOURCE_SEQUENCE_FAITHFUL
            and self.source_sequence is not CapabilitySupport.SUPPORTED
        ):
            raise ValueError("source-sequence fidelity requires declared sequence support")


class ProviderMetadata(Protocol):
    """Only metadata discovery is universal; operations require specialized contracts."""

    def describe_capabilities(self) -> ProviderCapabilities:
        """Return explicit passive source metadata."""
        ...
