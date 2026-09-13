"""Pure fixture health evaluations; no real clock, feed, watchdog or process control."""

from dataclasses import FrozenInstanceError, replace
from typing import cast

import pytest

from btg_ai_trader.observer.health import (
    HealthAssessment,
    HealthPolicy,
    HealthReason,
    HealthSample,
    ObserverCapability,
    ReadinessStatus,
    RuntimePhase,
    SafetyPosture,
    evaluate_health,
    monotonic_elapsed_ns,
)
from btg_ai_trader.observer.values import MissingReason

POLICY = HealthPolicy("fixture-policy:v1", 10, 20)


def sample() -> HealthSample:
    return HealthSample("fixture-clock:a", 100, 100, 100)


def assessed(
    value: HealthSample,
    *,
    phase: RuntimePhase = RuntimePhase.RUNNING,
    posture: SafetyPosture = SafetyPosture.NORMAL,
    previous: HealthAssessment | None = None,
) -> HealthAssessment:
    return evaluate_health(
        value, phase=phase, requested_posture=posture, policy=POLICY, previous=previous
    ).assessment


def test_fresh_passive_readiness_is_scoped_and_has_no_prior_transition() -> None:
    result = evaluate_health(
        sample(),
        phase=RuntimePhase.RUNNING,
        requested_posture=SafetyPosture.NORMAL,
        policy=POLICY,
    )
    assert result.transition is None
    assert result.assessment.readiness is ReadinessStatus.READY
    assert result.assessment.capability is ObserverCapability.CONSUME_FRESH_OBSERVATIONS
    assert result.assessment.heartbeat_alive
    assert result.assessment.heartbeat_age_ns == 0
    assert result.assessment.market_age_ns == 0
    assert result.assessment.reasons == ()


def test_exact_timeout_is_fresh_but_one_nanosecond_later_is_stale() -> None:
    boundary = assessed(HealthSample("fixture-clock:a", 100, 90, 80))
    assert boundary.readiness is ReadinessStatus.READY
    later = assessed(HealthSample("fixture-clock:a", 101, 90, 80), previous=boundary)
    assert not later.heartbeat_alive
    assert later.readiness is ReadinessStatus.NOT_READY
    assert later.posture is SafetyPosture.DEGRADED
    assert HealthReason.HEARTBEAT_TIMEOUT in later.reasons
    assert HealthReason.MARKET_DATA_STALE in later.reasons


def test_fresh_heartbeat_does_not_imply_fresh_data_or_readiness() -> None:
    observed = assessed(replace(sample(), market_data_ns=79))
    assert observed.heartbeat_alive
    assert observed.readiness is ReadinessStatus.NOT_READY
    assert HealthReason.MARKET_DATA_STALE in observed.reasons


@pytest.mark.parametrize("reason", list(MissingReason))
def test_unknown_values_are_preserved_and_never_become_zero(reason: MissingReason) -> None:
    observed = assessed(HealthSample("fixture-clock:a", 100, reason, reason))
    assert observed.heartbeat_age_ns is reason
    assert observed.market_age_ns is reason
    assert observed.last_known_heartbeat_ns is None
    assert observed.last_known_market_ns is None
    assert not observed.heartbeat_alive
    assert observed.readiness is ReadinessStatus.NOT_READY
    assert HealthReason.HEARTBEAT_MISSING in observed.reasons
    assert HealthReason.MARKET_DATA_MISSING in observed.reasons


@pytest.mark.parametrize(
    "phase", [item for item in RuntimePhase if item is not RuntimePhase.RUNNING]
)
def test_lifecycle_phases_are_not_readiness(phase: RuntimePhase) -> None:
    observed = assessed(sample(), phase=phase)
    assert observed.heartbeat_alive
    assert observed.posture is SafetyPosture.NORMAL
    assert observed.readiness is ReadinessStatus.NOT_READY
    assert HealthReason.PHASE_BLOCKED in observed.reasons


@pytest.mark.parametrize("phase", [RuntimePhase.RECOVERING, RuntimePhase.RECONCILING])
def test_recovery_and_halt_are_distinct_simultaneous_dimensions(phase: RuntimePhase) -> None:
    observed = assessed(sample(), phase=phase, posture=SafetyPosture.SAFE_HALT)
    assert observed.phase is phase
    assert observed.posture is SafetyPosture.SAFE_HALT
    assert observed.readiness is ReadinessStatus.NOT_READY
    assert HealthReason.PHASE_BLOCKED in observed.reasons
    assert HealthReason.POSTURE_BLOCKED in observed.reasons


@pytest.mark.parametrize(
    "posture", [SafetyPosture.DEGRADED, SafetyPosture.SAFE_HALT, SafetyPosture.EMERGENCY_STOP]
)
def test_fresh_evidence_cannot_unlatch_restrictive_posture(posture: SafetyPosture) -> None:
    previous = assessed(sample(), posture=posture)
    current = assessed(HealthSample("fixture-clock:a", 101, 101, 101), previous=previous)
    assert current.posture is posture
    assert current.readiness is ReadinessStatus.NOT_READY
    assert current.heartbeat_alive


def test_fault_driven_degradation_does_not_automatically_recover() -> None:
    failed = assessed(replace(sample(), heartbeat_ns=MissingReason.UNKNOWN))
    recovered_metrics = assessed(
        HealthSample("fixture-clock:a", 101, 101, 101), previous=failed
    )
    assert recovered_metrics.posture is SafetyPosture.DEGRADED
    assert recovered_metrics.readiness is ReadinessStatus.NOT_READY


def test_escalation_is_allowed_but_returns_only_immutable_evidence() -> None:
    previous = assessed(sample(), posture=SafetyPosture.SAFE_HALT)
    result = evaluate_health(
        HealthSample("fixture-clock:a", 101, 101, 101),
        phase=RuntimePhase.RUNNING,
        requested_posture=SafetyPosture.EMERGENCY_STOP,
        policy=POLICY,
        previous=previous,
    )
    assert result.transition is not None
    assert result.transition.before is previous
    assert result.transition.after is result.assessment
    assert result.assessment.posture is SafetyPosture.EMERGENCY_STOP
    assert previous.posture is SafetyPosture.SAFE_HALT
    field_name = "posture"
    with pytest.raises(FrozenInstanceError):
        setattr(result.assessment, field_name, SafetyPosture.NORMAL)


def test_startup_missing_evidence_is_blocked_without_inventing_latched_fault() -> None:
    initial = assessed(
        HealthSample("fixture-clock:a", 0, MissingReason.UNKNOWN, MissingReason.UNKNOWN),
        phase=RuntimePhase.STARTING,
    )
    assert initial.posture is SafetyPosture.NORMAL
    result = evaluate_health(
        sample(),
        phase=RuntimePhase.RUNNING,
        requested_posture=SafetyPosture.NORMAL,
        policy=POLICY,
        previous=initial,
    )
    assert result.assessment.readiness is ReadinessStatus.READY
    assert result.transition is not None
    assert result.transition.before.phase is RuntimePhase.STARTING


def test_stable_state_emits_assessment_without_fabricated_transition() -> None:
    previous = assessed(sample())
    result = evaluate_health(
        HealthSample("fixture-clock:a", 101, 101, 101),
        phase=RuntimePhase.RUNNING,
        requested_posture=SafetyPosture.NORMAL,
        policy=POLICY,
        previous=previous,
    )
    assert result.transition is None
    assert result.assessment.sample.now_ns == 101


@pytest.mark.parametrize("bad", [0, -1, True, 1.0, None])
def test_thresholds_must_be_explicit_positive_integers(bad: object) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        replace(POLICY, heartbeat_timeout_ns=cast(int, bad))
    with pytest.raises(ValueError, match="positive integer"):
        replace(POLICY, market_staleness_ns=cast(int, bad))


@pytest.mark.parametrize("bad", [-1, True, 1.0, None])
def test_malformed_monotonic_readings_fail_closed(bad: object) -> None:
    with pytest.raises(ValueError, match="nonnegative integer"):
        replace(sample(), now_ns=cast(int, bad))
    with pytest.raises(ValueError, match="nonnegative integer"):
        replace(sample(), heartbeat_ns=cast(int, bad))
    with pytest.raises(ValueError, match="nonnegative integer"):
        monotonic_elapsed_ns(cast(int, bad), 100)


def test_future_readings_and_backward_elapsed_time_are_rejected() -> None:
    with pytest.raises(ValueError, match="future"):
        replace(sample(), heartbeat_ns=101)
    with pytest.raises(ValueError, match="future"):
        replace(sample(), market_data_ns=101)
    with pytest.raises(ValueError, match="backward"):
        monotonic_elapsed_ns(101, 100)
    assert monotonic_elapsed_ns(100, 100) == 0
    assert monotonic_elapsed_ns(0, 100) == 100


def test_sample_time_and_clock_scope_require_continuity() -> None:
    previous = assessed(sample())
    with pytest.raises(ValueError, match="backward"):
        assessed(HealthSample("fixture-clock:a", 99, 99, 99), previous=previous)
    with pytest.raises(ValueError, match="clock scope"):
        assessed(replace(sample(), clock_scope="fixture-clock:b"), previous=previous)


@pytest.mark.parametrize("bad", ["", None, MissingReason.UNKNOWN])
def test_unknown_clock_scope_is_rejected(bad: object) -> None:
    with pytest.raises(ValueError, match="clock_scope"):
        replace(sample(), clock_scope=cast(str, bad))


def test_known_heartbeat_and_market_readings_cannot_move_backward() -> None:
    previous = assessed(sample())
    with pytest.raises(ValueError, match="heartbeat.*backward"):
        assessed(HealthSample("fixture-clock:a", 101, 99, 101), previous=previous)
    with pytest.raises(ValueError, match="market data.*backward"):
        assessed(HealthSample("fixture-clock:a", 101, 101, 99), previous=previous)


def test_missing_sample_preserves_ordering_watermark_without_fabricating_age() -> None:
    previous = assessed(sample())
    missing = assessed(
        HealthSample("fixture-clock:a", 101, MissingReason.UNKNOWN, MissingReason.UNKNOWN),
        previous=previous,
    )
    assert missing.heartbeat_age_ns is MissingReason.UNKNOWN
    assert missing.market_age_ns is MissingReason.UNKNOWN
    assert missing.last_known_heartbeat_ns == 100
    assert missing.last_known_market_ns == 100
    with pytest.raises(ValueError, match="heartbeat.*backward"):
        assessed(HealthSample("fixture-clock:a", 102, 99, 102), previous=missing)
    with pytest.raises(ValueError, match="market data.*backward"):
        assessed(HealthSample("fixture-clock:a", 102, 102, 99), previous=missing)


def test_evaluator_requires_distinct_validated_input_types() -> None:
    with pytest.raises(ValueError, match="distinct enum"):
        assessed(sample(), phase=cast(RuntimePhase, SafetyPosture.NORMAL))
    with pytest.raises(ValueError, match="distinct enum"):
        assessed(sample(), posture=cast(SafetyPosture, RuntimePhase.RUNNING))
    with pytest.raises(ValueError, match="validated health"):
        assessed(cast(HealthSample, None))
    with pytest.raises(ValueError, match="previous"):
        assessed(sample(), previous=cast(HealthAssessment, "bad"))


def test_identical_inputs_produce_identical_evidence_without_real_clock() -> None:
    assert assessed(sample()) == assessed(sample())
    first = assessed(sample())
    assert assessed(sample(), previous=first) == assessed(sample(), previous=first)


@pytest.mark.parametrize("bad", [None, 99, 101, -1, True, 1.0])
def test_inconsistent_previous_heartbeat_watermark_is_rejected(bad: object) -> None:
    previous = replace(assessed(sample()), last_known_heartbeat_ns=cast(int | None, bad))
    with pytest.raises(ValueError, match="previous heartbeat watermark"):
        assessed(HealthSample("fixture-clock:a", 101, 99, 101), previous=previous)


@pytest.mark.parametrize("bad", [None, 99, 101, -1, True, 1.0])
def test_inconsistent_previous_market_watermark_is_rejected(bad: object) -> None:
    previous = replace(assessed(sample()), last_known_market_ns=cast(int | None, bad))
    with pytest.raises(ValueError, match="previous market data watermark"):
        assessed(HealthSample("fixture-clock:a", 101, 101, 99), previous=previous)


@pytest.mark.parametrize("bad", [102, -1, True, 1.0])
def test_missing_previous_sample_still_requires_valid_retained_watermarks(
    bad: object,
) -> None:
    missing = assessed(
        HealthSample("fixture-clock:a", 101, MissingReason.UNKNOWN, MissingReason.UNKNOWN)
    )
    heartbeat = replace(missing, last_known_heartbeat_ns=cast(int, bad))
    market = replace(missing, last_known_market_ns=cast(int, bad))
    current = HealthSample("fixture-clock:a", 102, 102, 102)
    with pytest.raises(ValueError, match="previous heartbeat watermark"):
        assessed(current, previous=heartbeat)
    with pytest.raises(ValueError, match="previous market data watermark"):
        assessed(current, previous=market)


@pytest.mark.parametrize("known", [100, 102])
def test_valid_unknown_carryforward_accepts_nonregressive_return_to_known(
    known: int,
) -> None:
    first = assessed(sample())
    missing = assessed(
        HealthSample("fixture-clock:a", 101, MissingReason.UNKNOWN, MissingReason.UNKNOWN),
        previous=first,
    )
    current = assessed(
        HealthSample("fixture-clock:a", 102, known, known), previous=missing
    )
    assert missing.heartbeat_age_ns is MissingReason.UNKNOWN
    assert missing.market_age_ns is MissingReason.UNKNOWN
    assert missing.last_known_heartbeat_ns == 100
    assert missing.last_known_market_ns == 100
    assert current.last_known_heartbeat_ns == known
    assert current.last_known_market_ns == known
    assert current.heartbeat_age_ns == 102 - known
    assert current.market_age_ns == 102 - known
    assert current.posture is SafetyPosture.DEGRADED


def test_previous_sample_requires_validated_health_sample() -> None:
    previous = replace(assessed(sample()), sample=cast(HealthSample, None))
    with pytest.raises(ValueError, match="previous sample must be HealthSample"):
        assessed(sample(), previous=previous)
