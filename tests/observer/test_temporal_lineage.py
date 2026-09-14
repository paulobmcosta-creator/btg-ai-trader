"""Causal inheritance tests for RQM-039 / B-HQI-08."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from btg_ai_trader.observer.identity import ArtifactId, LineageRecordId, RunId
from btg_ai_trader.observer.lineage import ArtifactLineageRecord, TransformationKind
from btg_ai_trader.observer.provenance import ContentHash, InputIdentity
from btg_ai_trader.observer.temporal_lineage import (
    ArtifactTemporalRestriction,
    TemporalLineageEvidence,
    TemporalRestriction,
)
from btg_ai_trader.observer.values import MissingReason

NOW = datetime(2026, 9, 13, 12, tzinfo=UTC)


def _identity(number: int) -> InputIdentity:
    digest = f"{number:064x}"
    return InputIdentity(ArtifactId(str(UUID(int=number))), ContentHash(digest))


def _lineage(
    number: int,
    inputs: tuple[InputIdentity, ...],
    outputs: tuple[InputIdentity, ...],
) -> ArtifactLineageRecord:
    return ArtifactLineageRecord(
        LineageRecordId(str(UUID(int=number))),
        RunId(str(UUID(int=number + 1000))),
        TransformationKind.QUALITY_ASSESSMENT,
        inputs,
        outputs,
    )


def _bound(
    identity: InputIdentity,
    event: datetime | MissingReason,
    effective: datetime | MissingReason,
    knowledge: datetime | MissingReason,
) -> ArtifactTemporalRestriction:
    return ArtifactTemporalRestriction(
        identity,
        TemporalRestriction(event, effective, knowledge),
    )


def test_derived_artifact_cannot_precede_latest_known_ancestor_restriction() -> None:
    first = _identity(1)
    second = _identity(2)
    derived = _identity(3)
    lineage = _lineage(101, (first, second), (derived,))
    inputs = (
        _bound(first, NOW, NOW, NOW + timedelta(seconds=1)),
        _bound(
            second,
            NOW + timedelta(seconds=2),
            NOW + timedelta(seconds=1),
            NOW + timedelta(seconds=3),
        ),
    )

    valid = _bound(
        derived,
        NOW + timedelta(seconds=2),
        NOW + timedelta(seconds=1),
        NOW + timedelta(seconds=3),
    )
    assert TemporalLineageEvidence(lineage, inputs, (valid,)).outputs == (valid,)

    early = _bound(
        derived,
        NOW + timedelta(seconds=1),
        NOW + timedelta(seconds=1),
        NOW + timedelta(seconds=3),
    )
    with pytest.raises(ValueError, match="event_not_before cannot precede"):
        TemporalLineageEvidence(lineage, inputs, (early,))


def test_unknown_ancestral_knowledge_cannot_be_fabricated_as_known() -> None:
    first = _identity(4)
    second = _identity(5)
    derived = _identity(6)
    lineage = _lineage(102, (first, second), (derived,))
    inputs = (
        _bound(first, NOW, NOW, NOW + timedelta(seconds=1)),
        _bound(second, NOW, NOW, MissingReason.UNKNOWN),
    )

    fabricated = _bound(derived, NOW, NOW, NOW + timedelta(seconds=5))
    with pytest.raises(ValueError, match="knowledge_not_before must remain UNKNOWN"):
        TemporalLineageEvidence(lineage, inputs, (fabricated,))

    conservative = _bound(derived, NOW, NOW, MissingReason.UNKNOWN)
    TemporalLineageEvidence(lineage, inputs, (conservative,))


def test_not_provided_ancestral_time_is_conservatively_unknown() -> None:
    first = _identity(7)
    derived = _identity(8)
    lineage = _lineage(103, (first,), (derived,))
    inputs = (_bound(first, NOW, NOW, MissingReason.NOT_PROVIDED),)

    with pytest.raises(ValueError, match="knowledge_not_before must remain UNKNOWN"):
        TemporalLineageEvidence(
            lineage,
            inputs,
            (_bound(derived, NOW, NOW, NOW + timedelta(seconds=1)),),
        )


def test_not_applicable_axis_does_not_erase_other_ancestor_constraint() -> None:
    first = _identity(9)
    second = _identity(10)
    derived = _identity(11)
    lineage = _lineage(104, (first, second), (derived,))
    inputs = (
        _bound(first, NOW, MissingReason.NOT_APPLICABLE, NOW),
        _bound(second, NOW, NOW + timedelta(seconds=4), NOW),
    )

    with pytest.raises(ValueError, match="effective_not_before cannot precede"):
        TemporalLineageEvidence(
            lineage,
            inputs,
            (_bound(derived, NOW, NOW + timedelta(seconds=3), NOW),),
        )


def test_known_ancestral_constraint_cannot_be_erased_as_not_applicable() -> None:
    source = _identity(12)
    derived = _identity(13)
    lineage = _lineage(105, (source,), (derived,))
    inputs = (_bound(source, NOW, NOW, NOW),)

    with pytest.raises(ValueError, match="event_not_before cannot erase"):
        TemporalLineageEvidence(
            lineage,
            inputs,
            (_bound(derived, MissingReason.NOT_APPLICABLE, NOW, NOW),),
        )


def test_temporal_evidence_must_bind_exact_lineage_identities() -> None:
    source = _identity(14)
    wrong = _identity(15)
    derived = _identity(16)
    lineage = _lineage(106, (source,), (derived,))

    with pytest.raises(ValueError, match="inputs exactly"):
        TemporalLineageEvidence(
            lineage,
            (_bound(wrong, NOW, NOW, NOW),),
            (_bound(derived, NOW, NOW, NOW),),
        )


def test_inherited_restriction_remains_transitive_across_derivation_chain() -> None:
    source = _identity(17)
    middle = _identity(18)
    later_source = _identity(19)
    final = _identity(20)

    first_lineage = _lineage(107, (source,), (middle,))
    source_bound = _bound(source, NOW, NOW, NOW + timedelta(seconds=2))
    middle_bound = _bound(middle, NOW, NOW, NOW + timedelta(seconds=2))
    TemporalLineageEvidence(first_lineage, (source_bound,), (middle_bound,))

    second_lineage = _lineage(108, (middle, later_source), (final,))
    later_bound = _bound(
        later_source,
        NOW + timedelta(seconds=1),
        NOW,
        NOW + timedelta(seconds=5),
    )
    with pytest.raises(ValueError, match="knowledge_not_before cannot precede"):
        TemporalLineageEvidence(
            second_lineage,
            (middle_bound, later_bound),
            (_bound(final, NOW + timedelta(seconds=1), NOW, NOW + timedelta(seconds=4)),),
        )

    final_bound = _bound(
        final,
        NOW + timedelta(seconds=1),
        NOW,
        NOW + timedelta(seconds=5),
    )
    TemporalLineageEvidence(
        second_lineage,
        (middle_bound, later_bound),
        (final_bound,),
    )
