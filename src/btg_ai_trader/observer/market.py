"""Observed values only; these objects confer no execution or liquidity authority."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum

from btg_ai_trader.observer.temporal import TemporalValue, require_temporal, require_utc
from btg_ai_trader.observer.values import NumericValue, require_numeric


@dataclass(frozen=True, slots=True)
class Tick:
    """A reported observation, including explicit missing source fields."""

    bid: NumericValue
    ask: NumericValue
    last: NumericValue
    volume: NumericValue

    def __post_init__(self) -> None:
        require_numeric(self.bid, "bid")
        require_numeric(self.ask, "ask")
        require_numeric(self.last, "last")
        require_numeric(self.volume, "volume", quantity=True)
        if isinstance(self.bid, Decimal) and isinstance(self.ask, Decimal) and self.bid > self.ask:
            raise ValueError("observed bid must not exceed observed ask")


class CandleFinality(Enum):
    OPEN = "OPEN"
    FINAL = "FINAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class Candle:
    """Interval, source finality and availability are separate evidence fields."""

    interval_start: datetime
    interval_end: datetime
    finality: CandleFinality
    finalized_at: TemporalValue
    available_at: TemporalValue
    open: NumericValue
    high: NumericValue
    low: NumericValue
    close: NumericValue
    volume: NumericValue

    def __post_init__(self) -> None:
        require_utc(self.interval_start, "interval_start")
        require_utc(self.interval_end, "interval_end")
        if self.interval_end <= self.interval_start:
            raise ValueError("candle interval must have positive duration")
        if not isinstance(self.finality, CandleFinality):
            raise ValueError("finality must be explicit CandleFinality")
        require_temporal(self.finalized_at, "finalized_at")
        require_temporal(self.available_at, "available_at")
        if isinstance(self.finalized_at, datetime):
            if self.finality is not CandleFinality.FINAL:
                raise ValueError("known finalization time requires FINAL evidence")
            if self.finalized_at < self.interval_end:
                raise ValueError("candle cannot finalize before its interval ends")
        for field in ("open", "high", "low", "close"):
            require_numeric(getattr(self, field), field)
        require_numeric(self.volume, "volume", quantity=True)
        known = [v for v in (self.open, self.high, self.low, self.close) if isinstance(v, Decimal)]
        if isinstance(self.low, Decimal) and any(v < self.low for v in known):
            raise ValueError("observed OHLC value lies below low")
        if isinstance(self.high, Decimal) and any(v > self.high for v in known):
            raise ValueError("observed OHLC value lies above high")
