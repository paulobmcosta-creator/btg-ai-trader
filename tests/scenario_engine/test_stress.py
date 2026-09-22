"""Sprint 6 economic stress integration tests against the Sprint 3 kernel."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest

import btg_ai_trader.scenario_engine.stress as stress_module
from btg_ai_trader.backtesting import (
    ActionIdentity,
    BacktestAction,
    BacktestResult,
    DeterministicEconomicBacktester,
    EconomicAssumptions,
    EndOfWindowPolicy,
    ExecutionPolicy,
    FeeSchedule,
    FixedPointsSlippageModel,
    InstrumentEconomics,
    LatencyModel,
    OrderStyle,
    Side,
    SpreadModel,
    ZeroSlippageModel,
)
from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.identity import (
    EventId,
    ProviderInstrumentRef,
    RunId,
    TradableInstrumentId,
)
from btg_ai_trader.observer.market import Tick
from btg_ai_trader.observer.provenance import CodeRevision, ConfigHash, ContentHash
from btg_ai_trader.observer.temporal import EventTime, ObservationTimes
from btg_ai_trader.replay.core import CausalMarketReplaySchedule
from btg_ai_trader.scenario_engine import (
    ScenarioGrid,
    ScenarioShock,
    ScenarioSpec,
    ShockTarget,
    run_economic_scenario_grid,
    run_economic_stress,
)
from btg_ai_trader.scenario_engine.stress import _apply_shocks


REV = CodeRevision("b" * 40)


def uuid_text(num: int) -> str:
    return str(UUID(int=num))


def make_tick(
    seq: int,
    ts: datetime,
    iid: TradableInstrumentId,
    bid: Decimal,
    ask: Decimal,
) -> EventEnvelope:
    return EventEnvelope(
        event_id=EventId(uuid_text(100 + seq)),
        event_type=EventType.TICK,
        source=ProviderInstrumentRef("xp", "market", "WINV26"),
        instrument_id=iid,
        times=ObservationTimes(
            event_time=EventTime(ts, "fixture-clock", timedelta(microseconds=1)),
            ingestion_time=ts,
            knowledge_time=ts,
        ),
        payload=Tick(bid=bid, ask=ask, last=bid, volume=Decimal("10")),
    )


def make_action(
    num: int,
    ts: datetime,
    iid: TradableInstrumentId,
    side: Side,
) -> BacktestAction:
    return BacktestAction(
        action_id=ActionIdentity(uuid_text(num)),
        instrument_id=iid,
        side=side,
        quantity=Decimal("10"),
        order_style=OrderStyle.MARKET,
        knowledge_cutoff=ts,
        decision_time=ts,
        order_ready_time=ts,
    )


def fixture_bundle() -> tuple[
    TradableInstrumentId,
    InstrumentEconomics,
    EconomicAssumptions,
    list[BacktestAction],
    CausalMarketReplaySchedule,
    BacktestResult,
]:
    iid = TradableInstrumentId(uuid_text(1))
    econ = InstrumentEconomics(iid, "BRL", Decimal("1"), Decimal("0.5"), Decimal("1"))
    assumptions = EconomicAssumptions(
        assumptions_id="base",
        spread_model=SpreadModel(),
        slippage_model=ZeroSlippageModel(),
        fee_schedule=FeeSchedule(
            "fee",
            fixed_per_order=Decimal("1"),
            per_unit=Decimal("0.1"),
            bps_rate=Decimal("1"),
        ),
        latency_model=LatencyModel(),
        execution_policy=ExecutionPolicy(),
    )
    t0 = datetime(2026, 9, 22, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 9, 22, 10, 0, 1, tzinfo=UTC)
    actions = [
        make_action(1, t0, iid, Side.BUY),
        make_action(2, t1, iid, Side.SELL),
    ]
    events = [
        make_tick(1, t0, iid, Decimal("99.5"), Decimal("100")),
        make_tick(2, t1, iid, Decimal("110"), Decimal("110.5")),
    ]
    schedule = CausalMarketReplaySchedule(
        events,
        run_id=RunId(uuid_text(50)),
        code_revision=REV,
        config_hash=ConfigHash("1" * 64),
        provider_id="xp",
        capture_scope="market",
    )
    baseline = DeterministicEconomicBacktester(
        econ,
        assumptions,
        code_revision=REV,
        end_of_window_policy=EndOfWindowPolicy.KEEP_OPEN,
    ).run(actions=actions, replay_schedule=schedule)
    return iid, econ, assumptions, actions, schedule, baseline


def scenario(
    baseline: BacktestResult,
    scenario_id: str,
    shocks: tuple[ScenarioShock, ...],
    constraints: tuple[str, ...] = (),
) -> ScenarioSpec:
    return ScenarioSpec(
        scenario_id=scenario_id,
        baseline_evidence_ref=baseline.manifest.manifest_hash.value,
        shocks=shocks,
        structural_constraints=constraints,
        predeclared=True,
        research_history_ref="history",
        code_revision=REV.value,
    )


def test_apply_shocks_all_supported_dimensions() -> None:
    _, _, assumptions, _, _, _ = fixture_bundle()

    fee = _apply_shocks(
        assumptions,
        (ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("2"), "multiplier"),),
    )
    assert fee.fee_schedule.fixed_per_order == Decimal("2")
    assert fee.fee_schedule.per_unit == Decimal("0.2")
    assert fee.fee_schedule.bps_rate == Decimal("2")

    zero = _apply_shocks(
        assumptions,
        (ScenarioShock(ShockTarget.SLIPPAGE_POINTS, Decimal("0"), "points"),),
    )
    assert isinstance(zero.slippage_model, ZeroSlippageModel)

    slip = _apply_shocks(
        assumptions,
        (ScenarioShock(ShockTarget.SLIPPAGE_POINTS, Decimal("0.5"), "points"),),
    )
    assert isinstance(slip.slippage_model, FixedPointsSlippageModel)
    assert slip.slippage_model.adverse_points == Decimal("0.5")

    latency = _apply_shocks(
        assumptions,
        (ScenarioShock(ShockTarget.TRANSIT_LATENCY_US, Decimal("250"), "microseconds"),),
    )
    assert latency.latency_model.transit_latency_us == 250

    with pytest.raises(ValueError, match="integral Decimal"):
        _apply_shocks(
            assumptions,
            (
                ScenarioShock(
                    ShockTarget.TRANSIT_LATENCY_US,
                    Decimal("1.5"),
                    "microseconds",
                ),
            ),
        )

    combined = _apply_shocks(
        assumptions,
        (
            ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("1.5"), "multiplier"),
            ScenarioShock(ShockTarget.SLIPPAGE_POINTS, Decimal("0.25"), "points"),
            ScenarioShock(ShockTarget.TRANSIT_LATENCY_US, Decimal("100"), "microseconds"),
        ),
    )
    assert combined.fee_schedule.fixed_per_order == Decimal("1.5")
    assert isinstance(combined.slippage_model, FixedPointsSlippageModel)
    assert combined.latency_model.transit_latency_us == 100


def test_run_economic_stress_and_grid_preserve_sprint3_identity() -> None:
    _, econ, assumptions, actions, schedule, baseline = fixture_bundle()
    fee_scenario = scenario(
        baseline,
        "01-fee",
        (ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("2"), "multiplier"),),
    )
    evidence = run_economic_stress(
        fee_scenario,
        baseline_result=baseline,
        actions=actions,
        replay_schedule=schedule,
        instrument_economics=econ,
        base_assumptions=assumptions,
        end_of_window_policy=EndOfWindowPolicy.KEEP_OPEN,
        code_revision=REV,
    )
    assert evidence.baseline_manifest_hash == baseline.manifest.manifest_hash.value
    assert evidence.stressed_manifest_hash == evidence.result.manifest.manifest_hash.value
    assert evidence.result.manifest.verify_integrity()
    assert evidence.action_hash == baseline.manifest.input_boundary.actions_hash.value
    assert evidence.result.metrics.net_realized_pnl < baseline.metrics.net_realized_pnl

    slip_scenario = scenario(
        baseline,
        "02-slip",
        (ScenarioShock(ShockTarget.SLIPPAGE_POINTS, Decimal("0.5"), "points"),),
    )
    grid = ScenarioGrid("economic-grid", (fee_scenario, slip_scenario), True)
    results = run_economic_scenario_grid(
        grid,
        baseline_result=baseline,
        actions=actions,
        replay_schedule=schedule,
        instrument_economics=econ,
        base_assumptions=assumptions,
        end_of_window_policy=EndOfWindowPolicy.KEEP_OPEN,
        code_revision=REV,
    )
    assert tuple(item.scenario_id for item in results) == ("01-fee", "02-slip")


def test_run_economic_stress_rejects_upstream_identity_drift() -> None:
    iid, econ, assumptions, actions, schedule, baseline = fixture_bundle()
    valid = scenario(
        baseline,
        "01-fee",
        (ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("2"), "multiplier"),),
    )

    bad_manifest = replace(
        baseline.manifest,
        manifest_hash=ContentHash("0" * 64),
    )
    bad_baseline = replace(baseline, manifest=bad_manifest)
    with pytest.raises(ValueError, match="integrity verification failed"):
        run_economic_stress(
            valid,
            baseline_result=bad_baseline,
            actions=actions,
            replay_schedule=schedule,
            instrument_economics=econ,
            base_assumptions=assumptions,
            end_of_window_policy=EndOfWindowPolicy.KEEP_OPEN,
            code_revision=REV,
        )

    wrong_ref = ScenarioSpec(
        scenario_id="wrong-ref",
        baseline_evidence_ref="0" * 64,
        shocks=(ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("2"), "multiplier"),),
        structural_constraints=(),
        predeclared=True,
        research_history_ref="history",
        code_revision=REV.value,
    )
    with pytest.raises(ValueError, match="baseline_evidence_ref"):
        run_economic_stress(
            wrong_ref,
            baseline_result=baseline,
            actions=actions,
            replay_schedule=schedule,
            instrument_economics=econ,
            base_assumptions=assumptions,
            end_of_window_policy=EndOfWindowPolicy.KEEP_OPEN,
            code_revision=REV,
        )

    with pytest.raises(ValueError, match="BacktestAction sequence"):
        run_economic_stress(
            valid,
            baseline_result=baseline,
            actions=actions[:1],
            replay_schedule=schedule,
            instrument_economics=econ,
            base_assumptions=assumptions,
            end_of_window_policy=EndOfWindowPolicy.KEEP_OPEN,
            code_revision=REV,
        )

    other_schedule = CausalMarketReplaySchedule(
        tuple(schedule.events),
        run_id=RunId(uuid_text(51)),
        code_revision=REV,
        config_hash=ConfigHash("1" * 64),
        provider_id="xp",
        capture_scope="market",
    )
    with pytest.raises(ValueError, match="causal replay boundary"):
        run_economic_stress(
            valid,
            baseline_result=baseline,
            actions=actions,
            replay_schedule=other_schedule,
            instrument_economics=econ,
            base_assumptions=assumptions,
            end_of_window_policy=EndOfWindowPolicy.KEEP_OPEN,
            code_revision=REV,
        )

    other_iid = TradableInstrumentId(uuid_text(2))
    other_econ = InstrumentEconomics(
        other_iid, "BRL", Decimal("1"), Decimal("0.5"), Decimal("1")
    )
    with pytest.raises(ValueError, match="instrument identity"):
        run_economic_stress(
            valid,
            baseline_result=baseline,
            actions=actions,
            replay_schedule=schedule,
            instrument_economics=other_econ,
            base_assumptions=assumptions,
            end_of_window_policy=EndOfWindowPolicy.KEEP_OPEN,
            code_revision=REV,
        )

    changed_econ = InstrumentEconomics(
        iid, "BRL", Decimal("2"), Decimal("0.5"), Decimal("1")
    )
    with pytest.raises(ValueError, match="instrument economics"):
        run_economic_stress(
            valid,
            baseline_result=baseline,
            actions=actions,
            replay_schedule=schedule,
            instrument_economics=changed_econ,
            base_assumptions=assumptions,
            end_of_window_policy=EndOfWindowPolicy.KEEP_OPEN,
            code_revision=REV,
        )

    changed_assumptions = EconomicAssumptions(
        assumptions_id="changed",
        spread_model=assumptions.spread_model,
        slippage_model=assumptions.slippage_model,
        fee_schedule=FeeSchedule("changed-fee", fixed_per_order=Decimal("5")),
        latency_model=assumptions.latency_model,
        execution_policy=assumptions.execution_policy,
    )
    with pytest.raises(ValueError, match="assumptions/end-of-window"):
        run_economic_stress(
            valid,
            baseline_result=baseline,
            actions=actions,
            replay_schedule=schedule,
            instrument_economics=econ,
            base_assumptions=changed_assumptions,
            end_of_window_policy=EndOfWindowPolicy.KEEP_OPEN,
            code_revision=REV,
        )


def test_run_economic_stress_detects_kernel_output_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, econ, assumptions, actions, schedule, baseline = fixture_bundle()
    spec = scenario(
        baseline,
        "01-fee",
        (ScenarioShock(ShockTarget.FEE_MULTIPLIER, Decimal("2"), "multiplier"),),
    )

    real_evidence = run_economic_stress(
        spec,
        baseline_result=baseline,
        actions=actions,
        replay_schedule=schedule,
        instrument_economics=econ,
        base_assumptions=assumptions,
        end_of_window_policy=EndOfWindowPolicy.KEEP_OPEN,
        code_revision=REV,
    )

    class FakeEngine:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def run(self, *args: object, **kwargs: object) -> BacktestResult:
            return fake_result

    changed_boundary = replace(
        real_evidence.result.manifest.input_boundary,
        actions_hash=ContentHash("f" * 64),
    )
    changed_manifest = replace(
        real_evidence.result.manifest,
        input_boundary=changed_boundary,
    )
    fake_result = replace(real_evidence.result, manifest=changed_manifest)
    monkeypatch.setattr(stress_module, "DeterministicEconomicBacktester", FakeEngine)
    with pytest.raises(RuntimeError, match="action identity drift"):
        run_economic_stress(
            spec,
            baseline_result=baseline,
            actions=actions,
            replay_schedule=schedule,
            instrument_economics=econ,
            base_assumptions=assumptions,
            end_of_window_policy=EndOfWindowPolicy.KEEP_OPEN,
            code_revision=REV,
        )

    changed_boundary = replace(
        real_evidence.result.manifest.input_boundary,
        replay_boundary=other_replay_boundary(schedule),
    )
    changed_manifest = replace(
        real_evidence.result.manifest,
        input_boundary=changed_boundary,
    )
    fake_result = replace(real_evidence.result, manifest=changed_manifest)
    with pytest.raises(RuntimeError, match="replay-boundary drift"):
        run_economic_stress(
            spec,
            baseline_result=baseline,
            actions=actions,
            replay_schedule=schedule,
            instrument_economics=econ,
            base_assumptions=assumptions,
            end_of_window_policy=EndOfWindowPolicy.KEEP_OPEN,
            code_revision=REV,
        )


def other_replay_boundary(
    schedule: CausalMarketReplaySchedule,
) -> Any:
    return replace(schedule.boundary, capture_scope="different")
