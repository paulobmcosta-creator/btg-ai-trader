"""Comprehensive unit and property tests for Lossless Normalization & Quality Evidence (S2-B)."""

import ast
import inspect
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest

import btg_ai_trader.data_platform as dp_module
from btg_ai_trader.data_platform import (
    CausalLane,
    NormalizedMarketBatch,
    QualityFinding,
    QualityFindingCategory,
    QualityFindingCode,
    evaluate_envelope_quality,
    normalize_market_batch,
)
from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.identity import (
    CorrelationId,
    EventId,
    ProviderInstrumentRef,
    TradableInstrumentId,
)
from btg_ai_trader.observer.market import Candle, CandleFinality, Tick
from btg_ai_trader.observer.temporal import EventTime, ObservationTimes, TemporalValue
from btg_ai_trader.observer.values import MissingReason, NumericValue


def _utc(second: int, *, microsecond: int = 0) -> datetime:
    return datetime(2026, 1, 2, 10, 0, 0, tzinfo=UTC) + timedelta(
        seconds=second, microseconds=microsecond
    )


def _event(
    number: int,
    *,
    provider: str = "fixture-provider",
    scope: str = "capture-a",
    symbol: str = "WINF26",
    instrument_id: TradableInstrumentId | MissingReason | None = None,
    knowledge_time: TemporalValue | None = None,
    event_time_value: TemporalValue | None = None,
    event_time_basis: str | MissingReason = "fixture-clock",
    event_time_resolution: timedelta | MissingReason = timedelta(microseconds=1),
    effective_time: TemporalValue = MissingReason.NOT_APPLICABLE,
    payload: Tick | Candle | None = None,
    external_event_id: str | None = None,
    source_sequence: int | None = None,
    sequence_scope: str | None = None,
    ingestion_order: int | None = None,
    correlation_id: CorrelationId | None = None,
    causation_id: EventId | None = None,
) -> EventEnvelope:
    ingestion = _utc(number)
    et_val = ingestion if event_time_value is None else event_time_value
    event_time = EventTime(
        value=et_val,
        basis=event_time_basis,
        resolution=event_time_resolution,
    )
    kt = ingestion if knowledge_time is None else knowledge_time
    inst_id = (
        TradableInstrumentId(str(UUID(int=10_000 + number)))
        if instrument_id is None
        else instrument_id
    )
    actual_payload = (
        Tick(
            bid=Decimal("100.00"),
            ask=Decimal("100.50"),
            last=Decimal("100.25"),
            volume=Decimal("1"),
        )
        if payload is None
        else payload
    )
    event_type = (
        EventType.TICK if isinstance(actual_payload, Tick) else EventType.CANDLE
    )
    seq = number if source_sequence is None and sequence_scope is not None else source_sequence
    seq_scope = "scope-1" if seq is not None and sequence_scope is None else sequence_scope
    return EventEnvelope(
        event_id=EventId(str(UUID(int=number + 1))),
        event_type=event_type,
        source=ProviderInstrumentRef(provider, scope, symbol),
        instrument_id=inst_id,
        times=ObservationTimes(
            event_time=event_time,
            ingestion_time=ingestion,
            knowledge_time=kt,
            effective_time=effective_time,
        ),
        payload=actual_payload,
        external_event_id=external_event_id,
        source_sequence=seq,
        sequence_scope=seq_scope,
        ingestion_order=number if ingestion_order is None else ingestion_order,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )


# 1. Empty normalization batch
def test_empty_normalization_batch() -> None:
    lane = CausalLane("prov", "scope")
    batch = normalize_market_batch([], lane=lane)
    assert batch.lane == lane
    assert batch.provider_id == "prov"
    assert batch.capture_scope == "scope"
    assert len(batch) == 0
    assert batch.event_count == 0
    assert batch.events == ()
    assert batch.quality_findings == ()
    assert batch.is_clean is True
    assert batch.blocks_replay is False
    assert batch.instruments == ()

    # Empty batch with explicit provider_id and capture_scope
    batch2 = normalize_market_batch([], provider_id="prov2", capture_scope="scope2")
    assert batch2.provider_id == "prov2"
    assert batch2.capture_scope == "scope2"

    # Empty batch without lane or (provider_id, capture_scope) raises ValueError
    with pytest.raises(ValueError, match="empty events requires explicit lane"):
        normalize_market_batch([])


# 2. Defensive input capture and immutability
def test_defensive_input_capture_and_immutability() -> None:
    e0 = _event(0)
    e1 = _event(1)
    event_list = [e0, e1]

    batch = normalize_market_batch(event_list)
    assert len(batch) == 2

    # Mutating caller list does not affect batch
    event_list.append(_event(2))
    assert len(batch) == 2
    assert len(batch.events) == 2

    # Batch is frozen
    with pytest.raises(FrozenInstanceError):
        batch.lane = CausalLane("other", "other")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        batch.events = ()  # type: ignore[misc]

    # Indexing access
    assert batch[0] is e0
    assert batch[1] is e1


# 3. Multiple instruments within same lane
def test_multiple_instruments_in_same_lane() -> None:
    e0 = _event(0, symbol="WINF26")
    e1 = _event(1, symbol="PETR4")
    e2 = _event(2, symbol="VALE3")
    e3 = _event(3, symbol="PETR4")

    batch = normalize_market_batch([e0, e1, e2, e3])
    assert len(batch) == 4
    assert batch.instruments == ("PETR4", "VALE3", "WINF26")
    assert batch.is_clean is True


# 4. Mixed provider rejection
def test_mixed_provider_rejection() -> None:
    e0 = _event(0, provider="provider-A")
    e1 = _event(1, provider="provider-B")

    with pytest.raises(ValueError, match="mixed provider rejected"):
        normalize_market_batch([e0, e1])

    # Conflicting with explicit lane
    lane = CausalLane("provider-A", "capture-a")
    with pytest.raises(ValueError, match="mixed provider rejected"):
        normalize_market_batch([e0, e1], lane=lane)


# 5. Mixed capture scope rejection
def test_mixed_capture_scope_rejection() -> None:
    e0 = _event(0, scope="scope-A")
    e1 = _event(1, scope="scope-B")

    with pytest.raises(ValueError, match="mixed capture scope rejected"):
        normalize_market_batch([e0, e1])

    # Conflicting with explicit lane
    lane = CausalLane("fixture-provider", "scope-A")
    with pytest.raises(ValueError, match="mixed capture scope rejected"):
        normalize_market_batch([e0, e1], lane=lane)


# 6. Exact preservation of source facts
def test_exact_preservation_of_source_facts() -> None:
    corr_id = CorrelationId(str(UUID(int=999)))
    caus_id = EventId(str(UUID(int=888)))
    inst_id = TradableInstrumentId(str(UUID(int=777)))

    original = _event(
        42,
        provider="xp-mt5",
        scope="s1-xp-capture-a12",
        symbol="WINZ26",
        instrument_id=inst_id,
        knowledge_time=_utc(50),
        event_time_value=_utc(40),
        event_time_basis="mt5-exchange",
        event_time_resolution=timedelta(milliseconds=1),
        effective_time=_utc(45),
        external_event_id="ext-12345",
        source_sequence=1001,
        sequence_scope="feed-partition-0",
        ingestion_order=42,
        correlation_id=corr_id,
        causation_id=caus_id,
    )

    batch = normalize_market_batch([original])
    normalized = batch[0]

    # Every single field is preserved identically
    assert normalized.event_id == original.event_id
    assert normalized.event_type == original.event_type
    assert normalized.source == original.source
    assert normalized.source.provider == "xp-mt5"
    assert normalized.source.scope == "s1-xp-capture-a12"
    assert normalized.source.symbol == "WINZ26"
    assert normalized.instrument_id == inst_id
    assert normalized.times.event_time.value == _utc(40)
    assert normalized.times.event_time.basis == "mt5-exchange"
    assert normalized.times.event_time.resolution == timedelta(milliseconds=1)
    assert normalized.times.ingestion_time == _utc(42)
    assert normalized.times.knowledge_time == _utc(50)
    assert normalized.times.effective_time == _utc(45)
    assert normalized.payload == original.payload
    assert normalized.envelope_version == 1
    assert normalized.schema_version == 1
    assert normalized.external_event_id == "ext-12345"
    assert normalized.source_sequence == 1001
    assert normalized.sequence_scope == "feed-partition-0"
    assert normalized.ingestion_order == 42
    assert normalized.correlation_id == corr_id
    assert normalized.causation_id == caus_id

    # Order preservation
    e_rev0 = _event(10)
    e_rev1 = _event(5)
    e_rev2 = _event(8)
    batch_order = normalize_market_batch([e_rev0, e_rev1, e_rev2])
    assert [e.ingestion_order for e in batch_order] == [10, 5, 8]


# 7. Tick missingness preservation
@pytest.mark.parametrize(
    ("missing_field", "finding_code"),
    [
        ("bid", QualityFindingCode.MISSING_TICK_BID),
        ("ask", QualityFindingCode.MISSING_TICK_ASK),
        ("last", QualityFindingCode.MISSING_TICK_LAST),
        ("volume", QualityFindingCode.MISSING_TICK_VOLUME),
    ],
)
def test_tick_missingness_preservation_individual(
    missing_field: str, finding_code: QualityFindingCode
) -> None:
    kwargs: dict[str, NumericValue] = {
        "bid": Decimal("100.00"),
        "ask": Decimal("100.50"),
        "last": Decimal("100.25"),
        "volume": Decimal("10"),
    }
    kwargs[missing_field] = MissingReason.NOT_PROVIDED

    tick = Tick(**kwargs)
    event = _event(0, payload=tick)
    batch = normalize_market_batch([event])

    norm_tick = batch[0].payload
    assert isinstance(norm_tick, Tick)
    assert getattr(norm_tick, missing_field) is MissingReason.NOT_PROVIDED

    findings = batch.quality_findings
    assert len(findings) == 1
    f = findings[0]
    assert f.event_id == event.event_id
    assert f.category == QualityFindingCategory.MARKET_FIELD
    assert f.code == finding_code
    assert f.field == f"payload.{missing_field}"
    assert f.reason == MissingReason.NOT_PROVIDED
    assert f.blocks_replay is False


def test_tick_multiple_missing_fields_preserved() -> None:
    tick = Tick(
        bid=MissingReason.UNKNOWN,
        ask=MissingReason.NOT_PROVIDED,
        last=Decimal("100.00"),
        volume=MissingReason.NOT_APPLICABLE,
    )
    event = _event(0, payload=tick)
    batch = normalize_market_batch([event])

    norm_tick = batch[0].payload
    assert isinstance(norm_tick, Tick)
    assert norm_tick.bid is MissingReason.UNKNOWN
    assert norm_tick.ask is MissingReason.NOT_PROVIDED
    assert norm_tick.last == Decimal("100.00")
    assert norm_tick.volume is MissingReason.NOT_APPLICABLE

    findings = batch.findings_for_event(event.event_id)
    assert len(findings) == 3
    codes = {f.code for f in findings}
    assert codes == {
        QualityFindingCode.MISSING_TICK_BID,
        QualityFindingCode.MISSING_TICK_ASK,
        QualityFindingCode.MISSING_TICK_VOLUME,
    }


# 8. Candle missingness preservation
def test_candle_missingness_preservation() -> None:
    candle = Candle(
        interval_start=_utc(0),
        interval_end=_utc(60),
        finality=CandleFinality.UNKNOWN,
        finalized_at=MissingReason.NOT_APPLICABLE,
        available_at=MissingReason.NOT_PROVIDED,
        open=Decimal("100.00"),
        high=MissingReason.UNKNOWN,
        low=MissingReason.UNKNOWN,
        close=Decimal("101.00"),
        volume=MissingReason.NOT_PROVIDED,
    )
    event = _event(0, payload=candle)
    batch = normalize_market_batch([event])

    norm_candle = batch[0].payload
    assert isinstance(norm_candle, Candle)
    assert norm_candle.finality == CandleFinality.UNKNOWN
    assert norm_candle.finalized_at is MissingReason.NOT_APPLICABLE
    assert norm_candle.available_at is MissingReason.NOT_PROVIDED
    assert norm_candle.high is MissingReason.UNKNOWN
    assert norm_candle.low is MissingReason.UNKNOWN
    assert norm_candle.volume is MissingReason.NOT_PROVIDED

    findings = batch.findings_for_event(event.event_id)
    codes = {f.code for f in findings}
    assert QualityFindingCode.MISSING_CANDLE_HIGH in codes
    assert QualityFindingCode.MISSING_CANDLE_LOW in codes
    assert QualityFindingCode.MISSING_CANDLE_VOLUME in codes
    assert QualityFindingCode.UNRESOLVED_CANDLE_FINALITY in codes
    assert QualityFindingCode.MISSING_CANDLE_FINALIZED_AT in codes
    assert QualityFindingCode.MISSING_CANDLE_AVAILABLE_AT in codes

    for f in findings:
        assert f.blocks_replay is False


def test_clean_candle_produces_no_findings() -> None:
    candle = Candle(
        interval_start=_utc(0),
        interval_end=_utc(60),
        finality=CandleFinality.FINAL,
        finalized_at=_utc(60),
        available_at=_utc(65),
        open=Decimal("100.00"),
        high=Decimal("105.00"),
        low=Decimal("99.00"),
        close=Decimal("102.00"),
        volume=Decimal("500"),
    )
    event = _event(0, payload=candle)
    batch = normalize_market_batch([event])
    assert batch.is_clean is True
    assert len(batch.quality_findings) == 0


# 9. Missing or unknown knowledge_time marked replay-blocking
@pytest.mark.parametrize(
    ("reason", "expected_code"),
    [
        (MissingReason.UNKNOWN, QualityFindingCode.UNKNOWN_KNOWLEDGE_TIME),
        (MissingReason.NOT_PROVIDED, QualityFindingCode.MISSING_KNOWLEDGE_TIME),
        (MissingReason.NOT_APPLICABLE, QualityFindingCode.MISSING_KNOWLEDGE_TIME),
    ],
)
def test_missing_or_unknown_knowledge_time_marked_replay_blocking(
    reason: MissingReason, expected_code: QualityFindingCode
) -> None:
    event = _event(0, knowledge_time=reason)
    batch = normalize_market_batch([event])

    assert batch[0].times.knowledge_time is reason
    assert batch.blocks_replay is True

    blocking = batch.replay_blocking_findings
    assert len(blocking) == 1
    f = blocking[0]
    assert f.event_id == event.event_id
    assert f.category == QualityFindingCategory.TEMPORAL
    assert f.code == expected_code
    assert f.field == "times.knowledge_time"
    assert f.reason == reason
    assert f.blocks_replay is True


# 10. Known knowledge_time retained unmutated
def test_known_knowledge_time_retained_unmutated() -> None:
    kt = _utc(100)
    event = _event(0, knowledge_time=kt)
    batch = normalize_market_batch([event])

    assert batch[0].times.knowledge_time == kt
    assert batch.blocks_replay is False
    assert batch.replay_blocking_findings == ()


# 11. Missing event-time evidence surfaced as quality evidence
def test_missing_event_time_evidence_surfaced_as_quality_evidence() -> None:
    event = _event(
        0,
        event_time_value=MissingReason.UNKNOWN,
        event_time_basis=MissingReason.NOT_PROVIDED,
        event_time_resolution=MissingReason.NOT_APPLICABLE,
    )
    batch = normalize_market_batch([event])

    norm_et = batch[0].times.event_time
    assert norm_et.value is MissingReason.UNKNOWN
    assert norm_et.basis is MissingReason.NOT_PROVIDED
    assert norm_et.resolution is MissingReason.NOT_APPLICABLE

    findings = batch.quality_findings
    codes = {f.code for f in findings}
    assert codes == {
        QualityFindingCode.MISSING_EVENT_TIME,
        QualityFindingCode.MISSING_EVENT_TIME_BASIS,
        QualityFindingCode.MISSING_EVENT_TIME_RESOLUTION,
    }
    for f in findings:
        assert f.blocks_replay is False


# 12. Unresolved instrument identity
def test_unresolved_instrument_identity_surfaced() -> None:
    event = _event(0, instrument_id=MissingReason.UNKNOWN)
    batch = normalize_market_batch([event])

    assert batch[0].instrument_id is MissingReason.UNKNOWN
    findings = batch.quality_findings
    assert len(findings) == 1
    assert findings[0].code == QualityFindingCode.UNRESOLVED_INSTRUMENT_ID
    assert findings[0].blocks_replay is False


# 13. No temporal-axis substitution
def test_no_temporal_axis_substitution() -> None:
    event_val = _utc(10)
    ingest_val = _utc(20)
    effect_val = _utc(30)

    # Event with missing knowledge_time
    event = _event(
        20,
        event_time_value=event_val,
        knowledge_time=MissingReason.UNKNOWN,
        effective_time=effect_val,
    )
    batch = normalize_market_batch([event])
    norm = batch[0]

    # No substitution occurred
    assert norm.times.knowledge_time is MissingReason.UNKNOWN
    assert norm.times.knowledge_time != norm.times.event_time.value
    assert norm.times.knowledge_time != norm.times.ingestion_time
    assert norm.times.knowledge_time != norm.times.effective_time
    assert norm.times.event_time.value == event_val
    assert norm.times.ingestion_time == ingest_val
    assert norm.times.effective_time == effect_val


# 14. Deterministic repeated normalization
def test_deterministic_repeated_normalization() -> None:
    e0 = _event(0, knowledge_time=MissingReason.UNKNOWN)
    e1 = _event(
        1,
        payload=Tick(
            bid=Decimal("10.00"),
            ask=Decimal("10.50"),
            last=Decimal("10.25"),
            volume=MissingReason.NOT_PROVIDED,
        ),
    )

    batch_a = normalize_market_batch([e0, e1])
    batch_b = normalize_market_batch([e0, e1])

    assert batch_a.events == batch_b.events
    assert batch_a.quality_findings == batch_b.quality_findings
    assert batch_a.blocks_replay == batch_b.blocks_replay
    assert batch_a.instruments == batch_b.instruments


# 15. Source envelope remains unchanged
def test_source_envelope_remains_unchanged() -> None:
    original = _event(0, knowledge_time=MissingReason.UNKNOWN)
    original_dict = {f: getattr(original, f) for f in original.__slots__}

    batch = normalize_market_batch([original])
    post_dict = {f: getattr(original, f) for f in original.__slots__}

    assert original_dict == post_dict
    assert batch[0] is original


# 16. Finding-to-source EventId lineage
def test_finding_to_source_event_id_lineage() -> None:
    e0 = _event(0, knowledge_time=MissingReason.UNKNOWN)
    e1 = _event(1)
    e2 = _event(2, instrument_id=MissingReason.NOT_PROVIDED)

    batch = normalize_market_batch([e0, e1, e2])
    assert len(batch.quality_findings) == 2

    findings_e0 = batch.findings_for_event(e0.event_id)
    assert len(findings_e0) == 1
    assert findings_e0[0].event_id == e0.event_id

    findings_e1 = batch.findings_for_event(e1.event_id)
    assert len(findings_e1) == 0

    findings_e2 = batch.findings_for_event(e2.event_id)
    assert len(findings_e2) == 1
    assert findings_e2[0].event_id == e2.event_id


# 17. QualityFinding and evaluate_envelope_quality validation
def test_quality_finding_validation() -> None:
    eid = EventId(str(UUID(int=1)))
    with pytest.raises(ValueError, match="event_id must be EventId"):
        QualityFinding(
            event_id="not-id",  # type: ignore[arg-type]
            category=QualityFindingCategory.TEMPORAL,
            code=QualityFindingCode.MISSING_KNOWLEDGE_TIME,
            field="field",
            reason=MissingReason.UNKNOWN,
            blocks_replay=True,
            detail="detail",
        )
    with pytest.raises(ValueError, match="category must be QualityFindingCategory"):
        QualityFinding(
            event_id=eid,
            category="not-cat",  # type: ignore[arg-type]
            code=QualityFindingCode.MISSING_KNOWLEDGE_TIME,
            field="field",
            reason=MissingReason.UNKNOWN,
            blocks_replay=True,
            detail="detail",
        )
    with pytest.raises(ValueError, match="code must be QualityFindingCode"):
        QualityFinding(
            event_id=eid,
            category=QualityFindingCategory.TEMPORAL,
            code="not-code",  # type: ignore[arg-type]
            field="field",
            reason=MissingReason.UNKNOWN,
            blocks_replay=True,
            detail="detail",
        )
    with pytest.raises(ValueError, match="field must be nonempty text"):
        QualityFinding(
            event_id=eid,
            category=QualityFindingCategory.TEMPORAL,
            code=QualityFindingCode.MISSING_KNOWLEDGE_TIME,
            field="",
            reason=MissingReason.UNKNOWN,
            blocks_replay=True,
            detail="detail",
        )
    with pytest.raises(ValueError, match="reason must be MissingReason or str"):
        QualityFinding(
            event_id=eid,
            category=QualityFindingCategory.TEMPORAL,
            code=QualityFindingCode.MISSING_KNOWLEDGE_TIME,
            field="field",
            reason=123,  # type: ignore[arg-type]
            blocks_replay=True,
            detail="detail",
        )
    with pytest.raises(ValueError, match="blocks_replay must be bool"):
        QualityFinding(
            event_id=eid,
            category=QualityFindingCategory.TEMPORAL,
            code=QualityFindingCode.MISSING_KNOWLEDGE_TIME,
            field="field",
            reason=MissingReason.UNKNOWN,
            blocks_replay="not-bool",  # type: ignore[arg-type]
            detail="detail",
        )
    with pytest.raises(ValueError, match="detail must be nonempty text"):
        QualityFinding(
            event_id=eid,
            category=QualityFindingCategory.TEMPORAL,
            code=QualityFindingCode.MISSING_KNOWLEDGE_TIME,
            field="field",
            reason=MissingReason.UNKNOWN,
            blocks_replay=True,
            detail="   ",
        )

    with pytest.raises(ValueError, match="envelope must be an EventEnvelope"):
        evaluate_envelope_quality("not-envelope")  # type: ignore[arg-type]


# 18. NormalizedMarketBatch validation
def test_normalized_market_batch_validation() -> None:
    lane = CausalLane("p", "s")
    e0 = _event(0, provider="p", scope="s")
    eid = EventId(str(UUID(int=1)))
    f0 = QualityFinding(
        event_id=eid,
        category=QualityFindingCategory.TEMPORAL,
        code=QualityFindingCode.MISSING_KNOWLEDGE_TIME,
        field="times.knowledge_time",
        reason=MissingReason.UNKNOWN,
        blocks_replay=True,
        detail="detail",
    )

    with pytest.raises(ValueError, match="lane must be a CausalLane"):
        NormalizedMarketBatch(lane="not-lane", events=(e0,), quality_findings=(f0,))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="events must be a tuple"):
        NormalizedMarketBatch(lane=lane, events=[e0], quality_findings=(f0,))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="events must contain EventEnvelope"):
        NormalizedMarketBatch(lane=lane, events=("not-envelope",), quality_findings=(f0,))  # type: ignore[arg-type]

    e_bad_p = _event(0, provider="other-p", scope="s")
    with pytest.raises(ValueError, match="event provider does not match lane"):
        NormalizedMarketBatch(lane=lane, events=(e_bad_p,), quality_findings=(f0,))

    e_bad_s = _event(0, provider="p", scope="other-s")
    with pytest.raises(ValueError, match="event capture scope does not match lane"):
        NormalizedMarketBatch(lane=lane, events=(e_bad_s,), quality_findings=(f0,))

    with pytest.raises(ValueError, match="quality_findings must be a tuple"):
        NormalizedMarketBatch(lane=lane, events=(e0,), quality_findings=[f0])  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="quality_findings must contain QualityFinding"):
        NormalizedMarketBatch(lane=lane, events=(e0,), quality_findings=("not-finding",))  # type: ignore[arg-type]


# 19. normalize_market_batch parameter conflict handling
def test_normalize_market_batch_parameter_conflicts() -> None:
    e0 = _event(0, provider="p1", scope="s1")

    with pytest.raises(ValueError, match="all items must be EventEnvelope"):
        normalize_market_batch(["not-envelope"])  # type: ignore[list-item]

    lane = CausalLane("p1", "s1")
    with pytest.raises(ValueError, match="lane must be a CausalLane"):
        normalize_market_batch([e0], lane="not-lane")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="conflicting provider_id and lane"):
        normalize_market_batch([e0], lane=lane, provider_id="p2")

    with pytest.raises(ValueError, match="conflicting capture_scope and lane"):
        normalize_market_batch([e0], lane=lane, capture_scope="s2")

    with pytest.raises(ValueError, match="conflicting provider_id and first event"):
        normalize_market_batch([e0], provider_id="p2")

    with pytest.raises(ValueError, match="conflicting capture_scope and first event"):
        normalize_market_batch([e0], capture_scope="s2")


# 20. Static absence of prohibited capabilities in data_platform
def test_static_absence_of_prohibited_capabilities() -> None:
    src_dir = Path(inspect.getfile(dp_module)).parent
    assert src_dir.is_dir()

    prohibited_imports = {"MetaTrader5", "requests", "httpx", "aiohttp", "socket", "urllib"}
    prohibited_calls = {"sleep", "now", "utcnow", "time"}
    prohibited_keywords = {
        "TradeIntent",
        "StrategyDecision",
        "OrderIntent",
        "ExecutionOrder",
        "RiskEngine",
        "FinancialLedger",
        "PnL",
        "SlippageModel",
        "SpreadModel",
        "interpolate",
        "fillna",
        "bfill",
        "ffill",
    }

    for py_file in src_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in prohibited_imports, (
                        f"Prohibited import {alias.name} in {py_file}"
                    )
            elif isinstance(node, ast.ImportFrom):
                assert node.module not in prohibited_imports, (
                    f"Prohibited import from {node.module} in {py_file}"
                )
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    assert func.id not in prohibited_calls, (
                        f"Prohibited call {func.id} in {py_file}"
                    )
                elif isinstance(func, ast.Attribute):
                    assert func.attr not in prohibited_calls, (
                        f"Prohibited method call {func.attr} in {py_file}"
                    )
            elif isinstance(node, ast.Name):
                assert node.id not in prohibited_keywords, (
                    f"Prohibited name {node.id} in {py_file}"
                )
