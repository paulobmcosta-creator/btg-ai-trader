"""Data-quality evidence model and evaluation for lossless normalization (S2-B)."""

from dataclasses import dataclass
from enum import Enum

from btg_ai_trader.observer.envelope import EventEnvelope
from btg_ai_trader.observer.identity import EventId
from btg_ai_trader.observer.market import CandleFinality, Tick
from btg_ai_trader.observer.values import MissingReason, require_text


class QualityFindingCategory(Enum):
    """Factual categories of data-quality observations."""

    TEMPORAL = "TEMPORAL"
    MARKET_FIELD = "MARKET_FIELD"
    INSTRUMENT_IDENTITY = "INSTRUMENT_IDENTITY"
    FINALITY = "FINALITY"


class QualityFindingCode(Enum):
    """Specific factual codes for data-quality observations; neutral, non-economic."""

    # Temporal findings
    MISSING_KNOWLEDGE_TIME = "MISSING_KNOWLEDGE_TIME"
    UNKNOWN_KNOWLEDGE_TIME = "UNKNOWN_KNOWLEDGE_TIME"
    MISSING_EVENT_TIME = "MISSING_EVENT_TIME"
    MISSING_EVENT_TIME_BASIS = "MISSING_EVENT_TIME_BASIS"
    MISSING_EVENT_TIME_RESOLUTION = "MISSING_EVENT_TIME_RESOLUTION"

    # Market payload findings - Tick
    MISSING_TICK_BID = "MISSING_TICK_BID"
    MISSING_TICK_ASK = "MISSING_TICK_ASK"
    MISSING_TICK_LAST = "MISSING_TICK_LAST"
    MISSING_TICK_VOLUME = "MISSING_TICK_VOLUME"

    # Market payload findings - Candle
    MISSING_CANDLE_OPEN = "MISSING_CANDLE_OPEN"
    MISSING_CANDLE_HIGH = "MISSING_CANDLE_HIGH"
    MISSING_CANDLE_LOW = "MISSING_CANDLE_LOW"
    MISSING_CANDLE_CLOSE = "MISSING_CANDLE_CLOSE"
    MISSING_CANDLE_VOLUME = "MISSING_CANDLE_VOLUME"
    MISSING_CANDLE_FINALIZED_AT = "MISSING_CANDLE_FINALIZED_AT"
    MISSING_CANDLE_AVAILABLE_AT = "MISSING_CANDLE_AVAILABLE_AT"

    # Instrument and Finality findings
    UNRESOLVED_INSTRUMENT_ID = "UNRESOLVED_INSTRUMENT_ID"
    UNRESOLVED_CANDLE_FINALITY = "UNRESOLVED_CANDLE_FINALITY"


@dataclass(frozen=True, slots=True)
class QualityFinding:
    """Immutable data-quality observation traceable to a specific source EventId."""

    event_id: EventId
    category: QualityFindingCategory
    code: QualityFindingCode
    field: str
    reason: MissingReason | str
    blocks_replay: bool
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, EventId):
            raise ValueError("event_id must be EventId")
        if not isinstance(self.category, QualityFindingCategory):
            raise ValueError("category must be QualityFindingCategory")
        if not isinstance(self.code, QualityFindingCode):
            raise ValueError("code must be QualityFindingCode")
        require_text(self.field, "field")
        if not isinstance(self.reason, MissingReason | str):
            raise ValueError("reason must be MissingReason or str")
        if type(self.blocks_replay) is not bool:
            raise ValueError("blocks_replay must be bool")
        require_text(self.detail, "detail")


def evaluate_envelope_quality(envelope: EventEnvelope) -> tuple[QualityFinding, ...]:
    """Inspect an immutable EventEnvelope losslessly and return its quality findings."""
    if not isinstance(envelope, EventEnvelope):
        raise ValueError("envelope must be an EventEnvelope instance")

    findings: list[QualityFinding] = []
    eid = envelope.event_id

    # 1. Temporal: knowledge_time (blocks replay if missing/unknown)
    kt = envelope.times.knowledge_time
    if isinstance(kt, MissingReason):
        code = (
            QualityFindingCode.UNKNOWN_KNOWLEDGE_TIME
            if kt is MissingReason.UNKNOWN
            else QualityFindingCode.MISSING_KNOWLEDGE_TIME
        )
        findings.append(
            QualityFinding(
                event_id=eid,
                category=QualityFindingCategory.TEMPORAL,
                code=code,
                field="times.knowledge_time",
                reason=kt,
                blocks_replay=True,
                detail=f"knowledge_time is {kt.value}",
            )
        )

    # 2. Temporal: event_time value, basis, resolution
    et = envelope.times.event_time
    if isinstance(et.value, MissingReason):
        findings.append(
            QualityFinding(
                event_id=eid,
                category=QualityFindingCategory.TEMPORAL,
                code=QualityFindingCode.MISSING_EVENT_TIME,
                field="times.event_time.value",
                reason=et.value,
                blocks_replay=False,
                detail=f"event_time value is {et.value.value}",
            )
        )
    if isinstance(et.basis, MissingReason):
        findings.append(
            QualityFinding(
                event_id=eid,
                category=QualityFindingCategory.TEMPORAL,
                code=QualityFindingCode.MISSING_EVENT_TIME_BASIS,
                field="times.event_time.basis",
                reason=et.basis,
                blocks_replay=False,
                detail=f"event_time basis is {et.basis.value}",
            )
        )
    if isinstance(et.resolution, MissingReason):
        findings.append(
            QualityFinding(
                event_id=eid,
                category=QualityFindingCategory.TEMPORAL,
                code=QualityFindingCode.MISSING_EVENT_TIME_RESOLUTION,
                field="times.event_time.resolution",
                reason=et.resolution,
                blocks_replay=False,
                detail=f"event_time resolution is {et.resolution.value}",
            )
        )

    # 3. Instrument identity
    if isinstance(envelope.instrument_id, MissingReason):
        findings.append(
            QualityFinding(
                event_id=eid,
                category=QualityFindingCategory.INSTRUMENT_IDENTITY,
                code=QualityFindingCode.UNRESOLVED_INSTRUMENT_ID,
                field="instrument_id",
                reason=envelope.instrument_id,
                blocks_replay=False,
                detail=f"instrument_id is {envelope.instrument_id.value}",
            )
        )

    # 4. Payload market fields
    payload = envelope.payload
    if isinstance(payload, Tick):
        tick_checks = (
            ("bid", QualityFindingCode.MISSING_TICK_BID),
            ("ask", QualityFindingCode.MISSING_TICK_ASK),
            ("last", QualityFindingCode.MISSING_TICK_LAST),
            ("volume", QualityFindingCode.MISSING_TICK_VOLUME),
        )
        for field_name, finding_code in tick_checks:
            val = getattr(payload, field_name)
            if isinstance(val, MissingReason):
                findings.append(
                    QualityFinding(
                        event_id=eid,
                        category=QualityFindingCategory.MARKET_FIELD,
                        code=finding_code,
                        field=f"payload.{field_name}",
                        reason=val,
                        blocks_replay=False,
                        detail=f"tick {field_name} is {val.value}",
                    )
                )
    else:  # Candle
        candle_checks = (
            ("open", QualityFindingCode.MISSING_CANDLE_OPEN),
            ("high", QualityFindingCode.MISSING_CANDLE_HIGH),
            ("low", QualityFindingCode.MISSING_CANDLE_LOW),
            ("close", QualityFindingCode.MISSING_CANDLE_CLOSE),
            ("volume", QualityFindingCode.MISSING_CANDLE_VOLUME),
        )
        for field_name, finding_code in candle_checks:
            val = getattr(payload, field_name)
            if isinstance(val, MissingReason):
                findings.append(
                    QualityFinding(
                        event_id=eid,
                        category=QualityFindingCategory.MARKET_FIELD,
                        code=finding_code,
                        field=f"payload.{field_name}",
                        reason=val,
                        blocks_replay=False,
                        detail=f"candle {field_name} is {val.value}",
                    )
                )
        if payload.finality is CandleFinality.UNKNOWN:
            findings.append(
                QualityFinding(
                    event_id=eid,
                    category=QualityFindingCategory.FINALITY,
                    code=QualityFindingCode.UNRESOLVED_CANDLE_FINALITY,
                    field="payload.finality",
                    reason=CandleFinality.UNKNOWN.value,
                    blocks_replay=False,
                    detail="candle finality is UNKNOWN",
                )
            )
        if isinstance(payload.finalized_at, MissingReason):
            findings.append(
                QualityFinding(
                    event_id=eid,
                    category=QualityFindingCategory.FINALITY,
                    code=QualityFindingCode.MISSING_CANDLE_FINALIZED_AT,
                    field="payload.finalized_at",
                    reason=payload.finalized_at,
                    blocks_replay=False,
                    detail=f"candle finalized_at is {payload.finalized_at.value}",
                )
            )
        if isinstance(payload.available_at, MissingReason):
            findings.append(
                QualityFinding(
                    event_id=eid,
                    category=QualityFindingCategory.FINALITY,
                    code=QualityFindingCode.MISSING_CANDLE_AVAILABLE_AT,
                    field="payload.available_at",
                    reason=payload.available_at,
                    blocks_replay=False,
                    detail=f"candle available_at is {payload.available_at.value}",
                )
            )

    return tuple(findings)
