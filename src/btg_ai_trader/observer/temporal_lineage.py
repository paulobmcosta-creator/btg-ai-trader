"""Causal temporal restrictions for derived technical artifacts in Sprint 1."""

from dataclasses import dataclass
from datetime import datetime

from btg_ai_trader.observer.lineage import ArtifactLineageRecord
from btg_ai_trader.observer.provenance import InputIdentity
from btg_ai_trader.observer.temporal import TemporalValue, require_temporal
from btg_ai_trader.observer.values import MissingReason


@dataclass(frozen=True, slots=True)
class TemporalRestriction:
    """Conservative lower bounds for temporal admissibility, never fabricated timestamps."""

    event_not_before: TemporalValue
    effective_not_before: TemporalValue
    knowledge_not_before: TemporalValue

    def __post_init__(self) -> None:
        require_temporal(self.event_not_before, "event_not_before")
        require_temporal(self.effective_not_before, "effective_not_before")
        require_temporal(self.knowledge_not_before, "knowledge_not_before")


@dataclass(frozen=True, slots=True)
class ArtifactTemporalRestriction:
    identity: InputIdentity
    restriction: TemporalRestriction

    def __post_init__(self) -> None:
        if not isinstance(self.identity, InputIdentity):
            raise ValueError("temporal restriction requires immutable InputIdentity")
        if not isinstance(self.restriction, TemporalRestriction):
            raise ValueError("artifact temporal restriction requires TemporalRestriction")


def _aggregate_axis(values: tuple[TemporalValue, ...]) -> TemporalValue:
    if any(
        value in (MissingReason.UNKNOWN, MissingReason.NOT_PROVIDED)
        for value in values
        if isinstance(value, MissingReason)
    ):
        return MissingReason.UNKNOWN
    known = [value for value in values if isinstance(value, datetime)]
    return max(known) if known else MissingReason.NOT_APPLICABLE


def _validate_output_axis(inherited: TemporalValue, output: TemporalValue, field: str) -> None:
    if inherited is MissingReason.UNKNOWN:
        if output is not MissingReason.UNKNOWN:
            raise ValueError(f"{field} must remain UNKNOWN when any ancestor is temporally unknown")
        return
    if inherited is MissingReason.NOT_APPLICABLE:
        return
    if not isinstance(inherited, datetime):
        raise ValueError(f"unsupported inherited temporal restriction for {field}")
    if output is MissingReason.UNKNOWN:
        return
    if not isinstance(output, datetime):
        raise ValueError(f"{field} cannot erase an applicable ancestral temporal restriction")
    if output < inherited:
        raise ValueError(f"{field} cannot precede the latest ancestral temporal restriction")


@dataclass(frozen=True, slots=True)
class TemporalLineageEvidence:
    """Temporal admissibility claim bound to one immutable artifact-lineage record."""

    lineage: ArtifactLineageRecord
    inputs: tuple[ArtifactTemporalRestriction, ...]
    outputs: tuple[ArtifactTemporalRestriction, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.lineage, ArtifactLineageRecord):
            raise ValueError("temporal lineage evidence requires ArtifactLineageRecord")
        if type(self.inputs) is not tuple or type(self.outputs) is not tuple:
            raise ValueError("temporal lineage restrictions must be immutable tuples")
        if any(not isinstance(item, ArtifactTemporalRestriction) for item in self.inputs):
            raise ValueError("all temporal lineage inputs must be ArtifactTemporalRestriction")
        if any(not isinstance(item, ArtifactTemporalRestriction) for item in self.outputs):
            raise ValueError("all temporal lineage outputs must be ArtifactTemporalRestriction")
        if tuple(item.identity for item in self.inputs) != self.lineage.inputs:
            raise ValueError("temporal input restrictions must match lineage inputs exactly")
        if tuple(item.identity for item in self.outputs) != self.lineage.outputs:
            raise ValueError("temporal output restrictions must match lineage outputs exactly")

        event_floor = _aggregate_axis(
            tuple(item.restriction.event_not_before for item in self.inputs)
        )
        effective_floor = _aggregate_axis(
            tuple(item.restriction.effective_not_before for item in self.inputs)
        )
        knowledge_floor = _aggregate_axis(
            tuple(item.restriction.knowledge_not_before for item in self.inputs)
        )
        for output in self.outputs:
            _validate_output_axis(
                event_floor,
                output.restriction.event_not_before,
                "event_not_before",
            )
            _validate_output_axis(
                effective_floor,
                output.restriction.effective_not_before,
                "effective_not_before",
            )
            _validate_output_axis(
                knowledge_floor,
                output.restriction.knowledge_not_before,
                "knowledge_not_before",
            )
