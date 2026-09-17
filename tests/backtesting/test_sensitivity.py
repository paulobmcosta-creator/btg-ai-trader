"""Unit tests for friction sensitivity analysis and monotonicity verification."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest

from btg_ai_trader.backtesting.assumptions import (
    EconomicAssumptions,
    ExecutionPolicy,
    FeeSchedule,
    LatencyModel,
    SpreadModel,
    ZeroSlippageModel,
)
from btg_ai_trader.backtesting.domain import (
    ActionIdentity,
    BacktestAction,
    InstrumentEconomics,
    OrderStyle,
    Side,
)
from btg_ai_trader.backtesting.sensitivity import (
    MonotonicityViolationError,
    SensitivityDataPoint,
    run_fee_sensitivity_sweep,
    run_latency_sensitivity_sweep,
    run_slippage_sensitivity_sweep,
    verify_pnl_monotonicity,
)
from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.identity import (
    EventId,
    ProviderInstrumentRef,
    TradableInstrumentId,
)
from btg_ai_trader.observer.market import Tick
from btg_ai_trader.observer.temporal import EventTime, ObservationTimes


def make_uuid(num: int = 1) -> str:
    return str(UUID(int=num))


def make_tick_event(
    seq: int,
    ts: datetime,
    iid: TradableInstrumentId,
    bid: Decimal,
    ask: Decimal,
) -> EventEnvelope:
    payload = Tick(
        bid=bid,
        ask=ask,
        last=bid,
        volume=Decimal("10"),
    )
    event_time = EventTime(ts, "fixture-clock", timedelta(microseconds=1))
    return EventEnvelope(
        event_id=EventId(make_uuid(100 + seq)),
        event_type=EventType.TICK,
        source=ProviderInstrumentRef("xp", "market", "WINV26"),
        instrument_id=iid,
        times=ObservationTimes(
            event_time=event_time,
            ingestion_time=ts,
            knowledge_time=ts,
        ),
        payload=payload,
    )


def make_action(
    action_num: int,
    ts: datetime,
    iid: TradableInstrumentId,
    side: Side,
    qty: Decimal = Decimal("10"),
) -> BacktestAction:
    return BacktestAction(
        action_id=ActionIdentity(make_uuid(action_num)),
        instrument_id=iid,
        side=side,
        quantity=qty,
        order_style=OrderStyle.MARKET,
        knowledge_cutoff=ts,
        decision_time=ts,
        order_ready_time=ts,
    )


def test_verify_pnl_monotonicity_direct() -> None:
    # 0 or 1 items is no-op
    verify_pnl_monotonicity([])
    verify_pnl_monotonicity(
        [
            SensitivityDataPoint(
                "f", Decimal("0"), Decimal("10"), Decimal("10"), Decimal("0"), Decimal("0")
            )
        ]
    )

    # Monotonically non-increasing: 100 -> 90 -> 80 -> 80
    valid = [
        SensitivityDataPoint(
            "f", Decimal("1"), Decimal("100"), Decimal("100"), Decimal("0"), Decimal("0")
        ),
        SensitivityDataPoint(
            "f", Decimal("2"), Decimal("100"), Decimal("90"), Decimal("10"), Decimal("0")
        ),
        SensitivityDataPoint(
            "f", Decimal("3"), Decimal("100"), Decimal("80"), Decimal("20"), Decimal("0")
        ),
        SensitivityDataPoint(
            "f", Decimal("4"), Decimal("100"), Decimal("80"), Decimal("20"), Decimal("0")
        ),
    ]
    verify_pnl_monotonicity(valid)

    # Monotonicity violation: 100 -> 90 -> 95 (increased!)
    invalid = [
        SensitivityDataPoint(
            "f", Decimal("1"), Decimal("100"), Decimal("100"), Decimal("0"), Decimal("0")
        ),
        SensitivityDataPoint(
            "f", Decimal("2"), Decimal("100"), Decimal("90"), Decimal("10"), Decimal("0")
        ),
        SensitivityDataPoint(
            "f", Decimal("3"), Decimal("100"), Decimal("95"), Decimal("5"), Decimal("0")
        ),
    ]
    with pytest.raises(MonotonicityViolationError, match="Monotonicity violation on f"):
        verify_pnl_monotonicity(invalid)

    # Reject mismatched parameter names
    mismatched = [
        SensitivityDataPoint(
            "fee", Decimal("1"), Decimal("100"), Decimal("90"), Decimal("10"), Decimal("0")
        ),
        SensitivityDataPoint(
            "slip", Decimal("2"), Decimal("100"), Decimal("80"), Decimal("20"), Decimal("0")
        ),
    ]
    with pytest.raises(ValueError, match="Mixed parameters in sensitivity sweep"):
        verify_pnl_monotonicity(mismatched)

    # Reject unsorted friction_value
    unsorted_pts = [
        SensitivityDataPoint(
            "fee", Decimal("2"), Decimal("100"), Decimal("90"), Decimal("10"), Decimal("0")
        ),
        SensitivityDataPoint(
            "fee", Decimal("1"), Decimal("100"), Decimal("80"), Decimal("20"), Decimal("0")
        ),
    ]
    with pytest.raises(
        ValueError, match="Sensitivity sweep results must be sorted by friction_value ascending"
    ):
        verify_pnl_monotonicity(unsorted_pts)


def test_run_fee_sensitivity_sweep() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        assumptions_id="base",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule(
            schedule_id="fee",
            fixed_per_order=Decimal("2.0"),
            per_unit=Decimal("0.5"),
            bps_rate=Decimal("1.0"),
        ),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )

    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)

    # Buy 10 @ 100 (ask = 100.0)
    # Sell 10 @ 110 (bid = 110.0)
    # Gross realized = (110 - 100)*10 = 100
    actions = [
        make_action(1, t0, iid, Side.BUY, Decimal("10")),
        make_action(2, t1, iid, Side.SELL, Decimal("10")),
    ]
    events = [
        make_tick_event(1, t0, iid, bid=Decimal("99.5"), ask=Decimal("100.0")),
        make_tick_event(2, t1, iid, bid=Decimal("110.0"), ask=Decimal("110.5")),
    ]

    # Negative fee multiplier rejected
    with pytest.raises(ValueError, match="fee multiplier cannot be negative"):
        run_fee_sensitivity_sweep(actions, events, econ, assumptions, [Decimal("-1")])

    multipliers = [Decimal("0.0"), Decimal("0.5"), Decimal("1.0"), Decimal("2.0"), Decimal("5.0")]
    sweep = run_fee_sensitivity_sweep(actions, events, econ, assumptions, multipliers)

    assert len(sweep) == 5
    # As multiplier increases, fees strictly increase and net P&L strictly decreases
    for i in range(1, len(sweep)):
        assert sweep[i].total_explicit_fees >= sweep[i - 1].total_explicit_fees
        assert sweep[i].net_realized_pnl <= sweep[i - 1].net_realized_pnl


def test_run_slippage_sensitivity_sweep() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        assumptions_id="base",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule(schedule_id="fee"),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )

    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)

    actions = [
        make_action(1, t0, iid, Side.BUY, Decimal("10")),
        make_action(2, t1, iid, Side.SELL, Decimal("10")),
    ]
    events = [
        make_tick_event(1, t0, iid, bid=Decimal("99.5"), ask=Decimal("100.0")),
        make_tick_event(2, t1, iid, bid=Decimal("110.0"), ask=Decimal("110.5")),
    ]

    # Negative slippage rejected
    with pytest.raises(ValueError, match="slippage points cannot be negative"):
        run_slippage_sensitivity_sweep(actions, events, econ, assumptions, [Decimal("-1")])

    points_list = [Decimal("0.0"), Decimal("0.5"), Decimal("1.0"), Decimal("2.0")]
    sweep = run_slippage_sensitivity_sweep(actions, events, econ, assumptions, points_list)

    assert len(sweep) == 4
    # As slippage increases, net P&L strictly decreases
    for i in range(1, len(sweep)):
        assert sweep[i].net_realized_pnl <= sweep[i - 1].net_realized_pnl
        assert sweep[i].diagnostic_slippage_burden >= sweep[i - 1].diagnostic_slippage_burden


def test_run_latency_sensitivity_sweep() -> None:
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        assumptions_id="base",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule(schedule_id="fee"),
        latency_model=LatencyModel(decision_latency_us=100, transit_latency_us=100),
        execution_policy=ExecutionPolicy(),
    )

    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)

    actions = [
        make_action(1, t0, iid, Side.BUY, Decimal("10")),
        make_action(2, t1, iid, Side.SELL, Decimal("10")),
    ]
    events = [
        make_tick_event(
            1, t0 + timedelta(microseconds=500), iid, bid=Decimal("99.5"), ask=Decimal("100.0")
        ),
        make_tick_event(
            2, t1 + timedelta(microseconds=500), iid, bid=Decimal("110.0"), ask=Decimal("110.5")
        ),
    ]

    # Negative latency rejected
    with pytest.raises(ValueError, match="latency cannot be negative"):
        run_latency_sensitivity_sweep(actions, events, econ, assumptions, [-1])

    latencies = [0, 100, 500]
    sweep = run_latency_sensitivity_sweep(actions, events, econ, assumptions, latencies)

    assert len(sweep) == 3
    for pt in sweep:
        assert pt.parameter_name == "transit_latency_us"
