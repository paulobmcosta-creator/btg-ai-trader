"""Seeded generated invariant checks with independent bounded reference models."""

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from random import Random
from typing import cast
from uuid import UUID

import pytest

from btg_ai_trader.observer.admission import (
    Admitted,
    IngressMetadata,
    Quarantined,
    RejectionReason,
    admit_fixture,
)
from btg_ai_trader.observer.dedup import (
    DedupState,
    DedupStatus,
    LateStatus,
    annotate_late,
    classify_duplicate,
)
from btg_ai_trader.observer.envelope import EventEnvelope, EventType
from btg_ai_trader.observer.identity import (
    ArtifactId,
    EventId,
    LineageRecordId,
    ProviderInstrumentRef,
    RunId,
    TradableInstrumentId,
)
from btg_ai_trader.observer.ingestion import ObservationQueue, OfferStatus, offer, take
from btg_ai_trader.observer.lineage import (
    ArtifactLineageRecord,
    LineageGraph,
    TransformationKind,
)
from btg_ai_trader.observer.market import Tick
from btg_ai_trader.observer.provenance import ContentHash, InputIdentity
from btg_ai_trader.observer.raw_source import RawChannel, RawFrame
from btg_ai_trader.observer.storage_records import (
    EvidenceRecord,
    PersistenceRecordId,
    content_hash,
    decode_record,
    encode_record,
)
from btg_ai_trader.observer.temporal import EventTime, ObservationTimes
from btg_ai_trader.observer.values import MissingReason

SEEDS = (7, 19, 43, 101, 509, 2026)
T0 = datetime(2026, 9, 13, tzinfo=UTC)
MISSING = MissingReason.UNKNOWN
SOURCE = ProviderInstrumentRef("fixture", "generated", "TEST")


def generated_event(identity: int, value: int = 0) -> EventEnvelope:
    return EventEnvelope(
        EventId(str(UUID(int=identity + 1))), EventType.TICK, SOURCE,
        TradableInstrumentId(str(UUID(int=9000))),
        ObservationTimes(EventTime(T0, "source", timedelta(seconds=1)), T0, T0),
        Tick(Decimal("1"), Decimal("2"), Decimal(value), MISSING),
    )


@pytest.mark.parametrize("seed", SEEDS)
def test_generated_queue_state_machine(seed: int) -> None:
    rng = Random(seed)
    capacity = (1, 2, 5, 13)[seed % 4]
    queue = ObservationQueue.empty("generated", capacity)
    model: list[EventEnvelope] = []
    accepted = dequeued = rejected = 0
    for step in range(360):
        before = queue
        prior_items = tuple(model)
        if rng.randrange(10) < 7:
            item = generated_event(step, rng.randrange(20))
            result = offer(queue, item)
            queue = result.queue
            if len(model) == capacity:
                rejected += 1
                assert result.status is OfferStatus.BACKPRESSURE
                assert result.item is item
            else:
                accepted += 1
                model.append(item)
                assert result.status is OfferStatus.ACCEPTED
        else:
            delivery = take(queue)
            queue = delivery.queue
            expected = model.pop(0) if model else None
            assert delivery.item is expected
            dequeued += int(expected is not None)
        assert before.items == prior_items
        assert queue.items == tuple(model)
        assert len(queue.items) <= capacity
        assert queue.snapshot.accepted == accepted
        assert queue.snapshot.dequeued == dequeued
        assert queue.snapshot.backpressure_count == rejected
        assert accepted - dequeued == len(model)
    while model:
        drained = take(queue)
        queue = drained.queue
        assert drained.item is model.pop(0)
    assert take(queue).item is None


@pytest.mark.parametrize("seed", SEEDS)
def test_generated_dedup_state_machine(seed: int) -> None:
    rng = Random(seed)
    capacity = (1, 3, 7)[seed % 3]
    state = DedupState("generated", capacity)
    model: dict[int, tuple[int, EventEnvelope]] = {}
    for step in range(360):
        identity, value = rng.randrange(12), rng.randrange(3)
        incoming = replace(
            generated_event(identity, value),
            ingestion_order=step,
            times=replace(
                generated_event(identity).times,
                ingestion_time=T0 + timedelta(microseconds=step),
                knowledge_time=MISSING,
            ),
        )
        previous = state
        expected_original = model.get(identity)
        result = classify_duplicate(state, incoming)
        state = result.state
        if expected_original is not None:
            expected_status = (
                DedupStatus.DUPLICATE if expected_original[0] == value
                else DedupStatus.IDENTITY_CONFLICT
            )
            assert result.status is expected_status
            assert result.canonical is expected_original[1]
            assert state is previous
        elif len(model) == capacity:
            assert result.status is DedupStatus.CAPACITY_EXHAUSTED
            assert result.canonical is None
            assert state is previous
        else:
            assert result.status is DedupStatus.NEW
            model[identity] = (value, incoming)
        assert result.incoming is incoming
        assert state.canonical == tuple(entry[1] for entry in model.values())
        assert len(state.canonical) <= capacity


@pytest.mark.parametrize("seed", SEEDS)
def test_generated_canonical_codec_and_corruption(seed: int) -> None:
    rng = Random(seed)
    for index in range(45):
        raw = rng.randbytes(rng.randrange(513))
        record = EvidenceRecord(
            PersistenceRecordId(str(UUID(int=index + 1))),
            InputIdentity(EventId(str(UUID(int=index + 100))), content_hash(raw)),
            T0 + timedelta(microseconds=rng.randrange(1000000)), raw,
        )
        encoded = encode_record(record)
        decoded = decode_record(encoded)
        assert decoded == record
        assert isinstance(decoded, EvidenceRecord)
        assert decoded.raw == raw
        assert encode_record(decoded) == encoded
        with pytest.raises(ValueError):
            decode_record(encoded[:-1] + b" \n")
        with pytest.raises(ValueError):
            decode_record(encoded[:rng.randrange(1, len(encoded) - 1)])
        with pytest.raises(ValueError):
            replace(record, raw=raw + b"x")
        fields = cast(dict[str, object], json.loads(encoded))
        fields["schema"] = rng.choice((True, 0, 2, "1"))
        with pytest.raises(ValueError):
            decode_record(json.dumps(fields).encode())


def fixture_document(identity: int, number: int) -> dict[str, object]:
    return {
        "envelope_version": 1, "schema_version": 1,
        "event_id": str(UUID(int=identity + 1)), "event_type": "TICK",
        "source": {"provider": "fixture", "scope": "generated", "symbol": "TEST"},
        "instrument_id": {"missing": "UNKNOWN"},
        "event_time": {
            "value": {"missing": "UNKNOWN"}, "basis": {"missing": "UNKNOWN"},
            "resolution_us": {"missing": "UNKNOWN"},
        },
        "effective_time": {"missing": "NOT_APPLICABLE"},
        "payload": {
            "bid": {"decimal": "1"}, "ask": {"decimal": "2"},
            "last": {"decimal": str(number)}, "volume": {"missing": "UNKNOWN"},
        },
        "external_event_id": None, "source_sequence": None, "sequence_scope": None,
        "correlation_id": None, "causation_id": None,
    }


@pytest.mark.parametrize("seed", SEEDS)
def test_generated_json_quarantine_preserves_raw(seed: int) -> None:
    rng = Random(seed)
    context = IngressMetadata(T0, MISSING, None)
    for index in range(35):
        encoded = json.dumps(fixture_document(index, rng.randrange(1000))).encode()
        frame = RawFrame(encoded, SOURCE, RawChannel.TICK)
        accepted = admit_fixture(frame, context, max_payload_bytes=len(encoded))
        assert isinstance(accepted, Admitted)
        assert accepted.raw is frame
        assert accepted.ingress is context
        assert accepted.envelope.times.event_time.value is MISSING
        duplicate = encoded.replace(
            b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1'
        )
        malformed = (
            duplicate, encoded[:rng.randrange(1, len(encoded))],
            b"\xff" + encoded, encoded + b"x",
        )
        for payload in malformed:
            rejected_frame = replace(frame, payload=payload)
            rejected = admit_fixture(
                rejected_frame, context, max_payload_bytes=len(payload) + 1
            )
            assert isinstance(rejected, Quarantined)
            assert rejected.raw is rejected_frame
            assert rejected.raw.payload is payload
            assert rejected.ingress is context
        oversized = admit_fixture(frame, context, max_payload_bytes=len(encoded) - 1)
        assert isinstance(oversized, Quarantined)
        assert oversized.reason is RejectionReason.PAYLOAD_TOO_LARGE


@pytest.mark.parametrize("seed", SEEDS)
def test_generated_late_frontier_boundary(seed: int) -> None:
    rng = Random(seed)
    frontier = generated_event(0)
    for offset in (0, *[rng.randrange(-100, 101) for _ in range(70)]):
        incoming = replace(
            generated_event(1),
            times=replace(
                frontier.times,
                event_time=replace(
                    frontier.times.event_time, value=T0 + timedelta(seconds=offset)
                ),
            ),
        )
        expected = LateStatus.LATE if offset < 0 else LateStatus.ON_OR_AFTER_FRONTIER
        result = annotate_late(incoming, frontier)
        assert result.status is expected
        assert result.incoming is incoming
        assert result.frontier is frontier
        unresolved = replace(incoming, instrument_id=MISSING)
        assert annotate_late(unresolved, frontier).status is LateStatus.UNKNOWN


@pytest.mark.parametrize("seed", SEEDS)
def test_generated_lineage_dag_permutations_and_rejected_mutations(seed: int) -> None:
    rng = Random(seed)
    for trial in range(12):
        count = rng.randrange(3, 18)
        references = [
            InputIdentity(
                ArtifactId(str(UUID(int=1000 + index))),
                content_hash(rng.randbytes(20)),
            )
            for index in range(count + 1)
        ]
        records: list[ArtifactLineageRecord] = []
        run_id = RunId(str(UUID(int=seed + 1)))
        for index in range(1, count + 1):
            earlier = rng.sample(range(index - 1), rng.randrange(index))
            input_indices = (*earlier, index - 1)
            records.append(ArtifactLineageRecord(
                LineageRecordId(str(UUID(int=index))), run_id,
                TransformationKind.NORMALIZATION,
                tuple(references[item] for item in input_indices), (references[index],),
            ))
        original = LineageGraph(tuple(records))
        for _ in range(4):
            rng.shuffle(records)
            permuted = LineageGraph(tuple(records))
            assert set(permuted.records) == set(original.records)
        backedge = ArtifactLineageRecord(
            LineageRecordId(str(UUID(int=10000 + trial))), run_id,
            TransformationKind.NORMALIZATION, (references[-1],), (references[0],),
        )
        with pytest.raises(ValueError, match="acyclic"):
            original.with_record(backedge)
        last = original.records[-1]
        changed_hash = ContentHash("0" * 64)
        conflicting = replace(
            last, inputs=(replace(last.inputs[0], content_hash=changed_hash), *last.inputs[1:])
        )
        with pytest.raises(ValueError, match="content hash"):
            LineageGraph((*original.records[:-1], conflicting))
        assert original.records[-1] is last
        assert len(original.records) == count
