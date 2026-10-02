"""Deterministic side-effect-free Risk Engine core (Sprint 7)."""

from __future__ import annotations

import hashlib
import json
import types
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, localcontext
from enum import Enum

from btg_ai_trader.observer.identity import TradableInstrumentId
from btg_ai_trader.statistical_baselines.metrics import DEFAULT_NUMERIC_POLICY, NumericPolicy

_VERIFIED_BOUNDARY_TOKEN = object()
_ENGINE_AUTHORIZATION_TOKEN = object()


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field_name} must be nonempty text without surrounding whitespace")


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_decimal(
    value: Decimal,
    field_name: str,
    *,
    nonnegative: bool = False,
    positive: bool = False,
) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    if nonnegative and value < Decimal(0):
        raise ValueError(f"{field_name} must be non-negative")
    if positive and value <= Decimal(0):
        raise ValueError(f"{field_name} must be positive")


def _jsonable(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, TradableInstrumentId):
        return value.value
    if isinstance(value, Mapping):
        return {
            str(k): _jsonable(v)
            for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [_jsonable(item) for item in value]
    return value


def _digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _jsonable(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _freeze_metrics(metrics: Mapping[str, Decimal]) -> Mapping[str, Decimal]:
    frozen: dict[str, Decimal] = {}
    for name, value in sorted(metrics.items()):
        _require_text(name, "metric_name")
        _require_decimal(value, f"metric[{name}]")
        frozen[name] = value
    return types.MappingProxyType(frozen)


class EvidenceQuality(str, Enum):
    VALID = "VALID"
    UNKNOWN = "UNKNOWN"
    STALE = "STALE"
    INCOMPLETE = "INCOMPLETE"


class EconomicDirection(str, Enum):
    INCREASE_LONG = "INCREASE_LONG"
    INCREASE_SHORT = "INCREASE_SHORT"
    DECREASE_LONG = "DECREASE_LONG"
    DECREASE_SHORT = "DECREASE_SHORT"


class SafetyPosture(str, Enum):
    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    SAFE_HALT = "SAFE_HALT"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class CommitmentReadiness(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class RiskDecision(str, Enum):
    REJECT = "REJECT"
    PERMIT = "PERMIT"


class RiskMetric(str, Enum):
    CURRENT_POSITION_EXPOSURE = "CURRENT_POSITION_EXPOSURE"
    COMMITTED_POTENTIAL_EXPOSURE = "COMMITTED_POTENTIAL_EXPOSURE"
    RISK_CAPACITY_RESERVATION = "RISK_CAPACITY_RESERVATION"
    WORST_CASE_EXPOSURE = "WORST_CASE_EXPOSURE"
    PROJECTED_WORST_CASE_EXPOSURE = "PROJECTED_WORST_CASE_EXPOSURE"
    PROJECTED_CAPACITY_USAGE = "PROJECTED_CAPACITY_USAGE"
    REQUESTED_EXPOSURE = "REQUESTED_EXPOSURE"
    DAILY_LOSS = "DAILY_LOSS"
    DRAWDOWN_AMOUNT = "DRAWDOWN_AMOUNT"
    DRAWDOWN_RATIO = "DRAWDOWN_RATIO"
    VALUE_AT_RISK = "VALUE_AT_RISK"
    EXPECTED_SHORTFALL = "EXPECTED_SHORTFALL"


class LimitOperator(str, Enum):
    LTE = "LTE"
    GTE = "GTE"


class TailEvidenceSourceKind(str, Enum):
    EMPIRICAL_OBSERVED = "EMPIRICAL_OBSERVED"
    SYNTHETIC_SCENARIO = "SYNTHETIC_SCENARIO"


class PnlLossConvention(str, Enum):
    NEGATIVE_PNL_IS_LOSS = "NEGATIVE_PNL_IS_LOSS"


class DrawdownSeriesKind(str, Enum):
    EQUITY = "EQUITY"
    NAV = "NAV"
    CAPITAL = "CAPITAL"


class DrawdownDenominatorConvention(str, Enum):
    EXPLICIT_POSITIVE_CAPITAL = "EXPLICIT_POSITIVE_CAPITAL"


class TailLossDirection(str, Enum):
    LOWER_IS_LOSS = "LOWER_IS_LOSS"
    HIGHER_IS_LOSS = "HIGHER_IS_LOSS"


class TailQuantileConvention(str, Enum):
    NEAREST_RANK = "NEAREST_RANK"


class CircuitStatus(str, Enum):
    NORMAL = "NORMAL"
    LATCHED = "LATCHED"


class AuthorizationInvalidity(str, Enum):
    NOT_ENGINE_ISSUED = "NOT_ENGINE_ISSUED"
    DECISION_NOT_PERMIT = "DECISION_NOT_PERMIT"
    DECISION_MISMATCH = "DECISION_MISMATCH"
    PROPOSAL_MISMATCH = "PROPOSAL_MISMATCH"
    STATE_MISMATCH = "STATE_MISMATCH"
    POLICY_MISMATCH = "POLICY_MISMATCH"
    NOT_YET_VALID = "NOT_YET_VALID"
    EXPIRED = "EXPIRED"
    ENVELOPE_EXCEEDS_PROPOSAL = "ENVELOPE_EXCEEDS_PROPOSAL"
    POLICY_NOT_EFFECTIVE = "POLICY_NOT_EFFECTIVE"


@dataclass(frozen=True, slots=True)
class RiskProposal:
    proposal_id: str
    instrument_id: TradableInstrumentId
    portfolio_id: str
    direction: EconomicDirection
    requested_quantity: Decimal
    quantity_unit: str
    requested_exposure: Decimal
    exposure_unit: str
    created_at: datetime
    source_digest: str
    proposal_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _require_text(self.proposal_id, "proposal_id")
        if not isinstance(self.instrument_id, TradableInstrumentId):
            raise ValueError("instrument_id must be TradableInstrumentId")
        _require_text(self.portfolio_id, "portfolio_id")
        _require_decimal(self.requested_quantity, "requested_quantity", positive=True)
        _require_text(self.quantity_unit, "quantity_unit")
        _require_decimal(self.requested_exposure, "requested_exposure", positive=True)
        _require_text(self.exposure_unit, "exposure_unit")
        _require_aware(self.created_at, "created_at")
        _require_text(self.source_digest, "source_digest")
        object.__setattr__(
            self,
            "proposal_digest",
            _digest(
                {
                    "proposal_id": self.proposal_id,
                    "instrument_id": self.instrument_id,
                    "portfolio_id": self.portfolio_id,
                    "direction": self.direction,
                    "requested_quantity": self.requested_quantity,
                    "quantity_unit": self.quantity_unit,
                    "requested_exposure": self.requested_exposure,
                    "exposure_unit": self.exposure_unit,
                    "created_at": self.created_at,
                    "source_digest": self.source_digest,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class ExposureState:
    current_position_exposure: Decimal
    committed_potential_exposure: Decimal
    risk_capacity_reservation: Decimal
    worst_case_exposure: Decimal
    unit: str
    source_digest: str
    quality: EvidenceQuality = EvidenceQuality.VALID
    exposure_digest: str = field(init=False)

    def __post_init__(self) -> None:
        for value, name in (
            (self.current_position_exposure, "current_position_exposure"),
            (self.committed_potential_exposure, "committed_potential_exposure"),
            (self.risk_capacity_reservation, "risk_capacity_reservation"),
            (self.worst_case_exposure, "worst_case_exposure"),
        ):
            _require_decimal(value, name, nonnegative=True)
        if self.worst_case_exposure < (
            self.current_position_exposure + self.committed_potential_exposure
        ):
            raise ValueError(
                "worst_case_exposure cannot be below current plus committed exposure"
            )
        _require_text(self.unit, "unit")
        _require_text(self.source_digest, "source_digest")
        object.__setattr__(
            self,
            "exposure_digest",
            _digest(
                {
                    "current_position_exposure": self.current_position_exposure,
                    "committed_potential_exposure": self.committed_potential_exposure,
                    "risk_capacity_reservation": self.risk_capacity_reservation,
                    "worst_case_exposure": self.worst_case_exposure,
                    "unit": self.unit,
                    "source_digest": self.source_digest,
                    "quality": self.quality,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class DailyLossState:
    recognized_pnl: Decimal
    currency: str
    pnl_source_id: str
    include_unrealized: bool
    loss_sign_convention: PnlLossConvention
    session_id: str
    session_start: datetime
    session_end: datetime
    session_calendar_id: str
    timezone_name: str
    reset_semantics: str
    source_digest: str
    quality: EvidenceQuality = EvidenceQuality.VALID
    daily_loss_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _require_decimal(self.recognized_pnl, "recognized_pnl")
        _require_text(self.currency, "currency")
        _require_text(self.pnl_source_id, "pnl_source_id")
        _require_text(self.session_id, "session_id")
        _require_aware(self.session_start, "session_start")
        _require_aware(self.session_end, "session_end")
        if self.session_end <= self.session_start:
            raise ValueError("daily-loss session must have positive duration")
        _require_text(self.session_calendar_id, "session_calendar_id")
        _require_text(self.timezone_name, "timezone_name")
        _require_text(self.reset_semantics, "reset_semantics")
        _require_text(self.source_digest, "source_digest")
        object.__setattr__(
            self,
            "daily_loss_digest",
            _digest(
                {
                    "recognized_pnl": self.recognized_pnl,
                    "currency": self.currency,
                    "pnl_source_id": self.pnl_source_id,
                    "include_unrealized": self.include_unrealized,
                    "loss_sign_convention": self.loss_sign_convention,
                    "session_id": self.session_id,
                    "session_start": self.session_start,
                    "session_end": self.session_end,
                    "session_calendar_id": self.session_calendar_id,
                    "timezone_name": self.timezone_name,
                    "reset_semantics": self.reset_semantics,
                    "source_digest": self.source_digest,
                    "quality": self.quality,
                }
            ),
        )

    @property
    def loss_amount(self) -> Decimal:
        return max(-self.recognized_pnl, Decimal(0))


@dataclass(frozen=True, slots=True)
class DailyLossPolicySemantics:
    currency: str
    pnl_source_id: str
    include_unrealized: bool
    loss_sign_convention: PnlLossConvention
    session_calendar_id: str
    timezone_name: str
    reset_semantics: str
    semantics_digest: str = field(init=False)

    def __post_init__(self) -> None:
        for value, name in (
            (self.currency, "currency"),
            (self.pnl_source_id, "pnl_source_id"),
            (self.session_calendar_id, "session_calendar_id"),
            (self.timezone_name, "timezone_name"),
            (self.reset_semantics, "reset_semantics"),
        ):
            _require_text(value, name)
        object.__setattr__(
            self,
            "semantics_digest",
            _digest(
                {
                    "currency": self.currency,
                    "pnl_source_id": self.pnl_source_id,
                    "include_unrealized": self.include_unrealized,
                    "loss_sign_convention": self.loss_sign_convention,
                    "session_calendar_id": self.session_calendar_id,
                    "timezone_name": self.timezone_name,
                    "reset_semantics": self.reset_semantics,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class DrawdownState:
    peak_value: Decimal
    current_value: Decimal
    unit: str
    capital_denominator: Decimal | None
    denominator_convention: DrawdownDenominatorConvention | None
    source_id: str
    series_kind: DrawdownSeriesKind
    peak_id: str
    current_id: str
    source_digest: str
    quality: EvidenceQuality = EvidenceQuality.VALID
    drawdown_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _require_decimal(self.peak_value, "peak_value")
        _require_decimal(self.current_value, "current_value")
        if self.current_value > self.peak_value:
            raise ValueError("current_value cannot exceed governed peak_value")
        if self.capital_denominator is not None:
            _require_decimal(
                self.capital_denominator,
                "capital_denominator",
                positive=True,
            )
            if self.denominator_convention is None:
                raise ValueError(
                    "capital_denominator requires explicit denominator_convention"
                )
        elif self.denominator_convention is not None:
            raise ValueError(
                "denominator_convention requires an explicit capital_denominator"
            )
        _require_text(self.unit, "unit")
        _require_text(self.source_id, "source_id")
        _require_text(self.peak_id, "peak_id")
        _require_text(self.current_id, "current_id")
        _require_text(self.source_digest, "source_digest")
        object.__setattr__(
            self,
            "drawdown_digest",
            _digest(
                {
                    "peak_value": self.peak_value,
                    "current_value": self.current_value,
                    "unit": self.unit,
                    "capital_denominator": self.capital_denominator,
                    "denominator_convention": self.denominator_convention,
                    "source_id": self.source_id,
                    "series_kind": self.series_kind,
                    "peak_id": self.peak_id,
                    "current_id": self.current_id,
                    "source_digest": self.source_digest,
                    "quality": self.quality,
                }
            ),
        )

    @property
    def amount(self) -> Decimal:
        return self.peak_value - self.current_value

    @property
    def ratio(self) -> Decimal | None:
        if self.capital_denominator is None:
            return None
        return self.amount / self.capital_denominator


@dataclass(frozen=True, slots=True)
class DrawdownPolicySemantics:
    source_id: str
    series_kind: DrawdownSeriesKind
    denominator_convention: DrawdownDenominatorConvention | None
    semantics_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _require_text(self.source_id, "source_id")
        object.__setattr__(
            self,
            "semantics_digest",
            _digest(
                {
                    "source_id": self.source_id,
                    "series_kind": self.series_kind,
                    "denominator_convention": self.denominator_convention,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class TailRiskEvidence:
    source_kind: TailEvidenceSourceKind
    value_at_risk: Decimal | None
    expected_shortfall: Decimal | None
    unit: str
    tail_fraction: Decimal
    loss_direction: TailLossDirection
    quantile_convention: TailQuantileConvention
    missing_policy: str
    source_policy_digest: str
    total_count: int
    tail_count: int
    sufficient: bool
    source_digest: str
    quality: EvidenceQuality = EvidenceQuality.VALID
    tail_evidence_digest: str = field(init=False)

    def __post_init__(self) -> None:
        for value, name in (
            (self.value_at_risk, "value_at_risk"),
            (self.expected_shortfall, "expected_shortfall"),
        ):
            if value is not None:
                _require_decimal(value, name)
        _require_text(self.unit, "unit")
        _require_decimal(self.tail_fraction, "tail_fraction", positive=True)
        if self.tail_fraction > Decimal("0.5"):
            raise ValueError("tail_fraction must not exceed 0.5")
        _require_text(self.missing_policy, "missing_policy")
        _require_text(self.source_policy_digest, "source_policy_digest")
        if min(self.total_count, self.tail_count) <= 0:
            raise ValueError("tail counts must be positive")
        if self.tail_count > self.total_count:
            raise ValueError("tail_count cannot exceed total_count")
        if self.sufficient and None in (
            self.value_at_risk,
            self.expected_shortfall,
        ):
            raise ValueError("sufficient tail evidence requires VaR and ES")
        _require_text(self.source_digest, "source_digest")
        object.__setattr__(
            self,
            "tail_evidence_digest",
            _digest(
                {
                    "source_kind": self.source_kind,
                    "value_at_risk": self.value_at_risk,
                    "expected_shortfall": self.expected_shortfall,
                    "unit": self.unit,
                    "tail_fraction": self.tail_fraction,
                    "loss_direction": self.loss_direction,
                    "quantile_convention": self.quantile_convention,
                    "missing_policy": self.missing_policy,
                    "source_policy_digest": self.source_policy_digest,
                    "total_count": self.total_count,
                    "tail_count": self.tail_count,
                    "sufficient": self.sufficient,
                    "source_digest": self.source_digest,
                    "quality": self.quality,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class TailRiskPolicySemantics:
    tail_fraction: Decimal
    loss_direction: TailLossDirection
    quantile_convention: TailQuantileConvention
    missing_policy: str
    source_policy_digest: str
    semantics_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _require_decimal(self.tail_fraction, "tail_fraction", positive=True)
        if self.tail_fraction > Decimal("0.5"):
            raise ValueError("tail_fraction must not exceed 0.5")
        _require_text(self.missing_policy, "missing_policy")
        _require_text(self.source_policy_digest, "source_policy_digest")
        object.__setattr__(
            self,
            "semantics_digest",
            _digest(
                {
                    "tail_fraction": self.tail_fraction,
                    "loss_direction": self.loss_direction,
                    "quantile_convention": self.quantile_convention,
                    "missing_policy": self.missing_policy,
                    "source_policy_digest": self.source_policy_digest,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class CircuitBreakerState:
    status: CircuitStatus
    policy_digest: str
    reason: str
    changed_at: datetime
    transition_evidence_digest: str
    previous_state_digest: str | None = None
    circuit_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _require_text(self.policy_digest, "policy_digest")
        _require_text(self.reason, "reason")
        _require_aware(self.changed_at, "changed_at")
        _require_text(self.transition_evidence_digest, "transition_evidence_digest")
        if self.previous_state_digest is not None:
            _require_text(self.previous_state_digest, "previous_state_digest")
        object.__setattr__(
            self,
            "circuit_digest",
            _digest(
                {
                    "status": self.status,
                    "policy_digest": self.policy_digest,
                    "reason": self.reason,
                    "changed_at": self.changed_at,
                    "transition_evidence_digest": self.transition_evidence_digest,
                    "previous_state_digest": self.previous_state_digest,
                }
            ),
        )


def initial_circuit_state(
    *,
    policy_digest: str,
    at_time: datetime,
    evidence_digest: str,
) -> CircuitBreakerState:
    return CircuitBreakerState(
        status=CircuitStatus.NORMAL,
        policy_digest=policy_digest,
        reason="INITIAL_NORMAL",
        changed_at=at_time,
        transition_evidence_digest=evidence_digest,
    )


def latch_circuit(
    state: CircuitBreakerState,
    *,
    reason: str,
    evidence_digest: str,
    at_time: datetime,
) -> CircuitBreakerState:
    if state.status is CircuitStatus.LATCHED:
        raise ValueError("circuit is already latched")
    _require_text(reason, "reason")
    _require_text(evidence_digest, "evidence_digest")
    _require_aware(at_time, "at_time")
    if at_time < state.changed_at:
        raise ValueError("circuit transition cannot move backward in time")
    return CircuitBreakerState(
        status=CircuitStatus.LATCHED,
        policy_digest=state.policy_digest,
        reason=reason,
        changed_at=at_time,
        transition_evidence_digest=evidence_digest,
        previous_state_digest=state.circuit_digest,
    )


def unlatch_circuit(
    state: CircuitBreakerState,
    *,
    human_confirmation_digest: str,
    recovery_digest: str,
    at_time: datetime,
) -> CircuitBreakerState:
    if state.status is not CircuitStatus.LATCHED:
        raise ValueError("only a latched circuit can be unlatched")
    _require_text(human_confirmation_digest, "human_confirmation_digest")
    _require_text(recovery_digest, "recovery_digest")
    _require_aware(at_time, "at_time")
    if at_time < state.changed_at:
        raise ValueError("circuit transition cannot move backward in time")
    evidence = _digest(
        {
            "human_confirmation_digest": human_confirmation_digest,
            "recovery_digest": recovery_digest,
        }
    )
    return CircuitBreakerState(
        status=CircuitStatus.NORMAL,
        policy_digest=state.policy_digest,
        reason="HUMAN_CONFIRMED_UNLATCH",
        changed_at=at_time,
        transition_evidence_digest=evidence,
        previous_state_digest=state.circuit_digest,
    )


@dataclass(frozen=True, slots=True)
class RiskStateSnapshot:
    snapshot_id: str
    portfolio_id: str
    instrument_id: TradableInstrumentId
    as_of_time: datetime
    knowledge_time: datetime
    exposure: ExposureState
    daily_loss: DailyLossState | None
    drawdown: DrawdownState | None
    tail_risk: TailRiskEvidence | None
    safety_posture: SafetyPosture
    commitment_readiness: CommitmentReadiness
    circuit: CircuitBreakerState
    quality: EvidenceQuality
    source_lineage_digest: str
    state_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _require_text(self.snapshot_id, "snapshot_id")
        _require_text(self.portfolio_id, "portfolio_id")
        if not isinstance(self.instrument_id, TradableInstrumentId):
            raise ValueError("instrument_id must be TradableInstrumentId")
        _require_aware(self.as_of_time, "as_of_time")
        _require_aware(self.knowledge_time, "knowledge_time")
        if self.knowledge_time > self.as_of_time:
            raise ValueError("knowledge_time cannot be later than as_of_time")
        if self.daily_loss is not None and not (
            self.daily_loss.session_start <= self.as_of_time < self.daily_loss.session_end
        ):
            raise ValueError("as_of_time must fall inside the daily-loss session")
        if self.circuit.changed_at > self.as_of_time:
            raise ValueError("circuit state cannot be known after snapshot as_of_time")
        _require_text(self.source_lineage_digest, "source_lineage_digest")
        object.__setattr__(
            self,
            "state_digest",
            _digest(
                {
                    "snapshot_id": self.snapshot_id,
                    "portfolio_id": self.portfolio_id,
                    "instrument_id": self.instrument_id,
                    "as_of_time": self.as_of_time,
                    "knowledge_time": self.knowledge_time,
                    "exposure_digest": self.exposure.exposure_digest,
                    "daily_loss_digest": (
                        self.daily_loss.daily_loss_digest if self.daily_loss else None
                    ),
                    "drawdown_digest": self.drawdown.drawdown_digest if self.drawdown else None,
                    "tail_evidence_digest": (
                        self.tail_risk.tail_evidence_digest if self.tail_risk else None
                    ),
                    "safety_posture": self.safety_posture,
                    "commitment_readiness": self.commitment_readiness,
                    "circuit_digest": self.circuit.circuit_digest,
                    "quality": self.quality,
                    "source_lineage_digest": self.source_lineage_digest,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class RiskLimitRule:
    rule_id: str
    metric: RiskMetric
    operator: LimitOperator
    threshold: Decimal
    unit: str
    hard: bool

    def __post_init__(self) -> None:
        _require_text(self.rule_id, "rule_id")
        _require_decimal(self.threshold, "threshold")
        _require_text(self.unit, "unit")
        if self.metric in {
            RiskMetric.PROJECTED_WORST_CASE_EXPOSURE,
            RiskMetric.PROJECTED_CAPACITY_USAGE,
        }:
            _require_decimal(self.threshold, "threshold", positive=True)


@dataclass(frozen=True, slots=True)
class RiskPolicyBundle:
    policy_id: str
    version: str
    portfolio_id: str
    instrument_id: TradableInstrumentId | None
    effective_from: datetime
    effective_until: datetime | None
    rules: tuple[RiskLimitRule, ...]
    allowed_safety_postures: tuple[SafetyPosture, ...]
    authorization_ttl_seconds: int
    daily_loss_semantics: DailyLossPolicySemantics | None = None
    drawdown_semantics: DrawdownPolicySemantics | None = None
    tail_semantics: TailRiskPolicySemantics | None = None
    numeric_policy: NumericPolicy = DEFAULT_NUMERIC_POLICY
    predeclared: bool = True
    policy_digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))
        object.__setattr__(
            self,
            "allowed_safety_postures",
            tuple(self.allowed_safety_postures),
        )
        for value, name in (
            (self.policy_id, "policy_id"),
            (self.version, "version"),
            (self.portfolio_id, "portfolio_id"),
        ):
            _require_text(value, name)
        if self.instrument_id is not None and not isinstance(
            self.instrument_id, TradableInstrumentId
        ):
            raise ValueError("instrument_id must be TradableInstrumentId or None")
        _require_aware(self.effective_from, "effective_from")
        if self.effective_until is not None:
            _require_aware(self.effective_until, "effective_until")
            if self.effective_until <= self.effective_from:
                raise ValueError("policy effective interval must have positive duration")
        if not self.predeclared:
            raise ValueError("RiskPolicyBundle must be predeclared")
        if not self.rules:
            raise ValueError("RiskPolicyBundle requires at least one rule")
        rule_ids = tuple(rule.rule_id for rule in self.rules)
        if rule_ids != tuple(sorted(rule_ids)):
            raise ValueError("risk rules must be canonically ordered by rule_id")
        if len(set(rule_ids)) != len(rule_ids):
            raise ValueError("risk rule IDs must be unique")
        if not any(
            rule.hard
            and rule.operator is LimitOperator.LTE
            and rule.metric
            in {
                RiskMetric.PROJECTED_WORST_CASE_EXPOSURE,
                RiskMetric.PROJECTED_CAPACITY_USAGE,
            }
            for rule in self.rules
        ):
            raise ValueError("policy requires a hard projected exposure/capacity upper bound")
        if not self.allowed_safety_postures:
            raise ValueError("allowed_safety_postures cannot be empty")
        posture_values = tuple(posture.value for posture in self.allowed_safety_postures)
        if posture_values != tuple(sorted(posture_values)):
            raise ValueError("allowed_safety_postures must be canonically ordered")
        if len(set(posture_values)) != len(posture_values):
            raise ValueError("allowed_safety_postures must be unique")
        if self.authorization_ttl_seconds <= 0:
            raise ValueError("authorization_ttl_seconds must be positive")
        metrics = {rule.metric for rule in self.rules}
        if (
            RiskMetric.DAILY_LOSS in metrics
            and self.daily_loss_semantics is None
        ):
            raise ValueError(
                "DAILY_LOSS rule requires DailyLossPolicySemantics"
            )
        drawdown_metrics = {
            RiskMetric.DRAWDOWN_AMOUNT,
            RiskMetric.DRAWDOWN_RATIO,
        }
        if metrics.intersection(drawdown_metrics):
            if self.drawdown_semantics is None:
                raise ValueError(
                    "drawdown rule requires DrawdownPolicySemantics"
                )
            if (
                RiskMetric.DRAWDOWN_RATIO in metrics
                and self.drawdown_semantics.denominator_convention is None
            ):
                raise ValueError(
                    "DRAWDOWN_RATIO requires an explicit denominator convention"
                )
        tail_metrics = {
            RiskMetric.VALUE_AT_RISK,
            RiskMetric.EXPECTED_SHORTFALL,
        }
        if metrics.intersection(tail_metrics) and self.tail_semantics is None:
            raise ValueError(
                "VaR/ES rule requires TailRiskPolicySemantics"
            )
        object.__setattr__(
            self,
            "policy_digest",
            _digest(
                {
                    "policy_id": self.policy_id,
                    "version": self.version,
                    "portfolio_id": self.portfolio_id,
                    "instrument_id": self.instrument_id,
                    "effective_from": self.effective_from,
                    "effective_until": self.effective_until,
                    "rules": tuple(
                        (
                            rule.rule_id,
                            rule.metric,
                            rule.operator,
                            rule.threshold,
                            rule.unit,
                            rule.hard,
                        )
                        for rule in self.rules
                    ),
                    "allowed_safety_postures": self.allowed_safety_postures,
                    "authorization_ttl_seconds": self.authorization_ttl_seconds,
                    "daily_loss_semantics_digest": (
                        self.daily_loss_semantics.semantics_digest
                        if self.daily_loss_semantics is not None
                        else None
                    ),
                    "drawdown_semantics_digest": (
                        self.drawdown_semantics.semantics_digest
                        if self.drawdown_semantics is not None
                        else None
                    ),
                    "tail_semantics_digest": (
                        self.tail_semantics.semantics_digest
                        if self.tail_semantics is not None
                        else None
                    ),
                    "numeric_policy": self.numeric_policy.to_canonical_dict(),
                    "predeclared": self.predeclared,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class RiskEvaluationBoundary:
    proposal: RiskProposal
    state: RiskStateSnapshot
    policy: RiskPolicyBundle
    as_of_time: datetime
    engine_revision: str
    boundary_digest: str
    _verification_token: object = field(default=None, init=False, repr=False, compare=False)

    @property
    def is_verified(self) -> bool:
        return self._verification_token is _VERIFIED_BOUNDARY_TOKEN

    @classmethod
    def build(
        cls,
        *,
        proposal: RiskProposal,
        state: RiskStateSnapshot,
        policy: RiskPolicyBundle,
        as_of_time: datetime,
        engine_revision: str,
    ) -> RiskEvaluationBoundary:
        _require_aware(as_of_time, "as_of_time")
        _require_text(engine_revision, "engine_revision")
        if proposal.instrument_id != state.instrument_id:
            raise ValueError("proposal and risk state instrument identities differ")
        if proposal.portfolio_id != state.portfolio_id:
            raise ValueError("proposal and risk state portfolio identities differ")
        if proposal.created_at > as_of_time:
            raise ValueError("proposal cannot be created after evaluation as_of_time")
        if state.as_of_time > as_of_time or state.knowledge_time > as_of_time:
            raise ValueError("risk state cannot be from the future")
        payload: dict[str, object] = {
            "proposal_digest": proposal.proposal_digest,
            "state_digest": state.state_digest,
            "policy_digest": policy.policy_digest,
            "as_of_time": as_of_time,
            "engine_revision": engine_revision,
        }
        obj = cls(
            proposal=proposal,
            state=state,
            policy=policy,
            as_of_time=as_of_time,
            engine_revision=engine_revision,
            boundary_digest=_digest(payload),
        )
        object.__setattr__(obj, "_verification_token", _VERIFIED_BOUNDARY_TOKEN)
        return obj


@dataclass(frozen=True, slots=True)
class RiskDecisionRecord:
    decision: RiskDecision
    boundary_digest: str
    proposal_digest: str
    state_digest: str
    policy_digest: str
    reasons: tuple[str, ...]
    metrics: Mapping[str, Decimal]
    decided_at: datetime
    decision_digest: str = field(init=False)

    def __post_init__(self) -> None:
        for value, name in (
            (self.boundary_digest, "boundary_digest"),
            (self.proposal_digest, "proposal_digest"),
            (self.state_digest, "state_digest"),
            (self.policy_digest, "policy_digest"),
        ):
            _require_text(value, name)
        if not self.reasons:
            raise ValueError("RiskDecisionRecord requires at least one reason")
        if len(set(self.reasons)) != len(self.reasons):
            raise ValueError("decision reasons must be unique")
        _require_aware(self.decided_at, "decided_at")
        frozen = _freeze_metrics(self.metrics)
        object.__setattr__(self, "metrics", frozen)
        object.__setattr__(
            self,
            "decision_digest",
            _digest(
                {
                    "decision": self.decision,
                    "boundary_digest": self.boundary_digest,
                    "proposal_digest": self.proposal_digest,
                    "state_digest": self.state_digest,
                    "policy_digest": self.policy_digest,
                    "reasons": self.reasons,
                    "metrics": frozen,
                    "decided_at": self.decided_at,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class RiskAuthorization:
    decision_digest: str
    proposal_digest: str
    state_digest: str
    policy_digest: str
    max_quantity: Decimal
    quantity_unit: str
    max_exposure: Decimal
    exposure_unit: str
    valid_from: datetime
    valid_until: datetime
    engine_revision: str
    authorization_digest: str = field(init=False)
    _issuer_token: object = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        for value, name in (
            (self.decision_digest, "decision_digest"),
            (self.proposal_digest, "proposal_digest"),
            (self.state_digest, "state_digest"),
            (self.policy_digest, "policy_digest"),
            (self.engine_revision, "engine_revision"),
        ):
            _require_text(value, name)
        _require_decimal(self.max_quantity, "max_quantity", positive=True)
        _require_text(self.quantity_unit, "quantity_unit")
        _require_decimal(self.max_exposure, "max_exposure", positive=True)
        _require_text(self.exposure_unit, "exposure_unit")
        _require_aware(self.valid_from, "valid_from")
        _require_aware(self.valid_until, "valid_until")
        if self.valid_until <= self.valid_from:
            raise ValueError("authorization validity interval must have positive duration")
        object.__setattr__(
            self,
            "authorization_digest",
            _digest(
                {
                    "decision_digest": self.decision_digest,
                    "proposal_digest": self.proposal_digest,
                    "state_digest": self.state_digest,
                    "policy_digest": self.policy_digest,
                    "max_quantity": self.max_quantity,
                    "quantity_unit": self.quantity_unit,
                    "max_exposure": self.max_exposure,
                    "exposure_unit": self.exposure_unit,
                    "valid_from": self.valid_from,
                    "valid_until": self.valid_until,
                    "engine_revision": self.engine_revision,
                }
            ),
        )

    @property
    def is_engine_issued(self) -> bool:
        return self._issuer_token is _ENGINE_AUTHORIZATION_TOKEN


@dataclass(frozen=True, slots=True)
class RiskEvaluationResult:
    decision: RiskDecisionRecord
    authorization: RiskAuthorization | None
    result_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if self.decision.decision is RiskDecision.REJECT and self.authorization is not None:
            raise ValueError("REJECT cannot carry RiskAuthorization")
        if self.decision.decision is RiskDecision.PERMIT and self.authorization is None:
            raise ValueError("PERMIT requires RiskAuthorization")
        object.__setattr__(
            self,
            "result_digest",
            _digest(
                {
                    "decision_digest": self.decision.decision_digest,
                    "authorization_digest": (
                        self.authorization.authorization_digest
                        if self.authorization is not None
                        else None
                    ),
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class AuthorizationValidation:
    valid: bool
    reasons: tuple[AuthorizationInvalidity, ...]


def _policy_effective(policy: RiskPolicyBundle, as_of_time: datetime) -> bool:
    return policy.effective_from <= as_of_time and (
        policy.effective_until is None or as_of_time < policy.effective_until
    )


def _rule_passes(rule: RiskLimitRule, value: Decimal) -> bool:
    if rule.operator is LimitOperator.LTE:
        return value <= rule.threshold
    return value >= rule.threshold


def _metric_value(
    boundary: RiskEvaluationBoundary,
    metric: RiskMetric,
) -> tuple[Decimal | None, str | None, str | None]:
    proposal = boundary.proposal
    state = boundary.state
    exposure = state.exposure

    if metric is RiskMetric.REQUESTED_EXPOSURE:
        return proposal.requested_exposure, proposal.exposure_unit, None

    if exposure.quality is not EvidenceQuality.VALID:
        if metric in {
            RiskMetric.CURRENT_POSITION_EXPOSURE,
            RiskMetric.COMMITTED_POTENTIAL_EXPOSURE,
            RiskMetric.RISK_CAPACITY_RESERVATION,
            RiskMetric.WORST_CASE_EXPOSURE,
            RiskMetric.PROJECTED_WORST_CASE_EXPOSURE,
            RiskMetric.PROJECTED_CAPACITY_USAGE,
        }:
            return None, exposure.unit, "EXPOSURE_QUALITY"

    if metric is RiskMetric.CURRENT_POSITION_EXPOSURE:
        return exposure.current_position_exposure, exposure.unit, None
    if metric is RiskMetric.COMMITTED_POTENTIAL_EXPOSURE:
        return exposure.committed_potential_exposure, exposure.unit, None
    if metric is RiskMetric.RISK_CAPACITY_RESERVATION:
        return exposure.risk_capacity_reservation, exposure.unit, None
    if metric is RiskMetric.WORST_CASE_EXPOSURE:
        return exposure.worst_case_exposure, exposure.unit, None
    if metric is RiskMetric.PROJECTED_WORST_CASE_EXPOSURE:
        if proposal.exposure_unit != exposure.unit:
            return None, exposure.unit, "EXPOSURE_UNIT_MISMATCH"
        return exposure.worst_case_exposure + proposal.requested_exposure, exposure.unit, None
    if metric is RiskMetric.PROJECTED_CAPACITY_USAGE:
        if proposal.exposure_unit != exposure.unit:
            return None, exposure.unit, "EXPOSURE_UNIT_MISMATCH"
        return (
            exposure.worst_case_exposure
            + exposure.risk_capacity_reservation
            + proposal.requested_exposure,
            exposure.unit,
            None,
        )

    if metric is RiskMetric.DAILY_LOSS:
        if state.daily_loss is None:
            return None, None, "DAILY_LOSS_MISSING"
        if state.daily_loss.quality is not EvidenceQuality.VALID:
            return None, state.daily_loss.currency, "DAILY_LOSS_QUALITY"
        daily_semantics_policy = boundary.policy.daily_loss_semantics
        if daily_semantics_policy is None:
            return None, state.daily_loss.currency, "DAILY_LOSS_POLICY_MISSING"
        actual_daily_semantics = (
            state.daily_loss.currency,
            state.daily_loss.pnl_source_id,
            state.daily_loss.include_unrealized,
            state.daily_loss.loss_sign_convention,
            state.daily_loss.session_calendar_id,
            state.daily_loss.timezone_name,
            state.daily_loss.reset_semantics,
        )
        expected_daily_semantics = (
            daily_semantics_policy.currency,
            daily_semantics_policy.pnl_source_id,
            daily_semantics_policy.include_unrealized,
            daily_semantics_policy.loss_sign_convention,
            daily_semantics_policy.session_calendar_id,
            daily_semantics_policy.timezone_name,
            daily_semantics_policy.reset_semantics,
        )
        if actual_daily_semantics != expected_daily_semantics:
            return None, state.daily_loss.currency, "DAILY_LOSS_POLICY_MISMATCH"
        return state.daily_loss.loss_amount, state.daily_loss.currency, None

    if metric in {RiskMetric.DRAWDOWN_AMOUNT, RiskMetric.DRAWDOWN_RATIO}:
        if state.drawdown is None:
            return None, None, "DRAWDOWN_MISSING"
        if state.drawdown.quality is not EvidenceQuality.VALID:
            return None, state.drawdown.unit, "DRAWDOWN_QUALITY"
        drawdown_semantics_policy = boundary.policy.drawdown_semantics
        if drawdown_semantics_policy is None:
            return None, state.drawdown.unit, "DRAWDOWN_POLICY_MISSING"
        if (
            state.drawdown.source_id,
            state.drawdown.series_kind,
        ) != (
            drawdown_semantics_policy.source_id,
            drawdown_semantics_policy.series_kind,
        ):
            return None, state.drawdown.unit, "DRAWDOWN_POLICY_MISMATCH"
        if metric is RiskMetric.DRAWDOWN_AMOUNT:
            if (
                state.drawdown.denominator_convention
                is not drawdown_semantics_policy.denominator_convention
            ):
                return None, state.drawdown.unit, "DRAWDOWN_POLICY_MISMATCH"
            return state.drawdown.amount, state.drawdown.unit, None
        if state.drawdown.capital_denominator is None:
            return None, "ratio", "DRAWDOWN_DENOMINATOR_MISSING"
        if (
            state.drawdown.denominator_convention
            is not drawdown_semantics_policy.denominator_convention
        ):
            return None, "ratio", "DRAWDOWN_POLICY_MISMATCH"
        with localcontext(boundary.policy.numeric_policy.get_context()):
            ratio = state.drawdown.amount / state.drawdown.capital_denominator
        return ratio, "ratio", None

    if metric in {RiskMetric.VALUE_AT_RISK, RiskMetric.EXPECTED_SHORTFALL}:
        if state.tail_risk is None:
            return None, None, "TAIL_EVIDENCE_MISSING"
        tail = state.tail_risk
        if tail.quality is not EvidenceQuality.VALID:
            return None, tail.unit, "TAIL_EVIDENCE_QUALITY"
        tail_semantics_policy = boundary.policy.tail_semantics
        if tail_semantics_policy is None:
            return None, tail.unit, "TAIL_POLICY_MISSING"
        actual_tail_semantics = (
            tail.tail_fraction,
            tail.loss_direction,
            tail.quantile_convention,
            tail.missing_policy,
            tail.source_policy_digest,
        )
        expected_tail_semantics = (
            tail_semantics_policy.tail_fraction,
            tail_semantics_policy.loss_direction,
            tail_semantics_policy.quantile_convention,
            tail_semantics_policy.missing_policy,
            tail_semantics_policy.source_policy_digest,
        )
        if actual_tail_semantics != expected_tail_semantics:
            return None, tail.unit, "TAIL_POLICY_MISMATCH"
        if tail.source_kind is not TailEvidenceSourceKind.EMPIRICAL_OBSERVED:
            return None, tail.unit, "SYNTHETIC_TAIL_EVIDENCE_FORBIDDEN"
        if not tail.sufficient:
            return None, tail.unit, "TAIL_EVIDENCE_INSUFFICIENT"
        value = (
            tail.value_at_risk
            if metric is RiskMetric.VALUE_AT_RISK
            else tail.expected_shortfall
        )
        assert value is not None
        return value, tail.unit, None

    raise AssertionError(f"unsupported risk metric: {metric}")


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _projected_base(boundary: RiskEvaluationBoundary, metric: RiskMetric) -> Decimal:
    exposure = boundary.state.exposure
    if metric is RiskMetric.PROJECTED_WORST_CASE_EXPOSURE:
        return exposure.worst_case_exposure
    if metric is RiskMetric.PROJECTED_CAPACITY_USAGE:
        return exposure.worst_case_exposure + exposure.risk_capacity_reservation
    raise ValueError("metric is not a projected exposure/capacity metric")


def _build_decision(
    *,
    boundary: RiskEvaluationBoundary,
    decision: RiskDecision,
    reasons: Sequence[str],
    metrics: Mapping[str, Decimal],
) -> RiskDecisionRecord:
    return RiskDecisionRecord(
        decision=decision,
        boundary_digest=boundary.boundary_digest,
        proposal_digest=boundary.proposal.proposal_digest,
        state_digest=boundary.state.state_digest,
        policy_digest=boundary.policy.policy_digest,
        reasons=tuple(reasons),
        metrics=metrics,
        decided_at=boundary.as_of_time,
    )


def _build_authorization(
    *,
    boundary: RiskEvaluationBoundary,
    decision: RiskDecisionRecord,
    max_exposure: Decimal,
) -> RiskAuthorization:
    proposal = boundary.proposal
    with localcontext(boundary.policy.numeric_policy.get_context()):
        ratio = max_exposure / proposal.requested_exposure
        computed_max_quantity = proposal.requested_quantity * ratio
        max_quantity = min(computed_max_quantity, proposal.requested_quantity)
    ttl_valid_until = boundary.as_of_time + timedelta(
        seconds=boundary.policy.authorization_ttl_seconds
    )
    valid_until = ttl_valid_until
    if boundary.policy.effective_until is not None:
        valid_until = min(valid_until, boundary.policy.effective_until)
    authorization = RiskAuthorization(
        decision_digest=decision.decision_digest,
        proposal_digest=proposal.proposal_digest,
        state_digest=boundary.state.state_digest,
        policy_digest=boundary.policy.policy_digest,
        max_quantity=max_quantity,
        quantity_unit=proposal.quantity_unit,
        max_exposure=max_exposure,
        exposure_unit=proposal.exposure_unit,
        valid_from=boundary.as_of_time,
        valid_until=valid_until,
        engine_revision=boundary.engine_revision,
    )
    object.__setattr__(authorization, "_issuer_token", _ENGINE_AUTHORIZATION_TOKEN)
    return authorization


def evaluate_risk(boundary: RiskEvaluationBoundary) -> RiskEvaluationResult:
    if not boundary.is_verified:
        raise ValueError("RiskEvaluationBoundary must be created by build()")

    proposal = boundary.proposal
    state = boundary.state
    policy = boundary.policy
    reject_reasons: list[str] = []
    informational_reasons: list[str] = []
    metrics: dict[str, Decimal] = {}

    if not _policy_effective(policy, boundary.as_of_time):
        _append_unique(reject_reasons, "POLICY_NOT_EFFECTIVE")
    if policy.portfolio_id != proposal.portfolio_id:
        _append_unique(reject_reasons, "POLICY_PORTFOLIO_SCOPE_MISMATCH")
    if policy.instrument_id is not None and policy.instrument_id != proposal.instrument_id:
        _append_unique(reject_reasons, "POLICY_INSTRUMENT_SCOPE_MISMATCH")
    if state.quality is not EvidenceQuality.VALID:
        _append_unique(reject_reasons, f"STATE_QUALITY_{state.quality.value}")
    if state.exposure.quality is not EvidenceQuality.VALID:
        _append_unique(reject_reasons, f"EXPOSURE_QUALITY_{state.exposure.quality.value}")
    if state.commitment_readiness is not CommitmentReadiness.READY:
        _append_unique(
            reject_reasons,
            f"COMMITMENT_READINESS_{state.commitment_readiness.value}",
        )
    if state.safety_posture not in policy.allowed_safety_postures:
        _append_unique(
            reject_reasons,
            f"SAFETY_POSTURE_{state.safety_posture.value}",
        )
    if state.circuit.policy_digest != policy.policy_digest:
        _append_unique(reject_reasons, "CIRCUIT_POLICY_MISMATCH")
    if state.circuit.status is CircuitStatus.LATCHED:
        _append_unique(reject_reasons, "CIRCUIT_LATCHED")

    exposure_cap = proposal.requested_exposure
    for rule in policy.rules:
        value, unit, missing_reason = _metric_value(boundary, rule.metric)
        if missing_reason is not None or value is None or unit is None:
            reason = f"{missing_reason or 'METRIC_MISSING'}:{rule.rule_id}"
            if rule.hard:
                _append_unique(reject_reasons, reason)
            else:
                _append_unique(informational_reasons, f"ADVISORY_{reason}")
            continue

        metrics[rule.metric.value] = value
        if unit != rule.unit:
            reason = f"UNIT_MISMATCH:{rule.rule_id}"
            if rule.hard:
                _append_unique(reject_reasons, reason)
            else:
                _append_unique(informational_reasons, f"ADVISORY_{reason}")
            continue

        projected_cap_rule = (
            rule.hard
            and rule.operator is LimitOperator.LTE
            and rule.metric
            in {
                RiskMetric.PROJECTED_WORST_CASE_EXPOSURE,
                RiskMetric.PROJECTED_CAPACITY_USAGE,
            }
        )
        if projected_cap_rule:
            base = _projected_base(boundary, rule.metric)
            remaining = rule.threshold - base
            if remaining <= Decimal(0):
                _append_unique(reject_reasons, f"HARD_LIMIT_BREACH:{rule.rule_id}")
            elif proposal.requested_exposure > remaining:
                exposure_cap = min(exposure_cap, remaining)
                _append_unique(informational_reasons, f"AUTHORIZATION_CAPPED:{rule.rule_id}")
            continue

        if not _rule_passes(rule, value):
            reason = (
                f"HARD_LIMIT_BREACH:{rule.rule_id}"
                if rule.hard
                else f"ADVISORY_LIMIT_BREACH:{rule.rule_id}"
            )
            if rule.hard:
                _append_unique(reject_reasons, reason)
            else:
                _append_unique(informational_reasons, reason)

    if reject_reasons:
        decision = _build_decision(
            boundary=boundary,
            decision=RiskDecision.REJECT,
            reasons=tuple(reject_reasons + informational_reasons),
            metrics=metrics,
        )
        return RiskEvaluationResult(decision=decision, authorization=None)

    reasons = ["PERMITTED", *informational_reasons]
    decision = _build_decision(
        boundary=boundary,
        decision=RiskDecision.PERMIT,
        reasons=reasons,
        metrics=metrics,
    )
    authorization = _build_authorization(
        boundary=boundary,
        decision=decision,
        max_exposure=exposure_cap,
    )
    return RiskEvaluationResult(decision=decision, authorization=authorization)


def validate_authorization(
    authorization: RiskAuthorization,
    *,
    decision: RiskDecisionRecord,
    proposal: RiskProposal,
    state: RiskStateSnapshot,
    policy: RiskPolicyBundle,
    as_of_time: datetime,
) -> AuthorizationValidation:
    _require_aware(as_of_time, "as_of_time")
    reasons: list[AuthorizationInvalidity] = []
    if not authorization.is_engine_issued:
        reasons.append(AuthorizationInvalidity.NOT_ENGINE_ISSUED)
    if decision.decision is not RiskDecision.PERMIT:
        reasons.append(AuthorizationInvalidity.DECISION_NOT_PERMIT)
    if authorization.decision_digest != decision.decision_digest:
        reasons.append(AuthorizationInvalidity.DECISION_MISMATCH)
    if authorization.proposal_digest != proposal.proposal_digest:
        reasons.append(AuthorizationInvalidity.PROPOSAL_MISMATCH)
    if authorization.state_digest != state.state_digest:
        reasons.append(AuthorizationInvalidity.STATE_MISMATCH)
    if authorization.policy_digest != policy.policy_digest:
        reasons.append(AuthorizationInvalidity.POLICY_MISMATCH)
    if as_of_time < authorization.valid_from:
        reasons.append(AuthorizationInvalidity.NOT_YET_VALID)
    if as_of_time >= authorization.valid_until:
        reasons.append(AuthorizationInvalidity.EXPIRED)
    if (
        authorization.max_quantity > proposal.requested_quantity
        or authorization.quantity_unit != proposal.quantity_unit
        or authorization.max_exposure > proposal.requested_exposure
        or authorization.exposure_unit != proposal.exposure_unit
    ):
        reasons.append(AuthorizationInvalidity.ENVELOPE_EXCEEDS_PROPOSAL)
    if not _policy_effective(policy, as_of_time):
        reasons.append(AuthorizationInvalidity.POLICY_NOT_EFFECTIVE)
    return AuthorizationValidation(valid=not reasons, reasons=tuple(reasons))


def verify_deterministic_equivalence(
    first: RiskEvaluationResult,
    second: RiskEvaluationResult,
) -> str:
    if first != second or first.result_digest != second.result_digest:
        raise ValueError("risk evaluations are not deterministically equivalent")
    return first.result_digest
