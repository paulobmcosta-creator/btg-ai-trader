# S1 — Derived temporal-inheritance evidence

- Status: implementation detail selected for RQM-039 / B-HQI-08.
- Scope: causal temporal admissibility of derived technical data only.
- Authority: 0F-E RQM-039, 0E-B B-HQI-05/B-HQI-08 and QPI-02/QPI-11.

## Decision

A plain `ArtifactLineageRecord` proves identity/provenance only and makes no claim that a derived artifact was temporally admissible. Any such claim must be accompanied by `TemporalLineageEvidence`.

Each input and output artifact receives a typed `TemporalRestriction` with three conservative lower-bound axes:

- `event_not_before`;
- `effective_not_before`;
- `knowledge_not_before`.

For each axis, output restrictions must inherit the aggregate ancestral restriction:

1. known ancestor timestamps impose the latest (`max`) timestamp as the minimum admissible bound;
2. `UNKNOWN` or `NOT_PROVIDED` in any applicable ancestor makes the inherited bound `UNKNOWN`; the derived artifact may not replace it with a known timestamp;
3. `NOT_APPLICABLE` does not constrain an axis when another ancestor supplies an applicable restriction;
4. if every ancestor is `NOT_APPLICABLE` for an axis, no ancestral lower bound is asserted for that axis;
5. a derived artifact may remain more conservative (`UNKNOWN`) even when all ancestral bounds are known, but it may never claim an earlier known bound or erase an applicable ancestral restriction as `NOT_APPLICABLE`.

The evidence binds restrictions to the exact immutable `InputIdentity` values in the associated `ArtifactLineageRecord`, preventing temporal evidence from being silently attached to a different input/output ordering.

## Limits

- This is not a replay engine, backtester, feature pipeline or temporal join engine.
- It does not invent event/effective/knowledge timestamps.
- It does not authorize predictive features, labels, strategy, execution or financial state.
- Processing/ingestion timestamps remain observations of processing and are not substituted for historical knowledge availability.
