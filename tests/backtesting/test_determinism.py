"""Determinism verification test suite for Sprint 3.

Verifies that identical inputs yield byte-for-byte identical results across
repeated runs, independent of Python hash seeds, random state, or execution order.
"""

import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from btg_ai_trader.backtesting.accounting import EndOfWindowPolicy
from btg_ai_trader.backtesting.assumptions import (
    EconomicAssumptions,
    ExecutionPolicy,
    FeeSchedule,
    FixedPointsSlippageModel,
    LatencyModel,
    SpreadModel,
)
from btg_ai_trader.backtesting.domain import (
    ActionIdentity,
    BacktestAction,
    InstrumentEconomics,
    OrderStyle,
    Side,
)
from btg_ai_trader.backtesting.engine import DeterministicEconomicBacktester
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


def test_100_runs_exact_byte_determinism() -> None:
    """Run 100 consecutive backtests and assert absolute bit-level determinism."""
    iid = TradableInstrumentId(make_uuid(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    assumptions = EconomicAssumptions(
        assumptions_id="det_assump",
        spread_model=SpreadModel(),
        slippage_model=FixedPointsSlippageModel(adverse_points=Decimal("1.0")),
        fee_schedule=FeeSchedule(
            schedule_id="fee_det",
            fixed_per_order=Decimal("2.5"),
            per_unit=Decimal("0.1"),
            bps_rate=Decimal("0.5"),
        ),
        latency_model=LatencyModel(decision_latency_us=50, transit_latency_us=100),
        execution_policy=ExecutionPolicy(),
    )
    engine = DeterministicEconomicBacktester(
        instrument_economics=econ,
        assumptions=assumptions,
        end_of_window_policy=EndOfWindowPolicy.CLOSE_AT_LAST_VALID_QUOTE,
    )

    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)
    t2 = datetime(2026, 9, 16, 10, 0, 2, tzinfo=UTC)

    actions = [
        make_action(1, t0, iid, Side.BUY, Decimal("10")),
        make_action(2, t1, iid, Side.SELL, Decimal("10")),
    ]
    events = [
        make_tick_event(
            1, t0 + timedelta(microseconds=200), iid, bid=Decimal("99.0"), ask=Decimal("100.0")
        ),
        make_tick_event(
            2, t1 + timedelta(microseconds=200), iid, bid=Decimal("105.0"), ask=Decimal("106.0")
        ),
        make_tick_event(3, t2, iid, bid=Decimal("107.0"), ask=Decimal("108.0")),
    ]

    baseline_res = engine.run(actions, events, session_id="fixed-session-seed-100")
    baseline_json = baseline_res.manifest.to_json()
    baseline_hash = baseline_res.manifest.manifest_hash.value

    for i in range(100):
        # Vary external Python random state to verify zero dependence on RNG
        random.seed(i * 1337)
        res = engine.run(actions, events, session_id="fixed-session-seed-100")
        assert res.manifest.manifest_hash.value == baseline_hash
        assert res.manifest.to_json() == baseline_json
        assert res.metrics == baseline_res.metrics
        assert res.economic_state.pnl == baseline_res.economic_state.pnl
        assert len(res.fills) == len(baseline_res.fills)
        for f1, f2 in zip(res.fills, baseline_res.fills, strict=True):
            assert f1.fill_price == f2.fill_price
            assert f1.slippage == f2.slippage
            assert f1.explicit_fee == f2.explicit_fee
            assert f1.outcome == f2.outcome
