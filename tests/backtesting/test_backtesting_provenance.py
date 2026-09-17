from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest

from btg_ai_trader.backtesting.accounting import BacktestEconomicState
from btg_ai_trader.backtesting.assumptions import (
    EconomicAssumptions,
    ExecutionPolicy,
    FeeSchedule,
    FixedPointsSlippageModel,
    LatencyModel,
    SpreadModel,
    ZeroSlippageModel,
)
from btg_ai_trader.backtesting.domain import (
    ActionIdentity,
    BacktestAction,
    ExecutionOutcome,
    ExecutionTiming,
    InstrumentEconomics,
    OrderStyle,
    Side,
    SimulatedFill,
)
from btg_ai_trader.backtesting.metrics import DescriptiveBacktestMetrics
from btg_ai_trader.backtesting.provenance import (
    BacktestInputBoundary,
    BacktestRunManifest,
    compute_actions_hash,
    compute_assumptions_hash,
    compute_dataset_hash,
    sha256_canonical_json,
)
from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.identity import (
    EventId,
    ProviderInstrumentRef,
    RunId,
    TradableInstrumentId,
)
from btg_ai_trader.observer.market import Candle, CandleFinality, Tick
from btg_ai_trader.observer.provenance import CodeRevision, ConfigHash, ContentHash
from btg_ai_trader.observer.temporal import EventTime, ObservationTimes
from btg_ai_trader.replay.core import ReplayInputBoundary


def make_uuid(num: int = 1) -> str:
    return str(UUID(int=num))


def make_event(
    seq: int,
    ts: datetime,
    bid: Decimal = Decimal("100.0"),
    ask: Decimal = Decimal("100.5"),
) -> EventEnvelope:
    iid = TradableInstrumentId(make_uuid(1))
    payload = Tick(
        bid=bid,
        ask=ask,
        last=Decimal("100.2"),
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
    side: Side = Side.BUY,
    qty: Decimal = Decimal("10"),
) -> BacktestAction:
    iid = TradableInstrumentId(make_uuid(1))
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


def sample_metrics() -> DescriptiveBacktestMetrics:
    return DescriptiveBacktestMetrics(
        gross_realized_pnl=Decimal("100.0"),
        net_realized_pnl=Decimal("95.0"),
        total_explicit_fees=Decimal("5.0"),
        diagnostic_slippage_burden=Decimal("2.0"),
        turnover=Decimal("2000.0"),
        total_actions=2,
        fill_count=2,
        no_fill_count=0,
        indeterminate_count=0,
        rejected_count=0,
        fill_rate=Decimal("1.0"),
        closed_trade_count=1,
        winning_trade_count=1,
        losing_trade_count=0,
        breakeven_trade_count=0,
        hit_rate=Decimal("1.0"),
        average_win=Decimal("100.0"),
        average_loss=Decimal("0"),
        profit_factor=Decimal("Infinity"),
        expectancy=Decimal("100.0"),
        max_drawdown_amount=Decimal("0"),
        max_drawdown_ratio=Decimal("0"),
    )


def test_sha256_canonical_json_and_key_order() -> None:
    p1 = {"b": 2, "a": 1}
    p2 = {"a": 1, "b": 2}
    h1 = sha256_canonical_json(p1)
    h2 = sha256_canonical_json(p2)
    assert h1 == h2
    assert len(h1.value) == 64


def test_compute_dataset_hash_determinism_and_sensitivity() -> None:
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 0, 1, tzinfo=UTC)

    e1 = make_event(1, t0)
    e2 = make_event(2, t1)

    h1 = compute_dataset_hash([e1, e2])
    h2 = compute_dataset_hash([e1, e2])
    assert h1 == h2

    # Perturbed event sequence changes hash
    e2_alt = make_event(2, t1, bid=Decimal("101.0"), ask=Decimal("101.5"))
    h3 = compute_dataset_hash([e1, e2_alt])
    assert h1 != h3


def test_compute_actions_hash_determinism_and_sensitivity() -> None:
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    a1 = make_action(1, t0, Side.BUY, Decimal("10"))
    a2 = make_action(2, t0, Side.SELL, Decimal("10"))

    h1 = compute_actions_hash([a1, a2])
    h2 = compute_actions_hash([a1, a2])
    assert h1 == h2

    a2_alt = make_action(2, t0, Side.SELL, Decimal("15"))
    h3 = compute_actions_hash([a1, a2_alt])
    assert h1 != h3


def test_compute_assumptions_hash() -> None:
    assump1 = EconomicAssumptions(
        assumptions_id="assump1",
        spread_model=SpreadModel(max_spread=Decimal("2.0")),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule(schedule_id="fee1", fixed_per_order=Decimal("1.5")),
        latency_model=LatencyModel(decision_latency_us=100),
        execution_policy=ExecutionPolicy(small_lot_max_quantity=Decimal("50")),
    )
    h1 = compute_assumptions_hash(assump1)
    assert len(h1.value) == 64

    assump2 = EconomicAssumptions(
        assumptions_id="assump2",
        spread_model=SpreadModel(max_spread=Decimal("2.0")),
        slippage_model=FixedPointsSlippageModel(adverse_points=Decimal("0.5")),
        fee_schedule=FeeSchedule(schedule_id="fee1", fixed_per_order=Decimal("1.5")),
        latency_model=LatencyModel(decision_latency_us=100),
        execution_policy=ExecutionPolicy(small_lot_max_quantity=Decimal("50")),
    )
    h2 = compute_assumptions_hash(assump2)
    assert h1 != h2


def test_backtest_input_boundary_validation_and_codec() -> None:
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    events = [make_event(1, t0)]
    actions = [make_action(1, t0)]
    rev = CodeRevision("b" * 40)
    source_run_id = RunId(make_uuid(50))
    cfg_hash = ConfigHash("c" * 64)

    boundary = BacktestInputBoundary.create(
        events,
        actions,
        code_revision=rev,
        run_id=source_run_id,
        config_hash=cfg_hash,
        provider_id="xp",
        capture_scope="market",
    )
    d = boundary.to_dict()
    assert "replay_boundary" in d
    assert "actions_hash" in d
    assert "code_revision" in d
    assert "dataset_hash" in d

    recovered = BacktestInputBoundary.from_dict(d)
    assert recovered == boundary

    # Fail-closed when building from events without full provenance
    with pytest.raises(ValueError, match="run_id must be explicitly provided"):
        BacktestInputBoundary.create(
            events,
            actions,
            code_revision=rev,
            config_hash=cfg_hash,
            provider_id="xp",
            capture_scope="market",
        )
    with pytest.raises(ValueError, match="config_hash must be explicitly provided"):
        BacktestInputBoundary.create(
            events,
            actions,
            code_revision=rev,
            run_id=source_run_id,
            provider_id="xp",
            capture_scope="market",
        )
    with pytest.raises(ValueError, match="provider_id must be explicitly provided"):
        BacktestInputBoundary.create(
            events,
            actions,
            code_revision=rev,
            run_id=source_run_id,
            config_hash=cfg_hash,
            capture_scope="market",
        )
    with pytest.raises(ValueError, match="capture_scope must be explicitly provided"):
        BacktestInputBoundary.create(
            events,
            actions,
            code_revision=rev,
            run_id=source_run_id,
            config_hash=cfg_hash,
            provider_id="xp",
        )

    # Validations
    ch = ContentHash("a" * 64)
    rb = boundary.replay_boundary
    with pytest.raises(ValueError, match="replay_boundary must be ReplayInputBoundary"):
        BacktestInputBoundary(
            replay_boundary="bad",  # type: ignore[arg-type]
            actions_hash=ch,
            code_revision=rev,
            environment_signature="env",
        )

    with pytest.raises(ValueError, match="actions_hash must be ContentHash"):
        BacktestInputBoundary(
            replay_boundary=rb,
            actions_hash="bad",  # type: ignore[arg-type]
            code_revision=rev,
            environment_signature="env",
        )

    with pytest.raises(ValueError, match="code_revision must be CodeRevision"):
        BacktestInputBoundary(
            replay_boundary=rb,
            actions_hash=ch,
            code_revision="bad",  # type: ignore[arg-type]
            environment_signature="env",
        )

    with pytest.raises(ValueError, match="environment_signature"):
        BacktestInputBoundary(
            replay_boundary=rb, actions_hash=ch, code_revision=rev, environment_signature=""
        )


def test_backtest_run_manifest_lifecycle_and_integrity() -> None:
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    iid = TradableInstrumentId(make_uuid(1))
    events = [make_event(1, t0)]
    actions = [make_action(1, t0)]
    assumptions = EconomicAssumptions(
        assumptions_id="assump_base",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule(schedule_id="fee_base"),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )
    rev = CodeRevision("b" * 40)
    source_run_id = RunId(make_uuid(50))
    cfg_hash = ConfigHash("c" * 64)
    boundary = BacktestInputBoundary.create(
        events,
        actions,
        code_revision=rev,
        run_id=source_run_id,
        config_hash=cfg_hash,
        provider_id="xp",
        capture_scope="market",
    )
    metrics = sample_metrics()

    econ = InstrumentEconomics(iid, "BRL", Decimal("1.0"), Decimal("0.5"), Decimal("1.0"))
    economic_state = BacktestEconomicState.initial(econ)
    fill = SimulatedFill(
        fill_id=ActionIdentity(make_uuid(55)),
        action_id=ActionIdentity(make_uuid(1)),
        instrument_id=iid,
        side=Side.BUY,
        quantity=Decimal("10"),
        raw_price=Decimal("100.0"),
        fill_price=Decimal("100.0"),
        slippage=Decimal("0"),
        explicit_fee=Decimal("5.0"),
        timing=ExecutionTiming(t0, t0, t0, t0, t0),
        outcome=ExecutionOutcome.FILL,
        diagnostic_spread_burden=Decimal("0.5"),
        source_event_id=events[0].event_id,
    )

    manifest = BacktestRunManifest.create(
        run_id=ActionIdentity(make_uuid(10)),
        input_boundary=boundary,
        assumptions=assumptions,
        instrument_id=iid,
        instrument_economics=econ,
        fills=(fill,),
        economic_state=economic_state,
        metrics=metrics,
        created_at=t0,
    )

    assert manifest.verify_integrity()

    # Serialization and deserialization roundtrip
    json_str = manifest.to_json()
    reconstructed = BacktestRunManifest.from_json(json_str)
    assert reconstructed == manifest
    assert reconstructed.verify_integrity()

    # Deserializing manifest with missing hash or sentinel '0'*64 is rejected
    manifest_dict = manifest.to_dict()
    bad_dict = dict(manifest_dict)
    bad_dict["fills_hash"] = "0" * 64
    with pytest.raises(ValueError, match="sentinel '0'\\*64"):
        BacktestRunManifest.from_dict(bad_dict)

    incomplete_dict = dict(manifest_dict)
    del incomplete_dict["fills_hash"]
    with pytest.raises(ValueError, match="Incomplete manifest payload: missing"):
        BacktestRunManifest.from_dict(incomplete_dict)

    # Tampering with manifest_hash fails integrity verification
    tampered_hash = BacktestRunManifest(
        run_id=manifest.run_id,
        created_at=manifest.created_at,
        input_boundary=manifest.input_boundary,
        assumptions_hash=manifest.assumptions_hash,
        instrument_id=manifest.instrument_id,
        instrument_economics_hash=manifest.instrument_economics_hash,
        fills_hash=manifest.fills_hash,
        economic_state_hash=manifest.economic_state_hash,
        metrics_hash=manifest.metrics_hash,
        metrics=manifest.metrics,
        manifest_hash=ContentHash("f" * 64),
    )
    assert not tampered_hash.verify_integrity()


def test_manifest_field_validations() -> None:
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    iid = TradableInstrumentId(make_uuid(1))
    run_id = ActionIdentity(make_uuid(10))
    rev = CodeRevision("b" * 40)
    rb = ReplayInputBoundary(
        run_id=RunId(make_uuid(50)),
        code_revision=rev,
        config_hash=ConfigHash("c" * 64),
        provider_id="xp",
        capture_scope="market",
        event_ids=(EventId(make_uuid(101)),),
    )
    boundary = BacktestInputBoundary(
        replay_boundary=rb,
        actions_hash=ContentHash("2" * 64),
        code_revision=rev,
        environment_signature="env-sig",
    )
    assump_hash = ContentHash("c" * 64)
    manifest_hash = ContentHash("d" * 64)
    dummy_hash = ContentHash("1" * 64)
    metrics = sample_metrics()

    with pytest.raises(ValueError, match="run_id must be ActionIdentity"):
        BacktestRunManifest(
            run_id="bad",  # type: ignore[arg-type]
            created_at=t0,
            input_boundary=boundary,
            assumptions_hash=assump_hash,
            instrument_id=iid,
            instrument_economics_hash=dummy_hash,
            fills_hash=dummy_hash,
            economic_state_hash=dummy_hash,
            metrics_hash=dummy_hash,
            metrics=metrics,
            manifest_hash=manifest_hash,
        )

    with pytest.raises(ValueError, match="input_boundary must be BacktestInputBoundary"):
        BacktestRunManifest(
            run_id=run_id,
            created_at=t0,
            input_boundary="bad",  # type: ignore[arg-type]
            assumptions_hash=assump_hash,
            instrument_id=iid,
            instrument_economics_hash=dummy_hash,
            fills_hash=dummy_hash,
            economic_state_hash=dummy_hash,
            metrics_hash=dummy_hash,
            metrics=metrics,
            manifest_hash=manifest_hash,
        )

    with pytest.raises(ValueError, match="assumptions_hash must be ContentHash"):
        BacktestRunManifest(
            run_id=run_id,
            created_at=t0,
            input_boundary=boundary,
            assumptions_hash="bad",  # type: ignore[arg-type]
            instrument_id=iid,
            instrument_economics_hash=dummy_hash,
            fills_hash=dummy_hash,
            economic_state_hash=dummy_hash,
            metrics_hash=dummy_hash,
            metrics=metrics,
            manifest_hash=manifest_hash,
        )

    with pytest.raises(ValueError, match="instrument_id must be TradableInstrumentId"):
        BacktestRunManifest(
            run_id=run_id,
            created_at=t0,
            input_boundary=boundary,
            assumptions_hash=assump_hash,
            instrument_id="bad",  # type: ignore[arg-type]
            instrument_economics_hash=dummy_hash,
            fills_hash=dummy_hash,
            economic_state_hash=dummy_hash,
            metrics_hash=dummy_hash,
            metrics=metrics,
            manifest_hash=manifest_hash,
        )

    with pytest.raises(ValueError, match="metrics must be DescriptiveBacktestMetrics"):
        BacktestRunManifest(
            run_id=run_id,
            created_at=t0,
            input_boundary=boundary,
            assumptions_hash=assump_hash,
            instrument_id=iid,
            instrument_economics_hash=dummy_hash,
            fills_hash=dummy_hash,
            economic_state_hash=dummy_hash,
            metrics_hash=dummy_hash,
            metrics="bad",  # type: ignore[arg-type]
            manifest_hash=manifest_hash,
        )

    with pytest.raises(ValueError, match="manifest_hash must be ContentHash"):
        BacktestRunManifest(
            run_id=run_id,
            created_at=t0,
            input_boundary=boundary,
            assumptions_hash=assump_hash,
            instrument_id=iid,
            instrument_economics_hash=dummy_hash,
            fills_hash=dummy_hash,
            economic_state_hash=dummy_hash,
            metrics_hash=dummy_hash,
            metrics=metrics,
            manifest_hash="bad",  # type: ignore[arg-type]
        )


def test_compute_dataset_hash_candle() -> None:
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 16, 10, 1, 0, tzinfo=UTC)
    iid = TradableInstrumentId(make_uuid(1))
    candle = Candle(
        interval_start=t0,
        interval_end=t1,
        finality=CandleFinality.FINAL,
        finalized_at=t1,
        available_at=t1,
        open=Decimal("100.0"),
        high=Decimal("105.0"),
        low=Decimal("99.0"),
        close=Decimal("103.0"),
        volume=Decimal("100"),
    )
    event_time = EventTime(t1, "fixture-clock", timedelta(microseconds=1))
    ev = EventEnvelope(
        event_id=EventId(make_uuid(99)),
        event_type=EventType.CANDLE,
        source=ProviderInstrumentRef("xp", "market", "WINV26"),
        instrument_id=iid,
        times=ObservationTimes(event_time=event_time, ingestion_time=t1, knowledge_time=t1),
        payload=candle,
    )
    h = compute_dataset_hash([ev])
    assert len(h.value) == 64
