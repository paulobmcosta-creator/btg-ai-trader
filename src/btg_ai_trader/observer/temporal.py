"""Separate occurrence, ingestion, knowledge and effective time without inference."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from btg_ai_trader.observer.values import MissingReason, require_text

type TemporalValue = datetime | MissingReason


def require_utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be an explicit UTC-aware datetime")


def require_temporal(value: TemporalValue, field: str) -> None:
    if isinstance(value, MissingReason):
        return
    require_utc(value, field)


@dataclass(frozen=True, slots=True)
class EventTime:
    """Source evidence; unknown basis/resolution remain explicitly unknown."""

    value: TemporalValue
    basis: str | MissingReason
    resolution: timedelta | MissingReason

    def __post_init__(self) -> None:
        require_temporal(self.value, "event_time")
        if not isinstance(self.basis, MissingReason):
            require_text(self.basis, "event_time_basis")
        if not isinstance(self.resolution, MissingReason):
            if not isinstance(self.resolution, timedelta) or self.resolution <= timedelta(0):
                raise ValueError("event_time_resolution must be positive or explicitly missing")


@dataclass(frozen=True, slots=True)
class ObservationTimes:
    """No clock reads, derived timestamps, or assumed ordering of these axes."""

    event_time: EventTime
    ingestion_time: datetime
    knowledge_time: TemporalValue
    effective_time: TemporalValue = MissingReason.NOT_APPLICABLE

    def __post_init__(self) -> None:
        if not isinstance(self.event_time, EventTime):
            raise ValueError("event_time must include source basis and resolution")
        require_utc(self.ingestion_time, "ingestion_time")
        require_temporal(self.knowledge_time, "knowledge_time")
        require_temporal(self.effective_time, "effective_time")
