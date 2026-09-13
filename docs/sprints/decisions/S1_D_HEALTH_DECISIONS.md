# S1-D — Pure Observer health decisions

- Date: 2026-09-13.
- State: DECISIONS_RECORDED_BEFORE_FIRST_MATERIAL_DEPENDENCY.
- Base: corrected S1-A `5158dc3375fd9ed0a311dd745a981fadf2ea643a`.
- Authority: bounded autonomous mandate for pure Observer runtime/health work.
- Scope: explicit monotonic samples, configurable experimental timeouts, separate phase/posture/passive readiness, and immutable transition evidence.
- No queue, transport, I/O, real clock, provider, financial operation, scheduler, persistence or integration with other workstreams.

## Decisions recorded before code

| DD | Concrete decision | Boundary |
|---|---|---|
| DD-36 | Separate RuntimePhase (STARTING, RECOVERING, RECONCILING, RUNNING, STOPPING, STOPPED), SafetyPosture (NORMAL, DEGRADED, SAFE_HALT, EMERGENCY_STOP), and capability-specific ReadinessStatus (READY, NOT_READY). | Only passive CONSUME_FRESH_OBSERVATIONS is assessed. No financial capability exists or can be approved. |
| DD-37 | HealthPolicy requires explicit positive integer heartbeat timeout and market staleness timeout in nanoseconds, with an opaque policy_ref. Equality to timeout is fresh; strictly greater is stale. No default or empirically final threshold is selected. | Experimental caller-supplied thresholds, valid for fixture engineering only; future real-feed limits require evidence and a recorded policy decision. |

DD-54 is not triggered: no concurrency, threads, async or I/O. DD-22 transport is not selected. DD-60 provider choice remains unresolved. These DD-36/DD-37 rows require no ADR under 0F-E; this concretizes the existing ADR-0011/0020 separation without changing its authority.

## Temporal contract

HealthSample contains a nonempty clock_scope, monotonic now_ns, and last heartbeat/market-data instants as nonnegative integers or explicit MissingReason. Bool, float, negative instants and timestamps later than now are rejected. There is no UTC conversion or comparison with market event_time. Unknown timestamps remain unknown in output ages, never zero.

monotonic_elapsed_ns computes a duration from two explicit readings and rejects backward time. The caller must establish that its readings belong to the same monotonic scope; the helper cannot attest clock provenance. evaluate_health requires the same scope as its previous assessment and nondecreasing now_ns. It also rejects a known heartbeat/market timestamp moving backwards within the same scope; a missing sample is preserved rather than filled from an earlier sample. Separate last-known monotonic watermarks retain ordering evidence across a missing sample, but never replace its unknown age or make readiness succeed.

A restart/new clock scope requires an explicit future continuity/recovery protocol. Callers must thread previous assessments through continuous evaluation; omitting previous starts a new fixture assessment and does not prove restart safety. No production lifecycle, unlatch/recovery authority or persistent state reconstruction is implemented here.

## Readiness and containment policy

Heartbeat freshness is reported separately as heartbeat_alive evidence; it does not prove whole-process liveness or readiness. The passive capability is READY only when phase is RUNNING, posture is NORMAL, heartbeat is known/fresh and market-data timestamp is known/fresh.

Missing/stale evidence fails closed for this passive readiness. During RUNNING it requests DEGRADED containment if the prior/requested posture is NORMAL. During startup/recovery/stopping, phase already blocks readiness; incomplete samples do not fabricate a successful startup or automatically latch startup failure.

All restrictive postures are latched by this experimental evaluator: previous DEGRADED, SAFE_HALT or EMERGENCY_STOP cannot be weakened by a fresh sample or by requesting NORMAL. Escalation to a stronger posture is allowed. There is no unlatch API in this increment. This is a conservative policy for the named passive capability, not a universal permission matrix for DEGRADED.

SAFE_HALT and EMERGENCY_STOP return evidence only. No flatten, cancellation, execution, restart, callback, network or process control action occurs. RUNNING alone is insufficient. READY in this narrow assessment does not establish provider availability, data admission quality, recovery completeness, production readiness or economic authority.

## Evidence and verification

Each evaluation returns an immutable HealthAssessment with original sample, phase, effective posture, named capability, readiness, reasons, ages and the immutable policy (including policy_ref and thresholds). A HealthTransition is returned when phase/posture/readiness changes, recording complete before/after assessments; an initial evaluation has no fabricated predecessor. No transition is persisted by this module. Stable evaluations still preserve fresh assessments.

Required fixture tests: exact timeout boundary, stale heartbeat, stale data with live heartbeat, missing values, zero/negative/float/bool thresholds, malformed enums/timestamps, backward readings/sample time and incompatible scopes; RUNNING not ready, RECOVERING/RECONCILING plus SAFE_HALT, no automatic unlatch, escalation, immutable before/after evidence and deterministic repeat evaluation. Six inherited remote checks must pass on the final SHA.

Traceability: ADR-0004/0011/0020; 0F-E S1-EC-017/018/055/056/091 and RQM-022/023/032/033/034. RQM-022/023 receive fixture arithmetic/decision evidence only, not a real heartbeat, real feed staleness, transit latency measurement or complete integration proof. Full NEG-CAP suite and formal Security Diff Scan remain pending; no Sprint 1 acceptance is claimed.
