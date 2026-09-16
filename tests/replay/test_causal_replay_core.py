"""Comprehensive unit and property tests for Causal Replay Core (S2-A)."""

import inspect
from collections.abc import Iterable
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from uuid import UUID

import pytest

import btg_ai_trader.replay.core as replay_module
from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.identity import (
    EventId,
    ProviderInstrumentRef,
    RunId,
    TradableInstrumentId,
)
from btg_ai_trader.observer.market import Tick
from btg_ai_trader.observer.provenance import (
    CodeRevision,
    ConfigHash,
    ContentHash,
    InputIdentity,
    RunManifest,
)
from btg_ai_trader.observer.temporal import EventTime, ObservationTimes
from btg_ai_trader.observer.values import MissingReason
from btg_ai_trader.replay import (
    CausalLane,
    CausalMarketReplayCursor,
    CausalMarketReplaySchedule,
    ReplayEmission,
    ReplayEmissionLineage,
    ReplayInputBoundary,
    ReplayRate,
    ReplaySpeed,
    RunInputBoundary,
)

TEST_RUN_ID = RunId("00000000-0000-0000-0000-000000000001")
TEST_CODE_REVISION = CodeRevision("00cc56100d5c9a7cb28a34947726eb32bdfab8fd")
TEST_CONFIG_HASH = ConfigHash("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")


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
    events: Iterable[EventEnvelope],
    *,
    provider_id: str | None = "fixture-provider",
    capture_scope: str | None = "capture-a",
    speed: ReplaySpeed | None = None,
    rate: ReplaySpeed | None = None,
    boundary: ReplayInputBoundary | None = None,
    run_id: RunId | None = None,
    code_revision: CodeRevision | None = None,
    config_hash: ConfigHash | None = None,
    content_hashes: Iterable[ContentHash | None] | None = None,
    temporal_semantics: str = "knowledge_time_v1",
) -> CausalMarketReplaySchedule:
    return CausalMarketReplaySchedule(
        events,
        boundary=boundary,
        run_id=run_id or (TEST_RUN_ID if boundary is None else None),
        code_revision=code_revision or (TEST_CODE_REVISION if boundary is None else None),
        config_hash=config_hash or (TEST_CONFIG_HASH if boundary is None else None),
        provider_id=provider_id,
        capture_scope=capture_scope,
        speed=speed,
        rate=rate,
        content_hashes=content_hashes,
        temporal_semantics=temporal_semantics,
    )


# 1. Empty schedule
def test_empty_schedule_is_complete_and_emits_nothing() -> None:
    schedule = _schedule([])
    cursor = schedule.cursor()
    assert cursor.schedule is schedule
    assert cursor.complete is True
    assert cursor.emitted_count == 0
    assert cursor.remaining_count == 0
    assert len(schedule) == 0
    assert schedule.instruments == ()
    assert schedule.start_knowledge_time is None
    assert schedule.end_knowledge_time is None
    assert cursor.advance_to(_utc(0)) == ()
    assert cursor.current_cutoff == _utc(0)
    assert cursor.complete is True


# 2. Defensive input capture / immutability
def test_defensive_input_capture_and_immutability() -> None:
    events = [
        _event(0, _utc(0), symbol="WINF26"),
        _event(1, _utc(1), symbol="WING26"),
    ]
    schedule = _schedule(events)
    events.append(_event(2, _utc(2), symbol="WINJ26"))

    assert len(schedule) == 2
    assert [schedule[i].source.symbol for i in range(len(schedule))] == ["WINF26", "WING26"]
    assert schedule.instruments == ("WINF26", "WING26")
    assert schedule.start_knowledge_time == _utc(0)
    assert schedule.end_knowledge_time == _utc(1)
    assert isinstance(schedule.events, tuple)
    assert schedule.provider == "fixture-provider"
    assert schedule.provider_id == "fixture-provider"
    assert schedule.capture_scope == "capture-a"
    assert schedule.lane == CausalLane("fixture-provider", "capture-a")

    with pytest.raises(FrozenInstanceError):
        schedule.provider = "mutated-provider"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        schedule.provider_id = "mutated-provider"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        schedule.lane.provider_id = "mutated-provider"  # type: ignore[misc]


# 3. Multiple instruments in same lane
def test_multiple_instruments_in_same_lane() -> None:
    events = [
        _event(0, _utc(0), symbol="WINF26"),
        _event(1, _utc(1), symbol="WING26"),
        _event(2, _utc(2), symbol="WDOH26"),
    ]
    schedule = _schedule(events)
    assert schedule.instruments == ("WDOH26", "WINF26", "WING26")

    emissions = schedule.cursor().advance_to(_utc(2))
    assert len(emissions) == 3
    assert [e.symbol for e in emissions] == ["WINF26", "WING26", "WDOH26"]
    assert [e.ordinal for e in emissions] == [0, 1, 2]
    assert [e.event_id for e in emissions] == [
        events[0].event_id,
        events[1].event_id,
        events[2].event_id,
    ]


# 4. Mixed provider rejection
def test_mixed_provider_rejection() -> None:
    with pytest.raises(ValueError, match="mixed provider"):
        _schedule([
            _event(0, _utc(0), provider="fixture-provider"),
            _event(1, _utc(1), provider="other-provider"),
        ])


# 5. Mixed capture-scope rejection
def test_mixed_capture_scope_rejection() -> None:
    with pytest.raises(ValueError, match="mixed capture scope"):
        _schedule([
            _event(0, _utc(0), scope="capture-a"),
            _event(1, _utc(1), scope="capture-b"),
        ])


# 6. Missing / unknown / naive required knowledge-time rejection
def test_missing_unknown_or_naive_knowledge_time_rejection() -> None:
    for reason in (
        MissingReason.UNKNOWN,
        MissingReason.NOT_APPLICABLE,
        MissingReason.NOT_PROVIDED,
    ):
        with pytest.raises(ValueError, match="known, timezone-aware knowledge_time"):
            _schedule([_event(0, reason)])

    # Naive datetime (no tzinfo)
    naive_dt = datetime(2026, 1, 2, 10, 0, 0)
    with pytest.raises(ValueError, match="explicit UTC-aware"):
        _schedule([_event(0, naive_dt)])

    # Non-UTC timezone
    non_utc_dt = datetime(2026, 1, 2, 10, 0, 0, tzinfo=timezone(timedelta(hours=-3)))
    with pytest.raises(ValueError, match="explicit UTC-aware"):
        _schedule([_event(0, non_utc_dt)])


# 7. Knowledge-time regression rejection
def test_knowledge_time_regression_rejected_without_sorting() -> None:
    with pytest.raises(ValueError, match="knowledge-time regression rejected"):
        _schedule([_event(0, _utc(2)), _event(1, _utc(1))])


# 8. Duplicate EventId rejection
def test_duplicate_event_id_rejection() -> None:
    with pytest.raises(ValueError, match="duplicate EventId rejected"):
        _schedule([
            _event(0, _utc(0), event_id_number=42),
            _event(1, _utc(1), event_id_number=42),
        ])


# 9. Equal knowledge time preserving supplied order
def test_equal_knowledge_times_preserve_supplied_order() -> None:
    same_time = _utc(1)
    schedule = _schedule([
        _event(0, same_time, symbol="WINF26"),
        _event(1, same_time, symbol="WING26"),
        _event(2, _utc(2), symbol="WINJ26"),
    ])
    emissions = schedule.cursor().advance_to(same_time)

    assert [e.ordinal for e in emissions] == [0, 1]
    assert [e.symbol for e in emissions] == ["WINF26", "WING26"]
    assert [e.source_delta_us for e in emissions] == [0, 0]
    assert [e.virtual_delay_us for e in emissions] == [Fraction(0, 1), Fraction(0, 1)]


# 10. Cutoff before first event
def test_cutoff_before_first_event() -> None:
    schedule = _schedule([_event(0, _utc(2))])
    cursor = schedule.cursor()
    emissions = cursor.advance_to(_utc(1))
    assert emissions == ()
    assert cursor.emitted_count == 0
    assert cursor.remaining_count == 1
    assert cursor.complete is False
    assert cursor.current_cutoff == _utc(1)


# 11. Cutoff exactly at event
def test_cutoff_exactly_at_event() -> None:
    schedule = _schedule([_event(0, _utc(1)), _event(1, _utc(3))])
    cursor = schedule.cursor()
    emissions = cursor.advance_to(_utc(1))
    assert len(emissions) == 1
    assert emissions[0].ordinal == 0
    assert cursor.emitted_count == 1
    assert cursor.remaining_count == 1
    assert cursor.complete is False
    assert cursor.current_cutoff == _utc(1)


# 12. Cutoff after multiple events
def test_cutoff_after_multiple_events() -> None:
    schedule = _schedule([
        _event(0, _utc(1)),
        _event(1, _utc(2)),
        _event(2, _utc(3)),
    ])
    cursor = schedule.cursor()
    emissions = cursor.advance_to(_utc(2))
    assert [e.ordinal for e in emissions] == [0, 1]
    assert cursor.emitted_count == 2
    assert cursor.remaining_count == 1
    assert cursor.complete is False

    remaining = cursor.advance_to(_utc(3))
    assert [e.ordinal for e in remaining] == [2]
    assert cursor.emitted_count == 3
    assert cursor.remaining_count == 0
    assert cursor.complete is True


# 13. Repeated same cutoff behavior
def test_repeated_same_cutoff_behavior() -> None:
    schedule = _schedule([_event(0, _utc(1)), _event(1, _utc(2))])
    cursor = schedule.cursor()

    first_advance = cursor.advance_to(_utc(1))
    assert len(first_advance) == 1
    assert cursor.emitted_count == 1
    assert cursor.current_cutoff == _utc(1)

    repeated_advance = cursor.advance_to(_utc(1))
    assert repeated_advance == ()
    assert cursor.emitted_count == 1
    assert cursor.current_cutoff == _utc(1)


# 14. Backward cutoff rollback safety
def test_backward_cutoff_rollback_safety() -> None:
    schedule = _schedule([_event(0, _utc(1)), _event(1, _utc(2))])
    cursor = schedule.cursor()
    first = cursor.advance_to(_utc(1))
    assert len(first) == 1
    assert cursor.emitted_count == 1
    assert cursor.current_cutoff == _utc(1)

    with pytest.raises(ValueError, match="cutoff must be monotonic"):
        cursor.advance_to(_utc(0))

    # Cursor state is unchanged
    assert cursor.emitted_count == 1
    assert cursor.current_cutoff == _utc(1)

    second = cursor.advance_to(_utc(2))
    assert [e.ordinal for e in second] == [1]
    assert cursor.emitted_count == 2
    assert cursor.complete is True


# 15. Exact speed 1x
def test_exact_speed_1x() -> None:
    events = [_event(0, _utc(0)), _event(1, _utc(1)), _event(2, _utc(3))]
    schedule = _schedule(events, speed=ReplaySpeed(1, 1))
    emissions = schedule.cursor().advance_to(_utc(3))

    assert [e.source_delta_us for e in emissions] == [0, 1_000_000, 2_000_000]
    assert [e.virtual_delay_us for e in emissions] == [
        Fraction(0, 1),
        Fraction(1_000_000, 1),
        Fraction(2_000_000, 1),
    ]


# 16. Exact speed 2x
def test_exact_speed_2x() -> None:
    events = [_event(0, _utc(0)), _event(1, _utc(1)), _event(2, _utc(3))]
    schedule = _schedule(events, speed=ReplaySpeed(2, 1))
    emissions = schedule.cursor().advance_to(_utc(3))

    assert [e.source_delta_us for e in emissions] == [0, 1_000_000, 2_000_000]
    assert [e.virtual_delay_us for e in emissions] == [
        Fraction(0, 1),
        Fraction(500_000, 1),
        Fraction(1_000_000, 1),
    ]


# 17. Exact speed 1/2x
def test_exact_speed_half_x() -> None:
    events = [_event(0, _utc(0)), _event(1, _utc(1)), _event(2, _utc(3))]
    schedule = _schedule(events, speed=ReplaySpeed(1, 2))
    emissions = schedule.cursor().advance_to(_utc(3))

    assert [e.source_delta_us for e in emissions] == [0, 1_000_000, 2_000_000]
    assert [e.virtual_delay_us for e in emissions] == [
        Fraction(0, 1),
        Fraction(2_000_000, 1),
        Fraction(4_000_000, 1),
    ]


# 18. Arbitrary positive rational speed
def test_arbitrary_positive_rational_speed() -> None:
    rate = ReplaySpeed(3, 2)
    assert rate.virtual_delay_us(1) == Fraction(2, 3)
    assert rate.virtual_delay_us(2) == Fraction(4, 3)
    assert rate.as_fraction() == Fraction(3, 2)

    from_frac = ReplaySpeed.from_fraction(Fraction(7, 4))
    assert from_frac.numerator == 7
    assert from_frac.denominator == 4
    assert from_frac.virtual_delay_us(14) == Fraction(8, 1)

    ratio_speed = ReplaySpeed.from_ratio(5, 3)
    assert ratio_speed.numerator == 5
    assert ratio_speed.denominator == 3

    one_speed = ReplaySpeed.one()
    assert one_speed.numerator == 1
    assert one_speed.denominator == 1

    rate_alias = ReplayRate(3, 2)
    assert rate_alias == rate


# 19. Zero speed rejection
def test_zero_speed_rejection() -> None:
    with pytest.raises(ValueError, match="speed numerator must be a positive integer"):
        ReplaySpeed(0, 1)
    with pytest.raises(ValueError, match="speed denominator must be a positive integer"):
        ReplaySpeed(1, 0)
    with pytest.raises(ValueError, match="speed fraction must be positive"):
        ReplaySpeed.from_fraction(Fraction(0, 1))


# 20. Negative speed rejection
def test_negative_speed_rejection() -> None:
    with pytest.raises(ValueError, match="speed numerator must be a positive integer"):
        ReplaySpeed(-1, 1)
    with pytest.raises(ValueError, match="speed denominator must be a positive integer"):
        ReplaySpeed(1, -2)
    with pytest.raises(ValueError, match="speed fraction must be positive"):
        ReplaySpeed.from_fraction(Fraction(-1, 2))


# 21. Deterministic repeated schedule construction/replay
def test_deterministic_repeated_schedule_construction_and_replay() -> None:
    events = [_event(0, _utc(0)), _event(1, _utc(1)), _event(2, _utc(2))]
    first_run = _schedule(events, speed=ReplaySpeed(5, 2)).cursor().advance_to(_utc(2))
    second_run = _schedule(events, speed=ReplaySpeed(5, 2)).cursor().advance_to(_utc(2))
    assert first_run == second_run
    assert [e.source_delta_us for e in first_run] == [0, 1_000_000, 1_000_000]
    assert [e.virtual_delay_us for e in first_run] == [
        Fraction(0, 1),
        Fraction(400_000, 1),
        Fraction(400_000, 1),
    ]


# 22. Static absence of wall-clock, network and financial capability
def test_static_absence_of_wall_clock_network_and_financial_capability() -> None:
    source = inspect.getsource(replay_module)
    assert "datetime.now(" not in source
    assert "datetime.utcnow(" not in source
    assert "time.time(" not in source
    assert "sleep(" not in source
    assert "order_send" not in source
    assert "TradeIntent" not in source
    assert "StrategyDecision" not in source
    assert "RiskAuthorization" not in source
    assert "OrderIntent" not in source
    assert "ExecutionOrder" not in source
    assert "PaperExecution" not in source
    assert "FinancialLedger" not in source
    assert "PnL" not in source
    assert "SpreadModel" not in source
    assert "FeeModel" not in source
    assert "SlippageModel" not in source
    assert "socket" not in source
    assert "requests" not in source
    assert "httpx" not in source
    assert "aiohttp" not in source
    assert "MetaTrader5" not in source


# Additional validation and branch coverage tests
def test_lane_and_schedule_parameter_validation() -> None:
    # CausalLane validation
    with pytest.raises(ValueError, match="provider_id"):
        CausalLane("", "capture-a")
    with pytest.raises(ValueError, match="capture_scope"):
        CausalLane("provider", "")

    lane = CausalLane("prov", "scope")
    # Using lane object
    sch = CausalMarketReplaySchedule(
        [],
        lane=lane,
        run_id=TEST_RUN_ID,
        code_revision=TEST_CODE_REVISION,
        config_hash=TEST_CONFIG_HASH,
    )
    assert sch.lane == lane
    assert sch.provider_id == "prov"
    assert sch.capture_scope == "scope"

    # Conflicting lane vs parameters
    with pytest.raises(ValueError, match="conflicting provider_id and lane"):
        CausalMarketReplaySchedule([], lane=lane, provider_id="other")
    with pytest.raises(ValueError, match="conflicting provider and lane"):
        CausalMarketReplaySchedule([], lane=lane, provider="other")
    with pytest.raises(ValueError, match="conflicting capture_scope and lane"):
        CausalMarketReplaySchedule([], lane=lane, capture_scope="other")
    with pytest.raises(ValueError, match="conflicting scope and lane"):
        CausalMarketReplaySchedule([], lane=lane, scope="other")
    with pytest.raises(ValueError, match="lane must be a CausalLane instance"):
        CausalMarketReplaySchedule([], lane="not-a-lane")  # type: ignore[arg-type]

    # Without lane: conflicting or missing
    with pytest.raises(ValueError, match="conflicting provider_id and provider"):
        CausalMarketReplaySchedule([], provider_id="p1", provider="p2")
    with pytest.raises(ValueError, match="provider_id or provider must be supplied"):
        CausalMarketReplaySchedule([], capture_scope="scope")
    with pytest.raises(ValueError, match="conflicting capture_scope and scope"):
        CausalMarketReplaySchedule([], provider_id="p", capture_scope="s1", scope="s2")
    with pytest.raises(ValueError, match="capture_scope or scope must be supplied"):
        CausalMarketReplaySchedule([], provider_id="p")

    # Conflicting speed and rate
    with pytest.raises(ValueError, match="conflicting speed and rate"):
        CausalMarketReplaySchedule(
            [],
            provider_id="p",
            capture_scope="s",
            speed=ReplaySpeed(1, 1),
            rate=ReplaySpeed(2, 1),
        )
    with pytest.raises(ValueError, match="speed must be ReplaySpeed"):
        CausalMarketReplaySchedule(
            [],
            provider_id="p",
            capture_scope="s",
            speed="not-speed",  # type: ignore[arg-type]
        )

    # ReplaySpeed type checks
    with pytest.raises(ValueError, match="speed numerator must be a positive integer"):
        ReplaySpeed(True, 1)
    with pytest.raises(ValueError, match="speed denominator must be a positive integer"):
        ReplaySpeed(1, False)
    with pytest.raises(ValueError, match="fraction must be a Fraction instance"):
        ReplaySpeed.from_fraction("1/2")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_delta_us must be a nonnegative integer"):
        ReplaySpeed(1, 1).virtual_delay_us(-1)
    with pytest.raises(ValueError, match="source_delta_us must be a nonnegative integer"):
        ReplaySpeed(1, 1).virtual_delay_us(1.5)  # type: ignore[arg-type]

    # Non EventEnvelope
    with pytest.raises(ValueError, match="accepts only EventEnvelope values"):
        CausalMarketReplaySchedule(["not-envelope"], provider_id="p", capture_scope="s")  # type: ignore[list-item]

    # Cursor validation
    with pytest.raises(ValueError, match="cursor requires CausalMarketReplaySchedule"):
        CausalMarketReplayCursor("not-schedule")  # type: ignore[arg-type]

    # Cutoff timezone validation
    with pytest.raises(ValueError, match="explicit UTC-aware"):
        sch.cursor().advance_to(datetime(2026, 1, 1, 10, 0, 0))


def test_replay_emission_validation() -> None:
    envelope = _event(0, _utc(0))
    # Negative ordinal
    with pytest.raises(ValueError, match="ordinal must be a nonnegative integer"):
        ReplayEmission(
            ordinal=-1,
            envelope=envelope,
            knowledge_time=_utc(0),
            source_delta_us=0,
            virtual_delay_us=Fraction(0, 1),
            run_id=TEST_RUN_ID,
        )
    # Non EventEnvelope
    with pytest.raises(ValueError, match="emission requires EventEnvelope"):
        ReplayEmission(
            ordinal=0,
            envelope="not-envelope",  # type: ignore[arg-type]
            knowledge_time=_utc(0),
            source_delta_us=0,
            virtual_delay_us=Fraction(0, 1),
            run_id=TEST_RUN_ID,
        )
    # Negative source_delta_us
    with pytest.raises(ValueError, match="source_delta_us must be nonnegative"):
        ReplayEmission(
            ordinal=0,
            envelope=envelope,
            knowledge_time=_utc(0),
            source_delta_us=-5,
            virtual_delay_us=Fraction(0, 1),
            run_id=TEST_RUN_ID,
        )
    # Negative virtual_delay_us
    with pytest.raises(ValueError, match="virtual_delay_us must be a nonnegative exact Fraction"):
        ReplayEmission(
            ordinal=0,
            envelope=envelope,
            knowledge_time=_utc(0),
            source_delta_us=0,
            virtual_delay_us=Fraction(-1, 2),
            run_id=TEST_RUN_ID,
        )
    # Invalid run_id
    with pytest.raises(ValueError, match="run_id must be RunId"):
        ReplayEmission(
            ordinal=0,
            envelope=envelope,
            knowledge_time=_utc(0),
            source_delta_us=0,
            virtual_delay_us=Fraction(0, 1),
            run_id="invalid-run-id",  # type: ignore[arg-type]
        )


def test_delta_microseconds_function() -> None:
    assert replay_module._delta_microseconds(timedelta(seconds=1)) == 1_000_000
    assert replay_module._delta_microseconds(timedelta(microseconds=42)) == 42
    with pytest.raises(ValueError, match="replay delta must not be negative"):
        replay_module._delta_microseconds(timedelta(seconds=-1))


def test_replay_emission_lineage_and_properties() -> None:
    envelope = _event(0, _utc(0), provider="p1", scope="s1")
    emission = ReplayEmission(
        ordinal=5,
        envelope=envelope,
        knowledge_time=_utc(0),
        source_delta_us=100,
        virtual_delay_us=Fraction(100, 1),
        run_id=TEST_RUN_ID,
    )
    assert emission.event_id == envelope.event_id
    assert emission.symbol == envelope.source.symbol
    assert emission.run_id == TEST_RUN_ID

    lineage = emission.lineage
    assert isinstance(lineage, ReplayEmissionLineage)
    assert lineage.run_id == TEST_RUN_ID
    assert lineage.event_id == envelope.event_id
    assert lineage.ordinal == 5
    assert lineage.provider_id == "p1"
    assert lineage.capture_scope == "s1"

    # Lineage immutability
    with pytest.raises(FrozenInstanceError):
        lineage.ordinal = 10  # type: ignore[misc]

    # Lineage validation
    with pytest.raises(ValueError, match="run_id must be RunId"):
        ReplayEmissionLineage(
            run_id="not-run-id",  # type: ignore[arg-type]
            event_id=envelope.event_id,
            ordinal=0,
            provider_id="p1",
            capture_scope="s1",
        )
    with pytest.raises(ValueError, match="event_id must be EventId"):
        ReplayEmissionLineage(
            run_id=TEST_RUN_ID,
            event_id="not-event-id",  # type: ignore[arg-type]
            ordinal=0,
            provider_id="p1",
            capture_scope="s1",
        )
    with pytest.raises(ValueError, match="ordinal must be a nonnegative integer"):
        ReplayEmissionLineage(
            run_id=TEST_RUN_ID,
            event_id=envelope.event_id,
            ordinal=-1,
            provider_id="p1",
            capture_scope="s1",
        )
    with pytest.raises(ValueError, match="provider_id must be nonempty text"):
        ReplayEmissionLineage(
            run_id=TEST_RUN_ID,
            event_id=envelope.event_id,
            ordinal=0,
            provider_id="",
            capture_scope="s1",
        )
    with pytest.raises(ValueError, match="capture_scope must be nonempty text"):
        ReplayEmissionLineage(
            run_id=TEST_RUN_ID,
            event_id=envelope.event_id,
            ordinal=0,
            provider_id="p1",
            capture_scope="   ",
        )


def test_replay_input_boundary_initialization_and_validation() -> None:
    assert RunInputBoundary is ReplayInputBoundary

    eid1 = EventId(str(UUID(int=1)))
    eid2 = EventId(str(UUID(int=2)))
    ch1 = ContentHash("a" * 64)
    ch2 = ContentHash("b" * 64)

    boundary = ReplayInputBoundary(
        run_id=TEST_RUN_ID,
        code_revision=TEST_CODE_REVISION,
        config_hash=TEST_CONFIG_HASH,
        provider_id="xp-mt5",
        capture_scope="s1-xp-capture-a12",
        event_ids=(eid1, eid2),
        content_hashes=(ch1, ch2),
        temporal_semantics="knowledge_time_v1",
    )
    assert boundary.run_id == TEST_RUN_ID
    assert boundary.code_revision == TEST_CODE_REVISION
    assert boundary.config_hash == TEST_CONFIG_HASH
    assert boundary.provider_id == "xp-mt5"
    assert boundary.capture_scope == "s1-xp-capture-a12"
    assert boundary.event_ids == (eid1, eid2)
    assert boundary.content_hashes == (ch1, ch2)
    assert boundary.temporal_semantics == "knowledge_time_v1"
    assert boundary.lane == CausalLane("xp-mt5", "s1-xp-capture-a12")
    assert boundary.input_identities == (InputIdentity(eid1, ch1), InputIdentity(eid2, ch2))

    # Immutability
    with pytest.raises(FrozenInstanceError):
        boundary.provider_id = "other"  # type: ignore[misc]

    # Type validation
    with pytest.raises(ValueError, match="run_id must be RunId"):
        ReplayInputBoundary(
            run_id="invalid",  # type: ignore[arg-type]
            code_revision=TEST_CODE_REVISION,
            config_hash=TEST_CONFIG_HASH,
            provider_id="p",
            capture_scope="s",
            event_ids=(),
        )
    with pytest.raises(ValueError, match="code_revision must be CodeRevision"):
        ReplayInputBoundary(
            run_id=TEST_RUN_ID,
            code_revision="invalid",  # type: ignore[arg-type]
            config_hash=TEST_CONFIG_HASH,
            provider_id="p",
            capture_scope="s",
            event_ids=(),
        )
    with pytest.raises(ValueError, match="config_hash must be ConfigHash"):
        ReplayInputBoundary(
            run_id=TEST_RUN_ID,
            code_revision=TEST_CODE_REVISION,
            config_hash="invalid",  # type: ignore[arg-type]
            provider_id="p",
            capture_scope="s",
            event_ids=(),
        )
    with pytest.raises(ValueError, match="provider_id must be nonempty text"):
        ReplayInputBoundary(
            run_id=TEST_RUN_ID,
            code_revision=TEST_CODE_REVISION,
            config_hash=TEST_CONFIG_HASH,
            provider_id="",
            capture_scope="s",
            event_ids=(),
        )
    with pytest.raises(ValueError, match="capture_scope must be nonempty text"):
        ReplayInputBoundary(
            run_id=TEST_RUN_ID,
            code_revision=TEST_CODE_REVISION,
            config_hash=TEST_CONFIG_HASH,
            provider_id="p",
            capture_scope="",
            event_ids=(),
        )
    with pytest.raises(ValueError, match="event_ids must be a tuple"):
        ReplayInputBoundary(
            run_id=TEST_RUN_ID,
            code_revision=TEST_CODE_REVISION,
            config_hash=TEST_CONFIG_HASH,
            provider_id="p",
            capture_scope="s",
            event_ids=[eid1],  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="event_ids must contain EventId instances"):
        ReplayInputBoundary(
            run_id=TEST_RUN_ID,
            code_revision=TEST_CODE_REVISION,
            config_hash=TEST_CONFIG_HASH,
            provider_id="p",
            capture_scope="s",
            event_ids=("not-event-id",),  # type: ignore[arg-type]
        )
    # Duplicate EventId rejection
    with pytest.raises(ValueError, match="duplicate EventId in boundary event_ids"):
        ReplayInputBoundary(
            run_id=TEST_RUN_ID,
            code_revision=TEST_CODE_REVISION,
            config_hash=TEST_CONFIG_HASH,
            provider_id="p",
            capture_scope="s",
            event_ids=(eid1, eid1),
        )
    with pytest.raises(ValueError, match="content_hashes must be a tuple"):
        ReplayInputBoundary(
            run_id=TEST_RUN_ID,
            code_revision=TEST_CODE_REVISION,
            config_hash=TEST_CONFIG_HASH,
            provider_id="p",
            capture_scope="s",
            event_ids=(eid1,),
            content_hashes=[ch1],  # type: ignore[arg-type]
        )
    # Content hashes count mismatch
    with pytest.raises(ValueError, match="content_hashes count must match event_ids count"):
        ReplayInputBoundary(
            run_id=TEST_RUN_ID,
            code_revision=TEST_CODE_REVISION,
            config_hash=TEST_CONFIG_HASH,
            provider_id="p",
            capture_scope="s",
            event_ids=(eid1,),
            content_hashes=(ch1, ch2),
        )
    # Content hashes non-ContentHash / non-None
    with pytest.raises(ValueError, match="content_hashes entries must be ContentHash or None"):
        ReplayInputBoundary(
            run_id=TEST_RUN_ID,
            code_revision=TEST_CODE_REVISION,
            config_hash=TEST_CONFIG_HASH,
            provider_id="p",
            capture_scope="s",
            event_ids=(eid1,),
            content_hashes=("not-hash",),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="temporal_semantics must be nonempty text"):
        ReplayInputBoundary(
            run_id=TEST_RUN_ID,
            code_revision=TEST_CODE_REVISION,
            config_hash=TEST_CONFIG_HASH,
            provider_id="p",
            capture_scope="s",
            event_ids=(eid1,),
            temporal_semantics="",
        )


def test_replay_input_boundary_partial_content_hashes_and_input_identities() -> None:
    eid1 = EventId(str(UUID(int=1)))
    eid2 = EventId(str(UUID(int=2)))
    ch1 = ContentHash("c" * 64)

    # Partial content hashes: one available, one None (omitted without fabricating)
    boundary = ReplayInputBoundary(
        run_id=TEST_RUN_ID,
        code_revision=TEST_CODE_REVISION,
        config_hash=TEST_CONFIG_HASH,
        provider_id="p",
        capture_scope="s",
        event_ids=(eid1, eid2),
        content_hashes=(ch1, None),
    )
    assert len(boundary.input_identities) == 1
    assert boundary.input_identities[0] == InputIdentity(eid1, ch1)

    # Empty content hashes
    boundary_no_hashes = ReplayInputBoundary(
        run_id=TEST_RUN_ID,
        code_revision=TEST_CODE_REVISION,
        config_hash=TEST_CONFIG_HASH,
        provider_id="p",
        capture_scope="s",
        event_ids=(eid1, eid2),
        content_hashes=(),
    )
    assert boundary_no_hashes.input_identities == ()


def test_replay_input_boundary_factories() -> None:
    e0 = _event(0, _utc(0), provider="p1", scope="s1")
    e1 = _event(1, _utc(1), provider="p1", scope="s1")

    # from_events
    boundary = ReplayInputBoundary.from_events(
        [e0, e1],
        run_id=TEST_RUN_ID,
        code_revision=TEST_CODE_REVISION,
        config_hash=TEST_CONFIG_HASH,
        provider_id="p1",
        capture_scope="s1",
    )
    assert boundary.event_ids == (e0.event_id, e1.event_id)
    assert boundary.provider_id == "p1"
    assert boundary.capture_scope == "s1"
    assert boundary.temporal_semantics == "knowledge_time_v1"

    # from_events non EventEnvelope
    with pytest.raises(ValueError, match="events must contain EventEnvelope"):
        ReplayInputBoundary.from_events(
            ["not-envelope"],  # type: ignore[list-item]
            run_id=TEST_RUN_ID,
            code_revision=TEST_CODE_REVISION,
            config_hash=TEST_CONFIG_HASH,
            provider_id="p1",
            capture_scope="s1",
        )

    # from_manifest
    manifest = RunManifest(
        run_id=TEST_RUN_ID,
        started_at=_utc(0),
        code_revision=TEST_CODE_REVISION,
        config_hash=TEST_CONFIG_HASH,
        inputs=(InputIdentity(e0.event_id, ContentHash("f" * 64)),),
    )
    b_manifest = ReplayInputBoundary.from_manifest(
        manifest,
        provider_id="p1",
        capture_scope="s1",
        event_ids=(e0.event_id, e1.event_id),
    )
    assert b_manifest.run_id == TEST_RUN_ID
    assert b_manifest.code_revision == TEST_CODE_REVISION
    assert b_manifest.config_hash == TEST_CONFIG_HASH
    assert b_manifest.provider_id == "p1"
    assert b_manifest.capture_scope == "s1"
    assert b_manifest.event_ids == (e0.event_id, e1.event_id)
    assert b_manifest.content_hashes == (ContentHash("f" * 64), None)

    # from_manifest validation
    with pytest.raises(ValueError, match="manifest must be RunManifest"):
        ReplayInputBoundary.from_manifest(
            "not-manifest",  # type: ignore[arg-type]
            provider_id="p1",
            capture_scope="s1",
            event_ids=(),
        )


def test_schedule_boundary_validation_fail_closed() -> None:
    e0 = _event(0, _utc(0), provider="p1", scope="s1")
    e1 = _event(1, _utc(1), provider="p1", scope="s1")
    e2 = _event(2, _utc(2), provider="p1", scope="s1")

    valid_boundary = ReplayInputBoundary.from_events(
        [e0, e1],
        run_id=TEST_RUN_ID,
        code_revision=TEST_CODE_REVISION,
        config_hash=TEST_CONFIG_HASH,
        provider_id="p1",
        capture_scope="s1",
    )

    # Valid schedule construction with boundary
    sch = CausalMarketReplaySchedule([e0, e1], boundary=valid_boundary)
    assert sch.boundary is valid_boundary
    assert sch.run_id == TEST_RUN_ID
    assert sch.code_revision == TEST_CODE_REVISION
    assert sch.config_hash == TEST_CONFIG_HASH
    assert sch.provider_id == "p1"
    assert sch.capture_scope == "s1"
    assert sch.temporal_semantics == "knowledge_time_v1"

    # Reject schedule without boundary or explicit provenance
    with pytest.raises(
        ValueError,
        match=(
            "replay schedule requires boundary or explicit "
            r"\(run_id, code_revision, config_hash\)"
        ),
    ):
        CausalMarketReplaySchedule([e0, e1], provider_id="p1", capture_scope="s1")

    # Reject non-ReplayInputBoundary
    with pytest.raises(ValueError, match="boundary must be a ReplayInputBoundary instance"):
        CausalMarketReplaySchedule([e0, e1], boundary="not-boundary")  # type: ignore[arg-type]

    # Reject boundary provider mismatch
    b_bad_provider = ReplayInputBoundary(
        run_id=TEST_RUN_ID,
        code_revision=TEST_CODE_REVISION,
        config_hash=TEST_CONFIG_HASH,
        provider_id="other-provider",
        capture_scope="s1",
        event_ids=(e0.event_id, e1.event_id),
    )
    with pytest.raises(ValueError, match="boundary provider_id does not match schedule provider"):
        CausalMarketReplaySchedule([e0, e1], boundary=b_bad_provider, provider_id="p1")

    # Reject boundary capture_scope mismatch
    b_bad_scope = ReplayInputBoundary(
        run_id=TEST_RUN_ID,
        code_revision=TEST_CODE_REVISION,
        config_hash=TEST_CONFIG_HASH,
        provider_id="p1",
        capture_scope="other-scope",
        event_ids=(e0.event_id, e1.event_id),
    )
    with pytest.raises(
        ValueError, match="boundary capture_scope does not match schedule capture_scope"
    ):
        CausalMarketReplaySchedule([e0, e1], boundary=b_bad_scope, capture_scope="s1")

    # Reject boundary event sequence mismatch (different count)
    b_fewer_events = ReplayInputBoundary(
        run_id=TEST_RUN_ID,
        code_revision=TEST_CODE_REVISION,
        config_hash=TEST_CONFIG_HASH,
        provider_id="p1",
        capture_scope="s1",
        event_ids=(e0.event_id,),
    )
    with pytest.raises(
        ValueError, match="boundary event_ids do not match supplied events sequence"
    ):
        CausalMarketReplaySchedule([e0, e1], boundary=b_fewer_events)

    # Reject boundary event sequence mismatch (different order)
    b_reversed_order = ReplayInputBoundary(
        run_id=TEST_RUN_ID,
        code_revision=TEST_CODE_REVISION,
        config_hash=TEST_CONFIG_HASH,
        provider_id="p1",
        capture_scope="s1",
        event_ids=(e1.event_id, e0.event_id),
    )
    with pytest.raises(
        ValueError, match="boundary event_ids do not match supplied events sequence"
    ):
        CausalMarketReplaySchedule([e0, e1], boundary=b_reversed_order)

    # Reject boundary event sequence mismatch (different event IDs)
    b_different_events = ReplayInputBoundary(
        run_id=TEST_RUN_ID,
        code_revision=TEST_CODE_REVISION,
        config_hash=TEST_CONFIG_HASH,
        provider_id="p1",
        capture_scope="s1",
        event_ids=(e0.event_id, e2.event_id),
    )
    with pytest.raises(
        ValueError, match="boundary event_ids do not match supplied events sequence"
    ):
        CausalMarketReplaySchedule([e0, e1], boundary=b_different_events)

    # Reject temporal semantics mismatch
    with pytest.raises(ValueError, match="temporal_semantics does not match boundary"):
        CausalMarketReplaySchedule(
            [e0, e1],
            boundary=valid_boundary,
            temporal_semantics="other_semantics_v2",
        )


def test_schedule_lineage_preservation_during_replay() -> None:
    e0 = _event(0, _utc(0), provider="p1", scope="s1")
    e1 = _event(1, _utc(1), provider="p1", scope="s1")
    e2 = _event(2, _utc(2), provider="p1", scope="s1")

    sch = _schedule([e0, e1, e2], provider_id="p1", capture_scope="s1")
    cursor = sch.cursor()
    emissions = cursor.advance_to(_utc(5))
    assert len(emissions) == 3

    for idx, em in enumerate(emissions):
        assert em.run_id == sch.run_id
        lineage = em.lineage
        assert lineage.run_id == sch.run_id
        assert lineage.event_id == sch.events[idx].event_id
        assert lineage.ordinal == idx
        assert lineage.provider_id == "p1"
        assert lineage.capture_scope == "s1"
