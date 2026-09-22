"""Sprint 6 deterministic economic stress orchestration using Sprint 3 kernels."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from btg_ai_trader.backtesting import (
    BacktestAction,
    BacktestResult,
    DeterministicEconomicBacktester,
    EconomicAssumptions,
    EndOfWindowPolicy,
    FeeSchedule,
    FixedPointsSlippageModel,
    InstrumentEconomics,
    LatencyModel,
    ZeroSlippageModel,
    compute_actions_hash,
    compute_assumptions_hash,
    compute_instrument_economics_hash,
    compute_replay_boundary_fingerprint,
)
from btg_ai_trader.observer.provenance import CodeRevision
from btg_ai_trader.replay.core import CausalMarketReplaySchedule
from btg_ai_trader.scenario_engine.core import (
    ScenarioGrid,
    ScenarioShock,
    ScenarioSpec,
    ShockTarget,
)


@dataclass(frozen=True, slots=True)
class StressRunEvidence:
    scenario_id: str
    scenario_digest: str
    baseline_manifest_hash: str
    stressed_manifest_hash: str
    action_hash: str
    replay_boundary_digest: str
    baseline_assumptions_hash: str
    stressed_assumptions_hash: str
    result: BacktestResult


def apply_economic_shocks(
    base: EconomicAssumptions,
    shocks: Sequence[ScenarioShock],
) -> EconomicAssumptions:
    fee_schedule = base.fee_schedule
    slippage_model = base.slippage_model
    latency_model = base.latency_model

    for shock in shocks:
        if shock.target is ShockTarget.FEE_MULTIPLIER:
            fee_schedule = FeeSchedule(
                schedule_id=f"{base.fee_schedule.schedule_id}-s6-fee-{shock.value}",
                fixed_per_order=base.fee_schedule.fixed_per_order * shock.value,
                per_unit=base.fee_schedule.per_unit * shock.value,
                bps_rate=base.fee_schedule.bps_rate * shock.value,
                currency=base.fee_schedule.currency,
                effective_from=base.fee_schedule.effective_from,
                effective_until=base.fee_schedule.effective_until,
            )
        elif shock.target is ShockTarget.SLIPPAGE_POINTS:
            slippage_model = (
                ZeroSlippageModel()
                if shock.value == Decimal(0)
                else FixedPointsSlippageModel(shock.value)
            )
        else:
            integral = shock.value.to_integral_value()
            if integral != shock.value:
                raise ValueError("TRANSIT_LATENCY_US requires an integral Decimal")
            latency_model = LatencyModel(
                decision_latency_us=base.latency_model.decision_latency_us,
                transit_latency_us=int(integral),
            )

    suffix = "-".join(f"{shock.target.value}:{shock.value}" for shock in shocks)
    return EconomicAssumptions(
        assumptions_id=f"{base.assumptions_id}-s6-{suffix}",
        spread_model=base.spread_model,
        slippage_model=slippage_model,
        fee_schedule=fee_schedule,
        latency_model=latency_model,
        execution_policy=base.execution_policy,
    )


def run_economic_stress(
    scenario: ScenarioSpec,
    *,
    baseline_result: BacktestResult,
    actions: Sequence[BacktestAction],
    replay_schedule: CausalMarketReplaySchedule,
    instrument_economics: InstrumentEconomics,
    base_assumptions: EconomicAssumptions,
    end_of_window_policy: EndOfWindowPolicy,
    code_revision: CodeRevision | str,
) -> StressRunEvidence:
    if not scenario.predeclared:
        raise ValueError("economic stress requires a predeclared ScenarioSpec")
    baseline_manifest = baseline_result.manifest
    if not baseline_manifest.verify_integrity():
        raise ValueError("baseline BacktestRunManifest integrity verification failed")
    baseline_hash = baseline_manifest.manifest_hash.value
    if scenario.baseline_evidence_ref != baseline_hash:
        raise ValueError("scenario baseline_evidence_ref does not match baseline manifest")
    action_hash = compute_actions_hash(actions)
    if action_hash != baseline_manifest.input_boundary.actions_hash:
        raise ValueError("Sprint 6 stress must preserve exact BacktestAction sequence")
    if replay_schedule.boundary != baseline_manifest.input_boundary.replay_boundary:
        raise ValueError("Sprint 6 stress must preserve exact causal replay boundary")
    if instrument_economics.instrument_id != baseline_manifest.instrument_id:
        raise ValueError("Sprint 6 stress must preserve instrument identity")
    if (
        compute_instrument_economics_hash(instrument_economics)
        != baseline_manifest.instrument_economics_hash
    ):
        raise ValueError("Sprint 6 stress must preserve instrument economics")
    baseline_assumptions_hash = compute_assumptions_hash(
        base_assumptions,
        instrument_economics=instrument_economics,
        end_of_window_policy=end_of_window_policy,
    )
    if baseline_assumptions_hash != baseline_manifest.assumptions_hash:
        raise ValueError("base assumptions/end-of-window policy do not match baseline evidence")

    stressed_assumptions = apply_economic_shocks(base_assumptions, scenario.shocks)
    engine = DeterministicEconomicBacktester(
        instrument_economics=instrument_economics,
        assumptions=stressed_assumptions,
        code_revision=code_revision,
        end_of_window_policy=end_of_window_policy,
    )
    stressed = engine.run(actions=actions, replay_schedule=replay_schedule)
    if stressed.manifest.input_boundary.actions_hash != action_hash:
        raise RuntimeError("Sprint 3 kernel returned unexpected action identity drift")
    if stressed.manifest.input_boundary.replay_boundary != replay_schedule.boundary:
        raise RuntimeError("Sprint 3 kernel returned unexpected replay-boundary drift")
    return StressRunEvidence(
        scenario_id=scenario.scenario_id,
        scenario_digest=scenario.scenario_digest,
        baseline_manifest_hash=baseline_hash,
        stressed_manifest_hash=stressed.manifest.manifest_hash.value,
        action_hash=action_hash.value,
        replay_boundary_digest=compute_replay_boundary_fingerprint(
            stressed.manifest.input_boundary.replay_boundary
        ).value,
        baseline_assumptions_hash=baseline_assumptions_hash.value,
        stressed_assumptions_hash=stressed.manifest.assumptions_hash.value,
        result=stressed,
    )


def run_economic_scenario_grid(
    grid: ScenarioGrid,
    *,
    baseline_result: BacktestResult,
    actions: Sequence[BacktestAction],
    replay_schedule: CausalMarketReplaySchedule,
    instrument_economics: InstrumentEconomics,
    base_assumptions: EconomicAssumptions,
    end_of_window_policy: EndOfWindowPolicy,
    code_revision: CodeRevision | str,
) -> tuple[StressRunEvidence, ...]:
    return tuple(
        run_economic_stress(
            scenario,
            baseline_result=baseline_result,
            actions=actions,
            replay_schedule=replay_schedule,
            instrument_economics=instrument_economics,
            base_assumptions=base_assumptions,
            end_of_window_policy=end_of_window_policy,
            code_revision=code_revision,
        )
        for scenario in grid.scenarios
    )
