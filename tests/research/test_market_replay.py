"""Tests for the speculative Sprint 2 causal market replay schedule."""

import inspect
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from uuid import UUID

import pytest

import btg_ai_trader.research.market_replay as replay_module
from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.identity import (
    EventId,
    ProviderInstrumentRef,
    TradableInstrumentId,
)
from btg_ai_trader.observer.market import Tick
from btg_ai_trader.observer.temporal import EventTime, ObservationTimes
from btg_ai_trader.observer.values import MissingReason
from btg_ai_trader.research.market_replay import CausalMarketReplaySchedule, ReplayRate


def _utc(second: int, *, microsecond: int = 0) -> datetime:
    return datetime(2026, 1, 2, 10, 0, second, microsecond, tzinfo=UTC)


def _event(
    number: int,
    knowledge_time: datetime | MissingReason,
    *,
    provider: str = "fixture-provider",
    scope: str = "capture-a",
    symbol: str = "WINF26",
    event_id_number: int | None = None,
) -> EventEnvelope:
    event_number = number if event_id_number is None else event_id_number
    ingestion = _utc(number)
    event_time = EventTime(
        ingestion,
        "fixture-clock",
        timedelta(microseconds=1),
    )
    return EventEnvelope(
        event_id=EventId(str(UUID(int=event_number + 1))),
        event_type=EventType.TICK,
        source=ProviderInstrumentRef(provider, scope, symbol),
        instrument_id=TradableInstrumentId(str(UUID(int=10_000 + number))),
        times=ObservationTimes(
            event_time=event_time,
            ingestion_time=ingestion,
            knowledge_time=knowledge_time,
        ),
        payload=Tick(
            bid=Decimal("100.00"),
            ask=Decimal("100.50"),
            last=Decimal("100.25"),
            volume=Decimal("1"),
        ),
        ingestion_order=number,
    )


def _schedule(
    events: list[EventEnvelope],
    *,
    rate: ReplayRate | None = None,
) -> CausalMarketReplaySchedule:
    return CausalMarketReplaySchedule(
        events,
        provider="fixture-provider",
        capture_scope="capture-a",
        rate=ReplayRate(1, 1) if rate is None else rate,
    )


def test_empty_schedule_is_complete_and_emits_nothing() -> None:
    cursor = _schedule([]).cursor()
    assert cursor.complete is True
    assert cursor.emitted_count == 0
    assert cursor.advance_to(_utc(0)) == ()
    assert cursor.current_cutoff == _utc(0)


def test_schedule_copies_input_and_is_frozen() -> None:
    events = [
        _event(0, _utc(0), symbol="WINF26"),
        _event(1, _utc(1), symbol="WING26"),
    ]
    schedule = _schedule(events)
    events.append(_event(2, _utc(2), symbol="WINJ26"))

    assert [item.source.symbol for item in schedule.events] == ["WINF26", "WING26"]
    assert isinstance(schedule.events, tuple)
    assert schedule.provider == "fixture-provider"
    assert schedule.capture_scope == "capture-a"
    with pytest.raises(FrozenInstanceError):
        setattr(schedule, "provider", "mutated-provider")


def test_mixed_provider_or_capture_scope_is_rejected() -> None:
    with pytest.raises(ValueError, match="one provider/capture scope"):
        _schedule([_event(0, _utc(0)), _event(1, _utc(1), scope="capture-b")])

    with pytest.raises(ValueError, match="one provider/capture scope"):
        _schedule(
            [
                _event(0, _utc(0)),
                _event(1, _utc(1), provider="other-provider"),
            ]
        )


def test_unknown_knowledge_time_is_rejected_without_fallback() -> None:
    with pytest.raises(ValueError, match="known knowledge_time"):
        _schedule([_event(0, MissingReason.UNKNOWN)])


def test_knowledge_regression_is_rejected_instead_of_sorted() -> None:
    with pytest.raises(ValueError, match="knowledge-time causality"):
        _schedule([_event(0, _utc(2)), _event(1, _utc(1))])


def test_duplicate_event_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="repeat EventId"):
        _schedule(
            [
                _event(0, _utc(0), event_id_number=7),
                _event(1, _utc(1), event_id_number=7),
            ]
        )


def test_equal_knowledge_times_preserve_supplied_order() -> None:
    same_time = _utc(1)
    schedule = _schedule(
        [
            _event(0, same_time, symbol="WINF26"),
            _event(1, same_time, symbol="WING26"),
            _event(2, _utc(2), symbol="WINJ26"),
        ]
    )
    emissions = schedule.cursor().advance_to(same_time)

    assert [item.ordinal for item in emissions] == [0, 1]
    symbols = [item.envelope.source.symbol for item in emissions]
    assert symbols == ["WINF26", "WING26"]
    assert [item.source_delta_us for item in emissions] == [0, 0]


def test_cutoffs_are_inclusive_and_future_events_stay_hidden() -> None:
    schedule = _schedule(
        [
            _event(0, _utc(1)),
            _event(1, _utc(2)),
            _event(2, _utc(3)),
        ]
    )
    cursor = schedule.cursor()

    assert cursor.advance_to(_utc(0)) == ()
    at_first = cursor.advance_to(_utc(1))
    assert [item.ordinal for item in at_first] == [0]
    through_second = cursor.advance_to(_utc(2))
    assert [item.ordinal for item in through_second] == [1]
    assert cursor.complete is False
    final = cursor.advance_to(_utc(3))
    assert [item.ordinal for item in final] == [2]
    assert cursor.complete is True


def test_backward_cutoff_fails_without_mutating_cursor_state() -> None:
    cursor = _schedule([_event(0, _utc(1)), _event(1, _utc(2))]).cursor()
    first = cursor.advance_to(_utc(1))
    assert len(first) == 1
    assert cursor.emitted_count == 1
    assert cursor.current_cutoff == _utc(1)

    with pytest.raises(ValueError, match="cutoff must be monotonic"):
        cursor.advance_to(_utc(0))

    assert cursor.emitted_count == 1
    assert cursor.current_cutoff == _utc(1)
    second = cursor.advance_to(_utc(2))
    assert [item.ordinal for item in second] == [1]


def test_replay_rate_is_exact_rational_without_float_rounding() -> None:
    events = [
        _event(0, _utc(0)),
        _event(1, _utc(1)),
        _event(2, _utc(3)),
    ]

    one_x = _schedule(events, rate=ReplayRate(1, 1)).cursor().advance_to(_utc(3))
    two_x = _schedule(events, rate=ReplayRate(2, 1)).cursor().advance_to(_utc(3))
    half_x = _schedule(events, rate=ReplayRate(1, 2)).cursor().advance_to(_utc(3))

    assert [item.source_delta_us for item in one_x] == [0, 1_000_000, 2_000_000]
    assert [item.virtual_delay_us for item in one_x] == [
        Fraction(0, 1),
        Fraction(1_000_000, 1),
        Fraction(2_000_000, 1),
    ]
    assert [item.virtual_delay_us for item in two_x] == [
        Fraction(0, 1),
        Fraction(500_000, 1),
        Fraction(1_000_000, 1),
    ]
    assert [item.virtual_delay_us for item in half_x] == [
        Fraction(0, 1),
        Fraction(2_000_000, 1),
        Fraction(4_000_000, 1),
    ]


def test_sub_microsecond_rational_pacing_is_represented_exactly() -> None:
    rate = ReplayRate(3, 2)
    assert rate.virtual_delay_us(1) == Fraction(2, 3)
    assert rate.virtual_delay_us(2) == Fraction(4, 3)


def test_rate_and_cutoff_validation_fail_closed() -> None:
    for numerator, denominator in (
        (0, 1),
        (1, 0),
        (-1, 1),
        (1, -1),
        (True, 1),
    ):
        with pytest.raises(ValueError):
            ReplayRate(numerator, denominator)

    with pytest.raises(ValueError):
        ReplayRate(1, 1).virtual_delay_us(-1)

    cursor = _schedule([_event(0, _utc(0))]).cursor()
    with pytest.raises(ValueError, match="explicit UTC-aware"):
        cursor.advance_to(datetime(2026, 1, 2, 10, 0, 0))


def test_repeated_schedules_are_deterministic_for_same_inputs() -> None:
    events = [_event(0, _utc(0)), _event(1, _utc(1)), _event(2, _utc(2))]
    first = _schedule(events, rate=ReplayRate(5, 2)).cursor().advance_to(_utc(2))
    second = _schedule(events, rate=ReplayRate(5, 2)).cursor().advance_to(_utc(2))
    assert first == second


def test_module_has_no_wall_clock_sleep_or_financial_execution_surface() -> None:
    source = inspect.getsource(replay_module)
    assert "datetime.now(" not in source
    assert "sleep(" not in source
    assert "order_send" not in source
    assert "TradeIntent" not in source
    assert "RiskAuthorization" not in source
    assert "ExecutionOrder" not in source
    assert "Fill" not in source
    assert "Ledger" not in source
