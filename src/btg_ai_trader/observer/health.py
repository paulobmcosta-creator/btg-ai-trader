"""Pure passive Observer health evaluation; no clock reads or operational effects."""

from dataclasses import dataclass
from enum import Enum

from btg_ai_trader.observer.values import MissingReason, require_text

type MonotonicValue = int | MissingReason


def _reading(value: int, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a nonnegative integer monotonic reading")


def monotonic_elapsed_ns(start_ns: int, end_ns: int) -> int:
    """Caller establishes common clock scope; these values are not event timestamps."""
    _reading(start_ns, "start_ns")
    _reading(end_ns, "end_ns")
    if end_ns < start_ns:
        raise ValueError("monotonic readings cannot move backward")
    return end_ns - start_ns


@dataclass(frozen=True, slots=True)
class TransitLatencyEvidence:
    """Passive same-scope monotonic transit measurement; never inferred from wall-clock time."""

    clock_scope: str
    ingress_ns: int
    available_ns: int
    latency_ns: int

    def __post_init__(self) -> None:
        require_text(self.clock_scope, "clock_scope")
        _reading(self.ingress_ns, "ingress_ns")
        _reading(self.available_ns, "available_ns")
        _reading(self.latency_ns, "latency_ns")
        expected = monotonic_elapsed_ns(self.ingress_ns, self.available_ns)
        if self.latency_ns != expected:
            raise ValueError("latency_ns must equal the monotonic elapsed interval")


def measure_transit_latency(
    clock_scope: str, ingress_ns: int, available_ns: int
) -> TransitLatencyEvidence:
    """Measure explicit ingress→availability latency without reading a clock implicitly."""
    require_text(clock_scope, "clock_scope")
    return TransitLatencyEvidence(
        clock_scope,
        ingress_ns,
        available_ns,
        monotonic_elapsed_ns(ingress_ns, available_ns),
    )


class RuntimePhase(Enum):
    STARTING = "STARTING"
    RECOVERING = "RECOVERING"
    RECONCILING = "RECONCILING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class SafetyPosture(Enum):
    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    SAFE_HALT = "SAFE_HALT"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class ObserverCapability(Enum):
    CONSUME_FRESH_OBSERVATIONS = "CONSUME_FRESH_OBSERVATIONS"


class ReadinessStatus(Enum):
    READY = "READY"
    NOT_READY = "NOT_READY"


class HealthReason(Enum):
    PHASE_BLOCKED = "PHASE_BLOCKED"
    POSTURE_BLOCKED = "POSTURE_BLOCKED"
    HEARTBEAT_MISSING = "HEARTBEAT_MISSING"
    HEARTBEAT_TIMEOUT = "HEARTBEAT_TIMEOUT"
    MARKET_DATA_MISSING = "MARKET_DATA_MISSING"
    MARKET_DATA_STALE = "MARKET_DATA_STALE"


@dataclass(frozen=True, slots=True)
class HealthPolicy:
    policy_ref: str
    heartbeat_timeout_ns: int
    market_staleness_ns: int

    def __post_init__(self) -> None:
        require_text(self.policy_ref, "policy_ref")
        for field in ("heartbeat_timeout_ns", "market_staleness_ns"):
            value = getattr(self, field)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{field} must be an explicit positive integer")


@dataclass(frozen=True, slots=True)
class HealthSample:
    clock_scope: str
    now_ns: int
    heartbeat_ns: MonotonicValue
    market_data_ns: MonotonicValue

    def __post_init__(self) -> None:
        require_text(self.clock_scope, "clock_scope")
        _reading(self.now_ns, "now_ns")
        for field in ("heartbeat_ns", "market_data_ns"):
            value = getattr(self, field)
            if isinstance(value, MissingReason):
                continue
            _reading(value, field)
            if value > self.now_ns:
                raise ValueError(f"{field} cannot lie in the monotonic future")


@dataclass(frozen=True, slots=True)
class HealthAssessment:
    sample: HealthSample
    policy: HealthPolicy
    phase: RuntimePhase
    posture: SafetyPosture
    capability: ObserverCapability
    readiness: ReadinessStatus
    heartbeat_alive: bool
    heartbeat_age_ns: MonotonicValue
    market_age_ns: MonotonicValue
    reasons: tuple[HealthReason, ...]
    last_known_heartbeat_ns: int | None
    last_known_market_ns: int | None


@dataclass(frozen=True, slots=True)
class HealthTransition:
    before: HealthAssessment
    after: HealthAssessment


@dataclass(frozen=True, slots=True)
class HealthEvaluation:
    assessment: HealthAssessment
    transition: HealthTransition | None


def _age(sample: HealthSample, value: MonotonicValue) -> MonotonicValue:
    if isinstance(value, MissingReason):
        return value
    return monotonic_elapsed_ns(value, sample.now_ns)


def _watermark(value: MonotonicValue, previous: int | None, field: str) -> int | None:
    if isinstance(value, MissingReason):
        return previous
    if previous is not None and value < previous:
        raise ValueError(f"{field} cannot move backward within its clock scope")
    return value


def _validate_previous_watermark(
    value: MonotonicValue, watermark: int | None, now_ns: int, field: str
) -> None:
    if watermark is not None:
        _reading(watermark, field)
        if watermark > now_ns:
            raise ValueError(f"{field} cannot lie in the previous sample's future")
    if not isinstance(value, MissingReason) and watermark != value:
        raise ValueError(f"{field} must equal its known previous sample reading")


def evaluate_health(
    sample: HealthSample,
    *,
    phase: RuntimePhase,
    requested_posture: SafetyPosture,
    policy: HealthPolicy,
    previous: HealthAssessment | None = None,
) -> HealthEvaluation:
    """Return evidence only; restrictive posture never unlatches in this evaluator."""
    if not isinstance(sample, HealthSample) or not isinstance(policy, HealthPolicy):
        raise ValueError("sample and policy must be validated health records")
    if not isinstance(phase, RuntimePhase) or not isinstance(requested_posture, SafetyPosture):
        raise ValueError("runtime phase and safety posture must use their distinct enum types")
    if previous is not None:
        if not isinstance(previous, HealthAssessment):
            raise ValueError("previous must be HealthAssessment")
        if not isinstance(previous.sample, HealthSample):
            raise ValueError("previous sample must be HealthSample")
        _validate_previous_watermark(
            previous.sample.heartbeat_ns,
            previous.last_known_heartbeat_ns,
            previous.sample.now_ns,
            "previous heartbeat watermark",
        )
        _validate_previous_watermark(
            previous.sample.market_data_ns,
            previous.last_known_market_ns,
            previous.sample.now_ns,
            "previous market data watermark",
        )
        if sample.clock_scope != previous.sample.clock_scope:
            raise ValueError("clock scope change requires explicit recovery continuity")
        monotonic_elapsed_ns(previous.sample.now_ns, sample.now_ns)
    heartbeat_watermark = _watermark(
        sample.heartbeat_ns,
        previous.last_known_heartbeat_ns if previous else None,
        "heartbeat",
    )
    market_watermark = _watermark(
        sample.market_data_ns,
        previous.last_known_market_ns if previous else None,
        "market data",
    )
    heartbeat_age = _age(sample, sample.heartbeat_ns)
    market_age = _age(sample, sample.market_data_ns)
    heartbeat_alive = (
        isinstance(heartbeat_age, int) and heartbeat_age <= policy.heartbeat_timeout_ns
    )
    market_fresh = isinstance(market_age, int) and market_age <= policy.market_staleness_ns
    reasons: list[HealthReason] = []
    if isinstance(heartbeat_age, MissingReason):
        reasons.append(HealthReason.HEARTBEAT_MISSING)
    elif not heartbeat_alive:
        reasons.append(HealthReason.HEARTBEAT_TIMEOUT)
    if isinstance(market_age, MissingReason):
        reasons.append(HealthReason.MARKET_DATA_MISSING)
    elif not market_fresh:
        reasons.append(HealthReason.MARKET_DATA_STALE)
    if phase is not RuntimePhase.RUNNING:
        reasons.append(HealthReason.PHASE_BLOCKED)
    rank = {
        SafetyPosture.NORMAL: 0,
        SafetyPosture.DEGRADED: 1,
        SafetyPosture.SAFE_HALT: 2,
        SafetyPosture.EMERGENCY_STOP: 3,
    }
    posture = requested_posture
    if previous is not None and rank[previous.posture] > rank[posture]:
        posture = previous.posture
    if phase is RuntimePhase.RUNNING and not (heartbeat_alive and market_fresh):
        if posture is SafetyPosture.NORMAL:
            posture = SafetyPosture.DEGRADED
    if posture is not SafetyPosture.NORMAL:
        reasons.append(HealthReason.POSTURE_BLOCKED)
    assessment = HealthAssessment(
        sample=sample,
        policy=policy,
        phase=phase,
        posture=posture,
        capability=ObserverCapability.CONSUME_FRESH_OBSERVATIONS,
        readiness=ReadinessStatus.NOT_READY if reasons else ReadinessStatus.READY,
        heartbeat_alive=heartbeat_alive,
        heartbeat_age_ns=heartbeat_age,
        market_age_ns=market_age,
        reasons=tuple(reasons),
        last_known_heartbeat_ns=heartbeat_watermark,
        last_known_market_ns=market_watermark,
    )
    transition = None
    if previous is not None and (
        previous.phase != assessment.phase
        or previous.posture != assessment.posture
        or previous.readiness != assessment.readiness
    ):
        transition = HealthTransition(previous, assessment)
    return HealthEvaluation(assessment, transition)
