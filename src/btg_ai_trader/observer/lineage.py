"""Pure validation of derivation N-to-M; no artifact registry or persistence."""

from dataclasses import dataclass
from enum import Enum

from btg_ai_trader.observer.identity import ArtifactId, EventId, LineageRecordId, RunId
from btg_ai_trader.observer.provenance import (
    ContentHash,
    InputIdentity,
    ProvenanceLabel,
    require_inputs,
)


class TransformationKind(Enum):
    NORMALIZATION = "NORMALIZATION"
    FILTERING = "FILTERING"
    CLEANING = "CLEANING"
    QUALITY_ASSESSMENT = "QUALITY_ASSESSMENT"


@dataclass(frozen=True, slots=True)
class ArtifactLineageRecord:
    record_id: LineageRecordId
    run_id: RunId
    transformation: TransformationKind
    inputs: tuple[InputIdentity, ...]
    outputs: tuple[InputIdentity, ...]
    input_roles: tuple[ProvenanceLabel, ...] = ()
    output_roles: tuple[ProvenanceLabel, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, LineageRecordId) or not isinstance(self.run_id, RunId):
            raise ValueError("lineage requires explicit record and run identities")
        if not isinstance(self.transformation, TransformationKind):
            raise ValueError("lineage requires an explicit transformation kind")
        require_inputs(self.inputs, "lineage inputs")
        require_inputs(self.outputs, "lineage outputs")
        if not self.inputs or not self.outputs:
            raise ValueError("derivation requires nonempty input and output sets")
        if any(not isinstance(item.artifact_id, ArtifactId) for item in self.outputs):
            raise ValueError("derived outputs require new ArtifactId, not external EventId")
        if {item.artifact_id for item in self.inputs} & {
            item.artifact_id for item in self.outputs
        }:
            raise ValueError("an artifact must not derive from itself")
        for roles, references in (
            (self.input_roles, self.inputs),
            (self.output_roles, self.outputs),
        ):
            if type(roles) is not tuple or any(
                not isinstance(role, ProvenanceLabel) for role in roles
            ):
                raise ValueError("lineage roles must be immutable logical labels")
            if roles and len(roles) != len(references):
                raise ValueError("lineage roles must match the corresponding references")


@dataclass(frozen=True, slots=True)
class LineageGraph:
    """Immutable supplied evidence set; validates global cycles and identity reuse."""

    records: tuple[ArtifactLineageRecord, ...] = ()

    def __post_init__(self) -> None:
        if type(self.records) is not tuple or any(
            not isinstance(record, ArtifactLineageRecord) for record in self.records
        ):
            raise ValueError("lineage graph requires a tuple of records")
        if len({record.record_id for record in self.records}) != len(self.records):
            raise ValueError("lineage record identities must be unique")
        hashes: dict[EventId | ArtifactId, ContentHash] = {}
        edges: dict[EventId | ArtifactId, set[EventId | ArtifactId]] = {}
        indegrees: dict[EventId | ArtifactId, int] = {}
        produced: set[EventId | ArtifactId] = set()
        for record in self.records:
            for output in record.outputs:
                if output.artifact_id in produced:
                    raise ValueError("derived artifact identity already has a production record")
                produced.add(output.artifact_id)
            for ref in (*record.inputs, *record.outputs):
                previous = hashes.get(ref.artifact_id)
                if previous is not None and previous != ref.content_hash:
                    raise ValueError("artifact identity must not change its content hash")
                hashes[ref.artifact_id] = ref.content_hash
                edges.setdefault(ref.artifact_id, set())
                indegrees.setdefault(ref.artifact_id, 0)
            for source in record.inputs:
                for target in record.outputs:
                    targets = edges[source.artifact_id]
                    if target.artifact_id not in targets:
                        targets.add(target.artifact_id)
                        indegrees[target.artifact_id] += 1
        ready = [artifact for artifact, count in indegrees.items() if count == 0]
        visited = 0
        while ready:
            artifact = ready.pop()
            visited += 1
            for child in edges[artifact]:
                indegrees[child] -= 1
                if indegrees[child] == 0:
                    ready.append(child)
        if visited != len(indegrees):
            raise ValueError("artifact derivation must be acyclic")

    def with_record(self, record: ArtifactLineageRecord) -> "LineageGraph":
        """Return a newly validated graph; failure leaves the original intact."""
        return LineageGraph((*self.records, record))
