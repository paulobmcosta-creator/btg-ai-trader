"""Deterministic, side-effect-free operational Strategy domain."""

from __future__ import annotations

import hashlib
import json
import types
import weakref
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum

from btg_ai_trader.observer.identity import TradableInstrumentId

_MAX_TIMEDELTA_SECONDS = timedelta.max.days * 86_400 + timedelta.max.seconds

_IssuanceRegister = Callable[[object, str], None]
_IssuanceVerify = Callable[[object, str], bool]


def _make_issuance_registry() -> tuple[_IssuanceRegister, _IssuanceVerify]:
    records: dict[int, tuple[weakref.ReferenceType[object], str]] = {}

    def register(value: object, digest: str) -> None:
        key = id(value)

        def cleanup(reference: weakref.ReferenceType[object]) -> None:
            current = records.get(key)
            if current is not None and current[0] is reference:
                records.pop(key, None)

        reference = weakref.ref(value, cleanup)
        records[key] = (reference, digest)

    def verify(value: object, digest: str) -> bool:
        current = records.get(id(value))
        return (
            current is not None
            and current[0]() is value
            and current[1] == digest
        )

    return register, verify


_register_decision_issuance, _verify_decision_issuance = _make_issuance_registry()
_register_intent_issuance, _verify_intent_issuance = _make_issuance_registry()


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field_name} must be nonempty text without surrounding whitespace")


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _utc_instant(value: datetime) -> datetime:
    return value.astimezone(UTC)


def _require_decimal(
    value: Decimal,
    field_name: str,
    *,
    positive: bool = False,
) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
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
            str(key): _jsonable(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
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


def _freeze_signals(signals: Mapping[str, Decimal]) -> Mapping[str, Decimal]:
    frozen: dict[str, Decimal] = {}
    for name, value in sorted(signals.items()):
        _require_text(name, "signal_name")
        _require_decimal(value, f"signal[{name}]")
        frozen[name] = value
    return types.MappingProxyType(frozen)


class StrategyDisposition(str, Enum):
    NO_TRADE = "NO_TRADE"
    PROPOSE_TRADE = "PROPOSE_TRADE"


class StrategyEvidenceQuality(str, Enum):
    VALID = "VALID"
    UNKNOWN = "UNKNOWN"
    STALE = "STALE"
    INCOMPLETE = "INCOMPLETE"


class ComparisonOperator(str, Enum):
    LT = "LT"
    LE = "LE"
    GE = "GE"
    GT = "GT"


class EconomicDirection(str, Enum):
    INCREASE_LONG = "INCREASE_LONG"
    INCREASE_SHORT = "INCREASE_SHORT"
    DECREASE_LONG = "DECREASE_LONG"
    DECREASE_SHORT = "DECREASE_SHORT"


class DecisionReason(str, Enum):
    RULE_MATCHED = "RULE_MATCHED"
    NO_RULE_MATCHED = "NO_RULE_MATCHED"
    EVIDENCE_NOT_VALID = "EVIDENCE_NOT_VALID"
    EVIDENCE_TOO_OLD = "EVIDENCE_TOO_OLD"
    CANDIDATE_INSTRUMENT_MISMATCH = "CANDIDATE_INSTRUMENT_MISMATCH"
    CANDIDATE_PORTFOLIO_MISMATCH = "CANDIDATE_PORTFOLIO_MISMATCH"
    INPUT_SPEC_MISMATCH = "INPUT_SPEC_MISMATCH"
    MISSING_REQUIRED_SIGNAL = "MISSING_REQUIRED_SIGNAL"


@dataclass(frozen=True, slots=True)
class EconomicObjective:
    direction: EconomicDirection
    requested_quantity: Decimal
    quantity_unit: str
    requested_exposure: Decimal
    exposure_unit: str
    def __post_init__(self) -> None:
        if not isinstance(self.direction, EconomicDirection):
            raise ValueError("direction must be EconomicDirection")
        _require_decimal(self.requested_quantity, "requested_quantity", positive=True)
        _require_text(self.quantity_unit, "quantity_unit")
        _require_decimal(self.requested_exposure, "requested_exposure", positive=True)
        _require_text(self.exposure_unit, "exposure_unit")
    @property
    def objective_digest(self) -> str:
        return _digest(
            {
                "direction": self.direction,
                "requested_quantity": self.requested_quantity,
                "quantity_unit": self.quantity_unit,
                "requested_exposure": self.requested_exposure,
                "exposure_unit": self.exposure_unit,
            }
        )


@dataclass(frozen=True, slots=True)
class StrategyRule:
    rule_id: str
    priority: int
    signal_name: str
    operator: ComparisonOperator
    threshold: Decimal
    objective: EconomicObjective
    def __post_init__(self) -> None:
        _require_text(self.rule_id, "rule_id")
        if (
            isinstance(self.priority, bool)
            or not isinstance(self.priority, int)
            or self.priority < 0
        ):
            raise ValueError("priority must be a non-negative integer")
        _require_text(self.signal_name, "signal_name")
        if not isinstance(self.operator, ComparisonOperator):
            raise ValueError("operator must be ComparisonOperator")
        _require_decimal(self.threshold, "threshold")
        if not isinstance(self.objective, EconomicObjective):
            raise ValueError("objective must be EconomicObjective")
    @property
    def rule_digest(self) -> str:
        return _digest(
            {
                "rule_id": self.rule_id,
                "priority": self.priority,
                "signal_name": self.signal_name,
                "operator": self.operator,
                "threshold": self.threshold,
                "objective_digest": self.objective.objective_digest,
            }
        )


@dataclass(frozen=True, slots=True)
class CandidateStrategy:
    name: str
    version: str
    code_revision: str
    instrument_id: TradableInstrumentId
    portfolio_id: str
    input_spec_digest: str
    max_evidence_age_seconds: int
    rules: tuple[StrategyRule, ...]

    def __post_init__(self) -> None:
        _require_text(self.name, "name")
        _require_text(self.version, "version")
        _require_text(self.code_revision, "code_revision")
        if not isinstance(self.instrument_id, TradableInstrumentId):
            raise ValueError("instrument_id must be TradableInstrumentId")
        _require_text(self.portfolio_id, "portfolio_id")
        _require_text(self.input_spec_digest, "input_spec_digest")
        if (
            isinstance(self.max_evidence_age_seconds, bool)
            or not isinstance(self.max_evidence_age_seconds, int)
            or self.max_evidence_age_seconds < 0
        ):
            raise ValueError("max_evidence_age_seconds must be a non-negative integer")
        if self.max_evidence_age_seconds > _MAX_TIMEDELTA_SECONDS:
            raise ValueError("max_evidence_age_seconds exceeds timedelta range")
        if not self.rules:
            raise ValueError("rules must contain at least one StrategyRule")
        if not all(isinstance(rule, StrategyRule) for rule in self.rules):
            raise ValueError("rules must contain only StrategyRule values")
        rule_ids = [rule.rule_id for rule in self.rules]
        priorities = [rule.priority for rule in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("rule_id values must be unique")
        if len(priorities) != len(set(priorities)):
            raise ValueError("rule priorities must be unique")
        canonical_rules = tuple(sorted(self.rules, key=lambda rule: (rule.priority, rule.rule_id)))
        object.__setattr__(self, "rules", canonical_rules)

    @property
    def required_signals(self) -> tuple[str, ...]:
        return tuple(sorted({rule.signal_name for rule in self.rules}))

    @property
    def candidate_digest(self) -> str:
        return _digest(
            {
                "name": self.name,
                "version": self.version,
                "code_revision": self.code_revision,
                "instrument_id": self.instrument_id,
                "portfolio_id": self.portfolio_id,
                "input_spec_digest": self.input_spec_digest,
                "max_evidence_age_seconds": self.max_evidence_age_seconds,
                "rule_digests": [rule.rule_digest for rule in self.rules],
            }
        )

    @property
    def candidate_id(self) -> str:
        return f"strategy:{self.name}:{self.candidate_digest[:12]}"


@dataclass(frozen=True, slots=True)
class DecisionOpportunity:
    opportunity_id: str
    instrument_id: TradableInstrumentId
    portfolio_id: str
    event_time: datetime
    knowledge_time: datetime
    decision_time: datetime
    input_spec_digest: str
    signals: Mapping[str, Decimal]
    evidence_quality: StrategyEvidenceQuality
    source_digest: str

    def __post_init__(self) -> None:
        _require_text(self.opportunity_id, "opportunity_id")
        if not isinstance(self.instrument_id, TradableInstrumentId):
            raise ValueError("instrument_id must be TradableInstrumentId")
        _require_text(self.portfolio_id, "portfolio_id")
        _require_aware(self.event_time, "event_time")
        _require_aware(self.knowledge_time, "knowledge_time")
        _require_aware(self.decision_time, "decision_time")
        event_utc = _utc_instant(self.event_time)
        knowledge_utc = _utc_instant(self.knowledge_time)
        decision_utc = _utc_instant(self.decision_time)
        if event_utc > knowledge_utc:
            raise ValueError("event_time cannot be after knowledge_time")
        if knowledge_utc > decision_utc:
            raise ValueError("knowledge_time cannot be after decision_time")
        _require_text(self.input_spec_digest, "input_spec_digest")
        frozen_signals = _freeze_signals(self.signals)
        object.__setattr__(self, "signals", frozen_signals)
        if not isinstance(self.evidence_quality, StrategyEvidenceQuality):
            raise ValueError("evidence_quality must be StrategyEvidenceQuality")
        _require_text(self.source_digest, "source_digest")

    @property
    def opportunity_digest(self) -> str:
        return _digest(
            {
                "opportunity_id": self.opportunity_id,
                "instrument_id": self.instrument_id,
                "portfolio_id": self.portfolio_id,
                "event_time": self.event_time,
                "knowledge_time": self.knowledge_time,
                "decision_time": self.decision_time,
                "input_spec_digest": self.input_spec_digest,
                "signals": self.signals,
                "evidence_quality": self.evidence_quality,
                "source_digest": self.source_digest,
            }
        )


def _matches(value: Decimal, operator: ComparisonOperator, threshold: Decimal) -> bool:
    if operator is ComparisonOperator.LT:
        return value < threshold
    if operator is ComparisonOperator.LE:
        return value <= threshold
    if operator is ComparisonOperator.GE:
        return value >= threshold
    return value > threshold


def _evaluate_outcome(
    candidate: CandidateStrategy,
    opportunity: DecisionOpportunity,
) -> tuple[StrategyDisposition, tuple[DecisionReason, ...], str | None]:
    if opportunity.instrument_id != candidate.instrument_id:
        return (
            StrategyDisposition.NO_TRADE,
            (DecisionReason.CANDIDATE_INSTRUMENT_MISMATCH,),
            None,
        )
    if opportunity.portfolio_id != candidate.portfolio_id:
        return (
            StrategyDisposition.NO_TRADE,
            (DecisionReason.CANDIDATE_PORTFOLIO_MISMATCH,),
            None,
        )
    if opportunity.input_spec_digest != candidate.input_spec_digest:
        return (
            StrategyDisposition.NO_TRADE,
            (DecisionReason.INPUT_SPEC_MISMATCH,),
            None,
        )
    if opportunity.evidence_quality is not StrategyEvidenceQuality.VALID:
        return StrategyDisposition.NO_TRADE, (DecisionReason.EVIDENCE_NOT_VALID,), None
    max_age = timedelta(seconds=candidate.max_evidence_age_seconds)
    evidence_age = _utc_instant(opportunity.decision_time) - _utc_instant(
        opportunity.knowledge_time
    )
    if evidence_age > max_age:
        return StrategyDisposition.NO_TRADE, (DecisionReason.EVIDENCE_TOO_OLD,), None
    if any(name not in opportunity.signals for name in candidate.required_signals):
        return StrategyDisposition.NO_TRADE, (DecisionReason.MISSING_REQUIRED_SIGNAL,), None

    for rule in candidate.rules:
        if _matches(opportunity.signals[rule.signal_name], rule.operator, rule.threshold):
            return StrategyDisposition.PROPOSE_TRADE, (DecisionReason.RULE_MATCHED,), rule.rule_id
    return StrategyDisposition.NO_TRADE, (DecisionReason.NO_RULE_MATCHED,), None


@dataclass(frozen=True, slots=True, weakref_slot=True)
class StrategyDecision:
    decision_id: str
    candidate_id: str
    candidate_digest: str
    opportunity_id: str
    opportunity_digest: str
    disposition: StrategyDisposition
    reason_codes: tuple[DecisionReason, ...]
    matched_rule_id: str | None
    decided_at: datetime
    decision_digest: str

    def __post_init__(self) -> None:
        for value, name in (
            (self.decision_id, "decision_id"),
            (self.candidate_id, "candidate_id"),
            (self.candidate_digest, "candidate_digest"),
            (self.opportunity_id, "opportunity_id"),
            (self.opportunity_digest, "opportunity_digest"),
            (self.decision_digest, "decision_digest"),
        ):
            _require_text(value, name)
        if not isinstance(self.disposition, StrategyDisposition):
            raise ValueError("disposition must be StrategyDisposition")
        if not self.reason_codes or not all(
            isinstance(reason, DecisionReason) for reason in self.reason_codes
        ):
            raise ValueError("reason_codes must contain DecisionReason values")
        if self.disposition is StrategyDisposition.NO_TRADE and self.matched_rule_id is not None:
            raise ValueError("NO_TRADE cannot carry matched_rule_id")
        if self.disposition is StrategyDisposition.PROPOSE_TRADE:
            _require_text(self.matched_rule_id or "", "matched_rule_id")
        _require_aware(self.decided_at, "decided_at")

    def _expected_digest(self) -> str:
        return _digest(
            {
                "candidate_id": self.candidate_id,
                "candidate_digest": self.candidate_digest,
                "opportunity_id": self.opportunity_id,
                "opportunity_digest": self.opportunity_digest,
                "disposition": self.disposition,
                "reason_codes": self.reason_codes,
                "matched_rule_id": self.matched_rule_id,
                "decided_at": self.decided_at,
            }
        )

    @property
    def is_engine_issued(self) -> bool:
        expected_digest = self._expected_digest()
        identity_matches = (self.decision_id, self.decision_digest) == (
            f"strategy-decision:{expected_digest[:24]}",
            expected_digest,
        )
        return identity_matches and _verify_decision_issuance(self, expected_digest)

    @classmethod
    def _issue(
        cls,
        *,
        candidate: CandidateStrategy,
        opportunity: DecisionOpportunity,
    ) -> StrategyDecision:
        disposition, reason_codes, matched_rule_id = _evaluate_outcome(candidate, opportunity)
        payload: dict[str, object] = {
            "candidate_id": candidate.candidate_id,
            "candidate_digest": candidate.candidate_digest,
            "opportunity_id": opportunity.opportunity_id,
            "opportunity_digest": opportunity.opportunity_digest,
            "disposition": disposition,
            "reason_codes": reason_codes,
            "matched_rule_id": matched_rule_id,
            "decided_at": opportunity.decision_time,
        }
        digest = _digest(payload)
        decision = cls(
            decision_id=f"strategy-decision:{digest[:24]}",
            candidate_id=candidate.candidate_id,
            candidate_digest=candidate.candidate_digest,
            opportunity_id=opportunity.opportunity_id,
            opportunity_digest=opportunity.opportunity_digest,
            disposition=disposition,
            reason_codes=reason_codes,
            matched_rule_id=matched_rule_id,
            decided_at=opportunity.decision_time,
            decision_digest=digest,
        )
        _register_decision_issuance(decision, digest)
        return decision


@dataclass(frozen=True, slots=True, weakref_slot=True)
class TradeIntent:
    intent_id: str
    decision_digest: str
    candidate_id: str
    candidate_digest: str
    opportunity_digest: str
    instrument_id: TradableInstrumentId
    portfolio_id: str
    objective: EconomicObjective
    created_at: datetime
    source_digest: str
    intent_digest: str

    def __post_init__(self) -> None:
        for value, name in (
            (self.intent_id, "intent_id"),
            (self.decision_digest, "decision_digest"),
            (self.candidate_id, "candidate_id"),
            (self.candidate_digest, "candidate_digest"),
            (self.opportunity_digest, "opportunity_digest"),
            (self.portfolio_id, "portfolio_id"),
            (self.source_digest, "source_digest"),
            (self.intent_digest, "intent_digest"),
        ):
            _require_text(value, name)
        if not isinstance(self.instrument_id, TradableInstrumentId):
            raise ValueError("instrument_id must be TradableInstrumentId")
        if not isinstance(self.objective, EconomicObjective):
            raise ValueError("objective must be EconomicObjective")
        _require_aware(self.created_at, "created_at")

    def _expected_digest(self) -> str:
        return _digest(
            {
                "decision_digest": self.decision_digest,
                "candidate_id": self.candidate_id,
                "candidate_digest": self.candidate_digest,
                "opportunity_digest": self.opportunity_digest,
                "instrument_id": self.instrument_id,
                "portfolio_id": self.portfolio_id,
                "objective_digest": self.objective.objective_digest,
                "created_at": self.created_at,
                "source_digest": self.source_digest,
            }
        )

    @property
    def is_engine_issued(self) -> bool:
        expected_digest = self._expected_digest()
        identity_matches = (self.intent_id, self.intent_digest) == (
            f"trade-intent:{expected_digest[:24]}",
            expected_digest,
        )
        return identity_matches and _verify_intent_issuance(self, expected_digest)

    @classmethod
    def _build(
        cls,
        *,
        decision: StrategyDecision,
        candidate: CandidateStrategy,
        opportunity: DecisionOpportunity,
    ) -> TradeIntent:
        if not decision.is_engine_issued:
            raise ValueError("TradeIntent requires an engine-issued StrategyDecision")
        if decision.disposition is not StrategyDisposition.PROPOSE_TRADE:
            raise ValueError("TradeIntent requires PROPOSE_TRADE")
        if (decision.candidate_id, decision.candidate_digest) != (
            candidate.candidate_id,
            candidate.candidate_digest,
        ):
            raise ValueError("StrategyDecision candidate identity mismatch")
        if (
            decision.opportunity_id,
            decision.opportunity_digest,
            decision.decided_at,
        ) != (
            opportunity.opportunity_id,
            opportunity.opportunity_digest,
            opportunity.decision_time,
        ):
            raise ValueError("StrategyDecision opportunity identity mismatch")

        rules_by_id = {rule.rule_id: rule for rule in candidate.rules}
        objective = rules_by_id[decision.matched_rule_id or ""].objective
        payload: dict[str, object] = {
            "decision_digest": decision.decision_digest,
            "candidate_id": candidate.candidate_id,
            "candidate_digest": candidate.candidate_digest,
            "opportunity_digest": opportunity.opportunity_digest,
            "instrument_id": opportunity.instrument_id,
            "portfolio_id": opportunity.portfolio_id,
            "objective_digest": objective.objective_digest,
            "created_at": opportunity.decision_time,
            "source_digest": decision.decision_digest,
        }
        digest = _digest(payload)
        intent = cls(
            intent_id=f"trade-intent:{digest[:24]}",
            decision_digest=decision.decision_digest,
            candidate_id=candidate.candidate_id,
            candidate_digest=candidate.candidate_digest,
            opportunity_digest=opportunity.opportunity_digest,
            instrument_id=opportunity.instrument_id,
            portfolio_id=opportunity.portfolio_id,
            objective=objective,
            created_at=opportunity.decision_time,
            source_digest=decision.decision_digest,
            intent_digest=digest,
        )
        _register_intent_issuance(intent, digest)
        return intent


@dataclass(frozen=True, slots=True)
class StrategyEvaluationResult:
    decision: StrategyDecision
    trade_intent: TradeIntent | None
    result_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.decision, StrategyDecision) or not self.decision.is_engine_issued:
            raise ValueError("decision must be engine-issued StrategyDecision")
        if self.decision.disposition is StrategyDisposition.NO_TRADE:
            if self.trade_intent is not None:
                raise ValueError("NO_TRADE result cannot carry TradeIntent")
        else:
            if self.trade_intent is None or not self.trade_intent.is_engine_issued:
                raise ValueError("PROPOSE_TRADE result requires engine-issued TradeIntent")
            if self.trade_intent.decision_digest != self.decision.decision_digest:
                raise ValueError("TradeIntent decision_digest mismatch")
        object.__setattr__(
            self,
            "result_digest",
            _digest(
                {
                    "decision_digest": self.decision.decision_digest,
                    "intent_digest": (
                        self.trade_intent.intent_digest if self.trade_intent is not None else None
                    ),
                }
            ),
        )
